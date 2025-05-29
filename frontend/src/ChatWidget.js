import React, { useState, useEffect, useRef } from 'react';
import './ChatWidget.css';
import axios from 'axios';
import { AnimatePresence, motion } from 'framer-motion';
import { getUserLocation } from './geolocation';
import avatar1 from './assets/avatars/avatar1.png';
import avatar2 from './assets/avatars/avatar2.png';
import avatar3 from './assets/avatars/avatar3.png';
import avatar4 from './assets/avatars/avatar4.png';
import ReactMarkdown from 'react-markdown';

function ChatWidget() {
  const bottomRef = useRef(null);
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
  const [isThinking, setIsThinking] = useState(false);

  useEffect(() => {
    document.title = "Nestlé ChatBot";
  }, []);

  // Remove chat messages but keep user info (for debugging purposes)
  useEffect(() => {
    localStorage.removeItem('chatLog');
    localStorage.removeItem('userInfo');
    setChatLog([]);
  }, []);

  useEffect(() => {
    if (isOpen && bottomRef.current) {
      const scrollTimeout = setTimeout(() => {
        bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }, 100);

    return () => clearTimeout(scrollTimeout);
  }
  }, [isOpen]);

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatLog]);

  useEffect(() => {
    localStorage.setItem('userInfo', JSON.stringify(userInfo));
  }, [userInfo]);

  useEffect(() => {
    localStorage.setItem('chatLog', JSON.stringify(chatLog));
  }, [chatLog]);

  useEffect(() => {
    if (isOpen) {
      const welcome = {
        sender: 'bot',
        text: `Hi I'm ${userInfo.name}! Your personal MadeWithNestle assistant.\nAsk me anything, and I'll try my best to help!`,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      if (chatLog.length === 0) {
        setChatLog([welcome]);
      }
    }
  }, [isOpen, userInfo.name, chatLog.length]);

  const toggleChat = () => setIsOpen(!isOpen);

  const sendMessage = async () => {
    if (!message.trim() || isThinking) return;

    setIsThinking(true);

    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const userMessage = { sender: 'user', text: message, time: now };
    setChatLog(prev => [...prev, userMessage]);

    const thinkingMessage = { sender: 'bot', text: 'Thinking...', time: now };
    setChatLog(prev => [...prev, thinkingMessage]);
    setMessage('');

    try {
      let coords = null;

      try {
        coords = await getUserLocation();
      } catch (geoErr) {
        console.warn("User location unavailable:", geoErr);
      }

      const payload = {
        question: message,
        name: userInfo.name,
        ...(coords && {
          latitude: coords.latitude,
          longitude: coords.longitude
        })
      };

      // const res = await axios.post("https://nesbot-czf8e6dzgtbjgsgz.canadacentral-01.azurewebsites.net/chat/", payload);
      const res = await axios.post("http://localhost:8000/chat/", payload);
      const botMessage = {
        sender: 'bot',
        text: res.data.answer,
        time: now,
        refs: res.data.reference || []
      };
      setChatLog(prev => {
        const newLog = [...prev];
        newLog[newLog.length - 1] = botMessage;
        return newLog;
      });
    } catch (err) {
      console.error(err);
      const errorMessage = { sender: 'bot', text: 'Sorry, something went wrong.', time: now };
      setChatLog(prev => {
        const newLog = [...prev];
        newLog[newLog.length - 1] = errorMessage;
        return newLog;
      });
    } finally {
      setIsThinking(false);
    }
  };

  return (
    <div className="chat-container">
      <div
        className="chatbot-button-container"
        onClick={toggleChat}
        onMouseMove={(e) => {
          const rect = e.currentTarget.getBoundingClientRect();
          const x = e.clientX - rect.left - rect.width / 2;
          const y = e.clientY - rect.top - rect.height / 2;

          const rotateX = (-y / rect.height) * 15;
          const rotateY = (x / rect.width) * 15;

          e.currentTarget.querySelector('img').style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
        }}
        onMouseLeave={(e) => {
          e.currentTarget.querySelector('img').style.transform = 'rotateX(0deg) rotateY(0deg)';
        }}
      >
        <img src={"/bot-icon.png"}  alt="chat icon" className="chatbot-button"/>
      </div>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            className="chat-popup"
            initial={{ opacity: 0, y: 100 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 100 }}
            transition={{ duration: 0.3 }}
          >
            <div className={`chat-content ${showAvatarPopup ? 'chat-blurred' : ''}`}>
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
                    onKeyDown={(e) => e.key === 'Enter' && setIsEditingName(false)}
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
                <button onClick={toggleChat} className="chat-close-button">
                  <img src="/close.png" alt="Close" className="chat-close-icon" />
                </button>
              </div>

              <div className="chat-body">
                {chatLog.map((msg, idx) => (
                  <div key={idx} className={`chat-message-block ${msg.sender}`}>
                    <div className="chat-message-row">
                      <div className="chat-bubble">
                        <div className="chat-text">
                          <ReactMarkdown
                            components={{
                              a: ({ node, ...props }) => (
                                <a {...props} target="_blank" rel="noopener noreferrer">
                                  {props.children}
                                </a>
                              ),
                            }}
                          >
                            {msg.text}
                          </ReactMarkdown>
                        </div>
                        <div className="chat-time">{msg.time}</div>
                      </div>
                    </div>
                    {msg.refs && msg.refs.length > 0 && (
                      <div className="chat-references">
                        <strong>References:</strong>
                        {msg.refs.map(ref => (
                          <a
                            key={ref.number}
                            href={ref.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="ref-button"
                          >
                            [{ref.number}]
                          </a>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
                <div ref={bottomRef} />
              </div>

              <div className="chat-footer">
                <div className="chat-input-wrapper">
                  <input
                    type="text"
                    value={message}
                    onChange={e => setMessage(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && sendMessage()}
                    placeholder="Ask me anything..."
                  />
                  <button onClick={sendMessage} disabled={isThinking} className="send-button-wrapper">
                    <img
                      src="/send-icon.png"
                      alt="Send"
                      className={`send-icon ${isThinking ? 'hidden' : 'visible'}`}
                    />
                    <img
                      src="/loading.gif"
                      alt="Thinking"
                      className={`thinking-icon ${isThinking ? 'visible' : 'hidden'}`}
                    />
                  </button>
                </div>
              </div>
            </div>

            {showAvatarPopup && (
              <div className="avatar-overlay-inside" onClick={() => setShowAvatarPopup(false)}>
                <div className="avatar-popup" onClick={e => e.stopPropagation()}>
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
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default ChatWidget;