"""
The `crmfetch settings` command group: set/init/path. Registered onto
cli.app's `app` object by being imported from there - see the bottom of
cli/app.py.
"""
import json
import shutil
from pathlib import Path

import cyclopts

from cli.app import app, _print_error
from cli.cli_config import CliConfig
from core.utility import get_app_directory

settings_app = cyclopts.App(
    name="settings",
    help="Manage which tenant_settings.json file this CLI reads and writes.",
)
app.command(settings_app)


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
