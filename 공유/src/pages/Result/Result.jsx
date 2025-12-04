import React, { useState, useEffect, useRef } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js';
import { Radar } from 'react-chartjs-2';
import './Result.css';

ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
);

const Result = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [resultData, setResultData] = useState(null);
  const [expandedItems, setExpandedItems] = useState({});
  const [scrollState, setScrollState] = useState({
    showFab: false,
    showFooter: false,
  });

  const summaryRef = useRef(null);

  useEffect(() => {
    if (location.state && location.state.resultData) {
        setResultData(location.state.resultData);
    } else {
        alert("결과 데이터가 없습니다. 면접을 먼저 진행해주세요.");
        navigate('/');
    }
  }, [location, navigate]);

  useEffect(() => {
    const handleScroll = () => {
      if (!summaryRef.current) return;

      const summaryBottom = summaryRef.current.getBoundingClientRect().bottom;
      const isSummaryHidden = summaryBottom < 50;
      const isAtBottom = (window.innerHeight + window.scrollY) >= (document.body.offsetHeight - 100);

      setScrollState({
        showFab: isSummaryHidden && !isAtBottom,
        showFooter: isAtBottom,
      });
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const toggleFeedback = (index) => {
    setExpandedItems(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  if (!resultData) return <div style={{ padding: '50px', textAlign: 'center' }}>결과 분석 중...</div>;

  const chartData = {
    labels: ['직무 연관성', '논리 구조', '구체성', '핵심 키워드', '직업적 태도'],
    datasets: [
      {
        label: '면접 역량',
        data: resultData.radarScores,
        backgroundColor: 'rgba(0, 123, 255, 0.2)',
        borderColor: 'rgb(0, 123, 255)',
        borderWidth: 2,
        pointBackgroundColor: 'rgb(0, 123, 255)',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: 'rgb(0, 123, 255)',
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      r: {
        angleLines: { color: '#ddd' },
        grid: { color: '#ddd' },
        pointLabels: { font: { size: 14, family: "'Noto Sans KR', sans-serif" } },
        ticks: {
          beginAtZero: true,
          max: 100,
          stepSize: 25,
          backdropColor: 'rgba(255, 255, 255, 0.7)',
          display: false 
        },
      },
    },
    plugins: {
      legend: { display: false },
    },
  };

  return (
    <>
      <header>
        <Link to="/" className="logo-link">
            <div className="logo">AI 면접</div>
        </Link>
        <Link to="/profile" className="profile-link">
            <div className="profile-icon">👤</div>
        </Link>
      </header>

      <main>
        <div className="result-container">
          
          <div className="summary-card" ref={summaryRef}>
            <div className="summary-header">
              <h2>모의 면접 결과</h2>
              <p>당신의 면접 역량을 분석했습니다.</p>
            </div>

            <div className="score-display">
              <span className="score-label">종합 점수</span>
              <h1>
                <span id="total-score">{resultData.totalScore}</span> / 100
              </h1>
              <span className="score-grade">{resultData.grade}</span>
            </div>

            <div className="chart-container">
               <Radar data={chartData} options={chartOptions} />
            </div>

            <div className="analysis-summary">
              <h3>전체 분석 요약</h3>
              <p style={{ whiteSpace: "pre-line" }}>{resultData.analysisText}</p>
            </div>
          </div>

          <div className="feedback-section-header">
            <div className="divider"></div>
            <h2>질문별 상세 피드백</h2>
            <div className="divider"></div>
          </div>

          <div className="feedback-list">
            {resultData.questions.map((q, index) => {
              const isExpanded = expandedItems[index];

              return (
                <div key={index} className={`feedback-item ${isExpanded ? 'expanded' : ''}`}>
                  <div 
                    className="feedback-header" 
                    onClick={() => toggleFeedback(index)}
                  >
                    <div className="question-info">
                      <span className="question-label">{q.label || `질문 ${index + 1}`}</span>
                      <h3 className="question-title">{q.title}</h3>
                    </div>
                    <button className="toggle-icon">
                      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="6 9 12 15 18 9"></polyline>
                      </svg>
                    </button>
                  </div>
                  
                  <div className="feedback-content">
                    <div className="my-answer">
                      <h4>나의 답변</h4>
                      <p style={{ whiteSpace: "pre-line" }}>{q.answer}</p>
                    </div>
                    
                    <div className="good-points">
                      <h4><span className="icon">✓</span> 잘한 점</h4>
                      <ul>
                        {q.goodPoints && q.goodPoints.map((point, i) => (
                          <li key={i}>{point}</li>
                        ))}
                      </ul>
                    </div>
                    
                    <div className="improvement-points">
                      <h4><span className="icon">!</span> 개선할 점</h4>
                      <ul>
                        {q.improvementPoints && q.improvementPoints.map((point, i) => (
                          <li key={i}>{point}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className={`footer-actions ${scrollState.showFooter ? 'visible' : ''}`}>
            <Link to="/" className="btn-restart">
              <span>↻</span> 면접 다시 보기
            </Link>
            <Link to="/history" className="btn-learn">
              <span>📚</span> 피드백 학습하기
            </Link>
          </div>

        </div>
      </main>

      <Link 
        to="/history" 
        className={`fab-learn ${scrollState.showFab ? 'visible' : ''}`}
      >
        <span>📚</span> 피드백 학습하기
      </Link>
    </>
  );
};

export default Result;