# SPDX-FileCopyrightText: © 2016 Michel Anders (varkenvarken) & contributors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import blf
import bpy
import gpu

from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from bpy.utils import register_class, unregister_class
from bpy.types import VIEW3D_PT_overlay_object

bl_info = {
    "name": "Distance overlay",
    "author": "Michel Anders (varkenvarken)",
    "version": (0, 0, 1),
    "blender": (5, 0, 0),
    "location": "Overlays (Object)",
    "description": "Draw distances betwee currently selected and active objects",
    "category": "Overlay",
    "doc_url": "https://github.com/varkenvarken/Blender-add-on-development",
}

uniform_shader = gpu.shader.from_builtin("UNIFORM_COLOR")


def draw_line(p0, p1, color):
    """
    Draw a line from p0 -> p0 in 3d space.
    
    :param p0: Vector
    :param p1: Vector
    :param color: Vector (4 elements, rgba)
    """
    batch = batch_for_shader(uniform_shader, "LINES", {"pos": [p0, p1]})
    uniform_shader.bind()
    uniform_shader.uniform_float("color", color)
    batch.draw(uniform_shader)


# this global variable control whether the overlays are shown or not.
# it it set by toggling the corresponding property in the current Scene
# (this is not going to work properly with multiple scenes!)
# We have a separate property because global python variables cannot be
# accessed from Blender Python directly.
show_distances = False


def draw_handler_post_view():
    """
    This handler is responsible for drawing the distance lines in the 3d view.

    It deals with view camera settings like perspective and clipping automatically.
    """
    global active
    global targets
    global show_distances

    if show_distances:
        gpu.state.line_width_set(5)  # OPTION: make this a preference too if you like
        line_color = bpy.context.preferences.addons[__name__].preferences.linecolor
        try:
            name = active.name  # will trigger a ReferenceError if removed
            if active:
                for ob in targets:
                    try:
                        if ob is not active:
                            draw_line(
                                active.location, ob.location, line_color
                            )  # the location access will trigger a ReferenceError if removed
                    except ReferenceError:
                        print("target object removed")
        except ReferenceError:
            print("active object removed")

        gpu.state.line_width_set(1)


def draw_handler_post_pixel():
    """
    This handler is responsible for drawing the distance labels as a 2d overlay.
    """
    global active
    global targets
    global show_distances

    if show_distances:
        gpu.state.blend_set("ALPHA")  # necessary for font shadows to work as intended if they are (partially) transparent

        font_id = 0  # the built-in font; always available
        if bpy.context.preferences.addons[__name__].preferences.fontshadow:
            blf.enable(font_id, blf.SHADOW)
            blf.shadow(font_id, 5, 0, 0, 0, 0.7)
            blf.shadow_offset(font_id, 2, -2)
        else:
            blf.disable(font_id, blf.SHADOW)
        fontsize = bpy.context.preferences.addons[__name__].preferences.fontsize
        fontcolor = Vector((1, 1, 1, 1))  # white

        try:
            name = active.name  # will trigger a ReferenceError if removed
            if active:
                for ob in targets:
                    try:
                        if ob is not active:
                            # we want to position the label halfway between two objects
                            coords_3d = (
                                (active.location + ob.location) / 2
                            )  # the location access will trigger a ReferenceError if removed

                            # those coordinates need to be converted from 3d to a 2d location inside the VIEW3D area
                            coords_2d = view3d_utils.location_3d_to_region_2d(
                                region=bpy.context.region,
                                rv3d=bpy.context.space_data.region_3d,
                                coord=coords_3d,
                            )
                            length = (active.location - ob.location).length
                            blf.position(0, *coords_2d, 0)  # coords_2d is two elements, so we add the missing z coordinate explicitly here
                            blf.size(font_id, fontsize)
                            blf.color(font_id, *fontcolor)  # color expects separate r,g,b,a arguments, so we unpack fontcolor
                            blf.draw(font_id, f"{length:.4f}")  # limit the label to 4 decmal digits
                    except ReferenceError:
                        print("target object removed")
        except ReferenceError:
            print("active object removed")


def redraw():
    """
    Utility function to mark all areas in all screens for redraw.

    Overkill if we only want to mark any VIEW3D area, but this keeps the logic simple,
    and it won't hurt to much because it is only called after setting or clearing objects.
    """
    for s in bpy.data.screens:
        for a in s.areas:
            a.tag_redraw()


class OBJECT_OT_distance_overlay(bpy.types.Operator):
    bl_idname = "object.distance_overlay"
    bl_label = "Distance overlay"
    bl_description = "Add or remove currently selected objects to distance draw list"
    bl_options = {"REGISTER", "UNDO"}

    remove: bpy.props.BoolProperty(name="Remove", default=False)  # type: ignore

    @classmethod
    def poll(cls, context):
        return (
            context.active_object is not None
            and len(set(context.selected_objects).union([context.active_object]))
            >= 2  # make sure to count active object only once
        )

    def execute(self, context):
        global active
        global targets
        if self.remove:
            active = None
            targets = set()
            context.scene.show_distances = False  # this will also trigger setting the global  show_distances
        else:
            active = context.active_object
            targets = set(context.selected_objects)  # might or might not contain the active object
            targets.difference_update([context.active_object])  # remove the active object from the targets if it is there
            context.scene.show_distances = True  # this will also trigger setting the global  show_distances
        redraw()
        return {"FINISHED"}


def overlay_options(self, context):
    """Add UI elements to the overlay panel"""
    self.layout.label(text="Distances")
    row = self.layout.row()
    row.prop(context.scene, "show_distances")  # see update_show_distances() below
    row.operator(
        OBJECT_OT_distance_overlay.bl_idname, text="Set objects"
    ).remove = False
    row.operator(OBJECT_OT_distance_overlay.bl_idname, text="Clear").remove = True


def update_show_distances(self, context):
    # self is the object the property belongs to that has this update function, so in our case a Scene object
    # we need this, because a plain global cannot be accessed from the Blender UI elements directly,
    # so we tie it to a BoolProperty that can.
    global show_distances
    show_distances = self.show_distances
    return None


class DistanceOverlayPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__  # important: this links these preferences with the current add-on; you still need to register the class though

    fontsize: bpy.props.IntProperty(
        name="Fontsize",
        description="Fontsize for labels",
        default=14,
        min=2,
        soft_max=150,
    )  # type: ignore
    fontshadow: bpy.props.BoolProperty(
        name="Drop shadow", description="Add a dropshadow to labels", default=True
    )  # type: ignore
    linecolor: bpy.props.FloatVectorProperty(
        name="Line color",
        size=4,
        default=(1, 0, 0, 1),  # red
        description="Color of the distance lines",
        subtype="COLOR",
    )  # type: ignore

    def draw(self, context):
        # note unlike with operators there is no default draw implementation so if you don´t add it, you see nothing
        layout = self.layout
        row = layout.row()
        row.prop(self, "linecolor")
        row = layout.row(heading="Labels")
        row.prop(self, "fontsize", text="Size")
        row.prop(self, "fontshadow", text="Shadow")

def register():
    global handler
    global label_handler
    # this is post view, i.e. a 3D overlay
    handler = bpy.types.SpaceView3D.draw_handler_add(
        draw_handler_post_view, (), "WINDOW", "POST_VIEW"
    )
    # this is post pixel, i.e. a 2D overlay
    label_handler = bpy.types.SpaceView3D.draw_handler_add(
        draw_handler_post_pixel, (), "WINDOW", "POST_PIXEL"
    )
    register_class(OBJECT_OT_distance_overlay)
    register_class(DistanceOverlayPreferences)
    VIEW3D_PT_overlay_object.append(overlay_options)
    # custom property. Needs to be added somewhere, View3DOverlay overlay type itself would seem a good a choice
    # but that doesn´t work so we add it to the Scene instead.
    bpy.types.Scene.show_distances = bpy.props.BoolProperty(
        name="Show distances", default=False, update=update_show_distances
    )


def unregister():
    global handler
    global label_handler
    global active
    global targets
    global show_distances

    if handler is not None:
        bpy.types.SpaceView3D.draw_handler_remove(handler, "WINDOW")
    if label_handler is not None:
        bpy.types.SpaceView3D.draw_handler_remove(label_handler, "WINDOW")
    VIEW3D_PT_overlay_object.remove(overlay_options)
    unregister_class(OBJECT_OT_distance_overlay)
    unregister_class(DistanceOverlayPreferences)
    # a bit of final cleanup so that when we disable and then disable the whole add-on any remembered state is immediately shown
    active = None
    targets = set()
    bpy.types.Scene.show_distances = False


if __name__ == "__main__":
    register()
