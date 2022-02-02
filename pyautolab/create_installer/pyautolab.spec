# -*- mode: python ; coding: utf-8 -*-
from __future__ import annotations

import pkgutil
import platform

from PyInstaller.building.api import COLLECT, EXE, PYZ
from PyInstaller.building.build_main import BUNDLE, Analysis

import pyautolab
from pyautolab.core.utils.plugin_helpers import FORBIDDEN_SUFFIXES, PLUGIN_PREFIX
from pyautolab.create_installer.__main__ import PROJECT_ROOT_PATH

block_cipher = None
VERSION = pyautolab.__version__
APP_NAME = pyautolab.__title__
ENTRY_POINT = str(PROJECT_ROOT_PATH / "pyautolab" / "__main__.py")


def get_plugins_modules() -> list[str]:
    plugins = []
    for _, module_name, _ in pkgutil.iter_modules():
        if not module_name.startswith(PLUGIN_PREFIX):
            continue
        if any([str(module_name).endswith(s) for s in FORBIDDEN_SUFFIXES]):
            continue
        plugins.append(module_name)
    return plugins


def app_patch_assets(a: Analysis) -> list:
    return [a.scripts] if platform.system() == "Darwin" else [a.scripts, a.binaries, a.zipfiles, a.datas]


a = Analysis(
    [ENTRY_POINT],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=get_plugins_modules(),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    *app_patch_assets(a),
    [],
    exclude_binaries=platform.system() == "Darwin",
    name=f"{APP_NAME}-{VERSION.replace('.', '_')}",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)

if platform.system() == "Windows":
    coll = COLLECT(
        exe, a.binaries, a.zipfiles, a.datas, strip=False, upx=False, upx_exclude=[], name=APP_NAME, version=VERSION
    )

app = BUNDLE(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=f"{APP_NAME}.app",
    icon=None,
    bundle_identifier=f"run.{APP_NAME}",
    version=VERSION,
    info_plist={
        "NSPrincipalClass": "NSApplication",
        "LSBackgroundOnly": False,
        "CFBundleShortVersionString": VERSION,
    },
)
