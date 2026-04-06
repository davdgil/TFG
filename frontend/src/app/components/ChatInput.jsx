'use client';

import { Send } from 'lucide-react';

export default function ChatInput({ value, onChange, onSubmit, loading }) {
  return (
    <form onSubmit={onSubmit} className="p-4 border-t border-zinc-800">
      <div className="flex gap-2">
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Escribe tu consulta... (ej: estadísticas, clientes, pedidos)"
          className="flex-1 bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-3 text-white placeholder-zinc-500 focus:outline-none focus:border-blue-500"
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-6 py-3 rounded-lg transition-colors"
        >
          <Send className="w-5 h-5" />
        </button>
      </div>
    </form>
  );
}
