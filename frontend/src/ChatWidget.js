import React, { useState, useEffect } from 'react';
import './ChatWidget.css';
import axios from 'axios';
import avatar1 from './assets/avatars/avatar1.png';
import avatar2 from './assets/avatars/avatar2.png';
import avatar3 from './assets/avatars/avatar3.png';
import avatar4 from './assets/avatars/avatar4.png';

function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);

  const [userInfo, setUserInfo] = useState(() => {
    const saved = localStorage.getItem('userInfo');
    return saved ? JSON.parse(saved) : { name: 'SMARTIE', avatar: 'chat-icon.png' };
  });

  const [isEditingName, setIsEditingName] = useState(false);
  const [showAvatarPopup, setShowAvatarPopup] = useState(false);
  const [message, setMessage] = useState('');

  const [chatLog, setChatLog] = useState(() => {
    const saved = localStorage.getItem('chatLog');
    return saved ? JSON.parse(saved) : [];
  });

  const [countdown, setCountdown] = useState(() => {
    const saved = localStorage.getItem('countdownData');
    if (saved) {
      const { expiresAt } = JSON.parse(saved);
      const remaining = Math.floor((new Date(expiresAt) - new Date()) / 1000);
      return remaining > 0 ? remaining : 0;
    }
    return 0;
  });

  useEffect(() => {
    localStorage.setItem('userInfo', JSON.stringify(userInfo));
  }, [userInfo]);

  useEffect(() => {
    localStorage.setItem('chatLog', JSON.stringify(chatLog));
  }, [chatLog]);

  useEffect(() => {
    if (countdown > 0) {
      const expiresAt = new Date(new Date().getTime() + countdown * 1000);
      localStorage.setItem('countdownData', JSON.stringify({ expiresAt }));
    } else {
      localStorage.removeItem('countdownData');
    }
  }, [countdown]);

  useEffect(() => {
    if (countdown <= 0) return;
    const timer = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [countdown]);

  useEffect(() => {
    if (isOpen) {
      const welcome = {
        sender: 'bot',
        text: `Hi I'm ${userInfo.name}! Your personal MadeWithNestle assistant.\nAsk me anything, and I'll try my best to help!`,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setChatLog([welcome]);
    }
  }, [isOpen, userInfo.name, chatLog]);

  const toggleChat = () => {
    setIsOpen(!isOpen);
  };

  const sendMessage = async () => {
    if (!message.trim() || countdown > 0) return;

    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const userMessage = { sender: 'user', text: message, time: now };
    setChatLog(prev => [...prev, userMessage]);

    const thinkingMessage = { sender: 'bot', text: 'Thinking...', time: now };
    setChatLog(prev => [...prev, thinkingMessage]);

    setMessage('');
    setCountdown(60);

    try {
      const res = await axios.post('http://localhost:8000/chat/', { message });
      const botMessage = { sender: 'bot', text: res.data.reply, time: now };
      setChatLog(prev => {
        const newLog = [...prev];
        newLog[newLog.length - 1] = botMessage;
        return newLog;
      });
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="chat-container">
      <button className="chat-toggle-button" onClick={toggleChat}>
        <img src="/chat-icon.png" alt="chat icon" className="chat-icon-image" />
      </button>

      {isOpen && (
        <div className="chat-popup">
          <div className="chat-header">
            <img
              src={userInfo.avatar}
              className="user-avatar"
              alt="avatar"
              onClick={() => setShowAvatarPopup(true)}
              title="Click to change avatar"
            />
            {isEditingName ? (
              <input
                type="text"
                value={userInfo.name}
                onChange={(e) => setUserInfo({ ...userInfo, name: e.target.value })}
                onBlur={() => setIsEditingName(false)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') setIsEditingName(false);
                }}
                className="username-input"
                autoFocus
              />
            ) : (
              <span
                className="username"
                onDoubleClick={() => setIsEditingName(true)}
                title="Double click to edit"
              >
                {userInfo.name}
              </span>
            )}
            <button onClick={toggleChat}>✖</button>
          </div>

          <div className="chat-body">
            {chatLog.map((msg, idx) => (
              <div key={idx} className={`chat-message-row ${msg.sender}`}>
                <div className="chat-bubble">
                  <div className="chat-text">{msg.text}</div>
                  <div className="chat-time">{msg.time}</div>
                </div>
              </div>
            ))}
          </div>

          <div className="chat-footer">
            <input
              type="text"
              value={message}
              disabled={countdown > 0}
              onChange={e => setMessage(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter') sendMessage();
              }}
              placeholder={countdown > 0 ? `Please wait... ${countdown}s` : 'Ask me anything...'}
            />
            <button onClick={sendMessage} disabled={countdown > 0}>➤</button>
          </div>
        </div>
      )}

      {showAvatarPopup && (
        <div className="avatar-popup">
          <p>Choose your avatar:</p>
          <div className="avatar-options">
            {[avatar1, avatar2, avatar3, avatar4].map((img, idx) => (
              <img
                key={idx}
                src={img}
                alt={`avatar-${idx}`}
                className={`avatar-pick ${userInfo.avatar === img ? 'selected' : ''}`}
                onClick={() => {
                  setUserInfo({ ...userInfo, avatar: img });
                  setShowAvatarPopup(false);
                }}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default ChatWidget;
