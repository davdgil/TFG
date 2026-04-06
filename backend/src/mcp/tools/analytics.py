from typing import Any
from src.config.mongo import db

def register_analytics_tools(mcp):
    """Registra las herramientas de análisis en el servidor MCP"""
    
    @mcp.tool()
    async def get_sales_by_state() -> list[dict]:
        """Obtiene el total de ventas agrupadas por estado"""
        pipeline = [
            {"$group": {
                "_id": "$customer_state",
                "total_orders": {"$sum": 1}
            }},
            {"$sort": {"total_orders": -1}}
        ]
        result = await db.orders_final.aggregate(pipeline).to_list(length=None)
        return [{"state": r["_id"], "total_orders": r["total_orders"]} for r in result]

    @mcp.tool()
    async def get_top_customers() -> list[dict]:
        """Obtiene todos los clientes ordenados por número de pedidos"""
        pipeline = [
            {"$group": {
                "_id": "$customer_id",
                "order_count": {"$sum": 1}
            }},
            {"$sort": {"order_count": -1}}
        ]
        result = await db.orders_final.aggregate(pipeline).to_list(length=None)
        return [{"customer_id": r["_id"], "order_count": r["order_count"]} for r in result]

    @mcp.tool()
    async def get_database_stats() -> dict[str, Any]:
        """Obtiene estadísticas generales de la base de datos"""
        customers_count = await db.customers.count_documents({})
        orders_count = await db.orders_final.count_documents({})
        products_count = await db.products.count_documents({})
        
        return {
            "total_customers": customers_count,
            "total_orders": orders_count,
            "total_products": products_count
        }
