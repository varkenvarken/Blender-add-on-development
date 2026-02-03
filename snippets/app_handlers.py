# SPDX-FileCopyrightText: © 2026 Michel Anders (varkenvarken) & contributors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.app.handlers import persistent

# a whole collection of app handlers
# they all just print their arguments to the console, just to see when they are triggered


@persistent  # the persistent decorator will ensure the handler stays active even if a new file is loaded
def load_pre_handler(file: str):
    # gets called before loading a file
    print(f"load_pre_handler {file=}")


@persistent
def render_init_handler(scene: bpy.types.Scene):
    # gets called before a render job
    print(f"render_init_handler {scene.name=}")


@persistent
def render_complete_handler(scene: bpy.types.Scene):
    # gets called after a render job was completed
    print(f"render_complete_handler {scene.name=}")


@persistent
def render_cancel_handler(scene: bpy.types.Scene):
    # gets called after a render job was canceled
    print(f"render_cancel_handler {scene.name=}")


@persistent
def render_stats_handler(stats: str):
    # gets called after every frame, but only when rendering an animation
    print(f"render_cancel_handler {stats=}")


def register():
    bpy.app.handlers.render_init.append(render_init_handler)
    bpy.app.handlers.render_complete.append(render_complete_handler)
    bpy.app.handlers.render_stats.append(render_stats_handler)
    bpy.app.handlers.load_pre.append(load_pre_handler)


if __name__ == "__main__":
    register()
