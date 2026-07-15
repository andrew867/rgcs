// v7 (RGCS v3, Agent 08) -- derived from v6 with EXACTLY ONE functional
// change: D-02 fix (inert compact-mode rings). See scad/README.md
// 'CAD provenance' for the diff summary; v6 remains shipped verbatim.
/*
  Vogel / Eredyon-style faceted quartz representative model generator v6 RGCS v2 compact-mode integration
  ----------------------------------------------------------------------
  Units: millimeters.

  Purpose:
    Generate dimensionally representative double-terminated, faceted, tapered crystal models
    for 3D printing, acoustic/node experiments, coil-form design, and geometry comparison.

  v2 additions:
    - OpenSCAD Customizer dropdowns for presets and sizing modes.
    - Raw, density-corrected, and harmonic/ratio-driven presets.
    - 4096×N ideal axial length generation.
    - L/Davg and wide/narrow taper solver.
    - Optional eye/compression-node marker, 20/21 Hz electrode pads, coil reference, 52° collector.

  v4 public addition:
    - Optional spiral_reference render mode giving a simple contracting log-spiral path next to
      the selected crystal.

  v5 JH source-integration additions:
    - Separate metric-center, geometry-estimated, and measured eye/node markers.
    - Eye/node provenance is explicit; the metric center is no longer silently treated as the physical node.
    - Added an ideal N=7 reference near 110.038 mm, matching a source-referenced 110 mm specimen class.
    - Source turn-count variants remain measurement inputs rather than hidden assumptions.

  v6 RGCS v2 additions:
    - Optional even/odd compact-mode rings across the crystal body.
    - Optional paired-mode markers for coupled-mode / phase-conjugation experiments.
    - Dedicated compact_mode_crystal render dispatch.

  Angle convention warning:
    Source material uses 51.843°, 51°51'51", ~52°, and 60° across several
    drafting descriptions. Default here is face_slope: angle between pyramid face and base plane,
    matching Great-Pyramid-style slope usage. Change angle_mode if you are modelling another convention.

  Diameter convention warning:
    Product listing dimensions are treated as across-vertices by default, because seller calipers
    usually capture the largest bounding width. Use across_flats only if your measured value is flat-to-flat.
*/

// ----------------------------
// OpenSCAD Customizer controls
// ----------------------------

/* [Render] */
render_mode = "single"; // [single, all_presets, harmonic_ladder, collector_only, spiral_reference, compact_mode_crystal]
model_scale = 1.0; // [0.1:0.1:3]
spacing_mm = 65; // [30:5:150]

/* [Preset dropdown] */
selected_preset = "Himalayan_157mm_8sided"; // [Custom, Himalayan_157mm_8sided, Himalayan_157mm_8sided_density_corrected, Ideal_N5_154mm_6sided_ratio, Prototype_153mm_6sided, Prototype_152mm_6sided, Prototype_101mm_6sided, Ideal_N6_128mm_6sided_ratio, Ideal_N7_110mm_6sided_ratio, Ideal_N9_86mm_6sided_ratio, Himalayan_125mm_8sided, Himalayan_125mm_12sided, Citrine_71mm_24sided, Citrine_81mm_8sided, Smoky_62mm_24sided, Rutilated_86mm_24sided]

/* [Sizing mode] */
sizing_mode = "preset_dimensions"; // [preset_dimensions, density_corrected_if_available, ratio_from_length, ideal_4096_harmonic]
harmonic_N = 5; // [5:1:12]
base_frequency_hz = 4096; // [1:1:32768]
quartz_longitudinal_velocity_m_s = 6310; // [5000:10:7000]
length_to_avg_diameter = 6.0; // [2:0.1:10]
wide_to_narrow_ratio = 1.6; // [1:0.05:3]

/* [Custom dimensions, used when selected_preset = Custom or sizing mode asks for custom] */
custom_length_mm = 157; // [20:1:300]
custom_sides = 6; // [3:1:48]
custom_wide_d_mm = 32; // [3:0.1:80]
custom_narrow_d_mm = 20; // [3:0.1:80]
custom_rx_angle_deg = 51.843; // [20:0.001:80]
custom_tx_angle_deg = 60; // [20:0.001:80]

/* [Geometry convention] */
angle_mode = "face_slope"; // [face_slope, apex_included, axis_to_face]
diameter_mode = "across_vertices"; // [across_vertices, across_flats]
facet_rotation_deg = 30; // [0:1:360]
rx_angle_override_deg = 51.843; // [20:0.001:80]
tx_angle_override_deg = 60; // [20:0.001:80]
use_angle_overrides = false;

/* [Eye / node markers and references] */
show_eye_marker = true; // legacy alias: displays the geometry-estimated marker
show_metric_center_marker = true;
show_geometry_eye_marker = true;
show_measured_eye_marker = false;
geometry_eye_fraction_from_female = 0.50; // [0:0.001:1]
measured_eye_from_female_mm = 77.0; // [0:0.1:300]
marker_width_mm = 0.8; // [0.1:0.1:5]
metric_marker_radius_extra_mm = 0.30; // [0.1:0.05:3]
geometry_marker_radius_extra_mm = 0.70; // [0.1:0.05:3]
measured_marker_radius_extra_mm = 1.10; // [0.1:0.05:3]
show_axis_reference = false;
show_electrode_pads = false;
electrode_fraction_from_female = 0.50; // set to measured eye fraction after physical mapping // [0:0.01:1]
electrode_pad_radius_mm = 1.8; // [0.5:0.1:8]
electrode_pad_height_mm = 0.5; // [0.1:0.1:3]

/* [RGCS v2 compact-mode references] */
show_compact_mode_rings = false;
// v7 fix (D-02): OpenSCAD block-scope assignment cannot override a top-level
// customizer variable, so the compact_mode_crystal dispatch flag was inert in
// v6. The render dispatch and modules now use this derived flag instead.
effective_show_compact_mode_rings = show_compact_mode_rings || (render_mode == "compact_mode_crystal");
compact_mode_count = 12; // [1:1:32]
compact_mode_parity = "all"; // [all, odd, even]
compact_ring_width_mm = 0.45; // [0.1:0.05:3]
compact_ring_radius_extra_mm = 0.45; // [0.1:0.05:3]
show_phase_conjugate_pair = false;
phase_pair_mode_a = 5; // [1:1:32]
phase_pair_mode_b = 10; // [1:1:64]

/* [Coil reference, visual only] */
show_coil_reference = false;
coil_turns = 40; // [1:1:120]
coil_wire_d_mm = 0.33; // [0.1:0.01:2]
coil_clearance_mm = 2.0; // [0:0.1:10]
coil_phase_deg = 0; // [0:1:360]
show_counter_coil = true;

/* [52 degree collector / pyramid reference] */
show_pyramid_collector = false;
collector_slope_deg = 52; // [20:0.1:80]
collector_height_ratio_of_crystal = 0.20; // [0.05:0.01:1]
collector_gap_above_tip_mm = 2; // [0:0.1:30]
collector_wall_mm = 1.2; // [0.2:0.1:5]


/* [Spiral reference, visual only] */
show_spiral_reference_next_to_crystal = true;
spiral_reference_q = 2.0; // [1.05:0.01:8]
spiral_reference_turns = 5; // [1:0.25:12]
spiral_reference_radius_mm = 35; // [5:1:150]
spiral_reference_height_mm = 45; // [1:1:200]
spiral_reference_tube_mm = 0.8; // [0.1:0.1:5]
spiral_reference_steps = 160; // [24:8:480]

/* [Print helper] */
add_flat_base_support = false;
base_support_thickness_mm = 1.0; // [0.2:0.1:5]
base_support_radius_extra_mm = 2.0; // [0:0.1:10]

$fn = 80;

// ----------------------------
// Preset data
// list layout: [L, sides, wide, narrow, corrected_wide, corrected_narrow, rx, tx]
// corrected values equal raw when no density-corrected value is available.
// ----------------------------

function preset_values(p) =
    p == "Himalayan_157mm_8sided" ? [157, 8, 32, 20, 32.5445536782, 20.3403460489, 51.843, 60] :
    p == "Himalayan_157mm_8sided_density_corrected" ? [157, 8, 32.5445536782, 20.3403460489, 32.5445536782, 20.3403460489, 51.843, 60] :
    p == "Ideal_N5_154mm_6sided_ratio" ? [154.052734375, 6, 31.6005608974, 19.7503505609, 31.6005608974, 19.7503505609, 51.843, 60] :
    p == "Prototype_153mm_6sided" ? [153, 6, 32, 20, 32, 20, 51.843, 60] :
    p == "Prototype_152mm_6sided" ? [152, 6, 32, 20, 32, 20, 51.843, 60] :
    p == "Prototype_101mm_6sided" ? [101, 6, 22, 16, 22, 16, 51.843, 60] :
    p == "Ideal_N6_128mm_6sided_ratio" ? [128.377278646, 6, 26.333800748, 16.458625468, 26.333800748, 16.458625468, 51.843, 60] :
    p == "Ideal_N7_110mm_6sided_ratio" ? [110.037667411, 6, 22.571829213, 14.107393258, 22.571829213, 14.107393258, 51.843, 60] :
    p == "Ideal_N9_86mm_6sided_ratio" ? [85.584852431, 6, 17.555867165, 10.972416978, 17.555867165, 10.972416978, 51.843, 60] :
    p == "Himalayan_125mm_8sided" ? [125, 8, 21, 14, 22.9217020110, 15.2811346740, 51.843, 60] :
    p == "Himalayan_125mm_12sided" ? [125, 12, 20, 16, 19.8830334788, 15.9064267830, 51.843, 60] :
    p == "Citrine_71mm_24sided" ? [71, 24, 20, 15, 19.8902411032, 14.9176808274, 51.843, 60] :
    p == "Citrine_81mm_8sided" ? [81, 8, 19, 15, 19.9914806684, 15.7827478961, 51.843, 60] :
    p == "Smoky_62mm_24sided" ? [62, 24, 21, 17, 22.4933623558, 18.2089123833, 51.843, 60] :
    p == "Rutilated_86mm_24sided" ? [86, 24, 35, 29, 36.2043925337, 29.9979252422, 51.843, 60] :
    [custom_length_mm, custom_sides, custom_wide_d_mm, custom_narrow_d_mm, custom_wide_d_mm, custom_narrow_d_mm, custom_rx_angle_deg, custom_tx_angle_deg];

all_presets = [
    "Himalayan_157mm_8sided",
    "Himalayan_157mm_8sided_density_corrected",
    "Ideal_N5_154mm_6sided_ratio",
    "Prototype_153mm_6sided",
    "Prototype_152mm_6sided",
    "Prototype_101mm_6sided",
    "Ideal_N6_128mm_6sided_ratio",
    "Ideal_N7_110mm_6sided_ratio",
    "Ideal_N9_86mm_6sided_ratio",
    "Himalayan_125mm_8sided",
    "Himalayan_125mm_12sided",
    "Citrine_71mm_24sided",
    "Citrine_81mm_8sided",
    "Smoky_62mm_24sided",
    "Rutilated_86mm_24sided"
];

// ----------------------------
// Derived sizing functions
// ----------------------------

function ideal_length_for_harmonic(N, v=6310, fbase=4096) = v / (2 * fbase * N) * 1000;
function ratio_widths_from_length(L, ld=6, taper=1.6) =
    let(avg = L / ld, narrow = 2 * avg / (1 + taper), wide = taper * narrow)
    [wide, narrow];

function selected_raw() = preset_values(selected_preset);
function selected_length() =
    let(raw = selected_raw())
    sizing_mode == "ideal_4096_harmonic" ? ideal_length_for_harmonic(harmonic_N, quartz_longitudinal_velocity_m_s, base_frequency_hz) :
    selected_preset == "Custom" ? custom_length_mm : raw[0];
function selected_sides() = let(raw = selected_raw()) selected_preset == "Custom" ? custom_sides : raw[1];
function selected_widths() =
    let(raw = selected_raw())
    sizing_mode == "ratio_from_length" || sizing_mode == "ideal_4096_harmonic" ? ratio_widths_from_length(selected_length(), length_to_avg_diameter, wide_to_narrow_ratio) :
    sizing_mode == "density_corrected_if_available" ? [raw[4], raw[5]] :
    [raw[2], raw[3]];
function selected_rx() = let(raw = selected_raw()) use_angle_overrides ? rx_angle_override_deg : raw[6];
function selected_tx() = let(raw = selected_raw()) use_angle_overrides ? tx_angle_override_deg : raw[7];

// ----------------------------
// Geometry functions
// ----------------------------

function circumradius_from_diameter(d, sides, mode) =
    mode == "across_flats" ? (d / 2) / cos(180 / sides) : d / 2;
function apothem_from_circumradius(R, sides) = R * cos(180 / sides);
function side_width_from_circumradius(R, sides) = 2 * R * sin(180 / sides);
function across_flats_from_circumradius(R, sides) = 2 * R * cos(180 / sides);
function polygon_area_from_R(R, sides) = sides / 2 * R * R * sin(360 / sides);

function cap_height_from_angle(d, sides, angle_deg, mode, diameter_mode) =
    let(R = circumradius_from_diameter(d, sides, diameter_mode), a = apothem_from_circumradius(R, sides))
    mode == "apex_included" ? a / tan(angle_deg / 2) :
    mode == "axis_to_face"  ? a / tan(angle_deg) :
                               a * tan(angle_deg);

function ring_points(sides, R, z, rot_deg) =
    [for (i = [0 : sides - 1]) [R * cos(rot_deg + 360 * i / sides), R * sin(rot_deg + 360 * i / sides), z]];

function crystal_faces(s) =
    concat(
        [for (i = [0 : s - 1]) [0, 1 + ((i + 1) % s), 1 + i]],
        [for (i = [0 : s - 1]) [1 + i, 1 + ((i + 1) % s), 1 + s + ((i + 1) % s), 1 + s + i]],
        [for (i = [0 : s - 1]) [1 + 2 * s, 1 + s + i, 1 + s + ((i + 1) % s)]]
    );

function radius_at_z(z, L, rx_h, tx_h, Rw, Rn) =
    z <= rx_h ? max(Rw * z / max(rx_h, 0.001), 0) :
    z >= L - tx_h ? max(Rn * (L - z) / max(tx_h, 0.001), 0) :
    Rw + (Rn - Rw) * ((z - rx_h) / max(L - rx_h - tx_h, 0.001));

function volume_mm3(L, sides, wide_d, narrow_d, rx_angle, tx_angle, angle_mode, diameter_mode) =
    let(
        Rw = circumradius_from_diameter(wide_d, sides, diameter_mode),
        Rn = circumradius_from_diameter(narrow_d, sides, diameter_mode),
        Aw = polygon_area_from_R(Rw, sides),
        An = polygon_area_from_R(Rn, sides),
        rx_h = cap_height_from_angle(wide_d, sides, rx_angle, angle_mode, diameter_mode),
        tx_h = cap_height_from_angle(narrow_d, sides, tx_angle, angle_mode, diameter_mode),
        shaft_h = L - rx_h - tx_h
    )
    (shaft_h / 3 * (Aw + An + sqrt(Aw * An)) + Aw * rx_h / 3 + An * tx_h / 3);

// ----------------------------
// Main modules
// ----------------------------

module vogel_wand(length_mm, sides, wide_d_mm, narrow_d_mm, rx_angle_deg, tx_angle_deg, label="model") {
    Rw = circumradius_from_diameter(wide_d_mm, sides, diameter_mode);
    Rn = circumradius_from_diameter(narrow_d_mm, sides, diameter_mode);
    rx_h = cap_height_from_angle(wide_d_mm, sides, rx_angle_deg, angle_mode, diameter_mode);
    tx_h = cap_height_from_angle(narrow_d_mm, sides, tx_angle_deg, angle_mode, diameter_mode);
    body_len = length_mm - rx_h - tx_h;
    vol_cm3 = volume_mm3(length_mm, sides, wide_d_mm, narrow_d_mm, rx_angle_deg, tx_angle_deg, angle_mode, diameter_mode) / 1000;
    axial_khz = quartz_longitudinal_velocity_m_s / (2 * length_mm);
    nearest_N = round(axial_khz / (base_frequency_hz / 1000));

    echo(str("MODEL=", label));
    echo(str("L=", length_mm, " mm, sides=", sides, ", wide=", wide_d_mm, " mm, narrow=", narrow_d_mm, " mm"));
    echo(str("angles rx/tx=", rx_angle_deg, "/", tx_angle_deg, " deg, angle_mode=", angle_mode, ", diameter_mode=", diameter_mode));
    echo(str("rx_h=", rx_h, " mm, tx_h=", tx_h, " mm, body_len=", body_len, " mm"));
    echo(str("volume=", vol_cm3, " cm3, quartz_mass_at_2.65=", vol_cm3*2.65, " g"));
    echo(str("axial_half_wave=", axial_khz, " kHz, nearest N*4096=", nearest_N));
    echo(str("node metric=", length_mm/2, " mm, geometry=", length_mm*geometry_eye_fraction_from_female, " mm, measured_input=", measured_eye_from_female_mm, " mm"));

    assert(sides >= 3, "sides must be >= 3");
    assert(body_len > 0, "Termination cap heights exceed total length. Change dimensions or angle convention.");

    points = concat(
        [[0, 0, 0]],
        ring_points(sides, Rw, rx_h, facet_rotation_deg),
        ring_points(sides, Rn, length_mm - tx_h, facet_rotation_deg),
        [[0, 0, length_mm]]
    );

    union() {
        polyhedron(points = points, faces = crystal_faces(sides), convexity = 10);

        if (show_metric_center_marker) node_marker(length_mm/2, length_mm, sides, rx_h, tx_h, Rw, Rn, metric_marker_radius_extra_mm, "metric_center");
        if (show_eye_marker || show_geometry_eye_marker) node_marker(length_mm*geometry_eye_fraction_from_female, length_mm, sides, rx_h, tx_h, Rw, Rn, geometry_marker_radius_extra_mm, "geometry_estimate");
        if (show_measured_eye_marker) node_marker(measured_eye_from_female_mm, length_mm, sides, rx_h, tx_h, Rw, Rn, measured_marker_radius_extra_mm, "measured_eye");
        if (show_electrode_pads) electrode_pads(length_mm, sides, wide_d_mm, narrow_d_mm, rx_h, tx_h, Rw, Rn);
        if (effective_show_compact_mode_rings) compact_mode_rings(length_mm, sides, rx_h, tx_h, Rw, Rn);
        if (show_phase_conjugate_pair) phase_conjugate_pair_markers(length_mm, sides, rx_h, tx_h, Rw, Rn);
        if (add_flat_base_support) flat_support(length_mm, wide_d_mm, sides);
    }
}

module node_marker(z_node, L, sides, rx_h, tx_h, Rw, Rn, radial_extra, marker_label="node") {
    z_safe = min(max(z_node, 0), L);
    r_node = radius_at_z(z_safe, L, rx_h, tx_h, Rw, Rn);
    echo(str("NODE_MARKER=", marker_label, ", z_from_female=", z_safe, " mm, gamma=", z_safe/L));
    translate([0, 0, z_safe - marker_width_mm / 2])
        difference() {
            cylinder(h = marker_width_mm, r = r_node + radial_extra, $fn = sides * 8);
            translate([0, 0, -0.1]) cylinder(h = marker_width_mm + 0.2, r = max(r_node - 0.05, 0.1), $fn = sides * 8);
        }
}

module compact_mode_rings(L, sides, rx_h, tx_h, Rw, Rn) {
    for (n = [1:compact_mode_count]) {
        allowed = compact_mode_parity == "all" || (compact_mode_parity == "odd" && n % 2 == 1) || (compact_mode_parity == "even" && n % 2 == 0);
        if (allowed) {
            z = L * n / (compact_mode_count + 1);
            r = radius_at_z(z, L, rx_h, tx_h, Rw, Rn);
            echo(str("COMPACT_MODE_RING n=", n, ", parity=", n%2==0?"even":"odd", ", z=", z));
            translate([0,0,z-compact_ring_width_mm/2]) difference() {
                cylinder(h=compact_ring_width_mm, r=r+compact_ring_radius_extra_mm, $fn=sides*8);
                translate([0,0,-0.05]) cylinder(h=compact_ring_width_mm+0.1, r=max(r-0.04,0.1), $fn=sides*8);
            }
        }
    }
}

module phase_conjugate_pair_markers(L, sides, rx_h, tx_h, Rw, Rn) {
    for (n = [phase_pair_mode_a, phase_pair_mode_b]) {
        z = L * n / (max(phase_pair_mode_a, phase_pair_mode_b)+1);
        r = radius_at_z(z, L, rx_h, tx_h, Rw, Rn);
        translate([0,0,z-compact_ring_width_mm]) difference() {
            cylinder(h=compact_ring_width_mm*2, r=r+compact_ring_radius_extra_mm*1.8, $fn=sides*8);
            translate([0,0,-0.05]) cylinder(h=compact_ring_width_mm*2+0.1, r=max(r-0.04,0.1), $fn=sides*8);
        }
    }
}

module electrode_pads(L, sides, wide_d, narrow_d, rx_h, tx_h, Rw, Rn) {
    z = L * electrode_fraction_from_female;
    r = radius_at_z(z, L, rx_h, tx_h, Rw, Rn) + 0.25;
    for (ang = [0, 180]) {
        translate([r*cos(ang), r*sin(ang), z])
            rotate([0, 90, ang])
                cylinder(h = electrode_pad_height_mm, r = electrode_pad_radius_mm, center = true, $fn = 24);
    }
}

module flat_support(L, wide_d, sides) {
    R = circumradius_from_diameter(wide_d, sides, diameter_mode) + base_support_radius_extra_mm;
    translate([0, 0, -base_support_thickness_mm])
        cylinder(h = base_support_thickness_mm, r = R, $fn = max(sides*4, 32));
}

module axis_reference_rods(length_mm, radius_mm = 0.6, offset_mm = 24) {
    translate([offset_mm, 0, length_mm / 2]) rotate([0, 90, 0]) cylinder(h = offset_mm * 1.4, r = radius_mm, center = true);
    translate([0, offset_mm, length_mm / 2]) rotate([90, 0, 0]) cylinder(h = offset_mm * 1.4, r = radius_mm, center = true);
    translate([0, 0, length_mm / 2]) cylinder(h = length_mm, r = radius_mm, center = true);
}

module square_pyramid_shell(height_mm = 30, slope_deg = 52, wall_mm = 1.2) {
    half_base = height_mm / tan(slope_deg);
    inner_h = max(height_mm - wall_mm, 0.1);
    inner_half_base = max(half_base - wall_mm, 0.1);
    difference() {
        polyhedron(
            points = [[-half_base,-half_base,0],[half_base,-half_base,0],[half_base,half_base,0],[-half_base,half_base,0],[0,0,height_mm]],
            faces = [[0,1,2,3],[0,4,1],[1,4,2],[2,4,3],[3,4,0]], convexity = 10
        );
        translate([0,0,-0.05])
            polyhedron(
                points = [[-inner_half_base,-inner_half_base,0],[inner_half_base,-inner_half_base,0],[inner_half_base,inner_half_base,0],[-inner_half_base,inner_half_base,0],[0,0,inner_h]],
                faces = [[0,1,2,3],[0,4,1],[1,4,2],[2,4,3],[3,4,0]], convexity = 10
            );
    }
}

module coil_reference_helix(length_mm, radius_mm, turns, wire_d_mm, phase_deg = 0) {
    steps = max(turns * 16, 16);
    for (i = [0 : steps]) {
        t = i / steps;
        ang = phase_deg + 360 * turns * t;
        translate([radius_mm * cos(ang), radius_mm * sin(ang), length_mm * t])
            sphere(r = wire_d_mm / 2, $fn = 12);
    }
}

module render_current(label="current") {
    L = selected_length();
    S = selected_sides();
    WN = selected_widths();
    W = WN[0];
    N = WN[1];
    RX = selected_rx();
    TX = selected_tx();

    scale([model_scale, model_scale, model_scale]) {
        vogel_wand(L, S, W, N, RX, TX, label);
        if (show_axis_reference)
            axis_reference_rods(length_mm = L, offset_mm = W + 12);
        if (show_pyramid_collector) {
            collector_h = L * collector_height_ratio_of_crystal;
            translate([0, 0, L + collector_gap_above_tip_mm])
                square_pyramid_shell(height_mm = collector_h, slope_deg = collector_slope_deg, wall_mm = collector_wall_mm);
        }
        if (show_coil_reference) {
            coil_radius = max(W, N) / 2 + coil_clearance_mm;
            coil_reference_helix(length_mm = L, radius_mm = coil_radius, turns = coil_turns, wire_d_mm = coil_wire_d_mm, phase_deg = coil_phase_deg);
            if (show_counter_coil)
                coil_reference_helix(length_mm = L, radius_mm = coil_radius + 1.0, turns = coil_turns, wire_d_mm = coil_wire_d_mm, phase_deg = coil_phase_deg + 180);
        }
    }
}

module render_named_preset(p, offset=[0,0,0]) {
    translate(offset) {
        old = selected_preset; // no assignment mutation used; call preset directly below
        raw = preset_values(p);
        L0 = raw[0]; S0 = raw[1]; W0 = raw[2]; N0 = raw[3]; RX0 = raw[6]; TX0 = raw[7];
        vogel_wand(L0, S0, W0, N0, RX0, TX0, p);
    }
}

module render_all_presets() {
    for (idx = [0 : len(all_presets) - 1]) {
        translate([(idx % 4) * spacing_mm, floor(idx / 4) * spacing_mm, 0])
            render_named_preset(all_presets[idx]);
    }
}

module render_harmonic_ladder() {
    for (idx = [0 : 7]) {
        Nval = idx + 5;
        L = ideal_length_for_harmonic(Nval, quartz_longitudinal_velocity_m_s, base_frequency_hz);
        WN = ratio_widths_from_length(L, length_to_avg_diameter, wide_to_narrow_ratio);
        translate([(idx % 4) * spacing_mm, floor(idx / 4) * spacing_mm, 0])
            vogel_wand(L, custom_sides, WN[0], WN[1], selected_rx(), selected_tx(), str("N", Nval, "_", L, "mm"));
    }
}


// ----------------------------
// Spiral reference module added in v4 public
// ----------------------------

function spiral_reference_r(t) = max(0.5, spiral_reference_radius_mm / pow(spiral_reference_q, spiral_reference_turns * t));
function spiral_reference_z(t) = spiral_reference_height_mm * (1 - pow(spiral_reference_q, -spiral_reference_turns * t));
function spiral_reference_theta(t) = 360 * spiral_reference_turns * t;

module spiral_reference_path() {
    echo(str("SPIRAL_REFERENCE q=", spiral_reference_q, ", turns=", spiral_reference_turns, ", a=", ln(spiral_reference_q)/(2*PI)));
    for (i = [0:spiral_reference_steps-1]) {
        t1 = i / spiral_reference_steps;
        t2 = (i + 1) / spiral_reference_steps;
        hull() {
            translate([spiral_reference_r(t1)*cos(spiral_reference_theta(t1)), spiral_reference_r(t1)*sin(spiral_reference_theta(t1)), spiral_reference_z(t1)])
                sphere(r = spiral_reference_tube_mm, $fn = 12);
            translate([spiral_reference_r(t2)*cos(spiral_reference_theta(t2)), spiral_reference_r(t2)*sin(spiral_reference_theta(t2)), spiral_reference_z(t2)])
                sphere(r = spiral_reference_tube_mm, $fn = 12);
        }
    }
}

// ----------------------------
// Render dispatch
// ----------------------------

if (render_mode == "all_presets")
    render_all_presets();
else if (render_mode == "harmonic_ladder")
    render_harmonic_ladder();
else if (render_mode == "collector_only")
    square_pyramid_shell(height_mm = selected_length() * collector_height_ratio_of_crystal, slope_deg = collector_slope_deg, wall_mm = collector_wall_mm);
else if (render_mode == "spiral_reference")
    spiral_reference_path();
else if (render_mode == "compact_mode_crystal") {
    // v7: rings enabled via effective_show_compact_mode_rings (D-02 fix)
    render_current(str(selected_preset, "_compact_modes"));
}
else {
    render_current(selected_preset);
    if (show_spiral_reference_next_to_crystal)
        translate([selected_widths()[0] + spiral_reference_radius_mm + 12, 0, 0]) spiral_reference_path();
}
