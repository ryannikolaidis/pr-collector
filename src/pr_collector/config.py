"""Configuration management for pr-collector."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_DIR = Path.home() / ".pr-collector"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.yaml"


def get_config_dir() -> Path:
    """Get the configuration directory path."""
    return Path(os.getenv("PR_COLLECTOR_CONFIG_DIR", DEFAULT_CONFIG_DIR))


def get_config_file() -> Path:
    """Get the configuration file path."""
    config_dir = get_config_dir()
    return config_dir / "config.yaml"


def load_config() -> dict[str, Any]:
    """Load configuration from file."""
    config_file = get_config_file()

    if not config_file.exists():
        return {}

    try:
        with config_file.open("r") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        # If config file is corrupted, return empty config
        return {}


def save_config(config: dict[str, Any]) -> None:
    """Save configuration to file."""
    config_file = get_config_file()
    config_dir = config_file.parent

    # Ensure config directory exists
    config_dir.mkdir(parents=True, exist_ok=True)

    with config_file.open("w") as f:
        yaml.safe_dump(config, f, default_flow_style=False)


def get_github_token() -> str | None:
    """Get GitHub token from config, environment, or return None."""
    # Priority: CLI option > environment variable > config file
    token = os.getenv("GITHUB_TOKEN")
    if token:
        return token

    config = load_config()
    return config.get("github_token")


def set_github_token(token: str) -> None:
    """Set GitHub token in config."""
    config = load_config()
    config["github_token"] = token
    save_config(config)


def get_default_output_dir() -> str:
    """Get default output directory from config."""
    config = load_config()
    return config.get("default_output_dir", ".")


def set_default_output_dir(output_dir: str) -> None:
    """Set default output directory in config."""
    config = load_config()
    config["default_output_dir"] = output_dir
    save_config(config)


def create_default_config() -> dict[str, Any]:
    """Create a default configuration."""
    return {
        "github_token": None,
        "default_output_dir": ".",
    }


def ensure_config_exists() -> None:
    """Ensure configuration file exists with defaults."""
    config_file = get_config_file()
    if not config_file.exists():
        save_config(create_default_config())
