"""
Unit tests for fetch_service.FetchService.

The SuperOffice HTTP call (requests.get) is mocked; everything else runs for
real against a tmp_path local_directory, matching the existing pattern in
fetch_service.py itself (plain requests mocking, no framework coupling).
"""
import json
from pathlib import Path
from unittest.mock import Mock

import pytest
import requests

from core.fetch_service import FetchService
from core.utility import get_current_version


@pytest.fixture
def tenant(tmp_path: Path) -> dict:
    """Returns a valid tenant dict with an empty local_directory on tmp_path."""
    local_directory: Path = tmp_path / "tenant_dir"
    local_directory.mkdir()

    return {
        "id": 1,
        "tenant_name": "Acme",
        "url": "https://acme.superoffice.com",
        "include_id": "crmscript-fetcher",
        "key": "secret-key",
        "local_directory": str(local_directory),
        "fetch_options": {
            "fetch_scripts": True,
            "fetch_triggers": False,
            "fetch_screens": False,
            "fetch_screen_choosers": False,
            "fetch_scheduled_tasks": False,
            "fetch_extra_tables": False,
        },
    }


def mock_response(text: str) -> Mock:
    """Builds a Mock standing in for requests.Response, with a no-op raise_for_status."""
    response: Mock = Mock()
    response.raise_for_status = Mock()
    response.text = text
    return response


def test_fetch_success(monkeypatch: pytest.MonkeyPatch, tenant: dict) -> None:
    payload: dict = {
        "script_version": 2,
        "group_scripts": {"script_folders": [], "scripts": []},
    }
    monkeypatch.setattr("core.fetch_service.requests.get", lambda url, **kwargs: mock_response(json.dumps(payload)))

    result: dict = FetchService().fetch(tenant)

    assert result == {"success": True, "validation_error": False, "error": "", "info": ""}


def test_fetch_success_flags_outdated_script_version(monkeypatch: pytest.MonkeyPatch, tenant: dict) -> None:
    # No script_version key -> defaults to v1, which is older than CURRENT_CRMSCRIPT_VERSION.
    payload: dict = {"script_folders": [], "scripts": [], "triggers": []}
    monkeypatch.setattr("core.fetch_service.requests.get", lambda url, **kwargs: mock_response(json.dumps(payload)))

    result: dict = FetchService().fetch(tenant)

    assert result["success"] is True
    assert result["info"] != ""
    assert "<br>" not in result["info"]


def test_fetch_validation_error_when_key_missing(tenant: dict) -> None:
    tenant["key"] = ""

    result: dict = FetchService().fetch(tenant)

    assert result["success"] is False
    assert result["validation_error"] is True
    assert "Script key cannot be empty" in result["error"]
    assert "<br>" not in result["error"]
    assert "\n" in result["error"]


def test_fetch_validation_error_when_no_fetch_option_enabled(tenant: dict) -> None:
    tenant["fetch_options"] = {key: False for key in tenant["fetch_options"]}

    result: dict = FetchService().fetch(tenant)

    assert result["validation_error"] is True
    assert "You must check at least one fetch option" in result["error"]


def test_fetch_http_connection_error(monkeypatch: pytest.MonkeyPatch, tenant: dict) -> None:
    def raise_connection_error(url: str, **kwargs) -> None:
        raise requests.ConnectionError("connection refused")

    monkeypatch.setattr("core.fetch_service.requests.get", raise_connection_error)

    result: dict = FetchService().fetch(tenant)

    assert result["success"] is False
    assert result["validation_error"] is False
    assert "Failed to connect to SuperOffice" in result["error"]
    assert "<br>" not in result["error"]


def test_fetch_http_error_status(monkeypatch: pytest.MonkeyPatch, tenant: dict) -> None:
    response: Mock = mock_response("")
    response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
    monkeypatch.setattr("core.fetch_service.requests.get", lambda url, **kwargs: response)

    result: dict = FetchService().fetch(tenant)

    assert result["success"] is False
    assert "HTTP error occurred" in result["error"]
    assert "<br>" not in result["error"]


def test_fetch_invalid_json_response(monkeypatch: pytest.MonkeyPatch, tenant: dict) -> None:
    monkeypatch.setattr("core.fetch_service.requests.get", lambda url, **kwargs: mock_response("not valid json"))

    result: dict = FetchService().fetch(tenant)

    assert result["success"] is False
    assert result["validation_error"] is False
    assert "Invalid JSON response from server" in result["error"]
    assert "<br>" not in result["error"]
    assert "\n" in result["error"]


def test_fetch_verifies_ssl_certificate_by_default(monkeypatch: pytest.MonkeyPatch, tenant: dict) -> None:
    payload: dict = {"script_version": 2, "group_scripts": {"script_folders": [], "scripts": []}}
    get: Mock = Mock(return_value=mock_response(json.dumps(payload)))
    monkeypatch.setattr("core.fetch_service.requests.get", get)

    FetchService().fetch(tenant)

    assert get.call_args.kwargs["verify"] is True


def test_fetch_sends_crmfetch_version_user_agent_by_default(monkeypatch: pytest.MonkeyPatch, tenant: dict) -> None:
    payload: dict = {"script_version": 2, "group_scripts": {"script_folders": [], "scripts": []}}
    get: Mock = Mock(return_value=mock_response(json.dumps(payload)))
    monkeypatch.setattr("core.fetch_service.requests.get", get)

    FetchService().fetch(tenant)

    assert get.call_args.kwargs["headers"]["User-Agent"] == f"crmfetch/{get_current_version()}"


def test_fetch_sends_custom_user_agent(monkeypatch: pytest.MonkeyPatch, tenant: dict) -> None:
    payload: dict = {"script_version": 2, "group_scripts": {"script_folders": [], "scripts": []}}
    get: Mock = Mock(return_value=mock_response(json.dumps(payload)))
    monkeypatch.setattr("core.fetch_service.requests.get", get)

    FetchService().fetch(tenant, user_agent="foobar")

    assert get.call_args.kwargs["headers"]["User-Agent"] == "foobar"


def test_fetch_ignore_ssl_certificate_error_disables_verification(monkeypatch: pytest.MonkeyPatch, tenant: dict) -> None:
    payload: dict = {"script_version": 2, "group_scripts": {"script_folders": [], "scripts": []}}
    get: Mock = Mock(return_value=mock_response(json.dumps(payload)))
    monkeypatch.setattr("core.fetch_service.requests.get", get)

    result: dict = FetchService().fetch(tenant, ignore_ssl_certificate_error=True)

    assert result["success"] is True
    assert get.call_args.kwargs["verify"] is False


def test_fetch_ssl_error_suggests_ignore_flag(monkeypatch: pytest.MonkeyPatch, tenant: dict) -> None:
    def raise_ssl_error(url: str, **kwargs) -> None:
        raise requests.exceptions.SSLError("certificate verify failed")

    monkeypatch.setattr("core.fetch_service.requests.get", raise_ssl_error)

    result: dict = FetchService().fetch(tenant)

    assert result["success"] is False
    assert "SSL certificate verification failed" in result["error"]
    assert "--ignore-ssl-certificate-error" in result["error"]
