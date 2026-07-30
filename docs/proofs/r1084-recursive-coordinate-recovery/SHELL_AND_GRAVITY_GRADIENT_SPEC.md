# Shell and gravity-gradient spec (R10.8.4 SS6)

Baseline: g(r) = mu / r^2, dg/dr = -2 mu / r^3 (Newtonian, conventional; PHYSICAL_ANOMALOUS_GRAVITY_VALIDATED: no). Radial root intervals are DECLARED profiles (finite ambiguity), not derived facts; every radial statement below is conditional on its profile. Z-path for the training vector is (5, 6, 3).

Layer-size hypothesis (SS6.2): base-10 nested subdivision gives ratio_dr_over_r ~ 1/10 per level by construction; the tables show fractional gravity change and potential step both track that 1/10 (none is independently conserved), and the log-radius step ratio departs from all candidates. No conserved-quantity candidate is selected.

```json
{
 "ROOT_R0_FULL_DIAMETER": {
  "shells": [
   {
    "shell_id": "L1_z5",
    "radial_bounds_km": [
     6371.0,
     7645.2
    ],
    "midpoint_radius_km": 7008.1,
    "altitude_bounds_km": [
     0.0,
     1274.1999999999998
    ],
    "radial_thickness_km": 1274.1999999999998,
    "g_inner_m_s2": 9.820250487063928,
    "g_midpoint_m_s2": 8.115909493441263,
    "g_outer_m_s2": 6.819618393794395,
    "abs_gravity_change_m_s2": 3.0006320932695343,
    "gravity_change_midpoint_approx_m_s2": 2.9512398157968223,
    "fractional_gravity_change": 0.3697222222222223,
    "radial_gradient_mid_s2": -2.3161511660624886e-06
   },
   {
    "shell_id": "L2_z6",
    "radial_bounds_km": [
     7135.52,
     7262.94
    ],
    "midpoint_radius_km": 7199.23,
    "altitude_bounds_km": [
     764.5200000000004,
     891.9399999999996
    ],
    "radial_thickness_km": 127.41999999999916,
    "g_inner_m_s2": 7.82864356430479,
    "g_midpoint_m_s2": 7.69069659884402,
    "g_outer_m_s2": 7.556363871240326,
    "abs_gravity_change_m_s2": 0.27227969306446387,
    "gravity_change_midpoint_approx_m_s2": 0.2722370477466891,
    "fractional_gravity_change": 0.03540377514117381,
    "radial_gradient_mid_s2": -2.1365331011355434e-06
   },
   {
    "shell_id": "L3_z3",
    "radial_bounds_km": [
     7173.746,
     7186.488
    ],
    "midpoint_radius_km": 7180.117,
    "altitude_bounds_km": [
     802.7460000000001,
     815.4880000000003
    ],
    "radial_thickness_km": 12.74200000000019,
    "g_inner_m_s2": 7.745434480236181,
    "g_midpoint_m_s2": 7.731695353042036,
    "g_outer_m_s2": 7.717992749880483,
    "abs_gravity_change_m_s2": 0.02744173035569931,
    "gravity_change_midpoint_approx_m_s2": 0.02744168714478137,
    "fractional_gravity_change": 0.0035492513740731342,
    "radial_gradient_mid_s2": -2.1536404916638647e-06
   }
  ],
  "hypothesis_rows": [
   {
    "from_shell": "L1_z5",
    "to_shell": "L2_z6",
    "ratio_dr_over_r": 0.09734513274336222,
    "ratio_dg_over_g": 0.09575776897687881,
    "ratio_potential_step": 0.09476074868822869,
    "ratio_log_radius_step": 0.09707890504359569,
    "gamma_L_r": 0.2722370477466891
   },
   {
    "from_shell": "L2_z6",
    "to_shell": "L3_z3",
    "ratio_dr_over_r": 0.10026619343389744,
    "ratio_dg_over_g": 0.10025064728042048,
    "ratio_potential_step": 0.10053309545723522,
    "ratio_log_radius_step": 0.10026360225457318,
    "gamma_L_r": 0.02744168714478137
   }
  ],
  "stonehenge_radius_compatible": false
 },
 "ROOT_R1_BODY_INTERIOR": {
  "shells": [
   {
    "shell_id": "L1_z5",
    "radial_bounds_km": [
     3185.5,
     3822.6
    ],
    "midpoint_radius_km": 3504.05,
    "altitude_bounds_km": [
     -3185.5,
     -2548.4
    ],
    "radial_thickness_km": 637.0999999999999,
    "g_inner_m_s2": 39.281001948255714,
    "g_midpoint_m_s2": 32.46363797376505,
    "g_outer_m_s2": 27.27847357517758,
    "abs_gravity_change_m_s2": 12.002528373078137,
    "gravity_change_midpoint_approx_m_s2": 11.804959263187289,
    "fractional_gravity_change": 0.3697222222222223,
    "radial_gradient_mid_s2": -1.852920932849991e-05
   },
   {
    "shell_id": "L2_z6",
    "radial_bounds_km": [
     3567.76,
     3631.47
    ],
    "midpoint_radius_km": 3599.615,
    "altitude_bounds_km": [
     -2803.24,
     -2739.53
    ],
    "radial_thickness_km": 63.70999999999958,
    "g_inner_m_s2": 31.31457425721916,
    "g_midpoint_m_s2": 30.76278639537608,
    "g_outer_m_s2": 30.225455484961305,
    "abs_gravity_change_m_s2": 1.0891187722578555,
    "gravity_change_midpoint_approx_m_s2": 1.0889481909867564,
    "fractional_gravity_change": 0.03540377514117381,
    "radial_gradient_mid_s2": -1.7092264809084347e-05
   },
   {
    "shell_id": "L3_z3",
    "radial_bounds_km": [
     3586.873,
     3593.244
    ],
    "midpoint_radius_km": 3590.0585,
    "altitude_bounds_km": [
     -2784.127,
     -2777.756
    ],
    "radial_thickness_km": 6.371000000000095,
    "g_inner_m_s2": 30.981737920944724,
    "g_midpoint_m_s2": 30.926781412168143,
    "g_outer_m_s2": 30.87197099952193,
    "abs_gravity_change_m_s2": 0.10976692142279725,
    "gravity_change_midpoint_approx_m_s2": 0.10976674857912548,
    "fractional_gravity_change": 0.0035492513740731342,
    "radial_gradient_mid_s2": -1.7229123933310917e-05
   }
  ],
  "hypothesis_rows": [
   {
    "from_shell": "L1_z5",
    "to_shell": "L2_z6",
    "ratio_dr_over_r": 0.09734513274336222,
    "ratio_dg_over_g": 0.09575776897687881,
    "ratio_potential_step": 0.09476074868822869,
    "ratio_log_radius_step": 0.09707890504359569,
    "gamma_L_r": 1.0889481909867564
   },
   {
    "from_shell": "L2_z6",
    "to_shell": "L3_z3",
    "ratio_dr_over_r": 0.10026619343389744,
    "ratio_dg_over_g": 0.10025064728042048,
    "ratio_potential_step": 0.10053309545723522,
    "ratio_log_radius_step": 0.10026360225457318,
    "gamma_L_r": 0.10976674857912548
   }
  ],
  "stonehenge_radius_compatible": false
 },
 "ROOT_R2_SURFACE_BAND_10PCT": {
  "shells": [
   {
    "shell_id": "L1_z5",
    "radial_bounds_km": [
     6371.0,
     6498.42
    ],
    "midpoint_radius_km": 6434.71,
    "altitude_bounds_km": [
     0.0,
     127.42000000000007
    ],
    "radial_thickness_km": 127.42000000000007,
    "g_inner_m_s2": 9.820250487063928,
    "g_midpoint_m_s2": 9.62675275665516,
    "g_outer_m_s2": 9.43891819210297,
    "abs_gravity_change_m_s2": 0.3813322949609603,
    "gravity_change_midpoint_approx_m_s2": 0.3812575349170363,
    "fractional_gravity_change": 0.03961172625913115,
    "radial_gradient_mid_s2": -2.992132592348423e-06
   },
   {
    "shell_id": "L2_z6",
    "radial_bounds_km": [
     6447.452,
     6460.194
    ],
    "midpoint_radius_km": 6453.823,
    "altitude_bounds_km": [
     76.45200000000023,
     89.19400000000041
    ],
    "radial_thickness_km": 12.74200000000019,
    "g_inner_m_s2": 9.588739949717938,
    "g_midpoint_m_s2": 9.569817921866601,
    "g_outer_m_s2": 9.550951848736942,
    "abs_gravity_change_m_s2": 0.0377881009809963,
    "gravity_change_midpoint_approx_m_s2": 0.03778802733214904,
    "fractional_gravity_change": 0.0039486750207286805,
    "radial_gradient_mid_s2": -2.9656276355476754e-06
   },
   {
    "shell_id": "L3_z3",
    "radial_bounds_km": [
     6451.2746,
     6452.5488
    ],
    "midpoint_radius_km": 6451.9117,
    "altitude_bounds_km": [
     80.27459999999974,
     81.54879999999957
    ],
    "radial_thickness_km": 1.274199999999837,
    "g_inner_m_s2": 9.57738000606142,
    "g_midpoint_m_s2": 9.575488644919437,
    "g_outer_m_s2": 9.5735978439871,
    "abs_gravity_change_m_s2": 0.003782162074318325,
    "gravity_change_midpoint_approx_m_s2": 0.0037821620005601716,
    "fractional_gravity_change": 0.0003949837146248473,
    "radial_gradient_mid_s2": -2.9682640092298346e-06
   }
  ],
  "hypothesis_rows": [
   {
    "from_shell": "L1_z5",
    "to_shell": "L2_z6",
    "ratio_dr_over_r": 0.09970384995064309,
    "ratio_dg_over_g": 0.09968449733539313,
    "ratio_potential_step": 0.09940857694980207,
    "ratio_log_radius_step": 0.09970062427516833,
    "gamma_L_r": 0.03778802733214904
   },
   {
    "from_shell": "L2_z6",
    "to_shell": "L3_z3",
    "ratio_dr_over_r": 0.10002962377800488,
    "ratio_dg_over_g": 0.10002943077142819,
    "ratio_potential_step": 0.10005925633170629,
    "ratio_log_radius_step": 0.10002959161024386,
    "gamma_L_r": 0.0037821620005601716
   }
  ],
  "stonehenge_radius_compatible": false
 },
 "ROOT_R3_ALTITUDE_0_1000KM": {
  "shells": [
   {
    "shell_id": "L1_z5",
    "radial_bounds_km": [
     6871.0,
     6971.0
    ],
    "midpoint_radius_km": 6921.0,
    "altitude_bounds_km": [
     500.0,
     600.0
    ],
    "radial_thickness_km": 100.0,
    "g_inner_m_s2": 8.443021178212767,
    "g_midpoint_m_s2": 8.321470486964774,
    "g_outer_m_s2": 8.202525897759394,
    "abs_gravity_change_m_s2": 0.2404952804533735,
    "gravity_change_midpoint_approx_m_s2": 0.24047017734329648,
    "fractional_gravity_change": 0.028900574823896696,
    "radial_gradient_mid_s2": -2.4047017734329647e-06
   },
   {
    "shell_id": "L2_z6",
    "radial_bounds_km": [
     6931.0,
     6941.0
    ],
    "midpoint_radius_km": 6936.0,
    "altitude_bounds_km": [
     560.0,
     570.0
    ],
    "radial_thickness_km": 10.0,
    "g_inner_m_s2": 8.297475486513902,
    "g_midpoint_m_s2": 8.28551688680425,
    "g_outer_m_s2": 8.273584121178938,
    "abs_gravity_change_m_s2": 0.023891365334962177,
    "gravity_change_midpoint_approx_m_s2": 0.023891340504049164,
    "fractional_gravity_change": 0.0028835093406196833,
    "radial_gradient_mid_s2": -2.3891340504049162e-06
   },
   {
    "shell_id": "L3_z3",
    "radial_bounds_km": [
     6934.0,
     6935.0
    ],
    "midpoint_radius_km": 6934.5,
    "altitude_bounds_km": [
     563.0,
     564.0
    ],
    "radial_thickness_km": 1.0,
    "g_inner_m_s2": 8.290297222424892,
    "g_midpoint_m_s2": 8.289101750747953,
    "g_outer_m_s2": 8.287906537635235,
    "abs_gravity_change_m_s2": 0.002390684789657246,
    "gravity_change_midpoint_approx_m_s2": 0.002390684764798602,
    "fractional_gravity_change": 0.00028841301042559003,
    "radial_gradient_mid_s2": -2.390684764798602e-06
   }
  ],
  "hypothesis_rows": [
   {
    "from_shell": "L1_z5",
    "to_shell": "L2_z6",
    "ratio_dr_over_r": 0.09978373702422146,
    "ratio_dg_over_g": 0.09977342520659582,
    "ratio_potential_step": 0.09956794174518983,
    "ratio_log_radius_step": 0.09978201831998791,
    "gamma_L_r": 0.023891340504049164
   },
   {
    "from_shell": "L2_z6",
    "to_shell": "L3_z3",
    "ratio_dr_over_r": 0.100021630975557,
    "ratio_dg_over_g": 0.10002152806052932,
    "ratio_potential_step": 0.10004326663010502,
    "ratio_log_radius_step": 0.10002161382307244,
    "gamma_L_r": 0.002390684764798602
   }
  ],
  "stonehenge_radius_compatible": false
 }
}
```
