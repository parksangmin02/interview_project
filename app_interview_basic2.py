# app_interview_basic.py  (기존 프롬프트 수정, 계산 코드 추가 정리본)
import os
import json
from flask import Flask, request, jsonify
from openai import OpenAI
import docx
import PyPDF2
from dotenv import load_dotenv

# -------------------------
# 환경 변수 로드
# -------------------------
load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise EnvironmentError("OPENAI_API_KEY 누락됨 (.env 확인)")

client = OpenAI(api_key=API_KEY)


# 점수 산출 가중치 매핑(Weigh_map)/ 기준별 최종 점수 계산(calculate_final_scores)/등급 책정(grade) 코드 입니다.
# -------------------------
# 가중치 매핑(추가)
# -------------------------
WEIGHT_MAP = {
    "high": 1.0,
    "med-high": 0.8,
    "med": 0.6,
    "low": 0.4
}

# -------------------------
# 기준별 최종 점수 계산(추가)
# -------------------------
def calculate_final_scores(question_weights, answer_scores):
    criteria_list = ["직무", "논리", "구체성", "키워드", "태도"]
    final_scores = {c: 0 for c in criteria_list}

    for criterion in criteria_list:
        weighted_sum = 0
        weight_total = 0

        for q_num, weights in question_weights.items():
            weight = WEIGHT_MAP[weights[criterion]]
            score = answer_scores[q_num][criterion]

            weighted_sum += score * weight
            weight_total += weight

        final_scores[criterion] = round(weighted_sum / weight_total, 2)

    return final_scores


# -------------------------
# 등급 책정(추가)
# -------------------------
def grade(score):
    if score >= 90:
        return "우수"
    elif score >= 80:
        return "양호"
    elif score >= 70:
        return "보통"
    else:
        return "미흡"


# =====================================================================
# 1) 질문 생성 API
# =====================================================================
@app.post("/api/interview/create")
def generate_question():
    job = request.form.get("job_title", "").strip()
    experience = request.form.get("experience_level", "").strip()
    intro = request.form.get("cover_letter", "").strip()

    file = request.files.get("resume_file")

    if file and file.filename != '':
        filename = file.filename.lower()

        try:
            if filename.endswith(".txt"):
                intro += "\n" + file.read().decode("utf-8")

            elif filename.endswith(".pdf"):
                pdf_reader = PyPDF2.PdfReader(file.stream)
                text = ""
                for page in pdf_reader.pages:
                    extracted = page.extract_text() or ""
                    text += extracted + "\n"
                intro += "\n" + text

            elif filename.endswith(".docx"):
                doc = docx.Document(file.stream)
                text = "\n".join(p.text for p in doc.paragraphs)
                intro += "\n" + text

            else:
                return jsonify({"error": "지원 형식: txt, pdf, docx"}), 400

        except Exception as e:
            return jsonify({"error": f"파일 읽기 오류: {str(e)}"}), 500

    if not job:
        return jsonify({"error": "직무를 입력해야 합니다."}), 400

    prompt = f"""
당신은 전문 면접관입니다.
아래 직무, 경력, 자기소개서를 읽고 **면접 질문 5개**를 생성하세요.

직무: {job}
경력: {experience}
자기소개서:
\"\"\"{intro}\"\"\"

JSON 형식으로만 응답하세요:
{{
  "questions": [
    "질문1",
    "질문2",
    "질문3",
    "질문4",
    "질문5"
  ],
  "interviewId": "ses-{job.replace(' ', '_')}-{os.urandom(4).hex()}"
}}
"""

    try:
        resp = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        raw = resp.choices[0].message.content
        return jsonify(json.loads(raw))

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 기존 프롬프트에 면접 데이터를 분석해 가중치, 점수를 매기도록 추가했습니다.
# =====================================================================
# 2) 답변 제출 및 자동 평가 API
# =====================================================================
@app.post("/api/interview/submit")
def submit_interview():
    try:
        data = request.get_json()
        qna_list = data.get("qnaList")

        if not qna_list:
            return jsonify({"error": "qnaList 데이터 없음"}), 400

        # Q/A 텍스트 작성
        full_text = ""
        for i, item in enumerate(qna_list):
            full_text += f"Q{i+1}: {item['question']}\nA: {item['answer']}\n\n"

        # ★ AI 평가 프롬프트
        prompt = f"""
당신은 AI 면접 평가 전문가입니다.
아래 면접 Q/A 리스트를 기반으로 질문 중요도, 가중치, 점수, 분석을 수행하세요.

[면접 데이터]
{full_text}

해야 할 작업:
1) 각 질문의 중요도를 5개 기준으로 평가 (high / med-high / med / low)
2) 각 질문 답변을 기준별로 0~100점 평가
3) 각 질문별 Good / Improvement 포인트 생성
4) 전체 총평 작성

반드시 JSON만 출력하세요:

{{
  "questionWeights": {{
      "1": {{"직무": "high", "논리": "med", "구체성": "high", "키워드": "low", "태도": "high"}},
      ...
  }},
  "answerScores": {{
      "1": {{"직무": 85, "논리": 90, "구체성": 88, "키워드": 72, "태도": 93}},
      ...
  }},
  
  "analysisText": "(전체 총평)",
  "questions": [
    {{
      "id": 1,
       "title": "(질문 내용)",
       "answer": "(지원자 답변)",
       "goodPoints": ["잘한 점1", "잘한 점2"],
       "improvementPoints": ["아쉬운 점1", "아쉬운 점2"]
    }}
  ],
  
}}
"""

        # AI 호출
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )

        ai_result = json.loads(resp.choices[0].message.content)

        # 위의 프롬프트에서 radarScores/totalScore/grade 부분은 계산 코드로 변환했습니다.
        # -----------------------------
        # 점수 계산 (Radar Score)
        # -----------------------------
        radar = calculate_final_scores(
            ai_result["questionWeights"],
            ai_result["answerScores"]
        )

        total_score = round(sum(radar.values()) / len(radar))
        grade_result = grade(total_score)

        final_json = {
            "totalScore": total_score,
            "grade": grade_result,
            "radarScores": radar
        }

        return jsonify(final_json)

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500


# =====================================================================
# 실행
# =====================================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
