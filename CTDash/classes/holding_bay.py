# HoldingBay — waiting area patients sit in after transport delivers them,
# before a scanner becomes available.
#
# Two slot tiers:
#   proper_slots   — normal capacity (4 default)
#   overflow_slots — emergency buffer; occupying these triggers a score penalty
#
# The bay doesn't care about scan order — that's QueueManager's job.
# HoldingBay just tracks who is physically present and whether we're over capacity.

from dataclasses import dataclass, field
from typing import Dict
from config import HOLDING_PROPER_SLOTS, HOLDING_OVERFLOW_SLOTS


@dataclass
class HoldingBay:
    zone:           str                          # "ED" or "Main"
    proper_slots:   int = HOLDING_PROPER_SLOTS
    overflow_slots: int = HOLDING_OVERFLOW_SLOTS

    _patients: Dict[str, object] = field(default_factory=dict, repr=False)
    # str -> Patient; private so dataclass repr stays readable

    # ------------------------------------------------------------------
    def admit(self, patient) -> bool:
        """
        Place patient in the bay.
        Returns True if they landed in overflow (scoring_manager should be notified).
        Raises if the bay is completely full — caller must handle this case.
        """
        if self.is_full:
            raise OverflowError(
                f"HoldingBay '{self.zone}' is full "
                f"({self.proper_slots + self.overflow_slots} slots occupied)"
            )
        self._patients[patient.patient_id] = patient
        return self.is_overflowing   # True means this patient pushed into overflow

    def remove(self, patient_id: str):
        """Remove patient when they are called to a scanner."""
        self._patients.pop(patient_id, None)

    # ------------------------------------------------------------------
    @property
    def count(self) -> int:
        return len(self._patients)

    @property
    def overflow_count(self) -> int:
        """How many patients are sitting in overflow slots."""
        return max(0, self.count - self.proper_slots)

    @property
    def is_overflowing(self) -> bool:
        return self.count > self.proper_slots

    @property
    def is_full(self) -> bool:
        return self.count >= (self.proper_slots + self.overflow_slots)

    def all_patients(self):
        """Return all Patient objects currently in the bay."""
        return list(self._patients.values())
