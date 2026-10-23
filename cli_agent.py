import os
from pathlib import Path
import shutil
import subprocess

os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ.pop("LANGSMITH_API_KEY", None)
os.environ.pop("LANGCHAIN_API_KEY", None)

from dotenv import load_dotenv
load_dotenv()

from langchain_openrouter import ChatOpenRouter
from langchain.agents import create_agent
from langchain_core.tools import tool

from config import AUT_BASE_URL


SESSION = "qa-agent"
ROOT = Path(__file__).resolve().parent


def run_cli(*args):
    executable = shutil.which("playwright-cli")

    if not executable:
        return "ERROR: playwright-cli was not found."

    command = [executable, f"-s={SESSION}", *args]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120
        )

        output = result.stdout

        if result.stderr:
            output += "\n" + result.stderr

        return output.strip()

    except Exception as e:
        return f"ERROR: {str(e)}"


@tool
def open_application():
    """Open the configured application."""
    return run_cli(
        "open",
        AUT_BASE_URL,
        "--headed",
        "--persistent"
    )


@tool
def inspect_page():
    """Inspect the current page."""
    return run_cli("snapshot")


@tool
def click_element(ref: str):
    """Click an element using a snapshot ref."""
    return run_cli("click", ref)


@tool
def fill_element(ref: str, value: str):
    """Fill an input using a snapshot ref."""
    return run_cli("fill", ref, value)


@tool
def get_configured_credentials():
    """Get configured credentials."""
    return {
        "username": os.getenv("ORANGEHRM_USERNAME", ""),
        "password": os.getenv("ORANGEHRM_PASSWORD", "")
    }

@tool
def write_framework_file(relative_path: str, content: str):
    """Write a file into the current Playwright framework."""
    file_path = (ROOT / relative_path).resolve()

    if ROOT.resolve() not in file_path.parents:
        return "ERROR: Cannot write outside the project folder."

    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")

    return f"SUCCESS: Created/updated {relative_path}"

def create_framework():
    root = ROOT

    folders = [
        root / "tests",
        root / "src" / "pages",
        root / "src" / "fixtures",
        root / "src" / "utils"
    ]

    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)

    package_json = """{
  "name": "qa-playwright-framework",
  "version": "1.0.0",
  "scripts": {
    "test": "playwright test",
    "test:headed": "playwright test --headed",
    "test:debug": "playwright test --debug",
    "report": "playwright show-report"
  },
  "devDependencies": {
    "@playwright/test": "latest",
    "@types/node": "latest",
    "typescript": "latest"
  }
}"""

    tsconfig = """{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "resolveJsonModule": true
  },
  "include": [
    "tests/**/*.ts",
    "src/**/*.ts",
    "playwright.config.ts"
  ]
}"""

    playwright_config = """import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 30000,
  use: {
    baseURL: process.env.AUT_BASE_URL || 'https://opensource-demo.orangehrmlive.com',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure'
  },
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome']
      }
    }
  ],
  reporter: [
    ['html'],
    ['list']
  ]
});
"""

    base_fixture = """import { test as base, expect } from '@playwright/test';

export const test = base;
export { expect };
"""

    files = {
        root / "package.json": package_json,
        root / "tsconfig.json": tsconfig,
        root / "playwright.config.ts": playwright_config,
        root / "src" / "fixtures" / "base.fixture.ts": base_fixture
    }

    for file_path, content in files.items():
        file_path.write_text(content, encoding="utf-8")

    return f"""
Playwright TypeScript framework created successfully.

Location:
{root}

Created:
tests/
src/pages/
src/fixtures/
src/utils/
package.json
tsconfig.json
playwright.config.ts
"""


system_prompt = f"""
You are an AI QA automation agent.

Application URL:
{AUT_BASE_URL}

Your responsibilities:

1. Execute browser tasks using Playwright CLI.
2. Generate Playwright TypeScript automation.
3. Add generated automation code into the existing framework.
4. When the user asks to create, add, save, update, or generate automation in the framework, you MUST use the write_framework_file tool.
5. Never only display the generated code when the user asks to add it to the framework.
6. Do not claim a file was created unless write_framework_file returned SUCCESS.
7. Use this existing framework structure:

tests/
src/pages/
src/fixtures/
src/utils/

8. Page Objects MUST be stored in:
src/pages/

9. Test files MUST be stored in:
tests/

10. For tests/login.spec.ts importing LoginPage, use:
../src/pages/LoginPage

11. Inspect existing framework files before modifying them when necessary.
12. Do not reveal passwords.

For browser tasks:
- inspect the page before interacting
- use current snapshot refs
- never invent refs
- verify the result after actions
"""

tools = [
    open_application,
    inspect_page,
    click_element,
    fill_element,
    get_configured_credentials,
    write_framework_file
]

def main():
    print()
    print("=" * 60)
    print("        AI QA PLAYWRIGHT CLI AGENT")
    print("=" * 60)
    print("Type a normal English instruction.")
    print()
    print("Examples:")
    print("  Create a Playwright TypeScript automation framework")
    print("  Login to the application")
    print("  Verify the dashboard")
    print("  Search for an employee")
    print("  Logout")
    print()
    print("Type 'exit' to quit.")
    print("=" * 60)
    print()

    llm = ChatOpenRouter(
       model=os.getenv("OPENROUTER_MODEL"),
        #api_key=os.getenv("OPENROUTER_API_KEY"),
        api_key=os.getenv("OPENROUTER_API_KEY"),
        temperature=0,
        max_tokens=2500
    )

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt
    )

    while True:
        try:
            user_input = input("QA Agent> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nQA Agent stopped.")
            break

        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit", "q"]:
            print("QA Agent stopped.")
            break

        framework_request = any(
            phrase in user_input.lower()
            for phrase in [
                "create framework",
                "create a framework",
                "build framework",
                "build a framework",
                "create playwright framework",
                "create a playwright typescript framework",
                "create a playwright typescript automation framework"
            ]
        )

        if framework_request:
            print()
            print("Framework request detected.")
            print("Browser will NOT be opened.")
            print()
            print(create_framework())
            print()
            continue

        print()
        print("Executing browser task...")
        print()

        try:
            result = agent.invoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": user_input
                        }
                    ]
                }
            )

            messages = result.get("messages", [])

            if messages:
                print(messages[-1].content)
            else:
                print("No response received.")

        except Exception as e:
            import traceback
            print(f"Agent error: {e}")
            traceback.print_exc()

        print()


if __name__ == "__main__":
    main()
