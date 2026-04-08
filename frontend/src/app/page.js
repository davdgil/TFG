"use client";

import React, { useState } from "react";
import "./page.css";
import ChatPanel from "./components/ChatPanel";
import ResultsPanel from "./components/ResultsPanel";

export default function Page() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hola. Pregúntame algo sobre clientes, pedidos, productos o ventas y te mostraré resultados y gráficos.",
    },
  ]);

  const [result, setResult] = useState({
    message: "Aquí aparecerán los resultados analíticos.",
    kpis: {},
    table: [],
    chart: null,
  });

  const buildMockResponse = (prompt) => {
    const text = prompt.toLowerCase();

    if (text.includes("2017") || text.includes("top ventas")) {
      return {
        message:
          "En 2017 destacan varios productos con una concentración clara en el top 5.",
        kpis: {
          año: 2017,
          productos_analizados: 84,
          ventas_totales: "452.230 €",
          top_1: "Canon imageCLASS 2200",
        },
        table: [
          { producto: "Canon imageCLASS 2200", ventas: 63210, unidades: 182 },
          { producto: "Fellowes PB500", ventas: 58100, unidades: 171 },
          { producto: "Cisco Smart Phone", ventas: 54120, unidades: 160 },
          { producto: "GBC DocuBind", ventas: 48750, unidades: 149 },
          { producto: "HP LaserJet", ventas: 45100, unidades: 133 },
        ],
        chart: {
          type: "bar",
          title: "Top ventas de productos en 2017",
          data: [
            { name: "Canon", value: 63210 },
            { name: "Fellowes", value: 58100 },
            { name: "Cisco", value: 54120 },
            { name: "GBC", value: 48750 },
            { name: "HP", value: 45100 },
          ],
        },
      };
    }

    if (text.includes("categor")) {
      return {
        message: "Estas son las categorías disponibles del catálogo.",
        kpis: {
          categorias: 6,
          productos: 124,
        },
        table: [
          { categoria: "Technology", productos: 34 },
          { categoria: "Furniture", productos: 26 },
          { categoria: "Office Supplies", productos: 28 },
          { categoria: "Home", productos: 14 },
          { categoria: "Garden", productos: 12 },
          { categoria: "Accessories", productos: 10 },
        ],
        chart: {
          type: "bar",
          title: "Productos por categoría",
          data: [
            { name: "Technology", value: 34 },
            { name: "Furniture", value: 26 },
            { name: "Office", value: 28 },
            { name: "Home", value: 14 },
            { name: "Garden", value: 12 },
            { name: "Accessories", value: 10 },
          ],
        },
      };
    }

    if (text.includes("estado")) {
      return {
        message: "California y Nueva York concentran la mayor parte de las ventas.",
        kpis: {
          estados: 5,
          mejor_estado: "California",
          total_ventas: "1.24 M€",
        },
        table: [
          { estado: "California", ventas: 320000 },
          { estado: "New York", ventas: 250000 },
          { estado: "Texas", ventas: 190000 },
          { estado: "Washington", ventas: 140000 },
          { estado: "Florida", ventas: 120000 },
        ],
        chart: {
          type: "bar",
          title: "Ventas por estado",
          data: [
            { name: "CA", value: 320000 },
            { name: "NY", value: 250000 },
            { name: "TX", value: 190000 },
            { name: "WA", value: 140000 },
            { name: "FL", value: 120000 },
          ],
        },
      };
    }

    return {
      message:
        "He procesado la consulta. Cuando conectes el backend real, aquí verás el resumen, el gráfico y la tabla.",
      kpis: {
        estado: "demo",
      },
      table: [],
      chart: null,
    };
  };

  const handleSendMessage = async (input) => {
  if (!input.trim()) return;

  const newMessages = [...messages, { role: "user", content: input }];
  setMessages(newMessages);

  try {
    const res = await fetch("http://127.0.0.1:8000/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message: input }),
    });

    const apiResponse = await res.json();

    setMessages([
      ...newMessages,
      {
        role: "assistant",
        content: apiResponse.message || "Sin respuesta",
      },
    ]);

    setResult({
      message: apiResponse.message || "Sin respuesta",
      kpis: apiResponse.kpis || {},
      table: apiResponse.table || [],
      chart: apiResponse.chart || null,
    });
  } catch (error) {
    setMessages([
      ...newMessages,
      {
        role: "assistant",
        content: "Hubo un error al conectar con el backend.",
      },
    ]);
  }
};

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Asistente Analítico con MCP</h1>
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