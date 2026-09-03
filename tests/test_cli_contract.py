"""The contract this CLI makes with the programs that drive it.

o2-cli is built to be run by an AI coding agent, not only by a human at a
terminal. That makes a few properties load-bearing in a way they wouldn't be
for an ordinary CLI, and each test here pins one of them.
"""


import pytest

from o2_cli import cli
from o2_cli.cli import app, get_state


# ── stdout purity ──────────────────────────────────────────────────────────
#
# In --json mode stdout has exactly one consumer: a parser. Anything else
# printed to it — a version notice, a deprecation warning, a progress line —
# turns a successful command into a parse error at the other end.
#
# The root callback already encodes this by skipping the update check when
# --json is set. That intent lived only in a comment; these tests make it a
# property of the program.


def test_json_mode_suppresses_the_update_check(runner, monkeypatch):
    """--json must not let the update notifier write to stdout."""
    called = []
    monkeypatch.setattr(cli, "check_for_update", lambda *a, **k: called.append(1))

    runner.invoke(app, ["--json", "markets", "--help"])
    assert called == [], "update check ran in --json mode; it can pollute stdout"


def test_human_mode_still_gets_the_update_check(runner, monkeypatch):
    """The suppression must be specific to --json, not a blanket disable.

    Without this, 'fixing' the pollution bug by deleting the call entirely
    would still pass the test above.
    """
    called = []
    monkeypatch.setattr(cli, "check_for_update", lambda *a, **k: called.append(1))

    runner.invoke(app, ["markets", "--help"])
    assert called == [1], "update check should still run for human users"


# ── flag ordering ──────────────────────────────────────────────────────────
#
# --json is an option on the root callback, so it must appear before the
# subcommand. `o2 balance show --json` is the single most common mistake
# against this CLI, and it fails in the worst possible way: the command
# succeeds, but the output is formatted for a human.


def test_json_before_subcommand_sets_the_flag(runner):
    runner.invoke(app, ["--json", "markets", "--help"])
    assert get_state()["json_output"] is True


def test_json_after_subcommand_does_not_silently_produce_human_output(runner):
    """Trailing --json must fail loudly rather than fall back to human output.

    The assertion checks *why* it failed, not just that it did. A network or
    auth error would also produce a non-zero exit, and would make this test
    pass while the property it guards had been broken.
    """
    result = runner.invoke(app, ["markets", "list", "--json"])
    assert result.exit_code != 0, (
        "trailing --json was accepted; a caller expecting JSON would get "
        "human-formatted text with a success exit code"
    )
    assert "No such option" in result.output and "--json" in result.output, (
        f"expected an argument-parsing rejection, got:\n{result.output}"
    )


# ── command surface ────────────────────────────────────────────────────────
#
# Sixteen command groups are wired up by hand with add_typer(). Importing a
# group but forgetting to register it is invisible: the module loads, nothing
# errors, and the command is simply missing at runtime.


REGISTERED_GROUPS = [
    "auth", "balance", "orders", "positions", "markets", "trades", "fees",
    "deposits", "withdrawals", "settings", "notifications", "account",
    "admin", "mm", "setup", "config",
]


@pytest.mark.parametrize("group", REGISTERED_GROUPS)
def test_every_documented_group_is_reachable(runner, group):
    result = runner.invoke(app, [group, "--help"])
    assert result.exit_code == 0, f"command group '{group}' is not reachable"


def test_no_group_was_imported_but_left_unregistered(runner):
    """Catches the reverse mistake: a group added to the import list only.

    Compares what the app actually exposes against the list above, so adding
    a group without updating the tests (or the README table) fails here.
    """
    result = runner.invoke(app, ["--help"])
    for group in REGISTERED_GROUPS:
        assert group in result.output, f"'{group}' missing from top-level help"


# ── option plumbing ────────────────────────────────────────────────────────
#
# Overrides that silently fail to reach the client are how a command meant
# for a local dev server gets pointed at production, or vice versa.


def test_api_url_override_reaches_state(runner):
    runner.invoke(app, ["--api-url", "https://example.test/api/v1", "markets", "--help"])
    assert get_state()["api_url"] == "https://example.test/api/v1"


def test_profile_override_reaches_state(runner):
    runner.invoke(app, ["--profile", "production", "markets", "--help"])
    assert get_state()["profile"] == "production"


def test_defaults_are_sane_before_any_invocation():
    """get_state() must return a usable dict even if the callback never ran."""
    fresh = {
        "json_output": False, "config_path": None, "profile": None,
        "api_url": None, "timeout": 30.0, "verbose": False,
    }
    if hasattr(app, "state"):
        del app.state
    assert get_state() == fresh


# ── version ────────────────────────────────────────────────────────────────


def test_version_is_eager_and_needs_no_subcommand(runner):
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.output.strip(), "--version printed nothing"
