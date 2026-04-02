from typing import Any

from mcp.server.fastmcp import FastMCP


mcp = FastMCP("MCP_server")

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()