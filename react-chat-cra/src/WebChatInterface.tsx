import React, {useState, useRef, useEffect} from 'react';
import {Send, Smile, Paperclip, MoreVertical, Phone, Video, Search, ArrowLeft} from 'lucide-react';
import './styles.css';
import {w3cwebsocket as W3CWebSocket} from 'websocket';

interface Message {
    id: number;
    text: string;
    sender: 'me' | 'other';
    time: string;
    avatar?: string;
}

const ChatApp: React.FC = () => {
    const savedMessages = localStorage.getItem('chatMessages');
    const [messages, setMessages] = useState<Message[]>(
        savedMessages ? JSON.parse(savedMessages) : []
    );
    const [newMessage, setNewMessage] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const clientRef = useRef<W3CWebSocket | null>(null);

    useEffect(() => {
        const client = new W3CWebSocket('ws://localhost:8000/ws/chat/101/');
        clientRef.current = client;

        client.onopen = () => {
            console.log('WebSocket ulanildi');
        };

        client.onmessage = (message) => {
            try {
                const data = JSON.parse(message.data.toString());

                if (!data.message) return;

                setMessages((prevMessages) => {
                    // Oldin kiritilgan xabar bormi? Tekshiramiz
                    const alreadyExists = prevMessages.some(
                        (msg) => msg.text === data.message && msg.sender === (data.sender === 'bot' ? 'other' : data.sender)
                    );

                    if (alreadyExists) return prevMessages;

                    const newMsg: Message = {
                        id: Date.now(),
                        text: data.message,
                        sender: data.sender === 'bot' ? 'other' : (data.sender === 'me' ? 'me' : 'other'),
                        time: data.time || new Date().toLocaleTimeString('uz-UZ', {hour: '2-digit', minute: '2-digit'}),
                    };

                    const updated = [...prevMessages, newMsg];
                    localStorage.setItem('chatMessages', JSON.stringify(updated));
                    return updated;
                });

                setIsTyping(false);
            } catch (error) {
                console.error("WebSocket xabarini o'qishda xato:", error);
            }
        };


        client.onerror = (error) => {
            console.error('WebSocket xatosi:', error);
        };

        client.onclose = () => {
            console.log('WebSocket uzildi, qayta ulanish urinilmoqda...');
        };

        return () => {
            if (clientRef.current) {
                clientRef.current.close();
            }
        };
    }, []);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({behavior: 'smooth'});
    };

    useEffect(() => {
        scrollToBottom();
        localStorage.setItem('chatMessages', JSON.stringify(messages));
    }, [messages]);

    const handleSendMessage = () => {
        if (!newMessage.trim() || !clientRef.current) return;

        const message: Message = {
            id: Date.now(),
            text: newMessage,
            sender: 'me',
            time: new Date().toLocaleTimeString('uz-UZ', {hour: '2-digit', minute: '2-digit'}),
        };
        setMessages((prev) => {
            const updatedMessages = [...prev, message];
            localStorage.setItem('chatMessages', JSON.stringify(updatedMessages));
            return updatedMessages;
        });
        setNewMessage('');
        setIsTyping(true);

        if (clientRef.current.readyState === WebSocket.OPEN) {
            clientRef.current.send(JSON.stringify({message: message.text, sender: 'me'}));
        } else {
            console.error('WebSocket tayyor emas');
        }
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
                <button className="back-btn"><ArrowLeft size={20}/></button>
                <div className="contact-info">
                    <img src="https://images.unsplash.com/photo-1494790108755-2616c964c955?w=45&h=45&fit=crop&crop=face"
                         alt="Admin" className="contact-avatar"/>
                    <div className="contact-details">
                        <h3 className="contact-name">Admin</h3>
                        <p className="contact-status">Onlayn</p>
                    </div>
                </div>
                <div className="header-actions">
                    <button className="header-btn"><Phone size={20}/></button>
                    <button className="header-btn"><Video size={20}/></button>
                    <button className="header-btn"><MoreVertical size={20}/></button>
                </div>
            </div>
            <div className="messages-container">
                {messages.map((message) => (
                    <div key={message.id} className={`message ${message.sender}`}>
                        <div className="message-content">
                            {message.sender === 'other'}
                            <div className="message-wrapper">
                                <div className="message-bubble">{message.text}</div>
                                <div className="message-time">{message.time}</div>
                            </div>
                        </div>
                    </div>
                ))}
                {isTyping && (
                    <div className="typing-indicator">
                        <img src="/media/arzum.png" alt="Avatar" className="message-avatar"/>
                        <div className="typing-dots">
                            <div className="typing-dot"></div>
                            <div className="typing-dot"></div>
                            <div className="typing-dot"></div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef}/>
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
                        <button className="input-btn"><Paperclip size={20}/></button>
                        <button className="input-btn"><Smile size={20}/></button>
                    </div>
                </div>
                <button className="send-btn" onClick={handleSendMessage} disabled={!newMessage.trim()}><Send size={20}/>
                </button>
            </div>
        </div>
    );
};

export default ChatApp;