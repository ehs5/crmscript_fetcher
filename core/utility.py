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
        return Path(sys._MEIPASS)
    # When running from source, utility.py lives one level down (core/), so
    # the app directory (where tenant_settings.json/pyproject.toml/
    # crmscript_fetcher.crmscript live) is its parent's parent.
    return Path(__file__).resolve().parent.parent

def ask_directory_path_macos() -> str:
    """
    Uses AppleScript's native folder chooser instead of Tkinter.
    Tkinter's Cocoa/NSApplication integration doesn't tear down and
    reinitialize cleanly between calls on macOS, which is what causes
    the picker to misbehave (jump around, fail to close, refuse to reopen)
    when a fresh Tk root is created and destroyed on every call.
    """
    script = 'POSIX path of (choose folder with prompt "Select a folder")'
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        # User cancelled the dialog
        return ""


def ask_directory_path_tk() -> str:
    """
    Used for Windows and Linux.
    """
    root = tkinter.Tk()
    root.withdraw()                   # Hide the root window
    root.attributes('-topmost', True) # Appear on top of browser window
    folder: str = filedialog.askdirectory(parent=root)
    root.destroy()
    return folder


def ask_directory_path() -> str:
    """
    Opens a native folder picker and returns the folder path the user selected.
    Returns an empty string if the user cancels.
    """
    if platform.system() == "Darwin":
        return ask_directory_path_macos()
    return ask_directory_path_tk()


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
    elif system == "Darwin":  # macOS
        subprocess.Popen(["open", str(path)])

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


# Off by default - a fetch creates/deletes hundreds of files, and printing
# every single one is too noisy for normal use. The CLI's --verbose flag
# (and nothing else) flips this on for the duration of a fetch.
_verbose: bool = False


def set_verbose(verbose: bool) -> None:
    """Enables or disables the create/delete folder and file logging below."""
    global _verbose
    _verbose = verbose


def log(message: str) -> None:
    """Prints message only when verbose mode is enabled via set_verbose()."""
    if _verbose:
        print(message)


def create_folder(path: str) -> None:
    try:
        os.mkdir(path)
    except OSError:
        log(f"Creation of the directory failed. Folder might already exist: {path}")
    else:
        log(f"Successfully created directory: {path}")


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

    log(f"Deleting folder: {directory}")
    shutil.rmtree(directory)


def create_file(directory: str, file_name: str, body: str) -> None:
    """Creates a file in the given directory. file_name must include file extension."""
    log(f"Creating file: {file_name}")
    full_path: str = f"{directory}/{file_name}"

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(body)


def create_json_file(directory: str, file_name: str, content: Any) -> None:
    """Creates a JSON file in the given directory. file_name must include file extension."""
    log(f"Creating file: {file_name}")
    full_path: str = f"{directory}/{file_name}"
    with open(full_path, "w", encoding="utf8") as f:
        json.dump(content, f, indent=4, ensure_ascii=False)


def get_current_version() -> str:
    """Returns the version of CRMScript Fetcher from pyproject.toml file."""
    pyproject_path: Path = get_app_directory() / "pyproject.toml"
    pyproject: dict = toml.load(pyproject_path)
    return pyproject["project"]["version"]
