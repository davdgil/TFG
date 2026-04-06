


import sys
import logging
from pathlib import Path

# Añadir el directorio backend al path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from mcp.server.fastmcp import FastMCP
from src.mcp.tools.customer import register_customer_tools
from src.mcp.tools.orders import register_order_tools
from src.mcp.tools.products import register_product_tools
from src.mcp.tools.analytics import register_analytics_tools

# Configure logging to stderr (not stdout) 
logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)

def main():
    # Initialize FastMCP server
    mcp = FastMCP("BrazilianCommerce")
    
    # Register all tools
    register_customer_tools(mcp)
    register_order_tools(mcp)
    register_product_tools(mcp)
    register_analytics_tools(mcp)
    
    # Run the server
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()