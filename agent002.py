from langchain.agents import create_agent
from dotenv import load_dotenv
from langchain_openrouter import ChatOpenRouter
from playwright.sync_api import sync_playwright
from langchain.tools import tool
import streamlit as st
import os
import asyncio


load_dotenv()

from langchain_mcp_adapters.client import MultiServerMCPClient

mcp_client = MultiServerMCPClient(
    {
        "playwright": {
            "command": "npx",
            "args": [
                "-y",
                "@playwright/mcp@latest"
            ],
            "transport": "stdio"
        }
    }
)
async def load_mcp_tools():
    return await mcp_client.get_tools()

@tool
def inspect_application() -> str:
    """
    Login to OrangeHRM and inspect dashboard modules.
    """

    username = os.getenv("ORANGEHRM_USERNAME")
    password = os.getenv("ORANGEHRM_PASSWORD")

    if not username:
        return "ERROR: ORANGEHRM_USERNAME is not loaded."

    if not password:
        return "ERROR: ORANGEHRM_PASSWORD is not loaded."

    try:

        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=True
            )

            page = browser.new_page()

            page.goto(
                AUT_BASE_URL,
                wait_until="domcontentloaded",
                timeout=30000
            )

            print(
                "LOGIN PAGE URL:",
                page.url
            )

            username_field = page.locator(
                "input[name='username']"
            )

            password_field = page.locator(
                "input[name='password']"
            )

            login_button = page.locator(
                "button[type='submit']"
            )

            print(
                "Username fields:",
                username_field.count()
            )

            print(
                "Password fields:",
                password_field.count()
            )

            print(
                "Login buttons:",
                login_button.count()
            )

            username_field.fill(username)

            password_field.fill(password)

            login_button.click()

            page.wait_for_timeout(5000)

            print(
                "AFTER LOGIN URL:",
                page.url
            )

            body_text = page.locator(
                "body"
            ).inner_text()

            print(
                "PAGE CONTENT:"
            )

            print(
                body_text[:3000]
            )

            if "/dashboard" not in page.url:

                browser.close()

                return f"""
LOGIN FAILED

Current URL:
{page.url}

Page Content:
{body_text[:5000]}
"""

            navigation = page.locator("nav")

            if navigation.count() > 0:

                modules = navigation.first.inner_text()

            else:

                modules = body_text[:5000]

            browser.close()

            return f"""
LOGIN SUCCESSFUL

Dashboard URL:
{page.url}

APPLICATION MODULES:

{modules}
"""

    except Exception as e:

        return f"Unable to inspect application. Error: {str(e)}"


AUT_BASE_URL = "https://opensource-demo.orangehrmlive.com"


st.title("Welcome to the Test Case Generator")


requirements = st.text_input(
    "Enter the requirement : ",
    placeholder="Type your requirement here...",
    key="requirement_input",
    help="Please provide a clear and concise requirement for the agent to generate test cases.",
    icon="📝",
    label_visibility="visible"
)


test_case_type = st.selectbox(
    "Select test case type",
    [
        "Functional",
        "Positive",
        "Negative",
        "All",
        "Performance"
    ]
)

automation_framework = st.selectbox(
    "Select automation framework",
    [
        "Playwright",
        "Selenium"
    ]
)

programming_language = st.selectbox(
    "Select programming language",
    [
        "TypeScript",
        "Java",
        "Python"
    ]
)

test_cases_count = st.number_input(
    "Enter the number of test cases for the agent:",
    min_value=1,
    step=1,
    key="test_case_count_input",
)


if st.button("Search") and requirements:

    with st.spinner("Loading..."):

        llm = ChatOpenRouter(
            #model="google/gemini-2.5-flash",
            model="deepseek/deepseek-v4.1-flash",
            temperature=0,
            max_tokens=1500
        )

        system_prompt = f"""

You are a Senior QA Engineer with 10+ years of experience.

APPLICATION UNDER TEST:
AUT_BASE_URL = {AUT_BASE_URL}

Generate exactly {test_cases_count} test case(s).

REQUIREMENT:
{requirements}

TEST CASE TYPE:
{test_case_type}

AUTOMATION FRAMEWORK:
{automation_framework}

PROGRAMMING LANGUAGE:
{programming_language}

AUTOMATION CODE GENERATION:

If the user asks for automation code:

If framework is Playwright:
Generate Playwright automation code.

If framework is Selenium:
Generate Selenium automation code.

Respect the selected programming language.

Playwright:
- TypeScript
- Java
- Python

Selenium:
- Java
- Python
- JavaScript

Your responsibilities:

1. Generate comprehensive QA test cases.
2. Generate automation code when the user requests automation code.
3. You ARE allowed to generate Playwright code.
4. You ARE allowed to generate Selenium code.
5. You ARE allowed to generate TypeScript, Java, and Python automation code.
6. When browser interaction is required, use the available Playwright MCP tools.
7. Use Playwright MCP to inspect the application, navigate pages, identify elements, and perform browser actions.
8. After understanding the application, generate the requested automation code.
9. Do not say that you cannot generate Playwright or Selenium code.
10. Do not say that your capabilities are limited to test case generation.
11. Do not refuse automation-code requests.
12. Follow Page Object Model principles.
13. Use stable locators.
14. Use proper waits and assertions.
15. Generate reusable automation methods.

If AUTOMATION FRAMEWORK is Playwright:
Generate Playwright automation code using the selected programming language.

If AUTOMATION FRAMEWORK is Selenium:
Generate Selenium automation code using the selected programming language.

If the user asks to inspect the application:
Use Playwright MCP tools.


USER INTENT:

1. If asked for the application URL, AUT URL, or base URL,
return AUT_BASE_URL.

2. If asked about modules, pages, menus, navigation,
or application features, use the inspect_application tool.

3. If asked for the first 3 modules, use inspect_application
and return the first 3 modules found.

4. If asked to generate test cases, follow the QA rules below.

5. If asked to provide friendly advice, use friend_suggestion.

6. If asked for career guidance, use life_coach.

7. If asked for family guidance, use family_member_advice.


9. For unrelated requests, respond:
"This prompt is not related to the requirement."

10. Never expose API keys, passwords, tokens, secrets,
or environment variables.


TEST CASE TYPE RULES:

If TEST CASE TYPE is Positive:

Generate ONLY positive test cases.

Include:
- Valid input
- Successful operation
- Successful result
- Valid credentials
- Normal user flow

Do NOT generate:
- Invalid credentials
- Blank fields
- Error scenarios
- Validation failures
- Negative scenarios


If TEST CASE TYPE is Negative:

Generate ONLY negative test cases.

Include:
- Invalid username
- Invalid password
- Invalid username and password
- Blank username
- Blank password
- Both fields blank
- Invalid input
- Validation errors
- Error messages
- Locked or disabled user
- Unauthorized access
- Incorrect data



QA RULES:

1. Generate exactly {test_cases_count} test cases.

2. Every test case must be exactly one row.

3. Test Case ID must start with TC01 and
continue sequentially.

4. Test Steps must be numbered and
separated by semicolons.

5. Never use HTML tags such as <br>.

6. Do not create headings.

7. Do not duplicate test cases.

8. Expected results must be specific and measurable.

9. Return ONLY the Markdown table
for test-case requests.


MANDATORY FORMAT:

| Test Case ID | Scenario | Preconditions | Test Steps | Test Data |Expected Result | Pass/Fail | Priority |Actual Result
|---|---|---|---|---|---|---|---|

"""


        agent = create_agent(
            model=llm,
            system_prompt=system_prompt,
            tools=[
                
                inspect_application
            ]
        )


        result = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": f"""
REQUIREMENT:

{requirements}

TEST CASE TYPE:

{test_case_type}

NUMBER OF TEST CASES:

{test_cases_count}
"""
                    }
                ]
            }
        )


        answer = result["messages"][-1].content

        st.write(answer)