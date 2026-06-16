import asyncio
import json
import os
import re
import sys
import time
import unicodedata
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

GEMINI_MODEL = "gemini-2.5-flash"
MODEL_TIMEOUT_SECONDS = 20
TOOL_TIMEOUT_SECONDS = 20
MAX_MODEL_TURNS = 6
MAX_TOOL_CALLS = 8

DASHBOARD_INSTRUCTIONS = """
Eres un asistente analitico para un dashboard de e-commerce.
Cuando el usuario pida analisis por dimension, comparativas, rankings,
evoluciones temporales, top productos o distribuciones, debes elegir la
herramienta MCP mas adecuada.

Las herramientas analiticas ya devuelven un objeto listo para la interfaz con:
message, kpis, table y chart. No inventes datos.
Si una herramienta analitica devuelve ese objeto, usalo como resultado final.
"""

CONVERSATION_INSTRUCTIONS = """
Eres un asistente analitico para un dashboard de e-commerce.
Si la pregunta del usuario es exploratoria o abierta, responde como una persona
en lenguaje natural, de forma breve y profesional.

Puedes usar herramientas MCP para fundamentar tu respuesta, pero en este modo no
debes devolver JSON, tablas ni graficos automaticamente. Resume el hallazgo en
2 o 3 frases claras y sugiere una siguiente linea de analisis solo si aporta.
No inventes datos.
"""


class MCPClient:
    MONTH_NAME_TO_NUMBER = {
        "enero": 1,
        "febrero": 2,
        "marzo": 3,
        "abril": 4,
        "mayo": 5,
        "junio": 6,
        "julio": 7,
        "agosto": 8,
        "septiembre": 9,
        "setiembre": 9,
        "octubre": 10,
        "noviembre": 11,
        "diciembre": 12,
    }

    def __init__(self):
        self.session: ClientSession | None = None
        self.exit_stack = AsyncExitStack()
        self._gemini: genai.Client | None = None
        self.stdio = None
        self.write = None

    @property
    def gemini(self) -> genai.Client:
        if self._gemini is None:
            api_key = os.getenv("GEMINI_API_KEY")
            self._gemini = genai.Client(api_key=api_key)
        return self._gemini

    async def connect_to_server(self, server_script_path: str):
        is_python = server_script_path.endswith(".py")
        is_js = server_script_path.endswith(".js")

        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        if is_python:
            Path(server_script_path).resolve()
            server_params = StdioServerParameters(
                command=sys.executable,
                args=["-m", "src.mcp.server"],
                env=os.environ.copy(),
            )
        else:
            server_params = StdioServerParameters(
                command="node",
                args=[server_script_path],
                env=os.environ.copy(),
            )

        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.stdio, self.write = stdio_transport

        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        await self.session.initialize()

        response = await self.session.list_tools()
        tools = response.tools
        print("MCP conectado. Tools disponibles:", [tool.name for tool in tools])

    async def list_tools(self):
        if not self.session:
            raise RuntimeError("MCP session is not initialized")

        response = await self.session.list_tools()
        return response.tools

    def build_gemini_tools(self, mcp_tools: list[Any]) -> list[types.Tool]:
        function_declarations = []

        for tool in mcp_tools:
            parameters = tool.inputSchema or {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            }

            function_declarations.append(
                types.FunctionDeclaration(
                    name=tool.name,
                    description=tool.description or "",
                    parameters_json_schema=parameters,
                )
            )

        return [types.Tool(function_declarations=function_declarations)]

    def normalize_text(self, text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text.lower())
        return "".join(char for char in normalized if not unicodedata.combining(char))

    def extract_year(self, text: str) -> int | None:
        match = re.search(r"\b(20\d{2})\b", text)
        if match:
            return int(match.group(1))

        match = re.search(r"\b(20\d{2})(?=[a-f0-9]{8,}\b)", text)
        return int(match.group(1)) if match else None

    def extract_limit(self, text: str) -> int | None:
        match = re.search(r"\btop\s+(\d{1,3})\b", text)
        if not match:
            match = re.search(r"\b(\d{1,3})\b", text)
        if not match:
            return None
        return int(match.group(1))

    def extract_month(self, text: str) -> int | None:
        named_month = next(
            (number for name, number in self.MONTH_NAME_TO_NUMBER.items() if name in text),
            None,
        )
        if named_month is not None:
            return named_month

        match = re.search(r"\bmes\s*(\d{1,2})\b", text)
        if not match:
            match = re.search(r"\b(0?[1-9]|1[0-2])/(20\d{2})\b", text)
            if match:
                return int(match.group(1))

        if not match:
            match = re.search(r"\b(0?[1-9]|1[0-2])\b", text)
            if match:
                month = int(match.group(1))
                if 1 <= month <= 12:
                    return month

        return int(match.group(1)) if match else None

    def extract_hex_identifier(self, text: str) -> str | None:
        match = re.search(r"\b[a-f0-9]{32}\b", text)
        if match:
            return match.group(0)

        tokens = re.findall(r"\b[a-f0-9]{8,}\b", text)
        fragments: list[str] = []
        for token in tokens:
            if re.fullmatch(r"20\d{2}[a-f0-9]{8,}", token):
                fragments.append(token[4:])
            fragments.append(token)

        for start in range(len(fragments)):
            candidate = ""
            for fragment in fragments[start:]:
                candidate += fragment
                if len(candidate) == 32:
                    return candidate
                if len(candidate) > 32:
                    break

        return None

    def extract_product_id(self, text: str) -> str | None:
        return self.extract_hex_identifier(text)

    def format_label(self, value: Any) -> str:
        text = str(value or "").strip()
        if not text:
            return "sin datos"
        return text.replace("_", " ")

    def build_chat_response(
        self,
        message: str,
        meta: dict[str, Any],
        kpis: dict[str, Any] | None = None,
        table: list[dict[str, Any]] | None = None,
        chart: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "message": message,
            "kpis": kpis or {},
            "table": table or [],
            "chart": chart,
            "meta": meta,
        }

    def attach_meta(
        self, payload: str | dict[str, Any], meta: dict[str, Any]
    ) -> dict[str, Any]:
        if isinstance(payload, dict):
            return {
                "message": payload.get("message", ""),
                "kpis": payload.get("kpis", {}),
                "table": payload.get("table", []),
                "chart": payload.get("chart"),
                "meta": meta,
            }

        return self.build_chat_response(message=payload, meta=meta)

    def infer_allowed_functions(self, query: str) -> list[str] | None:
        text = self.normalize_text(query)
        entity_id = self.extract_hex_identifier(text)

        if any(word in text for word in ["que puedes hacer", "ayuda", "hola", "buenas"]):
            return None

        if any(term in text for term in ["cliente aleatorio", "usuario aleatorio", "consumidor aleatorio", "comprador aleatorio"]):
            if any(word in text for word in ["analiza", "estadistica", "resumen", "ventas", "pedidos", "compras", "facturacion"]):
                return ["get_random_customer_summary"]
            return ["get_random_customer"]

        if entity_id and any(term in text for term in ["cliente", "usuario", "consumidor", "comprador", "consumer"]):
            if ("dia" in text or "dias" in text) and self.extract_year(text) is not None and self.extract_month(text) is not None:
                return ["customer_sales_by_day"]
            if any(word in text for word in ["mes", "mensual", "meses"]) and any(word in text for word in ["ventas", "compras", "facturacion", "evolucion", "historial"]):
                return ["customer_sales_by_month"]
            if any(word in text for word in ["analiza", "estadistica", "resumen", "ventas", "pedidos", "compras", "facturacion"]):
                return ["get_customer_summary"]
            return ["get_customer_by_id", "get_customer_by_unique_id", "get_customer_summary"]

        if entity_id and "producto" in text:
            return ["get_product_by_id"]

        if "envio" in text or "flete" in text or "transporte" in text:
            if "estado" in text:
                return ["freight_by_state"]
            if "categoria" in text:
                return ["freight_by_category"]

        if "ticket" in text or "promedio" in text:
            return ["average_order_value_by_year"]

        if any(term in text for term in ["cliente", "usuario", "consumidor", "comprador", "consumer"]):
            if any(word in text for word in ["resumen", "estadistica", "analiza", "compras", "pedidos", "facturacion"]):
                return ["top_customers", "get_random_customer_summary"]
            return ["top_customers"]

        if ("dia" in text or "dias" in text) and self.extract_year(text) is not None and self.extract_month(text) is not None:
            return ["sales_by_day"]

        if "ciudad" in text:
            return ["sales_by_city"]

        if "estado" in text:
            return ["sales_by_state"]

        if "mensual" in text or "mes" in text:
            if "dia" in text or "dias" in text:
                return ["sales_by_day"]
            if any(signal in text for signal in ["estacionalidad", "por mes del año", "por mes del ano", "reparto mensual", "distribucion mensual"]):
                return ["sales_seasonality"]
            return ["sales_by_month"]

        if "pedido" in text and ("anio" in text or "ano" in text or "evolucion" in text):
            return ["orders_by_year"]

        if "categoria" in text:
            if "unidad" in text or "vendidas" in text or "vendidos" in text:
                return ["units_by_category"]
            if "venta" in text or "facturacion" in text:
                return ["sales_by_category"]
            return ["product_count_by_category", "list_categories"]

        if "producto" in text:
            return ["top_products", "get_product_by_id", "search_products"]

        if "estadistica" in text or "resumen general" in text or "base de datos" in text:
            return ["database_stats"]

        if "ventas" in text or "facturacion" in text:
            if any(signal in text for signal in ["estacionalidad", "por mes del año", "por mes del ano", "reparto mensual", "distribucion mensual"]):
                return ["sales_seasonality"]
            return ["sales_by_year", "sales_by_month", "sales_by_category", "sales_by_state", "sales_by_city", "top_products"]

        return None

    def infer_query_mode(self, query: str, allowed_functions: list[str] | None = None) -> str:
        text = self.normalize_text(query)
        entity_id = self.extract_hex_identifier(text)

        conversational_patterns = [
            "que me puedes decir",
            "que puedes decirme",
            "que sabes",
            "hablame de",
            "explicame",
            "resumeme",
            "como van",
            "como estan",
            "como fueron",
            "que opinas",
        ]
        if any(pattern in text for pattern in conversational_patterns):
            return "conversation"

        if entity_id and ("que producto es" in text or "que producto" in text):
            return "conversation"

        if entity_id and (
            "que cliente es" in text
            or "quien es el cliente" in text
            or "que usuario es" in text
        ):
            return "conversation"

        dashboard_signals = [
            "muestr",
            "analiza",
            "compara",
            "evolucion",
            "grafico",
            "top ",
            "ranking",
            "mas vendido",
            "mas vendidos",
            "mensual",
            "estacionalidad",
            "anual",
            "por estado",
            "por ciudad",
            "por categoria",
            "ticket medio",
            "coste de envio",
            "unidades vendidas",
            "quiero ver",
            "concentran",
            "generan mas",
            "con mas",
            "mas productos",
            "mas ventas",
            "mas facturacion",
            "que clientes",
            "que categorias",
            "que estados",
            "que ciudades",
            "cliente aleatorio",
            "usuario aleatorio",
        ]
        if any(signal in text for signal in dashboard_signals):
            return "dashboard"

        if allowed_functions:
            lookup_tools = {
                "get_product_by_id",
                "get_customer_by_id",
                "get_customer_by_unique_id",
                "get_random_customer",
                "get_order_by_id",
                "get_products_by_category",
                "search_products",
                "get_orders_by_customer",
                "get_all_customers",
                "get_all_products",
                "get_all_orders",
            }
            non_lookup_allowed = [name for name in allowed_functions if name not in lookup_tools]
            if non_lookup_allowed:
                return "dashboard"

        return "conversation"

    def build_fallback_tool_args(self, tool_name: str, query: str) -> dict[str, Any]:
        text = self.normalize_text(query)
        year = self.extract_year(text)
        month = self.extract_month(text)
        limit = self.extract_limit(text)
        entity_id = self.extract_hex_identifier(text)
        args: dict[str, Any] = {}

        if year is not None and tool_name in {
            "customer_sales_by_day",
            "customer_sales_by_month",
            "sales_by_day",
            "sales_by_month",
            "sales_by_category",
            "units_by_category",
            "top_products",
            "sales_by_state",
            "sales_by_city",
            "freight_by_state",
            "freight_by_category",
        }:
            args["year"] = year

        if month is not None and tool_name in {"sales_by_day", "customer_sales_by_day"}:
            args["month"] = month

        if limit is not None and tool_name in {
            "product_count_by_category",
            "sales_by_category",
            "units_by_category",
            "top_products",
            "sales_by_state",
            "sales_by_city",
            "freight_by_state",
            "freight_by_category",
            "top_customers",
            "list_categories",
        }:
            args["limit"] = limit

        if entity_id is not None and tool_name == "get_product_by_id":
            args["product_id"] = entity_id

        if entity_id is not None and tool_name == "get_customer_by_id":
            args["customer_id"] = entity_id

        if entity_id is not None and tool_name == "get_customer_by_unique_id":
            args["customer_unique_id"] = entity_id

        if entity_id is not None and tool_name == "get_customer_summary":
            args["customer_ref"] = entity_id

        if entity_id is not None and tool_name == "customer_sales_by_month":
            args["customer_ref"] = entity_id

        if entity_id is not None and tool_name == "customer_sales_by_day":
            args["customer_ref"] = entity_id

        return args

    def tool_content_to_text(self, content: Any) -> str:
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            parts = []
            for item in content:
                text = getattr(item, "text", None)
                if text is not None:
                    parts.append(text)
                else:
                    parts.append(str(item))
            return "\n".join(parts)

        return str(content)

    def parse_json_object(self, text: str) -> dict[str, Any] | None:
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return None

        if isinstance(parsed, dict):
            return parsed
        return None

    def is_frontend_result(self, value: Any) -> bool:
        return (
            isinstance(value, dict)
            and "message" in value
            and "kpis" in value
            and "table" in value
            and "chart" in value
        )

    def build_function_response_part(self, tool_name: str, tool_output: str) -> types.Part:
        parsed_output = self.parse_json_object(tool_output)
        if parsed_output is not None:
            response_payload = {"output": parsed_output}
        else:
            response_payload = {"output": tool_output}

        return types.Part.from_function_response(
            name=tool_name,
            response=response_payload,
        )

    def summarize_frontend_result(self, result: dict[str, Any]) -> str:
        message = str(result.get("message", "")).strip()
        kpis = result.get("kpis") or {}
        if not isinstance(kpis, dict) or not kpis:
            return message

        highlights = []
        for key, value in list(kpis.items())[:2]:
            label = str(key).replace("_", " ")
            highlights.append(f"{label}: {value}")

        if not highlights:
            return message

        return f"{message} Datos destacados: {'; '.join(highlights)}."

    def summarize_tool_result(self, tool_name: str, result: Any) -> str:
        if isinstance(result, dict):
            if "error" in result:
                return str(result["error"])

            if tool_name == "get_product_by_id":
                product_id = result.get("product_id", "desconocido")
                category = self.format_label(result.get("product_category_name_english"))
                return f"El producto {product_id} pertenece a la categoria {category}."

            if tool_name == "get_customer_by_id":
                customer_id = result.get("customer_id", "desconocido")
                city = self.format_label(result.get("customer_city"))
                state = self.format_label(result.get("customer_state"))
                return f"El cliente {customer_id} esta registrado en {city}, {state}."

            if tool_name == "get_customer_by_unique_id":
                customer_id = result.get("customer_unique_id", "desconocido")
                city = self.format_label(result.get("customer_city"))
                state = self.format_label(result.get("customer_state"))
                return f"El cliente {customer_id} esta registrado en {city}, {state}."

            if tool_name == "get_random_customer":
                customer_id = result.get("customer_unique_id") or result.get("customer_id", "desconocido")
                city = self.format_label(result.get("customer_city"))
                state = self.format_label(result.get("customer_state"))
                return f"He encontrado un cliente aleatorio: {customer_id}, ubicado en {city}, {state}."

            if tool_name == "get_order_by_id":
                order_id = result.get("order_id", "desconocido")
                customer_id = result.get("customer_id", "desconocido")
                items = result.get("items", [])
                items_count = len(items) if isinstance(items, list) else 0
                return f"El pedido {order_id} pertenece al cliente {customer_id} y contiene {items_count} productos."

        if isinstance(result, list):
            count = len(result)
            if tool_name == "get_products_by_category":
                return f"He encontrado {count} productos en esa categoria."
            if tool_name == "search_products":
                return f"He encontrado {count} productos que coinciden con esa busqueda."
            if tool_name == "get_orders_by_customer":
                return f"El cliente tiene {count} pedidos en el conjunto de datos consultado."
            if tool_name == "get_all_customers":
                return f"La consulta devuelve una muestra de {count} clientes."
            if tool_name == "get_all_products":
                return f"La consulta devuelve una muestra de {count} productos."
            if tool_name == "get_all_orders":
                return f"La consulta devuelve una muestra de {count} pedidos."

        return str(result)

    async def call_tool_with_timeout(
        self, tool_name: str, tool_args: dict[str, Any]
    ) -> Any:
        try:
            return await asyncio.wait_for(
                self.session.call_tool(tool_name, tool_args),
                timeout=TOOL_TIMEOUT_SECONDS,
            )
        except TimeoutError as exc:
            raise RuntimeError(
                f"La consulta no se pudo completar porque la herramienta {tool_name} ha tardado demasiado."
            ) from exc

    async def process_query(self, query: str) -> dict[str, Any]:
        if not self.session:
            raise RuntimeError("MCP session is not initialized")

        started_at = time.perf_counter()
        tools_response = await self.session.list_tools()
        gemini_tools = self.build_gemini_tools(tools_response.tools)
        allowed_functions = self.infer_allowed_functions(query)
        query_mode = self.infer_query_mode(query, allowed_functions)
        tool_config = None
        if allowed_functions:
            tool_config = types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(
                    mode="ANY",
                    allowed_function_names=allowed_functions,
                )
            )
        system_instruction = (
            DASHBOARD_INSTRUCTIONS if query_mode == "dashboard" else CONVERSATION_INSTRUCTIONS
        )
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=gemini_tools,
            tool_config=tool_config,
            temperature=0.2,
        )

        contents: list[types.Content] = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=query)],
            )
        ]
        repeated_calls: dict[str, int] = {}
        selected_tools: list[str] = []
        total_tool_calls = 0
        model_turns = 0

        def finalize(payload: str | dict[str, Any], had_error: bool = False) -> dict[str, Any]:
            latency_ms = round((time.perf_counter() - started_at) * 1000)
            meta = {
                "query_mode": query_mode,
                "selected_tool": selected_tools[0] if selected_tools else None,
                "selected_tools": selected_tools,
                "tool_calls": total_tool_calls,
                "latency_ms": latency_ms,
                "had_error": had_error,
            }
            return self.attach_meta(payload, meta)

        while True:
            model_turns += 1
            if model_turns > MAX_MODEL_TURNS:
                raise RuntimeError(
                    "No he podido completar la consulta de forma fiable. Prueba con una consulta mas concreta."
                )

            try:
                response = await asyncio.wait_for(
                    self.gemini.aio.models.generate_content(
                        model=GEMINI_MODEL,
                        contents=contents,
                        config=config,
                    ),
                    timeout=MODEL_TIMEOUT_SECONDS,
                )
            except TimeoutError:
                if allowed_functions and len(allowed_functions) == 1:
                    fallback_tool = allowed_functions[0]
                    fallback_args = self.build_fallback_tool_args(fallback_tool, query)
                    selected_tools.append(fallback_tool)
                    total_tool_calls += 1
                    result = await self.call_tool_with_timeout(fallback_tool, fallback_args)
                    tool_output = self.tool_content_to_text(result.content)
                    parsed_tool_output = self.parse_json_object(tool_output)
                    if self.is_frontend_result(parsed_tool_output):
                        if query_mode == "dashboard":
                            return finalize(parsed_tool_output)
                        return finalize(self.summarize_frontend_result(parsed_tool_output))
                    if parsed_tool_output is not None:
                        return finalize(
                            self.summarize_tool_result(fallback_tool, parsed_tool_output)
                        )
                raise RuntimeError(
                    "La consulta ha tardado demasiado y no se ha podido completar."
                )
            except Exception:
                if allowed_functions and len(allowed_functions) == 1:
                    fallback_tool = allowed_functions[0]
                    fallback_args = self.build_fallback_tool_args(fallback_tool, query)
                    selected_tools.append(fallback_tool)
                    total_tool_calls += 1
                    result = await self.call_tool_with_timeout(fallback_tool, fallback_args)
                    tool_output = self.tool_content_to_text(result.content)
                    parsed_tool_output = self.parse_json_object(tool_output)
                    if self.is_frontend_result(parsed_tool_output):
                        if query_mode == "dashboard":
                            return finalize(parsed_tool_output)
                        return finalize(self.summarize_frontend_result(parsed_tool_output))
                    if parsed_tool_output is not None:
                        return finalize(
                            self.summarize_tool_result(fallback_tool, parsed_tool_output)
                        )
                raise

            function_calls = response.function_calls or []
            if not function_calls:
                output_text = (response.text or "").strip()
                parsed_output = self.parse_json_object(output_text)
                if self.is_frontend_result(parsed_output):
                    return finalize(parsed_output)
                return finalize(output_text)

            contents.append(response.candidates[0].content)
            function_response_parts: list[types.Part] = []

            for function_call in function_calls:
                total_tool_calls += 1
                if total_tool_calls > MAX_TOOL_CALLS:
                    raise RuntimeError(
                        "La consulta necesita demasiados pasos y se ha detenido para evitar que quede bloqueada."
                    )

                tool_name = function_call.name
                tool_args = function_call.args or {}
                selected_tools.append(tool_name)
                result = await self.call_tool_with_timeout(tool_name, tool_args)
                tool_output = self.tool_content_to_text(result.content)
                parsed_tool_output = self.parse_json_object(tool_output)
                call_signature = json.dumps(
                    {"tool": tool_name, "args": tool_args},
                    ensure_ascii=False,
                    sort_keys=True,
                )
                repeated_calls[call_signature] = repeated_calls.get(call_signature, 0) + 1

                print(f"\n[Tool call] {tool_name}({tool_args})")
                print(f"[Tool result] {result.content}\n")

                if self.is_frontend_result(parsed_tool_output):
                    if query_mode == "dashboard":
                        return finalize(parsed_tool_output)
                    return finalize(self.summarize_frontend_result(parsed_tool_output))

                if parsed_tool_output is not None and query_mode == "conversation" and allowed_functions and len(allowed_functions) == 1:
                    return finalize(
                        self.summarize_tool_result(tool_name, parsed_tool_output)
                    )

                if parsed_tool_output is not None and repeated_calls[call_signature] >= 2:
                    return finalize(
                        self.summarize_tool_result(tool_name, parsed_tool_output)
                    )

                function_response_parts.append(
                    self.build_function_response_part(tool_name, tool_output)
                )

            contents.append(
                types.Content(
                    role="tool",
                    parts=function_response_parts,
                )
            )

    async def chat_loop(self):
        print("\nMCP Client Started!")
        print("Escribe tu consulta o 'quit' para salir.\n")

        while True:
            try:
                query = input("Query: ").strip()

                if query.lower() in {"quit", "exit", "salir"}:
                    break

                if not query:
                    continue

                response = await self.process_query(query)
                print(f"\nRespuesta:\n{response}\n")

            except Exception as e:
                print(f"\nError: {e}\n")

    async def cleanup(self):
        await self.exit_stack.aclose()
        if self._gemini is not None:
            await self._gemini.aio.aclose()
            self._gemini.close()


async def main():
    client = MCPClient()
    try:
        server_script = "src/mcp/server.py"
        await client.connect_to_server(server_script)

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("No se encontro GEMINI_API_KEY en el .env")
            return

        await client.chat_loop()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
