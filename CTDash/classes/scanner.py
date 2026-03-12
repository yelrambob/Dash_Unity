# [BUILD FIRST]
# Scanner class — represents one CT machine.
#
# States:
#   Idle     — available, no patient
#   Scanning — patient actively being scanned
#   Cooldown — post-scan reset period
#   Locked   — no tech assigned, cannot accept patients

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class ScannerState(Enum):
    IDLE     = auto()
    SCANNING = auto()
    COOLDOWN = auto()
    LOCKED   = auto()


@dataclass
class Scanner:
    scanner_id:      str
    zone:            str          # "ED" or "Main"
    state:           ScannerState = field(default=ScannerState.IDLE)
    current_patient: Optional[str] = None    # patient_id or None
    assigned_tech:   object        = None    # Tech object or None (avoids circular import)
    scan_timer:      int = 0
    cooldown_timer:  int = 0

    @property
    def is_available(self) -> bool:
        # A scanner can accept a patient only if idle AND a tech is assigned
        return self.state == ScannerState.IDLE and self.assigned_tech is not None
