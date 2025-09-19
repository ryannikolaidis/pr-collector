"""Tests for pr_collector modules."""

from typer.testing import CliRunner

from pr_collector.app import (
    build_greeting,
    get_application_info,
    get_config_messages,
)
from pr_collector.cli import app

runner = CliRunner()


def test_build_greeting_defaults() -> None:
    """Application logic returns default greeting."""

    assert build_greeting() == "Hello World!"
    assert build_greeting(name="Alice") == "Hello Alice!"


def test_build_greeting_loud() -> None:
    """Application logic can shout the greeting."""

    assert build_greeting(name="Bob", loud=True) == "HELLO BOB!"


def test_get_application_info() -> None:
    """Application metadata includes expected fields."""

    metadata = get_application_info()
    assert metadata["name"] == "pr-collector"
    assert metadata["description"] == "A Python project called pr-collector"
    assert metadata["version"] == "0.1.0"


def test_get_config_messages() -> None:
    """Configuration helper returns appropriate messages."""

    assert get_config_messages(show=False)[0] == "Configuration created!"
    assert "logic" in get_config_messages(show=True)[1]


def test_hello_command() -> None:
    """Test hello command with default name."""

    result = runner.invoke(app, ["hello"])
    assert result.exit_code == 0
    assert "Hello World!" in result.stdout


def test_hello_command_with_name() -> None:
    """Test hello command with custom name."""

    result = runner.invoke(app, ["hello", "--name", "Alice"])
    assert result.exit_code == 0
    assert "Hello Alice!" in result.stdout


def test_hello_command_loud() -> None:
    """Test hello command with loud option."""

    result = runner.invoke(app, ["hello", "--name", "Bob", "--loud"])
    assert result.exit_code == 0
    assert "HELLO BOB!" in result.stdout


def test_info_command() -> None:
    """Test info command."""

    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0
    assert "pr-collector" in result.stdout
    assert "0.1.0" in result.stdout


def test_config_command() -> None:
    """Test config command."""

    result = runner.invoke(app, ["config"])
    assert result.exit_code == 0
    assert "Configuration created!" in result.stdout


def test_config_show() -> None:
    """Test config command with show option."""

    result = runner.invoke(app, ["config", "--show"])
    assert result.exit_code == 0
    assert "No configuration file found" in result.stdout


def test_help() -> None:
    """Test help output."""

    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "A Python project called pr-collector" in result.stdout
