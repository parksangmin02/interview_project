# -*- coding: utf-8 -*-

# app_interview_basic.py
import os
import json
from flask import Flask, render_template, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
from flask_cors import CORS

# 0) 환경 설정
load_dotenv()
app = Flask(__name__)
CORS(app)

# 1️ OpenAI API 키 설정
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise EnvironmentError("OPENAI_API_KEY 환경변수가 설정되어 있지 않습니다.")

client = OpenAI(api_key='')


# 2️ 기본 페이지 (index.html 렌더링)
@app.get("/")
def home():
     return render_template("index.html")



# 3 면접 질문 생성 API
@app.post("/generate_questions")
def generate_questions():
    """
    요청(JSON):
    {
        "job_position": "데이터 분석가"
    }

    응답(JSON):
    {
        "questions": [
            {"question": "이 직무를 선택한 이유는 무엇인가요?"},
            {"question": "데이터 분석 과정에서 가장 중요한 단계는 무엇이라고 생각하나요?"},
            ...
        ]
    }
    """
    data = request.get_json(silent=True) or {}
    job = (data.get("job_position") or "").strip()

    if not job:
        return jsonify({"error": "직무(job_position)는 필수 입력 항목입니다."}), 400

    #프롬프트 구성
    prompt = f"""
당신은 면접관입니다. 사용자가 지원하는 직무에 맞추어 실제 면접에서 사용할 질문 5개를 생성하세요.
각 질문은 명확하고 실무 중심이어야 하며, 불필요한 팁이나 설명은 포함하지 마세요.

출력 형식은 아래 JSON 구조를 따르세요:
{{
  "questions": [
    {{"question": "질문 1"}},
    {{"question": "질문 2"}},
    {{"question": "질문 3"}},
    {{"question": "질문 4"}},
    {{"question": "질문 5"}}
  ]
}}

지원 직무: {job}
"""

    try:
        #OpenAI API 호출
        resp = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "당신은 전문 면접관입니다. 사용자의 직무에 맞는 질문을 구성합니다."},
                {"role": "user", "content": prompt}
            ]
        )

        raw = resp.choices[0].message.content

        #모델의 JSON 파싱 시도
        try:
            parsed = json.loads(raw)
            if not isinstance(parsed, dict) or "questions" not in parsed:
                raise ValueError("questions 키가 없습니다.")
            return jsonify(parsed), 200
        except Exception:
            #JSON 파싱 실패 시 원문 반환
            return jsonify({
                "warning": "모델 응답을 JSON으로 파싱하지 못했습니다. raw 필드를 확인하세요.",
                "raw": raw
            }), 200

    except Exception as e:
        return jsonify({"error": f"OpenAI 호출 실패: {e}"}), 500

@app.post("/analyze_answer")
def analyze_answer():
    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()
    answer = data.get("answer", "").strip()

    if not question or not answer:
        return jsonify({"error": "question과 answer는 필수입니다."}), 400

    prompt = f"""
당신은 면접 평가 전문가입니다.
다음 질문과 답변을 보고 아래 5개 기준에 대해 0~100 점수를 정수로 매기세요.

반드시 아래 JSON 형식만 출력하세요:

{{
  "scores": {{
    "job_fit": <0-100>,
    "logic": <0-100>,
    "attitude": <0-100>,
    "specificity": <0-100>,
    "keywords": <0-100>
  }},
  "strengths": ["문장1","문장2"],
  "weaknesses": ["문장1","문장2"]
}}

질문: {question}
답변: {answer}
"""

    try:
        # gpt-5-nano → gpt-5-mini (JSON 안정성 크게 증가)
        resp = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "당신은 면접 평가 전문가입니다."},
                {"role": "user", "content": prompt}
            ]
            # temperature 절대 넣지 않음 (모델 제한 때문)
        )

        raw = resp.choices[0].message.content

        # 1차 JSON 파싱
        try:
            parsed = json.loads(raw)
        except:
            # JSON 앞뒤에 text가 붙는 경우 → 괄호 부분만 추출
            import re
            json_match = re.search(r"\{[\s\S]*\}", raw)
            if not json_match:
                return jsonify({"warning": "JSON 파싱 실패", "raw": raw}), 200
            try:
                parsed = json.loads(json_match.group())
            except:
                return jsonify({"warning": "JSON 파싱 완전 실패", "raw": raw}), 200

        # 기본값 처리
        s = parsed.get("scores", {})
        normalized = {
            "job_fit": int(s.get("job_fit", 0)),
            "logic": int(s.get("logic", 0)),
            "attitude": int(s.get("attitude", 0)),
            "specificity": int(s.get("specificity", 0)),
            "keywords": int(s.get("keywords", 0))
        }

        return jsonify({
            "scores": normalized,
            "strengths": parsed.get("strengths", []),
            "weaknesses": parsed.get("weaknesses", [])
        }), 200

    except Exception as e:
        return jsonify({"error": f"분석 실패: {e}"}), 500


if __name__ == "__main__":
    #Flask 개발 서버 실행
    app.run(host="0.0.0.0", port=5000, debug=True)