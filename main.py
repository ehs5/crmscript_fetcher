import sys

import cli
from gui.main import run_gui


def main() -> None:
    # Dual-mode entry point (macOS ships this as the one binary for both
    # uses): no args -> double-clicked/launched bare, open the GUI same as
    # today. Args present -> dispatch to the Cyclopts CLI instead. cli.main()
    # exits the process itself (via cyclopts) with the CLI's own exit code,
    # so nothing after this call ever runs on that branch.
    if len(sys.argv) > 1:
        cli.main(sys.argv[1:])
        return

    run_gui()


if __name__ == "__main__":
    main()
