bl_info = {
    "name": "Simple Move X Operator",
    "author": "Your Name",
    "version": (0, 0, 3),
    "blender": (5, 0, 0),
    "location": "Object > Move X",
    "description": "Move the active object along the X axis",
    "category": "Object",
}

from bpy.types import Operator


class OBJECT_OT_move_x(Operator):
    bl_idname = "object.move_x"
    bl_label = "Move X"
    bl_options = {"REGISTER", "UNDO"}


    def execute(self, context):
        """Move the active object by 1 unit along the x-axis"""
        context.active_object.location.x += 1
        return {"FINISHED"}

    @classmethod
    def poll(cls, context):
        """Ensure we have an active object and that we are in object mode"""
        return context.active_object is not None and context.mode == "OBJECT"


from bpy.utils import register_class, unregister_class
from bpy.types import VIEW3D_MT_object


def menu_func(self, context):
    self.layout.operator(OBJECT_OT_move_x.bl_idname)


def register():
    register_class(OBJECT_OT_move_x)
    VIEW3D_MT_object.append(menu_func)


def unregister():
    VIEW3D_MT_object.remove(menu_func)
    unregister_class(OBJECT_OT_move_x)


if __name__ == "__main__":
    register()
