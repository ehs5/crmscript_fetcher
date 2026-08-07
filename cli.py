"""
crmfetch: flag-based CLI over the crmscript_fetcher core.

Calls TenantService/FetchService/utility functions directly and in-process -
there is no subprocess relationship with the GUI. See .scratch/crmfetch-cli/spec.md
for the full command surface and the decisions behind it.
"""
import json
import shutil
import sys
from pathlib import Path
from typing import Annotated

import cyclopts

from cli_config import CliConfig
from fetch_service import FetchService
from tenant_service import TenantService
from utility import get_app_directory, get_current_version

_NO_SETTINGS_MESSAGE = (
    "No active tenant_settings.json is configured. "
    "Run 'crmfetch settings set <path>' to point at an existing file, "
    "or 'crmfetch settings init <path>' to create a fresh one."
)

_LOGO = """
                       __     _       _
                      / _|   | |     | |
   ___ _ __ _ __ ___ | |_ ___| |_ ___| |__
  / __| '__| '_ ` _ \\|  _/ _ \\ __/ __| '_ \\
 | (__| |  | | | | | | ||  __/ || (__| | | |
  \\___|_|  |_| |_| |_|_| \\___|\\__\\___|_| |_|
""".strip("\n")

# get_current_version() is called once here, at CLI startup - each `crmfetch`
# invocation is a fresh process, so this always reflects the installed
# pyproject.toml, same as --version does.
_VERSION_LINE = f"  v{get_current_version()} - https://github.com/ehs5/crmscript_fetcher"

# Shown on `crmfetch --help` (and any subcommand's --help) - the fuller
# first-run guidance belongs here, not on the bare-invocation splash below,
# so that just running `crmfetch` with no arguments stays short.
BANNER = (
    f"{_LOGO}\n\n"
    f"{_VERSION_LINE}\n\n"
    "First run? Point crmfetch at a tenant_settings.json file before anything else:\n"
    "  - If the CRMScript Fetcher GUI is already installed, find its\n"
    "    tenant_settings.json and run: crmfetch settings set <path>\n"
    "  - Otherwise, create a fresh one: crmfetch settings init <path>\n\n"
    "Run a command with --help for its details, e.g. 'crmfetch add --help'."
)


def _print_splash() -> int:
    # Runs when `crmfetch` is invoked with no arguments at all. Reuses the
    # exact same Commands+Options panel render --help shows (via help_print),
    # just with the short banner (no first-run guidance) - that lives in
    # --help specifically. The epilogue below is the one thing every
    # first-time caller (human or agent) needs pointed out explicitly: where
    # to go next. No docstring here on purpose: cyclopts would otherwise
    # render it as the app's own description text.
    app.help_prologue = f"{_LOGO}\n\n{_VERSION_LINE}"
    app.help_epilogue = "Start here: run 'crmfetch --help'."
    # Version's already right there in the banner above - no need to also
    # list --version as an option on the splash specifically.
    app["--version"].show = False
    app.help_print([])
    return 0


app = cyclopts.App(
    name="crmfetch",
    version=get_current_version,
    version_flags=["--version", "-v"],
    help_prologue=BANNER,
    # Without this, cyclopts renders help_prologue as Markdown, which
    # collapses the banner's line breaks into one line.
    help_format="plaintext",
    # The Commands panel below already shows everything there is to run;
    # a top-level "Usage: crmfetch COMMAND" line adds nothing on top of it.
    # Subcommands (e.g. `crmfetch fetch --help`) keep their own usage line,
    # since those actually show argument syntax.
    usage="",
    # Without this, bare `crmfetch` (no arguments) falls back to the same
    # full help page as `crmfetch --help` - default_command overrides that
    # specific case only; --help/-h still trigger the real help page.
    default_command=_print_splash,
)

# --help/--version are cyclopts' own auto-registered commands, with no group
# assigned by default - which otherwise dumps them into the same "Commands"
# panel as add/delete/edit/fetch/list/show, blurring flags with commands.
_options_group = cyclopts.Group("Options")
app["--help"].group = _options_group
app["--version"].group = _options_group

# Left unset at import time - built lazily by _resolve_tenant_service() from
# the CLI's own settings pointer (cli_config.py) the first time a command
# actually needs it. Never falls back to TenantService()'s bundled-default
# path; that path is the GUI's, and using it here is exactly the bug this
# pointer exists to fix (see ticket 05).
tenant_service: TenantService | None = None
fetch_service = FetchService()


def _print_error(message: str) -> None:
    """Prints an error message to stderr."""
    print(message, file=sys.stderr)


def _tenant_summary(tenant: dict) -> str:
    """Formats a tenant as a single human-readable line: id, name, url."""
    return f"{tenant['id']}: {tenant['tenant_name']} ({tenant['url']})"


def _resolve_tenant_service() -> TenantService | None:
    """
    Returns the module-level TenantService, resolving it from the CLI's
    active settings pointer the first time a command needs one. Returns None
    (after printing an error naming settings set/init) if no pointer is
    configured yet - callers must check for None and exit 1 rather than
    falling back to any bundled default.
    """
    global tenant_service
    if tenant_service is not None:
        return tenant_service

    active_path: Path | None = CliConfig().get_active_settings_path()
    if active_path is None:
        _print_error(_NO_SETTINGS_MESSAGE)
        return None

    tenant_service = TenantService(active_path)
    return tenant_service


def _next_backup_path(path: Path) -> Path:
    """
    Finds a not-yet-taken backup filename for path: <path-without-extension>.backup.json,
    then .backup-2.json, .backup-3.json, ... - never overwrites a previous backup.
    """
    stem_path: Path = path.with_suffix("")
    candidate: Path = stem_path.with_name(f"{stem_path.name}.backup.json")

    suffix = 2
    while candidate.exists():
        candidate = stem_path.with_name(f"{stem_path.name}.backup-{suffix}.json")
        suffix += 1

    return candidate


@app.command(name="list")
def list_tenants(*, json_output: Annotated[bool, cyclopts.Parameter(name="--json")] = False) -> int:
    """Lists all configured tenants.

    Parameters
    ----------
    json_output: bool
        Print the full tenant objects as JSON instead of a human-readable summary.
    """
    service: TenantService | None = _resolve_tenant_service()
    if service is None:
        return 1

    tenants: list[dict] = service.get_all_tenants()

    if json_output:
        print(json.dumps(tenants, indent=4))
        return 0

    for tenant in tenants:
        print(_tenant_summary(tenant))
    return 0


@app.command(name="show")
def show_tenant(tenant_id: int) -> int:
    """Prints the full JSON for one tenant.

    Parameters
    ----------
    tenant_id: int
        The tenant's numeric ID, e.g. crmfetch show 3. Run crmfetch list
        to see available IDs.
    """
    service: TenantService | None = _resolve_tenant_service()
    if service is None:
        return 1

    try:
        tenant: dict = service.get_tenant_by_id(tenant_id)
    except ValueError as e:
        _print_error(str(e))
        return 1

    print(json.dumps(tenant, indent=4))
    return 0


@app.command(name="fetch")
def fetch_tenant(tenant_id: int) -> int:
    """Fetches from the given tenant ID into its specified directory.

    Parameters
    ----------
    tenant_id: int
        The tenant's numeric ID, e.g. crmfetch fetch 3. Run crmfetch list
        to see available IDs.
    """
    service: TenantService | None = _resolve_tenant_service()
    if service is None:
        return 1

    try:
        tenant: dict = service.get_tenant_by_id(tenant_id)
    except ValueError as e:
        _print_error(str(e))
        return 1

    result: dict = fetch_service.fetch(tenant)

    if not result["success"]:
        _print_error(result["error"])
        return 1

    if result["info"]:
        print(result["info"])

    print(f"Fetched tenant {tenant_id} successfully.")
    return 0


@app.command(name="add")
def add_tenant(
    *,
    name: str,
    url: str,
    include_id: str,
    key: str,
    local_dir: Annotated[str, cyclopts.Parameter(name="--local-dir")],
) -> int:
    """Creates a new tenant.

    Fetch options aren't set here - the new tenant starts with all of them
    enabled. Edit fetch options via the GUI, or directly in the settings
    file, if you need different ones.

    Parameters
    ----------
    name: str
        Tenant display name.
    url: str
        SuperOffice service URL.
    include_id: str
        SuperOffice script include id.
    key: str
        SuperOffice script key.
    local_dir: str
        Local directory CRMScripts are fetched into.
    """
    service: TenantService | None = _resolve_tenant_service()
    if service is None:
        return 1

    new_tenant: dict = {
        "tenant_name": name,
        "url": url,
        "include_id": include_id,
        "key": key,
        "local_directory": local_dir,
    }

    try:
        added: dict = service.add_tenant(new_tenant)
    except Exception as e:
        _print_error(str(e))
        return 1

    # Backfills default fetch_options onto the tenant we just added, same as
    # today's add_missing_fetch_options quirk for legacy tenants.
    service.add_missing_fetch_options(service.get_all_tenants())

    print(f"Added tenant {added['id']}: {added['tenant_name']}")
    return 0


@app.command(name="edit")
def edit_tenant(
    tenant_id: int,
    *,
    name: str | None = None,
    url: str | None = None,
    include_id: str | None = None,
    key: str | None = None,
    local_dir: Annotated[str | None, cyclopts.Parameter(name="--local-dir")] = None,
) -> int:
    """Updates a tenant.

    Leaves unspecified fields unchanged.

    Parameters
    ----------
    tenant_id: int
        The numeric id of the tenant to edit.
    name: str | None
        New tenant display name.
    url: str | None
        New SuperOffice service URL.
    include_id: str | None
        New SuperOffice script include id.
    key: str | None
        New SuperOffice script key.
    local_dir: str | None
        New local directory CRMScripts are fetched into.
    """
    service: TenantService | None = _resolve_tenant_service()
    if service is None:
        return 1

    try:
        tenant: dict = service.get_tenant_by_id(tenant_id)
    except ValueError as e:
        _print_error(str(e))
        return 1

    if name is not None:
        tenant["tenant_name"] = name
    if url is not None:
        tenant["url"] = url
    if include_id is not None:
        tenant["include_id"] = include_id
    if key is not None:
        tenant["key"] = key
    if local_dir is not None:
        tenant["local_directory"] = local_dir

    try:
        service.update_tenant(tenant)
    except ValueError as e:
        _print_error(str(e))
        return 1

    print(f"Updated tenant {tenant_id}.")
    return 0


@app.command(name="delete")
def delete_tenant(tenant_id: int, *, yes: bool = False) -> int:
    """Deletes a tenant by id.

    Refuses without confirmation: pass --yes to actually delete. Without it,
    prints the tenant that would be deleted and exits without changing
    anything - a safe way to double-check before you commit to it.

    Parameters
    ----------
    tenant_id: int
        The numeric id of the tenant to delete.
    yes: bool
        Confirms the deletion. Omitting it is a safe no-op.
    """
    service: TenantService | None = _resolve_tenant_service()
    if service is None:
        return 1

    try:
        tenant: dict = service.get_tenant_by_id(tenant_id)
    except ValueError as e:
        _print_error(str(e))
        return 1

    if not yes:
        print(f"Would delete tenant: {_tenant_summary(tenant)}")
        print("Pass --yes to actually delete it.")
        return 1

    service.delete_tenant(tenant_id)
    print(f"Deleted tenant {tenant_id}.")
    return 0


settings_app = cyclopts.App(
    name="settings",
    help="Manage which tenant_settings.json file this CLI reads and writes.",
)
app.command(settings_app)


@settings_app.command(name="set")
def settings_set(path: str) -> int:
    """Points the CLI at an existing tenant_settings.json file.

    Validates that the path exists and parses as a JSON list, then stores it
    as the active pointer. Does not copy or modify the file's contents - the
    CLI reads/writes that literal path directly from now on.

    Parameters
    ----------
    path: str
        Path to an existing tenant_settings.json file.
    """
    settings_path: Path = Path(path)

    if not settings_path.is_file():
        _print_error(f"No file found at {settings_path}.")
        return 1

    try:
        with open(settings_path) as f:
            parsed = json.load(f)
    except json.JSONDecodeError as e:
        _print_error(f"{settings_path} is not valid JSON: {e}")
        return 1

    if not isinstance(parsed, list):
        _print_error(f"{settings_path} doesn't look like a tenant_settings.json file - expected a JSON list.")
        return 1

    resolved_path: Path = settings_path.resolve()
    CliConfig().set_active_settings_path(resolved_path)
    print(f"Active settings file set to {resolved_path}.")
    return 0


@settings_app.command(name="init")
def settings_init(path: str) -> int:
    """Creates a fresh default tenant_settings.json at path and sets it active.

    If something already exists at path, it's backed up first (renamed to
    <path-without-extension>.backup.json, or .backup-2.json etc. if that name
    is taken) rather than overwritten silently.

    Parameters
    ----------
    path: str
        Where to create the fresh default settings file.
    """
    settings_path: Path = Path(path).resolve()

    if settings_path.exists():
        backup_path: Path = _next_backup_path(settings_path)
        settings_path.rename(backup_path)
        print(f"Backed up existing file to {backup_path}.")

    # The shipped tenant_settings.json template *is* the default - copying
    # it directly means there's only one place that shape is ever defined,
    # instead of a second copy here that could drift out of sync with it.
    template_path: Path = get_app_directory() / "tenant_settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(template_path, settings_path)
    print(f"Created fresh default settings file at {settings_path}.")

    CliConfig().set_active_settings_path(settings_path)
    print(f"Active settings file set to {settings_path}.")
    return 0


@settings_app.command(name="path")
def settings_path_command() -> int:
    """Prints the currently active tenant_settings.json path.

    Prints a clear "not configured yet" message (not an error) if no pointer
    has been set via settings set/init yet.
    """
    active_path: Path | None = CliConfig().get_active_settings_path()

    if active_path is None:
        print("No active settings file configured yet. Run 'crmfetch settings set <path>' or 'crmfetch settings init <path>' first.")
        return 0

    print(active_path)
    return 0


# Cyclopts sorts commands alphabetically by default; this pins an explicit
# order instead (show sits with the other tenant-lookup commands, right
# after fetch, rather than alphabetically after list).
for _sort_key, _command_name in enumerate(["add", "delete", "edit", "fetch", "show", "list", "settings"]):
    app[_command_name].sort_key = _sort_key
    # help_prologue would otherwise be inherited from app onto every
    # subcommand's own --help too - fine for `crmfetch -h` itself, but the
    # banner doesn't need repeating on every single subcommand's help page.
    # Setting it here on `settings` also covers its own set/init/path
    # children, since they inherit from their nearest ancestor with an
    # explicit override.
    app[_command_name].help_prologue = ""


def main(argv: list[str] | None = None) -> None:
    """Entry point for the `crmfetch` console script.

    Cyclopts' own parse-error handling exits with code 1 in the installed
    version, which doesn't match this CLI's exit code contract (0 success,
    1 runtime/logic failure, 2 usage/argument error). Running with
    exit_on_error=False turns parse errors into a CycloptsError we catch
    here and remap to exit code 2 ourselves.
    """
    try:
        app(argv, exit_on_error=False)
    except cyclopts.CycloptsError:
        sys.exit(2)


if __name__ == "__main__":
    main()
