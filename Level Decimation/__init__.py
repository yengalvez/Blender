"""Level Decimation addon for Blender."""

bl_info = {
    "name": "Level Decimation",
    "author": "Yen Gálvez",
    "version": (2025, 1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Level Decimation",
    "description": "Control scene decimation ratios based on object size groups.",
    "category": "Object",
}

import bpy
from bpy.props import FloatProperty, PointerProperty, BoolProperty
from bpy.types import Panel, PropertyGroup, Operator

SIZE_GROUPS = [
    ("≤ 2%", 0.0, 2.0, 0.10),
    ("2% - 10%", 2.0, 10.0, 0.20),
    ("10% - 20%", 10.0, 20.0, 0.30),
    ("20% - 30%", 20.0, 30.0, 0.40),
    ("30% - 40%", 30.0, 40.0, 0.50),
    ("40% - 50%", 40.0, 50.0, 0.60),
    ("50% - 70%", 50.0, 70.0, 0.80),
    ("> 70%", 70.0, float("inf"), 1.00),
]


def iter_target_objects(scene):
    for obj in scene.objects:
        if obj.type == 'MESH' and obj.data is not None and obj.dimensions.length > 0:
            yield obj


def compute_max_size(scene):
    sizes = [obj.dimensions[0] for obj in iter_target_objects(scene) if obj.dimensions[0] > 0]
    return max(sizes) if sizes else 0.0


def size_percent(obj, max_size):
    if max_size <= 0.0:
        return 0.0
    return (obj.dimensions[0] / max_size) * 100.0


def group_index_for_percent(percent):
    for idx, (_, start, end, _) in enumerate(SIZE_GROUPS):
        if start == 0.0 and percent <= end:
            return idx
        if start != 0.0 and start < percent <= end:
            return idx
    return len(SIZE_GROUPS) - 1


def find_or_create_decimate(obj):
    decimate = next((mod for mod in obj.modifiers if mod.type == 'DECIMATE'), None)
    if decimate is None:
        decimate = obj.modifiers.new(name="LevelDecimation", type='DECIMATE')
    decimate.show_viewport = True
    decimate.show_render = True
    return decimate


def apply_decimation(scene, props):
    max_size = compute_max_size(scene)
    if max_size <= 0.0:
        return

    ratios = props.ratios
    for obj in iter_target_objects(scene):
        percent = size_percent(obj, max_size)
        idx = group_index_for_percent(percent)
        ratio = ratios[idx]
        decimate = find_or_create_decimate(obj)
        decimate.ratio = ratio


def compute_group_statistics(context, scene):
    max_size = compute_max_size(scene)
    totals = [0] * len(SIZE_GROUPS)
    if max_size <= 0.0:
        return totals

    depsgraph = context.evaluated_depsgraph_get()
    for obj in iter_target_objects(scene):
        percent = size_percent(obj, max_size)
        idx = group_index_for_percent(percent)
        obj_eval = obj.evaluated_get(depsgraph)
        try:
            mesh = obj_eval.to_mesh(preserve_all_data_layers=False, depsgraph=depsgraph)
        except RuntimeError:
            continue
        if mesh is None:
            continue
        totals[idx] += len(mesh.polygons)
        obj_eval.to_mesh_clear()
    return totals


def update_auto_update(self, context):
    if self.auto_update and context.scene is not None:
        apply_decimation(context.scene, self)


class LevelDecimationProperties(PropertyGroup):
    auto_update: BoolProperty(
        name="Auto Update",
        description="Automatically apply decimation changes when sliders are adjusted",
        default=True,
        update=update_auto_update,
    )

    def get_ratio(self, index):
        return getattr(self, f"ratio_{index}")

    @property
    def ratios(self):
        return [self.get_ratio(i) for i in range(len(SIZE_GROUPS))]


def update_ratios(self, context):
    if self.auto_update and context.scene is not None:
        apply_decimation(context.scene, self)


for idx in range(len(SIZE_GROUPS)):
    prop_name = f"ratio_{idx}"
    setattr(LevelDecimationProperties, prop_name,
            FloatProperty(name=SIZE_GROUPS[idx][0], min=0.0, max=1.0,
                          default=SIZE_GROUPS[idx][3], update=update_ratios))


class LEVELDECIMATION_OT_apply(Operator):
    bl_idname = "level_decimation.apply"
    bl_label = "Apply Decimation"
    bl_description = "Apply decimation ratios to all mesh objects"

    def execute(self, context):
        scene = context.scene
        props = scene.level_decimation_props
        apply_decimation(scene, props)
        self.report({'INFO'}, "Level Decimation applied")
        return {'FINISHED'}


class LEVELDECIMATION_PT_panel(Panel):
    bl_label = "Level Decimation"
    bl_idname = "LEVELDECIMATION_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Level Decimation"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.level_decimation_props

        layout.prop(props, "auto_update")
        layout.operator(LEVELDECIMATION_OT_apply.bl_idname, icon='MOD_DECIM')

        totals = compute_group_statistics(context, scene)
        layout.label(text=f"Total Polygons: {sum(totals):,}")
        for idx, (label, _, _, _) in enumerate(SIZE_GROUPS):
            box = layout.box()
            box.prop(props, f"ratio_{idx}", slider=True)
            box.label(text=f"{label} | Polygons: {totals[idx]:,}")


classes = (
    LevelDecimationProperties,
    LEVELDECIMATION_OT_apply,
    LEVELDECIMATION_PT_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.level_decimation_props = PointerProperty(type=LevelDecimationProperties)

    def _initial_apply():
        if not bpy.context.window_manager.windows:
            return 1.0
        for window in bpy.context.window_manager.windows:
            scene = window.scene
            if scene is None:
                continue
            props = scene.level_decimation_props
            apply_decimation(scene, props)
        return None

    bpy.app.timers.register(_initial_apply, first_interval=0.1)


def unregister():
    if hasattr(bpy.types.Scene, 'level_decimation_props'):
        del bpy.types.Scene.level_decimation_props
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
