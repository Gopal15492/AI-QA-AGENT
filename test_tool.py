import os
from dotenv import load_dotenv
from langchain_openrouter import ChatOpenRouter
from langchain_core.tools import tool

load_dotenv()

@tool
def test_browser():
    """Test browser tool."""
    return "Browser tool executed successfully."

model = ChatOpenRouter(
    model="deepseek/deepseek-v4.1-flash",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    temperature=0
)

model_with_tools = model.bind_tools([test_browser])

response = model_with_tools.invoke(
    "Use the browser tool and execute the test."
)

print(response)