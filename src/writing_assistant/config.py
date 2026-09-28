"""Configuration loading and management."""

from __future__ import annotations

import os
import platform
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG = {
    "ollama": {
        "host": "http://localhost:11434",
        "model": "llama3.2:3b-instruct-q4_K_M",
        "temperature": 0.3,
        "max_tokens": 2048,
        "timeout": 60,
    },
    "output": {
        "streaming": True,
        "show_stats": True,
        "copy_to_clipboard": False,
    },
    "prompts": {
        "correct": (
            "You are an expert editor and proofreader. Correct grammar, spelling, "
            "and punctuation errors with minimal changes. Preserve meaning and tone. "
            "Do not add explanations. Output ONLY the corrected text."
        ),
        "improve": (
            "You are a skilled writing coach. Improve phrasing, word choice, and "
            "sentence structure while preserving meaning. Do not add explanations. "
            "Output ONLY the improved text."
        ),
        "rewrite_formal": (
            "Rewrite the following text in a formal tone. Use proper, polite language. "
            "Output ONLY the rewritten text."
        ),
        "rewrite_casual": (
            "Rewrite the following text in a casual, conversational tone. "
            "Output ONLY the rewritten text."
        ),
        "rewrite_professional": (
            "Rewrite the following text in a professional workplace tone. "
            "Output ONLY the rewritten text."
        ),
        "rewrite_concise": (
            "Rewrite the following text to be as concise as possible. "
            "Output ONLY the rewritten text."
        ),
        "rewrite_expanded": (
            "Rewrite the following text to be more detailed and elaborate. "
            "Output ONLY the rewritten text."
        ),
        "rewrite_persuasive": (
            "Rewrite the following text to be compelling and persuasive. "
            "Output ONLY the rewritten text."
        ),
        "rewrite_academic": (
            "Rewrite the following text in an academic tone. Use objective, precise language. "
            "Output ONLY the rewritten text."
        ),
        "rewrite_creative": (
            "Rewrite the following text in a creative, vivid style. "
            "Output ONLY the rewritten text."
        ),
        "rewrite_simple": (
            "Rewrite the following text in plain, simple English. A 10-year-old should understand it. "
            "Output ONLY the rewritten text."
        ),
    },
}


def _get_config_dir() -> Path:
    """Return the platform-specific config directory."""
    system = platform.system()
    if system == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming"))
    elif system == "Darwin":
        base = Path.home() / "Library/Application Support"
    else:
        base = Path.home() / ".config"
    return base / "local-writing-assistant"


def _find_config_file() -> Path | None:
    """Search for config.yaml in common locations."""
    candidates = [
        Path.cwd() / "config.yaml",
        Path.cwd() / "config.yml",
        _get_config_dir() / "config.yaml",
        _get_config_dir() / "config.yml",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def load_config() -> dict[str, Any]:
    """Load and merge configuration from file with defaults."""
    config = _deep_copy(DEFAULT_CONFIG)
    config_path = _find_config_file()

    if config_path:
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = yaml.safe_load(f) or {}
            config = _deep_merge(config, user_config)
        except Exception as e:
            print(f"[warning] Failed to load config from {config_path}: {e}")

    # Allow environment variable overrides
    if os.getenv("OLLAMA_HOST"):
        config["ollama"]["host"] = os.getenv("OLLAMA_HOST")
    if os.getenv("OLLAMA_MODEL"):
        config["ollama"]["model"] = os.getenv("OLLAMA_MODEL")

    return config


def _deep_copy(obj: Any) -> Any:
    """Simple deep copy for dict/list primitives."""
    import copy
    return copy.deepcopy(obj)


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base."""
    result = _deep_copy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def get_prompt(config: dict, mode: str, tone: str | None = None) -> str:
    """Get the system prompt for a given mode/tone."""
    prompts = config.get("prompts", {})
    if mode == "rewrite" and tone:
        key = f"rewrite_{tone}"
    else:
        key = mode
    return prompts.get(key, prompts.get("correct", ""))
