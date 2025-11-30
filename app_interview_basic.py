# app_interview_basic.py (수정/확장 버전)
import os
import json
from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import docx
import PyPDF2

app = Flask(__name__)

API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise EnvironmentError("OPENAI_API_KEY 환경변수 미설정")

client = OpenAI(api_key="")


@app.get("/")
def home():
    return render_template("index.html")


# -----------------------------
# 질문 생성 API (경력 + 파일 + 텍스트 모두 지원)
# -----------------------------
@app.post("/generate_question")
def generate_question():

    job = request.form.get("job_position", "").strip()
    experience = request.form.get("experience_level", "").strip()      # NEW
    intro = request.form.get("self_intro", "").strip()
    file = request.files.get("resume_file")

    # 파일 업로드 시 텍스트 추출
    if file:
        filename = file.filename.lower()

        if filename.endswith(".txt"):
            intro += "\n" + file.read().decode("utf-8")

        elif filename.endswith(".pdf"):
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            intro += "\n" + text

        elif filename.endswith(".docx"):
            doc = docx.Document(file)
            text = "\n".join([p.text for p in doc.paragraphs])
            intro += "\n" + text

        else:
            return jsonify({"error": "txt, pdf, docx 파일만 업로드할 수 있습니다."}), 400

    if not job or not intro:
        return jsonify({"error": "직무와 자기소개서를 입력해야 합니다."}), 400

    prompt = f"""
당신은 전문 면접관입니다.

아래 정보를 기반으로 지원자에게 꼭 물어봐야 할 핵심 면접 질문 1개를 생성하세요.
- 지원 직무: {job}
- 경력 기간: {experience}
- 자기소개서:
\"\"\"
{intro}
\"\"\"

JSON 형식:
{{
  "question": "질문 내용"
}}
"""

    try:
        resp = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[{"role": "user", "content": prompt}]
        )
        raw = resp.choices[0].message.content

        try:
            return jsonify(json.loads(raw))
        except:
            return jsonify({"raw": raw})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------
# 답변 평가 API (변경 없음)
# -----------------------------
@app.post("/evaluate_answer")
def evaluate_answer():
    data = request.get_json()
    answer = (data.get("answer") or "").strip()

    if not answer:
        return jsonify({"error": "답변을 입력하세요."}), 400

    prompt = f"""
당신은 전문 면접관입니다.

아래 답변을 보고 사용자의 강점(strengths)과 단점(weaknesses)을
간결하고 명확하게 JSON 형태로 작성하세요.

사용자 답변:
\"\"\"
{answer}
\"\"\"

출력:
{{
  "strengths": "강점 내용",
  "weaknesses": "단점 내용"
}}
"""

    try:
        resp = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[{"role": "user", "content": prompt}]
        )
        raw = resp.choices[0].message.content

        try:
            return jsonify(json.loads(raw))
        except:
            return jsonify({"raw": raw})

    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)