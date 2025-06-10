import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './MenuBar.css';

const MenuBar = ({
  onClearChat,
  onThemeChange,
  onFontSizeChange,
  currentTheme = 'nestle',
  currentFontSize = 'medium'
}) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [showClearConfirm, setShowClearConfirm] = useState(false);

  const themes = [
    {
      id: 'nestle',
      name: 'Nestlé Brand',
      color: '#D71920',
      description: 'Official Nestlé brand colors'
    },
    {
      id: 'dark',
      name: 'Dark Mode',
      color: '#2C2C2C',
      description: 'Easy on the eyes'
    },
    {
      id: 'blue',
      name: 'Ocean Blue',
      color: '#1E88E5',
      description: 'Calm and refreshing'
    },
    {
      id: 'green',
      name: 'Nature Green',
      color: '#43A047',
      description: 'Fresh and natural'
    },
    {
      id: 'purple',
      name: 'Royal Purple',
      color: '#8E24AA',
      description: 'Creative and elegant'
    },
    {
      id: 'orange',
      name: 'Warm Orange',
      color: '#FB8C00',
      description: 'Energetic and friendly'
    }
  ];

  const fontSizes = [
    {
      id: 'small',
      name: 'Small',
      size: '12px',
      description: 'Compact text'
    },
    {
      id: 'medium',
      name: 'Medium',
      size: '14px',
      description: 'Standard size'
    },
    {
      id: 'large',
      name: 'Large',
      size: '16px',
      description: 'Easy to read'
    },
    {
      id: 'extra-large',
      name: 'Extra Large',
      size: '18px',
      description: 'Maximum readability'
    }
  ];

  const handleClearChat = () => {
    setShowClearConfirm(true);
  };

  const confirmClearChat = () => {
    onClearChat();
    setShowClearConfirm(false);
    setIsMenuOpen(false);
  };

  const cancelClearChat = () => {
    setShowClearConfirm(false);
  };

  const handleThemeChange = (themeId) => {
    onThemeChange(themeId);
    if (themeId === 'nestle') {
      document.documentElement.style.setProperty('--brand-primary', '#D71920');
      document.documentElement.style.setProperty('--brand-secondary', '#8B4513');
    }
  };

  return (
    <div className="menu-bar-container">
      <button
        className="menu-toggle-button"
        onClick={() => setIsMenuOpen(!isMenuOpen)}
        title="Settings Menu"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12,15.5A3.5,3.5 0 0,1 8.5,12A3.5,3.5 0 0,1 12,8.5A3.5,3.5 0 0,1 15.5,12A3.5,3.5 0 0,1 12,15.5M19.43,12.97C19.47,12.65 19.5,12.33 19.5,12C19.5,11.67 19.47,11.34 19.43,11.03L21.54,9.37C21.73,9.22 21.78,8.95 21.66,8.73L19.66,5.27C19.54,5.05 19.27,4.97 19.05,5.05L16.56,6.05C16.04,5.65 15.48,5.32 14.87,5.07L14.5,2.42C14.46,2.18 14.25,2 14,2H10C9.75,2 9.54,2.18 9.5,2.42L9.13,5.07C8.52,5.32 7.96,5.66 7.44,6.05L4.95,5.05C4.73,4.96 4.46,5.05 4.34,5.27L2.34,8.73C2.21,8.95 2.27,9.22 2.46,9.37L4.57,11.03C4.53,11.34 4.5,11.67 4.5,12C4.5,12.33 4.53,12.65 4.57,12.97L2.46,14.63C2.27,14.78 2.21,15.05 2.34,15.27L4.34,18.73C4.46,18.95 4.73,19.03 4.95,18.95L7.44,17.95C7.96,18.35 8.52,18.68 9.13,18.93L9.5,21.58C9.54,21.82 9.75,22 10,22H14C14.25,22 14.46,21.82 14.5,21.58L14.87,18.93C15.48,18.68 16.04,18.34 16.56,17.95L19.05,18.95C19.27,19.04 19.54,18.95 19.66,18.73L21.66,15.27C21.78,15.05 21.73,14.78 21.54,14.63L19.43,12.97Z" />
        </svg>
      </button>

      <AnimatePresence>
        {isMenuOpen && (
          <motion.div
            className="menu-panel"
            initial={{ opacity: 0, scale: 0.95, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -10 }}
            transition={{ duration: 0.2 }}
          >
            <div className="menu-header">
              <div className="menu-header-content">
                <div className="menu-logo">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4M12,6A6,6 0 0,0 6,12A6,6 0 0,0 12,18A6,6 0 0,0 18,12A6,6 0 0,0 12,6M12,8A4,4 0 0,1 16,12A4,4 0 0,1 12,16A4,4 0 0,1 8,12A4,4 0 0,1 12,8Z" />
                  </svg>
                  <h3>Settings</h3>
                </div>
                <button
                  className="menu-close-button"
                  onClick={() => setIsMenuOpen(false)}
                  title="Close settings"
                >
                  ×
                </button>
              </div>
              {currentTheme === 'nestle' && (
                <div className="menu-brand-badge">
                  <span>Nestlé Official Theme</span>
                </div>
              )}
            </div>

            <div className="menu-content">
              <div className="menu-section">
                <div className="section-header">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M17.5,12A1.5,1.5 0 0,1 16,10.5A1.5,1.5 0 0,1 17.5,9A1.5,1.5 0 0,1 19,10.5A1.5,1.5 0 0,1 17.5,12M14.5,8A1.5,1.5 0 0,1 13,6.5A1.5,1.5 0 0,1 14.5,5A1.5,1.5 0 0,1 16,6.5A1.5,1.5 0 0,1 14.5,8M9.5,8A1.5,1.5 0 0,1 8,6.5A1.5,1.5 0 0,1 9.5,5A1.5,1.5 0 0,1 11,6.5A1.5,1.5 0 0,1 9.5,8M6.5,12A1.5,1.5 0 0,1 5,10.5A1.5,1.5 0 0,1 6.5,9A1.5,1.5 0 0,1 8,10.5A1.5,1.5 0 0,1 6.5,12M12,3A9,9 0 0,0 3,12A9,9 0 0,0 12,21A9,9 0 0,0 21,12A9,9 0 0,0 12,3M12,19A7,7 0 0,1 5,12A7,7 0 0,1 12,5A7,7 0 0,1 19,12A7,7 0 0,1 12,19Z" />
                  </svg>
                  <h4>Theme Colors</h4>
                </div>
                <p className="section-description">Choose your preferred color scheme</p>
                <div className="theme-options">
                  {themes.map(theme => (
                    <div
                      key={theme.id}
                      className="theme-option-wrapper"
                      title={theme.description}
                    >
                      <button
                        className={`theme-option ${currentTheme === theme.id ? 'active' : ''}`}
                        onClick={() => handleThemeChange(theme.id)}
                        data-theme={theme.id}
                        style={{
                          backgroundColor: theme.color,
                          backgroundImage: theme.id === 'dark' ? 'linear-gradient(135deg, #2C2C2C 0%, #1a1a1a 100%)' : 'none'
                        }}
                      >
                        {currentTheme === theme.id && (
                          <motion.svg
                            width="16"
                            height="16"
                            viewBox="0 0 24 24"
                            fill="white"
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            transition={{ type: "spring", stiffness: 500 }}
                          >
                            <path d="M9,20.42L2.79,14.21L5.62,11.38L9,14.77L18.88,4.88L21.71,7.71L9,20.42Z" />
                          </motion.svg>
                        )}
                      </button>
                      <span className="theme-name">{theme.name}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="menu-section">
                <div className="section-header">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M9,4V7H11V9H13V7H15V4H13V2H11V4H9M12,10A6,6 0 0,1 18,16V17A2,2 0 0,1 16,19H8A2,2 0 0,1 6,17V16A6,6 0 0,1 12,10M12,12A4,4 0 0,0 8,16V17H16V16A4,4 0 0,0 12,12Z" />
                  </svg>
                  <h4>Font Size</h4>
                </div>
                <p className="section-description">Adjust text size for better readability</p>
                <div className="font-size-options">
                  {fontSizes.map(fontSize => (
                    <button
                      key={fontSize.id}
                      className={`font-size-option ${currentFontSize === fontSize.id ? 'active' : ''}`}
                      onClick={() => onFontSizeChange(fontSize.id)}
                      style={{ fontSize: fontSize.size }}
                      title={fontSize.description}
                    >
                      <span className="font-size-label">{fontSize.name}</span>
                      <span className="font-size-sample">Aa</span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="menu-section">
                <div className="section-header">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z" />
                  </svg>
                  <h4>Chat History</h4>
                </div>
                <p className="section-description">Manage your conversation data</p>
                <button
                  className="clear-chat-button"
                  onClick={handleClearChat}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z" />
                  </svg>
                  <span>Clear Chat History</span>
                </button>
              </div>

              {currentTheme === 'nestle' && (
                <div className="menu-section nestlé-section">
                  <div className="section-header">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4M11,17H13V11H11M11,9H13V7H11" />
                    </svg>
                    <h4>About Nestlé Theme</h4>
                  </div>
                  <div className="nestlé-info">
                    <p>You're using the official Nestlé brand theme with authentic colors and typography that reflect our commitment to Quality, Caring, and Fun.</p>
                    <div className="brand-colors">
                      <div className="color-swatch" style={{ backgroundColor: '#D71920' }}>
                        <span>Nestlé Red</span>
                      </div>
                      <div className="color-swatch" style={{ backgroundColor: '#8B4513' }}>
                        <span>Nestlé Brown</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div className="menu-section">
                <div className="section-header">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M11,9H13V7H11M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M11,17H13V11H11V17Z" />
                  </svg>
                  <h4>Tips & Features</h4>
                </div>
                <div className="tips-section">
                  <div className="tip-item">
                    <span className="tip-icon">🎤</span>
                    <span className="tip-text">Use voice input for hands-free chatting</span>
                  </div>
                  <div className="tip-item">
                    <span className="tip-icon">📍</span>
                    <span className="tip-text">Allow location access to find nearby stores</span>
                  </div>
                  <div className="tip-item">
                    <span className="tip-icon">🛒</span>
                    <span className="tip-text">Ask "Where can I buy kit kat?" for shopping options</span>
                  </div>
                  <div className="tip-item">
                    <span className="tip-icon">📊</span>
                    <span className="tip-text">Try "How many products do you / does kit kat have?" for statistics</span>
                  </div>
                  <div className="tip-item">
                    <span className="tip-icon">📋</span>
                    <span className="tip-text">Try "Show me the products in table format." for structured layout</span>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showClearConfirm && (
          <motion.div
            className="confirm-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={cancelClearChat}
          >
            <motion.div
              className="confirm-dialog"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              onClick={e => e.stopPropagation()}
            >
              <div className="confirm-header">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="#FF6B6B">
                  <path d="M13,14H11V10H13M13,18H11V16H13M1,21H23L12,2L1,21Z" />
                </svg>
                <h3>Clear Chat History</h3>
              </div>
              <p>Are you sure you want to delete all chat messages? This action cannot be undone.</p>
              <div className="confirm-buttons">
                <button
                  className="cancel-button"
                  onClick={cancelClearChat}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z" />
                  </svg>
                  Cancel
                </button>
                <button
                  className="confirm-button"
                  onClick={confirmClearChat}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z" />
                  </svg>
                  Delete All
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default MenuBar;
