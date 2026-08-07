Status: ready-for-agent
Blocked by: 02, 03

# Packaging: macOS dual-mode binary + Windows two-binary split

Spec: `.scratch/crmfetch-cli/spec.md`

## Description

Update the PyInstaller build configuration (`CRMScript Fetcher.spec` and/or the `python -m eel`-style build command in `readme.md`) so that:

- **macOS**: one dual-mode binary/`.app` — invoked with no args launches the pywebview GUI (double-click friendly, matches today's behavior), invoked with args runs the Cyclopts CLI from ticket 02. Requires a single entry point (likely `main.py`) that dispatches on `sys.argv`.
- **Windows**: two separate build targets from the same source — `CRMScript Fetcher.exe` (GUI subsystem, `console=False`, unchanged double-click GUI) and `crmfetch.exe` (console subsystem, `console=True`, for PowerShell/cmd use). This avoids the Windows PE-subsystem issue where a GUI-subsystem `.exe` invoked with CLI args from a terminal has no attached console and silently drops all stdout/stderr.

Update `readme.md`'s build instructions to reflect both new build commands/targets. This is a Windows-only build step and can't be verified on macOS — flag clearly in the report which parts were verified vs. which need a Windows machine to confirm.

## Acceptance Criteria

- [ ] macOS: rebuilding produces one `.app` where running the bundled binary directly with no args opens the GUI, and with args (e.g. `... list`) runs the CLI and prints output to the calling terminal
- [ ] Windows spec/build config updated to produce two distinct executables from one source tree; changes reviewed for correctness even if not run on an actual Windows machine (call this out explicitly in the report)
- [ ] `readme.md` build instructions updated for both platforms, matching the actual commands used
- [ ] `pyproject.toml` version bump convention (see prior `2.1.0` bump in git history) still works unchanged — `get_current_version()` still reads from the same place
- [ ] `uv tool install` path from ticket 02 still works after any `pyproject.toml` packaging changes made in this ticket
