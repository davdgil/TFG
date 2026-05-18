from typing import Any
from src.config.mongo import db
from src.services.analytics_service import AnalyticsService

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
    async def get_customer_by_unique_id(customer_unique_id: str) -> dict[str, Any]:
        """Obtiene un cliente por su customer_unique_id."""
        customer = await db.customers.find_one(
            {"customer_unique_id": customer_unique_id},
            {"_id": 0},
        )
        if not customer:
            return {"error": "Customer not found"}
        return customer

    @mcp.tool()
    async def get_random_customer() -> dict[str, Any]:
        """Obtiene un cliente aleatorio del conjunto de datos."""
        customers = await db.customers.aggregate(
            [
                {"$sample": {"size": 1}},
                {"$project": {"_id": 0}},
            ]
        ).to_list(length=1)
        if not customers:
            return {"error": "No customers found"}
        return customers[0]

    @mcp.tool()
    async def get_customer_summary(customer_ref: str) -> dict[str, Any]:
        """Devuelve un resumen analitico de un cliente a partir de customer_id o customer_unique_id."""
        return await AnalyticsService.customer_summary(customer_ref)

    @mcp.tool()
    async def get_random_customer_summary() -> dict[str, Any]:
        """Devuelve un resumen analitico de un cliente aleatorio."""
        return await AnalyticsService.random_customer_summary()

    @mcp.tool()
    async def customer_sales_by_month(customer_ref: str, year: int | None = None) -> dict[str, Any]:
        """Devuelve la evolucion mensual de ventas de un cliente, con filtro opcional por año."""
        return await AnalyticsService.customer_sales_by_month(customer_ref=customer_ref, year=year)

    @mcp.tool()
    async def customer_sales_by_day(customer_ref: str, year: int, month: int) -> dict[str, Any]:
        """Devuelve la evolucion diaria de ventas de un cliente en un mes y año concretos."""
        return await AnalyticsService.customer_sales_by_day(customer_ref=customer_ref, year=year, month=month)

    @mcp.tool()
    async def get_all_customers(limit: int | None = 20) -> list[dict[str, Any]]:
        """Obtiene una muestra limitada de clientes."""
        safe_limit = AnalyticsService.clean_limit(limit)
        customers = await db.customers.find({}, {"_id": 0}).limit(safe_limit).to_list(length=safe_limit)
        return customers
