# SPDX-FileCopyrightText: © 2016 Michel Anders (varkenvarken) & contributors
#
# SPDX-License-Identifier: GPL-2.0-or-later 

bl_info = {
    "name": "Star",
    "author": "Your Name",
    "version": (0, 0, 2),
    "blender": (5, 0, 0),
    "location": "Object > Add",
    "description": "Add a star shaped mesh to the scene",
    "category": "Object",
}

from math import pi, sin, cos
import bpy
from bpy.types import Operator
from bpy.props import IntProperty, FloatProperty
from bpy_extras.object_utils import object_data_add

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
        min=0.0,
        update=update_outer_radius,
    )

    outer_radius: FloatProperty(
        name="Outer radius",
        description="Distance from center to point tips",
        default=1.5,
        min=0.0,
        update=update_inner_radius,
    )

    def star_geometry(self):
        """Calculate and return vertices, edges, and faces for the star mesh."""
        vertices = []
        angle = 2 * pi / self.points  # angle between two tips, in radians
        for p in range(self.points):
            vertices.append(  # tip vertex
                (
                    self.outer_radius * -sin(p * angle),
                    self.outer_radius * cos(p * angle),
                    0.0,
                )
            )
            vertices.append(  # intermediate vertex
                (
                    self.inner_radius * -sin(p * angle + angle / 2),
                    self.inner_radius * cos(p * angle + angle / 2),
                    0.0,
                )
            )
        number_of_vertices = len(vertices)

        # edges connecting each vertex to the next one; the modulo assures we wrap around at the end
        edges = [(p, (p + 1) % number_of_vertices) for p in range(number_of_vertices)]

        # a verts form a single face (an NGON)
        faces = [list(range(number_of_vertices))]

        return vertices, edges, faces

    def execute(self, context):
        """Create a star mesh from calculated geometry."""
        vertices, edges, faces = self.star_geometry()
        mesh = bpy.data.meshes.new(name="Star")
        mesh.from_pydata(vertices, edges, faces)
        object_data_add(context, mesh, operator=None, name=None)
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
    """Add the star operator to the Object menu."""
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
