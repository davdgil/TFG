"use client";

import React, { useState } from "react";
import "./ChatPanel.css";

const suggestions = [
  "Muéstrame las categorías disponibles",
  "Top ventas de productos vendidos en 2017",
  "Ventas por estado",
  "Dame estadísticas de la base de datos",
];

function ChatPanel({ messages, onSendMessage }) {
  const [input, setInput] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    onSendMessage(input);
    setInput("");
  };

  const handleSuggestion = (text) => {
    onSendMessage(text);
  };

  return (
    <div className="chat-panel">
      <div className="chat-panel__top">
        <div className="chat-panel__suggestions-box">
          <div className="chat-panel__suggestions-title">Consultas sugeridas</div>
          <div className="chat-panel__suggestions">
            {suggestions.map((item) => (
              <button
                key={item}
                type="button"
                className="chat-panel__suggestion-button"
                onClick={() => handleSuggestion(item)}
              >
                {item}
              </button>
            ))}
          </div>
        </div>

        <div className="chat-panel__messages">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`chat-panel__message ${
                msg.role === "user"
                  ? "chat-panel__message--user"
                  : "chat-panel__message--assistant"
              }`}
            >
              <strong>{msg.role === "user" ? "Tú" : "Asistente"}:</strong>
              <div className="chat-panel__message-text">{msg.content}</div>
            </div>
          ))}
        </div>
      </div>

      <form className="chat-panel__form" onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Escribe una consulta..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="chat-panel__input"
        />
        <button type="submit" className="chat-panel__button">
          Enviar
        </button>
      </form>
    </div>
  );
}

export default ChatPanel;