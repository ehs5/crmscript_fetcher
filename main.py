from pathlib import Path
import eel
import platform

# Files that contains exposed functions must be imported here
import bridge

# Returns the modes in prioritised order depending on OS
def get_modes() -> list[str]:
    if platform.system() == "Windows":
        return ["chrome", "edge", "default"]
    return ["chrome", "default"]


def main():
    # Define config options for eel.start()
    folder = str(Path(__file__).parent / "vue")
    start_file_name = "index.html"
    modes: list[str] = get_modes()
    size = (1000, 800)
    port = 0 # Eel picks port automatically

    eel.init(folder)

    # Try different modes in case Chrome isn't installed
    # "chrome" and "edge" launches in standalone browser window which is preferable.
    # "default" launches in a browser tab in user's default browser
    for m in modes:
        try:
            eel.start(start_file_name, mode=m, size=size, port=port)
            print(f"Launched in mode: '{m}'")
            break
        except EnvironmentError:
            print(f"Could not launch in mode '{m}', trying next")
            continue


if __name__ == "__main__":
    main()