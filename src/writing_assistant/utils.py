"""Utility functions for I/O and clipboard."""
#src/writing_assistant/utils.py
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import pyperclip


def read_input(
    text: Optional[str] = None,
    input_file: Optional[Path] = None,
    from_clipboard: bool = False,
    from_stdin: bool = False,
) -> str:
    """Read input from various sources with priority order."""
    if text:
        return text

    if from_clipboard:
        try:
            return pyperclip.paste()
        except Exception as e:
            print(f"[error] Failed to read clipboard: {e}", file=sys.stderr)
            sys.exit(1)

    if input_file:
        try:
            return input_file.read_text(encoding="utf-8")
        except Exception as e:
            print(f"[error] Failed to read file {input_file}: {e}", file=sys.stderr)
            sys.exit(1)

    if from_stdin:
        print("[info] Reading from stdin. Press Ctrl+D (Unix) or Ctrl+Z then Enter (Windows) to finish.")
        try:
            return sys.stdin.read()
        except KeyboardInterrupt:
            print("\n[info] Cancelled.", file=sys.stderr)
            sys.exit(0)

    return ""


def write_output(
    text: str,
    output_file: Optional[Path] = None,
    to_clipboard: bool = False,
    show_stats: bool = True,
) -> None:
    """Write output to various destinations."""
    # Strip stats line if not showing stats
    if not show_stats and "[Stats:" in text:
        text = text.split("\n\n[Stats:")[0]

    if output_file:
        try:
            output_file.write_text(text, encoding="utf-8")
            print(f"[info] Output written to {output_file}")
        except Exception as e:
            print(f"[error] Failed to write file {output_file}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(text)

    if to_clipboard:
        try:
            pyperclip.copy(text)
            print("[info] Result copied to clipboard.")
        except Exception as e:
            print(f"[warning] Failed to copy to clipboard: {e}", file=sys.stderr)


def clean_response(text: str) -> str:
    """Clean up model output: strip quotes, markdown blocks, etc."""
    text = text.strip()
    # Remove markdown code blocks
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    # Remove surrounding quotes
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        text = text[1:-1]
    return text.strip()
