import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import './InterviewSetup.css';
import { startInterview } from '../../services/InterviewService.js'; 

function InterviewSetup() {
    const navigate = useNavigate();
    const [isLoading, setIsLoading] = useState(false);
    
    const [resumeFile, setResumeFile] = useState(null);

    const handleFileChange = (event) => {
        if (event.target.files) {
            setResumeFile(event.target.files[0]);
        }
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        setIsLoading(true);
    
        const formData = new FormData(event.target);
        if (resumeFile) {
            formData.append('resume_file', resumeFile);
        }
        
        const jobTitle = formData.get('job_title');
        const experienceLevel = formData.get('experience_level');

        try {
            const result = await startInterview(formData); 
            console.log('API 응답 성공:', result);

            const generatedQuestions = result.questions.map((qText, index) => ({
                id: index + 1,
                title: qText
            }));

            navigate(`/interview/${result.interviewId}`, {
                state: {
                    jobTitle: jobTitle,
                    experienceLevel: experienceLevel,
                    questions: generatedQuestions
                }
            });

            navigate(`/interview/${result.interviewId}`, {
                state: {
                    jobTitle: jobTitle,
                    experienceLevel: experienceLevel,
                    questions: generatedQuestions
                }
            });

        } catch (error) {
            console.error("API 요청 실패:", error);
            alert(`면접 요청에 실패했습니다. (${error.message})`);
            
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <>
            <header>
                <Link to="/dashboard" className="logo-link">
                    <div className="logo">AI 면접</div>
                </Link>
                <Link to="/profile" className="profile-link">
                    <div className="profile-icon">👤</div>
                </Link>
            </header>

            <main>
                {isLoading ? (
                    <div className="loading-container" style={{ textAlign: 'center', padding: '100px' }}>
                        <h1>면접 준비 중...</h1>
                        <p>AI 면접관이 질문을 생성하고 있습니다. 잠시만 기다려주세요.</p>
                    </div>
                ) : (
                    <div className="form-container">
                        <h1>면접 설정하기</h1>
                        <p>AI 면접관에게 필요한 정보를 알려주세요.</p>

                        <form onSubmit={handleSubmit}>
                            
                            <div className="form-group">
                                <label htmlFor="job-title">직무명 (필수)</label>
                                <input type="text" id="job-title" name="job_title" placeholder="예: 프론트엔드 개발자" required autoComplete="off" />
                            </div>

                            <div className="form-group">
                                <label htmlFor="experience-level">경력 수준 (필수)</label>
                                <select id="experience-level" name="experience_level" required defaultValue="">
                                    <option value="" disabled>선택하세요</option>
                                    <option value="newbie">신입 (Newbie)</option>
                                    <option value="junior">주니어 (1~3년)</option>
                                    <option value="senior">시니어 (5년 이상)</option>
                                </select>
                            </div>
                            
                            <div className="form-group" 
                                style={{ display: 'none' }}>
                                <label htmlFor="resume-file">이력서 파일 (선택)</label>
                                <input 
                                    type="file" 
                                    id="resume-file"
                                    accept=".txt, .pdf, .docx"
                                    onChange={handleFileChange}
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="cover-letter">자기소개 자료 (선택)</label>
                                <textarea id="cover-letter" name="cover_letter" rows="8" placeholder="자기소개서를 붙여넣거나, 나중에 파일을 드래그하세요."></textarea>
                            </div>

                            <button type="submit" className="submit-btn">면접 시작하기</button>
                        </form>
                    </div>
                )}
            </main>
        </>
    );
}

export default InterviewSetup;