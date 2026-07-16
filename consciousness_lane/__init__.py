"""RGCS consciousness and temporal-coherence research lane
(Agents T01-T10; ledger C001-C052; gates G31-G40).

QUARANTINE CONTRACT: this package is a separate research lane. It may
import the shared record schema (`rscs2_core.research_records`) but
must never import quartz solvers (`rscs2_core.fem`, `rscs2_core.eye`,
`rscs2_core.modal`), and no record produced here may be used as
evidence in quartz computation. Reduced models here are mathematics
about oscillator populations and cognitive dynamics, not brain
measurements and not quartz physics."""

FORBIDDEN_IMPORTS = ("rscs2_core.fem", "rscs2_core.eye",
                     "rscs2_core.modal", "rscs2_core.eye_refinement")

ALLOWED_STATUSES = ("SOURCE_HYPOTHESIS", "REDUCED_ORDER_VALIDATED",
                    "ENGINEERING_PROTOTYPE", "NOT_APPLICABLE",
                    "INTERFACE_ONLY", "ETHICS_APPROVAL_REQUIRED",
                    "PROTOCOL_READY_HARDWARE_REQUIRED")
