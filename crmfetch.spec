# -*- mode: python ; coding: utf-8 -*-
# Windows-only console-subsystem build: produces crmfetch.exe with console=True,
# built into the same dist/CRMScript Fetcher folder as CRMScript Fetcher.exe
# (from "CRMScript Fetcher.spec") so a release zip ships both side by side.
# CRMScript Fetcher.exe stays GUI-subsystem (console=False) and unchanged -
# a GUI-subsystem exe run with CLI args from PowerShell/cmd has no attached
# console and silently drops all stdout/stderr, which is exactly why crmfetch
# needs its own console-subsystem binary. See ticket 04 in
# .scratch/crmfetch-cli/issues/ and readme.md's build instructions.
#
# macOS doesn't need this: its single "CRMScript Fetcher.spec" binary is
# already dual-mode (main.py dispatches on argv), because macOS executables
# have no GUI/console subsystem split to work around.

a = Analysis(
    ['cli.py'],
    pathex=[],
    binaries=[],
    datas=[('pyproject.toml', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='crmfetch',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CRMScript Fetcher',
)
