"""
CLI-level tests for the `crmfetch settings` command group and the lazy
tenant_service pointer resolution it feeds (ticket 05).

Unlike test_cli.py, these do not stub out TenantService with a Mock - the
point of this file is to prove the CLI genuinely reads/writes whichever file
its pointer names, not a bundled default. Every test monkeypatches
platformdirs' config-dir resolution to a tmp_path, so no test ever touches
the developer's real ~/.config (or platform equivalent) or real
tenant_settings.json.
"""
import json
from pathlib import Path

import pytest

import cli
from utility import get_app_directory


def shipped_default_tenants() -> list[dict]:
    """Reads the actual shipped tenant_settings.json template - the same file `settings init` copies from."""
    template_path: Path = get_app_directory() / "tenant_settings.json"
    return json.loads(template_path.read_text())


@pytest.fixture(autouse=True)
def reset_tenant_service_singleton(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    cli.tenant_service is a module-level cache, lazily populated by the first
    command that resolves it. Force it back to unresolved before every test
    in this file, so each test genuinely exercises pointer resolution instead
    of reusing whatever a previous test (in this file or another) resolved.
    """
    monkeypatch.setattr(cli, "tenant_service", None)


@pytest.fixture(autouse=True)
def isolated_config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Points platformdirs.user_config_dir("crmfetch") at a tmp directory for every test."""
    config_dir: Path = tmp_path / "config"
    monkeypatch.setattr("cli_config.platformdirs.user_config_dir", lambda name: str(config_dir / name))
    return config_dir


def run(args: list[str]) -> int:
    """Runs cli.main (the real entry point) in-process and returns its exit code."""
    with pytest.raises(SystemExit) as exc_info:
        cli.main(args)
    return exc_info.value.code


def test_settings_path_reports_not_configured_yet(capsys: pytest.CaptureFixture) -> None:
    exit_code: int = run(["settings", "path"])

    assert exit_code == 0
    out: str = capsys.readouterr().out
    assert "configured yet" in out.lower()


def test_list_without_pointer_configured_exits_one_naming_settings_commands(
    capsys: pytest.CaptureFixture,
) -> None:
    exit_code: int = run(["list"])

    assert exit_code == 1
    err: str = capsys.readouterr().err
    assert "settings set" in err
    assert "settings init" in err


def test_show_without_pointer_configured_exits_one(capsys: pytest.CaptureFixture) -> None:
    exit_code: int = run(["show", "1"])

    assert exit_code == 1


def test_settings_set_validates_path_exists(tmp_path: Path) -> None:
    missing_path: Path = tmp_path / "nope.json"

    exit_code: int = run(["settings", "set", str(missing_path)])

    assert exit_code == 1


def test_settings_set_validates_valid_json(tmp_path: Path) -> None:
    bad_json_path: Path = tmp_path / "bad.json"
    bad_json_path.write_text("not json")

    exit_code: int = run(["settings", "set", str(bad_json_path)])

    assert exit_code == 1


def test_settings_set_validates_json_is_a_list(tmp_path: Path) -> None:
    dict_path: Path = tmp_path / "dict.json"
    dict_path.write_text(json.dumps({"not": "a list"}))

    exit_code: int = run(["settings", "set", str(dict_path)])

    assert exit_code == 1


def test_settings_set_does_not_modify_the_file_it_points_at(tmp_path: Path) -> None:
    settings_path: Path = tmp_path / "tenant_settings.json"
    original_content = json.dumps([{"id": 1, "tenant_name": "Untouched", "url": "https://untouched.example"}])
    settings_path.write_text(original_content)

    exit_code: int = run(["settings", "set", str(settings_path)])

    assert exit_code == 0
    assert settings_path.read_text() == original_content


def test_settings_set_then_path_reports_the_configured_file(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    settings_path: Path = tmp_path / "tenant_settings.json"
    settings_path.write_text("[]")

    run(["settings", "set", str(settings_path)])
    capsys.readouterr()
    exit_code: int = run(["settings", "path"])

    assert exit_code == 0
    assert str(settings_path.resolve()) in capsys.readouterr().out


def test_settings_init_creates_default_tenant_and_sets_it_active(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    settings_path: Path = tmp_path / "fresh" / "tenant_settings.json"

    exit_code: int = run(["settings", "init", str(settings_path)])
    capsys.readouterr()

    assert exit_code == 0
    on_disk: list[dict] = json.loads(settings_path.read_text())
    assert on_disk == shipped_default_tenants()

    path_exit_code: int = run(["settings", "path"])
    assert path_exit_code == 0
    assert str(settings_path.resolve()) in capsys.readouterr().out


def test_settings_init_backs_up_pre_existing_file_instead_of_overwriting(tmp_path: Path) -> None:
    settings_path: Path = tmp_path / "tenant_settings.json"
    settings_path.write_text(json.dumps([{"id": 99, "tenant_name": "Old data", "url": "https://old.example"}]))

    exit_code: int = run(["settings", "init", str(settings_path)])

    assert exit_code == 0
    backup_path: Path = tmp_path / "tenant_settings.backup.json"
    assert json.loads(backup_path.read_text())[0]["tenant_name"] == "Old data"
    assert json.loads(settings_path.read_text()) == shipped_default_tenants()


def test_settings_init_does_not_overwrite_an_existing_backup(tmp_path: Path) -> None:
    settings_path: Path = tmp_path / "tenant_settings.json"
    settings_path.write_text(json.dumps([{"id": 1, "tenant_name": "First backup target", "url": "https://a.example"}]))
    run(["settings", "init", str(settings_path)])

    settings_path.write_text(json.dumps([{"id": 2, "tenant_name": "Second backup target", "url": "https://b.example"}]))
    exit_code: int = run(["settings", "init", str(settings_path)])

    assert exit_code == 0
    first_backup: Path = tmp_path / "tenant_settings.backup.json"
    second_backup: Path = tmp_path / "tenant_settings.backup-2.json"
    assert json.loads(first_backup.read_text())[0]["tenant_name"] == "First backup target"
    assert json.loads(second_backup.read_text())[0]["tenant_name"] == "Second backup target"


def test_once_pointer_set_list_reads_the_configured_tmp_file(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    settings_path: Path = tmp_path / "tenant_settings.json"
    settings_path.write_text(json.dumps([{"id": 7, "tenant_name": "FromTmpFile", "url": "https://tmp.example"}]))
    run(["settings", "set", str(settings_path)])
    capsys.readouterr()

    exit_code: int = run(["list"])

    assert exit_code == 0
    assert "FromTmpFile" in capsys.readouterr().out


def test_once_pointer_set_add_writes_to_the_configured_tmp_file(tmp_path: Path) -> None:
    settings_path: Path = tmp_path / "tenant_settings.json"
    settings_path.write_text("[]")
    run(["settings", "set", str(settings_path)])

    exit_code: int = run([
        "add",
        "--name", "Acme",
        "--url", "https://acme.example",
        "--include-id", "acme-inc",
        "--key", "secret",
        "--local-dir", "/tmp/acme",
    ])

    assert exit_code == 0
    on_disk: list[dict] = json.loads(settings_path.read_text())
    assert on_disk[0]["tenant_name"] == "Acme"


def test_once_pointer_set_delete_removes_from_the_configured_tmp_file(tmp_path: Path) -> None:
    settings_path: Path = tmp_path / "tenant_settings.json"
    settings_path.write_text(json.dumps([{"id": 1, "tenant_name": "Acme", "url": "https://acme.example"}]))
    run(["settings", "set", str(settings_path)])

    exit_code: int = run(["delete", "1", "--yes"])

    assert exit_code == 0
    assert json.loads(settings_path.read_text()) == []
