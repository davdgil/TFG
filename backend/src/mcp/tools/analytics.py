from typing import Any

from src.services.analytics_service import AnalyticsService


def register_analytics_tools(mcp):
    """Registra herramientas analiticas para que la IA decida que grafico usar."""

    @mcp.tool()
    async def database_stats() -> dict[str, Any]:
        """Muestra estadisticas generales: clientes, pedidos, productos e items."""
        return await AnalyticsService.database_stats()

    @mcp.tool()
    async def product_count_by_category(limit: int | None = None) -> dict[str, Any]:
        """Grafico de numero de productos por categoria."""
        return await AnalyticsService.product_count_by_category(limit=limit)

    @mcp.tool()
    async def sales_by_year() -> dict[str, Any]:
        """Grafico de ventas agregadas por anio usando todos los pedidos."""
        return await AnalyticsService.sales_by_year()

    @mcp.tool()
    async def sales_by_month(year: int | None = None) -> dict[str, Any]:
        """Grafico de ventas por mes. Puede filtrarse por anio."""
        return await AnalyticsService.sales_by_month(year=year)

    @mcp.tool()
    async def sales_by_category(year: int | None = None, limit: int | None = None) -> dict[str, Any]:
        """Grafico de ventas por categoria. Puede filtrarse por anio."""
        return await AnalyticsService.sales_by_category(year=year, limit=limit)

    @mcp.tool()
    async def units_by_category(year: int | None = None, limit: int | None = None) -> dict[str, Any]:
        """Grafico de unidades vendidas por categoria."""
        return await AnalyticsService.units_by_category(year=year, limit=limit)

    @mcp.tool()
    async def top_products(year: int | None = None, limit: int | None = None) -> dict[str, Any]:
        """Grafico de productos con mas ventas. Puede filtrarse por anio."""
        return await AnalyticsService.top_products(year=year, limit=limit)

    @mcp.tool()
    async def sales_by_state(year: int | None = None, limit: int | None = None) -> dict[str, Any]:
        """Grafico de ventas por estado. Puede filtrarse por anio."""
        return await AnalyticsService.sales_by_state(year=year, limit=limit)

    @mcp.tool()
    async def sales_by_city(year: int | None = None, limit: int | None = None) -> dict[str, Any]:
        """Grafico de ventas por ciudad. Puede filtrarse por anio."""
        return await AnalyticsService.sales_by_city(year=year, limit=limit)

    @mcp.tool()
    async def freight_by_state(year: int | None = None, limit: int | None = None) -> dict[str, Any]:
        """Grafico de coste de envio por estado."""
        return await AnalyticsService.freight_by_state(year=year, limit=limit)

    @mcp.tool()
    async def freight_by_category(year: int | None = None, limit: int | None = None) -> dict[str, Any]:
        """Grafico de coste de envio por categoria."""
        return await AnalyticsService.freight_by_category(year=year, limit=limit)

    @mcp.tool()
    async def average_order_value_by_year() -> dict[str, Any]:
        """Grafico de ticket medio por anio."""
        return await AnalyticsService.average_order_value_by_year()

    @mcp.tool()
    async def orders_by_year() -> dict[str, Any]:
        """Grafico de numero de pedidos por anio."""
        return await AnalyticsService.orders_by_year()

    @mcp.tool()
    async def top_customers(limit: int | None = None) -> dict[str, Any]:
        """Grafico de clientes con mas ventas acumuladas."""
        return await AnalyticsService.top_customers(limit=limit)
