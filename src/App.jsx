import React from 'react';
import { Routes, Route } from 'react-router-dom';
import './main.css';

import InterviewSetup from './pages/InterviewSetup/InterviewSetup.jsx';
import Interview from './pages/Interview/Interview.jsx';
import Result from './pages/Result/Result.jsx';

function App() {
  return (
    <Routes>
      <Route path="/" element={<InterviewSetup />} />
      <Route path="/interview/:interviewId" element={<Interview />} />
      <Route path="/result" element={<Result />} />
    </Routes>
  );
}

export default App;