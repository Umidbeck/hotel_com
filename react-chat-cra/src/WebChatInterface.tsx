import React, { useState, useRef, useEffect } from 'react';
import { Send, Smile, Paperclip, MoreVertical, Phone, Video, ArrowLeft } from 'lucide-react';
import './styles.css';
import { w3cwebsocket as W3CWebSocket } from 'websocket';
import { v4 as uuidv4 } from 'uuid';

interface Message {
  id: string;
  uuid: string;
  text: string;
  sender: 'me' | 'other';
  time: string;
}

const ROOM_NUMBER = '101';

const ChatApp: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const clientRef = useRef<W3CWebSocket | null>(null);
  const reconnectRef = useRef<NodeJS.Timeout | null>(null);
  const pendingMessages = useRef<Set<string>>(new Set());

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages]);

  const connectWebSocket = () => {
    const ws = new W3CWebSocket(`ws://localhost:8000/ws/chat/${ROOM_NUMBER}/`);
    clientRef.current = ws;

    ws.onopen = () => {
      console.log('✅ WebSocket ulandi');
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
    };

    ws.onmessage = (message) => {
      try {
        const data = JSON.parse(message.data.toString());
        if (!data.message || !data.uuid) return;

        const newMsg: Message = {
          id: uuidv4(),
          uuid: data.uuid,
          text: data.message,
          sender: data.sender === 'bot' ? 'other' : 'me',
          time: data.time || new Date().toLocaleTimeString('uz-UZ', { hour: '2-digit', minute: '2-digit' }),
        };

        setMessages((prev) => {
          const isDuplicate = prev.some((m) => m.uuid === newMsg.uuid);
          if (isDuplicate) return prev;
          return [...prev, newMsg];
        });

        // yuborilgandan keyin typing holatni o‘chir
        pendingMessages.current.delete(data.uuid);
        setIsTyping(pendingMessages.current.size > 0);
      } catch (e) {
        console.error('Xatolik:', e);
      }
    };

    ws.onclose = () => {
      console.warn('🔁 WebSocket uzildi. Qayta ulanmoqda...');
      reconnectRef.current = setTimeout(connectWebSocket, 5000);
    };

    ws.onerror = (err) => {
      console.error('WebSocket xato:', err);
      ws.close();
      reconnectRef.current = setTimeout(connectWebSocket, 5000);
    };
  };

  useEffect(() => {
    const fetchMessages = async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/messages/${ROOM_NUMBER}/`);
        const data = await res.json();

        const loaded = data.map((msg: any) => ({
          id: uuidv4(),
          uuid: msg.uuid || uuidv4(),
          text: msg.text,
          sender: msg.is_from_customer ? 'me' : 'other',
          time: new Date(msg.sent_at).toLocaleTimeString('uz-UZ', { hour: '2-digit', minute: '2-digit' }),
        }));

        setMessages(loaded);
      } catch (err) {
        console.error('❌ Tarixni olishda xato:', err);
      }
    };

    fetchMessages();
    connectWebSocket();

    return () => {
      if (clientRef.current) clientRef.current.close();
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
    };
  }, []);

  const handleSendMessage = () => {
    if (!newMessage.trim() || !clientRef.current || clientRef.current.readyState !== WebSocket.OPEN) return;

    const uuid = uuidv4();
    const msg = {
      message: newMessage,
      uuid,
    };

    clientRef.current.send(JSON.stringify(msg));
    pendingMessages.current.add(uuid);
    setIsTyping(true);
    setNewMessage('');
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <button className="back-btn"><ArrowLeft size={20} /></button>
        <div className="contact-info">
          <img src="https://images.unsplash.com/photo-1494790108755-2616c964c955?w=45&h=45&fit=crop&crop=face"
            alt="Admin" className="contact-avatar" />
          <div className="contact-details">
            <h3 className="contact-name">Admin</h3>
            <p className="contact-status">Onlayn</p>
          </div>
        </div>
        <div className="header-actions">
          <button className="header-btn"><Phone size={20} /></button>
          <button className="header-btn"><Video size={20} /></button>
          <button className="header-btn"><MoreVertical size={20} /></button>
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
        {isTyping && (
          <div className="typing-indicator">
            <img src="/media/arzum.png" alt="Avatar" className="message-avatar" />
            <div className="typing-dots">
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input">
        <div className="input-container">
          <textarea
            className="message-input"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Xabar yozing..."
            rows={1}
          />
          <div className="input-actions">
            <button className="input-btn"><Paperclip size={20} /></button>
            <button className="input-btn"><Smile size={20} /></button>
          </div>
        </div>
        <button className="send-btn" onClick={handleSendMessage} disabled={!newMessage.trim()}>
          <Send size={20} />
        </button>
      </div>
    </div>
  );
};

export default ChatApp;




