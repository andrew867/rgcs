# V6 Rejected Candidates

Every rejection carries its reason, salvage path, and nearest
surviving neighbor. Rejection is a report, not a deletion.

## V6C_0285: near_neighbor_merge

- why it failed: phi and RGCS families merged without a correction rule
- salvage path: keep families distinct; record the offset as a CANDIDATE_BRIDGE and compare, not merge
- fixable by one variable: True
- measurement can resolve: False
- nearest surviving neighbor: V6C_0240

## V6C_0286: non_sale_purchase_ranking

- why it failed: ideal-only crystal used in purchase ranking
- salvage path: swap in the nearest sale-dataset candidate; keep ideal rows as theory references only
- fixable by one variable: True
- measurement can resolve: True
- nearest surviving neighbor: V6C_0240

## V6C_0287: parent_not_control

- why it failed: one-variable chain broken: parent run is not the control
- salvage path: re-chain the run so its parent is its control; one variable per step
- fixable by one variable: True
- measurement can resolve: False
- nearest surviving neighbor: V6C_0240

## V6C_0288: sspp_status_missing

- why it failed: groove present but no diameter, so h/d status cannot be computed
- salvage path: supply the ring diameter so h/d and the well-formed status compute
- fixable by one variable: True
- measurement can resolve: True
- nearest surviving neighbor: V6C_0240

## V6C_0289: saw_missing_material

- why it failed: SAW geometry lacks material velocity or frequency
- salvage path: bind the feature sizes to a material velocity and frequency
- fixable by one variable: True
- measurement can resolve: False
- nearest surviving neighbor: V6C_0240

## V6C_0290: thyr_as_drive

- why it failed: THYR treated as drive validation; it is readout only
- salvage path: reclassify THYR as readout; pick a drive lane from the spine for excitation
- fixable by one variable: True
- measurement can resolve: False
- nearest surviving neighbor: V6C_0240

## V6C_0291: hbn_as_quartz

- why it failed: hBN treated as quartz replacement; it is a benchmark
- salvage path: keep hBN as the loss/measurement benchmark; quartz remains the device medium
- fixable by one variable: True
- measurement can resolve: False
- nearest surviving neighbor: V6C_0240

## V6C_0292: witness_as_validation

- why it failed: witness layer marked as validation
- salvage path: relabel the witness layer as hypothesis or measurement target
- fixable by one variable: True
- measurement can resolve: False
- nearest surviving neighbor: V6C_0240

## V6C_0293: craft_performance_scoring

- why it failed: score field implies physical craft performance
- salvage path: remove the performance field; score measurable coupling signatures only
- fixable by one variable: False
- measurement can resolve: False
- nearest surviving neighbor: V6C_0240

## V6C_0294: near_neighbor_merge

- why it failed: phi and RGCS families merged without a correction rule
- salvage path: keep families distinct; record the offset as a CANDIDATE_BRIDGE and compare, not merge
- fixable by one variable: True
- measurement can resolve: False
- nearest surviving neighbor: V6C_0240

## V6C_0295: saw_missing_material

- why it failed: SAW geometry lacks material velocity or frequency
- salvage path: bind the feature sizes to a material velocity and frequency
- fixable by one variable: True
- measurement can resolve: False
- nearest surviving neighbor: V6C_0240

## V6C_0296: non_sale_purchase_ranking

- why it failed: ideal-only crystal used in purchase ranking
- salvage path: swap in the nearest sale-dataset candidate; keep ideal rows as theory references only
- fixable by one variable: True
- measurement can resolve: True
- nearest surviving neighbor: V6C_0240

