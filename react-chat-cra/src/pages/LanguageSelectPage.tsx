import React, { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './language.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND || 'http://localhost:8000';

const LanguageSelectPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const searchParams = new URLSearchParams(location.search);
  const room = searchParams.get('room');
  const token = searchParams.get('token');

  useEffect(() => {
    if (!room || !token) {
      navigate('/404');
    }
  }, [room, token, navigate]);

  const handleSelectLanguage = async (language: 'uz' | 'ru' | 'en') => {
    if (!room || !token) return;

    const langCodeMap: Record<string, string> = {
      uzbek: 'uz',
      russian: 'ru',
      english: 'en',
    };

    const localLang = langCodeMap[language];

    try {
      const res = await fetch(`${BACKEND_URL}/api/set-language/${room}/?token=${token}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ language }),
      });

      const data = await res.json();
      if (data.success) {
        // 💾 Tanlangan tilni saqlaymiz
        localStorage.setItem('chat_language', localLang);
        navigate(`/chat/${room}?token=${token}`, { replace: true });
      } else {
        navigate('/404');
      }
    } catch (error) {
      console.error('❌ Tilni saqlashda xatolik:', error);
      navigate('/404');
    }
  };

  return (
    <div className="language-wrapper">
      <div className="floating-shapes">
        <div className="shape"></div>
        <div className="shape"></div>
        <div className="shape"></div>
      </div>

      <div className="container">
        <h1 className="greeting">Assalamu alaykum</h1>
        <p className="welcome-text">Mehmonxonamizga xush kelibsiz</p>

        <div className="language-buttons">
          <button
            className="language-btn uzbek-btn"
            onClick={() => handleSelectLanguage('uz')}
          >
            <span className="flag-icon">🇺🇿</span> O‘zbek tili
          </button>
          <button
            className="language-btn russian-btn"
            onClick={() => handleSelectLanguage('ru')}
          >
            <span className="flag-icon">🇷🇺</span> Русский язык
          </button>
          <button
            className="language-btn english-btn"
            onClick={() => handleSelectLanguage('en')}
          >
            <span className="flag-icon">🇬🇧</span> English
          </button>
        </div>
      </div>
    </div>
  );
};

export default LanguageSelectPage;



