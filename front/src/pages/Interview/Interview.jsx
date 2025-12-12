import React, { useState } from 'react';
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom';
import { submitInterview } from '../../services/InterviewService';
import './Interview.css';

const Interview = () => {
  const { interviewId } = useParams(); 
  const navigate = useNavigate();      
  const location = useLocation();

  const [isSubmitting, setIsSubmitting] = useState(false);

  const { jobTitle, experienceLevel, questions: receivedQuestions } = location.state || { 
      jobTitle: "직무 정보 없음", 
      experienceLevel: "newbie",
      questions: []
  };

  const levelMap = { newbie: "신입", junior: "주니어 (1~3년)", senior: "시니어 (5년 이상)" };
  const displayLevel = levelMap[experienceLevel] || "신입";

  const [questions] = useState(
    receivedQuestions && receivedQuestions.length > 0 
      ? receivedQuestions 
      : [{ id: 1, title: "질문 데이터를 불러오지 못했습니다." }]
  );

  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState({});

  const currentQuestion = questions[currentIndex];
  const currentAnswerText = answers[currentIndex] || "";

  const handleInputChange = (e) => {
    const newText = e.target.value;
    setAnswers((prevAnswers) => ({
      ...prevAnswers,
      [currentIndex]: newText 
    }));
  };

  const handlePrev = () => {
    if (currentIndex > 0) setCurrentIndex(currentIndex - 1);
  };

  const handleNext = async () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex(currentIndex + 1);
    } else {
      if (window.confirm("모든 답변을 제출하시겠습니까?")) {
        
        setIsSubmitting(true); 

        try {
          const qnaList = questions.map((q, index) => ({
            question: q.title,
            answer: answers[index] || "" 
          }));

          const resultData = await submitInterview(interviewId, qnaList);

          navigate('/result', { 
            state: { resultData: resultData } 
          });
          
        } catch (error) {
          console.error(error);
          alert("제출 중 오류가 발생했습니다. 다시 시도해주세요.");
          
          setIsSubmitting(false); 
        }
      }
    }
  };

  return (
    <>
      <header>
        <Link to="/dashboard" className="logo-link"><div className="logo">AI 면접</div></Link>
        <Link to="/profile" className="profile-link"><div className="profile-icon">👤</div></Link>
      </header>

      <main>
        <div className="interview-container">
          <div className="interview-info-header">
            <div className="info-left">
              <h1 className="job-title">{jobTitle} ({displayLevel})</h1>
              <span className="status-badge">면접 진행 중</span>
            </div>
            <div className="info-right">
              <span className="page-count">{currentIndex + 1} / {questions.length}</span>
            </div>
          </div>

          <div className="progress-bar-container">
            <div className="progress-bar">
              {questions.map((_, index) => {
                const isAnswered = answers[index] && answers[index].trim().length > 0;
                const isCurrent = index === currentIndex;
                let className = "progress-segment";
                if (isAnswered) className += " answered";
                if (isCurrent) className += " current";
                return (
                  <div 
                    key={index} 
                    className={className} 
                    onClick={() => !isSubmitting && setCurrentIndex(index)}
                    style={{ cursor: isSubmitting ? 'not-allowed' : 'pointer' }} 
                    title={`${index + 1}번 질문으로 이동`}
                  ></div>
                );
              })}
            </div>
          </div>

          <div className="interview-card">
            <div className="question-header">
              <span className="question-number">질문 {currentIndex + 1}</span>
              <h2>{currentQuestion.title}</h2>
              <p className="tip-message">답변은 자동으로 저장됩니다.</p>
            </div>
            
            <div className="answer-section">
              <textarea 
                className="answer-textarea" 
                placeholder="여기에 답변을 입력하세요..." 
                value={currentAnswerText} 
                onChange={handleInputChange}
                disabled={isSubmitting}
              ></textarea>
               <div className="char-count">{currentAnswerText.length} 자</div>
            </div>

            <div className="navigation-buttons">
              <button 
                className="nav-button prev-button" 
                onClick={handlePrev} 
                disabled={currentIndex === 0 || isSubmitting}
              >
                이전
              </button>
              
              <button 
                className="nav-button next-button" 
                onClick={handleNext} 
                disabled={isSubmitting}
              >
                {isSubmitting ? "제출 중..." : (currentIndex === questions.length - 1 ? "제출하기" : "다음")}
              </button>
            </div>
          </div>
        </div>
      </main>

      {isSubmitting && (
        <div className="loading-overlay">
          <div className="spinner"></div>
          <h2>AI 면접관이 결과를 분석하고 있습니다</h2>
          <p>답변 내용에 따라 최대 10초 정도 소요됩니다.<br/>잠시만 기다려주세요.</p>
        </div>
      )}
    </>
  );
};

export default Interview;