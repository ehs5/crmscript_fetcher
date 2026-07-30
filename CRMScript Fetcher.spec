# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('/Users/espen/dev/work/crmscript_fetcher/.venv/lib/python3.11/site-packages/eel/eel.js', 'eel'), ('vue/dist', 'vue/dist'), ('tenant_settings.json', '.'), ('crmscript_fetcher.crmscript', '.'), ('pyproject.toml', '.')],
    hiddenimports=['bottle_websocket'],
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
    icon=['icon.icns'],
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
app = BUNDLE(
    coll,
    name='CRMScript Fetcher.app',
    icon='icon.icns',
    bundle_identifier=None,
)
