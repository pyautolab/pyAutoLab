import inspect
import logging
import platform
import shutil
import subprocess
import tarfile
from pathlib import Path

import PyInstaller.__main__ as PyInstaller
from PyInstaller import DEFAULT_DISTPATH

import pyautolab

PROJECT_ROOT_PATH = Path(inspect.getfile(pyautolab)).parents[1]

logging.basicConfig(level=logging.INFO)


def create_pyautolab(spec_file_path: Path, dist_path: Path) -> Path:
    PyInstaller.run(["--clean", "-y", str(spec_file_path)])
    if platform.system() == "Darwin":
        dir_app_path = dist_path / f"{pyautolab.__title__}.app"
    else:
        dir_app_path = dist_path / pyautolab.__title__

    if not dir_app_path.exists():
        raise FileNotFoundError(f"Cannot find {pyautolab.__title__} executable") from None
    if not dir_app_path.is_dir():
        raise NotADirectoryError(f"{dir_app_path} is not a directory")
    return dir_app_path


def output_tar(target_dir_path: Path, tar_file_name: str) -> None:
    tarfile_path = Path(DEFAULT_DISTPATH) / f"{tar_file_name}.tar.gz"
    if tarfile_path.exists():
        logging.info("Removing previous tar file...")
        tarfile_path.unlink()
    with tarfile.open(tarfile_path.as_posix(), "w:gz") as tar:
        tar.add(target_dir_path, target_dir_path.name)


def output_zip(target_dir_path: Path, archive_name: str) -> None:
    archive_path = target_dir_path.parent / archive_name
    if archive_path.exists():
        logging.info("Removing previous zip file...")
        archive_path.unlink()
    shutil.make_archive(archive_path.as_posix(), "zip", target_dir_path.parent, target_dir_path.name)


def create_dmg(target_dir_path: Path, dmg_file_name: str, license_path: Path) -> None:
    dmg_path = Path(DEFAULT_DISTPATH) / f"{dmg_file_name}-installer.dmg"
    options = {
        "--volname": f"{dmg_file_name}-Installer",
        "--window-pos": (200, 120),
        "--window-size": (410, 200),
        "--icon-size": 100,
        "--icon": (target_dir_path.name, 40, 50),
        "--app-drop-link": (220, 50),
        "--format": "UDBZ",
        "--eula": license_path.relative_to(Path.cwd()),
    }

    if dmg_path.exists():
        logging.info("Removing previous installer...")
        dmg_path.unlink()

    commands = ["create-dmg"]
    for option, values in options.items():
        commands.append(str(option))
        if type(values) is not tuple:
            commands.append(str(values))
            continue
        for value in values:
            commands.append(str(value))
    commands.append(dmg_path.relative_to(Path.cwd()).as_posix())
    commands.append(target_dir_path.relative_to(Path.cwd()).as_posix())
    subprocess.run(commands)


def create_windows_installer(target_dir_path: Path, installer_name: str, license_path: Path) -> None:
    template_nsi_path = Path(__file__).parent / "template.nsi"
    exe_name = installer_name.replace(".", "_")
    nsi_text = template_nsi_path.read_text()
    nsi_text = (
        nsi_text.replace("$${app_name}", target_dir_path.name)
        .replace("$${exe_name}", exe_name)
        .replace("$${installer_path}", f"{Path(DEFAULT_DISTPATH) / installer_name}.exe")
        .replace("$${license_path}", str(license_path))
    )
    logging.info("Creating nsi file...")
    temp_nis_path = Path.cwd() / "install.nsi"
    temp_nis_path.write_text(nsi_text)
    subprocess.run(["makensis", "install.nsi"])
    temp_nis_path.unlink()


if __name__ == "__main__":
    logging.info("Creating pyAutoLab...")
    pyautolab_spec_path = PROJECT_ROOT_PATH / "pyautolab" / "create_installer" / "pyautolab.spec"
    app_path = create_pyautolab(pyautolab_spec_path, Path(DEFAULT_DISTPATH))
    license_file_path = PROJECT_ROOT_PATH / "pyautolab" / "create_installer" / "LICENSE.txt"
    output_file_name = f"{pyautolab.__title__}-{pyautolab.__version__}"

    logging.info("Archiving the application folder...")
    if platform.system() == "Darwin":
        output_tar(app_path, output_file_name)
    elif platform.system() == "Windows":
        output_zip(app_path, output_file_name)

    logging.info("Creating installer...")
    if platform.system() == "Darwin":
        create_dmg(app_path, output_file_name, license_file_path)
    elif platform.system() == "Windows":
        create_windows_installer(app_path, output_file_name, license_file_path)

    logging.info(f"Removing the {pyautolab.__title__} application folder...")
    shutil.rmtree(app_path)
    logging.info("Build finished successfully!")
