Status: ready-for-agent
Blocked by: 01, 02

# CLI settings-file pointer: settings set / init / path

Spec: `.scratch/crmfetch-cli/spec.md`

**Before writing any code, load the `coding-style` skill and follow it for everything in this ticket.**

**This environment is the developer's real, live desktop — not an isolated sandbox.** Never attempt real display/mouse/keyboard interaction or screen capture. Verify anything GUI-adjacent via code inspection, protocol/API-level calls, or headless checks only.

## Description

Right now the CLI (ticket 02) has no real way to see a user's actual tenant data. `TenantService` resolves `tenant_settings.json` via `get_app_directory()`, which locates the file relative to wherever the *currently running code* physically lives (`sys._MEIPASS` when frozen, `__file__`'s directory otherwise). Every install method computes a different answer: a dev checkout, `uv tool install .`, and the GUI's built `.app` each get their own disconnected copy. As it stands, `crmfetch show 1` on a `uv`-installed CLI prints the shipped template's "Example tenant" — never a real tenant.

**The GUI is out of scope here and must not change.** It keeps resolving `tenant_settings.json` next to its own binary/bundle exactly as it does today — no code changes to `main.py`, `bridge.py`, `tenant_service.py`'s default constructor behavior, or anything GUI-facing.

Instead, the CLI gets its own small persistent pointer — not a copy of the tenant data, a reference to wherever the real file already lives (typically the GUI's own file, if the user already uses the GUI). Every CLI command reads/writes that literal path directly, so if you point the CLI at the GUI's file, they're genuinely sharing the same file on disk, not two copies that can drift.

New commands (a `settings` subcommand group):

- `crmfetch settings set <path>` — points the CLI at an existing `tenant_settings.json`. Just validates the path exists and looks like a real settings file (valid JSON, is a list); stores the path. Does not copy anything.
- `crmfetch settings init <path>` — one-time convenience: creates a fresh default file at `<path>` (one "Example tenant" entry, matching today's shipped template exactly) and sets it active in the same step. If something unexpected already exists at `<path>`, back it up first (see below) rather than overwriting it silently.
- `crmfetch settings path` — prints the currently active settings file path, or a clear message if none is configured yet.

The pointer itself (which path is active) is small persistent CLI-owned config — stored via `platformdirs` (new dependency) at a stable, install-method-independent location, e.g. `platformdirs.user_config_dir("crmfetch")/config.json`, holding something like `{"tenant_settings_path": "<absolute path>"}`. This is the one piece of state that must survive regardless of how the CLI itself was installed; the actual tenant data can live wherever the user points it.

**Backup-before-overwrite**: `settings init <path>` only ever backs up what's already at `<path>` — it never touches the GUI's file (there's nothing to overwrite there; `init` and `set` operate on the CLI's own pointer, and `init`'s target `<path>` is a location the user is choosing to write a fresh file to). If `<path>` already exists, rename it to `<path-without-extension>.backup.json` before creating the fresh default (if that backup name is also already taken, append `-2`, `-3`, etc. — never overwrite a previous backup either). Print exactly what happened (backed up to where, then created fresh, then set active) — nothing silent.

**Every other command now requires the pointer to be set.** `list`/`fetch`/`add`/`edit`/`delete`/`show` must error clearly (exit code 1, a message naming `settings set`/`settings init`) if no active path is configured yet — no silent bundle-relative fallback, no implicit default. This means `TenantService`'s current eager `tenant_service = TenantService()` module-level instantiation in `cli.py` needs to become lazy: resolve the active path from the pointer only when a command that needs it actually runs, not at import time.

`TenantService` itself needs to accept an explicit path (it currently hardcodes `get_app_directory() / "tenant_settings.json"` with no way to override it) — add that without changing its existing no-argument behavior, since the GUI relies on that default staying exactly as-is.

## Acceptance Criteria

- [ ] `platformdirs` added as a direct dependency in `pyproject.toml` (not relied on transitively)
- [ ] `TenantService` accepts an optional explicit settings-file path; its no-argument behavior (used by the GUI, untouched) still resolves via `get_app_directory()` exactly as before
- [ ] `crmfetch settings set <path>` stores the path as the active pointer after validating it exists and parses as a JSON list; does not modify or copy the file's contents
- [ ] `crmfetch settings init <path>` creates a fresh default file (one "Example tenant" entry matching the shipped template) at `<path>` and sets it active, in one step
- [ ] `crmfetch settings init <path>` backs up a pre-existing file at `<path>` to `<path>.backup.json` (or `-2.json`, `-3.json`, ... if that name is taken) before writing the fresh default, and prints exactly what it did
- [ ] `crmfetch settings path` prints the active path, or a clear "not configured yet" message (not an error) if none is set
- [ ] `list`/`fetch`/`add`/`edit`/`delete`/`show` all exit 1 with a message pointing at `settings set`/`settings init` when no pointer is configured yet — verified for at least one of them
- [ ] Once a pointer is set, all six commands operate on that literal path (verified by pointing at a tmp file, running a command, and confirming the tmp file - not any bundled default - was read/written)
- [ ] No change in behavior for `TenantService()` called with no arguments (the GUI's path) - existing GUI-side tests, if any, and manual reasoning both confirm this
- [ ] Tests use `tmp_path`/monkeypatched config-dir resolution throughout - no test reads or writes the developer's real `~/.config` (or platform equivalent) or real `tenant_settings.json`
- [ ] Code follows the `coding-style` skill

## Comments

Raised directly by Espen mid-session, not covered by the original spec or grilling session - the CLI as built in ticket 02 had no way to see real tenant data at all. See conversation for the fuller reasoning trail (why platformdirs, why no copying, why GUI stays untouched).
