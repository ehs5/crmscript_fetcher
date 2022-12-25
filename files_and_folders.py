# Functions for handling local files and folders
import os
import shutil
import time


# Replace characters that are not allowed in Windows folders/files
def safe_name(text: str) -> str:
    replace_chars = [
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


def move_folder(src: str, dst: str) -> None:
    try:
        shutil.move(src, dst)
    except FileNotFoundError:
        return
    except shutil.Error:
        shutil.rmtree(dst)
        move_folder(src, dst)


def create_file(directory: str, file_name: str, body: str) -> None:
    full_path = f"{directory}/{file_name}.crmscript"
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(body)


def create_scripts_in_folder(directory: str, folder_id: int, scripts: list[dict]) -> None:
    for s in scripts:
        if s.get("hierarchy_id") == folder_id:
            file_name = safe_name(s.get("description"))
            print(f"Creating file: {file_name}")
            create_file(directory, file_name, s.get("body"))


def create_script_folders(directory: str, folders: list[dict], scripts: list[dict], lookup_parent_id: int = -1) -> None:
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


def create_trigger_files(triggers_directory: str, triggers: list[dict]) -> None:
    for t in triggers:
        description = t.get("description")
        # Triggers might have empty names. Use ID to avoid adding only 1 file.
        if not description:
            description = f"Unnamed trigger (ID {t.get('unique_identifier')})"

        create_file(triggers_directory, safe_name(description), t.get("body"))


def delete_folder(directory: str) -> None:
    if os.path.isdir(directory):
        # shutil.rmtree() often throws PermissionError since os module has just accessed the folder.
        # Usually works after retrying a number of times.
        print(f"Deleting folder: {directory}")
        for i in range(1, 11):
            print(f"Attempt {i}")
            if i > 5:
                time.sleep(0.5)
            try:
                shutil.rmtree(directory)
            except PermissionError:
                continue
            else:
                break
