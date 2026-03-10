# [LATER] — depends on staffing_manager.py
# Tech class — represents a CT technologist.
#
# Status values: "scanning", "paperwork", "idle", "off_shift"

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class TechStatus(Enum):
    SCANNING   = auto()
    PAPERWORK  = auto()
    IDLE       = auto()
    OFF_SHIFT  = auto()


@dataclass
class Tech:
    tech_id:        str
    name:           str
    speed:          float           # 0.0–1.0, affects scan time modifier
    accuracy:       float           # 0.0–1.0, affects error/repeat rate
    willingness:    float           # 0.0–1.0, affects refusal to take patients
    knowledge_base: float           # 0.0–1.0, affects contrast and protocol decisions
    shift_start:    float           # game-time hour, e.g. 7.0
    shift_end:      float           # game-time hour, e.g. 15.5

    assigned_scanner: Optional[str] = None   # scanner_id or None
    status: TechStatus = field(default=TechStatus.OFF_SHIFT)
