'use client';

import { useState } from 'react';
import { MessageSquare } from 'lucide-react';
import Sidebar from './components/Sidebar';
import ChatInput from './components/ChatInput';
import ChatMessages from './components/ChatMessages';

export default function Home() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const executeTool = async (tool, args = {}) => {
    try {
      const res = await fetch('/api/mcp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tool, args })
      });
      const data = await res.json();
      return data;
    } catch (error) {
      return { error: error.message };
    }
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    const lowerInput = input.toLowerCase();
    let tool = null;

    if (lowerInput.includes('estadísticas') || lowerInput.includes('stats')) {
      tool = 'get_database_stats';
    } else if (lowerInput.includes('clientes') || lowerInput.includes('customers')) {
      tool = 'get_all_customers';
    } else if (lowerInput.includes('pedidos') || lowerInput.includes('orders')) {
      tool = 'get_all_orders';
    } else if (lowerInput.includes('productos') || lowerInput.includes('products')) {
      tool = 'get_all_products';
    } else if (lowerInput.includes('categorías') || lowerInput.includes('categories')) {
      tool = 'list_categories';
    } else if (lowerInput.includes('ventas por estado') || lowerInput.includes('sales by state')) {
      tool = 'get_sales_by_state';
    } else if (lowerInput.includes('estado pedidos') || lowerInput.includes('order status')) {
      tool = 'count_orders_by_status';
    }

    if (tool) {
      const result = await executeTool(tool, {});
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Ejecutando: ${tool}`,
        data: result.result,
        tool: tool
      }]);
    } else {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Prueba preguntar por: estadísticas, clientes, pedidos, productos, categorías, ventas por estado, o estado de pedidos.'
      }]);
    }

    setLoading(false);
  };

  return (
    <div className="flex h-screen bg-zinc-950">
      <Sidebar onSelectQuery={setInput} />

      <main className="flex-1 flex flex-col">
        <header className="h-14 border-b border-zinc-800 flex items-center px-6">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-zinc-400" />
            Chat con tu base de datos
          </h2>
        </header>

        <ChatMessages messages={messages} loading={loading} />
        <ChatInput value={input} onChange={setInput} onSubmit={sendMessage} loading={loading} />
      </main>
    </div>
  );
}
