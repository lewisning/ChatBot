import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './MenuBar.css';

const MenuBar = ({
  onClearChat,
  onThemeChange,
  onFontSizeChange,
  currentTheme = 'default',
  currentFontSize = 'medium'
}) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [showClearConfirm, setShowClearConfirm] = useState(false);

  const themes = [
    { id: 'default', name: 'Default', color: '#f3efeb' },
    { id: 'dark', name: 'Dark', color: '#2C2C2C' },
    { id: 'blue', name: 'Blue', color: '#1E88E5' },
    { id: 'green', name: 'Green', color: '#43A047' },
    { id: 'purple', name: 'Purple', color: '#8E24AA' },
    { id: 'orange', name: 'Orange', color: '#FB8C00' }
  ];

  const fontSizes = [
    { id: 'small', name: 'Small', size: '10px' },
    { id: 'medium', name: 'Medium', size: '13px' },
    { id: 'large', name: 'Large', size: '15px' },
    { id: 'extra-large', name: 'Extra Large', size: '18px' }
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

  return (
    <div className="menu-bar-container">
      <button
        className="menu-toggle-button"
        onClick={() => setIsMenuOpen(!isMenuOpen)}
        title="Settings Menu"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12,16A2,2 0 0,1 14,18A2,2 0 0,1 12,20A2,2 0 0,1 10,18A2,2 0 0,1 12,16M12,10A2,2 0 0,1 14,12A2,2 0 0,1 12,14A2,2 0 0,1 10,12A2,2 0 0,1 12,10M12,4A2,2 0 0,1 14,6A2,2 0 0,1 12,8A2,2 0 0,1 10,6A2,2 0 0,1 12,4Z" />
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
              <h3>Settings</h3>
              <button
                className="menu-close-button"
                onClick={() => setIsMenuOpen(false)}
              >
                ×
              </button>
            </div>

            <div className="menu-content">
              <div className="menu-section">
                <h4>Theme Colors</h4>
                <div className="theme-options">
                  {themes.map(theme => (
                    <button
                      key={theme.id}
                      className={`theme-option ${currentTheme === theme.id ? 'active' : ''}`}
                      onClick={() => onThemeChange(theme.id)}
                      style={{ backgroundColor: theme.color }}
                      title={theme.name}
                    >
                      {currentTheme === theme.id && (
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="white">
                          <path d="M9,20.42L2.79,14.21L5.62,11.38L9,14.77L18.88,4.88L21.71,7.71L9,20.42Z" />
                        </svg>
                      )}
                    </button>
                  ))}
                </div>
              </div>

              <div className="menu-section">
                <h4>Font Size</h4>
                <div className="font-size-options">
                  {fontSizes.map(fontSize => (
                    <button
                      key={fontSize.id}
                      className={`font-size-option ${currentFontSize === fontSize.id ? 'active' : ''}`}
                      onClick={() => onFontSizeChange(fontSize.id)}
                      style={{ fontSize: fontSize.size }}
                    >
                      {fontSize.name}
                    </button>
                  ))}
                </div>
              </div>

              <div className="menu-section">
                <h4>Chat History</h4>
                <button
                  className="clear-chat-button"
                  onClick={handleClearChat}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z" />
                  </svg>
                  Clear Chat History
                </button>
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
                <h3>Delete Confirmation</h3>
              </div>
              <p>Do you really want to delete all chats? This action cannot be undone.</p>
              <div className="confirm-buttons">
                <button
                  className="cancel-button"
                  onClick={cancelClearChat}
                >
                  Cancel
                </button>
                <button
                  className="confirm-button"
                  onClick={confirmClearChat}
                >
                  Confirm
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
