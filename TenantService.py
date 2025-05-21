import json
from utility import get_app_directory


class TenantService:
    """
    Service class for reading and saving the TenantSettings.json file.
    """
    def __init__(self):
        self.tenant_settings_filename = get_app_directory() / "tenant_settings.json"

    def getAllTenants(self) -> list[dict]:
        """"
        Loads and returns the tenant settings file from file.
        TODO: Can I return it like does or must it be a json?
        """
        with open(self.tenant_settings_filename) as f:
            return json.load(f)

    def save(self, tenant_settings: list[dict]):
        """Saves entire JSON file"""
        with open(self.tenant_settings_filename, "w") as f:
            f.write(json.dumps(self.tenant_settings, indent=4))

    def get_next_id(self) -> int:
        all_tenants: list[dict] = self.getAllTenants()
        return max(t["id"] for t in all_tenants) + 1

    def add_tenant(self, new_tenant: dict) -> dict:
        """
        Adds a new tenant to json file
        Returns the tenant with new ID
        """
        # Some basic validation to make sure frontend isn't sending empty objects
        if not new_tenant.get("tenant_name"):
            raise Exception("Tenant name is missing")

        new_tenant["id"] = self.get_next_id()

        with open(self.tenant_settings_filename, 'r+') as f:
            tenants: list[dict] = json.load(f)
            tenants.append(new_tenant)
            f.seek(0)
            json.dump(tenants, f, indent=4)

        return new_tenant



    # TODO: Remember to always include this in frontend instead of doing it here
    #
    # def add_missing_fetch_options(self) -> None:
    #     """
    #     Checks if there are any tenants without "fetch options", and if so adds a default dictionary to each.
    #     Is done because earlier CRMScript Fetcher version did not contain this object in JSON.
    #     """
    #     for tenant in [t for t in self.tenant_settings if t.get("fetch_options") is None]:
    #         tenant["fetch_options"] = self.construct_fetch_options()
    #     self.save_json()
    #
    # def construct_fetch_options(fetch_scripts: bool = True,
    #                             fetch_triggers: bool = True,
    #                             fetch_screens: bool = True,
    #                             fetch_screen_choosers: bool = True,
    #                             fetch_scheduled_tasks: bool = True,
    #                             fetch_extra_tables: bool = True) -> dict:
    #     """Creates a fetch_options dictionary. All options are defaulted to True."""
    #     return {
    #         "fetch_scripts": fetch_scripts,
    #         "fetch_triggers": fetch_triggers,
    #         "fetch_screens": fetch_screens,
    #         "fetch_screen_choosers": fetch_screen_choosers,
    #         "fetch_scheduled_tasks": fetch_scheduled_tasks,
    #         "fetch_extra_tables": fetch_extra_tables
    #     }
