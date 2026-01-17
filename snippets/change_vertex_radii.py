import bpy

mesh_object = bpy.context.active_object

skin_layer = mesh_object.data.skin_vertices[0]

for v in skin_layer.data:
    v.radius[0] = 0.1
    v.radius[1] = 0.1

