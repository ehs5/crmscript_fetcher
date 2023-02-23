from utility import create_file
from utility import create_json_file
from utility import create_folder
from utility import safe_name


def create_screen_elements(screen_id: int, screen_path: str, screen_def_element: list[dict], item_config: list[dict]):
    """Creates a screen elements json file including item_config data"""
    screen_elements: list[dict] = [se for se in screen_def_element if se.get("screen_definition") == screen_id]

    # Add list of all item configs for each element
    for element in screen_elements:
        element["item_config"]: list[dict] = [ic for ic in item_config if ic.get("item_id") == element.get("id")]

    create_json_file(screen_path, "screen_definition_element.json", screen_elements)


def create_screen_folders(directory: str, folder_id: int, group_screens: dict) -> None:
    """For each screen, creates a folder containing .crmscript and .json files"""
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
        create_json_file(screen_path, "screen_definition.json", screen_to_json)

        create_screen_elements(screen_id, screen_path, screen_def_element, item_config)

        screen_hidden: list[dict] = [sh for sh in screen_def_hidden if sh.get("screen_definition") == screen_id]
        create_json_file(screen_path, "screen_definition_hidden.json", screen_hidden)

        screen_language: list[dict] = [sl for sl in screen_def_language if sl.get("screen_definition") == screen_id]
        create_json_file(screen_path, "screen_definition_language.json", screen_language)


def create_screens_hierarchy(directory: str, group_screens: dict, lookup_parent_id: int = -1) -> None:
    """Creates folders and files of Screens in local directory"""

    # Create screens in root folder
    if lookup_parent_id == -1:
        create_screen_folders(directory, lookup_parent_id, group_screens)

    folders: list[dict] = group_screens["screen_folders"]
    created_folders: list[dict] = []
    for folder in [f for f in folders if f["parent_id"] == lookup_parent_id]:
        if folder in created_folders:
            continue

        path: str = f"{directory}/{safe_name(folder.get('name'))}"
        create_folder(path)
        created_folders.append(folder)

        folder_id: int = folder.get("id")
        create_screen_folders(path, folder_id, group_screens)
        create_screens_hierarchy(path, group_screens, folder_id)  # Recursively creates child folders
