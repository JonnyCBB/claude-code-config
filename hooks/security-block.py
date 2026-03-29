#!/usr/bin/env python3
"""
Security blocking hook for Claude Code.
Blocks dangerous bash commands and protects sensitive files.
"""

import json
import re
import sys

# Dangerous bash command patterns
DANGEROUS_BASH_PATTERNS = [
    r"rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|rf|-[a-zA-Z]*f[a-zA-Z]*r)\s",  # rm -rf variants
    r">\s*/dev/(?!null|stderr|stdout)",  # Redirect to /dev devices (excluding null/stderr/stdout)
    r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;?\s*:",  # Fork bomb
    r"curl\s+.*\|\s*(ba)?sh",  # Piped curl to shell
    r"wget\s+.*\|\s*(ba)?sh",  # Piped wget to shell
    r"mkfs\.",  # Format filesystem
    r"dd\s+if=",  # dd command (disk destroyer)
]

# Protected file patterns
PROTECTED_FILE_PATTERNS = [
    ".env",
    ".git/",
    "credentials",
    "secrets",
    "id_rsa",
    "id_ed25519",
    ".pem",
    ".key",
    "password",
    ".netrc",
    ".npmrc",  # Can contain auth tokens
    ".pypirc",  # Can contain auth tokens
]


def check_bash_command(command: str) -> tuple[bool, str]:
    """Check if a bash command is dangerous."""
    for pattern in DANGEROUS_BASH_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, f"Dangerous command pattern blocked: {pattern}"
    return False, ""


def check_file_path(file_path: str) -> tuple[bool, str]:
    """Check if a file path is protected."""
    for pattern in PROTECTED_FILE_PATTERNS:
        if pattern in file_path.lower():
            return True, f"Protected file pattern blocked: {pattern}"
    return False, ""


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        sys.exit(0)  # Allow on parse error

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Check bash commands
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        is_dangerous, reason = check_bash_command(command)
        if is_dangerous:
            print(f"BLOCKED: {reason}", file=sys.stderr)
            sys.exit(2)

    # Check file operations
    if tool_name in ["Edit", "Write", "MultiEdit"]:
        file_path = tool_input.get("file_path", "")
        is_protected, reason = check_file_path(file_path)
        if is_protected:
            print(f"BLOCKED: {reason}", file=sys.stderr)
            sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
