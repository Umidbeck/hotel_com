import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import WebChatInterface from './WebChatInterface';

const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        <Route path="/chat/:roomNumber" element={<WebChatInterface />} />
      </Routes>
    </Router>
  );
};

export default App;
