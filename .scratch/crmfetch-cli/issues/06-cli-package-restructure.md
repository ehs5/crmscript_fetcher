Status: done
Blocked by: 04

# Low priority: split into core/, cli/, gui/

Spec: `.scratch/crmfetch-cli/spec.md`

**Low priority.** Confirm with Espen before starting even if unblocked.

**Before writing any code, load the `coding-style` skill.**

## Description

Reorganize the flat top-level layout into:

- `core/` - `tenant_service.py`, `fetch_service.py`, `utility.py`, `data_creator.py`, `data_creation/`
- `cli/` - `cli.py` (split into `app.py`, `tenant_commands.py`, `settings_commands.py`), `cli_config.py`
- `gui/` - `bridge.py` plus the actual GUI-launching code (from ticket 04's `run_gui()`), and the whole `vue/` project nested inside (it has no purpose outside being the GUI's frontend)

Ticket 04 made root `main.py` a dispatcher (`main()` picks GUI vs CLI on `sys.argv`, delegating to `run_gui()` or `cli.main()`) so PyInstaller has one entry point for the dual-mode macOS binary. Don't move that whole file into `gui/` as-is - split it: the dispatcher stays a tiny file at root (still what PyInstaller points at), and `run_gui()`'s actual GUI-launching code moves into `gui/main.py` on its own. Two files, not one doing both jobs.

Delete `tenant_settings.py` (legacy, already marked "to be deleted" in its own docstring).

Update `pyproject.toml`'s `[tool.poetry] packages` and `[project.scripts]` entry point, and all test imports, to match.

## Acceptance Criteria

- [x] Files reorganized as above; `tenant_settings.py` deleted
- [x] Root dispatcher stays a separate, minimal file from `gui/main.py`'s actual GUI-launching code
- [x] macOS dual-mode build (no args -> GUI, args -> CLI) still works after the split
- [x] `pyproject.toml` packaging config and entry point updated
- [x] Tests updated to new import paths, no behavior changes
- [x] `uv tool install .` still works; full test suite passes
- [x] GUI behavior unchanged
