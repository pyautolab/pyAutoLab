# -*- mode: python ; coding: utf-8 -*-
from __future__ import annotations

import platform

from PyInstaller.building.api import COLLECT, EXE, PYZ
from PyInstaller.building.build_main import Analysis
from PyInstaller.building.osx import BUNDLE

import pyautolab
from pyautolab.core.plugin.plugin_helpers import load_plugins
from pyautolab.create_installer.__main__ import PROJECT_ROOT_PATH

VERSION = pyautolab.__version__
APP_NAME = pyautolab.__title__
ENTRY_POINT = str(PROJECT_ROOT_PATH / "pyautolab" / "__main__.py")


def app_patch_assets(a: Analysis) -> list:
    return (
        [a.scripts] if platform.system() == "Darwin" else [a.scripts, a.binaries, a.zipfiles, a.datas]  # type: ignore
    )


plugins = load_plugins()[0]

a = Analysis(
    [ENTRY_POINT],
    datas=[],
    hiddenimports=[plugin.module_name for plugin in plugins if not plugin.is_internal],
)


exe = EXE(
    PYZ(a.pure, a.zipped_data),  # type: ignore
    *app_patch_assets(a),
    exclude_binaries=platform.system() == "Darwin",
    name=f"{APP_NAME}-{VERSION.replace('.', '_')}",
    console=False,
)

if platform.system() == "Windows":
    coll = COLLECT(
        exe,
        *(a.binaries, a.zipfiles, a.datas),  # type: ignore
        name=APP_NAME,
        version=VERSION,
    )

app = BUNDLE(
    exe,
    *(a.binaries, a.zipfiles, a.datas),  # type: ignore
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
