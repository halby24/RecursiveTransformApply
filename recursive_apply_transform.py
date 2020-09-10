import bpy
from mathutils import Vector

bl_info = {
    "name": "Recursive Apply Transform",
    "author": "HALBY",
    "version": (0, 1),
    "blender": (2, 80, 0),
    "location": "3D Viewport > Sidebar",
    "description": "Apply root transform while maintaining children transforms.",
    "category": "Object"
}


class HALBY_OT_RecursiveApplyTransformButton(bpy.types.Operator):

    bl_idname = "object.recursive_apply_transform"
    bl_label = "Recursive Apply Transform"
    bl_description = "Apply root transform while maintaining children transforms."
    bl_options = {'REGISTER', 'UNDO'}

    @staticmethod
    def mul(a, b):
        return Vector((a.x * b.x, a.y * b.y, a.z * b.z))

    @staticmethod
    def div(a, b):
        return Vector((a.x / b.x, a.y / b.y, a.z / b.z))
    
    def __init__(self):
        self.meshes = []
        
    def first_transform(self, obj, target_scale):
        resize = self.div(target_scale, obj.scale)
        resize_inverse = self.div(Vector((1, 1, 1)), resize)
        obj.scale = self.mul(obj.scale, resize)

        if obj.type == "MESH" and not obj.data in self.meshes:
            self.meshes.append(obj.data)
            for v in obj.data.vertices:
                v.co = self.mul(v.co, resize_inverse)

        elif obj.type == "ARMATURE":
            for b in obj.data.bones:
                b.head = self.mul(b.head, resize_inverse)
                b.tail = self.mul(b.tail, resize_inverse)

        for child in obj.children:
            self.recursive_transform(child, resize_inverse)

    def recursive_transform(self, obj, resize_inverse):
        obj.location = self.mul(obj.location, resize_inverse)

        if obj.type == "MESH" and not obj.data in self.meshes:
            self.meshes.append(obj.data)
            for mesh in self.meshes:
                print(mesh)
            for v in obj.data.vertices:
                v.co = self.mul(v.co, resize_inverse)

        elif obj.type == "ARMATURE":
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode="EDIT")
            bones = []
            for b in obj.data.edit_bones:
                bones.append((
                    self.mul(b.head, resize_inverse),
                    self.mul(b.tail, resize_inverse)
                ))
            for i in range(len(obj.data.edit_bones)):
                obj.data.edit_bones[i].head, obj.data.edit_bones[i].tail = bones[i]
            bpy.ops.object.mode_set(mode="OBJECT")

        for child in obj.children:
            self.recursive_transform(child, resize_inverse)

    def execute(self, context):

        target_scale = Vector((
            context.scene.halby_recursive_apply_transform.transform_x_scale,
            context.scene.halby_recursive_apply_transform.transform_y_scale,
            context.scene.halby_recursive_apply_transform.transform_z_scale
        ))

        self.first_transform(context.active_object, target_scale)

        return {'FINISHED'}


class HALBY_PT_RecursiveApplyTransformUI(bpy.types.Panel):

    bl_label = "Recursive Apply Transform"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Edit"
    bl_context = "objectmode"

    @classmethod
    def poll(cls, context):
        for o in bpy.data.objects:
            if o.select_get():
                return True
        return False

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon='OUTLINER_OB_EMPTY')

    def draw(self, context):
        scn = context.scene.halby_recursive_apply_transform
        layout = self.layout

        layout.label(text="Scale")
        col = layout.column(align=True)
        col.prop(scn, "transform_x_scale")  
        col.prop(scn, "transform_y_scale")  
        col.prop(scn, "transform_z_scale")
        
        layout.separator()

        layout.operator(HALBY_OT_RecursiveApplyTransformButton.bl_idname, text="Apply")


class HALBY_PG_RecursiveApplyTransformProps(bpy.types.PropertyGroup):
    transform_x_scale: bpy.props.FloatProperty(name="X", default=1.0, min=0.0001)
    transform_y_scale: bpy.props.FloatProperty(name="Y", default=1.0, min=0.0001)
    transform_z_scale: bpy.props.FloatProperty(name="Z", default=1.0, min=0.0001)


classes = [
    HALBY_OT_RecursiveApplyTransformButton,
    HALBY_PT_RecursiveApplyTransformUI,
    HALBY_PG_RecursiveApplyTransformProps
]

def register():
    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.Scene.halby_recursive_apply_transform = bpy.props.PointerProperty(type=HALBY_PG_RecursiveApplyTransformProps)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()
