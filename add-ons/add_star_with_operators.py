# SPDX-FileCopyrightText: © 2016 Michel Anders (varkenvarken) & contributors
#
# SPDX-License-Identifier: GPL-2.0-or-later 

bl_info = {
    "name": "Star",
    "author": "Your Name",
    "version": (0, 0, 3),
    "blender": (5, 0, 0),
    "location": "Object > Add",
    "description": "Add a star shaped mesh to the scene",
    "category": "Object",
}

import bpy
from bpy.types import Operator
from bpy.props import IntProperty, FloatProperty

# help function to check that that the outer radius is
# always larger than the inner radius.
# Note that the comparisons are strict, i.e. do NOT
# check for equality to prevent infinite recursion!


def update_outer_radius(self, context):
    """make sure outer radius > inner radius"""
    if self.inner_radius > self.outer_radius:
        self.outer_radius = self.inner_radius


def update_inner_radius(self, context):
    """make sure inner radius <= outer radius"""
    if self.outer_radius < self.inner_radius:
        self.inner_radius = self.outer_radius


class OBJECT_OT_add_star(Operator):
    bl_idname = "object.add_star"
    bl_label = "Add star"
    bl_description = "Add a star shaped mesh to the scene"
    bl_options = {"REGISTER", "UNDO"}

    points: IntProperty(
        name="Points",
        description="Number of points on the star",
        default=5,
        min=3,
        soft_max=20,
    )

    inner_radius: FloatProperty(
        name="Inner radius",
        description="Distance from center to indented vertices",
        default=1.0,
        min=0.001,
        update=update_outer_radius,
    )

    outer_radius: FloatProperty(
        name="Outer radius",
        description="Distance from center to point tips",
        default=1.5,
        min=0.0001,
        update=update_inner_radius,
    )

    def set_vertex_selection_mode(self):
        """Save current selection mode and switch to vertex selection mode."""
        self.old_selection_modes = [
            mode for mode in bpy.context.scene.tool_settings.mesh_select_mode
        ]
        bpy.context.scene.tool_settings.mesh_select_mode[0] = True
        bpy.context.scene.tool_settings.mesh_select_mode[1] = False
        bpy.context.scene.tool_settings.mesh_select_mode[2] = False

    def restore_selection_mode(self):
        """Restore the previously saved selection mode."""
        for i, mode in enumerate(self.old_selection_modes):
            bpy.context.scene.tool_settings.mesh_select_mode[i] = mode

    def execute(self, context):
        """Create a star mesh with the specified properties."""
        bpy.ops.mesh.primitive_circle_add(
            vertices=self.points * 2,
            radius=self.inner_radius,
            fill_type="NGON",
            calc_uvs=True,  # this always gives us a circle even if we move verts afterwards
            enter_editmode=True,
        )

        # select all vertices, deselect every other one and then scale
        self.set_vertex_selection_mode()
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.select_nth(offset=1)  # also known as "checker deselect"
        R = self.outer_radius / self.inner_radius
        bpy.ops.transform.resize(value=(R, R, R))

        # select all and create a uv map.smart_project even works if the camera is not aligned
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(rotate_method="AXIS_ALIGNED_X")

        self.restore_selection_mode()
        bpy.ops.object.mode_set(mode="OBJECT")
        return {"FINISHED"}

    @classmethod
    def poll(cls, context):
        """Enable operator only in Object mode."""
        return context.mode == "OBJECT"


# Note: best practice is to put all imports at the beginning
# but we want make a clear distinction between operator
# implementation and registration.

from bpy.utils import register_class, unregister_class
from bpy.types import VIEW3D_MT_add


def menu_func(self, context):
    """Add the star operator to the Add menu."""
    self.layout.operator(OBJECT_OT_add_star.bl_idname)


def register():
    """Register the add-on classes and menu."""
    register_class(OBJECT_OT_add_star)
    VIEW3D_MT_add.append(menu_func)


def unregister():
    """Unregister the add-on classes and menu."""
    VIEW3D_MT_add.remove(menu_func)
    unregister_class(OBJECT_OT_add_star)


if __name__ == "__main__":
    register()
