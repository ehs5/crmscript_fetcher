from utility import create_file
from utility import create_json_file
from utility import create_folder
from utility import safe_name


def create_scripts_in_folder(directory: str, folder_id: int, all_scripts: list[dict]) -> None:
    """
    For each script, creates two files:
    1. A .crmscript file with the script body
    2. A .json file with script's metadata
    """
    for script in [s for s in all_scripts if s.get("hierarchy_id") == folder_id]:
        file_name_no_ext: str = safe_name(script.get("description"))

        # Create script body file
        create_file(directory, f"{file_name_no_ext}.crmscript", script.get("body"))

        # Create meta data file with script body omitted
        script.pop("body")
        create_json_file(directory, f"{file_name_no_ext}.json", script)


def create_scripts_hierarchy(directory: str, group_scripts: dict, lookup_parent_id: int = -1) -> None:
    """Creates folders and files of Scripts in local directory"""

    # Create scripts in root folder
    if lookup_parent_id == -1:
        create_scripts_in_folder(directory, lookup_parent_id, group_scripts["scripts"])

    # Recursively create folder structure with scripts
    folders: list[dict] = group_scripts["script_folders"]
    created_folders: list[dict] = []
    for folder in [f for f in folders if f["parent_id"] == lookup_parent_id]:
        if folder in created_folders:
            continue

        path: str = f"{directory}/{safe_name(folder['name'])}"
        create_folder(path)
        created_folders.append(folder)

        create_scripts_in_folder(path, folder["id"], group_scripts["scripts"])
        create_scripts_hierarchy(path, group_scripts, folder["id"])  # Create child folders
