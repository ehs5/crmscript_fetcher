import eel
import bridge
import os

def main():
    folder: str = f"{os.path.dirname(__file__)}/vue"
    eel.init(folder)
    eel.start("index.html", mode="default")

if __name__ == "__main__":
    main()