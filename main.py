from files_and_folders import create_folder
from files_and_folders import delete_folder
from files_and_folders import move_folder
from files_and_folders import create_scripts_hierarchy
from files_and_folders import create_trigger_files
from files_and_folders import create_screens_hierarchy
from files_and_folders import create_screen_chooser_files

import json
import requests


# Represents the tenant settings json file. By "tenant" we mean a SuperOffice installation.
class TenantSettingsJson:
    def __init__(self):
        self.tenant_settings_filename: str = "tenant_settings.json"
        self.tenant_settings: list[dict] = []
        self.fetch_tenant_settings_from_json()

    # Loads the current data in the tenant settings JSON file as a list of dicts
    def fetch_tenant_settings_from_json(self) -> None:
        with open(self.tenant_settings_filename) as f:
            self.tenant_settings = json.load(f)

    def get_tenant_by_id(self, tenant_id: int) -> dict | None:
        for t in self.tenant_settings:
            if t.get("id") == tenant_id:
                return t

    def get_no_of_tenants_in_json(self) -> int:
        return len(self.tenant_settings)

    # Returns the last tenant in json file
    def get_last_tenant_in_json(self) -> dict | None:
        if len(self.tenant_settings) > 0:
            return self.tenant_settings[-1]

    # Returns True if another tenant in the tenant settings file uses the given local directory path
    def local_directory_already_used_by_tenant(self, tenant_id: int, local_directory: str) -> bool | None:
        for t in self.tenant_settings:
            if (t.get("id") != tenant_id) and (t.get("local_directory") == local_directory):
                return True

    # Adds a new tenant to json file with default values and returns the dict
    def add_tenant_to_json(self) -> dict:
        next_id: int = max(t["id"] for t in self.tenant_settings) + 1
        new_tenant: dict = {"id": next_id,
                            "tenant_name": "New tenant",
                            'url': 'https://online.superoffice.com/CustXXXXX/CS',
                            "include_id": 'crmscript_fetcher',
                            'key': "",
                            'local_directory': ""}

        with open(self.tenant_settings_filename, 'r+') as f:
            data = json.load(f)
            data.append(new_tenant)
            f.seek(0)
            json.dump(data, f, indent=4)

        return new_tenant

    # Deletes a tenant from json file by its ID
    def delete_tenant_from_json(self, tenant: dict) -> None:
        for t in self.tenant_settings:
            if t == tenant:
                self.tenant_settings.remove(t)
                break

        with open(self.tenant_settings_filename, "w") as f:
            f.write(json.dumps(self.tenant_settings, indent=4))

    # Updates an existing tenant in json file by its ID
    def update_tenant_in_json(self, updated_tenant: dict) -> None:
        for t in self.tenant_settings:
            if t.get("id") == updated_tenant.get("id"):
                t["tenant_name"] = updated_tenant.get("tenant_name")
                t["include_id"] = updated_tenant.get("include_id")
                t["key"] = updated_tenant.get("key")
                t["local_directory"] = updated_tenant.get("local_directory")
                t["url"] = updated_tenant.get("url").rstrip("/")
                break

        with open(self.tenant_settings_filename, "w") as f:
            f.write(json.dumps(self.tenant_settings, indent=4))


# Used for getting JSON from SuperOffice and performing the fetch itself
class Fetch:
    def __init__(self, tenant: dict):
        self.json: dict | None = None
        self.tenant: dict = tenant
        self.script_url = f"{self.tenant.get('url')}/scripts/customer.fcgi?action=safeParse" \
                          f"&includeId={self.tenant.get('include_id')}" \
                          f"&key={self.tenant.get('key')}"

        # Key = Version of fetcher script in SuperOffice. Informs self.fetch() which creator method to use.
        self.creator_methods: dict[int, callable] = {
            1: self.creator_v1,
            2: self.creator_v2
        }

    # Gets json from SuperOffice
    def get_json_from_superoffice(self) -> None:
        try:
            response = requests.get(self.script_url)
        except requests.HTTPError as e:
            print(f"Could not get data from SuperOffice: {e}")
        except requests.ReadTimeout as e:
            print(f"Could not get data from SuperOffice: {e}")
        except requests.Timeout as e:
            print(f"Could not get data from SuperOffice: {e}")
        except requests.TooManyRedirects as e:
            print(f"Could not get data from SuperOffice: {e}")
        except requests.ConnectionError as e:
            print(f"Could not get data from SuperOffice: {e}")
        except requests.RequestException as e:
            print(f"Could not get data from SuperOffice: {e}")
        else:
            try:
                data = json.loads(response.text)
                print("JSON fetched!")
            except json.JSONDecodeError:
                print("Invalid json file")
            else:
                self.json = data

    # Returns version of fetcher CRMScript from returned JSON
    def determine_script_version(self) -> int:
        script_version: int = self.json.get("script_version")
        # Version 1 had no script_version key in JSON
        if not script_version:
            return 1
        return script_version

    # Used for fetcher script version 1
    def creator_v1(self):
        temp_directory: str = f"{self.tenant.get('local_directory')}/temp"
        scripts_directory: str = f"{self.tenant.get('local_directory')}/Scripts"
        triggers_directory: str = f"{self.tenant.get('local_directory')}/Triggers"

        print("Trying to delete temp folder in case it was not deleted on previous fetch")
        delete_folder(temp_directory)

        print("Creating temp folder and moving existing folders and scripts to folder")
        create_folder(temp_directory)
        move_folder(scripts_directory, temp_directory)
        move_folder(triggers_directory, temp_directory)

        print("Creating folders and files from JSON")
        create_folder(scripts_directory)
        create_folder(triggers_directory)

        # Create a dict containing script folders and scripts since this was not a part of script version 1
        group_scripts: dict = {"script_folders": self.json["script_folders"], "scripts": self.json["scripts"]}
        create_scripts_hierarchy(scripts_directory, group_scripts)
        create_trigger_files(triggers_directory, self.json["triggers"])

        print("Deleting temp folder")
        delete_folder(temp_directory)

    # Used for fetcher script version 2
    def creator_v2(self):
        temp_directory: str = f"{self.tenant.get('local_directory')}/temp"
        scripts_directory: str = f"{self.tenant.get('local_directory')}/Scripts"
        triggers_directory: str = f"{self.tenant.get('local_directory')}/Triggers"
        screens_directory: str = f"{self.tenant.get('local_directory')}/Screens"
        screen_choosers_directory: str = f"{self.tenant.get('local_directory')}/ScreenChoosers"

        print("Trying to delete temp folder in case it was not deleted on previous fetch")
        delete_folder(temp_directory)

        print("Creating temp folder and moving existing folders and scripts to folder")
        create_folder(temp_directory)
        move_folder(scripts_directory, temp_directory)
        move_folder(triggers_directory, temp_directory)
        move_folder(screens_directory, temp_directory)
        move_folder(screen_choosers_directory, temp_directory)

        print("Creating folders and files from JSON")
        create_folder(scripts_directory)
        create_folder(triggers_directory)
        create_folder(screens_directory)
        create_folder(screen_choosers_directory)

        create_scripts_hierarchy(scripts_directory, self.json["group_scripts"])
        create_trigger_files(triggers_directory, self.json["group_triggers"]["triggers"])
        create_screens_hierarchy(screens_directory, self.json["group_screens"])
        create_screen_chooser_files(screen_choosers_directory, self.json["group_screen_choosers"]["screen_choosers"])

        print("Deleting temp folder")
        delete_folder(temp_directory)

    # Main fetch function
    # Returns true if CRMScripts were fetched and folders/files were created successfully
    # Will delete all files/folders before recreating them from the JSON again
    # A backup temp folder is created in case script fails during execution
    def fetch(self) -> bool:
        print(f"Getting JSON data from SuperOffice using endpoint: {self.script_url}")
        self.get_json_from_superoffice()
        if not self.json:
            return False

        # Call different fetch methods depending on what version fetcher script in SuperOffice is
        script_version: int = self.determine_script_version()
        creator_method: callable = None

        try:
            creator_method = self.creator_methods[script_version]
        except KeyError:
            print("Fetcher script version not supported")
            return False

        creator_method()
        return True
