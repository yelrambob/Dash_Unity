# [BUILD FIRST]
# HoldingBay class — waiting area before scanner assignment.
# Tracks proper slots and overflow slots separately.
# Overflow triggers a penalty via scoring_manager.

from dataclasses import dataclass, field
from typing import List


@dataclass
class HoldingBay:
    zone:           str              # "ED" or "Main"
    proper_slots:   int = 4
    overflow_slots: int = 2

    patients: List[str] = field(default_factory=list)   # list of patient_ids

    @property
    def is_overflowing(self) -> bool:
        return len(self.patients) > self.proper_slots

    @property
    def is_full(self) -> bool:
        # True when even overflow is exhausted
        return len(self.patients) >= (self.proper_slots + self.overflow_slots)
