import socket
import sys
from pathlib import Path

import webview

from gui.bridge import Api


def enforce_single_instance(port: int) -> socket.socket:
    """
    Returns a socket on the given port. Exits the program if port is already in use.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("localhost", port))
        return s
    except socket.error:
        sys.exit("App is already running")


def run_gui() -> None:
    # Fix for PyInstaller subprocess fileno errors when running as a --noconsole/windowed
    # bundle: sys.stdout/stderr have no real fileno there, which some native GUI backends
    # (e.g. spawning a WebView2 loader on Windows) don't tolerate. Scoped to this function
    # (not module level) so it never touches stdout/stderr on the CLI dispatch branch in
    # root main.py - crmfetch's output has to keep reaching the calling terminal.
    if hasattr(sys, '_MEIPASS'):  # Running in a PyInstaller bundle
        log_path = Path(__file__).parent / 'webview_log.txt'
        sys.stdout = open(log_path, 'a')
        sys.stderr = open(log_path, 'a')

    vue_index_path: Path = Path(__file__).parent / "vue/dist/index.html"
    size: tuple[int, int] = (890, 790)
    lock_port = 58686  # Used to check if app is already running

    # Keep a separate dummy "lock port" running.
    # This makes sure it's not possible to open more instances of app.
    single_instance: socket.socket = enforce_single_instance(lock_port)

    print("Initializing pywebview")
    webview.create_window(
        "CRMScript Fetcher",
        url=str(vue_index_path),
        js_api=Api(),
        width=size[0],
        height=size[1],
    )
    webview.start()
