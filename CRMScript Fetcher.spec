# -*- mode: python ; coding: utf-8 -*-
import sys

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('vue/dist', 'vue/dist'), ('tenant_settings.json', '.'), ('crmscript_fetcher.crmscript', '.'), ('pyproject.toml', '.')],
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
    icon=['icon.icns'],
)

# One COLLECT call is required here rather than a second standalone spec file/pyinstaller
# invocation for crmfetch.exe: PyInstaller's COLLECT fully owns and rebuilds its named
# output directory on every run, so two separate COLLECTs both targeting dist/CRMScript
# Fetcher either hard-fail ("output directory is not empty") or, with --noconfirm, silently
# delete each other's output - the two exes never actually end up coexisting. Folding both
# EXEs into this one COLLECT is what makes "one output folder holds both executables" true.
collect_args = [exe, a.binaries, a.datas]

if sys.platform == 'win32':
    # Windows-only second, console-subsystem exe (crmfetch.exe) built from the same source
    # tree - see ticket 04 in .scratch/crmfetch-cli/issues/ and readme.md's build instructions.
    # CRMScript Fetcher.exe above stays GUI-subsystem (console=False): a GUI-subsystem exe run
    # with CLI args from PowerShell/cmd has no attached console and silently drops all
    # stdout/stderr, which is exactly why crmfetch needs its own console-subsystem binary.
    # macOS doesn't need this: main.py (the exe above) already dual-mode-dispatches on argv
    # within one binary, since macOS executables have no such subsystem split to work around.
    a_cli = Analysis(
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
    pyz_cli = PYZ(a_cli.pure)

    exe_cli = EXE(
        pyz_cli,
        a_cli.scripts,
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
    collect_args += [exe_cli, a_cli.binaries, a_cli.datas]

coll = COLLECT(
    *collect_args,
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
