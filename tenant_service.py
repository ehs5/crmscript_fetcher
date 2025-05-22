import json
from utility import get_app_directory


class TenantService:
    """
    Service class for reading and saving the TenantSettings.json file.
    """
    def __init__(self):
        self.tenant_settings_filename = get_app_directory() / "tenant_settings.json"

    def get_all_tenants(self) -> list[dict]:
        """"
        Loads and returns the tenant settings file from file.
        TODO: Can I return it like does or must it be a json?
        """
        with open(self.tenant_settings_filename) as f:
            return json.load(f)

    def save(self, tenant_settings: list[dict]):
        """Saves entire JSON file"""
        with open(self.tenant_settings_filename, "w") as f:
            f.write(json.dumps(tenant_settings, indent=4))

    @staticmethod
    def get_next_id(all_tenants: list[dict]) -> int:
        if not all_tenants: return 1
        return max(t["id"] for t in all_tenants) + 1

    def add_tenant(self, new_tenant: dict) -> dict:
        """
        Adds a new tenant to json file
        Returns the tenant with new ID
        """
        # To make sure frontend isn't sending empty objects
        if not new_tenant.get("tenant_name"):
            raise Exception("Tenant name is missing")

        if not new_tenant.get("url"):
            raise Exception("URL is missing")

        with open(self.tenant_settings_filename, 'r+') as f:
            tenants: list[dict] = json.load(f)

            # Set the new tenant's ID before adding to list
            new_tenant["id"] = self.get_next_id(tenants)
            tenants.append(new_tenant)

            f.seek(0)
            json.dump(tenants, f, indent=4)

        return new_tenant

    @staticmethod
    def get_tenant_index(all_tenants: list[dict], tenant_id: int) -> int:
        """
        Returns the JSON array index of the tenant by its ID.
        """
        for i, tenant in enumerate(all_tenants):
            if tenant.get("id") == tenant_id:
                return i
        raise ValueError("Tenant ID not found in tenant list")

    def update_tenant(self, tenant: dict):
        """
        Updates an existing tenant in json file by its ID.
        """
        # Some basic validation to make sure Vue isn't sending faulty objects
        if not tenant.get("id"):
            raise ValueError("Tenant ID missing")

        if not tenant.get("tenant_name"):
            raise ValueError("Tenant must have a name")

        # Find the index of the given tenant in the JSON array so we can replace it.
        all_tenants: list[dict] = self.get_all_tenants()
        tenant_index: int = self.get_tenant_index(all_tenants, tenant["id"])

        if all_tenants[tenant_index] == tenant:
            return # No changes, no need to save

        # Replace tenant object and save file
        all_tenants[tenant_index] = tenant
        self.save(all_tenants)

    def delete_tenant(self, tenant_id: int) -> None:
        """
        Deletes a tenant from json file by its ID.
        """
        if not tenant_id:
            raise ValueError("Tenant ID missing")

        # Find the index of the given tenant in the JSON array so we can delete it.
        all_tenants: list[dict] = self.get_all_tenants()
        tenant_index: int = self.get_tenant_index(all_tenants, tenant_id)
        all_tenants.pop(tenant_index)
        self.save(all_tenants)

    # def get_tenant(self, tenant_id: int) -> dict:
    #    """
    #    Returns the tenant from JSON file by its ID
    #    TODO: Are we using this?
    #    """
    #    all_tenants: list[dict] = self.get_all_tenants()
    #    return [t for t in all_tenants if t.get("id") == tenant_id][0]

    # # TODO move to frontend
    # def local_directory_taken(self, tenant_id: int, local_directory: str) -> bool | None:
    #    """Returns True if another tenant in the tenant settings file uses the given local directory path"""
    #    for t in self.tenant_settings:
    #        if (t.get("id") != tenant_id) and (t.get("local_directory") == local_directory):
    #            return True


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
