import os
from dotenv import load_dotenv
from langchain_openrouter import ChatOpenRouter
from langchain.agents import create_agent

load_dotenv()


def create_llm(max_tokens=4000):
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is missing from .env")
    return ChatOpenRouter(
        model=os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-v4.1-flash"),
        api_key=api_key,
        temperature=0,
        max_tokens=max_tokens,
    )


def build_jira_agent(llm, tools):
    prompt = """You are the Jira Requirement Fetcher Agent.
Use available browser tools to fetch the requested Jira ticket.
Extract key, summary, description, acceptance criteria, priority, status,
labels and components. Do not invent missing values."""
    return create_agent(model=llm, system_prompt=prompt, tools=tools)


def build_test_design_agent(llm):
    prompt = """You are a Senior QA Test Design Agent.
Create exactly the requested number of comprehensive test cases grounded in
the supplied requirements. Cover positive, negative, boundary, validation,
error handling, security and UI scenarios when relevant.
Return only a Markdown table with columns:
Test Case ID, Scenario, Preconditions, Test Steps, Test Data,
Expected Result, Priority. Do not invent unsupported business rules."""
    return create_agent(model=llm, system_prompt=prompt, tools=[])


def build_code_agent(llm):
    prompt = """You are a Senior QA Automation Engineer.
Generate executable automation code for the supplied cases.
Prefer Playwright TypeScript when selected. Use stable locators, assertions,
sensible waits and Page Object Model where appropriate. Do not invent app
behavior. If locators are unknown, clearly mark them as needing validation.
Return the complete code in a fenced code block and name the proposed file."""
    return create_agent(model=llm, system_prompt=prompt, tools=[])


def build_execution_agent(llm, tools):
    prompt = """You are a QA Test Execution Agent.
Use supplied browser tools to execute only the relevant scenario.
Inspect before interacting. Do not claim PASS unless expected behavior was
actually verified. Return steps, actual result, PASS/FAIL, and evidence."""
    return create_agent(model=llm, system_prompt=prompt, tools=tools)


def build_cli_planner_agent(llm):
    prompt = """You are a Playwright CLI Execution Planner.
Use only commands supported by the installed Playwright CLI. Do not invent
snapshot refs. Return one command per line and no unrelated shell commands."""
    return create_agent(model=llm, system_prompt=prompt, tools=[])


def build_self_healing_agent(llm):
    prompt = """You are a QA failure-analysis agent.
Analyze the actual failure output, test code and requirement. Return:
1. Failure classification (automation, application defect, environment, data,
   or inconclusive)
2. Evidence and likely root cause
3. Recommended fix
4. Proposed updated code in a fenced code block if justified
5. Whether retry is appropriate
Never weaken/remove assertions just to make a test pass. Do not claim that
you executed or validated a fix. Treat proposed code as untrusted until reviewed
and independently rerun."""
    return create_agent(model=llm, system_prompt=prompt, tools=[])


def build_reporting_agent(llm):
    prompt = """You are a QA Reporting Agent. Summarize requirement, coverage,
execution mode, original result, retry result, failures, self-healing analysis,
and final status. Distinguish verified facts from AI recommendations.
Do not invent passed/failed counts if unavailable."""
    return create_agent(model=llm, system_prompt=prompt, tools=[])
