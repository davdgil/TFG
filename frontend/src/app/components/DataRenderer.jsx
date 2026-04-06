'use client';

import { Users, ShoppingCart, Package } from 'lucide-react';

export default function DataRenderer({ data, tool }) {
  if (!data) return null;

  // Estadísticas generales
  if (tool === 'get_database_stats') {
    return (
      <div className="grid grid-cols-3 gap-4 mt-4">
        <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4 text-center">
          <Users className="w-8 h-8 mx-auto mb-2 text-blue-500" />
          <div className="text-2xl font-bold text-blue-500">{data.total_customers?.toLocaleString()}</div>
          <div className="text-sm text-zinc-400">Clientes</div>
        </div>
        <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-4 text-center">
          <ShoppingCart className="w-8 h-8 mx-auto mb-2 text-green-500" />
          <div className="text-2xl font-bold text-green-500">{data.total_orders?.toLocaleString()}</div>
          <div className="text-sm text-zinc-400">Pedidos</div>
        </div>
        <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-4 text-center">
          <Package className="w-8 h-8 mx-auto mb-2 text-purple-500" />
          <div className="text-2xl font-bold text-purple-500">{data.total_products?.toLocaleString()}</div>
          <div className="text-sm text-zinc-400">Productos</div>
        </div>
      </div>
    );
  }

  // Datos de array (tablas)
  if (Array.isArray(data) && data.length > 0) {
    const keys = Object.keys(data[0]).slice(0, 5);
    const displayData = data.slice(0, 20);
    
    return (
      <div className="mt-4 overflow-x-auto">
        <div className="text-sm text-zinc-400 mb-2">
          Mostrando {displayData.length} de {data.length} registros
        </div>
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="bg-zinc-800">
              {keys.map(key => (
                <th key={key} className="border border-zinc-700 px-3 py-2 text-left text-zinc-300">
                  {key}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {displayData.map((row, i) => (
              <tr key={i} className="hover:bg-zinc-800/50">
                {keys.map(key => (
                  <td key={key} className="border border-zinc-700 px-3 py-2 text-zinc-400">
                    {typeof row[key] === 'object' ? JSON.stringify(row[key]) : String(row[key] ?? '')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  return <pre className="mt-4 text-sm text-zinc-400 overflow-auto">{JSON.stringify(data, null, 2)}</pre>;
}
