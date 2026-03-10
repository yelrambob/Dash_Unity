# [BUILD FIRST]
# Transport class — handles patient movement delays.
#
# States:
#   WaitingAssignment — order placed, no transporter yet
#   Acknowledged      — transporter accepted the job
#   OnWay             — transporter en route to patient
#   Delivered         — patient arrived at holding bay

from dataclasses import dataclass, field
from enum import Enum, auto


class TransportState(Enum):
    WAITING_ASSIGNMENT = auto()
    ACKNOWLEDGED       = auto()
    ON_WAY             = auto()
    DELIVERED          = auto()


@dataclass
class Transport:
    state: TransportState = field(default=TransportState.WAITING_ASSIGNMENT)

    # Delay timers (in game-seconds) — set randomly within config ranges on spawn
    arrival_delay:  int = 0    # time until transporter arrives at patient
    hold_wait:      int = 0    # extra wait at pick-up before moving
    leaving_delay:  int = 0    # time after scan before transporter picks up

    timer: int = 0             # counts down current active delay
