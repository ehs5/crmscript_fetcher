# Functions for handling local files and folders
import json
import os
import shutil
from tenacity import retry
from tenacity import wait_fixed
from tenacity import stop_after_attempt


# Replace characters that are not allowed in Windows folders/files
def safe_name(text: str) -> str:
    replace_chars: list[tuple[str, str]] = [
        ("/", "."),
        ('"', "'"),
        ("\\", ".."),
        (":", " - "),
        ("*", "X"),
        ("<", " Lt "),
        (">", " Gt "),
        ("|", "I")
    ]
    for chars in replace_chars:
        text = text.replace(chars[0], chars[1])

    return text


def create_folder(path: str) -> None:
    try:
        os.mkdir(path)
    except OSError:
        print(f"Creation of the directory failed. Folder might already exist: {path}")
    else:
        print(f"Successfully created directory: {path}")


# Sometimes throws PermissionError if os module has recently accessed the folder.
# Usually works after retrying a number of times.
@retry(wait=wait_fixed(1), stop=stop_after_attempt(10))
def move_folder(src: str, dst: str) -> None:
    try:
        shutil.move(src, dst)
    except FileNotFoundError:
        return
    except shutil.Error:
        shutil.rmtree(dst)
        move_folder(src, dst)


# shutil.rmtree() often throws PermissionError since os module has just accessed the folder.
# Usually works after retrying a number of times.
@retry(wait=wait_fixed(1), stop=stop_after_attempt(10))
def delete_folder(directory: str) -> None:
    if not os.path.isdir(directory):
        return

    print(f"Deleting folder: {directory}")
    shutil.rmtree(directory)


# Creates a file in the given directory. file_name must include file extension.
def create_file(directory: str, file_name: str, body: str) -> None:
    print(f"Creating file: {file_name}")
    full_path: str = f"{directory}/{file_name}"
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(body)


def create_scripts_in_folder(directory: str, folder_id: int, all_scripts: list[dict]) -> None:
    for script in [s for s in all_scripts if s.get("hierarchy_id") == folder_id]:
        file_name: str = f"{script.get('description')}.crmscript"
        create_file(directory, safe_name(file_name), script.get("body"))


# Creates folders and files of Scripts in local directory
def create_scripts_hierarchy(directory: str, group_scripts: dict, lookup_parent_id: int = -1) -> None:
    folders: list[dict] = group_scripts["script_folders"]
    all_scripts: list[dict] = group_scripts["scripts"]

    created_folders: list[dict] = []
    for f in folders:
        parent_id: int = f.get("parent_id")
        if (f not in created_folders) and (parent_id == lookup_parent_id):
            path: str = f"{directory}/{safe_name(f.get('name'))}"
            create_folder(path)
            created_folders.append(f)

            folder_id: int = f.get("id")
            create_scripts_in_folder(path, folder_id, all_scripts)
            create_scripts_hierarchy(path, group_scripts, folder_id)  # Recursively creates child folders


# Creates a screen elements json file including item_config data
def create_screen_elements(screen_id: int, screen_path: str, screen_def_element: list[dict], item_config: list[dict]):
    screen_elements: list[dict] = [se for se in screen_def_element if se.get("screen_definition") == screen_id]

    # Add list of all item configs for each element
    for element in screen_elements:
        element["item_config"]: list[dict] = [ic for ic in item_config if ic.get("item_id") == element.get("id")]

    create_file(screen_path, "screen_definition_element.json", json.dumps(screen_elements, indent=4))


# For each screen, creates a folder containing .crmscript and .json files
def create_screen_folders(directory: str, folder_id: int, group_screens: dict) -> None:
    screen_defs: list[dict] = group_screens["screen_definition"]
    screen_actions: list[dict] = group_screens["screen_definition_action"]
    screen_def_element: list[dict] = group_screens["screen_definition_element"]
    item_config: list[dict] = group_screens["item_config"]
    screen_def_hidden: list[dict] = group_screens["screen_definition_hidden"]
    screen_def_language: list[dict] = group_screens["screen_definition_language"]

    for screen in [sd for sd in screen_defs if sd.get("hierarchy_id") == folder_id]:
        folder_name: str = safe_name(f"(Screen) {screen.get('name')}")
        screen_path: str = f"{directory}/{folder_name}"
        print(f"Creating folder: {folder_name}")
        create_folder(screen_path)

        # Create one .crmscript file for each of the loading scripts
        create_file(screen_path,
                    "Creation script.crmscript",
                    f'{screen.get("creation_script")}')

        create_file(screen_path,
                    "Loading script (before setFromCgi).crmscript",
                    f'{screen.get("load_script_body")}')

        create_file(screen_path,
                    "Loading script (after setFromCgi).crmscript",
                    f'{screen.get("load_post_cgi_script_body")}')

        create_file(screen_path,
                    "Load script (run after everything else).crmscript",
                    f'{screen.get("load_final_script_body")}')

        # Create "Buttons" folder with button .crmscript files within
        buttons_folder_path: str = f"{screen_path}/Buttons"
        create_folder(buttons_folder_path)

        screen_id: int = screen.get("id")
        for button in [sa for sa in screen_actions if sa.get("screen_definition") == screen_id]:
            create_file(buttons_folder_path,
                        safe_name(f'{button.get("button")}.crmscript'),
                        button.get("ejscript_body"))

        # Create screen_definition tables as separate .json files
        # Exclude crmscript bodies in screen_definition since these have already been created as separate files
        screen_to_json: dict = screen.copy()
        screen_to_json.pop("load_script_body")
        screen_to_json.pop("load_post_cgi_script_body")
        screen_to_json.pop("load_final_script_body")
        screen_to_json.pop("creation_script")
        create_file(screen_path, "screen_definition.json", json.dumps(screen_to_json, indent=4))

        create_screen_elements(screen_id, screen_path, screen_def_element, item_config)

        screen_hidden: list[dict] = [sh for sh in screen_def_hidden if sh.get("screen_definition") == screen_id]
        create_file(screen_path, "screen_definition_hidden.json", json.dumps(screen_hidden, indent=4))

        screen_language: list[dict] = [sl for sl in screen_def_language if sl.get("screen_definition") == screen_id]
        create_file(screen_path, "screen_definition_language.json", json.dumps(screen_language, indent=4))


# Creates folders and files of Screens in local directory
def create_screens_hierarchy(directory: str, group_screens: dict, lookup_parent_id: int = -1) -> None:
    folders: list[dict] = group_screens["screen_folders"]
    created_folders: list[dict] = []
    for f in folders:
        parent_id: int = f.get("parent_id")
        if (f not in created_folders) and (parent_id == lookup_parent_id):
            path: str = f"{directory}/{safe_name(f.get('name'))}"
            create_folder(path)
            created_folders.append(f)

            folder_id: int = f.get("id")
            create_screen_folders(path, folder_id, group_screens)
            create_screens_hierarchy(path, group_screens, folder_id)  # Recursively creates child folders


# Creates .crmscript files of Triggers in local directory
def create_trigger_files(triggers_directory: str, triggers: list[dict]) -> None:
    for t in triggers:
        description: str = t.get("description")
        # Triggers might have empty names. Use ID instead.
        if not description:
            description = f"Unnamed trigger (ID {t.get('unique_identifier')})"

        create_file(triggers_directory, f'{safe_name(description)}.crmscript', t.get("body"))


# Creates .crmscript files of ScreenChoosers in local directory
def create_screen_chooser_files(screen_choosers_directory: str, screen_choosers: list[dict]) -> None:
    for sc in screen_choosers:
        description: str = sc.get("description")
        # ScreenChoosers might have empty names. Use ID instead.
        if not description:
            description = f"Unnamed ScreenChooser (ID {sc.get('unique_identifier')})"

        create_file(screen_choosers_directory, f'{safe_name(description)}.crmscript', sc.get("body"))


# Creates JSON files of scheduled tasks in local directory
def create_scheduled_tasks_files(directory: str, group_scheduled_tasks: dict):
    scheduled_tasks: list[dict] = group_scheduled_tasks["scheduled_task"]
    schedules: list[dict] = group_scheduled_tasks["schedule"]

    # Create a JSON of each "scheduled_task" entry also containing corresponding "schedule" entry
    for task in scheduled_tasks:
        # Insert schedule entry
        task["schedule"]: dict = [s for s in schedules if s.get("id") == task.get("schedule_id")][0]

        # Create JSON File
        schedule_name: str = task["schedule"]["name"]
        file_name: str = f"{safe_name(schedule_name)}.json"
        create_file(directory, file_name, json.dumps(task, indent=4))
