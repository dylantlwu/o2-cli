"""Shared fixtures.

Every CLI invocation runs `ensure_skill_installed()` and `check_for_update()`
in the root callback. Both touch the outside world — the first writes skill
files into the user's home directory, the second makes a network call. Tests
must not do either, so they are neutralised for the whole suite.
"""

import pytest
from typer.testing import CliRunner


@pytest.fixture(autouse=True)
def no_side_effects(monkeypatch):
    """Stop the root callback from writing to $HOME or hitting the network."""
    monkeypatch.setattr("o2_cli.cli.ensure_skill_installed", lambda *a, **k: None)
    monkeypatch.setattr("o2_cli.cli.check_for_update", lambda *a, **k: None)


@pytest.fixture
def runner():
    return CliRunner()
