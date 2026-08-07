Status: ready-for-agent

# crmfetch CLI + pywebview GUI rework

## Problem Statement

crmscript_fetcher only has a GUI (Eel + Vue) — every fetch requires opening the app and clicking through it by hand. There's no way to fetch a tenant from a terminal, a script, CI, or an AI coding agent. On top of that, Eel (the library the GUI is built on) is discontinued, which is a long-term maintenance risk regardless of the CLI question.

## Solution

Extract the existing tenant/fetch logic into a shared, UI-agnostic core that both a new flag-based CLI ("crmfetch") and the existing Vue GUI sit on top of. Replace Eel with pywebview (actively maintained) for the GUI, keeping the Vue frontend itself largely unchanged. Ship both through the existing PyInstaller/GitHub Releases channel, and make the CLI additionally installable on its own via `uv tool install` for developers who want it without the GUI.

## User Stories

1. As a developer, I want to fetch a single tenant by id from a terminal, so that I don't have to open the GUI for a routine fetch.
2. As a developer, I want to list all configured tenants from a terminal, so that I can look up a tenant's id without opening the GUI.
3. As a developer, I want `crmfetch list --json`, so that I can pipe tenant data into another script or tool.
4. As an AI coding agent, I want `crmfetch fetch <id>` to behave predictably (clear exit codes, no interactive prompts blocking on stdin), so that I can drive it without a human present.
5. As a developer, I want `crmfetch add` to create a new tenant with the core fields (name, url, include-id, key, local directory) via flags, so that I can set up a new tenant without touching the GUI.
6. As a developer, I want `crmfetch edit <id>` to update a tenant's core fields via flags, so that I can fix a typo'd URL or key without opening the GUI.
7. As a developer, I want `crmfetch delete <id>` to require an explicit `--yes` flag, so that I can't accidentally delete a tenant with a typo'd id and no way to undo it.
8. As a developer, I want `crmfetch delete <id>` without `--yes` to print exactly what it would delete before refusing, so that I get a chance to double check before confirming.
9. As a developer, I want `crmfetch --version`, so that I can confirm which build I'm running when reporting a bug.
10. As a developer on macOS, I want the same single app I download today to still just double-click and open as a GUI, so that the CLI addition doesn't change my existing workflow.
11. As a developer on Windows, I want a working `crmfetch` command from PowerShell/cmd that actually prints output, so that the CLI isn't silently broken by the GUI-subsystem/console-subsystem split.
12. As a developer on Windows, I want double-clicking the app to still open the GUI with no visible console flash, so that the CLI fix doesn't regress the existing GUI experience.
13. As a developer comfortable with dev tooling, I want to `uv tool install` crmfetch straight from the repo, so that I get a `crmfetch` command on PATH without downloading a GUI app bundle.
14. As a developer who's never touched Python, I want to keep using the app exactly like today (download, run, GUI) with zero awareness that a CLI or Python packaging exists, so that this rework doesn't force any new tooling on me.
15. As a maintainer, I want the tenant/fetch core logic to have no Eel or pywebview imports in it, so that it stays testable and reusable regardless of which UI framework is on top.
16. As a maintainer, I want fetch/tenant core logic to return plain, framework-neutral data (no embedded HTML) from now on, so that both the CLI and any future consumer can use it without stripping presentation markup out of error messages.
17. As a maintainer, I want the CLI and GUI to call the same core functions in-process, so that there's exactly one implementation of tenant/fetch logic to maintain, not two.
18. As a developer, I want `add`/`edit` to leave the 6 fetch-option booleans alone (editable only via the GUI or directly in `tenant_settings.json`), so that the CLI's flag surface for those commands stays small and memorable.
19. As a developer, I want tenant selection in the CLI to be by numeric id only for now, so that the CLI's first version doesn't have to solve fuzzy/ambiguous name matching.
20. As a developer, I want standard Unix exit codes (0 success, 1 failure, 2 usage error) from crmfetch, so that I can use it reliably in shell scripts and CI conditionals.

## Implementation Decisions

- Reorganize `tenant_service.py`, `fetch_service.py`, `utility.py`, `data_creator.py` into a UI-agnostic core that both the CLI and the GUI import directly and in-process. No subprocess relationship between CLI and GUI — they are two thin front ends over one shared implementation.
- `fetch_service.fetch()`'s `error`/`info` strings currently contain literal `<br>` tags intended for Vue's HTML rendering. This needs to change to plain, newline-separated (or structured) text at the core level; if the Vue GUI still wants HTML formatting, that conversion happens in the GUI layer, not in core.
- CLI framework: Cyclopts (not Typer) — native `Union`/`Literal` support, docstring-driven help, and it avoids Typer's proxy-default-value pattern, which matters here because core functions need to stay directly callable from the GUI layer too, not just reachable through CLI-decorated wrappers.
- CLI command surface (flags only, no interactive/wizard mode):
  - `crmfetch list [--json]`
  - `crmfetch fetch <id>`
  - `crmfetch add --name <name> --url <url> --include-id <id> --key <key> --local-dir <path>`
  - `crmfetch edit <id> [--name] [--url] [--include-id] [--key] [--local-dir]`
  - `crmfetch delete <id> --yes` (refuses and prints what it would delete if `--yes` is omitted; no interactive `[y/N]` prompt anywhere — would block on stdin and break agent/CI use)
  - `crmfetch --version`
- Explicitly no `crmfetch fetch --all` and no bare `crmfetch fetch` with an implicit "fetch everything" meaning — always require an explicit id.
- Tenant selection is by numeric `id` only (matches the existing `tenant_settings.json` schema field) — no name/slug matching in this version.
- `add`/`edit` only expose the five core fields (`tenant_name`, `url`, `include_id`, `key`, `local_directory`). The `fetch_options` object (6 booleans) is not exposed as CLI flags on these commands.
- `list` and `fetch` support `--json` for machine-readable output. Add/edit/delete can still emit their own JSON confirmation payload if convenient during implementation, but it's not a hard requirement of this spec.
- Exit codes: `0` success, `1` runtime/logic failure (tenant not found, validation error, SuperOffice fetch failure), `2` usage/argument error (Cyclopts' default behavior for malformed flags).
- GUI: replace Eel with pywebview. The Vue frontend stays largely as-is; only the JS-Python bridge layer changes shape — `useEel.ts` (wrapping the global `eel` object) becomes an equivalent composable wrapping `window.pywebview.api`, and `bridge.py`'s `eel.expose(...)` registrations become pywebview's exposed-API-object pattern. Existing exposed operations to carry over: `get_all_tenants`, `add_tenant`, `update_tenant`, `delete_tenant`, `fetch`, `get_fetcher_script`, `ask_directory_path`, `open_directory`, `get_current_version`.
- Distribution:
  - **macOS**: one dual-mode binary/`.app` — invoked with no args launches the pywebview GUI (double-click friendly, matches today), invoked with args runs the Cyclopts CLI. Works because macOS executables have no GUI/console subsystem split.
  - **Windows**: two separate PyInstaller build targets from the same source tree — `CRMScript Fetcher.exe` (GUI subsystem, `console=False`, unchanged double-click GUI experience) and `crmfetch.exe` (console subsystem, `console=True`, for PowerShell/cmd use). This sidesteps the Windows PE-level issue where a GUI-subsystem `.exe` invoked with CLI args from a terminal has no attached console and silently drops all stdout/stderr — the same constraint Electron/Tauri apps hit (why VS Code ships a separate `code.cmd` shim) and the same reason Windows Python installs ship both `python.exe` and `pythonw.exe`.
  - Same GitHub Releases channel as today (the project already tags `v1.0.0`–`v2.1.0` and attaches zipped platform builds).
  - Independently, `uv tool install git+https://github.com/ehs5/crmscript_fetcher.git` installs `crmfetch` on PATH straight from source for developers who want the CLI without downloading a GUI build — this requires a `[project.scripts]` entry point in `pyproject.toml` pointing at the CLI's Cyclopts app.
- `tenant_settings.json` read/write behavior (including the existing `add_missing_fetch_options` backfill-on-load quirk in `tenant_service.py`) must behave identically whether driven by the CLI or the GUI, since both go through the same core `TenantService`.

## Testing Decisions

- Single highest seam: test through the core package's functions directly (`tenant_service`, `fetch_service`, `utility`) — not through a CLI subprocess and not through the GUI/pywebview bridge. `bridge.py` today is already a thin pass-through over these exact functions, so this is the existing natural seam, not a new one.
- `fetch_service.fetch()` already returns a plain result dict and is testable via HTTP mocking with no framework coupling — that's the prior art/pattern new core tests should follow.
- A small number of CLI-level tests should invoke the Cyclopts app object directly (in-process, not via subprocess) to confirm each command's flags wire onto the correct core calls with the correct arguments — these test the CLI seam only; business-logic correctness stays covered at the core level to avoid duplicating assertions across layers.
- No automated test coverage planned for the pywebview/GUI bridge, matching the current project's convention (there's no existing Eel-bridge test suite either). Manual smoke-testing (launch the app, click through it) remains the verification method there.
- PyInstaller packaging/build output (both the macOS dual-mode binary and the Windows two-binary split) is out of scope for automated testing — verify manually per release, as has been done throughout this project's history.

## Out of Scope

- Wizard/interactive CLI mode.
- `crmfetch fetch --all` or any implicit "fetch everything" behavior.
- Tenant name/slug-based selection (id-only for this version).
- Fetch-option (6 booleans) flags on `add`/`edit`.
- `crmfetch open <id>` (open a tenant's local folder from the CLI) — not requested; straightforward to add later since `open_directory` already exists in core.
- A CLI command to print/install the SuperOffice-side fetcher script (`get_fetcher_script`) — stays GUI-only for now.
- Any "install CLI command onto PATH" action from within the GUI (the VS Code/Docker-Desktop-style pattern) — explicitly declined in favor of two independent install paths (download the GUI, or `uv tool install` the CLI).
- Live/incremental fetch progress reporting — doesn't exist today and isn't part of this rework.
- Publishing the package to public PyPI (internal `uv tool install git+https://...` only).
- Code-signing/notarization of built binaries — pre-existing gap, unrelated to this work.

## Further Notes

- This work originated from a broader conversation about modernizing crmscript_fetcher now that Eel is discontinued and CLI-first tooling has become more valuable in an agentic-coding context — not from a bug report.
- The Windows two-binary decision was specifically surfaced because cross-platform support (macOS + Windows/PowerShell) was raised as a hard requirement mid-discussion; it is a correctness fix, not a nice-to-have.
- `tenant_settings.json` is not git-tracked at runtime — it lives inside the installed app bundle (e.g. `~/Applications/CRMScript Fetcher.app/Contents/Frameworks/tenant_settings.json` on macOS). The repo's own `tenant_settings.json` is only the shipped template/example.
- Version reporting (`get_current_version`) reads `pyproject.toml`'s `[project] version` — this is the single source of truth and should stay that way for the CLI's `--version` too.
