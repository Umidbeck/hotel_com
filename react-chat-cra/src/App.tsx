// src/App.tsx
import React from 'react';
import { Routes, Route } from 'react-router-dom';
import WebChatInterface from './WebChatInterface';
import LanguageSelectPage from './pages/LanguageSelectPage';
import NotFoundPage from './pages/NotFoundPage';

const App: React.FC = () => {
  return (
    <Routes>
      <Route path="/chat/:roomNumber" element={<WebChatInterface />} />
      <Route path="/language-select" element={<LanguageSelectPage />} />
      <Route path="/404" element={<NotFoundPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
};

export default App;

