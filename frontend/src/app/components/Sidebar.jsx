'use client';

import { Database, Users, Package, ShoppingCart, BarChart3 } from 'lucide-react';

const menuItems = [
  { icon: BarChart3, label: 'Estadísticas', query: 'estadísticas' },
  { icon: Users, label: 'Clientes', query: 'clientes' },
  { icon: ShoppingCart, label: 'Pedidos', query: 'pedidos' },
  { icon: Package, label: 'Productos', query: 'productos' },
  { icon: BarChart3, label: 'Categorías', query: 'categorías' },
  { icon: BarChart3, label: 'Ventas por estado', query: 'ventas por estado' },
];

export default function Sidebar({ onSelectQuery }) {
  return (
    <aside className="w-64 bg-zinc-900 border-r border-zinc-800 flex flex-col">
      <div className="p-4 border-b border-zinc-800">
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <Database className="w-6 h-6 text-green-500" />
          Brazilian Commerce
        </h1>
        <p className="text-xs text-zinc-500 mt-1">MCP Server Dashboard</p>
      </div>
      
      <nav className="flex-1 p-4">
        <h3 className="text-xs font-semibold text-zinc-500 uppercase mb-3">Tools disponibles</h3>
        <ul className="space-y-1">
          {menuItems.map((item, i) => (
            <li key={i}>
              <button
                onClick={() => onSelectQuery(item.query)}
                className="w-full flex items-center gap-3 px-3 py-2 text-sm text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors"
              >
                <item.icon className="w-4 h-4" />
                {item.label}
              </button>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}
