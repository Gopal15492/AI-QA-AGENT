
import os
import subprocess
from pathlib import Path

from config import COPILOT_CLI_COMMAND, COPILOT_TIMEOUT


def call_copilot(prompt: str) -> str:
    """Send a prompt to GitHub Copilot CLI and return its response."""

    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    project_root = Path(__file__).resolve().parent

    command = [
        COPILOT_CLI_COMMAND,
        "-p",
        prompt,
        "-s",
    ]

    try:
        result = subprocess.run(
            command,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=COPILOT_TIMEOUT,
            shell=(os.name == "nt"),
        )

        if result.returncode != 0:
            error = result.stderr.strip() or result.stdout.strip()
            raise RuntimeError(
                f"Copilot CLI failed (exit code "
                f"{result.returncode}): {error}"
            )

        response = result.stdout.strip()

        if not response:
            raise RuntimeError("Copilot CLI returned an empty response.")

        return response

    except subprocess.TimeoutExpired as exc:
        raise TimeoutError(
            f"Copilot CLI timed out after {COPILOT_TIMEOUT} seconds."
        ) from exc

    except FileNotFoundError as exc:
        raise RuntimeError(
            "Copilot CLI was not found. Verify installation and PATH."
        ) from exc
