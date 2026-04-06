#!/usr/bin/env python3
"""Bridge entre la API de Next.js y las tools MCP"""

import sys
import json
import asyncio
from pathlib import Path

# Añadir el directorio backend al path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from src.config.mongo import db

# Importar las funciones de las tools directamente
async def get_database_stats():
    customers_count = await db.customers.count_documents({})
    orders_count = await db.orders_final.count_documents({})
    products_count = await db.products.count_documents({})
    return {
        "total_customers": customers_count,
        "total_orders": orders_count,
        "total_products": products_count
    }

async def get_all_customers():
    customers = await db.customers.find({}, {"_id": 0}).to_list(length=None)
    return customers

async def get_all_orders():
    orders = await db.orders_final.find({}, {"_id": 0}).to_list(length=None)
    return orders

async def get_all_products():
    products = await db.products.find({}, {"_id": 0}).to_list(length=None)
    return products

async def list_categories():
    pipeline = [
        {"$group": {"_id": "$product_category_name", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    result = await db.products.aggregate(pipeline).to_list(length=None)
    return [{"category": r["_id"], "count": r["count"]} for r in result]

async def get_sales_by_state():
    pipeline = [
        {"$group": {"_id": "$customer_state", "total_orders": {"$sum": 1}}},
        {"$sort": {"total_orders": -1}}
    ]
    result = await db.orders_final.aggregate(pipeline).to_list(length=None)
    return [{"state": r["_id"], "total_orders": r["total_orders"]} for r in result]

async def count_orders_by_status():
    pipeline = [
        {"$group": {"_id": "$order_status", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    result = await db.orders_final.aggregate(pipeline).to_list(length=None)
    return [{"status": r["_id"], "count": r["count"]} for r in result]

async def get_top_customers():
    pipeline = [
        {"$group": {"_id": "$customer_id", "order_count": {"$sum": 1}}},
        {"$sort": {"order_count": -1}}
    ]
    result = await db.orders_final.aggregate(pipeline).to_list(length=None)
    return [{"customer_id": r["_id"], "order_count": r["order_count"]} for r in result]

# Mapeo de tools
TOOLS = {
    "get_database_stats": get_database_stats,
    "get_all_customers": get_all_customers,
    "get_all_orders": get_all_orders,
    "get_all_products": get_all_products,
    "list_categories": list_categories,
    "get_sales_by_state": get_sales_by_state,
    "count_orders_by_status": count_orders_by_status,
    "get_top_customers": get_top_customers,
}

async def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No tool specified"}))
        return

    tool_name = sys.argv[1]
    args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}

    if tool_name not in TOOLS:
        print(json.dumps({"error": f"Tool '{tool_name}' not found"}))
        return

    try:
        result = await TOOLS[tool_name](**args)
        print(json.dumps(result, default=str))
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    asyncio.run(main())
