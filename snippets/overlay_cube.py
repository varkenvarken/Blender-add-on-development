# SPDX-FileCopyrightText: © 2016 Michel Anders (varkenvarken) & contributors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import gpu

from gpu_extras.batch import batch_for_shader
from mathutils import Vector

# UNIFORM_COLOR is deprecated, so use POLYLINE_UNIFORM_COLOR
uniform_shader = gpu.shader.from_builtin("POLYLINE_UNIFORM_COLOR")


def draw_line(p0, p1, color, width):
    """
    Draw a line from p0 -> p0 in 3d space.

    :param p0: Vector
    :param p1: Vector
    :param color: Vector (4 elements, rgba)
    """
    batch = batch_for_shader(uniform_shader, "LINES", {"pos": [p0, p1]})
    uniform_shader.bind()
    uniform_shader.uniform_float("color", color)
    uniform_shader.uniform_float("viewportSize", gpu.state.viewport_get()[2:])
    uniform_shader.uniform_float("lineWidth", width)
    batch.draw(uniform_shader)


def draw_handler_post_view():
    """
    This handler is responsible for drawing items in the 3d view.

    It deals with view camera settings like perspective and clipping automatically.

    It is a simple example, drawing a 2x2x2 cube centered on the origin.
    """
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
    edges = [
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 0),
        (4, 5),
        (5, 6),
        (6, 7),
        (7, 4),
        (0, 4),
        (1, 5),
        (2, 6),
        (3, 7),
    ]
    line_color = Vector((1, 0, 0, 1))  # red
    width = 5
    for v1, v2 in edges:
        draw_line(verts[v1], verts[v2], line_color, width)


def redraw():
    """
    Utility function to mark all areas in all screens for redraw.

    Overkill if we only want to mark any VIEW3D area, but this keeps the logic simple,
    and it won't hurt to much because it is only called after setting or clearing objects.
    """
    for s in bpy.data.screens:
        for a in s.areas:
            a.tag_redraw()


if __name__ == "__main__":
    handler = bpy.types.SpaceView3D.draw_handler_add(
        draw_handler_post_view, (), "WINDOW", "POST_VIEW"
    )

    redraw()

    # evil hack so we can remove the handler from the Python console
    __builtins__["handler"] = handler
    
    # in the Python console us the following line to remove the handler:
    # bpy.types.SpaceView3D.draw_handler_remove(__builtins__.handler, "WINDOW")