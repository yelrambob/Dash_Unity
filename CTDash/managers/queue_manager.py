# [BUILD FIRST]
# QueueManager — manages the ordered queue of waiting patients.
# Handles priority ordering by acuity (1 = highest priority).
# Moves patients from queue into a holding bay when space is available.
# Tracks per-patient wait times.

import heapq


class QueueManager:
    def __init__(self):
        # Min-heap: (acuity, arrival_time, patient_id)
        # Lower acuity number = higher priority
        self._heap = []
        self._patients = {}    # patient_id -> Patient object

    def add_patient(self, patient):
        """Add a newly spawned patient to the priority queue."""
        # TODO: push onto heap, store in _patients dict
        pass

    def tick(self, game_second: int):
        """Advance wait timers for all queued patients."""
        # TODO: increment wait_timer on each queued patient
        pass

    def pop_next(self):
        """Return the highest-priority patient and remove from queue."""
        # TODO: pop from heap, return Patient object
        pass

    def is_empty(self) -> bool:
        return len(self._heap) == 0
