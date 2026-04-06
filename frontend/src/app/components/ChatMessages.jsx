'use client';

import { Database, Loader2 } from 'lucide-react';
import DataRenderer from './DataRenderer';

export default function ChatMessages({ messages, loading }) {
  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-4">
      {messages.length === 0 && (
        <div className="text-center text-zinc-500 mt-20">
          <Database className="w-16 h-16 mx-auto mb-4 opacity-20" />
          <p className="text-lg">Pregunta algo sobre tu base de datos</p>
          <p className="text-sm mt-2">Por ejemplo: "estadísticas", "clientes", "ventas por estado"</p>
        </div>
      )}
      
      {messages.map((msg, i) => (
        <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
          <div className={`max-w-[80%] rounded-lg p-4 ${
            msg.role === 'user' 
              ? 'bg-blue-600 text-white' 
              : 'bg-zinc-800 text-zinc-200'
          }`}>
            <p>{msg.content}</p>
            {msg.data && <DataRenderer data={msg.data} tool={msg.tool} />}
          </div>
        </div>
      ))}

      {loading && (
        <div className="flex justify-start">
          <div className="bg-zinc-800 rounded-lg p-4">
            <Loader2 className="w-5 h-5 animate-spin text-zinc-400" />
          </div>
        </div>
      )}
    </div>
  );
}
