export const startInterview = async (formData) => {
    const API_URL = '/api/interview/create'; 

    const response = await fetch(API_URL, {
        method: 'POST',
        body: formData 
    });
    
    if (!response.ok) {
        const errorData = await response.json(); 
        throw new Error(errorData.message || `서버 응답 오류: ${response.status}`);
    }

    return response.json();
};

export const submitInterview = async (interviewId, qnaList) => {
    const API_URL = '/api/interview/submit';

    const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ interviewId, qnaList })
    });

    if (!response.ok) {
        throw new Error('제출 실패');
    }

    return response.json();
};