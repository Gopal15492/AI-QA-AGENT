from langchain_mcp_adapters.client import MultiServerMCPClient

mcp_client = MultiServerMCPClient(
    {
        "playwright": {
            "command": "npx",
            "args": [
                "-y",
                "@playwright/mcp@latest",
                "--headless"
            ],
            "transport": "stdio"
        }
    }
)

async def get_playwright_tools():
    return await mcp_client.get_tools()
