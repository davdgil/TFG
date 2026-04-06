from typing import Any
from src.config.mongo import db

def register_order_tools(mcp):
    """Registra las herramientas de pedidos en el servidor MCP"""
    
    @mcp.tool()
    async def get_order_by_id(order_id: str) -> dict[str, Any]:
        """Obtiene un pedido por su ID"""
        order = await db.orders_final.find_one({"order_id": order_id}, {"_id": 0})
        if not order:
            return {"error": "Order not found"}
        return order

    @mcp.tool()
    async def get_orders_by_customer(customer_id: str) -> list[dict]:
        """Obtiene todos los pedidos de un cliente específico"""
        orders = await db.orders_final.find(
            {"customer_id": customer_id}, 
            {"_id": 0}
        ).to_list(length=None)
        return orders

    @mcp.tool()
    async def get_all_orders() -> list[dict]:
        """Obtiene todos los pedidos"""
        orders = await db.orders_final.find(
            {}, 
            {"_id": 0}
        ).to_list(length=None)
        return orders

    @mcp.tool()
    async def count_orders_by_status() -> list[dict]:
        """Cuenta los pedidos agrupados por estado"""
        pipeline = [
            {"$group": {"_id": "$order_status", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        result = await db.orders_final.aggregate(pipeline).to_list(length=None)
        return [{"status": r["_id"], "count": r["count"]} for r in result]
