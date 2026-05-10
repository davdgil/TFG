from __future__ import annotations

from typing import Any

from ..config.mongo import db


class AnalyticsService:
    DEFAULT_LIMIT = 10
    MAX_LIMIT = 100

    @staticmethod
    def clean_limit(limit: int | None) -> int:
        if limit is None:
            return AnalyticsService.DEFAULT_LIMIT
        return max(1, min(limit, AnalyticsService.MAX_LIMIT))

    @staticmethod
    def format_money(value: float | int | None) -> str:
        number = float(value or 0)
        return f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @staticmethod
    def build_date_stage() -> dict[str, Any]:
        return {"$addFields": {"order_date_parsed": {"$toDate": "$order_date"}}}

    @staticmethod
    def build_year_filter_stage(year: int | None) -> list[dict[str, Any]]:
        if not year:
            return []
        return [{"$match": {"$expr": {"$eq": [{"$year": "$order_date_parsed"}, year]}}}]

    @staticmethod
    def build_orders_with_items_pipeline(year: int | None = None) -> list[dict[str, Any]]:
        return [
            AnalyticsService.build_date_stage(),
            *AnalyticsService.build_year_filter_stage(year),
            {"$unwind": "$items"},
        ]

    @staticmethod
    async def resolve_customer_reference(customer_ref: str) -> dict[str, Any] | None:
        customer_ref = str(customer_ref or "").strip()
        if not customer_ref:
            return None

        return await db.customers.find_one(
            {
                "$or": [
                    {"customer_id": customer_ref},
                    {"customer_unique_id": customer_ref},
                ]
            },
            {"_id": 0},
        )

    @staticmethod
    async def build_customer_summary(customer: dict[str, Any]) -> dict[str, Any]:
        pipeline = [
            {"$match": {"customer_id": customer["customer_id"]}},
            AnalyticsService.build_date_stage(),
            {"$unwind": "$items"},
            {
                "$group": {
                    "_id": {
                        "anio": {"$year": "$order_date_parsed"},
                        "order_id": "$order_id",
                    },
                    "ventas": {"$sum": "$items.price"},
                    "envio": {"$sum": "$items.freight_value"},
                    "unidades": {"$sum": 1},
                }
            },
            {
                "$group": {
                    "_id": "$_id.anio",
                    "ventas": {"$sum": "$ventas"},
                    "envio": {"$sum": "$envio"},
                    "unidades": {"$sum": "$unidades"},
                    "pedidos": {"$sum": 1},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "anio": "$_id",
                    "ventas": {"$round": ["$ventas", 2]},
                    "envio": {"$round": ["$envio", 2]},
                    "unidades": 1,
                    "pedidos": 1,
                }
            },
            {"$sort": {"anio": 1}},
        ]
        rows = await db.orders_final.aggregate(pipeline).to_list(length=None)
        total_orders = sum(row["pedidos"] for row in rows)
        total_sales = sum(row["ventas"] for row in rows)
        total_units = sum(row["unidades"] for row in rows)
        average_ticket = total_sales / total_orders if total_orders else 0
        location = f'{customer["customer_city"]}, {customer["customer_state"]}'

        return {
            "message": f"Resumen de actividad del cliente seleccionado en {location}.",
            "kpis": {
                "pedidos": total_orders,
                "ventas_totales": AnalyticsService.format_money(total_sales),
                "ticket_medio": AnalyticsService.format_money(average_ticket),
                "unidades": total_units,
            },
            "table": rows,
            "chart": {
                "type": "line",
                "title": "Ventas del cliente por anio",
                "data": [{"name": str(row["anio"]), "value": row["ventas"]} for row in rows],
            },
        }

    @staticmethod
    async def customer_summary(customer_ref: str) -> dict[str, Any]:
        customer = await AnalyticsService.resolve_customer_reference(customer_ref)
        if not customer:
            return {
                "message": "No se ha encontrado ningun cliente con ese identificador.",
                "kpis": {},
                "table": [],
                "chart": None,
            }

        return await AnalyticsService.build_customer_summary(customer)

    @staticmethod
    async def random_customer_summary() -> dict[str, Any]:
        customers = await db.customers.aggregate(
            [
                {"$sample": {"size": 1}},
                {"$project": {"_id": 0}},
            ]
        ).to_list(length=1)

        if not customers:
            return {
                "message": "No hay clientes disponibles para generar un resumen aleatorio.",
                "kpis": {},
                "table": [],
                "chart": None,
            }

        return await AnalyticsService.build_customer_summary(customers[0])

    @staticmethod
    async def database_stats() -> dict[str, Any]:
        customers_count = await db.customers.count_documents({})
        orders_count = await db.orders_final.count_documents({})
        products_count = await db.products.count_documents({})
        order_items_count = await db.order_items.count_documents({})

        return {
            "message": "Resumen general del conjunto de datos con el volumen actual de clientes, pedidos, productos y lineas de pedido.",
            "kpis": {
                "clientes": customers_count,
                "pedidos": orders_count,
                "productos": products_count,
                "lineas_pedido": order_items_count,
            },
            "table": [
                {"coleccion": "customers", "registros": customers_count},
                {"coleccion": "orders_final", "registros": orders_count},
                {"coleccion": "products", "registros": products_count},
                {"coleccion": "order_items", "registros": order_items_count},
            ],
            "chart": {
                "type": "bar",
                "title": "Registros por coleccion",
                "data": [
                    {"name": "Clientes", "value": customers_count},
                    {"name": "Pedidos", "value": orders_count},
                    {"name": "Productos", "value": products_count},
                    {"name": "Items", "value": order_items_count},
                ],
            },
        }

    @staticmethod
    async def product_count_by_category(limit: int | None = None) -> dict[str, Any]:
        limit = AnalyticsService.clean_limit(limit)
        pipeline = [
            {
                "$group": {
                    "_id": "$product_category_name_english",
                    "productos": {"$sum": 1},
                }
            },
            {"$sort": {"productos": -1}},
            {"$limit": limit},
            {
                "$project": {
                    "_id": 0,
                    "categoria": {"$ifNull": ["$_id", "uncategorized"]},
                    "productos": 1,
                }
            },
        ]
        rows = await db.products.aggregate(pipeline).to_list(length=limit)

        return {
            "message": f"Distribucion de productos por categoria. Se muestran las {len(rows)} categorias con mayor volumen del catalogo.",
            "kpis": {
                "categorias_mostradas": len(rows),
                "mayor_categoria": rows[0]["categoria"] if rows else "sin datos",
            },
            "table": rows,
            "chart": {
                "type": "bar",
                "title": "Productos por categoria",
                "data": [{"name": row["categoria"], "value": row["productos"]} for row in rows],
            },
        }

    @staticmethod
    async def sales_by_year() -> dict[str, Any]:
        pipeline = [
            *AnalyticsService.build_orders_with_items_pipeline(),
            {
                "$group": {
                    "_id": {"$year": "$order_date_parsed"},
                    "ventas": {"$sum": "$items.price"},
                    "envio": {"$sum": "$items.freight_value"},
                    "pedidos": {"$addToSet": "$order_id"},
                    "unidades": {"$sum": 1},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "anio": "$_id",
                    "ventas": {"$round": ["$ventas", 2]},
                    "envio": {"$round": ["$envio", 2]},
                    "pedidos": {"$size": "$pedidos"},
                    "unidades": 1,
                }
            },
            {"$sort": {"anio": 1}},
        ]
        rows = await db.orders_final.aggregate(pipeline).to_list(length=None)
        total_sales = sum(row["ventas"] for row in rows)

        return {
            "message": "Evolucion anual de las ventas del negocio a partir del historico completo de pedidos.",
            "kpis": {
                "anios": len(rows),
                "ventas_totales": AnalyticsService.format_money(total_sales),
                "mejor_anio": max(rows, key=lambda row: row["ventas"])["anio"] if rows else "sin datos",
            },
            "table": rows,
            "chart": {
                "type": "line",
                "title": "Ventas por anio",
                "data": [{"name": str(row["anio"]), "value": row["ventas"]} for row in rows],
            },
        }

    @staticmethod
    async def sales_by_month(year: int | None = None) -> dict[str, Any]:
        pipeline = [
            *AnalyticsService.build_orders_with_items_pipeline(year),
            {
                "$group": {
                    "_id": {
                        "anio": {"$year": "$order_date_parsed"},
                        "mes": {"$month": "$order_date_parsed"},
                    },
                    "ventas": {"$sum": "$items.price"},
                    "pedidos": {"$addToSet": "$order_id"},
                    "unidades": {"$sum": 1},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "anio": "$_id.anio",
                    "mes": "$_id.mes",
                    "periodo": {
                        "$concat": [
                            {"$toString": "$_id.anio"},
                            "-",
                            {
                                "$cond": [
                                    {"$lt": ["$_id.mes", 10]},
                                    {"$concat": ["0", {"$toString": "$_id.mes"}]},
                                    {"$toString": "$_id.mes"},
                                ]
                            },
                        ]
                    },
                    "ventas": {"$round": ["$ventas", 2]},
                    "pedidos": {"$size": "$pedidos"},
                    "unidades": 1,
                }
            },
            {"$sort": {"anio": 1, "mes": 1}},
        ]
        rows = await db.orders_final.aggregate(pipeline).to_list(length=None)
        title_year = f" en {year}" if year else ""

        return {
            "message": f"Evolucion mensual de las ventas{title_year}, con el detalle cronologico del periodo analizado.",
            "kpis": {
                "meses": len(rows),
                "ventas_totales": AnalyticsService.format_money(sum(row["ventas"] for row in rows)),
                "mejor_mes": max(rows, key=lambda row: row["ventas"])["periodo"] if rows else "sin datos",
            },
            "table": rows,
            "chart": {
                "type": "line",
                "title": f"Ventas mensuales{title_year}",
                "data": [{"name": row["periodo"], "value": row["ventas"]} for row in rows],
            },
        }

    @staticmethod
    async def sales_by_category(year: int | None = None, limit: int | None = None) -> dict[str, Any]:
        limit = AnalyticsService.clean_limit(limit)
        pipeline = [
            *AnalyticsService.build_orders_with_items_pipeline(year),
            {
                "$group": {
                    "_id": "$items.product_category_name_english",
                    "ventas": {"$sum": "$items.price"},
                    "envio": {"$sum": "$items.freight_value"},
                    "pedidos": {"$addToSet": "$order_id"},
                    "unidades": {"$sum": 1},
                }
            },
            {"$sort": {"ventas": -1}},
            {"$limit": limit},
            {
                "$project": {
                    "_id": 0,
                    "categoria": {"$ifNull": ["$_id", "uncategorized"]},
                    "ventas": {"$round": ["$ventas", 2]},
                    "envio": {"$round": ["$envio", 2]},
                    "pedidos": {"$size": "$pedidos"},
                    "unidades": 1,
                }
            },
        ]
        rows = await db.orders_final.aggregate(pipeline).to_list(length=limit)
        title_year = f" en {year}" if year else ""

        return {
            "message": f"Ventas por categoria{title_year}. Se destacan las {len(rows)} categorias con mayor peso en la facturacion.",
            "kpis": {
                "categorias_mostradas": len(rows),
                "ventas_top": AnalyticsService.format_money(rows[0]["ventas"]) if rows else "0,00",
                "top_categoria": rows[0]["categoria"] if rows else "sin datos",
            },
            "table": rows,
            "chart": {
                "type": "bar",
                "title": f"Ventas por categoria{title_year}",
                "data": [{"name": row["categoria"], "value": row["ventas"]} for row in rows],
            },
        }

    @staticmethod
    async def units_by_category(year: int | None = None, limit: int | None = None) -> dict[str, Any]:
        limit = AnalyticsService.clean_limit(limit)
        pipeline = [
            *AnalyticsService.build_orders_with_items_pipeline(year),
            {
                "$group": {
                    "_id": "$items.product_category_name_english",
                    "unidades": {"$sum": 1},
                    "ventas": {"$sum": "$items.price"},
                }
            },
            {"$sort": {"unidades": -1}},
            {"$limit": limit},
            {
                "$project": {
                    "_id": 0,
                    "categoria": {"$ifNull": ["$_id", "uncategorized"]},
                    "unidades": 1,
                    "ventas": {"$round": ["$ventas", 2]},
                }
            },
        ]
        rows = await db.orders_final.aggregate(pipeline).to_list(length=limit)

        return {
            "message": f"Categorias con mayor volumen de unidades vendidas. Se muestran {len(rows)} categorias principales.",
            "kpis": {
                "categorias_mostradas": len(rows),
                "top_categoria": rows[0]["categoria"] if rows else "sin datos",
                "unidades_top": rows[0]["unidades"] if rows else 0,
            },
            "table": rows,
            "chart": {
                "type": "bar",
                "title": "Unidades vendidas por categoria",
                "data": [{"name": row["categoria"], "value": row["unidades"]} for row in rows],
            },
        }

    @staticmethod
    async def top_products(year: int | None = None, limit: int | None = None) -> dict[str, Any]:
        limit = AnalyticsService.clean_limit(limit)
        pipeline = [
            *AnalyticsService.build_orders_with_items_pipeline(year),
            {
                "$group": {
                    "_id": {
                        "product_id": "$items.product_id",
                        "categoria": "$items.product_category_name_english",
                    },
                    "ventas": {"$sum": "$items.price"},
                    "envio": {"$sum": "$items.freight_value"},
                    "unidades": {"$sum": 1},
                }
            },
            {"$sort": {"ventas": -1}},
            {"$limit": limit},
            {
                "$project": {
                    "_id": 0,
                    "producto": "$_id.product_id",
                    "categoria": {"$ifNull": ["$_id.categoria", "uncategorized"]},
                    "ventas": {"$round": ["$ventas", 2]},
                    "envio": {"$round": ["$envio", 2]},
                    "unidades": 1,
                }
            },
        ]
        rows = await db.orders_final.aggregate(pipeline).to_list(length=limit)
        title_year = f" en {year}" if year else ""

        return {
            "message": f"Ranking de los {len(rows)} productos con mayor volumen de ventas{title_year}.",
            "kpis": {
                "productos_mostrados": len(rows),
                "anio": year or "todos",
                "top_producto": rows[0]["producto"] if rows else "sin datos",
            },
            "table": rows,
            "chart": {
                "type": "bar",
                "title": f"Top productos por ventas{title_year}",
                "data": [{"name": row["producto"][:8], "value": row["ventas"]} for row in rows],
            },
        }

    @staticmethod
    async def sales_by_state(year: int | None = None, limit: int | None = None) -> dict[str, Any]:
        limit = AnalyticsService.clean_limit(limit)
        pipeline = [
            *AnalyticsService.build_orders_with_items_pipeline(year),
            {
                "$lookup": {
                    "from": "customers",
                    "localField": "customer_id",
                    "foreignField": "customer_id",
                    "as": "customer",
                }
            },
            {"$unwind": "$customer"},
            {
                "$group": {
                    "_id": "$customer.customer_state",
                    "ventas": {"$sum": "$items.price"},
                    "envio": {"$sum": "$items.freight_value"},
                    "pedidos": {"$addToSet": "$order_id"},
                    "unidades": {"$sum": 1},
                }
            },
            {"$sort": {"ventas": -1}},
            {"$limit": limit},
            {
                "$project": {
                    "_id": 0,
                    "estado": "$_id",
                    "ventas": {"$round": ["$ventas", 2]},
                    "envio": {"$round": ["$envio", 2]},
                    "pedidos": {"$size": "$pedidos"},
                    "unidades": 1,
                }
            },
        ]
        rows = await db.orders_final.aggregate(pipeline).to_list(length=limit)
        title_year = f" en {year}" if year else ""

        return {
            "message": f"Distribucion territorial de las ventas por estado{title_year}. Se muestran {len(rows)} estados en el analisis.",
            "kpis": {
                "estados_mostrados": len(rows),
                "mejor_estado": rows[0]["estado"] if rows else "sin datos",
                "ventas_top": AnalyticsService.format_money(rows[0]["ventas"]) if rows else "0,00",
            },
            "table": rows,
            "chart": {
                "type": "bar",
                "title": f"Ventas por estado{title_year}",
                "data": [{"name": row["estado"], "value": row["ventas"]} for row in rows],
            },
        }

    @staticmethod
    async def sales_by_city(year: int | None = None, limit: int | None = None) -> dict[str, Any]:
        limit = AnalyticsService.clean_limit(limit)
        pipeline = [
            *AnalyticsService.build_orders_with_items_pipeline(year),
            {
                "$lookup": {
                    "from": "customers",
                    "localField": "customer_id",
                    "foreignField": "customer_id",
                    "as": "customer",
                }
            },
            {"$unwind": "$customer"},
            {
                "$group": {
                    "_id": {
                        "ciudad": "$customer.customer_city",
                        "estado": "$customer.customer_state",
                    },
                    "ventas": {"$sum": "$items.price"},
                    "pedidos": {"$addToSet": "$order_id"},
                    "unidades": {"$sum": 1},
                }
            },
            {"$sort": {"ventas": -1}},
            {"$limit": limit},
            {
                "$project": {
                    "_id": 0,
                    "ciudad": "$_id.ciudad",
                    "estado": "$_id.estado",
                    "ventas": {"$round": ["$ventas", 2]},
                    "pedidos": {"$size": "$pedidos"},
                    "unidades": 1,
                }
            },
        ]
        rows = await db.orders_final.aggregate(pipeline).to_list(length=limit)

        return {
            "message": f"Ranking de las {len(rows)} ciudades con mayor volumen de ventas.",
            "kpis": {
                "ciudades_mostradas": len(rows),
                "top_ciudad": rows[0]["ciudad"] if rows else "sin datos",
                "top_estado": rows[0]["estado"] if rows else "sin datos",
            },
            "table": rows,
            "chart": {
                "type": "bar",
                "title": "Ventas por ciudad",
                "data": [{"name": row["ciudad"], "value": row["ventas"]} for row in rows],
            },
        }

    @staticmethod
    async def freight_by_state(year: int | None = None, limit: int | None = None) -> dict[str, Any]:
        limit = AnalyticsService.clean_limit(limit)
        result = await AnalyticsService.sales_by_state(year=year, limit=limit)
        rows = result["table"]

        return {
            "message": "Distribucion del coste de envio por estado para el conjunto de pedidos analizado.",
            "kpis": {
                "estados_mostrados": len(rows),
                "estado_mayor_envio": max(rows, key=lambda row: row["envio"])["estado"] if rows else "sin datos",
                "envio_total_mostrado": AnalyticsService.format_money(sum(row["envio"] for row in rows)),
            },
            "table": rows,
            "chart": {
                "type": "bar",
                "title": "Envio por estado",
                "data": [{"name": row["estado"], "value": row["envio"]} for row in rows],
            },
        }

    @staticmethod
    async def freight_by_category(year: int | None = None, limit: int | None = None) -> dict[str, Any]:
        result = await AnalyticsService.sales_by_category(year=year, limit=limit)
        rows = result["table"]

        return {
            "message": "Distribucion del coste de envio por categoria de producto.",
            "kpis": {
                "categorias_mostradas": len(rows),
                "categoria_mayor_envio": max(rows, key=lambda row: row["envio"])["categoria"] if rows else "sin datos",
                "envio_total_mostrado": AnalyticsService.format_money(sum(row["envio"] for row in rows)),
            },
            "table": rows,
            "chart": {
                "type": "bar",
                "title": "Envio por categoria",
                "data": [{"name": row["categoria"], "value": row["envio"]} for row in rows],
            },
        }

    @staticmethod
    async def average_order_value_by_year() -> dict[str, Any]:
        pipeline = [
            *AnalyticsService.build_orders_with_items_pipeline(),
            {
                "$group": {
                    "_id": {
                        "anio": {"$year": "$order_date_parsed"},
                        "order_id": "$order_id",
                    },
                    "importe_pedido": {"$sum": "$items.price"},
                    "unidades_pedido": {"$sum": 1},
                }
            },
            {
                "$group": {
                    "_id": "$_id.anio",
                    "ticket_medio": {"$avg": "$importe_pedido"},
                    "unidades_medias": {"$avg": "$unidades_pedido"},
                    "pedidos": {"$sum": 1},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "anio": "$_id",
                    "ticket_medio": {"$round": ["$ticket_medio", 2]},
                    "unidades_medias": {"$round": ["$unidades_medias", 2]},
                    "pedidos": 1,
                }
            },
            {"$sort": {"anio": 1}},
        ]
        rows = await db.orders_final.aggregate(pipeline).to_list(length=None)

        return {
            "message": "Evolucion del ticket medio por anio, calculado a partir del importe total de cada pedido.",
            "kpis": {
                "anios": len(rows),
                "mayor_ticket": AnalyticsService.format_money(max(rows, key=lambda row: row["ticket_medio"])["ticket_medio"]) if rows else "0,00",
            },
            "table": rows,
            "chart": {
                "type": "line",
                "title": "Ticket medio por anio",
                "data": [{"name": str(row["anio"]), "value": row["ticket_medio"]} for row in rows],
            },
        }

    @staticmethod
    async def orders_by_year() -> dict[str, Any]:
        pipeline = [
            AnalyticsService.build_date_stage(),
            {
                "$group": {
                    "_id": {"$year": "$order_date_parsed"},
                    "pedidos": {"$sum": 1},
                    "clientes": {"$addToSet": "$customer_id"},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "anio": "$_id",
                    "pedidos": 1,
                    "clientes": {"$size": "$clientes"},
                }
            },
            {"$sort": {"anio": 1}},
        ]
        rows = await db.orders_final.aggregate(pipeline).to_list(length=None)

        return {
            "message": "Evolucion anual del numero de pedidos registrados en el negocio.",
            "kpis": {
                "anios": len(rows),
                "pedidos_totales": sum(row["pedidos"] for row in rows),
                "anio_con_mas_pedidos": max(rows, key=lambda row: row["pedidos"])["anio"] if rows else "sin datos",
            },
            "table": rows,
            "chart": {
                "type": "bar",
                "title": "Pedidos por anio",
                "data": [{"name": str(row["anio"]), "value": row["pedidos"]} for row in rows],
            },
        }

    @staticmethod
    async def top_customers(limit: int | None = None) -> dict[str, Any]:
        limit = AnalyticsService.clean_limit(limit)
        pipeline = [
            *AnalyticsService.build_orders_with_items_pipeline(),
            {
                "$lookup": {
                    "from": "customers",
                    "localField": "customer_id",
                    "foreignField": "customer_id",
                    "as": "customer",
                }
            },
            {"$unwind": "$customer"},
            {
                "$group": {
                    "_id": "$customer.customer_unique_id",
                    "ventas": {"$sum": "$items.price"},
                    "pedidos": {"$addToSet": "$order_id"},
                    "estado": {"$first": "$customer.customer_state"},
                    "ciudad": {"$first": "$customer.customer_city"},
                }
            },
            {"$sort": {"ventas": -1}},
            {"$limit": limit},
            {
                "$project": {
                    "_id": 0,
                    "cliente": "$_id",
                    "estado": 1,
                    "ciudad": 1,
                    "ventas": {"$round": ["$ventas", 2]},
                    "pedidos": {"$size": "$pedidos"},
                }
            },
        ]
        rows = await db.orders_final.aggregate(pipeline).to_list(length=limit)

        return {
            "message": f"Ranking de los {len(rows)} clientes con mayor facturacion acumulada.",
            "kpis": {
                "clientes_mostrados": len(rows),
                "top_cliente": rows[0]["cliente"] if rows else "sin datos",
                "ventas_top": AnalyticsService.format_money(rows[0]["ventas"]) if rows else "0,00",
            },
            "table": rows,
            "chart": {
                "type": "bar",
                "title": "Clientes por ventas",
                "data": [{"name": row["cliente"][:8], "value": row["ventas"]} for row in rows],
            },
        }
