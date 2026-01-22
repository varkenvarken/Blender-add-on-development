# SPDX-FileCopyrightText: © 2016 Michel Anders (varkenvarken) & contributors
#
# SPDX-License-Identifier: GPL-2.0-or-later 

from typing import Any
import typing
import bpy
from bpy_extras.object_utils import object_data_add
from bpy.types import Operator
from bpy.props import FloatProperty, BoolProperty
from bpy.utils import register_class, unregister_class
from bpy.types import VIEW3D_MT_object


bl_info = {
    "name": "Rig curve",
    "author": "Michel Anders (varkenvarken)",
    "version": (0, 0, 3),
    "blender": (5, 0, 0),
    "location": "Object > Object",
    "description": "Rig a curve with a bone for each control point",
    "category": "Object",
    "doc_url": "https://github.com/varkenvarken/Blender-add-on-development",
}


def control_points(spline: bpy.types.Spline) -> list[tuple[Any, ...]]:
    """
    Return a list of tuples with the coordinates of all control_points.

    :param spline: A single Bezier spline
    :return: A list of tuples with the coordinates of each control point
    :rtype: list[tuple[Any, ...]]

    This currently assumes (but does not check!) that the spline is a Bezier curve.
    """
    return [tuple(bp.co) for bp in spline.bezier_points]  # type: ignore (you can convert a Vector to a tuple w.o. issues)


def create_armature(
    context: Any, points: list[tuple[Any, ...]], ik: bool
) -> bpy.types.Object:
    """
    Create an armature object rigged to control points.

    :param context: The Blender context
    :param points: A list of tuples with the coordinates of each control point
    :param ik: Whether to add an inverse kinematic constraint to the last bone
    :return: The created armature object
    :rtype: bpy.types.Object

    The armature will contain a single chain of bones, one bone for
    each section of the curve, i.e. 5 points will have 4 bones.
    The head and tail positions of each bone will coincide with the points.

    The list of points should contain at least 2 items.
    """
    armature = bpy.data.armatures.new(name="Curve Rig")
    armature_object = object_data_add(bpy.context, armature, operator=None, name=None)

    # bones need to be added in edit mode and to the edit_bones attribute
    bpy.ops.object.mode_set(mode="EDIT")
    parent = None
    for a, b, index in zip(points, points[1:], range(len(points))):
        bone = armature.edit_bones.new(name=f"Bone.{index:03d}")
        bone.head = a
        bone.tail = b
        # each bone except the first point to the previous one
        if parent:
            bone.parent = parent
        parent = bone

    # if a inverse kinematic constraint is needed,
    # we need to switch to pose mode, in which case
    # the pose is available in the object.pose attribute
    # Complicated? Yes a bit, see: https://docs.blender.org/api/current/info_gotchas_armatures_and_bones.html#pose-bones
    if ik:
        bpy.ops.object.mode_set(mode="POSE")
        context.object.pose.bones[-1].constraints.new(type="IK")

    bpy.ops.object.mode_set(mode="OBJECT")

    return armature_object


def create_hooks(
    context: Any, curve: bpy.types.Object, armature: bpy.types.Object, size: float
) -> None:
    """
    Create hooks to control curve control points with armature bones.

    :param context: The Blender context
    :param curve: The curve object to rig
    :param armature: The armature object created by create_armature
    :param size: The display size of the empty hook objects
    :return: None
    :rtype: None

    For each control point of the first spline in the curve,
    a new hook to an an empty is generated and the position of this
    empty is constrained to the location of a head or tail position
    of a bone in the armature.

    The curve is assumed to contain a single Bezier spline with at least
    2 control points.
    """
    context.view_layer.objects.active = curve

    # keep type checker happy
    assert type(curve.data) is bpy.types.Curve
    assert type(armature.data) is bpy.types.Armature

    data: bpy.types.Curve = curve.data

    # loop over each control point
    for j in range(len(data.splines[0].bezier_points)):
        # make sure only that specific control point is selected
        # and never any of the handles. This is imporant, because
        # anything that is selected will be incorporated in the hook
        for i, bp in enumerate(data.splines[0].bezier_points):
            bp.select_control_point = i == j
            bp.select_left_handle = False
            bp.select_right_handle = False

        # hook can only be added in edit mode and will generate an empty
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.object.hook_add_newob()
        bpy.ops.object.mode_set(mode="OBJECT")

        # operators do not return anything useful, so we need a trick:
        # to get access to the newly added empty, we look at the last modifier
        # and retrieve the object it is pointing to
        # then we change its display type and size (just eye candy)
        empty = curve.modifiers[-1].object  # type: ignore (not all modifiers have an object attribute)
        empty.empty_display_type = "SPHERE"
        empty.empty_display_size = size

        # then we constrain the location of the empty to the corresponding bone in the armature
        constraint = empty.constraints.new(type="COPY_LOCATION")
        constraint.target = armature
        # the first empty is contrained to the head of the first bone
        if j == 0:
            constraint.subtarget = armature.data.bones[j].name
            constraint.head_tail = 0.0
        # all other empties are constrained to the tail ends
        else:
            constraint.subtarget = armature.data.bones[j - 1].name
            constraint.head_tail = 1.0


class OBJECT_OT_rig_curve(Operator):
    bl_idname = "object.rig_curve"
    bl_label = "Rig a curve"
    bl_description = "Rig a curve with a bone for each control point"
    bl_options = {"REGISTER", "UNDO"}

    size: FloatProperty(
        name="Size", description="Display size of empty hooks", default=0.1
    )  # type: ignore (needed because static type checkers are not happy with an annotation that calls a function)

    ik: BoolProperty(
        name="Add IK", description="Add inverse kinematic contraint", default=True
    )  # type: ignore (needed because static type checkers are not happy with an annotation that calls a function)

    def draw(self, context):
        """
        A custom draw function.

        Not really needed (because all properties would be shown regardless
        and we are not really changing the layout from the default), but it
        demonstrates that we can do it :-)

        :param self: Our operator
        :param context: The Blender context
        """
        layout = self.layout

        # keep the type checker happy
        assert type(layout) is bpy.types.UILayout

        # just show the properties in a single column
        # that is just like the default, but if you would
        # like something different, this is the place to do it
        col = layout.column()
        col.prop(self, "size")
        col.prop(self, "ik")

    @classmethod
    def poll(cls, context) -> bool:
        """
        Check if we are in object mode and that the active object is a
        Curve object with a single Bezier spline with at least 2 control points.

        :param cls: Our operator class
        :param context: The Blender context
        :return: True if requirements are met
        :rtype: bool
        """
        return (
            context.mode == "OBJECT"
            and context.active_object
            and context.active_object.type == "CURVE"
            and len(context.active_object.data.splines) == 1  # type: ignore
            and context.active_object.data.splines[0].type == "BEZIER"  # type: ignore
            and len(context.active_object.data.splines[0].bezier_points) >= 2  # type: ignore
        )

    def execute(
        self, context: Any
    ) -> set[  # yes this is awkward. We could have included something from bpy.stub_internal, but
        # using something labeled 'internal'is weird and only available in the fake-bpy-module
        # So here the Python type annotations break down and we have to repeat stuff just to
        # keep the type check happy :-( would be better id Blender annoted bpy itself
        typing.Literal[
            "RUNNING_MODAL",
            "CANCELLED",
            "FINISHED",
            "PASS_THROUGH",
            "INTERFACE",
        ]
    ]:
        """
        Execute the operator to rig a curve with an armature.

        :param self: Our operator
        :param context: The Blender context
        :return: A dictionary with operation status
        :rtype: set[str]
        """
        # note that the poll() method will guarantee the active object is a curve
        curve = context.active_object
        # likewise, it will have 1 spline (of type Bezier with at least 2 control points)
        spline = curve.data.splines[0]

        points = control_points(spline)
        armature = create_armature(context, points, self.ik)
        # make sure the armature is at the location of the curve
        armature.matrix_world = curve.matrix_world.copy()  # copy is needed, objects shouldn´t share!
        armature.show_in_front = True

        create_hooks(context, curve, armature, self.size)

        # for some reason, if we make the armature the active object again
        # then the properties will not be shown. Is this a bug? 
        # context.view_layer.objects.active = armature

        return {"FINISHED"}


def menu_func(self, context):
    """Add the operator to the  menu."""
    self.layout.separator()
    self.layout.operator(OBJECT_OT_rig_curve.bl_idname)


def register():
    """Register the add-on classes and menu."""
    register_class(OBJECT_OT_rig_curve)
    VIEW3D_MT_object.append(menu_func)


def unregister():
    """Unregister the add-on classes and menu."""
    VIEW3D_MT_object.remove(menu_func)
    unregister_class(OBJECT_OT_rig_curve)


if __name__ == "__main__":
    register()
