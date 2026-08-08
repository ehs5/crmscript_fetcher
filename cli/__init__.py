# Re-exports main() as the package's own attribute so that both the
# `crmfetch = "cli:main"` console-script entry point and root main.py's
# `import cli; cli.main(...)` dispatch keep working against `cli` the
# package, same as they did against cli.py the flat module before the split.
from cli.app import main

__all__ = ["main"]
