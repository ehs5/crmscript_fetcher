# Functions for handling local files and folders
import os
import sys
import toml
import json
import tkinter
import shutil
import platform
import subprocess
from typing import Any
from pathlib import Path
from tkinter import filedialog
from tenacity import retry
from tenacity import wait_fixed
from tenacity import stop_after_attempt


def get_app_directory() -> Path:
    """
    Returns the correct path that crmscript fetcher resides in
    regardless of whether its run as a .exe or in a code editor, and regardless of OS
    """
    # When ran as .exe bundled by PyInstaller
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    # When running from source
    return Path(__file__).resolve().parent

def ask_directory_path() -> str:
    """
    Opens a Tkinter dialog box in front of the Eel window and returns the folder path the user selected.
    Ensures it stays on top on Windows.
    """
    root = tkinter.Tk()
    root.withdraw()                   # Hide the root window
    root.attributes('-topmost', True) # Appear on top of browser window
    folder: str = filedialog.askdirectory(parent=root)
    root.destroy()
    return folder


def get_fetcher_script() -> str:
    """
    Opens crmscript_fetcher.crmscript file and returns the contents.
    """
    file_path: Path = get_app_directory() / "crmscript_fetcher.crmscript"
    with open(file_path) as f:
        return f.read()


def open_directory(directory_path: str):
    """Opens the folder in user's OS. Handles both Windows and Linux."""
    path = Path(directory_path).resolve()
    system: str = platform.system()

    if system == "Windows":
        subprocess.Popen(f'explorer "{str(path)}"')
    elif system == "Linux":
        subprocess.Popen(["xdg-open", str(path)])

def safe_name(text: str) -> str:
    """Replace characters that are not allowed in Windows folders/files"""
    replace_chars: list[tuple[str, str]] = [
        ("/", "."),
        ('"', "'"),
        ("\\", ".."),
        (":", " - "),
        ("*", "X"),
        ("<", " Lt "),
        (">", " Gt "),
        ("|", "I"),
        ("?", "")
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


def create_file(directory: str, file_name: str, body: str) -> None:
    """Creates a file in the given directory. file_name must include file extension."""
    print(f"Creating file: {file_name}")
    full_path: str = f"{directory}/{file_name}"
    
    """ Normalize newlines """
    # TODO: What to do here? This fix caused every line to be two linebreaks, in Windows at least
    # body = body.replace("\r\n", "\n")
    # body = body.replace("\n", "\r\n")

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(body)


def create_json_file(directory: str, file_name: str, content: Any) -> None:
    """Creates a JSON file in the given directory. file_name must include file extension."""
    print(f"Creating file: {file_name}")
    full_path: str = f"{directory}/{file_name}"
    with open(full_path, "w", encoding="utf8") as f:
        json.dump(content, f, indent=4, ensure_ascii=False)


def get_current_version() -> str:
    """Returns the version of CRMScript Fetcher from pyproject.toml file."""
    pyproject_path: Path = get_app_directory() / "pyproject.toml"
    pyproject: dict = toml.load(pyproject_path)
    return pyproject["project"]["version"]