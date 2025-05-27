import React, { useEffect, useRef } from "react";
import "./ChatToggleButton.css";

const ChatToggleButton = ({ toggleChat }) => {
  const iconRef = useRef(null);

  useEffect(() => {
    const handleMouseMove = (e) => {
      const icon = iconRef.current;
      if (!icon) return;

      const rect = icon.getBoundingClientRect();
      const x = e.clientX - (rect.left + rect.width / 2);
      const y = e.clientY - (rect.top + rect.height / 2);

      const angle = Math.atan2(y, x);
      const degree = angle * (180 / Math.PI);

      icon.style.transform = `rotate(${degree}deg)`;
    };

    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  return (
    <button className="chat-toggle-button" onClick={toggleChat}>
      <div className="chat-icon-container">
        <div ref={iconRef} className="chat-icon-rotatable" />
      </div>
    </button>
  );
};

export default ChatToggleButton;
