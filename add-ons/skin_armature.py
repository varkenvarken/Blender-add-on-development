bl_info = {
    "name": "Skin Armature",
    "author": "Your Name",
    "version": (0, 0, 1),
    "blender": (5, 0, 0),
    "location": "Object > Object",
    "description": "Add a fitting skinned mesh to an armature",
    "category": "Object",
}

from pprint import pp as pprint
import bpy

def stick_figure(armature):
    verts = {}
    edges = []
    heads = set()

    # make sure we are in EDIT_ARMATURE mode!
    bpy.ops.object.mode_set(mode='EDIT')

    for bone in armature.data.edit_bones:
        print(bone.head, bone.tail)
        
        # converting a Vector to a tuple will copy it and so make sure we will not keep a reference to any of them
        # see: https://docs.blender.org/api/current/info_gotchas_armatures_and_bones.html#armature-mode-switching
        # NOTE: we could opt to round each component to make sure we have proper overlap but for extruded bones this isn necessay because the overlap is perfect
        head = tuple(bone.head)
        tail = tuple(bone.tail)
        
        if head not in verts:
            vi = len(verts)
            verts[head] = vi
            # this might be an unconnected head
            heads.add(vi)
     
        if tail not in verts:
            vi = len(verts)
            verts[tail] = vi
        # any tail that ends at a head makes the head connected
        heads.discard(verts[tail])    # not .remove(), that would raise a KeyError if the index wasn't there
        
        edges.append((verts[head], verts[tail]))
        
    bpy.ops.object.mode_set(mode='OBJECT')

    pprint(verts)
    pprint(edges)
    return verts, edges, heads

from bpy_extras.object_utils import object_data_add
from bpy.types import Operator

class OBJECT_OT_skin_armature(Operator):
    bl_idname = "object.skin_armature"
    bl_label = "Skin an armature"
    bl_description = "Add a fitting skinned mesh to an armature"
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        return (
            context.mode == "OBJECT" and 
            context.active_object and 
            context.active_object.type == "ARMATURE" 
        )
    
    def execute(self, context):
        armature = bpy.context.active_object
        verts, edges, heads = stick_figure(armature)
        mesh = bpy.data.meshes.new(name="Stick figure")
        mesh.from_pydata(verts, edges, [])
        object = object_data_add(bpy.context, mesh, operator=None, name=None)

        # copy rotatation, scale and location all in one go 
        object.matrix_world = armature.matrix_world.copy()

        skin_modifier = object.modifiers.new(name="Skin", type="SKIN")
        skin_modifier.use_x_symmetry = False  # override default so we can deal with irregular forms
        skin_modifier.branch_smoothing = 1.0  # just looks nicer
        skin_modifier.use_smooth_shade = True

        # mark all unconnected heads as roots
        pprint(heads)

        # go to edit mode and deselect all vertices
        bpy.ops.object.mode_set(mode = 'EDIT') 
        bpy.ops.mesh.select_mode(type="VERT")
        bpy.ops.mesh.select_all(action = 'DESELECT')

        # counter intuitive, but go to object mode to mark individual vertices as selected
        bpy.ops.object.mode_set(mode = 'OBJECT')
        for vertex_index in heads:
            object.data.vertices[vertex_index].select = True

        # back to edit mode to mark currently selected vertices as root for the skin modifier
        # this ensures that disconnected edge nets are still skinned
        bpy.ops.object.mode_set(mode = 'EDIT') 
        bpy.ops.object.skin_root_mark()

        # and back to object mode because it is always a good idea to leave in its original state as much as possible        
        bpy.ops.object.mode_set(mode='OBJECT')


        subdivision_modifier = object.modifiers.new(name="Subdivision", type="SUBSURF")
        subdivision_modifier.levels = 2  # viewport
        subdivision_modifier.render_levels = 2  # render

        # this is not ideal, but works for many plain armatures
        #armature_modifier = object.modifiers.new(name="Armature", type="ARMATURE")
        #armature_modifier.object = armature
        #armature_modifier.use_vertex_groups = False
        #armature_modifier.use_bone_envelopes = True

        # this is much nicer (and parents the stick figure to the armature at the same time)

        armature.select_set(True)  # also select the armature
        bpy.context.view_layer.objects.active = armature  # and make it active too
        bpy.ops.object.parent_set(type="ARMATURE_AUTO")

        armature.show_in_front = True
        object.select_set(False)

        return {"FINISHED"}


from bpy.utils import register_class, unregister_class
from bpy.types import VIEW3D_MT_object


def menu_func(self, context):
    """Add the operator to the  menu."""
    self.layout.separator()
    self.layout.operator(OBJECT_OT_skin_armature.bl_idname)


def register():
    """Register the add-on classes and menu."""
    register_class(OBJECT_OT_skin_armature)
    VIEW3D_MT_object.append(menu_func)


def unregister():
    """Unregister the add-on classes and menu."""
    VIEW3D_MT_object.remove(menu_func)
    unregister_class(OBJECT_OT_skin_armature)


if __name__ == "__main__":
    register()