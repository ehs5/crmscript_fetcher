"""
The `crmfetch script` command: prints the CRMScript Fetcher script.
Registered onto cli.app's `app` object by being imported from there - see
the bottom of cli/app.py.
"""
from cli.app import app
from core.utility import get_fetcher_script


@app.command(name="script")
def print_script() -> int:
    """Prints the script you add in the SuperOffice tenant.

    This is the CLI equivalent of the GUI's "Copy Fetcher Script" button.
    Pipe it straight to your OS clipboard tool instead of copying from the
    terminal by hand: crmfetch script | pbcopy on macOS, or
    crmfetch script | Set-Clipboard on Windows.
    """
    print(get_fetcher_script())
    return 0
