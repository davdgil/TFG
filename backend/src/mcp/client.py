import asyncio
import json
import os
from contextlib import AsyncExitStack
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

OPENAI_MODEL = "gpt-5.4-mini"


class MCPClient:
    def __init__(self):
        self.session: ClientSession | None = None
        self.exit_stack = AsyncExitStack()
        self._openai: AsyncOpenAI | None = None
        self.stdio = None
        self.write = None

    @property
    def openai(self) -> AsyncOpenAI:
        if self._openai is None:
            self._openai = AsyncOpenAI(
                api_key=os.getenv("OPENAI_API_KEY")
            )
        return self._openai

    async def connect_to_server(self, server_script_path: str):
        is_python = server_script_path.endswith(".py")
        is_js = server_script_path.endswith(".js")

        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        if is_python:
            path = Path(server_script_path).resolve()
            server_params = StdioServerParameters(
                command=r"C:\Users\theivid\Documents\GitHub\TFG\backend\venv\Scripts\python.exe",
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

    def _build_openai_tools(self, mcp_tools):
        openai_tools = []

        for tool in mcp_tools:
            parameters = tool.inputSchema or {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            }

            openai_tools.append(
                {
                    "type": "function",
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": parameters,
                }
            )

        return openai_tools

    async def process_query(self, query: str) -> str:
        if not self.session:
            raise RuntimeError("MCP session is not initialized")

        tools_response = await self.session.list_tools()
        available_tools = self._build_openai_tools(tools_response.tools)

        input_items = [
            {
                "role": "user",
                "content": query,
            }
        ]

        while True:
            response = await self.openai.responses.create(
                model=OPENAI_MODEL,
                input=input_items,
                tools=available_tools,
            )

            function_calls = [
                item for item in response.output
                if item.type == "function_call"
            ]

            if not function_calls:
                return (response.output_text or "").strip()

            # Guardamos la salida del modelo para el siguiente turno
            input_items.extend(response.output)

            for tool_call in function_calls:
                tool_name = tool_call.name

                try:
                    tool_args = json.loads(tool_call.arguments) if tool_call.arguments else {}
                except json.JSONDecodeError:
                    tool_args = {}

                result = await self.session.call_tool(tool_name, tool_args)

                print(f"\n[Tool call] {tool_name}({tool_args})")
                print(f"[Tool result] {result.content}\n")

                input_items.append(
                    {
                        "type": "function_call_output",
                        "call_id": tool_call.call_id,
                        "output": json.dumps(result.content, ensure_ascii=False, default=str),
                    }
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


async def main():
    client = MCPClient()
    try:
        server_script = "src/mcp/server.py"
        await client.connect_to_server(server_script)

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("No se encontró OPENAI_API_KEY en el .env")
            return

        await client.chat_loop()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())