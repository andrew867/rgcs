"""Example: LiNiPO4 IOME domain writing — direction flips the sign,
polarization does not (channel ablation in four lines)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
from rscs2_core.refmodels import iome_linipo4 as io

k = np.array([0.0, 1.0, 0.0])
fwd = io.write_domains("reference.linipo4", k, 1.0, 1.0, 2.0)
bwd = io.write_domains("reference.linipo4", -k, 1.0, 1.0, 2.0)
rcp = io.write_domains("reference.linipo4", k, 1.0, 1.0, 2.0,
                       jones=(2 ** -0.5, 1j * 2 ** -0.5))
print("forward alignment:", fwd["value"]["alignment"])
print("reversed alignment:", bwd["value"]["alignment"])
print("RCP == linear (polarization-blind):",
      rcp["value"]["alignment"] == fwd["value"]["alignment"])
quartz = io.write_domains("material.alpha_quartz", k, 1.0, 1.0, 2.0)
print("quartz:", quartz["classification"], quartz["reason_code"])
