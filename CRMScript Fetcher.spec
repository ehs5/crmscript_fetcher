# -*- mode: python ; coding: utf-8 -*-
import sys

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    # vue/dist now lives under gui/ (ticket 06) - destination mirrors that so
    # gui/main.py's Path(__file__).parent / "vue/dist/..." still resolves
    # correctly against the frozen bundle's synthesized module path.
    datas=[('gui/vue/dist', 'gui/vue/dist'), ('tenant_settings.json', '.'), ('crmscript_fetcher.crmscript', '.'), ('pyproject.toml', '.')],
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
    name='CRMScript Fetcher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # PyInstaller's Windows icon path only accepts .ico/.exe (PyInstaller/utils/win32/icon.py
    # normalize_icon_type), not .icns. Since Pillow is installed, an un-branched icon=['icon.icns']
    # would silently succeed on Windows by auto-converting to a generated .ico instead of using
    # the hand-crafted icon.ico already in the repo - a real icon regression, not just a note.
    icon=['icon.ico'] if sys.platform == 'win32' else ['icon.icns'],
)

# This app is GUI-only on every platform - no bundled CLI binary. The CLI
# (crmfetch) is uv-install-only: `uv tool install git+https://github.com/ehs5/crmscript_fetcher.git`
# gives a real, better-integrated `crmfetch` on PATH than a bundled exe ever
# would (proper updates, same command on every OS) - see readme.md.
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CRMScript Fetcher',
)
app = BUNDLE(
    coll,
    name='CRMScript Fetcher.app',
    icon='icon.icns',
    bundle_identifier=None,
)
