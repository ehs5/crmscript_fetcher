"""
Unit tests for the crmfetch Cyclopts app.

These invoke cli.app.app (or cli.main, which wraps it) directly and
in-process - no subprocess - and monkeypatch the tenant_service/fetch_service
singletons cli.tenant_commands calls into. Per the spec's Testing Decisions,
this is the CLI seam only: it confirms each command's flags map onto the
correct core call with the correct arguments, not business-logic correctness
(that's covered at the core seam in test_tenant_service.py / test_fetch_service.py).

The tenant_service fixture below bypasses cli's lazy pointer resolution
entirely by pre-seeding cli.tenant_commands.tenant_service with a Mock - see
test_cli_settings.py for tests that exercise that resolution (the
no-pointer-configured error path, and the real pointer -> real file path).
"""
import json
from unittest.mock import Mock

import pytest

import cli
import cli.app
import cli.tenant_commands
from core import utility
from core.tenant_service import TenantService


@pytest.fixture(autouse=True)
def tenant_service(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """Replaces cli.tenant_commands' module-level TenantService singleton with a spec'd Mock."""
    service = Mock(spec=TenantService)
    monkeypatch.setattr(cli.tenant_commands, "tenant_service", service)
    return service


@pytest.fixture(autouse=True)
def fetch_service(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """Replaces cli.tenant_commands' FetchService singleton's fetch() with a Mock."""
    service = Mock(spec=cli.tenant_commands.fetch_service)
    monkeypatch.setattr(cli.tenant_commands, "fetch_service", service)
    return service


def run(args: list[str]) -> int:
    """Runs cli.main (the real entry point) in-process and returns its exit code."""
    with pytest.raises(SystemExit) as exc_info:
        cli.main(args)
    return exc_info.value.code


def test_list_json_prints_full_tenant_list_as_valid_json(
    tenant_service: Mock, capsys: pytest.CaptureFixture
) -> None:
    tenant_service.get_all_tenants.return_value = [
        {"id": 1, "tenant_name": "Acme", "url": "https://acme.example"}
    ]

    exit_code: int = run(["list", "--json"])

    assert exit_code == 0
    tenant_service.get_all_tenants.assert_called_once_with()
    printed: list[dict] = json.loads(capsys.readouterr().out)
    assert printed == [{"id": 1, "tenant_name": "Acme", "url": "https://acme.example"}]


def test_list_human_prints_id_name_url_per_tenant(
    tenant_service: Mock, capsys: pytest.CaptureFixture
) -> None:
    tenant_service.get_all_tenants.return_value = [
        {"id": 1, "tenant_name": "Acme", "url": "https://acme.example"},
        {"id": 2, "tenant_name": "Beta", "url": "https://beta.example"},
    ]

    exit_code: int = run(["list"])

    assert exit_code == 0
    out: str = capsys.readouterr().out
    assert "1: Acme (https://acme.example)" in out
    assert "2: Beta (https://beta.example)" in out


def test_search_json_prints_matching_tenants_as_valid_json(
    tenant_service: Mock, capsys: pytest.CaptureFixture
) -> None:
    tenant_service.search_tenants.return_value = [
        {"id": 1, "tenant_name": "Acme", "url": "https://acme.example"}
    ]

    exit_code: int = run(["search", "acme", "--json"])

    assert exit_code == 0
    tenant_service.search_tenants.assert_called_once_with("acme")
    printed: list[dict] = json.loads(capsys.readouterr().out)
    assert printed == [{"id": 1, "tenant_name": "Acme", "url": "https://acme.example"}]


def test_search_human_prints_id_name_url_per_matching_tenant(
    tenant_service: Mock, capsys: pytest.CaptureFixture
) -> None:
    tenant_service.search_tenants.return_value = [
        {"id": 2, "tenant_name": "Beta", "url": "https://beta.example"},
    ]

    exit_code: int = run(["search", "beta"])

    assert exit_code == 0
    tenant_service.search_tenants.assert_called_once_with("beta")
    out: str = capsys.readouterr().out
    assert "2: Beta (https://beta.example)" in out


def test_search_without_query_is_a_usage_error(tenant_service: Mock) -> None:
    exit_code: int = run(["search"])

    assert exit_code == 2
    tenant_service.search_tenants.assert_not_called()


def test_fetch_calls_get_tenant_by_id_then_fetches_that_tenant(
    tenant_service: Mock, fetch_service: Mock
) -> None:
    tenant: dict = {"id": 5, "tenant_name": "Acme", "url": "https://acme.example"}
    tenant_service.get_tenant_by_id.return_value = tenant
    fetch_service.fetch.return_value = {"success": True, "validation_error": False, "error": "", "info": ""}

    exit_code: int = run(["fetch", "5"])

    assert exit_code == 0
    tenant_service.get_tenant_by_id.assert_called_once_with(5)
    fetch_service.fetch.assert_called_once_with(tenant)


def test_fetch_prints_error_and_exits_one_on_fetch_failure(
    tenant_service: Mock, fetch_service: Mock, capsys: pytest.CaptureFixture
) -> None:
    tenant_service.get_tenant_by_id.return_value = {"id": 5, "tenant_name": "Acme", "url": "https://acme.example"}
    fetch_service.fetch.return_value = {
        "success": False,
        "validation_error": False,
        "error": "Failed to connect to SuperOffice",
        "info": "",
    }

    exit_code: int = run(["fetch", "5"])

    assert exit_code == 1
    assert "Failed to connect to SuperOffice" in capsys.readouterr().err


def test_fetch_unknown_id_exits_one_without_calling_fetch(
    tenant_service: Mock, fetch_service: Mock
) -> None:
    tenant_service.get_tenant_by_id.side_effect = ValueError("Tenant ID not found in tenant list")

    exit_code: int = run(["fetch", "999"])

    assert exit_code == 1
    fetch_service.fetch.assert_not_called()


def test_fetch_without_id_is_a_usage_error(tenant_service: Mock, fetch_service: Mock) -> None:
    exit_code: int = run(["fetch"])

    assert exit_code == 2
    tenant_service.get_tenant_by_id.assert_not_called()
    fetch_service.fetch.assert_not_called()


def test_fetch_all_flag_is_a_usage_error_not_fetch_everything(
    tenant_service: Mock, fetch_service: Mock
) -> None:
    exit_code: int = run(["fetch", "--all"])

    assert exit_code == 2
    tenant_service.get_tenant_by_id.assert_not_called()
    fetch_service.fetch.assert_not_called()


def test_add_calls_add_tenant_with_only_the_five_core_fields(tenant_service: Mock) -> None:
    tenant_service.add_tenant.return_value = {"id": 1, "tenant_name": "Acme"}
    tenant_service.get_all_tenants.return_value = [{"id": 1, "tenant_name": "Acme"}]

    exit_code: int = run([
        "add",
        "--name", "Acme",
        "--url", "https://acme.example",
        "--include-id", "acme-inc",
        "--key", "secret",
        "--local-dir", "/tmp/acme",
    ])

    assert exit_code == 0
    tenant_service.add_tenant.assert_called_once_with({
        "tenant_name": "Acme",
        "url": "https://acme.example",
        "include_id": "acme-inc",
        "key": "secret",
        "local_directory": "/tmp/acme",
    })


def test_add_backfills_default_fetch_options_via_core_helper(tenant_service: Mock) -> None:
    tenant_service.add_tenant.return_value = {"id": 1, "tenant_name": "Acme"}
    all_tenants: list[dict] = [{"id": 1, "tenant_name": "Acme"}]
    tenant_service.get_all_tenants.return_value = all_tenants

    run([
        "add",
        "--name", "Acme",
        "--url", "https://acme.example",
        "--include-id", "acme-inc",
        "--key", "secret",
        "--local-dir", "/tmp/acme",
    ])

    tenant_service.add_missing_fetch_options.assert_called_once_with(all_tenants)


def test_add_missing_required_flag_is_a_usage_error(tenant_service: Mock) -> None:
    exit_code: int = run(["add", "--name", "Acme"])

    assert exit_code == 2
    tenant_service.add_tenant.assert_not_called()


def test_edit_merges_specified_fields_onto_existing_tenant(tenant_service: Mock) -> None:
    tenant_service.get_tenant_by_id.return_value = {
        "id": 5,
        "tenant_name": "Acme",
        "url": "https://acme.example",
        "include_id": "acme-inc",
        "key": "secret",
        "local_directory": "/tmp/acme",
    }

    exit_code: int = run(["edit", "5", "--url", "https://new.example"])

    assert exit_code == 0
    tenant_service.update_tenant.assert_called_once_with({
        "id": 5,
        "tenant_name": "Acme",
        "url": "https://new.example",
        "include_id": "acme-inc",
        "key": "secret",
        "local_directory": "/tmp/acme",
    })


def test_edit_with_no_flags_leaves_all_fields_unchanged(tenant_service: Mock) -> None:
    tenant: dict = {
        "id": 5,
        "tenant_name": "Acme",
        "url": "https://acme.example",
        "include_id": "acme-inc",
        "key": "secret",
        "local_directory": "/tmp/acme",
    }
    tenant_service.get_tenant_by_id.return_value = dict(tenant)

    exit_code: int = run(["edit", "5"])

    assert exit_code == 0
    tenant_service.update_tenant.assert_called_once_with(tenant)


def test_edit_unknown_id_exits_one_without_calling_update(tenant_service: Mock) -> None:
    tenant_service.get_tenant_by_id.side_effect = ValueError("Tenant ID not found in tenant list")

    exit_code: int = run(["edit", "999", "--name", "Ghost"])

    assert exit_code == 1
    tenant_service.update_tenant.assert_not_called()


def test_delete_without_yes_prints_tenant_and_does_not_delete(
    tenant_service: Mock, capsys: pytest.CaptureFixture
) -> None:
    tenant_service.get_tenant_by_id.return_value = {
        "id": 5, "tenant_name": "Acme", "url": "https://acme.example"
    }

    exit_code: int = run(["delete", "5"])

    assert exit_code == 1
    tenant_service.delete_tenant.assert_not_called()
    assert "Acme" in capsys.readouterr().out


def test_delete_with_yes_calls_delete_tenant_and_exits_zero(tenant_service: Mock) -> None:
    tenant_service.get_tenant_by_id.return_value = {
        "id": 5, "tenant_name": "Acme", "url": "https://acme.example"
    }

    exit_code: int = run(["delete", "5", "--yes"])

    assert exit_code == 0
    tenant_service.delete_tenant.assert_called_once_with(5)


def test_version_matches_pyproject_toml(capsys: pytest.CaptureFixture) -> None:
    exit_code: int = run(["--version"])

    assert exit_code == 0
    assert capsys.readouterr().out.strip() == utility.get_current_version()


def test_version_shorthand_flag_matches_long_flag(capsys: pytest.CaptureFixture) -> None:
    exit_code: int = run(["-v"])

    assert exit_code == 0
    assert capsys.readouterr().out.strip() == utility.get_current_version()


def test_show_prints_human_readable_summary_by_default(tenant_service: Mock, capsys: pytest.CaptureFixture) -> None:
    tenant: dict = {
        "id": 5,
        "tenant_name": "Acme",
        "url": "https://acme.example",
        "include_id": "acme-inc",
        "key": "secret",
        "local_directory": "/tmp/acme",
        "fetch_options": {"fetch_scripts": True},
    }
    tenant_service.get_tenant_by_id.return_value = tenant

    exit_code: int = run(["show", "5"])

    assert exit_code == 0
    tenant_service.get_tenant_by_id.assert_called_once_with(5)
    out: str = capsys.readouterr().out
    assert "ID:   5" in out
    assert "Name: Acme" in out
    assert "https://acme.example" in out


def test_show_prints_full_tenant_as_json_with_json_flag(tenant_service: Mock, capsys: pytest.CaptureFixture) -> None:
    tenant: dict = {
        "id": 5,
        "tenant_name": "Acme",
        "url": "https://acme.example",
        "include_id": "acme-inc",
        "key": "secret",
        "local_directory": "/tmp/acme",
    }
    tenant_service.get_tenant_by_id.return_value = tenant

    exit_code: int = run(["show", "5", "--json"])

    assert exit_code == 0
    tenant_service.get_tenant_by_id.assert_called_once_with(5)
    assert json.loads(capsys.readouterr().out) == tenant


def test_show_unknown_id_exits_one(tenant_service: Mock) -> None:
    tenant_service.get_tenant_by_id.side_effect = ValueError("Tenant ID not found in tenant list")

    exit_code: int = run(["show", "999"])

    assert exit_code == 1


def test_main_remaps_bare_apps_usage_error_exit_code_to_two(tenant_service: Mock) -> None:
    # cli.app.app on its own exits 1 on a parse error (Cyclopts' own default
    # in this library version). cli.main - the actual console script entry
    # point - is what remaps that to exit code 2 for the CLI's contract.
    with pytest.raises(SystemExit) as bare_app_exit_info:
        cli.app.app(["fetch"])
    assert bare_app_exit_info.value.code == 1

    exit_code: int = run(["fetch"])

    assert exit_code == 2
