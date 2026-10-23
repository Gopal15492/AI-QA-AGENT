import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
AUT_BASE_URL = os.getenv("AUT_BASE_URL", "https://opensource-demo.orangehrmlive.com")
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "")
JIRA_USERNAME = os.getenv("JIRA_USERNAME", "")
JIRA_PASSWORD = os.getenv("JIRA_PASSWORD", "")


import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# AI provider: "copilot_cli" or "openrouter"
AI_PROVIDER = os.getenv("AI_PROVIDER", "copilot_cli").lower()

# Copilot CLI configuration
COPILOT_CLI_COMMAND = os.getenv("COPILOT_CLI_COMMAND", "copilot")
COPILOT_MODEL = os.getenv("COPILOT_MODEL", "")
COPILOT_TIMEOUT = int(os.getenv("COPILOT_TIMEOUT", "180"))

# Existing OpenRouter configuration (optional fallback/provider)
OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "google/gemini-2.5-flash"
)

# Application configuration
AUT_BASE_URL = os.getenv(
    "AUT_BASE_URL",
    "https://opensource-demo.orangehrmlive.com"
)

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "")
JIRA_USERNAME = os.getenv("JIRA_USERNAME", "")
JIRA_PASSWORD = os.getenv("JIRA_PASSWORD", "")

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent
TESTS_DIR = PROJECT_ROOT / "tests"
GENERATED_TEST_CASES_DIR = PROJECT_ROOT / "generated_test_cases"

TESTS_DIR.mkdir(parents=True, exist_ok=True)
GENERATED_TEST_CASES_DIR.mkdir(parents=True, exist_ok=True)

# Safe automatic repair limits
MAX_SELF_HEAL_RETRIES = int(
    os.getenv("MAX_SELF_HEAL_RETRIES", "2")
)
 # When copilot subscripti
# import os
# from pathlib import Path
# from dotenv import load_dotenv

# load_dotenv()

# AI provider: "copilot_cli" or "openrouter"
AI_PROVIDER = os.getenv("AI_PROVIDER", "copilot_cli").lower()

# Copilot CLI configuration
COPILOT_CLI_COMMAND = os.getenv("COPILOT_CLI_COMMAND", "copilot")
COPILOT_MODEL = os.getenv("COPILOT_MODEL", "")
COPILOT_TIMEOUT = int(os.getenv("COPILOT_TIMEOUT", "180"))

# Existing OpenRouter configuration (optional fallback/provider)
OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "google/gemini-2.5-flash"
)

# Application configuration
AUT_BASE_URL = os.getenv(
    "AUT_BASE_URL",
    "https://opensource-demo.orangehrmlive.com"
)

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "")
JIRA_USERNAME = os.getenv("JIRA_USERNAME", "")
JIRA_PASSWORD = os.getenv("JIRA_PASSWORD", "")

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent
TESTS_DIR = PROJECT_ROOT / "tests"
GENERATED_TEST_CASES_DIR = PROJECT_ROOT / "generated_test_cases"

TESTS_DIR.mkdir(parents=True, exist_ok=True)
GENERATED_TEST_CASES_DIR.mkdir(parents=True, exist_ok=True)

# Safe automatic repair limits
MAX_SELF_HEAL_RETRIES = int(
    os.getenv("MAX_SELF_HEAL_RETRIES", "2")
)

