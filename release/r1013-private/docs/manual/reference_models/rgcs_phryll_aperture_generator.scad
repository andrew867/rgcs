// RGCS R10.13 parametric reference model.
// Units: millimetres.
// Status: geometry hypothesis only. Not a validated apparatus.

$fn = 96;

scale_factor = 1.0;
r_outer = 144.109699835 * scale_factor;
r_inner = 82.261610772 * scale_factor;
plate_thickness = 4.0 * scale_factor;
aperture_count = 35;
gap_indices = [0, 18];
aperture_diameter = 6.0 * scale_factor;
crystal_length = 77.8 * scale_factor;
crystal_wide_diameter = 30.2 * scale_factor;
crystal_narrow_diameter = 24.0 * scale_factor;
facets = 6;
female_angle_deg = 51.843;
male_angle_deg = 60.0;
plate_z = 0;
crystal_z = -crystal_length/2;

function is_gap(i) = len(search(i, gap_indices)) > 0;

module aperture_plate() {
    difference() {
        cylinder(h=plate_thickness, r=r_outer, center=true);
        cylinder(h=plate_thickness + 2, r=r_inner, center=true);
        for (i = [0:aperture_count-1]) {
            if (!is_gap(i)) {
                a = 360*i/aperture_count;
                rr = (r_inner + r_outer)/2;
                translate([rr*cos(a), rr*sin(a), 0])
                    cylinder(h=plate_thickness + 2, d=aperture_diameter, center=true);
            }
        }
    }
}

module frustum_between(z0, z1, r0, r1, n=6) {
    translate([0,0,z0])
        cylinder(h=z1-z0, r1=r0, r2=r1, center=false, $fn=n);
}

module vogel_crystal() {
    hf = crystal_wide_diameter/2 * cos(180/facets) * tan(female_angle_deg);
    hm = crystal_narrow_diameter/2 * cos(180/facets) * tan(male_angle_deg);
    shaft = crystal_length - hf - hm;
    if (shaft <= 0) {
        echo("ERROR: termination heights exceed total crystal length");
    } else {
        translate([0,0,crystal_z]) {
            cylinder(h=hf, r1=0, r2=crystal_wide_diameter/2, $fn=facets);
            frustum_between(hf, hf+shaft, crystal_wide_diameter/2, crystal_narrow_diameter/2, facets);
            translate([0,0,hf+shaft])
                cylinder(h=hm, r1=crystal_narrow_diameter/2, r2=0, $fn=facets);
        }
    }
}

module torus_preview(R, a) {
    rotate_extrude($fn=128)
        translate([R,0,0]) circle(r=a, $fn=48);
}

module complete_generator() {
    color([0.75,0.45,0.15,0.8]) translate([0,0,plate_z]) aperture_plate();
    color([0.85,0.95,1.0,0.55]) vogel_crystal();
}

complete_generator();
