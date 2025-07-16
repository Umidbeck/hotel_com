import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Send } from 'lucide-react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import './styles.css';
import { w3cwebsocket as W3CWebSocket } from 'websocket';
import { v4 as uuidv4 } from 'uuid';
import { getTranslation } from './i18n';

const BACKEND_URL = process.env.REACT_APP_BACKEND || 'http://localhost:8000';
const WS_URL = BACKEND_URL.replace('http', 'ws');

interface Message {
  id: string;
  uuid: string;
  text: string;
  sender: 'me' | 'other';
  time: string;
  status?: 'pending' | 'delivered' | 'failed';
}

interface RoomInfo {
  language: string | null;
}

const WebChatInterface: React.FC = () => {
  const { roomNumber } = useParams<{ roomNumber: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const TOKEN = searchParams.get('token') || '';
  const ROOM = roomNumber || '';

  const [t, setT] = useState(getTranslation());
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [tokenValid, setTokenValid] = useState<boolean | null>(null);
  const [hasLoaded, setHasLoaded] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<W3CWebSocket | null>(null);
  const reconnectRef = useRef<NodeJS.Timeout | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const checkTokenValidity = useCallback(async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/validate/${ROOM}/?token=${TOKEN}`);
      const data = await res.json();
      if (data.valid === true) {
        setTokenValid(true);
      } else {
        setTokenValid(false);
        navigate('/404', { replace: true });
      }
    } catch {
      setTokenValid(false);
      navigate('/404', { replace: true });
    }
  }, [ROOM, TOKEN, navigate]);

  const fetchRoomLanguage = useCallback(async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/room-info/${ROOM}/?token=${TOKEN}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data: RoomInfo = await res.json();

      if (!data.language) {
        navigate(`/language-select?room=${ROOM}&token=${TOKEN}`, { replace: true });
        return;
      }

      localStorage.setItem('chat_language', data.language);
      setT(getTranslation());
    } catch (err) {
      console.error('❌ Xatolik: room info', err);
      navigate('/404', { replace: true });
    }
  }, [ROOM, TOKEN, navigate]);

  const loadHistory = useCallback(async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/messages/${ROOM}/`);
      const data = await res.json();

      const history: Message[] = data.map((m: any) => ({
        id: uuidv4(),
        uuid: m.uuid,
        text: m.text,
        sender: m.is_from_customer ? 'me' : 'other',
        time: new Date(m.sent_at).toLocaleTimeString('uz-UZ', {
          hour: '2-digit',
          minute: '2-digit',
        }),
        status: 'delivered',
      }));

      setMessages(history);
      setHasLoaded(true);
    } catch (e) {
      console.error('❌ Tarixni olishda xato:', e);
    }
  }, [ROOM]);

  const connectWS = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.close(1000, 'Reconnect');
    }

    const ws = new W3CWebSocket(`${WS_URL}/ws/chat/${ROOM}/?token=${TOKEN}`);
    wsRef.current = ws;
    setIsConnected(false);

    ws.onopen = () => {
      setIsConnected(true);
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
    };

    ws.onmessage = (message) => {
      try {
        const data = JSON.parse(message.data.toString());

        const incoming: Message = {
          id: uuidv4(),
          uuid: data.uuid,
          text: data.message,
          sender: data.sender === 'bot' ? 'other' : 'me',
          time: new Date().toLocaleTimeString('uz-UZ', {
            hour: '2-digit',
            minute: '2-digit',
          }),
          status: 'delivered',
        };

        setMessages(prev => {
          const already = prev.some(m => m.uuid === incoming.uuid);
          return already ? prev : [...prev, incoming];
        });
      } catch (e) {
        console.error('❌ WS parsing xatosi:', e);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      reconnectRef.current = setTimeout(connectWS, 3000);
    };

    ws.onerror = () => {
      setIsConnected(false);
    };
  }, [ROOM, TOKEN]);

  useEffect(() => {
    checkTokenValidity();
  }, [checkTokenValidity]);

  useEffect(() => {
    if (tokenValid) {
      fetchRoomLanguage();
      loadHistory();
      connectWS();
    }

    return () => {
      if (wsRef.current) wsRef.current.close(1000, 'Unmount');
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
    };
  }, [tokenValid, fetchRoomLanguage, loadHistory, connectWS]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    const text = newMessage.trim();
    if (!text || !isConnected) return;

    const uuid = uuidv4();
    const outgoing: Message = {
      id: uuidv4(),
      uuid,
      text,
      sender: 'me',
      time: new Date().toLocaleTimeString('uz-UZ', {
        hour: '2-digit',
        minute: '2-digit',
      }),
      status: 'pending',
    };

    setMessages(prev => [...prev, outgoing]);
    setNewMessage('');

    try {
      const res = await fetch(`${BACKEND_URL}/api/messages/${ROOM}/send/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, uuid }),
      });
      if (!res.ok) throw new Error('Send error');
    } catch {
      setMessages(prev =>
        prev.map(m => (m.uuid === uuid ? { ...m, status: 'failed' } : m))
      );
    }
  };

  const handleKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (!hasLoaded) {
    return <div className="loading">⏳ Yuklanmoqda...</div>;
  }

  return (
    <div className="chat-wrapper">
      <div className="chat-header">
        <img src="/images/arzum.png" alt="Bot Avatar" className="avatar-img" />
        <div className="title">{t.hotel}</div>
        <div className="status">{isConnected ? t.online : t.connecting}</div>
      </div>

      <div className="chat-body">
        {messages.map((msg) => (
          <div key={msg.id} className={`message-row ${msg.sender === 'me' ? 'me' : 'other'}`}>
            {msg.sender === 'other' && (
              <div className="avatar">
                <img src="/images/arzum.png" alt="Bot" className="avatar-img" />
              </div>
            )}
            <div className="message">
              <div className="text">{msg.text}</div>
              <div className="time">{msg.time}</div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input">
        <textarea
          placeholder={t.placeholder}
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          onKeyDown={handleKey}
        />
        <button onClick={sendMessage} disabled={!newMessage.trim() || !isConnected}>
          <Send size={18} />
        </button>
      </div>
    </div>
  );
};

export default WebChatInterface;



























