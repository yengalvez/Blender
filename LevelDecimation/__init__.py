"""Level Decimation addon for Blender."""

import bpy
from bpy.types import Panel, Operator, PropertyGroup
from bpy.props import (
    BoolProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
)

bl_info = {
    "name": "Level Decimation",
    "author": "Yen Gálvez",
    "version": (2025, 1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar",
    "description": (
        "Gestión interactiva de modificadores Decimate en función del tamaño de los objetos"
    ),
    "category": "Object",
}

CATEGORY_DATA = (
    {
        "id": "grp_0",
        "label": "0% - 2%",
        "min": 0.0,
        "max": 2.0,
        "default": 0.1,
    },
    {
        "id": "grp_1",
        "label": "2% - 10%",
        "min": 2.0,
        "max": 10.0,
        "default": 0.2,
    },
    {
        "id": "grp_2",
        "label": "10% - 20%",
        "min": 10.0,
        "max": 20.0,
        "default": 0.3,
    },
    {
        "id": "grp_3",
        "label": "20% - 30%",
        "min": 20.0,
        "max": 30.0,
        "default": 0.4,
    },
    {
        "id": "grp_4",
        "label": "30% - 40%",
        "min": 30.0,
        "max": 40.0,
        "default": 0.5,
    },
    {
        "id": "grp_5",
        "label": "40% - 50%",
        "min": 40.0,
        "max": 50.0,
        "default": 0.6,
    },
    {
        "id": "grp_6",
        "label": "50% - 70%",
        "min": 50.0,
        "max": 70.0,
        "default": 0.8,
    },
    {
        "id": "grp_7",
        "label": "70% - 100%",
        "min": 70.0,
        "max": 100.0,
        "default": 1.0,
    },
)


def ensure_decimate_modifier(obj: bpy.types.Object) -> bpy.types.DecimateModifier:
    """Return the first Decimate modifier or create a new one."""
    for modifier in obj.modifiers:
        if modifier.type == 'DECIMATE':
            return modifier
    modifier = obj.modifiers.new(name="Decimate", type='DECIMATE')
    modifier.show_viewport = True
    return modifier


def get_mesh_objects(scene: bpy.types.Scene) -> list[bpy.types.Object]:
    """Return mesh objects ignoring cameras and lights."""
    return [obj for obj in scene.objects if obj.type == 'MESH']


def compute_object_size(obj: bpy.types.Object) -> float:
    """Compute the size metric used for grouping objects."""
    return max(obj.dimensions) if obj.dimensions else 0.0


def find_category(percent: float) -> dict:
    """Return the category configuration for a given percent."""
    for category in CATEGORY_DATA:
        minimum = category["min"]
        maximum = category["max"]
        if percent <= maximum and (percent > minimum or minimum == 0.0):
            return category
    return CATEGORY_DATA[-1]


def update_decimate_settings(self, context):
    if context is None:
        return
    apply_decimate_settings(context)


class LevelDecimationSettings(PropertyGroup):
    initialized: BoolProperty(
        name="initialized",
        default=False,
        options={'HIDDEN'},
    )
    ratio_grp_0: FloatProperty(
        name=CATEGORY_DATA[0]["label"],
        min=0.0,
        max=1.0,
        default=CATEGORY_DATA[0]["default"],
        update=update_decimate_settings,
    )
    ratio_grp_1: FloatProperty(
        name=CATEGORY_DATA[1]["label"],
        min=0.0,
        max=1.0,
        default=CATEGORY_DATA[1]["default"],
        update=update_decimate_settings,
    )
    ratio_grp_2: FloatProperty(
        name=CATEGORY_DATA[2]["label"],
        min=0.0,
        max=1.0,
        default=CATEGORY_DATA[2]["default"],
        update=update_decimate_settings,
    )
    ratio_grp_3: FloatProperty(
        name=CATEGORY_DATA[3]["label"],
        min=0.0,
        max=1.0,
        default=CATEGORY_DATA[3]["default"],
        update=update_decimate_settings,
    )
    ratio_grp_4: FloatProperty(
        name=CATEGORY_DATA[4]["label"],
        min=0.0,
        max=1.0,
        default=CATEGORY_DATA[4]["default"],
        update=update_decimate_settings,
    )
    ratio_grp_5: FloatProperty(
        name=CATEGORY_DATA[5]["label"],
        min=0.0,
        max=1.0,
        default=CATEGORY_DATA[5]["default"],
        update=update_decimate_settings,
    )
    ratio_grp_6: FloatProperty(
        name=CATEGORY_DATA[6]["label"],
        min=0.0,
        max=1.0,
        default=CATEGORY_DATA[6]["default"],
        update=update_decimate_settings,
    )
    ratio_grp_7: FloatProperty(
        name=CATEGORY_DATA[7]["label"],
        min=0.0,
        max=1.0,
        default=CATEGORY_DATA[7]["default"],
        update=update_decimate_settings,
    )

    objects_grp_0: IntProperty(default=0, options={'HIDDEN'})
    objects_grp_1: IntProperty(default=0, options={'HIDDEN'})
    objects_grp_2: IntProperty(default=0, options={'HIDDEN'})
    objects_grp_3: IntProperty(default=0, options={'HIDDEN'})
    objects_grp_4: IntProperty(default=0, options={'HIDDEN'})
    objects_grp_5: IntProperty(default=0, options={'HIDDEN'})
    objects_grp_6: IntProperty(default=0, options={'HIDDEN'})
    objects_grp_7: IntProperty(default=0, options={'HIDDEN'})

    polygons_grp_0: IntProperty(default=0, options={'HIDDEN'})
    polygons_grp_1: IntProperty(default=0, options={'HIDDEN'})
    polygons_grp_2: IntProperty(default=0, options={'HIDDEN'})
    polygons_grp_3: IntProperty(default=0, options={'HIDDEN'})
    polygons_grp_4: IntProperty(default=0, options={'HIDDEN'})
    polygons_grp_5: IntProperty(default=0, options={'HIDDEN'})
    polygons_grp_6: IntProperty(default=0, options={'HIDDEN'})
    polygons_grp_7: IntProperty(default=0, options={'HIDDEN'})


def apply_decimate_settings(context):
    scene = context.scene
    settings = scene.level_decimation_settings
    mesh_objects = get_mesh_objects(scene)

    if not mesh_objects:
        for index, category in enumerate(CATEGORY_DATA):
            setattr(settings, f"objects_{category['id']}", 0)
            setattr(settings, f"polygons_{category['id']}", 0)
        return

    max_size = max((compute_object_size(obj) for obj in mesh_objects), default=0.0)
    if max_size <= 0.0:
        max_size = 1.0

    counters = {
        category["id"]: {"objects": 0, "polygons": 0}
        for category in CATEGORY_DATA
    }

    for obj in mesh_objects:
        size = compute_object_size(obj)
        percent = (size / max_size) * 100.0
        category = find_category(percent)
        ratio = getattr(settings, f"ratio_{category['id']}")
        modifier = ensure_decimate_modifier(obj)
        modifier.show_viewport = True
        modifier.ratio = ratio

        polygon_count = len(obj.data.polygons) if obj.data else 0
        counters[category["id"]]["objects"] += 1
        counters[category["id"]]["polygons"] += polygon_count

    for category in CATEGORY_DATA:
        group_id = category["id"]
        setattr(settings, f"objects_{group_id}", counters[group_id]["objects"])
        setattr(settings, f"polygons_{group_id}", counters[group_id]["polygons"])

    settings.initialized = True


class LEVELDECIMATION_OT_apply(Operator):
    bl_idname = "object.level_decimation_apply"
    bl_label = "Aplicar configuración"
    bl_description = "Crea o actualiza los modificadores Decimate según el tamaño de cada objeto"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        apply_decimate_settings(context)
        self.report({'INFO'}, "Decimates actualizados")
        return {'FINISHED'}


class LEVELDECIMATION_PT_panel(Panel):
    bl_idname = "LEVELDECIMATION_PT_panel"
    bl_label = "Level Decimation"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Level Decimation"

    @classmethod
    def poll(cls, context):
        return context.mode in {'OBJECT', 'EDIT_MESH'} and context.area.type == 'VIEW_3D'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.level_decimation_settings

        if not settings.initialized:
            layout.label(text="Aplica la configuración inicial")
        layout.operator('object.level_decimation_apply', icon='MOD_DECIM')

        box = layout.box()
        box.label(text="Control de ratios")

        for category in CATEGORY_DATA:
            group_id = category["id"]
            ratio_attr = f"ratio_{group_id}"
            obj_attr = f"objects_{group_id}"
            poly_attr = f"polygons_{group_id}"

            row = box.row(align=True)
            row.prop(settings, ratio_attr, text=category["label"], slider=True)
            stats = row.column(align=True)
            stats.enabled = False
            stats.label(text=f"Objs: {getattr(settings, obj_attr)}")
            stats.label(text=f"Polys: {getattr(settings, poly_attr):,}")

        layout.separator()
        layout.label(text="Los cambios se aplican automáticamente a la escena")


classes = (
    LevelDecimationSettings,
    LEVELDECIMATION_OT_apply,
    LEVELDECIMATION_PT_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.level_decimation_settings = PointerProperty(type=LevelDecimationSettings)


def unregister():
    del bpy.types.Scene.level_decimation_settings
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
