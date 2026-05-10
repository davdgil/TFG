from typing import Any

from src.config.mongo import db
from src.services.analytics_service import AnalyticsService


def register_product_tools(mcp):
    """Registra herramientas de productos alineadas con el esquema actual."""

    @mcp.tool()
    async def get_product_by_id(product_id: str) -> dict[str, Any]:
        """Obtiene un producto por su ID."""
        product = await db.products.find_one({"product_id": product_id}, {"_id": 0})
        if not product:
            return {"error": "Product not found"}
        return product

    @mcp.tool()
    async def get_products_by_category(category: str, limit: int | None = 20) -> list[dict[str, Any]]:
        """Obtiene productos de una categoria en ingles usando el esquema actual."""
        safe_limit = AnalyticsService.clean_limit(limit)
        products = await db.products.find(
            {"product_category_name_english": category},
            {"_id": 0},
        ).limit(safe_limit).to_list(length=safe_limit)
        return products

    @mcp.tool()
    async def get_all_products(limit: int | None = 20) -> list[dict[str, Any]]:
        """Obtiene una muestra limitada de productos."""
        safe_limit = AnalyticsService.clean_limit(limit)
        products = await db.products.find({}, {"_id": 0}).limit(safe_limit).to_list(length=safe_limit)
        return products

    @mcp.tool()
    async def list_categories(limit: int | None = None) -> dict[str, Any]:
        """Muestra categorias disponibles con conteo de productos y grafico."""
        return await AnalyticsService.product_count_by_category(limit=limit)

    @mcp.tool()
    async def search_products(keyword: str, limit: int | None = 20) -> list[dict[str, Any]]:
        """Busca productos por palabra clave dentro de la categoria en ingles."""
        safe_limit = AnalyticsService.clean_limit(limit)
        products = await db.products.find(
            {"product_category_name_english": {"$regex": keyword, "$options": "i"}},
            {"_id": 0},
        ).limit(safe_limit).to_list(length=safe_limit)
        return products
