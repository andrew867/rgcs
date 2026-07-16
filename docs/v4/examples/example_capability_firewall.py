"""Example: the capability firewall in three calls."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from rscs2_core.multiphysics import applicability, get_material

quartz = get_material("material.alpha_quartz")
print(applicability(quartz, "piezoelectric"))       # APPLICABLE
print(applicability(quartz, "magnon_modes"))        # NOT implemented
li = get_material("reference.linipo4")
print(applicability(li, "domain_writing"))          # REFERENCE_ONLY
