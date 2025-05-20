from pathlib import Path
import eel
import platform

# Files that contains exposed functions must be imported here
import bridge

# Returns the modes to start app in, in prioritised order
def get_modes() -> list[str]:
    if platform.system() == "Windows":
        return ["chrome", "edge", "default"]
    return ["chrome", "default"]


def main():
    # Config options for eel
    vue_folder = str(Path(__file__).parent / "vue/dist")
    start_file_name = "index.html"
    modes: list[str] = get_modes()
    size = (1000, 800)
    port = 8686 # 0 = Eel picks port automatically

    eel.init(vue_folder)

    # Preferably app is run as a standalone Chrome app, but we try different modes in case Chrome isn't installed.
    # "default" launches in a normal browser tab in user's default browser
    for m in modes:
        try:
            print(f"Launching in mode: '{m}'")
            eel.start(start_file_name, mode=m, size=size, port=port)
            break
        except EnvironmentError:
            print(f"Could not launch in mode '{m}', trying next")
            continue


if __name__ == "__main__":
    main()