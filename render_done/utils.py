# SPDX-FileCopyrightText: © 2026 Michel Anders (varkenvarken) & contributors
#
# SPDX-License-Identifier: GPL-2.0-or-later

from pathlib import Path

import bpy
from bpy.utils import previews


def get_package_name():
    return __package__.split(".")[0]


def read_password():
    """Read password from file and update global password variable.

    Reads the first line of the password file specified in addon preferences,
    stores it in the password attribute we added to the window manager,
    and sets a custom property in the window manager to indicate whether the password was successfully loaded.
    """
    password = read_first_line(
        bpy.context.preferences.addons[get_package_name()].preferences.password_file  # type: ignore (password_file is an attribute)
    )
    bpy.context.window_manager.password = password  # type: ignore (password is an attribute)
    bpy.context.window_manager.password_loaded = password is not None  # type: ignore (password_loaded is an attribute)


def read_first_line(filepath):
    """Read and return the first line from a file.

    Args:
        filepath: Path to the file to read.

    Returns:
        The first line of the file with leading/trailing whitespace stripped,
        or the empty string if the file cannot be read (e.g., missing or not readable).
    """
    try:  # can fail for several reasons: file might not exist, or is not readable, etc.
        with open(filepath, "r", encoding="utf-8") as f:
            return f.readline().strip()
    except IOError:
        return ""


# we can have several collections of previews/icons
preview_collections = {}


def load_icons():
    pcoll = previews.new()

    # path to the folder where the icon is
    # the path is calculated relative to this py file inside the addon folder
    my_icons_dir = Path(__file__).parent / "icons"

    # load all previews
    icons = [
        entry
        for entry in my_icons_dir.iterdir()   # cannot use walk method introduced in Python 3.12 because Blender 5.0 comes with 3.11.x
        if entry.is_file() and entry.name.endswith(".svg")
    ]
    for icon in icons:
        name = icon.stem
        print(f"{icon=} {name=}")
        pcoll.load(name, str(icon), "IMAGE")  # unfortunately load() doesn´t like Path objects so we have to convert to str explicitly

    preview_collections["operator_icons"] = pcoll

    for k in preview_collections:
        for ic in preview_collections[k]:
            print(f"{k} {ic} {preview_collections[k][ic]}")

    print(f"LOAD {id(preview_collections)=}")