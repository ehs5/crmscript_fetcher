import json


class TenantSettingsJson:
    """
    Represents the tenant settings JSON file. By "tenant" we mean a SuperOffice installation.
    """
    def __init__(self, add_fetch_options: bool = False):
        self.tenant_settings_filename: str = "tenant_settings.json"

        self.tenant_settings: list[dict] = []
        with open(self.tenant_settings_filename) as f:
            self.tenant_settings = json.load(f)

        if add_fetch_options:
            self.add_missing_fetch_options()

    def add_missing_fetch_options(self) -> None:
        """
        Checks if there are any tenants without "fetch options", and if so adds a default dictionary to each.
        Is done because earlier CRMScript Fetcher version did not contain this object in JSON.
        """
        for tenant in [t for t in self.tenant_settings if t.get("fetch_options") is None]:
            tenant["fetch_options"] = construct_fetch_options()
        self.save_json()

    def get_tenant_by_id(self, tenant_id: int) -> dict | None:
        return [t for t in self.tenant_settings if t.get("id") == tenant_id][0]

    def get_no_of_tenants(self) -> int:
        return len(self.tenant_settings)

    def get_last_tenant(self) -> dict | None:
        """Returns the last tenant entry in json file"""
        if len(self.tenant_settings) > 0:
            return self.tenant_settings[-1]

    def local_directory_taken(self, tenant_id: int, local_directory: str) -> bool | None:
        """Returns True if another tenant in the tenant settings file uses the given local directory path"""
        for t in self.tenant_settings:
            if (t.get("id") != tenant_id) and (t.get("local_directory") == local_directory):
                return True

    def add_tenant(self) -> dict:
        """Adds a new tenant to json file with default values and returns the dict"""

        next_id: int = max(t["id"] for t in self.tenant_settings) + 1
        new_tenant: dict = {"id": next_id,
                            "tenant_name": "New tenant",
                            "url": 'https://online.superoffice.com/CustXXXXX/CS',
                            "include_id": 'crmscript_fetcher',
                            "key": "",
                            "local_directory": "",
                            "fetch_options": construct_fetch_options()}

        with open(self.tenant_settings_filename, 'r+') as f:
            tenants: list = json.load(f)
            tenants.append(new_tenant)
            f.seek(0)
            json.dump(tenants, f, indent=4)

        return new_tenant

    def delete_tenant(self, tenant: dict) -> None:
        """Deletes a tenant from json file by its ID"""
        for t in self.tenant_settings:
            if t == tenant:
                self.tenant_settings.remove(t)
                break

        self.save_json()

    def update_tenant(self, updated_tenant: dict) -> None:
        """
        Updates an existing tenant in json file by its ID
        NOTE: Use self.update_tenant_fetch_options to update fetch options
        """
        tenant: dict = [t for t in self.tenant_settings if t.get("id") == updated_tenant.get("id")][0]
        tenant["tenant_name"] = updated_tenant.get("tenant_name")
        tenant["include_id"] = updated_tenant.get("include_id")
        tenant["key"] = updated_tenant.get("key")
        tenant["local_directory"] = updated_tenant.get("local_directory")
        tenant["url"] = updated_tenant.get("url").rstrip("/")
        self.save_json()

    def update_tenant_fetch_options(self, tenant_id: int, fetch_options: dict):
        """Saves fetch options of a given tenant ID."""
        tenant: dict = [t for t in self.tenant_settings if t.get("id") == tenant_id][0]
        tenant["fetch_options"] = fetch_options
        self.save_json()

    def save_json(self):
        """Saves self.tenant_settings to JSON as is"""
        with open(self.tenant_settings_filename, "w") as f:
            f.write(json.dumps(self.tenant_settings, indent=4))


def construct_fetch_options(fetch_scripts: bool = True,
                            fetch_triggers: bool = True,
                            fetch_screens: bool = True,
                            fetch_screen_choosers: bool = True,
                            fetch_scheduled_tasks: bool = True,
                            fetch_extra_tables: bool = True) -> dict:
    """Creates a fetch_options dictionary. All options are defaulted to True."""
    return {
        "fetch_scripts": fetch_scripts,
        "fetch_triggers": fetch_triggers,
        "fetch_screens": fetch_screens,
        "fetch_screen_choosers": fetch_screen_choosers,
        "fetch_scheduled_tasks": fetch_scheduled_tasks,
        "fetch_extra_tables": fetch_extra_tables
    }
