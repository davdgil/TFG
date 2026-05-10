"use client";

import React, { useState } from "react";
import "./page.css";
import ChatPanel from "./components/ChatPanel";
import ResultsPanel from "./components/ResultsPanel";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
const REQUEST_TIMEOUT_MS = 25000;
const LOADING_MESSAGE = "Estoy analizando la consulta...";

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
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = async (input) => {
    if (!input.trim() || isLoading) return;

    const userMessage = { role: "user", content: input };
    const loadingMessage = {
      role: "assistant",
      content: LOADING_MESSAGE,
      loading: true,
    };
    const pendingMessages = [...messages, userMessage, loadingMessage];
    setMessages(pendingMessages);
    setIsLoading(true);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: input }),
        signal: controller.signal,
      });

      if (!res.ok) {
        const errorBody = await res.json().catch(() => null);
        const detail = errorBody?.detail || `Backend error: ${res.status}`;
        throw new Error(detail);
      }

      const apiResponse = await res.json();
      const assistantMessage = apiResponse.message || "No se ha podido generar una respuesta.";

      setMessages([
        ...messages,
        userMessage,
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
      const errorMessage =
        error?.name === "AbortError"
          ? "La consulta ha tardado demasiado y se ha cancelado. Prueba con una consulta mas concreta."
          : error?.message || "No se ha podido completar la consulta en este momento.";

      setMessages([
        ...messages,
        userMessage,
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
    } finally {
      clearTimeout(timeoutId);
      setIsLoading(false);
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
          <ChatPanel
            messages={messages}
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
          />
        </aside>

        <section className="page-results">
          <ResultsPanel result={result} />
        </section>
      </main>
    </div>
  );
}
