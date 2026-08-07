Status: ready-for-agent
Blocked by: 01

# Replace Eel with pywebview in the GUI

Spec: `.scratch/crmfetch-cli/spec.md`

## Description

Eel is discontinued. Replace it with pywebview, calling the core extracted in ticket 01 directly and in-process. The Vue frontend itself (`vue/src/`) should stay largely as-is — only the JS↔Python bridge layer changes shape.

Carry over all existing exposed operations: `get_all_tenants`, `add_tenant`, `update_tenant`, `delete_tenant`, `fetch`, `get_fetcher_script`, `ask_directory_path`, `open_directory`, `get_current_version`.

Concretely:

- `bridge.py`'s `eel.expose(...)` registrations become pywebview's exposed-API-object pattern (a Python class instance passed to `webview.create_window(..., js_api=...)`)
- `vue/src/composables/useEel.ts` (wrapping the global `eel` object) becomes an equivalent composable wrapping `window.pywebview.api` — same method names/shapes so call sites in `App.vue` need minimal changes
- `main.py` swaps `eel.init`/`eel.start` for `webview.create_window`/`webview.start`

## Acceptance Criteria

- [ ] All 9 operations listed above work identically from the Vue GUI (list tenants, add, edit, delete, fetch, get fetcher script, pick a directory, open a directory, show version)
- [ ] No `import eel` remains anywhere in the codebase
- [ ] `python main.py` launches a pywebview window (not a browser tab) displaying the existing Vue UI
- [ ] Fetch error/info display still reads correctly in the GUI after ticket 01's HTML→plain-text change (verify visually, not just that it doesn't crash)
- [ ] Manual smoke test performed and reported: launch the app, exercise list/add/edit/delete/fetch/get-directory/open-directory/version once each (per the spec's Testing Decisions, no automated GUI test coverage is expected — this is deliberately a manual pass)
