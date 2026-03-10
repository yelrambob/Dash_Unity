# [BUILD FIRST]
# Patient class — the core game object.
#
# Full state machine:
#   Ordered > InTransport > InHolding >
#   ContrastOrdered > ContrastReady >
#   InjectorReady > Scanning > Cooldown >
#   Leaving > Completed | Refused | Holdover

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional
from classes.transport import Transport


class PatientState(Enum):
    ORDERED          = auto()
    IN_TRANSPORT     = auto()
    IN_HOLDING       = auto()
    CONTRAST_ORDERED = auto()
    CONTRAST_READY   = auto()
    INJECTOR_READY   = auto()
    SCANNING         = auto()
    COOLDOWN         = auto()
    LEAVING          = auto()
    COMPLETED        = auto()
    REFUSED          = auto()
    HOLDOVER         = auto()


@dataclass
class Patient:
    patient_id:   str
    acuity:       int                   # 1–5
    personability: float                # 0.0–1.0, affects refusal risk
    mobility:     str                   # "ambulatory", "wheelchair", "stretcher"
    exam_list:    List[str] = field(default_factory=list)   # ordered list of exam keys
    transport:    Optional[Transport] = None

    state:         PatientState = field(default=PatientState.ORDERED)
    wait_timer:    int = 0              # total game-seconds spent waiting
    contrast_timer: int = 0            # counts down oral contrast wait
    current_exam_index: int = 0        # index into exam_list for multi-exam patients
