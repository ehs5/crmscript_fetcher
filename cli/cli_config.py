"""
Manages the CLI's own persistent pointer to the active tenant_settings.json
file - not a copy of the tenant data, just a reference to wherever the real
file already lives.

TenantService's default (no-argument) constructor resolves its path via
get_app_directory(), which locates the file relative to wherever the
currently running code physically lives - a dev checkout, `uv tool install .`,
and the GUI's built .app each get their own disconnected answer. This pointer
is CLI-only config, stored via platformdirs at a location stable regardless
of how the CLI itself was installed, so `crmfetch` commands can consistently
find whichever tenant_settings.json the user pointed them at (typically the
GUI's own file). The GUI never reads or writes this pointer.
"""
import json
from pathlib import Path

import platformdirs


class CliConfig:
    """Reads and writes the CLI's config.json, which stores the active tenant_settings.json path."""

    def __init__(self, config_dir: Path | None = None):
        self.config_dir: Path = config_dir or Path(platformdirs.user_config_dir("crmfetch"))
        self.config_file: Path = self.config_dir / "config.json"

    def get_active_settings_path(self) -> Path | None:
        """Returns the currently active tenant_settings.json path, or None if not configured yet."""
        if not self.config_file.is_file():
            return None

        with open(self.config_file) as f:
            config: dict = json.load(f)

        raw_path: str = config.get("tenant_settings_path", "")
        if not raw_path:
            return None

        return Path(raw_path)

    def set_active_settings_path(self, path: Path) -> None:
        """Stores the given path as the active tenant_settings.json pointer."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

        with open(self.config_file, "w") as f:
            json.dump({"tenant_settings_path": str(path)}, f, indent=4)
