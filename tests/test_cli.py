import pytest
from click.testing import CliRunner
from orchify.cli import main


@pytest.fixture
def runner():
    return CliRunner()


def test_hello_command(runner):
    result = runner.invoke(main, ["hello"])
    assert result.exit_code == 0
    assert "👋 Welcome to Orchify!" in result.output


def test_main_help(runner):
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Usage: main" in result.output
    assert "hello" in result.output
    assert "scan" in result.output
    assert "gen" in result.output


def test_unknown_command(runner):
    result = runner.invoke(main, ["unknown"])
    assert result.exit_code != 0
    assert "No such command" in result.output
