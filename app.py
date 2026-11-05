import asyncio
import os
import streamlit as st
import tempfile
import subprocess
from pathlib import Path
import re
from dotenv import load_dotenv
from pipeline import run_pipeline
from rag import retrieve_requirements, index_documents
from langchain_openrouter import ChatOpenRouter
load_dotenv()
from datetime import datetime

TEST_CASES_DIR = Path(__file__).resolve().parent / "generated_test_cases"

TEST_CASES_DIR.mkdir(parents=True, exist_ok=True)

def save_test_cases(test_cases: str) -> str:

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    file_path = TEST_CASES_DIR / f"test_cases_{timestamp}.md"

    file_path.write_text(test_cases, encoding="utf-8")
    return str(file_path)

# RAG test-case generation model. Set OPENROUTER_API_KEY in your .env file.

# You can override the model with OPENROUTER_MODEL in .env.

@st.cache_resource

def get_rag_model():

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:

        raise ValueError(

            "OPENROUTER_API_KEY is missing. Add it to your .env file and restart Streamlit."
        )

    return ChatOpenRouter(

       model=os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-v4.1-flash"),
         temperature=0,
         max_tokens=3000,
         api_key=api_key,
    )

def generate_test_cases(requirement: str) -> str:

    """Generate test cases grounded in indexed requirement documents."""

    context = retrieve_requirements(requirement, k=5)

    if not context or not context.strip():

        return (

            "Relevant requirement context was not found. Upload and index requirement "

            "documents first, or try a more specific requirement."

        )

    model = get_rag_model()
    prompt = f"""
You are a Senior QA Engineer. Generate clear, testable test cases using the
retrieved requirement context as the source of truth.

USER REQUEST:
{requirement}
RETRIEVED DOCUMENT CONTEXT:
{context}

Rules:
1. Generate positive, negative, boundary, and validation cases where applicable.
2. Do not invent business rules that are not supported by the context.
3. Explicitly call out missing or ambiguous requirements.
4. Use IDs TC01, TC02, TC03, and so on.
5. Return a Markdown table with columns:
   Test Case ID | Scenario | Preconditions | Test Steps | Test Data |
   Expected Result | Priority
6. Keep each test case specific and actionable.
"""
    response = model.invoke(prompt)
    content = getattr(response, "content", response)
    return str(content)

def generate_playwright_code(requirement: str, approved_test_cases: str) -> str:

    """Generate a Playwright Test TypeScript spec from the reviewed test cases."""
    model = get_rag_model()
    prompt = f"""
You are a senior Playwright TypeScript automation engineer.

APPLICATION BASE URL:
{os.getenv("AUT_BASE_URL", "Use the project's configured baseURL")}

REQUIREMENT:
{requirement}
APPROVED TEST CASES (SOURCE OF TRUTH):
{approved_test_cases}
Generate a single executable Playwright Test TypeScript spec file.
Rules:
- Automate only the approved test cases above; do not add unrelated cases.
- Preserve the expected results and assertions. Never weaken assertions to make tests pass.
- Import {{ test, expect }} from '@playwright/test'.
- Use stable role/label/test-id locators where supported by evidence.
- Do not invent locators, credentials, or application behavior. If details are unknown,
  use clearly marked TODO placeholders and explain them in comments.
- Use process.env for credentials; never hardcode secrets.
- Use the project's configured baseURL where possible; otherwise use the provided URL.
- Return the COMPLETE TypeScript file inside exactly one ```typescript code fence.
- Do not claim the code has been executed or passed.
"""
    response = model.invoke(prompt)
    content = getattr(response, "content", response)
    text = str(content)
    match = re.search(
        r"```(?:typescript|ts|javascript|js)?\s*\n(.*?)```",text,

        flags=re.IGNORECASE | re.DOTALL,

    )

    if not match:
        raise ValueError(
            "The model did not return a fenced TypeScript code block. "
            "Try generating the code again."
        )

    code = match.group(1).strip()
    if "from '@playwright/test'" not in code and 'from "@playwright/test"' not in code:
        raise ValueError(
            "Generated code does not import @playwright/test. "
            "Review the model output and regenerate."
        )
    return code + "\n"

def save_and_run_playwright_test(code: str):
    """Save a reviewed spec under tests/ and run only that spec."""

    project_dir = Path.cwd()
    tests_dir = project_dir / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    test_file = tests_dir / "rag_generated.spec.ts"

    # Require a Playwright Test import before writing executable code.
    if "from '@playwright/test'" not in code and 'from "@playwright/test"' not in code:
        raise ValueError("Code must import @playwright/test before it can be run.")

    test_file.write_text(code, encoding="utf-8")
    relative_test_file = test_file.relative_to(project_dir)
    try:
        result = subprocess.run(

            ["npx", "playwright", "test", str(relative_test_file), "--reporter=line"],

            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=300,
            shell=False,

        )

        output = result.stdout
        if result.stderr:

            output += "\nSTDERR:\n" + result.stderr
        return str(relative_test_file), result.returncode, output.strip()

    except subprocess.TimeoutExpired:
        return str(relative_test_file), 124, "Playwright execution timed out after 300 seconds."
    except OSError as exc:
        return str(relative_test_file), 1, f"Could not start Playwright Test: {exc}"



st.set_page_config(

    page_title="AI QA Automation Agent",

    page_icon="🧠",

    layout="wide",

    initial_sidebar_state="expanded",

)



st.markdown("""

<style>

.main {

    background: #f6f8fc;

}

.block-container {

    padding-top: 1.2rem;

    padding-bottom: 2rem;

    max-width: 1500px;

}

.hero {

    padding: 24px 28px;

    border-radius: 18px;

    background: linear-gradient(135deg, #172554 0%, #1d4ed8 55%, #0f766e 100%);

    color: white;

    margin-bottom: 20px;

}

.hero h1 {

    margin: 0;

    font-size: 32px;

}

.hero p {

    margin: 8px 0 0 0;

    opacity: .9;

    font-size: 15px;

}

.metric-card {

    background: white;

    border: 1px solid #e5e7eb;

    border-radius: 14px;

    padding: 18px;

    min-height: 105px;

    box-shadow: 0 2px 10px rgba(15,23,42,.04);

}

.metric-title {

    color: #64748b;

    font-size: 13px;

    font-weight: 600;

}

.metric-value {

    color: #0f172a;

    font-size: 27px;

    font-weight: 800;

    margin-top: 8px;

}

.pipeline {

    background: white;

    border: 1px solid #e5e7eb;

    border-radius: 14px;

    padding: 18px;

    margin: 18px 0;

}

.pipeline-step {

    text-align: center;

    padding: 12px 8px;

    border-radius: 12px;

    background: #f8fafc;

    border: 1px solid #e2e8f0;

    font-weight: 700;

    color: #1e293b;

}

.pipeline-arrow {

    text-align: center;

    font-size: 22px;

    color: #2563eb;

    padding-top: 12px;

}

.metric-card,

.section-card {

    background: white;

    border: 1px solid #e5e7eb;

    border-radius: 14px;

    padding: 20px;

    margin-bottom: 16px;

}

.small-muted {

    color: #64748b;

    font-size: 13px;

}

.status-pill {

    display: inline-block;

    padding: 5px 10px;

    border-radius: 999px;

    background: #dcfce7;

    color: #166534;

    font-size: 12px;

    font-weight: 700;

}

div[data-testid="stSidebar"] {

    background: #0f172a;

}

div[data-testid="stSidebar"] * {

    color: #e2e8f0;

}

</style>

""", unsafe_allow_html=True)



if "result" not in st.session_state:

    st.session_state.result = None



if "run_count" not in st.session_state:

    st.session_state.run_count = 0



with st.sidebar:

    st.markdown("## 🧠 AI QA AGENT")

    st.markdown(

        '<span class="status-pill">● Agent Online</span>',

        unsafe_allow_html=True

    )



    st.markdown("---")



    page = st.radio(

        "Navigation",

        [

            "Dashboard",

            "Jira",

            "Test Cases",

            "Requirements & RAG",

            "Automation",

            "Execution",

            "Self-Healing",

            "Reports"

        ],

        label_visibility="collapsed",

    )



    st.markdown("---")



    st.markdown("### Agent Stack")

    st.markdown("**Primary:** Playwright MCP")

    st.markdown("**Secondary:** Playwright CLI")

    st.markdown("**LLM:** OpenRouter")

    st.markdown("**Tracing:** LangSmith")

    st.markdown("**Deployment:** Docker / Render")



st.markdown("""
<div class="hero">
    <h1>AI QA Automation Agent</h1>
    <p>Jira → Test Cases → Automation</p>
</div>
""", unsafe_allow_html=True)






if page == "Dashboard":
    st.subheader("Automation Control Center")

    c1, c2, c3, c4 = st.columns(4)

    metrics = [
        ("Jira Tickets", "Optional"),
        ("Test Cases", "—"),
        ("Automation", "Playwright"),
        ("Execution", "Ready"),
    ]

    for col, (title, value) in zip([c1, c2, c3, c4], metrics):
        with col:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-title">{title}</div>
                    <div class="metric-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        '<div class="pipeline"><h3>Agent Pipeline</h3></div>',
        unsafe_allow_html=True,
    )

    p1, a1, p2, a2, p3, a3, p4 = st.columns(
        [2, 0.5, 2, 0.5, 2, 0.5, 2]
    )

    with p1:
        st.info("📋 Jira / Requirement")
    with a1:
        st.write("→")
    with p2:
        st.info("🧪 Test Design")
    with a2:
        st.write("→")
    with p3:
        st.info("💻 Playwright Code")
    with a3:
        st.write("→")
    with p4:
        st.info("▶️ Execute")
    

        with col:

            st.markdown(

                f'<div class="pipeline-step">{title}</div>',

                unsafe_allow_html=True

            )



    for col in [a1, a2, a3]:

        with col:

            st.markdown(

                '<div class="pipeline-arrow">→</div>',

                unsafe_allow_html=True

            )



    st.markdown("</div>", unsafe_allow_html=True)



    st.markdown("### Start QA Pipeline")



    left, right = st.columns([1.7, 1])



    with left:



        jira_ticket = st.text_input(

            "Jira Ticket ID (Optional)",

            placeholder="Example: ABC-123",

            key="dashboard_jira",

        )

#main

        requirement_note = st.text_area(

            "QA Requirement / Prompt",

            placeholder="Example: Generate login test cases",

            height=130,

        )



        st.caption(

            "Provide either a Jira ticket, a direct requirement, or both."

        )



    with right:



        test_case_count = st.number_input(

            "Number of Test Cases",

            min_value=1,

            max_value=50,

            value=10,

            step=1,

        )



        automation_framework = st.selectbox(

            "Automation Framework",

            ["Playwright", "Selenium"],

            index=0,

        )



        programming_language = st.selectbox(

            "Programming Language",

            ["TypeScript", "Python", "Java"],

            index=0,

        )



        execution_mode = st.selectbox(

            "Browser Execution",

            ["Playwright MCP", "Playwright CLI"],

            index=0,

        )



        execute_test = st.toggle(

            "Execute browser flow",

            value=False

        )



        headed = st.toggle(

            "Show browser window",

            value=False,

            disabled=execution_mode != "Playwright CLI",

        )



    run = st.button(

        "🚀 Run AI QA Pipeline",

        type="primary",

        use_container_width=True,

    )



    if run:



        jira_value = jira_ticket.strip()

        requirement_value = requirement_note.strip()



        if not jira_value and not requirement_value:



            st.error(

                "Please enter either a Jira Ticket or a QA Requirement."

            )



        else:



            try:



                with st.status(

                    "Running QA agent pipeline...",

                    expanded=True

                ) as status:



                    if jira_value:

                        st.write(

                            f"🎫 Fetching Jira requirement: {jira_value}"

                        )

                    else:

                        st.write(

                            "📝 Using direct QA requirement..."

                        )



                    st.write("🧪 Designing test coverage...")

                    st.write(

                        "💻 Generating Playwright-first automation..."

                    )



                    if execute_test:

                        st.write(

                            f"▶️ Executing with {execution_mode}..."

                        )



                    st.write("📊 Preparing QA report...")



                    result = asyncio.run(

                        run_pipeline(

                            jira_ticket=jira_value,

                            requirement_note=requirement_value,

                            test_case_count=int(test_case_count),

                            automation_framework=automation_framework,

                            programming_language=programming_language,

                            execution_mode=execution_mode,

                            execute_test=execute_test,

                            headed=headed,

                        )

                    )



                    st.session_state.result = result

                    st.session_state.run_count += 1



                    status.update(

                        label="QA pipeline completed",

                        state="complete"

                    )
                st.success("Pipeline completed successfully.")

            except Exception as exc:
                st.error(

                    f"Pipeline failed: {exc}"

                )



    if st.session_state.result:
        st.markdown("### Latest Run")
        r = st.session_state.result
        t1, t2, t3, t4, t5, t6 = st.tabs(

            [
                "🎫 Jira",
                "🧪 Test Cases",
                "💻 Automation",
                "▶️ Execution",
                "🔧 Self-Healing",
                "📊 Report",
            ]

        )
        with t1:
            st.markdown(r["jira"])
        with t2:
            st.markdown(r["test_cases"])

        with t3:
            st.code(
                r["code"],
                language="typescript"

            )
        with t4:
            st.markdown(r["execution"])
        with t5:
            st.markdown(r["healing"])

        with t6:
            st.markdown(r["report"])

elif page == "Jira":
    st.subheader("🎫 Jira Requirement")

    st.info(
        "Jira is optional. Enter a Jira ticket from the Dashboard "
        "when you want to fetch a requirement from Jira."
    )

    if st.session_state.result:
        st.markdown(
            st.session_state.result["jira"]
        )
    else:
        st.warning(
            "No Jira result available yet."
        )
elif page == "Test Cases":
    st.subheader("🧪 Test Design")
    if st.session_state.result:
        st.markdown(
            st.session_state.result["test_cases"]
        )
    else:
        st.warning(

            "Run the pipeline first."
        )
elif page == "Automation":

    st.subheader("💻 Automation Code")
    if st.session_state.result:

        st.code(
            st.session_state.result["code"],
            language="typescript"
        )
    else:
        st.warning(
            "Run the pipeline first."
        )

elif page == "Execution":
    st.subheader("▶️ Test Execution")
    st.caption(
        "Playwright MCP is the primary execution mode. "
        "Playwright CLI is available as an alternate mode."

    )
    if st.session_state.result:
        st.markdown(
            st.session_state.result["execution"]
        )
    else:
        st.warning(

            "No execution result available yet."

        )





elif page == "Self-Healing":



    st.subheader("🔧 AI Self-Healing")



    if st.session_state.result:

        st.markdown(

            st.session_state.result["healing"]

        )

    else:

        st.warning(

            "Self-healing output appears after an execution failure."

        )





elif page == "Reports":



    st.subheader("📊 QA Report")



    if st.session_state.result:

        st.markdown(

            st.session_state.result["report"]

        )

    else:

        st.warning(

            "Run the pipeline first."

        )





elif page == "Requirements & RAG":



    st.subheader("📄 Requirement Documents")

    st.caption(

        "Upload and index requirements, generate test cases, review them, "

        "then generate and optionally execute Playwright TypeScript code."

    )



    uploaded_files = st.file_uploader(

        "Upload requirement documents",

        type=["pdf", "docx", "txt", "md"],

        accept_multiple_files=True,

        key="requirement_document_uploader",

        help="Select one or more requirement documents."

    )



    if uploaded_files:

        st.write("Selected files:")

        for uploaded_file in uploaded_files:

            st.write(f"📎 {uploaded_file.name} ({uploaded_file.size:,} bytes)")



    if st.button("📚 Index Documents", type="primary", use_container_width=True):

        if not uploaded_files:

            st.warning("Please upload at least one document.")

        else:

            temp_paths = []

            try:

                with st.spinner("Reading and indexing requirement documents..."):

                    for uploaded_file in uploaded_files:

                        suffix = os.path.splitext(uploaded_file.name)[1].lower()

                        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:

                            temp_file.write(uploaded_file.getvalue())

                            temp_paths.append(temp_file.name)

                    chunk_count = index_documents(temp_paths)

                st.success(f"Indexing completed. {chunk_count} document chunk(s) processed.")

            except Exception as exc:

                st.error(f"Document indexing failed: {exc}")

            finally:

                for temp_path in temp_paths:

                    try:

                        if os.path.exists(temp_path):

                            os.remove(temp_path)

                    except OSError:

                        pass



    st.divider()

    st.subheader("🧪 Step 1 — Generate Test Cases from RAG")



    rag_requirement = st.text_area(

        "Requirement or feature to test",

        placeholder="Example: Generate test cases for login, password validation, and account lockout.",

        height=100,

        key="rag_requirement_input"

    )



    if st.button("🚀 Generate Test Cases", use_container_width=True):

        if not rag_requirement.strip():

            st.warning("Enter a requirement or feature first.")

        else:

            try:

                with st.spinner("Retrieving document context and generating test cases..."):

                    rag_result = generate_test_cases(rag_requirement.strip())

                if "Relevant requirement context was not found" in rag_result:

                    st.warning(rag_result)

                else:

                    st.session_state["rag_test_case_result"] = rag_result
                    saved_path = save_test_cases(rag_result)
                    st.session_state["rag_test_case_saved_path"] = saved_path

                    st.session_state["rag_approved"] = False

                    st.session_state.pop("rag_code_result", None)

                    st.session_state.pop("rag_execution_result", None)

                    st.success("Test cases generated and saved. Review or edit them below.")
                    st.caption(f"Saved location: {saved_path}")

            except Exception as exc:

                st.error(f"Test-case generation failed: {exc}")



    if st.session_state.get("rag_test_case_result"):

        st.markdown("### Step 2 — Review and approve test cases")

        edited_cases = st.text_area(

            "Edit test cases before code generation",

            value=st.session_state["rag_test_case_result"],

            height=320,

            key="rag_test_cases_editor",

            help="You can manually edit the Markdown test cases. The code generator will use this edited content."

        )

        st.download_button(

            "⬇️ Download Test Cases (Markdown)",

            data=edited_cases,

            file_name="approved_test_cases.md",

            mime="text/markdown",

            use_container_width=True

        )



        approved = st.checkbox(

            "I reviewed these test cases and approve them as the source of truth for automation.",

            key="rag_approve_test_cases"

        )



        st.divider()

        st.subheader("💻 Step 3 — Generate Playwright TypeScript Code")



        if st.button("🧩 Generate Playwright Code", use_container_width=True):

            if not approved:

                st.warning("Review and approve the test cases before generating code.")

            elif not edited_cases.strip():

                st.warning("Test cases cannot be empty.")

            else:

                try:

                    st.session_state["rag_approved_test_cases"] = edited_cases

                    with st.spinner("Generating code only for the approved test cases..."):

                        generated_code = generate_playwright_code(

                            rag_requirement.strip(),

                            edited_cases

                        )

                    st.session_state["rag_code_result"] = generated_code

                    st.session_state.pop("rag_execution_result", None)

                    st.success("Code generated. Review it before execution.")

                except Exception as exc:

                    st.error(f"Code generation failed: {exc}")



    if st.session_state.get("rag_code_result"):

        st.markdown("### Review generated automation code")

        st.warning(

            "AI-generated code has not been verified. Review locators, test data, "

            "baseURL and assertions before executing."

        )

        editable_code = st.text_area(

            "Playwright TypeScript spec",

            value=st.session_state["rag_code_result"],

            height=360,

            key="rag_code_editor"

        )

        st.download_button(

            "⬇️ Download Playwright Spec",

            data=editable_code,

            file_name="rag_generated.spec.ts",

            mime="text/plain",

            use_container_width=True

        )



        st.markdown("### Step 4 — Save and execute reviewed code")

        st.caption(

            "This writes the reviewed code to tests/rag_generated.spec.ts and runs "

            "only that file with the local Playwright Test runner."

        )

        if st.button("▶️ Save and Execute This Test", type="primary", use_container_width=True):

            try:

                with st.spinner("Saving the spec and running Playwright Test..."):

                    saved_file, return_code, output = save_and_run_playwright_test(editable_code)

                status = "PASSED" if return_code == 0 else "FAILED"

                st.session_state["rag_execution_result"] = {

                    "file": saved_file,

                    "return_code": return_code,

                    "status": status,

                    "output": output,

                }

            except Exception as exc:

                st.error(f"Could not save or execute the spec: {exc}")



    if st.session_state.get("rag_execution_result"):

        result = st.session_state["rag_execution_result"]

        st.subheader("📊 Step 5 — Execution result")

        st.write(f"**Spec file:** `{result['file']}`")

        if result["return_code"] == 0:

            st.success(f"Playwright result: {result['status']}")

        else:

            st.error(f"Playwright result: {result['status']} (exit code {result['return_code']})")

        st.code(result["output"] or "No console output returned.", language="text")

        if result["return_code"] != 0:

            st.info(

                "A failed run is not automatically self-healed in this RAG page yet. "

                "Use the failure output to diagnose the issue; don't change assertions "

                "just to make the test pass."

            )


