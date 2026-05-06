"use client";

import React, { useState } from "react";
import "./page.css";
import ChatPanel from "./components/ChatPanel";
import ResultsPanel from "./components/ResultsPanel";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export default function Page() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hola. Preguntame algo sobre clientes, pedidos, productos o ventas y te mostrare resultados y graficos.",
    },
  ]);

  const [result, setResult] = useState({
    message: "Aqui apareceran los resultados analiticos.",
    kpis: {},
    table: [],
    chart: null,
  });

  const handleSendMessage = async (input) => {
    if (!input.trim()) return;

    const newMessages = [...messages, { role: "user", content: input }];
    setMessages(newMessages);

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: input }),
      });

      if (!res.ok) {
        throw new Error(`Backend error: ${res.status}`);
      }

      const apiResponse = await res.json();
      const assistantMessage = apiResponse.message || "Sin respuesta";

      setMessages([
        ...newMessages,
        {
          role: "assistant",
          content: assistantMessage,
        },
      ]);

      setResult({
        message: assistantMessage,
        kpis: apiResponse.kpis || {},
        table: apiResponse.table || [],
        chart: apiResponse.chart || null,
      });
    } catch (error) {
      const errorMessage = "Hubo un error al conectar con el backend.";

      setMessages([
        ...newMessages,
        {
          role: "assistant",
          content: errorMessage,
        },
      ]);

      setResult({
        message: errorMessage,
        kpis: {},
        table: [],
        chart: null,
      });
    }
  };

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Asistente Analitico con MCP</h1>
          <p>Consulta datos de clientes, pedidos, productos y ventas en lenguaje natural</p>
        </div>
      </header>

      <main className="page-main">
        <aside className="page-sidebar">
          <ChatPanel messages={messages} onSendMessage={handleSendMessage} />
        </aside>

        <section className="page-results">
          <ResultsPanel result={result} />
        </section>
      </main>
    </div>
  );
}
