"""Example: avoided crossing anchored to the frozen v3 model."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from rgcs_core.coupled_modes.static import coupled_two_mode
from rscs2_core.refmodels import avoided_crossing as ac

out = ac.two_mode("reference.soe_phonon", 980.0, 1020.0, 15.0,
                  gamma_a_hz=2.0, gamma_b_hz=1.0)
frozen = coupled_two_mode(980.0, 1020.0, 15.0)
print("reduced model:", out["value"]["lower_hz"],
      out["value"]["upper_hz"])
print("frozen v3    :", frozen["lower_hybrid_hz"],
      frozen["upper_hybrid_hz"])
print("linewidths   :", out["value"]["lower_linewidth_hz"],
      out["value"]["upper_linewidth_hz"])
