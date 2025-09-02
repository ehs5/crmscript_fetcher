import socket
from pathlib import Path
import eel
import platform
import sys

# Fix for PyInstaller + Eel subprocess fileno error when running in edge mode.
if hasattr(sys, '_MEIPASS'):  # Running in a PyInstaller bundle
    log_path = Path(__file__).parent / 'eel_log.txt'
    sys.stdout = open(log_path, 'a')
    sys.stderr = open(log_path, 'a')


# Files that contains Eel exposed functions must be imported here
import bridge

# Returns the modes to start app in, in prioritised order
def get_modes() -> list[str]:
    if platform.system() == "Windows":
        return ["edge", "chrome", "default"]
    return ["chrome", "default"]

def enforce_single_instance(port: int):
    """
    Returns a socket on the given port. Exits the program if port is already in use.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("localhost", port))
        return s
    except socket.error:
        sys.exit("App is already running")

def main():
    # Config options for eel
    vue_folder = str(Path(__file__).parent / "vue/dist")
    start_file_name = "index.html"
    modes: list[str] = get_modes()
    size = (890, 790)
    port = 8686 # If set to 0: Eel picks port automatically
    lock_port = 58686 # Used to check if app is already running

    # Keep a separate dummy "lock port" running.
    # This makes sure it's not possible to open more instances of app.
    single_instance: socket = enforce_single_instance(lock_port)

    print("Initializing Eel")
    eel.init(vue_folder)

    # Preferably app is run as a standalone Edge app,
    # but we try different modes in case that doesn't work/for other operating systems.
    for m in modes:
        try:
            print(f"Launching in {m} mode on port {port}")
            eel.start(start_file_name, mode=m, size=size, port=port)
            break
        except EnvironmentError:
            print(f"Could not launch in {m} mode, trying next")
            continue


if __name__ == "__main__":
    main()