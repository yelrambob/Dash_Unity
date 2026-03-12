# [BUILD FIRST]
# Patient class — the core game object.
#
# Full state machine:
#   ORDERED
#     → CONTRAST_ORDERED  (oral contrast timer running; patient still in their room)
#     → IN_TRANSPORT       (oral contrast done, transport dispatched — OR immediate for no-oral exams)
#     → IN_HOLDING         (arrived in CT holding bay)
#     → INJECTOR_READY     (IV injector filled, ready to scan; skipped for non-IV exams)
#     → SCANNING
#     → COOLDOWN
#     → LEAVING
#     → COMPLETED | REFUSED | CANCELLED | HOLDOVER
#
# Key rule: transport is NEVER called until oral contrast timer is finished.
# Patients in CONTRAST_ORDERED are visible in the order queue with a countdown timer.

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
    REFUSED          = auto()   # patient declined exam (personability-driven)
    CANCELLED        = auto()   # TODO (future): MD cancelled the order mid-queue
                                #   - very rare, random trigger on any pre-scan state
                                #   - no score penalty (out of tech's control)
                                #   - distinct from REFUSED so scoring can treat them differently
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

    # --- Event fields (REFUSED / CANCELLED) --------------------------------
    # Set by EventManager when a random event fires. UI should display event_reason
    # in a popup and block further interaction until the player acknowledges it.
    pending_acknowledgment: bool = False   # True = player must tap to dismiss
    event_reason:  Optional[str] = None    # displayed reason string
    requires_outbound: bool = False        # True if patient is physically in bay/scanner
                                           # when event fires — slot held until acknowledged,
                                           # then outbound transport is dispatched
    terminal_state: "PatientState" = field(default=None)
    # terminal_state is set by EventManager so transport knows what final state
    # to assign on departure (REFUSED / CANCELLED rather than COMPLETED).
