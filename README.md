# O2 CLI

[![PyPI](https://img.shields.io/pypi/v/o2-cli)](https://pypi.org/project/o2-cli/)
[![Python](https://img.shields.io/pypi/pyversions/o2-cli)](https://pypi.org/project/o2-cli/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

Command-line interface for **[O2](https://oxygen2.xyz)**, a perpetual futures
DEX running in production.

Markets, order entry, positions, margin, deposits and withdrawals — the full
trading surface, from a terminal or from a script.

```bash
pip install o2-cli
```

## Built to be driven by an agent

Most trading CLIs are built for a human at a prompt and grow a `--json` flag
later. This one assumes from the start that the caller might be a program.

Two consequences shape the design:

**`--json` output is machine-only.** Nothing else is allowed onto stdout in
that mode — not a version notice, not a progress line. A single stray print
turns a successful command into a parse error at the other end, so the
property is [pinned by tests](tests/test_cli_contract.py) rather than left to
discipline.

**It installs its own instructions.** `o2 setup` writes a skill file into your
AI coding tool, so the agent knows the command surface, the flag-ordering
rule, and the exit-code convention without you pasting documentation.

```bash
o2 setup                                   # interactive wizard
o2 setup --tool claude-code --scope global
o2 setup --update                          # refresh all installed tools
```

Supported: **Claude Code**, **Cursor**, **Codex**, **Windsurf**, **Cline**, **Trae**

## Quick start

```bash
# Public data — no login required
o2 --json markets list
o2 --json markets orderbook -m 1

# Authenticate
o2 auth test-login

# Trade
o2 --json balance show
o2 --json orders create -m 1 -s long -t market -a 0.001
o2 --json positions list
```

## Rules worth knowing

1. **`--json` goes before the subcommand.** `o2 --json balance show`, never
   `o2 balance show --json`. It's a root-level option, so the trailing form is
   rejected outright — deliberately, because silently returning
   human-formatted text to a caller expecting JSON is the worse failure.
2. Public commands need no login: `markets list`, `fees rates`.
3. Everything else needs `o2 auth test-login` first.
4. Exit codes: `0` success, `1` error, `2` bad arguments.

## Commands

| Group | Commands | Auth |
|---|---|---|
| `auth` | `test-login`, `me`, `session` | — (login) |
| `markets` | `list`, `orderbook`, `candles`, `trades` | No |
| `fees` | `rates`, `estimate` | No |
| `balance` | `show`, `history` | Yes |
| `orders` | `create`, `list`, `cancel`, `cancel-all`, `modify`, `batch` | Yes |
| `positions` | `list`, `market`, `close`, `risk` | Yes |
| `trades` | `list`, `summary` | Yes |
| `deposits` | `address`, `history` | Yes |
| `withdrawals` | `create`, `status`, `cancel`, `list` | Yes |
| `settings` | `get`, `leverage`, `margin-mode` | Yes |
| `notifications` | `list`, `unread`, `read` | Yes |
| `account` | `overview` | Yes |
| `mm` | `status`, `start`, `stop`, `stats`, `orders` | API key |
| `admin` | `gas-status`, `proxy-list`, `api-keys`, `reconcile` | Admin JWT |
| `setup` | wizard, `--tool`, `--update`, `--status` | No |
| `config` | profile management | No |

## Configuration

`~/.o2/config.yaml`:

```yaml
active_profile: default
profiles:
  default:
    api_url: https://api.oxygen2.xyz/api/v1
    timeout: 30
    auth_type: jwt
    token: eyJ...        # written on login
```

Override per invocation:

```bash
o2 --profile staging --json balance show
o2 --api-url http://localhost:8000/api/v1 --json markets list
```

## Development

```bash
git clone https://github.com/dylantlwu/o2-cli.git
cd o2-cli
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

pytest              # 25 tests
ruff check o2_cli/
```

The test suite covers the contract rather than the implementation: stdout
purity in `--json` mode, flag-ordering rejection, that every documented
command group is actually reachable, and that `--api-url` / `--profile`
overrides reach the client. Each test says in its docstring what breaks if
the property stops holding.

## License

MIT
