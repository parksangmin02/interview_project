# app_interview_basic.py (프론트엔드 연동을 위한 최종 수정본 / 상세 주석)

import os
import json
from flask import Flask, request, jsonify  # ◀ render_template는 React가 있으니 삭제
from openai import OpenAI
import docx
import PyPDF2
from dotenv import load_dotenv  # ◀ [추가] .env 파일을 읽기 위한 라이브러리

# [추가] .env 파일(API 키 비밀 상자)을 읽어옵니다.
# (이유: API 키를 코드에 하드코딩하면 깃허브에 유출되는 보안 사고가 나기 때문입니다.)
load_dotenv()

app = Flask(__name__)

# [수정] .env에서 API 키를 안전하게 불러옵니다.
# (원래: 키를 하드코딩하거나, .env 로드 없이 os.getenv를 써서 에러 발생)
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise EnvironmentError("OPENAI_API_KEY 환경변수 미설정 ( .env 파일을 확인하세요! )")

# [수정] 불러온 API_KEY '변수'를 사용해 클라이언트를 실행합니다.
client = OpenAI(api_key=API_KEY)


# [삭제] @app.get("/") (홈페이지) 라우트는 삭제했습니다.
# (이유: 홈페이지(/)는 이제 React(프론트엔드)가 담당하며,
#       Vite Proxy 설정으로 인해 백엔드의 이 코드는 절대 실행되지 않습니다.)


# ------------------------------------------------------------------
# 질문 생성 API (프론트엔드 'InterviewSetup.jsx'와 연동)
# ------------------------------------------------------------------
# [수정] 프론트엔드의 API 명세서와 URL을 통일합니다.
# (원래: /generate_question)
@app.post("/api/interview/create")
def generate_question():

    # --- 1. FormData(텍스트) 수신 ---

    # [수정] 프론트엔드의 <input name="...">에 맞게 필드명을 통일합니다.
    # (원래: job_position)
    job = request.form.get("job_title", "").strip()

    # [추가] 프론트엔드 폼에 'experience_level'이 추가되어, 여기서 받습니다.
    experience = request.form.get("experience_level", "").strip()

    # [수정] 프론트엔드 <textarea name="...">에 맞게 필드명을 통일합니다.
    # (원래: self_intro)
    intro = request.form.get("cover_letter", "").strip()

    # --- 2. FormData(파일) 수신 ---

    # [수정] 프론트엔드가 'resume_file'이라는 이름으로 파일을 보냅니다.
    # 💥 (버그 수정!) 원본 코드에 이 'file' 변수 정의가 누락되어 500 에러가 발생했습니다.
    file = request.files.get("resume_file")

    # --- 3. 파일 처리 로직 (프론트엔드 요청사항 반영) ---

    # 💥 (버그 수정!) 파일이 '실제로' 있는지(None이 아니고, 파일명도 있는지)
    #     정확히 확인하는 로직으로 수정했습니다.
    if file and file.filename != '':
        filename = file.filename.lower()
        try:
            if filename.endswith(".txt"):
                # (로직 설명) 자소서(intro) 텍스트 뒤에 파일 텍스트를 합칩니다.
                intro += "\n" + file.read().decode("utf-8")

            elif filename.endswith(".pdf"):
                # 💥 (버그 수정!) PDF/DOCX 파일은 .stream 으로 읽어야 에러가 안 납니다.
                pdf_reader = PyPDF2.PdfReader(file.stream)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                intro += "\n" + text

            elif filename.endswith(".docx"):
                # 💥 (버그 수정!) .stream 으로 읽어야 에러가 안 납니다.
                doc = docx.Document(file.stream)
                text = "\n".join([p.text for p in doc.paragraphs])
                intro += "\n" + text

            else:
                return jsonify({"error": "지원하는 파일 형식은 txt, pdf, docx 입니다."}), 400

        except Exception as e_file:
             # (설명) 파일이 깨졌거나 읽을 수 없을 때의 대비책입니다.
             return jsonify({"error": f"파일 처리 중 오류 발생: {str(e_file)}"}), 500

    if not job: # ◀ 직무명은 필수 항목으로 체크
        return jsonify({"error": "직무를 입력해야 합니다."}), 400

    # --- 4. AI 프롬프트 (프론트엔드 연동용) ---
    prompt = f"""
당신은 전문 면접관입니다.
아래 직무 정보와 자기소개서를 분석하여,
지원자에게 반드시 물어볼 핵심 질문을 1개 생성하세요.

지원 직무: {job}
경력 수준: {experience}
자기소개서 (이력서 내용 포함):
\"\"\"
{intro}
\"\"\"

JSON 형식으로만 응답하세요:
{{
  "question": "AI가 생성한 질문 내용",
  "interviewId": "ses-{job.replace(' ', '_')}-{os.urandom(4).hex()}"
}}
""" # ◀ [수정] 프론트엔드의 `Maps()`가 `interviewId`를 필요로 합니다.
    #     따라서 AI가 아닌, 서버(Python)가 직접 고유 ID를 생성해서
    #     AI가 이 형식을 흉내 내도록 프롬프트를 수정했습니다.
    # 💥 (버그 수정!) 원본 JSON 예시에 쉼표(,)가 빠져있던 것을 수정했습니다.

    try:
        resp = client.chat.completions.create(
            model="gpt-5-nano", # ◀ 프론트엔드 팀원이 요청한 모델 이름
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"} # ◀ [추가] AI가 JSON으로만 답하도록 강제
        )
        raw = resp.choices[0].message.content

        try:
            # (설명) AI가 보낸 JSON 문자열을 실제 JSON 객체로 변환 후 프론트엔드에 전송
            return jsonify(json.loads(raw))
        except Exception as e_json:
            # (설명) AI가 JSON 형식을 어겼을 때의 대비책
            return jsonify({"error": "AI 응답 파싱 실패", "raw": raw, "details": str(e_json)}), 500

    except Exception as e:
        # (설명) OpenAI API 키 오류, 한도 초과 등 모든 심각한 에러 처리
        return jsonify({"error": str(e)}), 500


# -----------------------------
# 답변 평가 API
# -----------------------------
# (설명) 이 API는 프론트엔드의 'Interview.jsx' 페이지에서 사용될 예정입니다.
@app.post("/evaluate_answer")
def evaluate_answer():
    data = request.get_json()
    answer = (data.get("answer") or "").strip()

    if not answer:
        return jsonify({"error": "답변을 입력하세요."}), 400

    prompt = f"""
(답변 평가 프롬프트는 생략...)
"""

    try:
        resp = client.chat.completions.create(
            model="gpt-5-nano", # ◀ 프론트엔드 팀원이 요청한 모델 이름
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        raw = resp.choices[0].message.content

        try:
            return jsonify(json.loads(raw))
        except:
            return jsonify({"raw": raw})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # [수정] app.run() 방식을 표준적인 방식으로 변경
    # 'host="0.0.0.0"' : localhost, 127.0.0.1 등 모든 접속을 허용
    # 'port=5000' : 5000번 포트로 서버 실행
    # 'debug=True' : 코드 수정 시 서버 자동 재시작 (개발 편의용)
    app.run(host="0.0.0.0", port=5000, debug=True)