# SPDX-FileCopyrightText: © 2016 Michel Anders (varkenvarken) & contributors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import gpu
import blf

from bpy_extras import view3d_utils
from mathutils import Vector

def draw_handler_post_pixel():
    verts = [
        Vector((-1, -1, -1)),
        Vector((1, -1, -1)),
        Vector((1, 1, -1)),
        Vector((-1, 1, -1)),
        Vector((-1, -1, 1)),
        Vector((1, -1, 1)),
        Vector((1, 1, 1)),
        Vector((-1, 1, 1)),
    ]

    gpu.state.blend_set("ALPHA")  # necessary for font shadows to work as intended if they are (partially) transparent

    font_id = 0  # the built-in font; always available
    blf.enable(font_id, blf.SHADOW)
    blf.shadow(font_id, 5, 0, 0, 0, 0.7)
    blf.shadow_offset(font_id, 2, -2)
    fontsize = 20
    fontcolor = Vector((1, 1, 1, 1))

    blf.size(font_id, fontsize)
    blf.color(font_id, *fontcolor)

    blf.position(0, 100, 100, 0)
    blf.draw(font_id, "Hello, world!")

    for index, coords_3d in enumerate(verts):
        coords_2d = view3d_utils.location_3d_to_region_2d(
            region=bpy.context.region,
            rv3d=bpy.context.space_data.region_3d,
            coord=coords_3d,
        )
        blf.position(0, *coords_2d, 0)
        blf.draw(font_id, f"{index}")

def redraw():
    for s in bpy.data.screens:
        for a in s.areas:
            a.tag_redraw()


if __name__ == "__main__":
    label_handler = bpy.types.SpaceView3D.draw_handler_add(
        draw_handler_post_pixel, (), "WINDOW", "POST_PIXEL"
    )

    redraw()

    # evil hack so we can remove the handler from the Python console
    __builtins__["label_handler"] = label_handler
    
    # in the Python console us the following line to remove the handler:
    # bpy.types.SpaceView3D.draw_handler_remove(__builtins__.label_handler, "WINDOW")