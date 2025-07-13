import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Smile, Paperclip } from 'lucide-react';
import { useParams, useSearchParams } from 'react-router-dom';
import './styles.css';
import { w3cwebsocket as W3CWebSocket } from 'websocket';
import { v4 as uuidv4 } from 'uuid';

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

const WebChatInterface: React.FC = () => {
  const { roomNumber } = useParams<{ roomNumber: string }>();
  const [searchParams] = useSearchParams();
  const TOKEN = searchParams.get('token') || '';
  const ROOM = roomNumber || 'unknown';

  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<W3CWebSocket | null>(null);
  const reconnectRef = useRef<NodeJS.Timeout | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

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

  const connectWS = useCallback(() => {
    const ws = new W3CWebSocket(`${WS_URL}/ws/chat/${ROOM}/?token=${TOKEN}`);
    wsRef.current = ws;
    setIsConnected(false);

    ws.onopen = () => {
      console.log('✅ WS ulandi');
      setIsConnected(true);
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
    };

    ws.onmessage = (msg) => {
      try {
        const data = JSON.parse(msg.data.toString());

        // ✅ Sana formatini tekshirish
        let timeFormatted = '';
        try {
          const rawTime = data.time || data.sent_at || data.created_at;
          const parsed = new Date(rawTime);
          if (!isNaN(parsed.getTime())) {
            timeFormatted = parsed.toLocaleTimeString('uz-UZ', {
              hour: '2-digit',
              minute: '2-digit',
            });
          } else {
            console.warn('⚠️ Noto‘g‘ri sana:', rawTime);
            timeFormatted = new Date().toLocaleTimeString('uz-UZ', {
              hour: '2-digit',
              minute: '2-digit',
            });
          }
        } catch {
          timeFormatted = new Date().toLocaleTimeString('uz-UZ', {
            hour: '2-digit',
            minute: '2-digit',
          });
        }

        const incoming: Message = {
          id: uuidv4(),
          uuid: data.uuid,
          text: data.message,
          sender: data.sender === 'bot' ? 'other' : 'me',
          time: timeFormatted,
          status: 'delivered',
        };

        setMessages(prev => {
          const exists = prev.some(m => m.uuid === incoming.uuid);
          return exists ? prev : [...prev, incoming];
        });
      } catch (e) {
        console.error('Xatolik:', e);
      }
    };

    ws.onclose = () => {
      console.warn('🔁 WS uzildi');
      setIsConnected(false);
      reconnectRef.current = setTimeout(connectWS, 3000);
    };

    ws.onerror = (err) => {
      console.error('❌ WS xato:', err);
      setIsConnected(false);
    };
  }, [ROOM, TOKEN]);

  useEffect(() => {
    loadHistory();
    connectWS();
    return () => {
      wsRef.current?.close();
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
    };
  }, [loadHistory, connectWS]);

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
    } catch (e) {
      console.error('❌ Yuborishda xato:', e);
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

  return (
    <div className="chat-wrapper">
      {/* Header */}
      <div className="chat-header">
        <img src="/images/arzum.png" alt="Bot Avatar" className="avatar-img" />
        <div className="title">Hotel</div>
        <div className="status">{isConnected ? '🟢 Onlayn' : '🕗 Ulanmoqda...'}</div>
      </div>

      {/* Chat Body */}
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

      {/* Input */}
      <div className="chat-input">
        <textarea
          placeholder="Xabar yozing..."
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








