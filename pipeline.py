
import asyncio
import re
import os
import uuid
from pathlib import Path
from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from agents import (
    create_llm,
    build_jira_agent,
    build_test_design_agent,
    build_code_agent,
    build_execution_agent,
    build_self_healing_agent,
    build_reporting_agent,
)
from config import AUT_BASE_URL, JIRA_BASE_URL
from mcp_client import get_playwright_tools
from playwright_cli import (
    cli_available,
    open_page,
    snapshot,
    screenshot,
    close,
)


# =========================================================
# Configuration
# =========================================================

MAX_REPAIR_ATTEMPTS = 2
PROJECT_ROOT = Path.cwd()
TESTS_DIR = PROJECT_ROOT / "tests"


class QAState(TypedDict, total=False):
    jira_ticket: str
    requirement_note: str
    test_case_count: int
    automation_framework: str
    programming_language: str
    execution_mode: str
    execute_test: bool
    headed: bool

    jira_text: str
    test_cases: str
    code: str
    execution: str
    execution_exit_code: int
    failure_detected: bool
    healing: str
    proposed_fix: str
    retry_execution: str
    repair_attempts: int
    report: str
    spec_path: str
    error: str


# =========================================================
# Helpers
# =========================================================

def _last_content(result) -> str:
    messages = result.get("messages", [])
    if not messages:
        return str(result)

    content = getattr(messages[-1], "content", "")
    return content if isinstance(content, str) else str(content)


def _extract_code(text: str):
    match = re.search(
        r"```(?:typescript|ts|javascript|js)?[ \t]*\n"
        r"(.*?)```",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return match.group(1).strip() if match else None


def _is_playwright_typescript(state: QAState) -> bool:
    framework = state.get("automation_framework", "").lower()
    language = state.get("programming_language", "").lower()

    return (
        "playwright" in framework
        and ("typescript" in language or language in ("ts", ""))
    )


def _looks_like_playwright_spec(code: str) -> bool:
    return (
        "test(" in code
        and ("@playwright/test" in code or "from 'playwright/test'" in code
             or 'from "playwright/test"' in code
             or "from '@playwright/test'" in code
             or 'from "@playwright/test"' in code)
    )


async def _run_playwright_spec(spec_path: Path, headed: bool = False):
    """Run a real Playwright Test spec and return its actual exit code."""
    command = [
        "npx",
        "playwright",
        "test",
        str(spec_path),
        "--reporter=line",
    ]

    if headed:
        command.append("--headed")

    process = await asyncio.create_subprocess_exec(
        *command,
        cwd=str(PROJECT_ROOT),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    try:
        stdout, _ = await asyncio.wait_for(
            process.communicate(),
            timeout=300,
        )
        output = stdout.decode("utf-8", errors="replace")
        return process.returncode, output

    except asyncio.TimeoutError:
        process.kill()
        await process.communicate()
        return 124, "Playwright test timed out after 300 seconds."


def _safe_spec_path() -> Path:
    TESTS_DIR.mkdir(parents=True, exist_ok=True)
    unique_id = uuid.uuid4().hex[:8]
    return TESTS_DIR / f"ai_generated_{unique_id}.spec.ts"


# =========================================================
# Main pipeline
# =========================================================

async def run_pipeline(
    jira_ticket,
    requirement_note,
    test_case_count,
    automation_framework,
    programming_language,
    execution_mode,
    execute_test,
    headed=False,
):
    llm = create_llm(4000)
    playwright_tools = await get_playwright_tools()

    # -------------------- Node: Jira ----------------------

    async def jira_node(state: QAState):
        ticket = state.get("jira_ticket", "")

        if not ticket:
            return {
                "jira_text": state.get("requirement_note")
                or "No Jira requirement provided."
            }

        agent = build_jira_agent(llm, playwright_tools)

        result = await agent.ainvoke({
            "messages": [{
                "role": "user",
                "content": f"""
Open Jira at {JIRA_BASE_URL} using the authenticated browser
session. Fetch {ticket}. Extract key, summary, description,
acceptance criteria, priority, status, labels and components.
Do not invent missing values or modify Jira.
"""
            }]
        })

        return {"jira_text": _last_content(result)}

    # -------------------- Node: Test design --------------

    async def test_design_node(state: QAState):
        agent = build_test_design_agent(llm)

        result = await agent.ainvoke({
            "messages": [{
                "role": "user",
                "content": f"""
REQUIREMENT:
{state.get("jira_text", "")}

Generate exactly {state.get("test_case_count", 5)} test cases.
Cover relevant positive, negative, boundary, validation,
error handling, security and UI scenarios.

Do not invent unsupported business rules. Return a Markdown table.
"""
            }]
        })

        return {"test_cases": _last_content(result)}

    # -------------------- Node: Code generation ----------

    async def code_generation_node(state: QAState):
        agent = build_code_agent(llm)

        result = await agent.ainvoke({
            "messages": [{
                "role": "user",
                "content": f"""
REQUIREMENT:
{state.get("jira_text", "")}

TEST CASES:
{state.get("test_cases", "")}

FRAMEWORK: {state.get("automation_framework", "")}
LANGUAGE: {state.get("programming_language", "")}
APPLICATION URL: {AUT_BASE_URL}

Generate a complete Playwright Test spec if Playwright
TypeScript is selected. Use valid imports, executable tests,
explicit assertions, and the configured application URL.
Do not claim the code has been executed.
Return code in a fenced code block.
"""
            }]
        })

        raw = _last_content(result)
        code = _extract_code(raw)

        return {
            "code": code or raw,
            "spec_path": "",
            "repair_attempts": 0,
            "healing": "No repair attempted.",
            "retry_execution": "No retry performed.",
        }

    # -------------------- Node: Execute ------------------

    async def execution_node(state: QAState):
        if not state.get("execute_test", False):
            return {
                "execution": "Execution not requested.",
                "execution_exit_code": 0,
                "failure_detected": False,
            }

        if not _is_playwright_typescript(state):
            return {
                "execution": (
                    "Automatic repair/retest currently supports "
                    "Playwright TypeScript specs only."
                ),
                "execution_exit_code": -1,
                "failure_detected": False,
            }

        code = state.get("code", "")
        extracted = _extract_code(code) or code

        if not _looks_like_playwright_spec(extracted):
            return {
                "execution": (
                    "Execution blocked: generated output does not "
                    "look like a valid Playwright Test spec. "
                    "Review imports and test structure."
                ),
                "execution_exit_code": -1,
                "failure_detected": False,
                "code": extracted,
            }

        spec_path = _safe_spec_path()

        try:
            spec_path.write_text(extracted, encoding="utf-8")
        except OSError as exc:
            return {
                "execution": f"Could not save generated spec: {exc}",
                "execution_exit_code": -1,
                "failure_detected": False,
            }

        exit_code, output = await _run_playwright_spec(
            spec_path,
            headed=state.get("headed", False),
        )

        return {
            "code": extracted,
            "spec_path": str(spec_path),
            "execution": (
                f"Playwright exit code: {exit_code}\n"
                f"Spec: {spec_path}\n\n{output}"
            ),
            "execution_exit_code": exit_code,
            "failure_detected": exit_code != 0,
        }

    # -------------------- Node: Self-healing --------------

    async def self_healing_node(state: QAState):
        attempts = state.get("repair_attempts", 0)

        if attempts >= MAX_REPAIR_ATTEMPTS:
            return {
                "healing": "Maximum repair attempts reached.",
                "proposed_fix": "",
                "retry_execution": "Retry limit reached.",
            }

        agent = build_self_healing_agent(llm)

        result = await agent.ainvoke({
            "messages": [{
                "role": "user",
                "content": f"""
You are repairing a Playwright TypeScript test.

REQUIREMENT:
{state.get("jira_text", "")}

APPROVED TEST CASES:
{state.get("test_cases", "")}

CURRENT SPEC:
{state.get("code", "")}

ACTUAL EXECUTION OUTPUT:
{state.get("execution", "")}

Repair only the identified test automation issue.
Preserve all business requirements and meaningful assertions.
Never remove assertions, skip tests, hardcode a fake PASS,
or weaken validation just to make the test pass.
Do not change application business logic or production data.

Return the complete corrected Playwright TypeScript spec
inside one fenced TypeScript code block. Explain the cause
and fix outside the code block.
"""
            }]
        })

        healing = _last_content(result)
        proposed_fix = _extract_code(healing)

        if not proposed_fix or not _looks_like_playwright_spec(proposed_fix):
            return {
                "healing": healing,
                "proposed_fix": "",
                "retry_execution": (
                    "No valid complete Playwright spec was extracted. "
                    "Automatic repair stopped; manual review required."
                ),
            }

        # Only accept a complete test spec; never overwrite original.
        return {
            "healing": healing,
            "proposed_fix": proposed_fix,
            "repair_attempts": attempts + 1,
            "retry_execution": "Corrected spec ready for isolated retest.",
        }

    # -------------------- Node: Apply and retest ---------

    async def retry_execution_node(state: QAState):
        fix = state.get("proposed_fix", "")

        if not fix:
            return {
                "retry_execution": (
                    "No valid proposed fix. Retest not performed."
                ),
                "failure_detected": True,
            }

        # Each repaired version is saved separately.
        spec_path = _safe_spec_path()

        try:
            spec_path.write_text(fix, encoding="utf-8")
        except OSError as exc:
            return {
                "retry_execution": f"Could not save repaired spec: {exc}",
                "failure_detected": True,
            }

        exit_code, output = await _run_playwright_spec(
            spec_path,
            headed=state.get("headed", False),
        )

        result_label = "PASS" if exit_code == 0 else "FAIL"

        return {
            "code": fix,
            "spec_path": str(spec_path),
            "execution": (
                f"Retest result: {result_label}\n"
                f"Exit code: {exit_code}\n"
                f"Spec: {spec_path}\n\n{output}"
            ),
            "execution_exit_code": exit_code,
            "failure_detected": exit_code != 0,
            "retry_execution": (
                f"Retest {result_label}; exit code {exit_code}. "
                "Inspect output before accepting the repair."
            ),
        }

    # -------------------- Node: Reporting ----------------

    async def reporting_node(state: QAState):
        agent = build_reporting_agent(llm)

        result = await agent.ainvoke({
            "messages": [{
                "role": "user",
                "content": f"""
JIRA: {state.get("jira_ticket") or "Not provided"}

REQUIREMENT:
{state.get("jira_text", "")}

TEST CASES:
{state.get("test_cases", "")}

FINAL CODE:
{state.get("code", "")}

EXECUTION:
{state.get("execution", "")}

EXIT CODE:
{state.get("execution_exit_code", "Not available")}

SELF-HEALING ANALYSIS:
{state.get("healing", "")}

REPAIR ATTEMPTS:
{state.get("repair_attempts", 0)}

RETEST:
{state.get("retry_execution", "")}

Write a concise report. Clearly distinguish actual runner
results from AI suggestions. Do not invent pass/fail counts.
An inspection-only result is not a test PASS.
"""
            }]
        })

        return {"report": _last_content(result)}

    # -------------------- Routing ------------------------

    def route_after_code(state: QAState):
        if state.get("execute_test", False):
            return "execution"
        return "reporting"

    def route_after_execution(state: QAState):
        if state.get("failure_detected", False):
            return "self_healing"
        return "reporting"

    def route_after_healing(state: QAState):
        if state.get("proposed_fix"):
            return "retry_execution"
        return "reporting"

    def route_after_retry(state: QAState):
        if (
            state.get("failure_detected", False)
            and state.get("repair_attempts", 0) < MAX_REPAIR_ATTEMPTS
        ):
            return "self_healing"
        return "reporting"

    # -------------------- Build graph --------------------

    builder = StateGraph(QAState)

    builder.add_node("jira", jira_node)
    builder.add_node("test_design", test_design_node)
    builder.add_node("code_generation", code_generation_node)
    builder.add_node("execution", execution_node)
    builder.add_node("self_healing", self_healing_node)
    builder.add_node("retry_execution", retry_execution_node)
    builder.add_node("reporting", reporting_node)

    builder.add_edge(START, "jira")
    builder.add_edge("jira", "test_design")
    builder.add_edge("test_design", "code_generation")

    builder.add_conditional_edges(
        "code_generation",
        route_after_code,
        {
            "execution": "execution",
            "reporting": "reporting",
        },
    )

    builder.add_conditional_edges(
        "execution",
        route_after_execution,
        {
            "self_healing": "self_healing",
            "reporting": "reporting",
        },
    )

    builder.add_conditional_edges(
        "self_healing",
        route_after_healing,
        {
            "retry_execution": "retry_execution",
            "reporting": "reporting",
        },
    )

    builder.add_conditional_edges(
        "retry_execution",
        route_after_retry,
        {
            "self_healing": "self_healing",
            "reporting": "reporting",
        },
    )

    builder.add_edge("reporting", END)

    graph = builder.compile()

    initial_state: QAState = {
        "jira_ticket": jira_ticket or "",
        "requirement_note": requirement_note or "",
        "test_case_count": test_case_count,
        "automation_framework": automation_framework,
        "programming_language": programming_language,
        "execution_mode": execution_mode,
        "execute_test": execute_test,
        "headed": headed,
        "repair_attempts": 0,
        "execution": "Execution not requested.",
        "execution_exit_code": 0,
        "failure_detected": False,
        "healing": "Failure analysis not required.",
        "retry_execution": "Retry not performed.",
    }

    final_state = await graph.ainvoke(initial_state)

    return {
        "jira": final_state.get("jira_text", ""),
        "test_cases": final_state.get("test_cases", ""),
        "code": final_state.get("code", ""),
        "execution": final_state.get("execution", ""),
        "healing": final_state.get("healing", ""),
        "report": final_state.get("report", ""),
        "retry_execution": final_state.get("retry_execution", ""),
        "proposed_fix": final_state.get("proposed_fix"),
        "repair_attempts": final_state.get("repair_attempts", 0),
        "spec_path": final_state.get("spec_path", ""),
    }
