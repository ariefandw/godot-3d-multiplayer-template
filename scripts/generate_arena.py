import math
import os
import re

def format_transform(x=0.0, y=0.0, z=0.0, rx=0.0, ry=0.0, rz=0.0):
    rad_x = math.radians(rx)
    rad_y = math.radians(ry)
    rad_z = math.radians(rz)
    
    cx, sx = math.cos(rad_x), math.sin(rad_x)
    cy, sy = math.cos(rad_y), math.sin(rad_y)
    cz, sz = math.cos(rad_z), math.sin(rad_z)
    
    if rx != 0 and ry == 0 and rz == 0:
        xx, xy, xz = 1.0, 0.0, 0.0
        yx, yy, yz = 0.0, cx, -sx
        zx, zy, zz = 0.0, sx, cx
    elif ry != 0 and rx == 0 and rz == 0:
        xx, xy, xz = cy, 0.0, sy
        yx, yy, yz = 0.0, 1.0, 0.0
        zx, zy, zz = -sy, 0.0, cy
    elif rz != 0 and rx == 0 and ry == 0:
        xx, xy, xz = cz, -sz, 0.0
        yx, yy, yz = sz, cz, 0.0
        zx, zy, zz = 0.0, 0.0, 1.0
    else:
        xx, xy, xz = 1.0, 0.0, 0.0
        yx, yy, yz = 0.0, 1.0, 0.0
        zx, zy, zz = 0.0, 0.0, 1.0
        
    return f"Transform3D({xx:.6f}, {xy:.6f}, {xz:.6f}, {yx:.6f}, {yy:.6f}, {yz:.6f}, {zx:.6f}, {zy:.6f}, {zz:.6f}, {x:.4f}, {y:.4f}, {z:.4f})"

class ArenaGenerator:
    def __init__(self):
        self.materials = {}
        self.sub_resources = []
        self.nodes = []

    def add_shader_material(self, name, albedo, grid_col, major_col, grid_size=1.0, major_step=5.0, line_th=0.02, roughness=0.8, metallic=0.0):
        mat_id = f"ShaderMaterial_{name}"
        lines = [
            f'[sub_resource type="ShaderMaterial" id="{mat_id}"]',
            'render_priority = 0',
            'shader = ExtResource("1_grid_shader")',
            f'shader_parameter/albedo_color = Color({albedo[0]}, {albedo[1]}, {albedo[2]}, 1)',
            f'shader_parameter/grid_color = Color({grid_col[0]}, {grid_col[1]}, {grid_col[2]}, 1)',
            f'shader_parameter/major_grid_color = Color({major_col[0]}, {major_col[1]}, {major_col[2]}, 1)',
            f'shader_parameter/grid_size = {grid_size:.2f}',
            f'shader_parameter/major_grid_step = {major_step:.2f}',
            f'shader_parameter/line_thickness = {line_th:.3f}',
            f'shader_parameter/roughness = {roughness:.2f}',
            f'shader_parameter/metallic = {metallic:.2f}',
        ]
        self.materials[name] = mat_id
        self.sub_resources.append("\n".join(lines))

    def add_standard_material(self, name, albedo, roughness=0.7, metallic=0.0, emission=None, emission_energy=1.0, transparency=0):
        mat_id = f"StandardMaterial3D_{name}"
        lines = [
            f'[sub_resource type="StandardMaterial3D" id="{mat_id}"]',
            f'albedo_color = Color({albedo[0]}, {albedo[1]}, {albedo[2]}, {albedo[3] if len(albedo) > 3 else 1.0})',
            f'roughness = {roughness:.2f}',
        ]
        if metallic > 0.0:
            lines.append(f'metallic = {metallic:.2f}')
        if emission:
            lines.append('emission_enabled = true')
            lines.append(f'emission = Color({emission[0]}, {emission[1]}, {emission[2]}, 1)')
            lines.append(f'emission_energy_multiplier = {emission_energy:.2f}')
        if transparency > 0:
            lines.append('transparency = 1')
            lines.append('cull_mode = 0')
        self.materials[name] = mat_id
        self.sub_resources.append("\n".join(lines))

    def add_box(self, parent_path, name, x, y, z, sx, sy, sz, mat_name, rx=0.0, ry=0.0, rz=0.0, collision=True):
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        mesh_id = f"BoxMesh_{clean_name}"
        mat_ref = f'SubResource("{self.materials[mat_name]}")'
        mesh_res = f'[sub_resource type="BoxMesh" id="{mesh_id}"]\nmaterial = {mat_ref}\nsize = Vector3({sx:.3f}, {sy:.3f}, {sz:.3f})'
        self.sub_resources.append(mesh_res)

        shape_id = None
        if collision:
            shape_id = f"BoxShape3D_{clean_name}"
            shape_res = f'[sub_resource type="BoxShape3D" id="{shape_id}"]\nsize = Vector3({sx:.3f}, {sy:.3f}, {sz:.3f})'
            self.sub_resources.append(shape_res)

        transform_str = format_transform(x, y, z, rx, ry, rz)
        node_lines = []
        if collision:
            node_lines.append(f'[node name="{name}" type="StaticBody3D" parent="{parent_path}"]')
            node_lines.append(f'transform = {transform_str}')
            node_lines.append('collision_layer = 2')
            node_lines.append('collision_mask = 0')
            node_lines.append('')
            node_lines.append(f'[node name="MeshInstance3D" type="MeshInstance3D" parent="{parent_path}/{name}"]')
            node_lines.append(f'mesh = SubResource("{mesh_id}")')
            node_lines.append('')
            node_lines.append(f'[node name="CollisionShape3D" type="CollisionShape3D" parent="{parent_path}/{name}"]')
            node_lines.append(f'shape = SubResource("{shape_id}")')
        else:
            node_lines.append(f'[node name="{name}" type="MeshInstance3D" parent="{parent_path}"]')
            node_lines.append(f'transform = {transform_str}')
            node_lines.append(f'mesh = SubResource("{mesh_id}")')
            
        self.nodes.append("\n".join(node_lines))

    def add_cylinder(self, parent_path, name, x, y, z, radius, height, mat_name, collision=True):
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        mesh_id = f"CylinderMesh_{clean_name}"
        mat_ref = f'SubResource("{self.materials[mat_name]}")'
        mesh_res = f'[sub_resource type="CylinderMesh" id="{mesh_id}"]\nmaterial = {mat_ref}\ntop_radius = {radius:.3f}\nbottom_radius = {radius:.3f}\nheight = {height:.3f}'
        self.sub_resources.append(mesh_res)

        shape_id = None
        if collision:
            shape_id = f"CylinderShape3D_{clean_name}"
            shape_res = f'[sub_resource type="CylinderShape3D" id="{shape_id}"]\nradius = {radius:.3f}\nheight = {height:.3f}'
            self.sub_resources.append(shape_res)

        transform_str = format_transform(x, y, z)
        node_lines = []
        if collision:
            node_lines.append(f'[node name="{name}" type="StaticBody3D" parent="{parent_path}"]')
            node_lines.append(f'transform = {transform_str}')
            node_lines.append('collision_layer = 2')
            node_lines.append('collision_mask = 0')
            node_lines.append('')
            node_lines.append(f'[node name="MeshInstance3D" type="MeshInstance3D" parent="{parent_path}/{name}"]')
            node_lines.append(f'mesh = SubResource("{mesh_id}")')
            node_lines.append('')
            node_lines.append(f'[node name="CollisionShape3D" type="CollisionShape3D" parent="{parent_path}/{name}"]')
            node_lines.append(f'shape = SubResource("{shape_id}")')
        else:
            node_lines.append(f'[node name="{name}" type="MeshInstance3D" parent="{parent_path}"]')
            node_lines.append(f'transform = {transform_str}')
            node_lines.append(f'mesh = SubResource("{mesh_id}")')
            
        self.nodes.append("\n".join(node_lines))

    def add_omni_light(self, parent_path, name, x, y, z, color, energy=1.0, range_val=8.0, shadow=True):
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        transform_str = format_transform(x, y, z)
        node_lines = [
            f'[node name="{clean_name}" type="OmniLight3D" parent="{parent_path}"]',
            f'transform = {transform_str}',
            f'light_color = Color({color[0]}, {color[1]}, {color[2]}, 1)',
            f'light_energy = {energy:.2f}',
            f'omni_range = {range_val:.2f}',
            f'shadow_enabled = {"true" if shadow else "false"}',
        ]
        self.nodes.append("\n".join(node_lines))

    def build(self):
        # 1. Prototype Grid Shader Materials
        self.add_shader_material("floor_grid", 
                                 albedo=(0.11, 0.13, 0.17), 
                                 grid_col=(0.19, 0.23, 0.30), 
                                 major_col=(0.30, 0.38, 0.48), 
                                 grid_size=1.0, major_step=5.0, line_th=0.02, roughness=0.85)

        self.add_shader_material("wall_grid", 
                                 albedo=(0.15, 0.17, 0.22), 
                                 grid_col=(0.23, 0.27, 0.35), 
                                 major_col=(0.33, 0.41, 0.52), 
                                 grid_size=1.0, major_step=5.0, line_th=0.02, roughness=0.8)

        self.add_shader_material("platform_grid", 
                                 albedo=(0.24, 0.28, 0.35), 
                                 grid_col=(0.34, 0.40, 0.49), 
                                 major_col=(0.48, 0.56, 0.67), 
                                 grid_size=1.0, major_step=5.0, line_th=0.025, roughness=0.7)

        self.add_shader_material("cover_light_grid", 
                                 albedo=(0.74, 0.77, 0.82), 
                                 grid_col=(0.58, 0.62, 0.68), 
                                 major_col=(0.40, 0.46, 0.54), 
                                 grid_size=1.0, major_step=2.0, line_th=0.025, roughness=0.55)

        self.add_shader_material("indoor_floor_grid",
                                 albedo=(0.08, 0.09, 0.12),
                                 grid_col=(0.14, 0.18, 0.24),
                                 major_col=(0.20, 0.30, 0.42),
                                 grid_size=1.0, major_step=4.0, line_th=0.025, roughness=0.6)

        self.add_shader_material("indoor_wall_grid",
                                 albedo=(0.12, 0.14, 0.18),
                                 grid_col=(0.20, 0.24, 0.32),
                                 major_col=(0.28, 0.36, 0.48),
                                 grid_size=1.0, major_step=3.0, line_th=0.02, roughness=0.7)

        # 2. Accent & Emissive Standard Materials
        self.add_standard_material("steel_trim", (0.28, 0.32, 0.38, 1.0), roughness=0.4, metallic=0.6)
        self.add_standard_material("caution_orange", (0.95, 0.52, 0.10, 1.0), roughness=0.45)
        self.add_standard_material("parkour_orange", (0.95, 0.40, 0.08, 1.0), roughness=0.4, emission=(0.95, 0.40, 0.08), emission_energy=1.2)
        self.add_standard_material("parkour_gold", (0.98, 0.78, 0.15, 1.0), roughness=0.35, emission=(0.98, 0.78, 0.15), emission_energy=1.6)
        self.add_standard_material("tech_cyan", (0.10, 0.80, 0.98, 1.0), roughness=0.25, emission=(0.10, 0.80, 0.98), emission_energy=2.2)
        self.add_standard_material("railing_metal", (0.50, 0.56, 0.64, 1.0), roughness=0.35, metallic=0.65)
        self.add_standard_material("beacon_core", (0.40, 0.94, 1.0, 1.0), roughness=0.1, emission=(0.40, 0.94, 1.0), emission_energy=4.0)
        self.add_standard_material("server_green", (0.20, 0.95, 0.40, 1.0), roughness=0.3, emission=(0.20, 0.95, 0.40), emission_energy=2.0)
        self.add_standard_material("server_amber", (0.98, 0.60, 0.10, 1.0), roughness=0.3, emission=(0.98, 0.60, 0.10), emission_energy=2.0)
        self.add_standard_material("reactor_core", (0.15, 0.85, 1.0, 1.0), roughness=0.1, emission=(0.15, 0.85, 1.0), emission_energy=3.0)
        self.add_standard_material("window_glass", (0.25, 0.65, 0.85, 0.35), roughness=0.1, metallic=0.2, transparency=1)

        # 3. Environment & Procedural Sky
        env_resources = """[sub_resource type="ProceduralSkyMaterial" id="ProceduralSkyMaterial_sky"]
sky_top_color = Color(0.24, 0.46, 0.75, 1)
sky_horizon_color = Color(0.68, 0.78, 0.88, 1)
ground_bottom_color = Color(0.12, 0.14, 0.18, 1)
ground_horizon_color = Color(0.55, 0.65, 0.74, 1)
sun_angle_max = 28.0

[sub_resource type="Sky" id="Sky_demo"]
sky_material = SubResource("ProceduralSkyMaterial_sky")

[sub_resource type="Environment" id="Environment_demo"]
background_mode = 2
sky = SubResource("Sky_demo")
ambient_light_source = 3
ambient_light_sky_contribution = 0.55
ambient_light_energy = 0.6
tonemap_mode = 2
tonemap_white = 6.0
glow_enabled = true
glow_bloom = 0.15
glow_intensity = 0.8
fog_enabled = true
fog_light_color = Color(0.68, 0.78, 0.88, 1)
fog_density = 0.0035"""
        self.sub_resources.insert(0, env_resources)

        # 4. Foundation Floor (72m x 72m, 2m thickness from Y=-2.0 to 0.0)
        self.add_box("Geometry/Ground", "BaseFloor", 0, -1.0, 0, 72, 2.0, 72, "floor_grid")

        # 5. Central Spawn Plaza (X: -12 to 12, Z: -12 to 12)
        self.add_box("Geometry/Plaza", "PlazaOuterRing", 0, 0.02, 0, 24, 0.04, 24, "platform_grid", collision=False)
        self.add_cylinder("Geometry/Plaza", "PlazaInnerCircle", 0, 0.05, 0, 6.5, 0.06, "wall_grid", collision=False)
        self.add_cylinder("Geometry/Plaza", "PlazaCenterCore", 0, 0.07, 0, 2.8, 0.08, "platform_grid", collision=False)

        # Central Orientation Monolith
        self.add_box("Geometry/Plaza", "MonolithBase", 0, 0.25, 0, 3.2, 0.5, 3.2, "steel_trim")
        self.add_box("Geometry/Plaza", "MonolithSubBase", 0, 0.55, 0, 2.2, 0.3, 2.2, "caution_orange")
        self.add_box("Geometry/Plaza", "BeaconCrystal", 0, 2.0, 0, 0.6, 1.4, 0.6, "beacon_core", collision=False)
        self.add_box("Geometry/Plaza", "BeaconRingTop", 0, 2.7, 0, 1.2, 0.08, 1.2, "tech_cyan", collision=False)
        self.add_box("Geometry/Plaza", "BeaconRingBot", 0, 1.3, 0, 1.2, 0.08, 1.2, "tech_cyan", collision=False)

        # Cardinal Direction Floor Arrows
        self.add_box("Geometry/Plaza", "ArrowN", 0, 0.08, -8.0, 1.2, 0.04, 3.5, "tech_cyan", collision=False)
        self.add_box("Geometry/Plaza", "ArrowS", 0, 0.08, 8.0, 1.2, 0.04, 3.5, "caution_orange", collision=False)
        self.add_box("Geometry/Plaza", "ArrowE", 8.0, 0.08, 0, 3.5, 0.04, 1.2, "tech_cyan", collision=False)
        self.add_box("Geometry/Plaza", "ArrowW", -8.0, 0.08, 0, 3.5, 0.04, 1.2, "caution_orange", collision=False)

        # 6. Perimeter Enclosure & Industrial Boundary Walls (72m x 72m)
        wall_h = 4.2
        wall_y = wall_h / 2.0
        wall_len = 72.0
        wall_t = 1.5

        self.add_box("Geometry/Boundaries", "WallNorth", 0, wall_y, -35.25, wall_len, wall_h, wall_t, "wall_grid")
        self.add_box("Geometry/Boundaries", "WallSouth", 0, wall_y, 35.25, wall_len, wall_h, wall_t, "wall_grid")
        self.add_box("Geometry/Boundaries", "WallEast", 35.25, wall_y, 0, wall_t, wall_h, wall_len, "wall_grid")
        self.add_box("Geometry/Boundaries", "WallWest", -35.25, wall_y, 0, wall_t, wall_h, wall_len, "wall_grid")

        # Architectural Base Skirting
        skirt_h = 0.4
        self.add_box("Geometry/Boundaries", "SkirtNorth", 0, 0.2, -34.35, wall_len, skirt_h, 0.4, "steel_trim", collision=False)
        self.add_box("Geometry/Boundaries", "SkirtSouth", 0, 0.2, 34.35, wall_len, skirt_h, 0.4, "steel_trim", collision=False)
        self.add_box("Geometry/Boundaries", "SkirtEast", 34.35, 0.2, 0, 0.4, skirt_h, wall_len, "steel_trim", collision=False)
        self.add_box("Geometry/Boundaries", "SkirtWest", -34.35, 0.2, 0, 0.4, skirt_h, wall_len, "steel_trim", collision=False)

        # Wall Top Caution Trims
        self.add_box("Geometry/Boundaries", "TrimNorth", 0, wall_h + 0.1, -35.25, wall_len, 0.2, wall_t + 0.2, "caution_orange", collision=False)
        self.add_box("Geometry/Boundaries", "TrimSouth", 0, wall_h + 0.1, 35.25, wall_len, 0.2, wall_t + 0.2, "caution_orange", collision=False)
        self.add_box("Geometry/Boundaries", "TrimEast", 35.25, wall_h + 0.1, 0, wall_t + 0.2, 0.2, wall_len, "caution_orange", collision=False)
        self.add_box("Geometry/Boundaries", "TrimWest", -35.25, wall_h + 0.1, 0, wall_t + 0.2, 0.2, wall_len, "caution_orange", collision=False)

        # 4 Corner Bastions with Beacons
        tower_h = 7.0
        for name, cx, cz in [("TowerNW", -35.0, -35.0), ("TowerNE", 35.0, -35.0), ("TowerSW", -35.0, 35.0), ("TowerSE", 35.0, 35.0)]:
            self.add_box("Geometry/Boundaries", name, cx, tower_h / 2.0, cz, 4.2, tower_h, 4.2, "steel_trim")
            self.add_box("Geometry/Boundaries", f"{name}_Stripe", cx, tower_h / 2.0, cz, 4.4, tower_h - 1.0, 0.2, "tech_cyan", collision=False)
            self.add_box("Geometry/Boundaries", f"{name}_Beacon", cx, tower_h + 0.5, cz, 1.4, 1.0, 1.4, "tech_cyan", collision=False)

        # 7. Zone 1: North Parkour & Jump Test Course (Z: -14 to -31, X: -26 to +6)
        self.add_box("Geometry/Parkour", "Platform_1_Low", -13.0, 0.6, -17.0, 4.0, 1.2, 4.0, "platform_grid")
        self.add_box("Geometry/Parkour", "Trim_1", -13.0, 1.15, -17.0, 4.2, 0.1, 4.2, "steel_trim", collision=False)
        self.add_box("Geometry/Parkour", "Pad_1", -13.0, 1.22, -17.0, 3.2, 0.05, 3.2, "parkour_orange", collision=False)

        self.add_box("Geometry/Parkour", "Platform_2_Mid", -18.0, 1.2, -20.0, 4.0, 2.4, 4.0, "platform_grid")
        self.add_box("Geometry/Parkour", "Trim_2", -18.0, 2.35, -20.0, 4.2, 0.1, 4.2, "steel_trim", collision=False)
        self.add_box("Geometry/Parkour", "Pad_2", -18.0, 2.42, -20.0, 3.2, 0.05, 3.2, "parkour_orange", collision=False)

        self.add_box("Geometry/Parkour", "Platform_3_High", -23.0, 2.1, -23.0, 4.5, 4.2, 4.5, "platform_grid")
        self.add_box("Geometry/Parkour", "Trim_3", -23.0, 4.15, -23.0, 4.7, 0.1, 4.7, "steel_trim", collision=False)
        self.add_box("Geometry/Parkour", "Pad_3", -23.0, 4.22, -23.0, 3.6, 0.05, 3.6, "tech_cyan", collision=False)

        self.add_box("Geometry/Parkour", "Platform_4_Summit", -17.0, 3.25, -27.0, 5.0, 6.5, 5.0, "platform_grid")
        self.add_box("Geometry/Parkour", "Trim_4", -17.0, 6.45, -27.0, 5.2, 0.1, 5.2, "steel_trim", collision=False)
        self.add_box("Geometry/Parkour", "Pad_4", -17.0, 6.52, -27.0, 4.0, 0.05, 4.0, "parkour_gold", collision=False)

        self.add_box("Geometry/Parkour", "SkybridgeWalkway", -8.0, 6.5, -27.0, 13.0, 0.5, 3.0, "cover_light_grid")
        self.add_box("Geometry/Parkour", "SkybridgePad", -8.0, 6.77, -27.0, 12.0, 0.05, 2.2, "parkour_gold", collision=False)
        self.add_box("Geometry/Parkour", "SkybridgeLegA", -12.0, 3.125, -27.0, 0.8, 6.25, 0.8, "steel_trim")
        self.add_box("Geometry/Parkour", "SkybridgeLegB", -4.0, 3.125, -27.0, 0.8, 6.25, 0.8, "steel_trim")

        pillar_data = [
            ("PillarA", -5.0, 2.0, -18.0, 2.2, "parkour_orange"),
            ("PillarB", -1.5, 3.5, -21.0, 2.2, "tech_cyan"),
            ("PillarC", 2.0, 5.2, -24.0, 2.2, "parkour_orange"),
            ("PillarD", 5.5, 7.0, -27.0, 2.5, "parkour_gold"),
        ]
        for pname, px, ph, pz, psize, pmat in pillar_data:
            self.add_box("Geometry/Parkour", pname, px, ph / 2.0, pz, psize, ph, psize, "platform_grid")
            self.add_box("Geometry/Parkour", f"{pname}_Trim", px, ph - 0.05, pz, psize + 0.15, 0.1, psize + 0.15, "steel_trim", collision=False)
            self.add_box("Geometry/Parkour", f"{pname}_Pad", px, ph + 0.02, pz, psize - 0.4, 0.05, psize - 0.4, pmat, collision=False)

        # 8. Zone 2: East Observation Deck, Ramp & Stepped Stairs (X: +14 to +32, Z: -24 to +24)
        deck_y = 4.0
        self.add_box("Geometry/ObservationDeck", "DeckFloor", 23.0, deck_y, 0.0, 16.0, 0.6, 26.0, "platform_grid")
        self.add_box("Geometry/ObservationDeck", "DeckAccentPad", 23.0, deck_y + 0.32, 0.0, 14.0, 0.05, 24.0, "cover_light_grid", collision=False)

        self.add_box("Geometry/ObservationDeck", "OverlookBalcony", 13.5, deck_y, 0.0, 3.5, 0.6, 8.0, "platform_grid")
        self.add_box("Geometry/ObservationDeck", "OverlookTrim", 11.7, deck_y + 0.1, 0.0, 0.2, 0.4, 8.0, "tech_cyan", collision=False)

        # Observation Deck Railings
        self.add_box("Geometry/ObservationDeck", "RailingNorth", 23.0, deck_y + 0.85, -12.9, 16.0, 1.1, 0.3, "railing_metal")
        self.add_box("Geometry/ObservationDeck", "RailingSouth", 23.0, deck_y + 0.85, 12.9, 16.0, 1.1, 0.3, "railing_metal")
        self.add_box("Geometry/ObservationDeck", "RailingWestN", 15.1, deck_y + 0.85, -8.0, 0.3, 1.1, 9.8, "railing_metal")
        self.add_box("Geometry/ObservationDeck", "RailingWestS", 15.1, deck_y + 0.85, 8.0, 0.3, 1.1, 9.8, "railing_metal")
        self.add_box("Geometry/ObservationDeck", "RailingOverlookFront", 11.8, deck_y + 0.85, 0.0, 0.3, 1.1, 8.0, "railing_metal")
        self.add_box("Geometry/ObservationDeck", "RailingOverlookN", 13.5, deck_y + 0.85, -4.0, 3.2, 1.1, 0.3, "railing_metal")
        self.add_box("Geometry/ObservationDeck", "RailingOverlookS", 13.5, deck_y + 0.85, 4.0, 3.2, 1.1, 0.3, "railing_metal")

        # North Incline Ramp (Smooth slope)
        ramp_len = 10.45
        ramp_angle = math.degrees(math.atan(4.3 / 9.5))
        self.add_box("Geometry/ObservationDeck", "RampNorth", 20.0, 2.15, -17.75, 5.0, 0.5, ramp_len, "platform_grid", rx=-ramp_angle)
        self.add_box("Geometry/ObservationDeck", "RampNorthPad", 20.0, 2.42, -17.75, 4.2, 0.05, ramp_len - 0.4, "caution_orange", rx=-ramp_angle, collision=False)

        # South Stepped Staircase (14 steps)
        num_steps = 14
        step_rise = 4.2 / num_steps
        step_run = 9.5 / num_steps
        step_width = 5.0
        start_z = 22.5
        for s in range(num_steps):
            sz = start_z - (s + 0.5) * step_run
            st_height = (s + 1) * step_rise
            self.add_box("Geometry/ObservationDeck", f"Step_{s}", 20.0, st_height / 2.0, sz, step_width, st_height, step_run + 0.05, "platform_grid")
            self.add_box("Geometry/ObservationDeck", f"StepTread_{s}", 20.0, st_height + 0.01, sz - step_run * 0.4, step_width - 0.4, 0.02, 0.1, "tech_cyan", collision=False)

        # 9. SEAMLESS INDOOR FACILITY: Command Center & Research Lab
        # Positioned right under the Observation Deck (X: 18 to 31, Z: -7.5 to +7.5, Y: 0 to 4.0m)
        # Inside Floor
        self.add_box("Geometry/IndoorFacility", "IndoorFloor", 24.5, 0.02, 0.0, 13.0, 0.04, 15.0, "indoor_floor_grid", collision=False)

        # Solid Light-Blocking Ceiling (prevents sunlight bleed)
        self.add_box("Geometry/IndoorFacility", "IndoorCeiling", 24.5, 3.85, 0.0, 13.0, 0.3, 15.0, "steel_trim")

        # West Exterior Facade (facing Central Plaza at X = 18.0)
        # Left Wing (Z: -7.5 to -2.0)
        self.add_box("Geometry/IndoorFacility", "Facade_West_NorthWing", 18.0, 1.85, -4.75, 0.8, 3.7, 5.5, "wall_grid")
        # Right Wing with Observation Window Slit (Z: +2.0 to +7.5)
        # Lower wall under window
        self.add_box("Geometry/IndoorFacility", "Facade_West_SouthLower", 18.0, 0.55, 4.75, 0.8, 1.1, 5.5, "wall_grid")
        # Upper wall above window
        self.add_box("Geometry/IndoorFacility", "Facade_West_SouthUpper", 18.0, 3.0, 4.75, 0.8, 1.4, 5.5, "wall_grid")
        # Observation Window Glass
        self.add_box("Geometry/IndoorFacility", "Facade_West_WindowGlass", 18.0, 1.75, 4.75, 0.2, 1.3, 5.2, "window_glass", collision=False)
        # Main Entrance Airlock Portal Lintel (Above doorway)
        self.add_box("Geometry/IndoorFacility", "Facade_Entrance_Lintel", 18.0, 3.4, 0.0, 0.8, 0.6, 4.0, "steel_trim")
        # Entrance Glowing Portal Arch (Frame)
        self.add_box("Geometry/IndoorFacility", "EntranceArch_Left", 17.6, 1.5, -2.0, 0.2, 3.0, 0.2, "tech_cyan", collision=False)
        self.add_box("Geometry/IndoorFacility", "EntranceArch_Right", 17.6, 1.5, 2.0, 0.2, 3.0, 0.2, "tech_cyan", collision=False)
        self.add_box("Geometry/IndoorFacility", "EntranceArch_Top", 17.6, 3.0, 0.0, 0.2, 0.2, 4.2, "tech_cyan", collision=False)

        # North Exterior Wall (Z = -7.5, X: 18 to 31)
        self.add_box("Geometry/IndoorFacility", "Wall_North_Main", 22.5, 1.85, -7.5, 9.0, 3.7, 0.8, "indoor_wall_grid")
        self.add_box("Geometry/IndoorFacility", "Wall_North_Lintel", 28.5, 3.3, -7.5, 3.0, 0.8, 0.8, "steel_trim")
        self.add_box("Geometry/IndoorFacility", "Doorframe_North", 28.5, 1.4, -7.5, 2.2, 2.8, 0.2, "caution_orange", collision=False)

        # South Exterior Wall (Z = +7.5, X: 18 to 31)
        self.add_box("Geometry/IndoorFacility", "Wall_South_Main", 22.5, 1.85, 7.5, 9.0, 3.7, 0.8, "indoor_wall_grid")
        self.add_box("Geometry/IndoorFacility", "Wall_South_Lintel", 28.5, 3.3, 7.5, 3.0, 0.8, 0.8, "steel_trim")
        self.add_box("Geometry/IndoorFacility", "Doorframe_South", 28.5, 1.4, 7.5, 2.2, 2.8, 0.2, "caution_orange", collision=False)

        # East Back Wall (X = 31.0, Z: -7.5 to +7.5)
        self.add_box("Geometry/IndoorFacility", "Wall_East_Back", 31.0, 1.85, 0.0, 0.8, 3.7, 15.0, "indoor_wall_grid")

        # Interior Dividing Partition Wall (X = 24.5, separating Briefing Room & Server Chamber)
        self.add_box("Geometry/IndoorFacility", "Partition_North", 24.5, 1.85, -4.5, 0.6, 3.7, 6.0, "indoor_wall_grid")
        self.add_box("Geometry/IndoorFacility", "Partition_South", 24.5, 1.85, 4.5, 0.6, 3.7, 6.0, "indoor_wall_grid")
        self.add_box("Geometry/IndoorFacility", "Partition_Lintel", 24.5, 3.25, 0.0, 0.6, 0.9, 3.0, "steel_trim")
        self.add_box("Geometry/IndoorFacility", "Partition_Doorframe", 24.5, 1.4, 0.0, 0.65, 2.8, 3.0, "caution_orange", collision=False)

        # --- Room 1: Briefing & Operations Command (X: 18.5 to 24.2, Z: -7.0 to +7.0) ---
        # Central Hologram Briefing Table
        self.add_box("Geometry/IndoorFacility", "HoloTable_Pedestal", 21.5, 0.45, 0.0, 2.6, 0.9, 2.0, "steel_trim")
        self.add_box("Geometry/IndoorFacility", "HoloTable_DisplayPad", 21.5, 0.92, 0.0, 2.2, 0.04, 1.6, "tech_cyan", collision=False)
        self.add_cylinder("Geometry/IndoorFacility", "HoloProjectorBeam", 21.5, 1.4, 0.0, 0.4, 0.9, "beacon_core", collision=False)

        # Wall-mounted Command Consoles
        self.add_box("Geometry/IndoorFacility", "Console_North", 21.5, 0.65, -6.8, 3.0, 1.3, 0.8, "steel_trim")
        self.add_box("Geometry/IndoorFacility", "Console_North_Screen", 21.5, 1.45, -6.9, 2.6, 0.7, 0.1, "tech_cyan", collision=False)

        self.add_box("Geometry/IndoorFacility", "Console_South", 21.5, 0.65, 6.8, 3.0, 1.3, 0.8, "steel_trim")
        self.add_box("Geometry/IndoorFacility", "Console_South_Screen", 21.5, 1.45, 6.9, 2.6, 0.7, 0.1, "server_green", collision=False)

        # Briefing Room Lighting: Calm Sci-Fi Cyan/White OmniLight3D
        self.add_omni_light("Geometry/IndoorFacility", "Light_BriefingRoom", 21.5, 3.2, 0.0, (0.85, 0.94, 1.0), energy=1.4, range_val=8.0, shadow=True)

        # --- Room 2: Server Rack Array & Power Core Chamber (X: 24.8 to 30.6, Z: -7.0 to +7.0) ---
        # 4 High-Density Server Racks with LED arrays
        server_positions = [
            ("ServerRack_1", 27.5, -5.5),
            ("ServerRack_2", 29.5, -5.5),
            ("ServerRack_3", 27.5, 5.5),
            ("ServerRack_4", 29.5, 5.5),
        ]
        for sname, sx, sz in server_positions:
            self.add_box("Geometry/IndoorFacility", sname, sx, 1.5, sz, 1.4, 3.0, 1.6, "steel_trim")
            # Blinking LED indicators
            self.add_box("Geometry/IndoorFacility", f"{sname}_LED_G", sx, 1.8, sz, 1.45, 0.8, 0.1, "server_green", collision=False)
            self.add_box("Geometry/IndoorFacility", f"{sname}_LED_A", sx, 0.9, sz, 1.45, 0.6, 0.1, "server_amber", collision=False)

        # Central Energy Core / Reactor Cylinder
        self.add_cylinder("Geometry/IndoorFacility", "PowerReactor_Base", 28.5, 0.4, 0.0, 1.3, 0.8, "steel_trim")
        self.add_cylinder("Geometry/IndoorFacility", "PowerReactor_Core", 28.5, 1.8, 0.0, 0.8, 2.0, "reactor_core")
        self.add_cylinder("Geometry/IndoorFacility", "PowerReactor_RingTop", 28.5, 2.8, 0.0, 1.1, 0.2, "tech_cyan", collision=False)

        # Server Room Lighting: Atmospheric Amber Warning Glow OmniLight3D
        self.add_omni_light("Geometry/IndoorFacility", "Light_ServerRoom", 28.5, 3.2, 0.0, (1.0, 0.65, 0.20), energy=1.6, range_val=7.0, shadow=True)

        # 10. Zone 3: South Combat & Tactical Sandbox (Z: +15 to +32, X: -20 to +20)
        self.add_box("Geometry/CoverArea", "ContainerA", 7.0, 1.4, 21.0, 3.2, 2.8, 6.5, "caution_orange")
        self.add_box("Geometry/CoverArea", "ContainerA_Roof", 7.0, 2.82, 21.0, 2.8, 0.05, 5.8, "platform_grid", collision=False)
        self.add_box("Geometry/CoverArea", "ContainerA_Frame1", 7.0, 1.4, 17.8, 3.4, 2.9, 0.2, "steel_trim", collision=False)
        self.add_box("Geometry/CoverArea", "ContainerA_Frame2", 7.0, 1.4, 24.2, 3.4, 2.9, 0.2, "steel_trim", collision=False)

        self.add_box("Geometry/CoverArea", "ContainerB", -9.0, 1.4, 24.0, 6.5, 2.8, 3.2, "platform_grid")
        self.add_box("Geometry/CoverArea", "ContainerB_Trim", -9.0, 2.82, 24.0, 6.0, 0.05, 2.6, "tech_cyan", collision=False)
        self.add_box("Geometry/CoverArea", "ContainerB_Frame1", -12.2, 1.4, 24.0, 0.2, 2.9, 3.4, "steel_trim", collision=False)
        self.add_box("Geometry/CoverArea", "ContainerB_Frame2", -5.8, 1.4, 24.0, 0.2, 2.9, 3.4, "steel_trim", collision=False)

        barriers = [
            ("LowCover1", -2.0, 18.0, 6.0, 0.8),
            ("LowCover2", 13.0, 27.0, 5.0, 0.8),
            ("LowCover3", -16.0, 20.0, 4.5, 0.8),
        ]
        for bname, bx, bz, bw, bd in barriers:
            self.add_box("Geometry/CoverArea", bname, bx, 0.55, bz, bw, 1.1, bd, "cover_light_grid")
            self.add_box("Geometry/CoverArea", f"{bname}_Cap", bx, 1.12, bz, bw + 0.1, 0.06, bd + 0.1, "steel_trim", collision=False)

        self.add_box("Geometry/CoverArea", "LWall_WingA", -14.0, 1.3, 27.0, 5.0, 2.6, 0.7, "wall_grid")
        self.add_box("Geometry/CoverArea", "LWall_WingB", -11.85, 1.3, 29.5, 0.7, 2.6, 4.5, "wall_grid")
        self.add_box("Geometry/CoverArea", "LWall_TrimA", -14.0, 2.62, 27.0, 5.1, 0.08, 0.8, "steel_trim", collision=False)
        self.add_box("Geometry/CoverArea", "LWall_TrimB", -11.85, 2.62, 29.5, 0.8, 0.08, 4.6, "steel_trim", collision=False)

        self.add_box("Geometry/CoverArea", "BunkerPlatform", 0.0, 0.8, 27.0, 5.5, 1.6, 5.5, "platform_grid")
        self.add_box("Geometry/CoverArea", "BunkerPad", 0.0, 1.62, 27.0, 4.5, 0.05, 4.5, "cover_light_grid", collision=False)
        self.add_box("Geometry/CoverArea", "BunkerParapetN", 0.0, 2.1, 24.5, 4.5, 0.9, 0.5, "steel_trim")
        self.add_box("Geometry/CoverArea", "BunkerStep1", 0.0, 0.4, 23.6, 2.5, 0.8, 1.0, "platform_grid")

        self.add_box("Geometry/CoverArea", "Crate1", 2.0, 0.6, 21.5, 1.2, 1.2, 1.2, "cover_light_grid")
        self.add_box("Geometry/CoverArea", "Crate2", 3.3, 0.6, 21.5, 1.2, 1.2, 1.2, "cover_light_grid")
        self.add_box("Geometry/CoverArea", "Crate3_Stacked", 2.65, 1.8, 21.5, 1.2, 1.2, 1.2, "caution_orange")

        self.add_box("Geometry/CoverArea", "Crate4", -4.5, 0.6, 23.5, 1.2, 1.2, 1.2, "cover_light_grid")
        self.add_box("Geometry/CoverArea", "Crate5_Stacked", -4.5, 1.8, 23.5, 1.2, 1.2, 1.2, "platform_grid")

        # 11. Zone 4: West Sprint & Speed Highway (X: -16 to -32, Z: -12 to +28)
        self.add_box("Geometry/SprintTrack", "TrackStrip", -25.0, 0.02, 8.0, 7.5, 0.04, 40.0, "platform_grid", collision=False)
        dist_markers = [(-10.0, "START"), (0.0, "10M"), (10.0, "20M"), (20.0, "30M"), (30.0, "40M")]
        for idx, (mz, mlabel) in enumerate(dist_markers):
            self.add_box("Geometry/SprintTrack", f"DistLine_{idx}", -25.0, 0.05, mz, 7.0, 0.04, 0.5, "tech_cyan", collision=False)

        for zi in range(-8, 28, 4):
            tag = f"m{abs(zi)}" if zi < 0 else str(zi)
            self.add_box("Geometry/SprintTrack", f"Dash_{tag}", -25.0, 0.05, float(zi), 0.4, 0.04, 2.0, "caution_orange", collision=False)

        for idx, gz in enumerate([-8.0, 4.0, 16.0, 28.0]):
            self.add_box("Geometry/SprintTrack", f"Arch_{idx}_Left", -28.75, 2.25, gz, 0.9, 4.5, 0.9, "steel_trim")
            self.add_box("Geometry/SprintTrack", f"Arch_{idx}_Right", -21.25, 2.25, gz, 0.9, 4.5, 0.9, "steel_trim")
            self.add_box("Geometry/SprintTrack", f"Arch_{idx}_Beam", -25.0, 4.4, gz, 8.4, 0.6, 0.9, "steel_trim")
            self.add_box("Geometry/SprintTrack", f"Arch_{idx}_Glow", -25.0, 4.05, gz, 6.5, 0.1, 0.4, "tech_cyan", collision=False)

        for h_idx, hz in enumerate([-2.0, 6.0, 14.0, 22.0]):
            self.add_box("Geometry/SprintTrack", f"Hurdle_{h_idx}", -30.5, 0.4, hz, 2.4, 0.8, 0.3, "steel_trim")
            self.add_box("Geometry/SprintTrack", f"HurdlePad_{h_idx}", -30.5, 0.82, hz, 2.2, 0.06, 0.25, "caution_orange", collision=False)

    def export_tscn(self, file_path, root_node_name="Arena"):
        self.build()
        
        lines = []
        total_steps = len(self.sub_resources) + 2
        lines.append(f'[gd_scene load_steps={total_steps} format=3]')
        lines.append('')
        lines.append('[ext_resource type="Shader" path="res://assets/shaders/prototype_grid.gdshader" id="1_grid_shader"]')
        lines.append('')

        for sr in self.sub_resources:
            lines.append(sr)
            lines.append('')

        lines.append(f'[node name="{root_node_name}" type="Node3D"]')
        lines.append('')
        
        # Environment
        lines.append('[node name="Environment" type="Node3D" parent="."]')
        lines.append('')
        lines.append('[node name="WorldEnvironment" type="WorldEnvironment" parent="Environment"]')
        lines.append('environment = SubResource("Environment_demo")')
        lines.append('')
        lines.append('[node name="DirectionalLight3D" type="DirectionalLight3D" parent="Environment"]')
        lines.append('transform = Transform3D(0.819152, -0.405580, 0.405580, 0.000000, 0.707107, 0.707107, -0.573576, -0.579228, 0.579228, 0, 15, 0)')
        lines.append('light_color = Color(1, 0.96, 0.9, 1)')
        lines.append('light_energy = 1.25')
        lines.append('shadow_enabled = true')
        lines.append('shadow_blur = 1.2')
        lines.append('directional_shadow_mode = 2')
        lines.append('directional_shadow_blend_splits = true')
        lines.append('')
        
        # Category containers
        lines.append('[node name="Geometry" type="Node3D" parent="."]')
        lines.append('')
        for cat in ["Ground", "Plaza", "Boundaries", "Parkour", "ObservationDeck", "IndoorFacility", "CoverArea", "SprintTrack"]:
            lines.append(f'[node name="{cat}" type="Node3D" parent="Geometry"]')
            lines.append('')
            
        for n in self.nodes:
            lines.append(n)
            lines.append('')
            
        content = "\n".join(lines)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Successfully generated {file_path} with {len(self.nodes)} geometry elements and {len(self.sub_resources)} sub-resources.")

if __name__ == "__main__":
    out_dir = os.path.join(os.getcwd(), "scenes", "level")
    os.makedirs(out_dir, exist_ok=True)
    gen = ArenaGenerator()
    gen.export_tscn(os.path.join(out_dir, "arena.tscn"), root_node_name="Arena")
    # Also keep demo_arena.tscn for compatibility
    gen2 = ArenaGenerator()
    gen2.export_tscn(os.path.join(out_dir, "demo_arena.tscn"), root_node_name="DemoArena")
