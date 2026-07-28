/*
  Vogel / Eredyon-style faceted quartz representative model generator v7
  Scale-A 4096 Hz bulk-acoustic candidate integration
  ----------------------------------------------------------------------
  Units: millimetres.

  This file is a geometry and calculation aid. It does not assert that the
  finished crystal will resonate at the requested frequency. The exact mode
  depends on anisotropic material tensors, crystal orientation, termination
  reflection, electrodes, supports, temperature, stress, and machining.

  v7 additions:
    - ScaleA_4096Hz_Shear_463p867mm_6sided preset.
    - Exact effective half-wave path calculation from f = v/(2L).
    - Separate effective acoustic path and nominal CAD tip-to-tip length.
    - Shear and longitudinal working branch controls.
    - Manufacturing envelope and axis-reference helpers.
    - Design-sheet echo output with geometry, volume, mass, and unresolved data.
    - R10.15 boundary: 4096 Hz is not treated as the electromagnetic
      surface-wave carrier.

  Default angle convention:
    face_slope = angle between termination face and its base plane.

  Default diameter convention:
    across_vertices = maximum caliper width of the regular polygon.
*/

// ----------------------------
// OpenSCAD Customizer controls
// ----------------------------

/* [Render] */
render_mode = "single"; // [single, design_sheet, acoustic_path_reference, harmonic_ladder, collector_only, compact_mode_crystal]
model_scale = 1.0; // [0.01:0.01:3]
spacing_mm = 130; // [30:5:800]

/* [Preset] */
selected_preset = "ScaleA_4096Hz_Shear_463p867mm_6sided"; // [ScaleA_4096Hz_Shear_463p867mm_6sided, ScaleA_4096Hz_Longitudinal_695p801mm_6sided_Control, Custom, Himalayan_157mm_8sided, Ideal_N5_154mm_6sided_ratio, Prototype_153mm_6sided, Prototype_152mm_6sided, Prototype_101mm_6sided, Ideal_N6_128mm_6sided_ratio, Ideal_N7_110mm_6sided_ratio, Ideal_N9_86mm_6sided_ratio, Himalayan_125mm_8sided, Himalayan_125mm_12sided, Citrine_71mm_24sided, Citrine_81mm_8sided, Smoky_62mm_24sided, Rutilated_86mm_24sided]

/* [Acoustic path candidate] */
sizing_mode = "preset_dimensions"; // [preset_dimensions, ratio_from_length, ideal_half_wave_branch, ideal_4096_harmonic]
target_frequency_hz = 4096; // [1:1:10000000]
acoustic_branch = "shear_proxy"; // [shear_proxy, longitudinal_proxy, custom_velocity]
quartz_shear_velocity_m_s = 3800; // [2500:1:5000]
quartz_longitudinal_velocity_m_s = 5700; // [4500:1:7000]
custom_phase_velocity_m_s = 3800; // [100:1:10000]
harmonic_N = 1; // [1:1:128]
effective_path_correction_mm = 0; // [-100:0.001:100]
nominal_body_minus_effective_path_mm = 0; // [-100:0.001:100]

/* [Ratio geometry] */
length_to_avg_diameter = 6.0; // [2:0.1:20]
wide_to_narrow_ratio = 1.6; // [1:0.01:4]

/* [Custom geometry] */
custom_length_mm = 463.8671875; // [20:0.001:1000]
custom_sides = 6; // [3:1:48]
custom_wide_d_mm = 95.15224359; // [3:0.001:300]
custom_narrow_d_mm = 59.47015224; // [3:0.001:300]
custom_rx_angle_deg = 51.843; // [20:0.001:80]
custom_tx_angle_deg = 60; // [20:0.001:80]

/* [Geometry convention] */
angle_mode = "face_slope"; // [face_slope, apex_included, axis_to_face]
diameter_mode = "across_vertices"; // [across_vertices, across_flats]
facet_rotation_deg = 30; // [0:1:360]
use_angle_overrides = false;
rx_angle_override_deg = 51.843; // [20:0.001:80]
tx_angle_override_deg = 60; // [20:0.001:80]

/* [Material bookkeeping] */
quartz_density_g_cm3 = 2.65; // [2.5:0.001:2.8]
operating_temperature_C = 25; // [-50:0.1:300]
frequency_temperature_correction_ppm = 0; // [-10000:0.1:10000]

/* [Manufacturing envelope, visual only] */
show_manufacturing_envelope = false;
blank_radial_allowance_mm = 5; // [0:0.1:30]
blank_end_allowance_mm = 5; // [0:0.1:30]
show_axis_reference = true;
axis_rod_radius_mm = 0.75; // [0.1:0.05:5]
axis_reference_offset_mm = 25; // [5:1:200]

/* [Markers] */
show_metric_center_marker = true;
show_geometry_eye_marker = true;
geometry_eye_fraction_from_female = 0.50; // [0:0.001:1]
show_measured_eye_marker = false;
measured_eye_from_female_mm = 231.93359375; // [0:0.001:1000]
marker_width_mm = 1.2; // [0.1:0.1:10]
metric_marker_radius_extra_mm = 0.5; // [0.1:0.05:5]
geometry_marker_radius_extra_mm = 1.0; // [0.1:0.05:5]
measured_marker_radius_extra_mm = 1.5; // [0.1:0.05:5]

/* [Compact mode references] */
show_compact_mode_rings = false;
compact_mode_count = 12; // [1:1:64]
compact_mode_parity = "all"; // [all, odd, even]
compact_ring_width_mm = 0.7; // [0.1:0.05:5]
compact_ring_radius_extra_mm = 0.7; // [0.1:0.05:5]

/* [Coil reference, visual only] */
show_coil_reference = false;
coil_turns = 40; // [1:1:300]
coil_wire_d_mm = 1.0; // [0.1:0.05:10]
coil_clearance_mm = 6.0; // [0:0.1:50]
coil_phase_deg = 0; // [0:1:360]
show_counter_coil = true;

/* [Collector reference, visual only] */
show_pyramid_collector = false;
collector_slope_deg = 52; // [20:0.1:80]
collector_height_ratio_of_crystal = 0.20; // [0.05:0.01:1]
collector_gap_above_tip_mm = 5; // [0:0.1:100]
collector_wall_mm = 2; // [0.2:0.1:20]

$fn = 96;

// ----------------------------
// Preset data
// [L, sides, wide, narrow, rx, tx, branch_name, velocity_m_s, target_hz]
// ----------------------------

function preset_values(p) =
    p == "ScaleA_4096Hz_Shear_463p867mm_6sided" ?
        [463.8671875, 6, 95.1522435897, 59.4701522436, 51.843, 60, "shear_proxy", 3800, 4096] :
    p == "ScaleA_4096Hz_Longitudinal_695p801mm_6sided_Control" ?
        [695.80078125, 6, 142.728365385, 89.2052283654, 51.843, 60, "longitudinal_proxy", 5700, 4096] :
    p == "Himalayan_157mm_8sided" ?
        [157, 8, 32, 20, 51.843, 60, "unspecified", 0, 0] :
    p == "Ideal_N5_154mm_6sided_ratio" ?
        [154.052734375, 6, 31.6005608974, 19.7503505609, 51.843, 60, "legacy_longitudinal_proxy", 6310, 4096*5] :
    p == "Prototype_153mm_6sided" ?
        [153, 6, 32, 20, 51.843, 60, "unspecified", 0, 0] :
    p == "Prototype_152mm_6sided" ?
        [152, 6, 32, 20, 51.843, 60, "unspecified", 0, 0] :
    p == "Prototype_101mm_6sided" ?
        [101, 6, 22, 16, 51.843, 60, "unspecified", 0, 0] :
    p == "Ideal_N6_128mm_6sided_ratio" ?
        [128.377278646, 6, 26.333800748, 16.458625468, 51.843, 60, "legacy_longitudinal_proxy", 6310, 4096*6] :
    p == "Ideal_N7_110mm_6sided_ratio" ?
        [110.037667411, 6, 22.571829213, 14.107393258, 51.843, 60, "legacy_longitudinal_proxy", 6310, 4096*7] :
    p == "Ideal_N9_86mm_6sided_ratio" ?
        [85.584852431, 6, 17.555867165, 10.972416978, 51.843, 60, "legacy_longitudinal_proxy", 6310, 4096*9] :
    p == "Himalayan_125mm_8sided" ?
        [125, 8, 21, 14, 51.843, 60, "unspecified", 0, 0] :
    p == "Himalayan_125mm_12sided" ?
        [125, 12, 20, 16, 51.843, 60, "unspecified", 0, 0] :
    p == "Citrine_71mm_24sided" ?
        [71, 24, 20, 15, 51.843, 60, "unspecified", 0, 0] :
    p == "Citrine_81mm_8sided" ?
        [81, 8, 19, 15, 51.843, 60, "unspecified", 0, 0] :
    p == "Smoky_62mm_24sided" ?
        [62, 24, 21, 17, 51.843, 60, "unspecified", 0, 0] :
    p == "Rutilated_86mm_24sided" ?
        [86, 24, 35, 29, 51.843, 60, "unspecified", 0, 0] :
        [custom_length_mm, custom_sides, custom_wide_d_mm, custom_narrow_d_mm,
         custom_rx_angle_deg, custom_tx_angle_deg, acoustic_branch,
         selected_velocity_m_s(), target_frequency_hz];

function selected_velocity_m_s() =
    acoustic_branch == "longitudinal_proxy" ? quartz_longitudinal_velocity_m_s :
    acoustic_branch == "custom_velocity" ? custom_phase_velocity_m_s :
    quartz_shear_velocity_m_s;

function ideal_half_wave_path_mm(v_m_s, f_hz, N=1) =
    v_m_s / (2 * f_hz * N) * 1000 + effective_path_correction_mm;

function ratio_widths_from_length(L, ld=6, taper=1.6) =
    let(avg = L / ld, narrow = 2 * avg / (1 + taper), wide = taper * narrow)
    [wide, narrow];

function selected_raw() = preset_values(selected_preset);

function selected_effective_path_mm() =
    sizing_mode == "ideal_half_wave_branch" ?
        ideal_half_wave_path_mm(selected_velocity_m_s(), target_frequency_hz, harmonic_N) :
    sizing_mode == "ideal_4096_harmonic" ?
        ideal_half_wave_path_mm(quartz_longitudinal_velocity_m_s, 4096, harmonic_N) :
    selected_raw()[0] - nominal_body_minus_effective_path_mm;

function selected_length_mm() =
    (sizing_mode == "ideal_half_wave_branch" || sizing_mode == "ideal_4096_harmonic") ?
        selected_effective_path_mm() + nominal_body_minus_effective_path_mm :
    selected_preset == "Custom" ? custom_length_mm : selected_raw()[0];

function selected_sides() =
    selected_preset == "Custom" ? custom_sides : selected_raw()[1];

function selected_widths() =
    (sizing_mode == "ratio_from_length" ||
     sizing_mode == "ideal_half_wave_branch" ||
     sizing_mode == "ideal_4096_harmonic") ?
        ratio_widths_from_length(selected_length_mm(), length_to_avg_diameter, wide_to_narrow_ratio) :
    selected_preset == "Custom" ? [custom_wide_d_mm, custom_narrow_d_mm] :
        [selected_raw()[2], selected_raw()[3]];

function selected_rx() =
    use_angle_overrides ? rx_angle_override_deg :
    selected_preset == "Custom" ? custom_rx_angle_deg : selected_raw()[4];

function selected_tx() =
    use_angle_overrides ? tx_angle_override_deg :
    selected_preset == "Custom" ? custom_tx_angle_deg : selected_raw()[5];

// ----------------------------
// Geometry functions
// ----------------------------

function circumradius_from_diameter(d, n, mode) =
    mode == "across_flats" ? (d/2) / cos(180/n) : d/2;

function apothem_from_R(R, n) = R * cos(180/n);
function polygon_area_from_R(R, n) = n/2 * R*R * sin(360/n);

function cap_height_from_angle(d, n, angle_deg, mode, dmode) =
    let(R = circumradius_from_diameter(d, n, dmode),
        a = apothem_from_R(R, n))
    mode == "apex_included" ? a / tan(angle_deg/2) :
    mode == "axis_to_face"  ? a / tan(angle_deg) :
                              a * tan(angle_deg);

function ring_points(n, R, z, rot) =
    [for (i=[0:n-1]) [R*cos(rot+360*i/n), R*sin(rot+360*i/n), z]];

function crystal_faces(n) =
    concat(
        [for (i=[0:n-1]) [0, 1+((i+1)%n), 1+i]],
        [for (i=[0:n-1]) [1+i, 1+((i+1)%n), 1+n+((i+1)%n), 1+n+i]],
        [for (i=[0:n-1]) [1+2*n, 1+n+i, 1+n+((i+1)%n)]]
    );

function radius_at_z(z, L, rx_h, tx_h, Rw, Rn) =
    z <= rx_h ? max(Rw*z/max(rx_h,0.001),0) :
    z >= L-tx_h ? max(Rn*(L-z)/max(tx_h,0.001),0) :
    Rw + (Rn-Rw)*((z-rx_h)/max(L-rx_h-tx_h,0.001));

function volume_mm3(L,n,wide_d,narrow_d,rx_deg,tx_deg,amode,dmode) =
    let(
        Rw = circumradius_from_diameter(wide_d,n,dmode),
        Rn = circumradius_from_diameter(narrow_d,n,dmode),
        Aw = polygon_area_from_R(Rw,n),
        An = polygon_area_from_R(Rn,n),
        hr = cap_height_from_angle(wide_d,n,rx_deg,amode,dmode),
        ht = cap_height_from_angle(narrow_d,n,tx_deg,amode,dmode),
        hs = L-hr-ht
    )
    hs/3*(Aw+An+sqrt(Aw*An)) + Aw*hr/3 + An*ht/3;

// ----------------------------
// Main crystal
// ----------------------------

module vogel_crystal(L,n,wide_d,narrow_d,rx_deg,tx_deg,label="model") {
    Rw = circumradius_from_diameter(wide_d,n,diameter_mode);
    Rn = circumradius_from_diameter(narrow_d,n,diameter_mode);
    hr = cap_height_from_angle(wide_d,n,rx_deg,angle_mode,diameter_mode);
    ht = cap_height_from_angle(narrow_d,n,tx_deg,angle_mode,diameter_mode);
    hs = L-hr-ht;
    vol_cm3 = volume_mm3(L,n,wide_d,narrow_d,rx_deg,tx_deg,angle_mode,diameter_mode)/1000;
    mass_g = vol_cm3*quartz_density_g_cm3;
    effective_path = selected_effective_path_mm();
    selected_v = selected_preset == "Custom" ? selected_velocity_m_s() :
                 selected_raw()[7] > 0 ? selected_raw()[7] : selected_velocity_m_s();
    proxy_frequency = selected_v > 0 && effective_path > 0 ?
                      selected_v/(2*(effective_path/1000)*harmonic_N) : 0;

    echo("--------------------------------------------------");
    echo(str("MODEL=",label));
    echo(str("STATUS=GEOMETRY_AND_HALF_WAVE_PROXY_ONLY"));
    echo(str("L_tip_to_tip=",L," mm"));
    echo(str("L_effective_candidate=",effective_path," mm"));
    echo(str("facets=",n,", wide=",wide_d," mm, narrow=",narrow_d," mm"));
    echo(str("angles_rx_tx=",rx_deg,"/",tx_deg," deg"));
    echo(str("rx_cap=",hr," mm, shaft=",hs," mm, tx_cap=",ht," mm"));
    echo(str("volume=",vol_cm3," cm3, mass_proxy=",mass_g," g"));
    echo(str("working_velocity=",selected_v," m/s, harmonic_N=",harmonic_N));
    echo(str("half_wave_frequency_proxy=",proxy_frequency," Hz"));
    echo(str("temperature_C=",operating_temperature_C,
             ", frequency_temperature_input_ppm=",frequency_temperature_correction_ppm));
    echo("NONCLAIM: this is not a measured resonance or validated mode.");
    echo("NONCLAIM: 4096 Hz is not the R10.15 electromagnetic surface-wave carrier.");
    echo("REQUIRED: full anisotropic eigenmode, fixture, electrode, thermal, and uncertainty solve.");
    echo("--------------------------------------------------");

    assert(n >= 3, "Facet count must be at least 3.");
    assert(hs > 0, "Termination heights exceed total body length.");
    assert(L > 0 && wide_d > 0 && narrow_d > 0, "All dimensions must be positive.");

    pts = concat(
        [[0,0,0]],
        ring_points(n,Rw,hr,facet_rotation_deg),
        ring_points(n,Rn,L-ht,facet_rotation_deg),
        [[0,0,L]]
    );

    union() {
        polyhedron(points=pts,faces=crystal_faces(n),convexity=10);

        if (show_metric_center_marker)
            node_marker(L/2,L,n,hr,ht,Rw,Rn,metric_marker_radius_extra_mm,"metric_center");
        if (show_geometry_eye_marker)
            node_marker(L*geometry_eye_fraction_from_female,L,n,hr,ht,Rw,Rn,geometry_marker_radius_extra_mm,"geometry_estimate");
        if (show_measured_eye_marker)
            node_marker(measured_eye_from_female_mm,L,n,hr,ht,Rw,Rn,measured_marker_radius_extra_mm,"measured_input");
        if (show_compact_mode_rings)
            compact_mode_rings(L,n,hr,ht,Rw,Rn);
    }
}

module node_marker(z,L,n,hr,ht,Rw,Rn,extra,label="node") {
    zs = min(max(z,0),L);
    r = radius_at_z(zs,L,hr,ht,Rw,Rn);
    echo(str("NODE_MARKER=",label,", z=",zs," mm, fraction=",zs/L));
    translate([0,0,zs-marker_width_mm/2])
        difference() {
            cylinder(h=marker_width_mm,r=r+extra,$fn=n*8);
            translate([0,0,-0.1])
                cylinder(h=marker_width_mm+0.2,r=max(r-0.05,0.1),$fn=n*8);
        }
}

module compact_mode_rings(L,n,hr,ht,Rw,Rn) {
    for (k=[1:compact_mode_count]) {
        allowed = compact_mode_parity == "all" ||
                  (compact_mode_parity == "odd" && k%2==1) ||
                  (compact_mode_parity == "even" && k%2==0);
        if (allowed) {
            z = L*k/(compact_mode_count+1);
            r = radius_at_z(z,L,hr,ht,Rw,Rn);
            translate([0,0,z-compact_ring_width_mm/2])
                difference() {
                    cylinder(h=compact_ring_width_mm,r=r+compact_ring_radius_extra_mm,$fn=n*8);
                    translate([0,0,-0.05])
                        cylinder(h=compact_ring_width_mm+0.1,r=max(r-0.04,0.1),$fn=n*8);
                }
        }
    }
}

// ----------------------------
// Reference helpers
// ----------------------------

module axis_references(L,wide_d) {
    o = max(axis_reference_offset_mm,wide_d/2+10);
    color("red")
        translate([0,0,L/2]) rotate([0,90,0])
            cylinder(h=2*o,r=axis_rod_radius_mm,center=true,$fn=24);
    color("green")
        translate([0,0,L/2]) rotate([90,0,0])
            cylinder(h=2*o,r=axis_rod_radius_mm,center=true,$fn=24);
    color("blue")
        translate([0,0,L/2])
            cylinder(h=L+20,r=axis_rod_radius_mm,center=true,$fn=24);
}

module manufacturing_envelope(L,wide_d) {
    color([0.7,0.7,0.7,0.15])
        translate([0,0,-blank_end_allowance_mm])
            cylinder(
                h=L+2*blank_end_allowance_mm,
                r=wide_d/2+blank_radial_allowance_mm,
                $fn=96
            );
}

module coil_reference_helix(L,radius,turns,wire_d,phase=0) {
    steps=max(turns*20,40);
    for (i=[0:steps]) {
        t=i/steps;
        a=phase+360*turns*t;
        translate([radius*cos(a),radius*sin(a),L*t])
            sphere(r=wire_d/2,$fn=12);
    }
}

module square_pyramid_shell(height_mm=30,slope_deg=52,wall_mm=2) {
    hb=height_mm/tan(slope_deg);
    hi=max(height_mm-wall_mm,0.1);
    hbi=max(hb-wall_mm,0.1);
    difference() {
        polyhedron(
            points=[[-hb,-hb,0],[hb,-hb,0],[hb,hb,0],[-hb,hb,0],[0,0,height_mm]],
            faces=[[0,1,2,3],[0,4,1],[1,4,2],[2,4,3],[3,4,0]],
            convexity=10
        );
        translate([0,0,-0.05])
            polyhedron(
                points=[[-hbi,-hbi,0],[hbi,-hbi,0],[hbi,hbi,0],[-hbi,hbi,0],[0,0,hi]],
                faces=[[0,1,2,3],[0,4,1],[1,4,2],[2,4,3],[3,4,0]],
                convexity=10
            );
    }
}

module acoustic_path_reference(L) {
    color([0.15,0.4,1.0,0.8])
        cylinder(h=L,r=1.2,$fn=24);
    for (f=[0,0.25,0.5,0.75,1])
        translate([0,0,L*f])
            color([1.0,0.3,0.1,0.8])
                cylinder(h=0.8,r=8,$fn=48);
}

module design_sheet() {
    L=selected_length_mm();
    n=selected_sides();
    w=selected_widths();
    RX=selected_rx();
    TX=selected_tx();

    render_current("design_sheet_crystal");
    translate([w[0]*1.8,0,0])
        acoustic_path_reference(selected_effective_path_mm());
    translate([-w[0]*1.8,0,0])
        manufacturing_envelope(L,w[0]);
}

// ----------------------------
// Dispatch
// ----------------------------

module render_current(label="current") {
    L=selected_length_mm();
    n=selected_sides();
    w=selected_widths();
    RX=selected_rx();
    TX=selected_tx();

    scale([model_scale,model_scale,model_scale]) {
        color([0.82,0.94,1.0,0.62])
            vogel_crystal(L,n,w[0],w[1],RX,TX,label);

        if (show_axis_reference)
            axis_references(L,w[0]);

        if (show_manufacturing_envelope)
            manufacturing_envelope(L,w[0]);

        if (show_pyramid_collector) {
            ch=L*collector_height_ratio_of_crystal;
            translate([0,0,L+collector_gap_above_tip_mm])
                square_pyramid_shell(ch,collector_slope_deg,collector_wall_mm);
        }

        if (show_coil_reference) {
            cr=max(w[0],w[1])/2+coil_clearance_mm;
            coil_reference_helix(L,cr,coil_turns,coil_wire_d_mm,coil_phase_deg);
            if (show_counter_coil)
                coil_reference_helix(L,cr+2,coil_turns,coil_wire_d_mm,coil_phase_deg+180);
        }
    }
}

module harmonic_ladder() {
    for (i=[1:8]) {
        Li=ideal_half_wave_path_mm(selected_velocity_m_s(),target_frequency_hz,i);
        wi=ratio_widths_from_length(Li,length_to_avg_diameter,wide_to_narrow_ratio);
        translate([(i-1)%4*spacing_mm,floor((i-1)/4)*spacing_mm,0])
            vogel_crystal(Li,custom_sides,wi[0],wi[1],selected_rx(),selected_tx(),str("harmonic_N_",i));
    }
}

if (render_mode == "design_sheet")
    design_sheet();
else if (render_mode == "acoustic_path_reference")
    acoustic_path_reference(selected_effective_path_mm());
else if (render_mode == "harmonic_ladder")
    harmonic_ladder();
else if (render_mode == "collector_only")
    square_pyramid_shell(
        selected_length_mm()*collector_height_ratio_of_crystal,
        collector_slope_deg,
        collector_wall_mm
    );
else if (render_mode == "compact_mode_crystal") {
    show_compact_mode_rings = true;
    render_current(str(selected_preset,"_compact_modes"));
}
else
    render_current(selected_preset);
