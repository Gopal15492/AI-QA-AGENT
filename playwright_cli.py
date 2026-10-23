import os
import shutil
import subprocess
from pathlib import Path

CLI_COMMAND = os.getenv("PLAYWRIGHT_CLI_COMMAND", "playwright-cli")


def cli_available():
    return shutil.which(CLI_COMMAND) is not None


def run_cli(args, timeout=120, cwd=None):
    command = [CLI_COMMAND, *args]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd or os.getcwd(),
            shell=False,
        )
        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR:\n{result.stderr}"
        return result.returncode, output.strip()
    except subprocess.TimeoutExpired as exc:
        return 124, f"Playwright CLI timed out after {timeout}s: {exc}"
    except OSError as exc:
        return 1, f"Could not run Playwright CLI: {exc}"


def open_page(url, session="qa-agent", headed=False):
    args = [f"-s={session}", "open", url]
    if headed:
        args.append("--headed")
    return run_cli(args)


def snapshot(session="qa-agent"):
    return run_cli([f"-s={session}", "snapshot"])


def screenshot(session="qa-agent"):
    return run_cli([f"-s={session}", "screenshot"])


def close(session="qa-agent"):
    return run_cli([f"-s={session}", "close"])


def run_playwright_test(test_file, timeout=180, cwd=None):
    """Run an existing Playwright Test file using the project's local npx."""
    test_path = Path(test_file)
    if not test_path.exists():
        return 1, f"Test file not found: {test_file}"
    try:
        result = subprocess.run(
            ["npx", "playwright", "test", str(test_path), "--reporter=line"],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd or os.getcwd(),
            shell=False,
        )
        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR:\n{result.stderr}"
        return result.returncode, output.strip()
    except subprocess.TimeoutExpired:
        return 124, f"Playwright test timed out after {timeout}s."
    except OSError as exc:
        return 1, f"Could not run Playwright Test: {exc}"
