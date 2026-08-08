"""
crmfetch: flag-based CLI over the crmscript_fetcher core.

Calls TenantService/FetchService/utility functions directly and in-process -
there is no subprocess relationship with the GUI. See .scratch/crmfetch-cli/spec.md
for the full command surface and the decisions behind it.

This module owns the cyclopts App itself, the splash/help banner, and the
main() entry point. The actual commands are registered onto `app` by
cli.tenant_commands and cli.settings_commands, imported at the bottom of this
file for their registration side effects.
"""
import sys

import cyclopts

from core.utility import get_current_version

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

# Shown on `crmfetch --help` (and any subcommand's --help)
HELP_TEXT = (
    f"{_LOGO}\n\n"
    f"{_VERSION_LINE}\n\n"
    "  First run? Point crmfetch at a tenant_settings.json file before anything else:\n"
    "  - If the CRMScript Fetcher GUI is already installed, find its\n"
    "    tenant_settings.json and run: crmfetch settings set <path>\n"
    "  - Otherwise, create a fresh one: crmfetch settings init <path>\n\n"
    "  Run a command with --help for its details, e.g. 'crmfetch add --help'."
)


def _print_splash() -> int:
    # Runs when `crmfetch` is invoked with no arguments at all. Reuses the
    # exact same Commands+Options panel render --help shows (via help_print),
    # just with the short banner (no first-run guidance) - that lives in
    # --help specifically. No docstring here on purpose: cyclopts would
    # otherwise render it as the app's own description text.
    app.help_prologue = (
        f"{_LOGO}\n\n{_VERSION_LINE}\n\n"
        "  Run a command with --help for its details, e.g. 'crmfetch add --help'."
    )
    # Version's already right there in the banner above - no need to also
    # list --version as an option on the splash specifically.
    app["--version"].show = False
    app.help_print([])
    return 0


app = cyclopts.App(
    name="crmfetch",
    version=get_current_version,
    version_flags=["--version", "-v"],
    help_prologue=HELP_TEXT,
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
# The default text is generic ("Display this message and exit.") - this is
# the one thing a first-time caller (human or agent) needs pointed at.
app["--help"].help = "Start here - shows setup instructions and every command."


def _print_error(message: str) -> None:
    """Prints an error message to stderr."""
    print(message, file=sys.stderr)


# Imported for their registration side effects (each decorates commands onto
# `app` above) - must happen after `app`/`_print_error` are defined, since
# both modules import them back from here.
from cli import tenant_commands, settings_commands  # noqa: E402,F401

# Cyclopts sorts commands alphabetically by default; this pins an explicit
# order instead (show sits with the other tenant-lookup commands, right
# after fetch, rather than alphabetically after list).
for _sort_key, _command_name in enumerate(["add", "delete", "edit", "fetch", "show", "list", "search", "settings"]):
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
