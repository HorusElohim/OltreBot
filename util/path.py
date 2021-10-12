from pathlib import Path
from os import makedirs, rename
from shutil import rmtree


def mkdir(folder):
    if not isinstance(folder, Path):
        folder = Path(folder)
    if not folder.exists():
        makedirs(folder, exist_ok=True)


def get_home_path(folder: str = 'OltreBot'):
    folder = Path().home() / f'.{folder}'
    mkdir(folder)
    return folder


def get_package_path_dict(folder=get_home_path()):
    if folder is None:
        folder = get_home_path()
    elif not isinstance(folder, Path):
        folder = get_home_path(folder)

    package_path = {
        'path': {
            'home': folder,
            'param': folder / "params",
            'log': folder / "logs",
            'cache': folder / "caches"
        }
    }

    for name, path in package_path['path'].items():
        mkdir(folder=path)

    return package_path
