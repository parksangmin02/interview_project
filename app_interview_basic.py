# app_interview_basic.py (버그 3개 최종 수정본)
import os
import json
from flask import Flask, request, jsonify
from openai import OpenAI
import docx
import PyPDF2
from dotenv import load_dotenv

# .env 파일(비밀 상자)을 읽어옵니다.
load_dotenv()

app = Flask(__name__)

# .env에서 API 키를 안전하게 불러옵니다.
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise EnvironmentError("OPENAI_API_KEY 환경변수 미설정 ( .env 파일을 확인하세요! )")

# 불러온 키로 클라이언트를 실행합니다.
client = OpenAI(api_key=API_KEY)


# -----------------------------
# 질문 생성 API (FormData 전용으로 수정)
# -----------------------------
@app.post("/api/interview/create")
def generate_question():

    # --- 1. FormData(텍스트) 수신 ---
    job = request.form.get("job_title", "").strip()
    experience = request.form.get("experience_level", "").strip()
    intro = request.form.get("cover_letter", "").strip()
    
    # --- 2. FormData(파일) 수신 ---
    # 💥 (버그 수정!) 'file' 변수 정의가 누락되었던 것을 수정합니다.
    file = request.files.get("resume_file") 

    # --- 3. 파일 처리 로직 (님이 둬야 한다고 한 부분) ---
    # 💥 (버그 수정!) 파일이 '실제로' 있는지 확인하는 로직으로 수정
    if file and file.filename != '':
        filename = file.filename.lower()
        try:
            if filename.endswith(".txt"):
                intro += "\n" + file.read().decode("utf-8")
            
            elif filename.endswith(".pdf"):
                # 💥 (버그 수정!) .stream 으로 읽어야 합니다.
                pdf_reader = PyPDF2.PdfReader(file.stream) 
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                intro += "\n" + text
            
            elif filename.endswith(".docx"):
                # 💥 (버그 수정!) .stream 으로 읽어야 합니다.
                doc = docx.Document(file.stream) 
                text = "\n".join([p.text for p in doc.paragraphs])
                intro += "\n" + text
            
            else:
                return jsonify({"error": "지원하는 파일 형식은 txt, pdf, docx 입니다."}), 400
        
        except Exception as e_file:
             return jsonify({"error": f"파일 처리 중 오류 발생: {str(e_file)}"}), 500

    if not job:
        return jsonify({"error": "직무를 입력해야 합니다."}), 400

# --- 4. AI 프롬프트 (수정됨) ---
    prompt = f"""
당신은 전문 면접관입니다.
아래 직무 정보와 자기소개서를 분석하여,
지원자의 역량을 검증할 수 있는 **면접 질문 5개**를 생성하세요.

지원 직무: {job}
경력 수준: {experience}
자기소개서:
\"\"\"
{intro}
\"\"\"

**중요: 반드시 아래와 같은 JSON 포맷으로만 응답하세요. 다른 말은 하지 마세요.**
{{
  "questions": [
    "질문 1 내용",
    "질문 2 내용",
    "질문 3 내용",
    "질문 4 내용",
    "질문 5 내용"
  ],
  "interviewId": "ses-{job.replace(' ', '_')}-{os.urandom(4).hex()}"
}}
"""

    try:
        resp = client.chat.completions.create(
            model="gpt-5-nano", # ◀ 님이 요청한 모델 이름
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"} # ◀ JSON 응답 강제
        )
        raw = resp.choices[0].message.content

        try:
            return jsonify(json.loads(raw))
        except Exception as e_json:
            return jsonify({"error": "AI 응답 파싱 실패", "raw": raw, "details": str(e_json)}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------
# 답변 평가 API
# -----------------------------
# app_interview_basic.py 에 추가할 코드

@app.post("/api/interview/submit")
def submit_interview():
    try:
        data = request.get_json()
        # 프론트에서 보낸 질문+답변 리스트 받기
        qna_list = data.get("qnaList") 

        if not qna_list:
            return jsonify({"error": "데이터 없음"}), 400

        # AI에게 보낼 내용 정리
        full_text = ""
        for i, item in enumerate(qna_list):
            full_text += f"Q{i+1}: {item['question']}\nA: {item['answer']}\n\n"

        # ★ 여기가 핵심! 종합 평가 프롬프트 ★
        prompt = f"""
당신은 AI 면접관입니다. 지원자의 전체 면접 답변을 분석하여 성적표를 만드세요.

[면접 데이터]
{full_text}

반드시 아래 JSON 형식으로만 응답하세요 (다른 말 금지):
{{
  "totalScore": (0~100점 사이 정수),
  "grade": "(우수/양호/보통/미흡 중 하나)",
  "radarScores": [(직무), (논리), (구체성), (키워드), (태도) 각 점수 5개 리스트],
  "analysisText": "(전체적인 강점과 약점 총평 3문장)",
  "questions": [
    {{
       "id": 1,
       "title": "(질문 내용)",
       "answer": "(지원자 답변)",
       "goodPoints": ["잘한 점1", "잘한 점2"],
       "improvementPoints": ["아쉬운 점1", "아쉬운 점2"]
    }},
    ... (나머지 질문들도 동일하게)
  ]
}}
"""
        # AI 호출
        resp = client.chat.completions.create(
            model="gpt-4o-mini", # 모델명 (gpt-3.5-turbo 등 가능)
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        return jsonify(json.loads(resp.choices[0].message.content))

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)