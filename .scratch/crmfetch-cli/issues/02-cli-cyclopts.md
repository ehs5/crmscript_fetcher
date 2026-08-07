Status: ready-for-agent
Blocked by: 01

# Build the crmfetch CLI on Cyclopts

Spec: `.scratch/crmfetch-cli/spec.md`

**Before writing any code, load the `coding-style` skill and follow it for everything in this ticket.**

**This environment is the developer's real, live desktop — not an isolated sandbox.** Never attempt real display/mouse/keyboard interaction or screen capture. Verify anything GUI-adjacent via code inspection, protocol/API-level calls, or headless checks only. Any manual click-through step is always a human follow-up — leave its acceptance criterion honestly unchecked rather than attempting it yourself (see ticket 01's Comments for what happened when this wasn't followed).

## Description

Build a flag-based CLI ("crmfetch") using Cyclopts, calling the core extracted in ticket 01 directly and in-process (no subprocess relationship). No wizard/interactive mode. No `fetch --all` and no implicit "fetch everything" behavior — `fetch` always requires an explicit id.

Commands:

- `crmfetch list [--json]` — list all tenants (id, tenant_name, url at minimum in human mode; full tenant objects in `--json` mode)
- `crmfetch fetch <id>` — fetch one tenant by numeric id
- `crmfetch add --name <name> --url <url> --include-id <id> --key <key> --local-dir <path>` — create a tenant with the 5 core fields only (no fetch-option flags; new tenants get default fetch_options same as today's `add_missing_fetch_options` defaults)
- `crmfetch edit <id> [--name] [--url] [--include-id] [--key] [--local-dir]` — update a tenant's core fields, leaving unspecified fields unchanged
- `crmfetch delete <id> --yes` — delete a tenant; without `--yes`, refuse and print exactly what would be deleted (no interactive `[y/N]` prompt anywhere)
- `crmfetch --version` — print the version from `pyproject.toml` (reuse `get_current_version`)

Exit codes: `0` success, `1` runtime/logic failure (tenant not found, validation error, fetch failure), `2` usage/argument error (Cyclopts default).

Add a `[project.scripts]` entry point in `pyproject.toml` pointing at the CLI's Cyclopts app, so `uv tool install git+https://github.com/ehs5/crmscript_fetcher.git` produces a working `crmfetch` command on PATH.

## Acceptance Criteria

- [x] All six commands above implemented and calling core functions from ticket 01 directly (no duplicated business logic)
- [x] `crmfetch fetch` with no id, and `crmfetch fetch --all`, both error as usage errors (exit code 2) rather than doing anything — confirms the "no implicit fetch-all" decision is enforced, not just undocumented
- [x] `crmfetch delete <id>` without `--yes` prints the tenant it would delete and exits non-zero without modifying `tenant_settings.json`
- [x] `crmfetch delete <id> --yes` actually deletes and exits 0
- [x] `crmfetch list --json` output is valid JSON parseable by `json.loads`, containing the full tenant list
- [x] `crmfetch --version` output matches `pyproject.toml`'s `[project] version`
- [x] Exit codes verified for at least one success case, one runtime-failure case (e.g. `fetch` on a nonexistent id), and one usage-error case (e.g. missing required flag on `add`)
- [x] `[project.scripts]` entry added; `uv tool install .` (or equivalent local install) from the repo root produces a working `crmfetch` command
- [x] Tests added invoking the Cyclopts app object directly (in-process, not via subprocess) confirming each command's flags map onto the correct core call with the correct arguments
- [x] Code follows the `coding-style` skill

## Comments

- code-review confirmed this ticket is clean (2026-08-07). Status left as-is; closing is a human decision.
