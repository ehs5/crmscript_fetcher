"""
Tenant-facing commands: list/show/fetch/add/edit/delete. Registered onto
cli.app's `app` object by being imported from there - see the bottom of
cli/app.py.
"""
import json
from pathlib import Path
from typing import Annotated

import cyclopts

from cli.app import app, _print_error
from cli.cli_config import CliConfig
from core.fetch_service import FetchService
from core.tenant_service import TenantService

_NO_SETTINGS_MESSAGE = (
    "No active tenant_settings.json is configured. "
    "Run 'crmfetch settings set <path>' to point at an existing file, "
    "or 'crmfetch settings init <path>' to create a fresh one."
)

# Left unset at import time - built lazily by _resolve_tenant_service() from
# the CLI's own settings pointer (cli_config.py) the first time a command
# actually needs it. Never falls back to TenantService()'s bundled-default
# path; that path is the GUI's, and using it here is exactly the bug this
# pointer exists to fix (see ticket 05).
tenant_service: TenantService | None = None
fetch_service = FetchService()


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


@app.command(name="search")
def search_tenants(query: str, *, json_output: Annotated[bool, cyclopts.Parameter(name="--json")] = False) -> int:
    """Searches tenants by name or URL substring, case-insensitive.

    Parameters
    ----------
    query: str
        Substring to match against a tenant's name or URL.
    json_output: bool
        Print the full tenant objects as JSON instead of a human-readable summary.
    """
    service: TenantService | None = _resolve_tenant_service()
    if service is None:
        return 1

    tenants: list[dict] = service.search_tenants(query)

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
