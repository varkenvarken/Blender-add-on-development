# SPDX-FileCopyrightText: © 2016 Michel Anders (varkenvarken) & contributors
#
# SPDX-License-Identifier: GPL-2.0-or-later 

bl_info = {
    "name": "Simple Move X Operator",
    "author": "Your Name",
    "version": (0, 0, 1),
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

from bpy.utils import register_class, unregister_class

def register():
    register_class(OBJECT_OT_move_x)
    
def unregister():
    unregister_class(OBJECT_OT_move_x)
    
if __name__ == "__main__":
    register()