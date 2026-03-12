# Transport class — three-phase patient movement model.
#
# Three counters, each owned by a different manager:
#
#   inbound_delay  — call for patient + deliver to scanner area (TransportManager)
#   setup_delay    — get on table / position / scan / get off  (ScannerManager)
#   leaving_delay  — transporter arrives post-scan, patient leaves dept (TransportManager)
#
# Mobility affects all three, but setup_delay is where it really matters:
# an ambulatory patient hops on the table; a stretcher patient is a full
# bed-to-table transfer with positioning aids, which can take several minutes.
#
# States track which phase is active:
#   INBOUND   — patient being brought to scanner area
#   IN_SETUP  — patient at scanner (table on / scan / table off)
#   OUTBOUND  — transporter returning patient to their unit
#   DONE      — patient has left the department

from dataclasses import dataclass, field
from enum import Enum, auto


class TransportState(Enum):
    INBOUND  = auto()
    IN_SETUP = auto()
    OUTBOUND = auto()
    DONE     = auto()


@dataclass
class Transport:
    state: TransportState = field(default=TransportState.INBOUND)

    # Delay values (game-seconds) — rolled at spawn, scaled by mobility multiplier
    inbound_delay:  int = 0    # call + deliver to scanner area
    setup_delay:    int = 0    # table on/off overhead (owned by ScannerManager)
    leaving_delay:  int = 0    # post-scan pickup + exit from dept

    timer: int = 0             # counts down current active phase
