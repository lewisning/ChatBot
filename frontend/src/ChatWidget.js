import React, { useState } from 'react';
import './ChatWidget.css';
import axios from 'axios';
import avatar1 from './assets/avatars/avatar1.png';
import avatar2 from './assets/avatars/avatar2.png';
import avatar3 from './assets/avatars/avatar3.png';
import avatar4 from './assets/avatars/avatar4.png';


function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [userInfo, setUserInfo] = useState({
    name: 'SMARTIE',
    avatar: 'chat-icon.png',
  });
  const [isEditingName, setIsEditingName] = useState(false);
  const [showAvatarPopup, setShowAvatarPopup] = useState(false);
  const [message, setMessage] = useState('');
  const [chatLog, setChatLog] = useState([]);

  const toggleChat = () => setIsOpen(!isOpen);

  const sendMessage = async () => {
    if (!message.trim()) return;

    const userMessage = { sender: 'user', text: message };
    setChatLog([...chatLog, userMessage]);

    try {
      const res = await axios.post('http://localhost:8000/api/chat/', { message });
      const botMessage = { sender: 'bot', text: res.data.reply };
      setChatLog(prev => [...prev, botMessage]);
    } catch (err) {
      console.error(err);
    }

    setMessage('');
  };

  return (
    <div className="chat-container">
      {/* 聊天图标按钮（始终存在） */}
      <button className="chat-toggle-button" onClick={toggleChat}>
        <img src="/chat-icon.png" alt="chat icon" className="chat-icon-image" />
      </button>

      {/* 聊天窗口 */}
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
                  if (e.key === 'Enter') {
                    setIsEditingName(false);
                  }
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
              <div key={idx} className={`chat-message ${msg.sender}`}>
                {msg.sender === 'user' && <strong>{userInfo.name}: </strong>}
                {msg.text}
              </div>
            ))}
          </div>

          <div className="chat-footer">
            <input
              type="text"
              value={message}
              onChange={e => setMessage(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter') {
                  sendMessage();
                }
              }}
              placeholder="Ask me anything..."
            />
            <button onClick={sendMessage}>➤</button>
          </div>
        </div>
      )}

      {/* 头像选择弹窗 */}
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
