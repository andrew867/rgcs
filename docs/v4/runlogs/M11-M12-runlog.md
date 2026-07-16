# Run log — Agents M11 + M12

M11 base `6d3f7d4` (9 tests, H1-H5). Fix during dev: logistic
saturation overflow at scale*bias ~ 6000 -> clamped exponent.
M12 (7 tests, H6-H7). Fixes: classifier used uncentered correlation
-> Pearson; test regime for 1.3x threshold was wrong physics (strong
overdrive runs through multiple wells; now asserted as such, with the
single-switch pi-slip tested just above threshold at higher damping).
