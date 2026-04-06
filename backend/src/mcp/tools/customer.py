from typing import Any
from src.config.mongo import db

def register_customer_tools(mcp):
    """Registra las herramientas de clientes en el servidor MCP"""
    
    @mcp.tool()
    async def get_customer_by_id(customer_id: str) -> dict[str, Any]:
        """Obtiene un cliente por su ID"""
        customer = await db.customers.find_one({"customer_id": customer_id}, {"_id": 0})
        if not customer:
            return {"error": "Customer not found"}
        return customer

    @mcp.tool()
    async def get_all_customers() -> list[dict]:
        """Obtiene todos los clientes"""
        customers = await db.customers.find({}, {"_id": 0}).to_list(length=None)
        return customers