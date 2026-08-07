"""
crmfetch: flag-based CLI over the crmscript_fetcher core.

Calls TenantService/FetchService/utility functions directly and in-process -
there is no subprocess relationship with the GUI. See .scratch/crmfetch-cli/spec.md
for the full command surface and the decisions behind it.
"""
import json
import sys
from typing import Annotated

import cyclopts

from fetch_service import FetchService
from tenant_service import TenantService
from utility import get_current_version

app = cyclopts.App(name="crmfetch", version=get_current_version)

tenant_service = TenantService()
fetch_service = FetchService()


def _print_error(message: str) -> None:
    """Prints an error message to stderr."""
    print(message, file=sys.stderr)


def _tenant_summary(tenant: dict) -> str:
    """Formats a tenant as a single human-readable line: id, name, url."""
    return f"{tenant['id']}: {tenant['tenant_name']} ({tenant['url']})"


@app.command(name="list")
def list_tenants(*, json_output: Annotated[bool, cyclopts.Parameter(name="--json")] = False) -> int:
    """Lists all configured tenants.

    Parameters
    ----------
    json_output: bool
        Print the full tenant objects as JSON instead of a human-readable summary.
    """
    tenants: list[dict] = tenant_service.get_all_tenants()

    if json_output:
        print(json.dumps(tenants, indent=4))
        return 0

    for tenant in tenants:
        print(_tenant_summary(tenant))
    return 0


@app.command(name="fetch")
def fetch_tenant(tenant_id: int) -> int:
    """Fetches CRMScripts for one tenant by id.

    Parameters
    ----------
    tenant_id: int
        The numeric id of the tenant to fetch, as shown by `crmfetch list`.
    """
    try:
        tenant: dict = tenant_service.get_tenant_by_id(tenant_id)
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
    """Creates a new tenant with the core fields.

    Fetch options aren't exposed here - new tenants get the same defaults
    `TenantService.add_missing_fetch_options` backfills onto legacy tenants
    (all six options enabled).

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
    new_tenant: dict = {
        "tenant_name": name,
        "url": url,
        "include_id": include_id,
        "key": key,
        "local_directory": local_dir,
    }

    try:
        added: dict = tenant_service.add_tenant(new_tenant)
    except Exception as e:
        _print_error(str(e))
        return 1

    # Backfills default fetch_options onto the tenant we just added, same as
    # today's add_missing_fetch_options quirk for legacy tenants.
    tenant_service.add_missing_fetch_options(tenant_service.get_all_tenants())

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
    """Updates a tenant's core fields, leaving unspecified fields unchanged.

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
    try:
        tenant: dict = tenant_service.get_tenant_by_id(tenant_id)
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
        tenant_service.update_tenant(tenant)
    except ValueError as e:
        _print_error(str(e))
        return 1

    print(f"Updated tenant {tenant_id}.")
    return 0


@app.command(name="delete")
def delete_tenant(tenant_id: int, *, yes: bool = False) -> int:
    """Deletes a tenant by id.

    Refuses without confirmation: pass --yes to actually delete. Without it,
    prints the tenant that would be deleted and exits non-zero, leaving
    tenant_settings.json untouched - there is no interactive [y/N] prompt,
    since that would block on stdin and break agent/CI use.

    Parameters
    ----------
    tenant_id: int
        The numeric id of the tenant to delete.
    yes: bool
        Confirms the deletion. Omitting it is a safe no-op.
    """
    try:
        tenant: dict = tenant_service.get_tenant_by_id(tenant_id)
    except ValueError as e:
        _print_error(str(e))
        return 1

    if not yes:
        print(f"Would delete tenant: {_tenant_summary(tenant)}")
        print("Pass --yes to actually delete it.")
        return 1

    tenant_service.delete_tenant(tenant_id)
    print(f"Deleted tenant {tenant_id}.")
    return 0


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
