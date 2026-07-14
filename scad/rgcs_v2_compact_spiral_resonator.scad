/*
  RGCS v2 compact-coordinate spiral resonator
  ------------------------------------------------------------
  A printable / visual 3D projection of the scale-rotation model

    X(theta) = [r cos(theta), r sin(theta), z(theta), chi(theta)]
    r(theta) = R exp(-a theta)
    a = ln(q)/(2 pi)
    z(theta) = H [1 - (r/R)^p]
    chi(theta) = phase_cycles * theta mod 2 pi

  The fourth coordinate chi is represented by phase-colored / phase-marked
  rings in the 3D projection.  The compact-mode markers are a design aid for
  testing discrete phase/path mode indices. They are not a claim that the
  printed object is a physical extra dimension.

  Units: millimeters.
*/

/* [Render] */
render_mode = "spiral_tube"; // [spiral_tube, spiral_with_mode_markers, cone_shell, flat_projection, controls_grid]
$fn = 48;

/* [Spiral geometry] */
q_per_turn = 2.718281828; // [1.01:0.01:8]
turns = 4; // [0.5:0.25:12]
outer_radius_mm = 60; // [5:1:200]
height_mm = 80; // [5:1:300]
cone_exponent = 1.5; // [0.25:0.05:5]
inner_cutoff_mm = 0.8; // [0.1:0.1:10]
steps = 360; // [48:12:1200]

/* [Tube / shell] */
tube_radius_mm = 1.2; // [0.2:0.1:8]
cone_wall_mm = 1.2; // [0.3:0.1:5]
flat_plate_thickness_mm = 1.2; // [0.3:0.1:5]

/* [Compact phase / mode markers] */
phase_cycles_per_theta = 1; // [0.25:0.25:8]
mode_index_max = 12; // [1:1:32]
mode_parity = "all"; // [all, odd, even]
marker_radius_mm = 1.8; // [0.3:0.1:8]
marker_every_mode = 1; // [1:1:8]
show_phase_axis = true;

/* [Controls grid] */
control_spacing_mm = 150; // [60:10:300]

function a_scale(q) = ln(q)/(2*PI);
function r_at_theta(th) = max(inner_cutoff_mm, outer_radius_mm*exp(-a_scale(q_per_turn)*th));
function z_at_theta(th) = height_mm*(1-pow(r_at_theta(th)/outer_radius_mm, cone_exponent));
function p3(th) = [r_at_theta(th)*cos(th*180/PI), r_at_theta(th)*sin(th*180/PI), z_at_theta(th)];
function include_mode(n) = mode_parity == "all" || (mode_parity == "odd" && n%2==1) || (mode_parity == "even" && n%2==0);
function theta_for_mode(n) = 2*PI*turns*n/mode_index_max;

module segment(a,b,r=tube_radius_mm) {
    hull() {
        translate(a) sphere(r=r,$fn=16);
        translate(b) sphere(r=r,$fn=16);
    }
}

module spiral_path() {
    echo(str("RGCS_V2 q=",q_per_turn," a=",a_scale(q_per_turn)," turns=",turns));
    for(i=[0:steps-1]) {
        th1=2*PI*turns*i/steps;
        th2=2*PI*turns*(i+1)/steps;
        segment(p3(th1),p3(th2));
    }
}

module mode_markers() {
    for(n=[1:mode_index_max]) if(include_mode(n) && n%marker_every_mode==0) {
        th=theta_for_mode(n);
        pt=p3(th);
        echo(str("MODE_MARKER n=",n," parity=",n%2==0?"even":"odd"," theta=",th," point=",pt));
        translate(pt) sphere(r=marker_radius_mm,$fn=24);
    }
}

module phase_axis() {
    if(show_phase_axis) {
        color("gray") translate([0,0,height_mm/2]) cylinder(h=height_mm,r=0.6,center=true,$fn=16);
        for(k=[0:mode_index_max]) {
            z=height_mm*k/mode_index_max;
            translate([0,0,z]) cylinder(h=0.5,r=2.2,$fn=32);
        }
    }
}

module cone_shell() {
    difference() {
        cylinder(h=height_mm,r1=outer_radius_mm,r2=inner_cutoff_mm,$fn=steps);
        translate([0,0,cone_wall_mm])
            cylinder(h=height_mm,r1=max(outer_radius_mm-cone_wall_mm,0.1),r2=max(inner_cutoff_mm-cone_wall_mm/2,0.1),$fn=steps);
    }
}

module flat_projection() {
    linear_extrude(height=flat_plate_thickness_mm)
        union() {
            for(i=[0:steps-1]) {
                th1=2*PI*turns*i/steps;
                th2=2*PI*turns*(i+1)/steps;
                hull() {
                    translate([r_at_theta(th1)*cos(th1*180/PI),r_at_theta(th1)*sin(th1*180/PI)]) circle(r=tube_radius_mm,$fn=16);
                    translate([r_at_theta(th2)*cos(th2*180/PI),r_at_theta(th2)*sin(th2*180/PI)]) circle(r=tube_radius_mm,$fn=16);
                }
            }
        }
}

module archimedean_control() {
    for(i=[0:steps-1]) {
        th1=2*PI*turns*i/steps;
        th2=2*PI*turns*(i+1)/steps;
        r1=outer_radius_mm*(1-i/steps);
        r2=outer_radius_mm*(1-(i+1)/steps);
        z1=height_mm*i/steps;
        z2=height_mm*(i+1)/steps;
        segment([r1*cos(th1*180/PI),r1*sin(th1*180/PI),z1],[r2*cos(th2*180/PI),r2*sin(th2*180/PI),z2]);
    }
}

if(render_mode=="spiral_tube") {
    spiral_path(); phase_axis();
} else if(render_mode=="spiral_with_mode_markers") {
    spiral_path(); mode_markers(); phase_axis();
} else if(render_mode=="cone_shell") {
    cone_shell();
} else if(render_mode=="flat_projection") {
    flat_projection();
} else if(render_mode=="controls_grid") {
    translate([-control_spacing_mm/2,0,0]) { spiral_path(); mode_markers(); }
    translate([control_spacing_mm/2,0,0]) archimedean_control();
    translate([0,control_spacing_mm,0]) cone_shell();
    translate([0,-control_spacing_mm,0]) flat_projection();
}
