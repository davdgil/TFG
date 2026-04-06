from typing import Any
from src.config.mongo import db

def register_product_tools(mcp):
    """Registra las herramientas de productos en el servidor MCP"""
    
    @mcp.tool()
    async def get_product_by_id(product_id: str) -> dict[str, Any]:
        """Obtiene un producto por su ID"""
        product = await db.products.find_one({"product_id": product_id}, {"_id": 0})
        if not product:
            return {"error": "Product not found"}
        return product

    @mcp.tool()
    async def get_products_by_category(category: str) -> list[dict]:
        """Obtiene todos los productos de una categoría específica"""
        products = await db.products.find(
            {"product_category_name": category}, 
            {"_id": 0}
        ).to_list(length=None)
        return products

    @mcp.tool()
    async def get_all_products() -> list[dict]:
        """Obtiene todos los productos"""
        products = await db.products.find({}, {"_id": 0}).to_list(length=None)
        return products

    @mcp.tool()
    async def list_categories() -> list[dict]:
        """Lista todas las categorías de productos con su conteo"""
        pipeline = [
            {"$group": {"_id": "$product_category_name", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        result = await db.products.aggregate(pipeline).to_list(length=None)
        return [{"category": r["_id"], "count": r["count"]} for r in result]

    @mcp.tool()
    async def search_products(keyword: str) -> list[dict]:
        """Busca todos los productos por palabra clave en la categoría"""
        products = await db.products.find(
            {"product_category_name": {"$regex": keyword, "$options": "i"}},
            {"_id": 0}
        ).to_list(length=None)
        return products
