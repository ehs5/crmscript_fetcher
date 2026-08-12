"""
Unit tests for cli_config.CliConfig.

These test the pointer-storage seam directly against a tmp_path config
directory - never the developer's real platformdirs.user_config_dir()
location, per the ticket's testing requirement.
"""
import json
from pathlib import Path

from cli.cli_config import CliConfig


def test_get_active_settings_path_returns_none_when_config_file_missing(tmp_path: Path) -> None:
    config = CliConfig(config_dir=tmp_path / "does-not-exist-yet")

    assert config.get_active_settings_path() is None


def test_set_then_get_active_settings_path_round_trips(tmp_path: Path) -> None:
    config = CliConfig(config_dir=tmp_path / "config")
    pointed_at: Path = tmp_path / "somewhere" / "tenant_settings.json"

    config.set_active_settings_path(pointed_at)

    assert config.get_active_settings_path() == pointed_at


def test_set_active_settings_path_creates_config_dir_if_missing(tmp_path: Path) -> None:
    config_dir: Path = tmp_path / "config" / "nested"
    config = CliConfig(config_dir=config_dir)

    config.set_active_settings_path(tmp_path / "tenant_settings.json")

    assert config_dir.is_dir()
    assert (config_dir / "config.json").is_file()


def test_set_active_settings_path_persists_as_json(tmp_path: Path) -> None:
    config_dir: Path = tmp_path / "config"
    config = CliConfig(config_dir=config_dir)
    pointed_at: Path = tmp_path / "tenant_settings.json"

    config.set_active_settings_path(pointed_at)

    on_disk: dict = json.loads((config_dir / "config.json").read_text())
    assert on_disk == {"tenant_settings_path": str(pointed_at)}


def test_get_active_settings_path_returns_none_when_pointer_field_empty(tmp_path: Path) -> None:
    config_dir: Path = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "config.json").write_text(json.dumps({"tenant_settings_path": ""}))
    config = CliConfig(config_dir=config_dir)

    assert config.get_active_settings_path() is None


def test_default_config_dir_uses_platformdirs(monkeypatch, tmp_path: Path) -> None:
    """Confirms the no-argument constructor defers to platformdirs, not a hardcoded path."""
    monkeypatch.setattr("cli.cli_config.platformdirs.user_config_dir", lambda name: str(tmp_path / name))

    config = CliConfig()

    assert config.config_dir == tmp_path / "crmfetch"
