// RGCS-ARDK-001 RevA fixture. Mechanical geometry only.
// PUBLICATION_HOLD; no mechanical rotation.
base_outer_d = 320;
base_inner_clearance_d = 180;
base_thickness = 8;
spacer_height = 12;
probe_radius = 119;
probe_hole_d = 2.2;
sector_count = 37;
pcb_mount_radius = 136;
pcb_mount_hole_d = 3.2;

module base_plate() {
    difference() {
        cylinder(d=base_outer_d, h=base_thickness, $fn=256);
        translate([0,0,-0.1]) cylinder(d=base_inner_clearance_d, h=base_thickness+0.2, $fn=256);
        for (i=[0:sector_count-1]) {
            rotate([0,0,360*i/sector_count])
                translate([probe_radius,0,-0.1])
                    cylinder(d=probe_hole_d, h=base_thickness+0.2, $fn=24);
        }
        for (a=[45,135,225,315]) {
            rotate([0,0,a]) translate([pcb_mount_radius,0,-0.1])
                cylinder(d=pcb_mount_hole_d, h=base_thickness+0.2, $fn=32);
        }
    }
}

module center_ptfe_sleeve() {
    difference() {
        cylinder(d=18, h=30, $fn=64);
        translate([0,0,-0.1]) cylinder(d=8, h=30.2, $fn=64);
    }
}

module dielectric_spacer(angle_deg) {
    rotate([0,0,angle_deg]) translate([pcb_mount_radius,0,base_thickness])
        difference() {
            cylinder(d=8, h=spacer_height, $fn=32);
            translate([0,0,-0.1]) cylinder(d=pcb_mount_hole_d, h=spacer_height+0.2, $fn=32);
        }
}

base_plate();
center_ptfe_sleeve();
for (a=[45,135,225,315]) dielectric_spacer(a);
