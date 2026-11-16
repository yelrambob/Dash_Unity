# [BUILD FIRST]
# QueueManager — manages the ordered queue of waiting patients.
# Handles priority ordering by acuity (1 = highest priority).
# Moves patients from queue into a holding bay when space is available.
# Tracks per-patient wait times.

import heapq

from config import TICK_SECONDS


class QueueManager:
    def __init__(self):
        # Min-heap: (acuity, arrival_time, patient_id)
        # Lower acuity number = higher priority
        self._heap = []
        self._patients = {}    # patient_id -> Patient object

    def add_patient(self, patient, game_second: int):
        """Add a newly spawned patient to the priority queue."""
        heapq.heappush(self._heap, (patient.acuity, game_second, patient.patient_id))
        self._patients[patient.patient_id] = patient

    def tick(self, game_second: int):
        """Advance wait timers for all queued patients."""
        for patient in self._patients.values():
            patient.wait_timer += TICK_SECONDS

    def pop_next(self):
        """Return the highest-priority patient and remove from queue."""
        if not self._heap:
            return None
        _, _, patient_id = heapq.heappop(self._heap)
        return self._patients.pop(patient_id)

    def is_empty(self) -> bool:
        return len(self._heap) == 0
