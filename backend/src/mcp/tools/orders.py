from typing import Any

from src.config.mongo import db
from src.services.analytics_service import AnalyticsService


def register_order_tools(mcp):
    """Registra herramientas de pedidos alineadas con el esquema actual."""

    @mcp.tool()
    async def get_order_by_id(order_id: str) -> dict[str, Any]:
        """Obtiene un pedido por su ID."""
        order = await db.orders_final.find_one({"order_id": order_id}, {"_id": 0})
        if not order:
            return {"error": "Order not found"}
        return order

    @mcp.tool()
    async def get_orders_by_customer(customer_id: str, limit: int | None = 20) -> list[dict[str, Any]]:
        """Obtiene pedidos de un cliente."""
        safe_limit = AnalyticsService.clean_limit(limit)
        orders = await db.orders_final.find(
            {"customer_id": customer_id},
            {"_id": 0},
        ).limit(safe_limit).to_list(length=safe_limit)
        return orders

    @mcp.tool()
    async def get_all_orders(limit: int | None = 20) -> list[dict[str, Any]]:
        """Obtiene una muestra limitada de pedidos."""
        safe_limit = AnalyticsService.clean_limit(limit)
        orders = await db.orders_final.find({}, {"_id": 0}).limit(safe_limit).to_list(length=safe_limit)
        return orders

    @mcp.tool()
    async def count_orders_by_year() -> dict[str, Any]:
        """Grafico del numero de pedidos por anio."""
        return await AnalyticsService.orders_by_year()
