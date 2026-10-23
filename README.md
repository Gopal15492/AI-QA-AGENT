# AI QA Multi-Agent - Playwright First

Pipeline:

Jira Ticket → Jira Fetch Agent → Test Design Agent → Playwright/Selenium Code Agent → Browser Execution → Self-Healing → Reporting

## Browser execution priority

1. Playwright MCP - primary agentic browser execution mode.
2. Playwright CLI - secondary lightweight command-driven execution mode.

The UI defaults to Playwright and lets you choose either Playwright MCP or Playwright CLI for browser execution.

## Install

Python:

```bash
pip install -r requirements.txt
```

Node.js 20+ is recommended for the current Playwright CLI workflow.

Install Playwright CLI:

```bash
npm install -g @playwright/cli@latest
```

Verify:

```bash
playwright-cli --help
```

Playwright's current CLI documentation describes `playwright-cli` as a browser automation CLI designed for coding agents and notes that it is more token-efficient than MCP for command-driven workflows.

## Run

```bash
streamlit run app.py
```

## MCP mode

The app starts the Playwright MCP server through `npx @playwright/mcp@latest` and loads its tools through `langchain-mcp-adapters`.

## CLI mode

The app uses `playwright-cli` for opening the AUT, snapshots and screenshots. The CLI session is named `qa-agent`.

## Important

Do not commit `.env` or API keys. Use environment variables locally and in Render.

The current CLI execution stage is intentionally safe: it does not execute arbitrary generated shell code. Only the application's predefined Playwright CLI operations are used.
