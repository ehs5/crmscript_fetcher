Status: ready-for-agent

# Extract UI-agnostic core + fix HTML-embedded messages

Spec: `.scratch/crmfetch-cli/spec.md`

## Description

Reorganize `tenant_service.py`, `fetch_service.py`, `utility.py`, `data_creator.py` into a UI-agnostic core with no Eel/pywebview imports, importable directly and in-process by both a future CLI and the existing GUI. This is the foundation ticket — everything else depends on it.

Also fix `fetch_service.fetch()`'s `error`/`info` strings, which currently contain literal `<br>` HTML intended for Vue's rendering. Core should return plain, newline-separated text; if the GUI still wants HTML, that conversion belongs in the GUI layer, not core.

## Acceptance Criteria

- [ ] `tenant_service.py`, `fetch_service.py`, `utility.py`, `data_creator.py` (or their reorganized equivalents) contain no `import eel` / pywebview imports
- [ ] `bridge.py` still works unmodified against the reorganized core (existing GUI behavior unchanged) — confirmed by running the existing GUI (`python main.py`) and exercising list/fetch/add/edit/delete once each
- [ ] `fetch_service.fetch()`'s `error` and `info` fields no longer contain `<br>` or other HTML markup — plain text with `\n` for line breaks instead
- [ ] Existing Vue GUI still displays fetch errors/info sensibly after the plain-text change (adjust the Vue display layer to convert `\n` → line breaks if needed, so this isn't a visual regression)
- [ ] Unit tests added at the core seam (calling `tenant_service`/`fetch_service` functions directly, mocking the SuperOffice HTTP call per the existing pattern in `fetch_service.py`) covering: fetch success, fetch validation error, fetch HTTP error, tenant CRUD (add/update/delete/get_all)
- [ ] `python -m py_compile` (or equivalent) passes on all touched files
