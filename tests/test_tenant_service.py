"""
Unit tests for tenant_service.TenantService.

These test the core seam directly (no Eel/GUI involved) against a real
tenant_settings.json file written to a pytest tmp_path, matching how
TenantService is actually used - a thin wrapper around a JSON file on disk.
"""
import json
from pathlib import Path

import pytest

from tenant_service import TenantService


@pytest.fixture
def settings_file(tmp_path: Path) -> Path:
    """Writes an empty tenant_settings.json to tmp_path and returns its path."""
    path: Path = tmp_path / "tenant_settings.json"
    path.write_text("[]")
    return path


@pytest.fixture
def service(settings_file: Path, monkeypatch: pytest.MonkeyPatch) -> TenantService:
    """Returns a TenantService pointed at the fixture's tenant_settings.json."""
    monkeypatch.setattr("tenant_service.get_app_directory", lambda: settings_file.parent)
    return TenantService()


def test_get_all_tenants_returns_empty_list_for_new_file(service: TenantService) -> None:
    assert service.get_all_tenants() == []


def test_add_tenant_assigns_incrementing_ids(service: TenantService) -> None:
    first: dict = service.add_tenant({"tenant_name": "Acme", "url": "https://acme.example"})
    second: dict = service.add_tenant({"tenant_name": "Beta", "url": "https://beta.example"})

    assert first["id"] == 1
    assert second["id"] == 2
    assert [t["id"] for t in service.get_all_tenants()] == [1, 2]


def test_add_tenant_persists_to_disk(service: TenantService, settings_file: Path) -> None:
    service.add_tenant({"tenant_name": "Acme", "url": "https://acme.example"})

    on_disk: list[dict] = json.loads(settings_file.read_text())
    assert len(on_disk) == 1
    assert on_disk[0]["tenant_name"] == "Acme"


def test_add_tenant_without_name_raises(service: TenantService) -> None:
    with pytest.raises(Exception):
        service.add_tenant({"url": "https://acme.example"})


def test_add_tenant_without_url_raises(service: TenantService) -> None:
    with pytest.raises(Exception):
        service.add_tenant({"tenant_name": "Acme"})


def test_get_tenant_by_id_returns_matching_tenant(service: TenantService) -> None:
    added: dict = service.add_tenant({"tenant_name": "Acme", "url": "https://acme.example"})

    found: dict = service.get_tenant_by_id(added["id"])

    assert found["tenant_name"] == "Acme"


def test_get_tenant_by_id_raises_when_not_found(service: TenantService) -> None:
    with pytest.raises(ValueError):
        service.get_tenant_by_id(999)


def test_update_tenant_replaces_fields_and_persists(service: TenantService, settings_file: Path) -> None:
    added: dict = service.add_tenant({"tenant_name": "Acme", "url": "https://acme.example"})
    added["tenant_name"] = "Acme Renamed"

    service.update_tenant(added)

    on_disk: list[dict] = json.loads(settings_file.read_text())
    assert on_disk[0]["tenant_name"] == "Acme Renamed"


def test_update_tenant_without_id_raises(service: TenantService) -> None:
    with pytest.raises(ValueError):
        service.update_tenant({"tenant_name": "Acme"})


def test_update_tenant_without_name_raises(service: TenantService) -> None:
    with pytest.raises(ValueError):
        service.update_tenant({"id": 1})


def test_update_tenant_unknown_id_raises(service: TenantService) -> None:
    with pytest.raises(ValueError):
        service.update_tenant({"id": 999, "tenant_name": "Ghost"})


def test_delete_tenant_removes_it_and_persists(service: TenantService, settings_file: Path) -> None:
    added: dict = service.add_tenant({"tenant_name": "Acme", "url": "https://acme.example"})

    service.delete_tenant(added["id"])

    assert service.get_all_tenants() == []
    assert json.loads(settings_file.read_text()) == []


def test_delete_tenant_without_id_raises(service: TenantService) -> None:
    with pytest.raises(ValueError):
        service.delete_tenant(None)


def test_delete_tenant_unknown_id_raises(service: TenantService) -> None:
    with pytest.raises(ValueError):
        service.delete_tenant(999)


def test_get_all_tenants_backfills_missing_fetch_options_on_initial_load(
    service: TenantService, settings_file: Path
) -> None:
    settings_file.write_text(json.dumps([
        {"id": 1, "tenant_name": "Legacy", "url": "https://legacy.example"}
    ]))

    tenants: list[dict] = service.get_all_tenants(initial_load=True)

    expected_fetch_options: dict = {
        "fetch_scripts": True,
        "fetch_triggers": True,
        "fetch_screens": True,
        "fetch_screen_choosers": True,
        "fetch_scheduled_tasks": True,
        "fetch_extra_tables": True,
    }
    assert tenants[0]["fetch_options"] == expected_fetch_options

    # Backfill must be persisted, not just returned in-memory.
    on_disk: list[dict] = json.loads(settings_file.read_text())
    assert on_disk[0]["fetch_options"] == expected_fetch_options


def test_get_all_tenants_without_initial_load_does_not_backfill(
    service: TenantService, settings_file: Path
) -> None:
    settings_file.write_text(json.dumps([
        {"id": 1, "tenant_name": "Legacy", "url": "https://legacy.example"}
    ]))

    tenants: list[dict] = service.get_all_tenants(initial_load=False)

    assert tenants[0].get("fetch_options") is None


def test_explicit_settings_path_is_used_directly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    An explicit settings_path must be used as-is, bypassing get_app_directory()
    entirely - this is the CLI's pointer feature (ticket 05), which must never
    fall back to the bundled default TenantService()'s no-argument constructor
    resolves for the GUI.
    """
    explicit_path: Path = tmp_path / "somewhere-else" / "pointed_at.json"
    explicit_path.parent.mkdir()
    explicit_path.write_text(json.dumps([{"id": 1, "tenant_name": "Pointed", "url": "https://pointed.example"}]))

    def fail_if_called() -> Path:
        raise AssertionError("get_app_directory() must not be called when an explicit path is given")

    monkeypatch.setattr("tenant_service.get_app_directory", fail_if_called)

    service = TenantService(explicit_path)

    assert service.tenant_settings_filename == explicit_path
    assert service.get_all_tenants()[0]["tenant_name"] == "Pointed"


def test_no_argument_constructor_still_resolves_via_get_app_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Confirms TenantService() with no arguments is unaffected by the optional
    settings_path parameter - this is the GUI's own default and must keep
    resolving via get_app_directory() exactly as before.
    """
    monkeypatch.setattr("tenant_service.get_app_directory", lambda: tmp_path)
    (tmp_path / "tenant_settings.json").write_text("[]")

    service = TenantService()

    assert service.tenant_settings_filename == tmp_path / "tenant_settings.json"
