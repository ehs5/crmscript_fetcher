Status: done
Blocked by: 06

# Add a search command

Spec: `.scratch/crmfetch-cli/spec.md`

**Before writing any code, load the `coding-style` skill.**

**This environment is the developer's real, live desktop — not an isolated sandbox.** Never attempt real display/mouse/keyboard interaction or screen capture.

## Description

No search exists in `core` today. The GUI's "Search tenants..." box (`gui/vue/src/App.vue`, `filteredTenants`) is purely client-side - it filters the already-fetched tenant list in JS by name/URL substring, nothing backend-side.

Add `search_tenants(query: str) -> list[dict]` to `TenantService` in `core` - case-insensitive substring match on `tenant_name` and `url`, mirroring the Vue filter's logic exactly. Then add `crmfetch search <query>` calling it, same output shape as `list` (human summary lines, `--json` for the full objects).

## Acceptance Criteria

- [x] `TenantService.search_tenants(query)` added to core, matches the Vue filter's behavior (case-insensitive, name or URL substring)
- [x] `crmfetch search <query>` command added, with `--json` like `list`
- [x] Core tests for `search_tenants`; CLI-seam test confirming the command wires to it
- [x] No change to the GUI - this ticket is core+CLI only
- [x] Code follows the `coding-style` skill
