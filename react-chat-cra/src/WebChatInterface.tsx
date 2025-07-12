import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { Send, ArrowLeft } from 'lucide-react';
import './styles.css';
import { w3cwebsocket as W3CWebSocket } from 'websocket';
import { v4 as uuidv4 } from 'uuid';

// Backend → .env yoki default
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

const ChatApp: React.FC = () => {
  const { roomNumber } = useParams<{ roomNumber: string }>();
  const ROOM = roomNumber || 'default';

  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<W3CWebSocket | null>(null);
  const reconnectRef = useRef<NodeJS.Timeout | null>(null);

  /* ---------- scroll ---------- */
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  /* ---------- tarixni bazadan yuklash ---------- */
  const loadHistory = useCallback(async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/messages/${ROOM}/`);
      if (!res.ok) throw new Error('Network error');
      const data = await res.json();
      const loaded: Message[] = data.map((m: any) => ({
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
      setMessages(loaded);
    } catch (e) {
      console.error('❌ Tarixni olishda xato:', e);
    }
  }, [ROOM]);

  /* ---------- WebSocket ---------- */
  const connectWS = useCallback(() => {
    const ws = new W3CWebSocket(`${WS_URL}/ws/chat/${ROOM}/`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('✅ WS ulandi');
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
    };

    ws.onmessage = (msg) => {
      try {
        const data = JSON.parse(msg.data.toString());
        const incoming: Message = {
          id: uuidv4(),
          uuid: data.uuid,
          text: data.message,
          sender: data.sender === 'bot' ? 'other' : 'me',
          time: new Date(data.time || Date.now()).toLocaleTimeString('uz-UZ', {
            hour: '2-digit',
            minute: '2-digit',
          }),
          status: 'delivered',
        };

        setMessages((prev) => {
          if (prev.some((m) => m.uuid === incoming.uuid)) return prev; // Duplicate oldini olish
          return [...prev, incoming];
        });
      } catch (e) {
        console.error('Xatolik:', e);
      }
    };

    ws.onclose = () => {
      console.warn('🔁 WS uzildi, reconnect qilinmoqda...');
      reconnectRef.current = setTimeout(connectWS, 5000);
    };

    ws.onerror = (err) => {
      console.error('❌ WS xato:', err);
      ws.close();
    };
  }, [ROOM]);

  useEffect(() => {
    loadHistory();
    connectWS();
    return () => {
      wsRef.current?.close();
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
    };
  }, [loadHistory, connectWS]);

  /* ---------- send message ---------- */
  const sendMessage = () => {
    const text = newMessage.trim();
    if (!text || !wsRef.current) return;

    const uuid = uuidv4();
    wsRef.current.send(JSON.stringify({
      message: text,
      uuid,
      sender: 'me', // ✅ MUHIM: bu bo‘lmasa bot yubormaydi
      room: ROOM,
    }));

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

    setMessages((prev) => [...prev, outgoing]);
    setNewMessage('');
    scrollToBottom();
  };

  /* ---------- keyDown ---------- */
  const handleKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  /* ---------- UI ---------- */
  return (
    <div className="chat-container">
      <div className="chat-header">
        <button className="back-btn">
          <ArrowLeft size={20} />
        </button>
        <div className="contact-info">
          <img
            src="https://images.unsplash.com/photo-1494790108755-2616c964c955?w=45&h=45&fit=crop&crop=face"
            alt="Admin"
            className="contact-avatar"
          />
          <div className="contact-details">
            <h3 className="contact-name">Admin</h3>
            <p className="contact-status">Onlayn</p>
          </div>
        </div>
      </div>

      <div className="messages-container">
        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.sender}`}>
            <div className="message-content">
              <div className="message-wrapper">
                <div className="message-bubble">{msg.text}</div>
                <div className="message-time">{msg.time}</div>
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input">
        <textarea
          className="message-input"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          onKeyPress={handleKey}
          placeholder="Xabar yozing..."
          rows={1}
        />
        <button className="send-btn" onClick={sendMessage} disabled={!newMessage.trim()}>
          <Send size={20} />
        </button>
      </div>
    </div>
  );
};

export default ChatApp;





