Status: ready-for-agent
Blocked by: 04

# Low priority: split into core/, cli/, gui/

Spec: `.scratch/crmfetch-cli/spec.md`

**Low priority.** Confirm with Espen before starting even if unblocked.

**Before writing any code, load the `coding-style` skill.**

## Description

Reorganize the flat top-level layout into:

- `core/` - `tenant_service.py`, `fetch_service.py`, `utility.py`, `data_creator.py`, `data_creation/`
- `cli/` - `cli.py` (split into `app.py`, `tenant_commands.py`, `settings_commands.py`), `cli_config.py`
- `gui/` - `main.py`, `bridge.py`, and the whole `vue/` project nested inside (it has no purpose outside being the GUI's frontend)

Delete `tenant_settings.py` (legacy, already marked "to be deleted" in its own docstring).

Update `pyproject.toml`'s `[tool.poetry] packages` and `[project.scripts]` entry point, and all test imports, to match.

## Acceptance Criteria

- [ ] Files reorganized as above; `tenant_settings.py` deleted
- [ ] `pyproject.toml` packaging config and entry point updated
- [ ] Tests updated to new import paths, no behavior changes
- [ ] `uv tool install .` still works; full test suite passes
- [ ] GUI behavior unchanged
