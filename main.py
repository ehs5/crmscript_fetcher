import json
import os
import shutil
import time

import requests


# CLASSES
# Used for getting Json from SuperOffice and performing the fetch itself
class SuperOfficeData:
    def __init__(self):
        self.script_url = ""
        self.data = {}

    # Gets json from SuperOffice. Make sure script_url is set through fetch() first.
    def get_json_from_superoffice(self):
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
                self.data = data

    # Main fetch function that puts CRMScripts based on JSON file retrieved from given SuperOffice tenant
    # Returns true if CRMScripts were fetched and folders/files were created successfully
    # Will delete Scripts and Trigger Folders before rebuilding them from the JSON again
    # A backup temp folder is created in case script fails during execution
    def fetch(self, tenant):
        self.script_url = f"{tenant.get('url')}/scripts/customer.fcgi?action=safeParse" \
                          f"&includeId={tenant.get('include_id')}" \
                          f"&key={tenant.get('key')}"

        temp_directory = f"{tenant.get('local_directory')}/temp"
        scripts_directory = f"{tenant.get('local_directory')}/Scripts"
        triggers_directory = f"{tenant.get('local_directory')}/Triggers"

        print(f"Getting JSON data from SuperOffice using endpoint: {self.script_url}")
        self.get_json_from_superoffice()

        if self.data:
            print("Trying to delete temp folder in case it was not deleted on previous fetch")
            delete_temp_folder(temp_directory)

            print("Creating temp folder and moving existing folders and scripts to folder")
            create_folder(temp_directory)
            move_folder_to_temp(scripts_directory, temp_directory)
            move_folder_to_temp(triggers_directory, temp_directory)

            print("Creating folders and files from JSON")
            create_folder(scripts_directory)
            create_folder(triggers_directory)
            create_script_folders(scripts_directory, self.data["script_folders"], self.data["scripts"],
                                  -1)
            create_trigger_files(triggers_directory, self.data["triggers"])

            print("Deleting temp folder")
            delete_temp_folder(temp_directory)

            return True


class TenantSettingsJson:
    def __init__(self):
        self.tenant_settings_filename = "tenant_settings.json"
        self.tenant_settings = []
        self.fetch_tenant_settings_from_json()

    # Loads the current data in the tenant settings JSON file as a list of dicts
    def fetch_tenant_settings_from_json(self):
        with open(self.tenant_settings_filename) as f:
            self.tenant_settings = json.load(f)

    def get_tenant_by_id(self, tenant_id):
        for t in self.tenant_settings:
            if t.get("id") == tenant_id:
                return t

    def get_no_of_tenants_in_json(self):
        return len(self.tenant_settings)

    # Returns the last tenant in json file
    def get_last_tenant_in_json(self):
        if len(self.tenant_settings) > 0:
            return self.tenant_settings[-1]
        else:
            return None

    # Returns True if another tenant in the tenant settings file uses the given local directory path
    def local_directory_already_used_by_tenant(self, tenant_id, local_directory):
        for t in self.tenant_settings:
            if (t.get("id") != tenant_id) and (t.get("local_directory") == local_directory):
                return True

    # Adds a new tenant to json file and returns new tenant as dict
    def add_tenant_to_json(self):
        next_id = max(t["id"] for t in self.tenant_settings) + 1
        new_tenant = {"id": next_id,
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
    def delete_tenant_from_json(self, tenant):
        for t in self.tenant_settings:
            if t == tenant:
                self.tenant_settings.remove(t)
                break

        with open(self.tenant_settings_filename, "w") as f:
            f.write(json.dumps(self.tenant_settings, indent=4))

    # Updates an existing tenant in json file by its ID
    def update_tenant_in_json(self, updated_tenant):
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


# FUNCTIONS FOR HANDLING FOLDERS AND FILES
def create_folder(path):
    try:
        os.mkdir(path)
    except OSError:
        print(f"Creation of the directory failed. Folder might already exist: {path}")
    else:
        print(f"Successfully created directory: {path}")


def move_folder_to_temp(src, dst):
    try:
        shutil.move(src, dst)
    except FileNotFoundError:
        return
    except shutil.Error:
        shutil.rmtree(dst)
        move_folder_to_temp(src, dst)


# Replace characters that are not allowed in Windows folders/files
def safe_name(text):
    return text.replace('/', '.').replace('"', "'").replace("\\", "..").replace(":", " - "). \
        replace("*", "X").replace("<", " Lt ").replace(">", " Gt ").replace("|", "I")


def create_file(directory, file_name, body):
    full_path = f"{directory}/{file_name}.crmscript"
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(body)


def create_scripts_in_folder(directory, folder_id, scripts):
    for s in scripts:
        if s.get("hierarchy_id") == folder_id:
            file_name = safe_name(s.get("description"))
            print(f"Creating file: {file_name}")
            create_file(directory, file_name, s.get("body"))


def create_script_folders(directory, folders, scripts, lookup_parent_id):
    created_folders = []
    for f in folders:
        parent_id = f.get("parent_id")
        if (f not in created_folders) and (parent_id == lookup_parent_id):
            path = f"{directory}/{safe_name(f.get('name'))}"
            create_folder(path)
            created_folders.append(f)

            folder_id = f.get("id")
            create_scripts_in_folder(path, folder_id, scripts)
            create_script_folders(path, folders, scripts, folder_id)  # Recursively creates child folders


def create_trigger_files(triggers_directory, triggers):
    for t in triggers:
        create_file(triggers_directory, safe_name(t.get("description")), t.get("body"))


def delete_temp_folder(directory):
    if os.path.isdir(directory):
        # shutil.rmtree() often throws PermissionError since os module has just accessed the folder.
        # Usually works after retrying a number of times.
        for i in range(1, 11):
            print(f"Deleting temp folder (attempt {i})")
            if i > 5:
                time.sleep(0.5)
            try:
                shutil.rmtree(directory)
            except PermissionError:
                continue
            else:
                break
