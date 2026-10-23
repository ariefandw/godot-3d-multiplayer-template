shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back, diffuse_burley, specular_schlick_ggx;

uniform vec4 albedo_color : source_color = vec4(0.14, 0.16, 0.20, 1.0);
uniform vec4 grid_color : source_color = vec4(0.24, 0.28, 0.35, 1.0);
uniform vec4 major_grid_color : source_color = vec4(0.38, 0.45, 0.55, 1.0);
uniform float grid_size : hint_range(0.1, 10.0) = 1.0;
uniform float major_grid_step : hint_range(1.0, 20.0) = 5.0;
uniform float line_thickness : hint_range(0.005, 0.1) = 0.02;
uniform float roughness : hint_range(0.0, 1.0) = 0.8;
uniform float metallic : hint_range(0.0, 1.0) = 0.0;

varying vec3 world_pos;
varying vec3 world_normal;

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	world_normal = abs(normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz));
}

void fragment() {
	vec3 blend_weights = pow(world_normal, vec3(4.0));
	blend_weights /= (blend_weights.x + blend_weights.y + blend_weights.z + 0.0001);

	// Grid coords for triplanar
	vec2 coord_x = world_pos.zy / grid_size;
	vec2 coord_y = world_pos.xz / grid_size;
	vec2 coord_z = world_pos.xy / grid_size;

	// Anti-aliased 1m grid lines
	vec2 fx = fwidth(coord_x);
	vec2 fy = fwidth(coord_y);
	vec2 fz = fwidth(coord_z);

	vec2 gx = abs(fract(coord_x - 0.5) - 0.5);
	vec2 gy = abs(fract(coord_y - 0.5) - 0.5);
	vec2 gz = abs(fract(coord_z - 0.5) - 0.5);

	float lx = 1.0 - smoothstep(0.0, max(fx.x, fx.y) * 1.5 + line_thickness, min(gx.x, gx.y));
	float ly = 1.0 - smoothstep(0.0, max(fy.x, fy.y) * 1.5 + line_thickness, min(gy.x, gy.y));
	float lz = 1.0 - smoothstep(0.0, max(fz.x, fz.y) * 1.5 + line_thickness, min(gz.x, gz.y));

	float grid_1m = lx * blend_weights.x + ly * blend_weights.y + lz * blend_weights.z;

	// Major 5m grid lines
	vec2 m_coord_x = coord_x / major_grid_step;
	vec2 m_coord_y = coord_y / major_grid_step;
	vec2 m_coord_z = coord_z / major_grid_step;

	vec2 m_fx = fwidth(m_coord_x);
	vec2 m_fy = fwidth(m_coord_y);
	vec2 m_fz = fwidth(m_coord_z);

	vec2 m_gx = abs(fract(m_coord_x - 0.5) - 0.5);
	vec2 m_gy = abs(fract(m_coord_y - 0.5) - 0.5);
	vec2 m_gz = abs(fract(m_coord_z - 0.5) - 0.5);

	float m_lx = 1.0 - smoothstep(0.0, max(m_fx.x, m_fx.y) * 1.5 + line_thickness * 1.5, min(m_gx.x, m_gx.y));
	float m_ly = 1.0 - smoothstep(0.0, max(m_fy.x, m_fy.y) * 1.5 + line_thickness * 1.5, min(m_gy.x, m_gy.y));
	float m_lz = 1.0 - smoothstep(0.0, max(m_fz.x, m_fz.y) * 1.5 + line_thickness * 1.5, min(m_gz.x, m_gz.y));

	float grid_5m = m_lx * blend_weights.x + m_ly * blend_weights.y + m_lz * blend_weights.z;

	vec3 col = mix(albedo_color.rgb, grid_color.rgb, clamp(grid_1m, 0.0, 1.0));
	col = mix(col, major_grid_color.rgb, clamp(grid_5m, 0.0, 1.0));

	ALBEDO = col;
	ROUGHNESS = roughness;
	METALLIC = metallic;
}
