import bpy
from mathutils import Vector, Matrix, Euler, Quaternion
from math import radians

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
        
    def first_transform(self, obj, affine):
        obj.matrix_local = obj.matrix_local @ affine

        if obj.type == "MESH":
            print("poe")
            self.meshes.append(obj.data)
            for v in obj.data.vertices:
                v.co = (affine.inverted() @ v.co.to_4d()).to_3d()

        elif obj.type == "ARMATURE":
            for b in obj.data.bones:
                b.head = (affine @ b.head.to_4d()).to_3d()
                b.tail = (affine @ b.tail.to_4d()).to_3d()

        for child in obj.children:
            self.recursive_transform(child, affine)

    def recursive_transform(self, obj, affine):
        obj.location = (affine @ obj.location.to_4d()).to_3d()

        if obj.type == "MESH" and not obj.data in self.meshes:
            self.meshes.append(obj.data)
            for v in obj.data.vertices:
                v.co = (affine @ v.co.to_4d()).to_3d()

        elif obj.type == "ARMATURE":
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode="EDIT")
            bones = []
            for b in obj.data.edit_bones:
                bones.append((
                    (affine @ b.head.to_4d()).to_3d(),
                    (affine @ b.tail.to_4d()).to_3d()
                ))
            for i in range(len(obj.data.edit_bones)):
                obj.data.edit_bones[i].head, obj.data.edit_bones[i].tail = bones[i]
            bpy.ops.object.mode_set(mode="OBJECT")

        for child in obj.children:
            self.recursive_transform(child, affine)
    

    def execute(self, context):
        t = context.scene.halby_recursive_apply_transform
        o = context.active_object

        # Object Affine
        object_affine = o.matrix_local

        # Target Affine
        loc = Matrix.Translation((t.transform_x_location, t.transform_y_location, t.transform_z_location))
        rot = Euler((t.transform_x_rotation, t.transform_y_rotation, t.transform_z_rotation)).to_matrix().to_4x4()
        sca = Matrix((
            [t.transform_x_scale, 0, 0, 0],
            [0, t.transform_y_scale, 0, 0],
            [0, 0, t.transform_z_scale, 0],
            [0, 0, 0, 1]
        ))
        target_affine = rot

        self.first_transform(context.active_object, object_affine.inverted() @ target_affine)

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

        layout.label(text="Location")
        
        col = layout.column(align=True)
        col.prop(scn, "transform_x_location")  
        col.prop(scn, "transform_y_location")  
        col.prop(scn, "transform_z_location")
        
        layout.separator()

        layout.label(text="Rotation")
        
        col = layout.column(align=True)
        col.prop(scn, "transform_x_rotation")  
        col.prop(scn, "transform_y_rotation")  
        col.prop(scn, "transform_z_rotation")
        
        layout.separator()

        layout.label(text="Scale")

        col = layout.column(align=True)
        col.prop(scn, "transform_x_scale")  
        col.prop(scn, "transform_y_scale")  
        col.prop(scn, "transform_z_scale")
        
        layout.separator()

        layout.operator(HALBY_OT_RecursiveApplyTransformButton.bl_idname, text="Apply")


class HALBY_PG_RecursiveApplyTransformProps(bpy.types.PropertyGroup):
    transform_x_location: bpy.props.FloatProperty(name="X", unit="LENGTH")
    transform_y_location: bpy.props.FloatProperty(name="Y", unit="LENGTH")
    transform_z_location: bpy.props.FloatProperty(name="Z", unit="LENGTH")
    transform_x_rotation: bpy.props.FloatProperty(name="X", unit="ROTATION")
    transform_y_rotation: bpy.props.FloatProperty(name="Y", unit="ROTATION")
    transform_z_rotation: bpy.props.FloatProperty(name="Z", unit="ROTATION")
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
