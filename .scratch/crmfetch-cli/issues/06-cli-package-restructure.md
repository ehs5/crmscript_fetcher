Status: ready-for-agent
Blocked by: 04

# Low priority: restructure cli.py into a cli/ package

Spec: `.scratch/crmfetch-cli/spec.md`

**Low priority - not urgent.** This is a deferred nice-to-have, not a bug or a blocker. If picked up as the next item in the frontier, double check with Espen first that this is actually what he wants worked on next rather than starting it automatically just because it's unblocked.

**Before writing any code, load the `coding-style` skill and follow it for everything in this ticket.**

**This environment is the developer's real, live desktop — not an isolated sandbox.** Never attempt real display/mouse/keyboard interaction or screen capture.

## Description

`cli.py` currently holds everything: banner/logo, Cyclopts app setup, all tenant commands (list/show/fetch/add/edit/delete), the settings subcommand group (set/init/path), and `main()`. At ~470 lines it's still manageable, but it'll keep growing - the spec's Out of Scope section already names likely future additions (`crmfetch open <id>`, a command to print the SuperOffice-side fetcher script).

Splitting it into a proper package would look something like:

- `cli/app.py` - banner, Cyclopts `App` setup, command ordering/grouping, `main()`
- `cli/tenant_commands.py` - list/show/fetch/add/edit/delete
- `cli/settings_commands.py` - the settings subcommand group

**Why this waited**: `pyproject.toml` currently documents a deliberate choice - "The core + CLI live as flat top-level modules (not a package), matching how this repo has always been laid out. poetry-core can't autodetect that layout, so list exactly the modules crmfetch's import graph needs." Moving to a package changes that: the `[tool.poetry] packages` list, the `[project.scripts]` entry point (`cli:main` → something like `cli.app:main`), and every test's `import cli` all need reworking together. Doing this after ticket 04's packaging work has landed and settled avoids doing that rework twice.

## Acceptance Criteria

- [ ] `cli.py` split into a `cli/` package along the lines described above (exact module boundaries are a judgment call - the point is separating banner/setup/main from the two command groups, not a specific file count)
- [ ] `pyproject.toml`'s `[tool.poetry] packages` and `[project.scripts]` entry point updated to match the new layout
- [ ] All existing tests (`tests/test_cli.py`, `tests/test_cli_settings.py`) updated to import from the new locations; no test behavior changes, only import paths
- [ ] `uv tool install .` still produces a working `crmfetch` command afterward
- [ ] `python -m py_compile` clean across all new files; full test suite passes
- [ ] No change to the GUI (`main.py`, `bridge.py`) - this ticket is CLI-only
- [ ] Code follows the `coding-style` skill

## Comments

Raised by Espen mid-session as a "would this be reasonable" question, not a concrete pain point yet - see conversation for the fuller reasoning trail on why now versus later.
