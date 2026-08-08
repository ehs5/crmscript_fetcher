# Re-exports main() as the package's own attribute so the
# `crmfetch = "cli:main"` console-script entry point keeps working against
# `cli` the package, same as it did against cli.py the flat module before
# the split.
from cli.app import main

__all__ = ["main"]
