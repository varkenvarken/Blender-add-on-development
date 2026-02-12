# SPDX-FileCopyrightText: © 2026 Michel Anders (varkenvarken) & contributors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.utils import register_class, unregister_class

from .utils import load_icons, preview_collections, read_password
from .operators import ReadPasswordFromFile, VerifyServer
from .preferences import RENDERDONE_MT_presets, RENDERDONE_PT_presets, RenderDone_OT_AddMyPreset, RenderDonePreferences
from .handlers import load_pre_handler, render_cancel_handler, render_init_handler, render_complete_handler, render_stats_handler
from .mail import verify_smtp_connection


bl_info = {
    "name": "Mail when render is done",
    "author": "Michel Anders",
    "version": (0, 0, 2),
    "blender": (5, 0, 0),
    "location": "User preferences",
    "description": "Send a mail when rendering is done",
    "category": "Render",
}


classes = (
    RENDERDONE_PT_presets,
    RENDERDONE_MT_presets,
    RenderDone_OT_AddMyPreset,
    RenderDonePreferences,
    ReadPasswordFromFile,
    VerifyServer,
)


def register():
    load_icons()
    print(f"REGISTER {id(preview_collections)=}")
    print(f"register: {preview_collections.keys()=}")
    bpy.app.handlers.render_init.append(render_init_handler)
    bpy.app.handlers.render_complete.append(render_complete_handler)
    bpy.app.handlers.render_cancel.append(render_cancel_handler)
    bpy.app.handlers.render_stats.append(render_stats_handler)
    bpy.app.handlers.load_pre.append(load_pre_handler)
    for klass in classes:
        register_class(klass)
    bpy.types.WindowManager.password = bpy.props.StringProperty(name="Password") # type: ignore (we can define a new attribute dynamically no problem)
    bpy.types.WindowManager.password_loaded = bpy.props.BoolProperty(  # type: ignore (we can define a new attribute dynamically no problem)
        name="Password loaded", default=False
    )
    bpy.types.WindowManager.connection_status = bpy.props.StringProperty(name="Connection sattus", default="Unknown") # type: ignore (we can define a new attribute dynamically no problem)
    read_password()
    verify_smtp_connection()


def unregister():
    bpy.app.handlers.render_init.remove(render_init_handler)
    bpy.app.handlers.render_complete.remove(render_complete_handler)
    bpy.app.handlers.render_cancel.remove(render_cancel_handler)
    bpy.app.handlers.render_stats.remove(render_stats_handler)
    bpy.app.handlers.load_pre.remove(load_pre_handler)
    for klass in classes:
        unregister_class(klass)
    try:
        print(f"unregister: {preview_collections.keys()=}")
        for pcoll in preview_collections.values():
            bpy.utils.previews.remove(pcoll)
    except Exception:
        pass
