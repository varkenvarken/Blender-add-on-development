# SPDX-FileCopyrightText: © 2026 Michel Anders (varkenvarken) & contributors
#
# SPDX-License-Identifier: GPL-2.0-or-later

from datetime import datetime

import bpy
from bpy.app.handlers import persistent

from .utils import read_password
from .mail import send_smtp_message


# a whole collection of app handlers
# the first one might be a bit superfluous as it tries to read the password on every .blend file being opened.
# we keep it for now.
@persistent
def load_pre_handler(file: str):
    # gets called before loading a file
    read_password()


# the next handlers are all relevant to rendering
# the render int, complete, and cancel ones will be called
# at most once for any render job (where a job can be a still render or an animation)
# but the stats handler will be called for every frame rendered.
# because we want to preserve those statuses we keep a record of them in the
# status_lines variable, and send all of them as the context of a message
# at the end of a job.
# status_lines get reset at the start of a job.
status_lines = []


@persistent
def render_init_handler(scene: bpy.types.Scene):
    # gets called before a render job
    status_lines.clear()
    status_lines.append(
        f"Render init: Scene '{scene.name}' frames {scene.frame_start} - {scene.frame_end} (step {scene.frame_step}) started at {datetime.now()}"
    )


@persistent
def render_complete_handler(scene: bpy.types.Scene):
    # gets called after a render job completed successfully
    lines = "\n".join(status_lines)
    send_smtp_message(
        f"Hello,\n\nthe render job for Scene '{scene.name}' was completed and reported the following:\n\n{lines}\n\nBye.\n",
    )


@persistent
def render_cancel_handler(scene: bpy.types.Scene):
    # gets called after a render job was canceled
    lines = "\n".join(status_lines)
    send_smtp_message(
        f"Hello,\n\nthe render job for Scene '{scene.name}' was canceled and reported the following:\n\n{lines}\n\nBye.\n",
    )


@persistent
def render_stats_handler(stats: str):
    # gets called after every frame, but only when rendering an animation
    status_lines.append(stats)
