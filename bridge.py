# Exposes core tenant/fetch functions to the Vue frontend via pywebview.
# An Api instance is passed to webview.create_window(..., js_api=...) in main.py;
# pywebview reflects over its public methods, so each one below becomes callable
# from Vue as window.pywebview.api.<method_name>(...).
from fetch_service import FetchService
from tenant_service import TenantService
from utility import ask_directory_path, get_current_version, get_fetcher_script, open_directory


class Api:
    """
    pywebview js_api object exposing tenant/fetch operations to the Vue GUI.

    pywebview reflects over every non-underscore attribute of this instance,
    recursing into non-callable ones - so the wrapped services are kept
    private (leading underscore) to stop the Vue-facing API surface from
    also picking up their full internal method sets.
    """

    def __init__(self) -> None:
        self._tenant_service = TenantService()
        self._fetch_service = FetchService()

    def get_all_tenants(self, initial_load: bool = False) -> list[dict]:
        """Returns all tenants from tenant_settings.json."""
        return self._tenant_service.get_all_tenants(initial_load)

    def add_tenant(self, tenant: dict) -> dict:
        """Adds a new tenant and returns it with its assigned id."""
        return self._tenant_service.add_tenant(tenant)

    def update_tenant(self, tenant: dict) -> None:
        """Updates an existing tenant by id."""
        self._tenant_service.update_tenant(tenant)

    def delete_tenant(self, tenant_id: int) -> None:
        """Deletes a tenant by id."""
        self._tenant_service.delete_tenant(tenant_id)

    def fetch(self, tenant: dict) -> dict:
        """Fetches CRMScripts and other data from SuperOffice for the given tenant."""
        return self._fetch_service.fetch(tenant)

    def get_fetcher_script(self) -> str:
        """Returns the contents of the CRMScript fetcher script."""
        return get_fetcher_script()

    def ask_directory_path(self) -> str:
        """Opens a native folder picker and returns the chosen path."""
        return ask_directory_path()

    def open_directory(self, directory_path: str) -> None:
        """Opens the given directory in the OS file explorer."""
        open_directory(directory_path)

    def get_current_version(self) -> str:
        """Returns the current CRMScript Fetcher version."""
        return get_current_version()
