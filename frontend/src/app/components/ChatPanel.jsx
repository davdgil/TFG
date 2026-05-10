"use client";

import React, { useState } from "react";
import "./ChatPanel.css";

const suggestions = [
  "Muestrame la evolucion anual de las ventas",
  "Cuales son las categorias con mas productos",
  "Cuales son los 15 productos con mas ventas en 2017",
  "Que clientes generan mas facturacion acumulada",
  "Analiza el coste de envio por estado",
];

function formatMessage(content) {
  if (!content) return [];

  const normalized = content
    .replace(/\r/g, "")
    .replace(/\s+\*\s/g, "\n* ")
    .replace(/ \* /g, "\n* ")
    .replace(/:\s+\*\*/g, ":\n**");

  return normalized
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

function renderInlineText(text) {
  const parts = text.split(/(\*\*.*?\*\*)/g).filter(Boolean);

  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={index} className="chat-panel__message-strong">
          {part.slice(2, -2)}
        </strong>
      );
    }

    return <span key={index}>{part}</span>;
  });
}

function ChatPanel({ messages, onSendMessage, isLoading }) {
  const [input, setInput] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSendMessage(input);
    setInput("");
  };

  const handleSuggestion = (text) => {
    if (isLoading) return;
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
                disabled={isLoading}
                onClick={() => handleSuggestion(item)}
              >
                {item}
              </button>
            ))}
          </div>
        </div>

        {isLoading ? (
          <div className="chat-panel__status">Consultando datos...</div>
        ) : null}

        <div className="chat-panel__messages">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`chat-panel__message ${
                msg.role === "user"
                  ? "chat-panel__message--user"
                  : "chat-panel__message--assistant"
              } ${msg.loading ? "chat-panel__message--loading" : ""}`}
            >
              <div className="chat-panel__message-label">
                {msg.role === "user" ? "Tu" : "Asistente"}
              </div>
              <div className="chat-panel__message-text">
                {formatMessage(msg.content).map((line, lineIndex) =>
                  line.startsWith("* ") ? (
                    <div key={lineIndex} className="chat-panel__message-bullet">
                      <span className="chat-panel__message-bullet-mark">-</span>
                      <span>{renderInlineText(line.slice(2))}</span>
                    </div>
                  ) : (
                    <p key={lineIndex} className="chat-panel__message-paragraph">
                      {renderInlineText(line)}
                    </p>
                  )
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      <form className="chat-panel__form" onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder={
            isLoading ? "Esperando respuesta del backend..." : "Escribe una consulta..."
          }
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="chat-panel__input"
          disabled={isLoading}
        />
        <button type="submit" className="chat-panel__button" disabled={isLoading}>
          {isLoading ? "Cargando..." : "Enviar"}
        </button>
      </form>
    </div>
  );
}

export default ChatPanel;
