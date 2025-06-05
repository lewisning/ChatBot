import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import './ChatWidget.css';
import axios from 'axios';
import { AnimatePresence, motion } from 'framer-motion';
import { getUserLocation } from './geolocation';
import MenuBar from './MenuBar';
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
  const [showWelcome, setShowWelcome] = useState(true);
  const [isFadingOut, setIsFadingOut] = useState(false);
  const [displayedText, setDisplayedText] = useState('');

  // Const for Voice functionality
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [audioLevel, setAudioLevel] = useState(0);
  const [, setIsPlaying] = useState(false);
  const [currentPlayingIndex, setCurrentPlayingIndex] = useState(null);

  const recognitionRef = useRef(null);
  const synthRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const microphoneRef = useRef(null);
  const animationRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const audioRef = useRef(null);
  const [windowSize, setWindowSize] = useState(() => {
    const saved = localStorage.getItem('chatWindowSize');
    return saved || 'normal';
  });

  const fullWelcomeText = useMemo(() =>
    `Hi I'm ${userInfo.name}!\nYour personal MadeWithNestle assistant.\nAsk me anything, and I'll try my best to help!`,
    [userInfo.name]
  );

  const [theme, setTheme] = useState(() => {
    // const saved = localStorage.getItem('chatTheme');
    return 'default';
  });

  const [fontSize, setFontSize] = useState(() => {
    const saved = localStorage.getItem('chatFontSize');
    return saved || 'medium';
  });

  const handleThemeChange = (newTheme) => {
    setTheme(newTheme);
    localStorage.setItem('chatTheme', newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
  };

  const handleFontSizeChange = (newFontSize) => {
    setFontSize(newFontSize);
    localStorage.setItem('chatFontSize', newFontSize);
    document.documentElement.setAttribute('data-font-size', newFontSize);
  };

  const handleWindowSizeChange = (newSize) => {
    setWindowSize(newSize);
    localStorage.setItem('chatWindowSize', newSize);
    document.documentElement.setAttribute('data-window-size', newSize);
  };

  const toggleWindowSize = () => {
    const sizes = ['normal', 'large', 'small'];
    const currentIndex = sizes.indexOf(windowSize);
    const nextIndex = (currentIndex + 1) % sizes.length;
    const newSize = sizes[nextIndex];
    handleWindowSizeChange(newSize);
  };

  const getWindowSizeTitle = () => {
    switch (windowSize) {
      case 'small':
        return 'Current: Small - Click for Normal';
      case 'large':
        return 'Current: Large - Click for Small';
      default:
        return 'Current: Normal - Click for Large';
    }
  };

  const handleClearChat = () => {
    setChatLog([]);
    localStorage.removeItem('chatLog');
    setShowWelcome(true);
    setIsFadingOut(false);
    setDisplayedText('');
    localStorage.removeItem('userInfo');
  };

  const cleanupMediaStream = useCallback(() => {
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => {
        track.stop();
      });
      mediaStreamRef.current = null;
    }
  }, []);

  const closeAudioContext = useCallback(async () => {
    if (audioContextRef.current) {
      try {
        if (audioContextRef.current.state !== 'closed') {
          await audioContextRef.current.close();
        }
      } catch (err) {
        console.warn('AudioContext close error:', err);
      } finally {
        audioContextRef.current = null;
      }
    }
  }, []);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
      setAudioLevel(0);
      cleanupMediaStream();
    }
  }, [cleanupMediaStream]);

  const stopSpeaking = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }

    setIsPlaying(false);
    setCurrentPlayingIndex(null);
  }, []);

  const speakText = useCallback(async (text, messageIndex) => {
    try {
      stopSpeaking();

      const response = await fetch("https://nesbot-czf8e6dzgtbjgsgz.canadacentral-01.azurewebsites.net/tts/generate/", {
      // const response = await fetch("http://localhost:8000/tts/generate/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ text })
      });

      if (!response.ok) {
        throw new Error("Azure TTS failed");
      }

      const audioBlob = await response.blob();
      const audioURL = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioURL);

      audioRef.current = audio;

      setIsPlaying(true);
      setCurrentPlayingIndex(messageIndex);

      audio.onended = () => {
        setIsPlaying(false);
        setCurrentPlayingIndex(null);
        audioRef.current = null;
        URL.revokeObjectURL(audioURL);
      };

      audio.onerror = () => {
        setIsPlaying(false);
        setCurrentPlayingIndex(null);
        audioRef.current = null;
        console.error("Audio playback error");
        URL.revokeObjectURL(audioURL);
      };

      await audio.play();
    } catch (err) {
      console.error("Azure TTS error:", err);
      setIsPlaying(false);
      setCurrentPlayingIndex(null);
      audioRef.current = null;
    }
  }, [stopSpeaking]);

  const handleVoiceSend = useCallback(async (voiceMessage) => {
    if (!voiceMessage.trim() || isThinking) return;

    if (showWelcome) {
      setIsFadingOut(true);
      setTimeout(() => {
        setShowWelcome(false);
        setIsFadingOut(false);
      }, 550);
    }

    setIsThinking(true);

    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const userMessage = { sender: 'user', text: voiceMessage, time: now, isVoice: true };
    const messageDelay = showWelcome ? 500 : 0;

    setTimeout(() => {
      setChatLog(prev => [...prev, userMessage]);
      const thinkingMessage = { sender: 'bot', text: 'Thinking...', time: now };
      setChatLog(prev => [...prev, thinkingMessage]);
    }, messageDelay);

    try {
      let coords = null;
      try {
        coords = await getUserLocation();
      } catch (geoErr) {
        console.warn("User location unavailable:", geoErr);
      }

      const payload = {
        question: voiceMessage,
        name: userInfo.name,
        ...(coords && {
          latitude: coords.latitude,
          longitude: coords.longitude
        }),
        chat_history: chatLog
      };

      const res = await axios.post("https://nesbot-czf8e6dzgtbjgsgz.canadacentral-01.azurewebsites.net/chat/", payload);
      // const res = await axios.post("http://localhost:8000/chat/", payload);
      const botMessage = {
        sender: 'bot',
        text: res.data.answer,
        time: now,
        refs: res.data.sources || [],
        canSpeak: true
      };

      setChatLog(prev => {
        const newLog = [...prev];
        newLog[newLog.length - 1] = botMessage;
        return newLog;
      });

      setTimeout(() => {
        const messageIndex = chatLog.length + 1;
        speakText(res.data.answer, messageIndex);
      }, 500);

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
  }, [isThinking, showWelcome, userInfo.name, chatLog, speakText]);

  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();

      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = 'en-US'; // You can change this to your preferred language

      recognitionRef.current.onresult = (event) => {
        let finalTranscript = '';
        let interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }

        setTranscript(finalTranscript + interimTranscript);

        if (finalTranscript.trim()) {
          setMessage('');
          setTranscript('');
          stopListening();
          setTimeout(() => {
            if (finalTranscript.trim()) {
              handleVoiceSend(finalTranscript.trim());
            }
          }, 100);
        }
      };

      recognitionRef.current.onerror = (event) => {
        console.error('Voice recognition error:', event.error);
        setIsListening(false);
        setTranscript('');
        cleanupMediaStream();
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
        cleanupMediaStream();
      };
    }

    if ('speechSynthesis' in window) {
      synthRef.current = window.speechSynthesis;
    }

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }

      closeAudioContext();

      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      if (synthRef.current) {
        synthRef.current.cancel();
      }
      cleanupMediaStream();
    };
  }, [handleVoiceSend, stopListening, cleanupMediaStream, closeAudioContext]);

  useEffect(() => {
    document.title = "Nestlé ChatBot";
  }, []);

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
    if (isOpen && showWelcome) {
      setDisplayedText('');
      let index = 0;
      let active = true;

      const typeLetter = () => {
        if (!active) return;
        if (index <= fullWelcomeText.length) {
          setDisplayedText(fullWelcomeText.slice(0, index));
          index++;
          setTimeout(typeLetter, 15);
        }
      };

      typeLetter();

      return () => {
        active = false;
      };
    }
  }, [isOpen, showWelcome, fullWelcomeText]);

  useEffect(() => {
    requestAnimationFrame(() => {
      if (bottomRef.current) {
        bottomRef.current.scrollIntoView({ behavior: 'smooth' });
      }
    });
  }, [chatLog]);

  useEffect(() => {
    localStorage.setItem('userInfo', JSON.stringify(userInfo));
  }, [userInfo]);

  useEffect(() => {
    localStorage.setItem('chatLog', JSON.stringify(chatLog));
  }, [chatLog]);

  const setupAudioVisualization = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;

      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      analyserRef.current = audioContextRef.current.createAnalyser();
      microphoneRef.current = audioContextRef.current.createMediaStreamSource(stream);

      analyserRef.current.fftSize = 256;
      microphoneRef.current.connect(analyserRef.current);

      const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);

      const updateAudioLevel = () => {
        if (analyserRef.current && isListening) {
          analyserRef.current.getByteFrequencyData(dataArray);
          const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
          setAudioLevel(average / 255);
          animationRef.current = requestAnimationFrame(updateAudioLevel);
        }
      };

      updateAudioLevel();
    } catch (error) {
      console.error('Unable to access microphone:', error);
      alert('Please allow microphone access to use voice features.');
      setIsListening(false);
    }
  };

  const startListening = () => {
    if (recognitionRef.current && !isThinking) {
      setIsListening(true);
      setTranscript('');
      setMessage('');
      recognitionRef.current.start();
      setupAudioVisualization();
    }
  };

  const toggleChat = () => setIsOpen(!isOpen);

  const sendMessage = async () => {
    if (!message.trim() || isThinking) return;
    if (showWelcome) {
      setIsFadingOut(true);
      setTimeout(() => {
        setShowWelcome(false);
        setIsFadingOut(false);
      }, 550);
    }

    setIsThinking(true);

    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const userMessage = { sender: 'user', text: message, time: now };
    const messageDelay = showWelcome ? 500 : 0;
    setTimeout(() => {
      setChatLog(prev => [...prev, userMessage]);

      const thinkingMessage = { sender: 'bot', text: 'Thinking...', time: now };
      setChatLog(prev => [...prev, thinkingMessage]);
    }, messageDelay);

    const currentMessage = message;
    setMessage('');

    try {
      let coords = null;

      try {
        coords = await getUserLocation();
      } catch (geoErr) {
        console.warn("User location unavailable:", geoErr);
      }

      const payload = {
        question: currentMessage,
        name: userInfo.name,
        ...(coords && {
          latitude: coords.latitude,
          longitude: coords.longitude
        }),
        chat_history: chatLog
      };

      const res = await axios.post("https://nesbot-czf8e6dzgtbjgsgz.canadacentral-01.azurewebsites.net/chat/", payload);
      // const res = await axios.post("http://localhost:8000/chat/", payload);
      const botMessage = {
        sender: 'bot',
        text: res.data.answer,
        time: now,
        refs: res.data.sources || [],
        canSpeak: true
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
        <img src={"/bot-icon.png"} alt="chat icon" className="chatbot-button"/>
      </div>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            className={`chat-popup ${windowSize}`}
            initial={{ opacity: 0, y: 100 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 100 }}
            transition={{ duration: 0.3 }}
            layout
            layoutScroll
          >
            <motion.div className={`chat-content ${showAvatarPopup ? 'chat-blurred' : ''}`} layout transition={{ layout: { duration: 0.3, ease: "easeOut" } }}>
              <motion.div className="chat-window" layout>
                <AnimatePresence mode="wait">
                  {showWelcome ? (
                    <motion.div
                      key="welcome"
                      className="welcome-container"
                      initial={{ opacity: 1, y: 0, scale: 1 }}
                      animate={isFadingOut ? { opacity: 0, y: -40, scale: 0.96 } : { opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: -40, scale: 0.96 }}
                      transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
                    >
                      <img src={userInfo.avatar} alt="avatar" className="welcome-avatar" />
                      <div className="welcome-text">
                        {displayedText.split('\n').map((line, idx) => (
                          <div key={idx}>{line}</div>
                        ))}
                      </div>
                    </motion.div>
                  ) : (
                    <div
                      key="header"
                      className="chat-fade-wrapper fade-chat"
                      initial={{ opacity: 0, y: 30 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -30 }}
                      transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
                    >
                      <motion.div className="chat-header" layout transition={{ layout: { duration: 0.3, ease: "easeOut" } }}>
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

                        <button
                          onClick={toggleWindowSize}
                          className="window-size-button"
                          title={getWindowSizeTitle()}
                        >
                            <img src={"/window-change.png"} alt="Change Window Size" className="window-size-icon" />
                        </button>

                        <MenuBar
                          onClearChat={handleClearChat}
                          onThemeChange={handleThemeChange}
                          onFontSizeChange={handleFontSizeChange}
                          currentTheme={theme}
                          currentFontSize={fontSize}
                        />

                        <button onClick={toggleChat} className="chat-close-button">
                          <img
                            src={theme === 'dark' ? '/close-dark.png' : '/close.png'}
                            alt="Close"
                            className="chat-close-icon"
                          />
                        </button>
                      </motion.div>

                      <motion.div className="chat-body" layout transition={{ layout: { duration: 0.3, ease: "easeOut" } }}>
                        {chatLog.map((msg, idx) => (
                          <div key={idx} className={`chat-message-block ${msg.sender}`}>
                            <div className="chat-message-row">
                              <div className={`chat-bubble ${msg.isVoice ? 'voice-message' : ''} ${currentPlayingIndex === idx ? 'speaking' : ''}`}>
                                <div className="chat-text">
                                  {msg.text === 'Thinking...' ? (
                                    <div className="breathing-indicator">Thinking...</div>
                                  ) : (
                                    <div className="markdown-body">
                                      <ReactMarkdown
                                        components={{
                                          a: ({ node, ...props }) => (
                                            <a {...props} target="_blank" rel="noopener noreferrer">
                                              {props.children}
                                            </a>
                                          ),
                                          img: ({ node, ...props }) => (
                                            <img
                                              {...props}
                                              alt={props.alt}
                                              style={{
                                                display: 'block',
                                                margin: '12px auto',
                                                maxWidth: '80%',
                                                height: 'auto',
                                                borderRadius: '8px'
                                              }}
                                            />
                                          )
                                        }}
                                      >
                                        {msg.text}
                                      </ReactMarkdown>
                                    </div>
                                  )}
                                </div>
                                <div className="chat-time-row">
                                  <div className="chat-time">{msg.time}</div>
                                  {msg.canSpeak && msg.sender === 'bot' && (
                                    <button
                                      onClick={() =>
                                        currentPlayingIndex === idx ? stopSpeaking() : speakText(msg.text, idx)
                                      }
                                      className="voice-play-button"
                                      title={currentPlayingIndex === idx ? "Stop speaking" : "Play voice"}
                                    >
                                      <img
                                        src={currentPlayingIndex === idx ? "/voice-stop.png" : "/play.png"}
                                        alt={currentPlayingIndex === idx ? "Stop" : "Play"}
                                        className="w-5 h-5 object-contain"
                                      />
                                    </button>
                                  )}
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                        <div ref={bottomRef} />
                      </motion.div>
                    </div>
                  )}
                </AnimatePresence>
              </motion.div>

              <div className="chat-footer">
                {isListening && (
                  <div className="voice-status">
                    <div className="voice-visualizer">
                      {[...Array(12)].map((_, i) => (
                        <div
                          key={i}
                          className="voice-bar"
                          style={{
                            height: `${Math.max(4, (audioLevel + Math.random() * 0.3) * 20)}px`,
                            animationDelay: `${i * 100}ms`
                          }}
                        />
                      ))}
                    </div>
                    <div className="voice-status-text">
                      {transcript ? `Recorded: ${transcript}` : 'Recording...'}
                    </div>
                  </div>
                )}

                <div className="chat-input-wrapper">
                  <input
                    type="text"
                    value={message}
                    onChange={e => setMessage(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && sendMessage()}
                    placeholder={isListening ? "Voice input in progress" : "Ask me anything..."}
                    disabled={isListening}
                  />

                  <button
                    onClick={isListening ? stopListening : startListening}
                    disabled={isThinking}
                    className={`
                      relative p-4 rounded-full transition-all duration-300 transform hover:scale-110 shadow-lg
                      ${isListening 
                        ? 'bg-gradient-to-r from-red-500 to-pink-600 text-white animate-pulse' 
                        : 'bg-gradient-to-r from-blue-500 to-purple-600 text-white hover:from-blue-600 hover:to-purple-700'
                      }
                      ${isThinking ? 'cursor-not-allowed opacity-50' : ''}
                    `}
                    title={isListening ? "Stop listening" : "Start voice input"}
                  >
                    <img
                      src={isListening ? "/voice-stop.png" : "/voice-start.png"}
                      alt={isListening ? "Stop" : "Mic"}
                      className="w-5 h-5"
                    />
                    {isListening && (
                      <div className="absolute inset-0 rounded-full bg-red-400 animate-ping opacity-30" />
                    )}
                  </button>


                  <button onClick={sendMessage} disabled={isThinking || isListening} className="send-button-wrapper">
                    <img
                      src="/send-icon.png"
                      alt="Send"
                      className={`send-icon ${isThinking || isListening ? 'hidden' : 'visible'}`}
                    />
                    <img
                      src="/loading.gif"
                      alt="Thinking"
                      className={`thinking-icon ${isThinking ? 'visible' : 'hidden'}`}
                    />
                  </button>
                </div>
              </div>
            </motion.div>

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
