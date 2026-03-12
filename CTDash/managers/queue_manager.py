# QueueManager — ordered list of patients waiting for a scanner.
#
# Priority rules (in order):
#   1. acuity tier (1 = highest, 4 = lowest) — from acuity_table queue_priority
#   2. arrival_time tiebreaker — earlier arrival wins within same tier
#
# The heap stores (acuity, arrival_time, patient_id) tuples so Python's
# min-heap gives us the right patient on every pop without a sort pass.
#
# Patients live here between IN_HOLDING and being handed to ScannerManager.
# wait_timer is incremented each tick regardless of state — scoring uses it.

import heapq


class QueueManager:
    def __init__(self):
        self._heap     = []              # (acuity, arrival_time, patient_id)
        self._patients = {}              # patient_id -> Patient
        self._removed  = set()           # patient_ids that were popped or cancelled

    # ------------------------------------------------------------------
    def add_patient(self, patient, game_time: int):
        """
        Enqueue a patient.
        game_time is current sim time in game-seconds — used as arrival tiebreaker.
        """
        heapq.heappush(
            self._heap,
            (patient.acuity, game_time, patient.patient_id)
        )
        self._patients[patient.patient_id] = patient

    def pop_next(self):
        """
        Return highest-priority patient and remove from queue.
        Skips any stale heap entries (lazy deletion pattern).
        Returns None if queue is empty.
        """
        while self._heap:
            _, _, pid = heapq.heappop(self._heap)
            if pid in self._removed:
                continue
            if pid in self._patients:
                patient = self._patients.pop(pid)
                return patient
        return None

    def remove(self, patient_id: str):
        """
        Remove a specific patient without popping (e.g. patient refused / left).
        Uses lazy deletion — actual heap entry is skipped on next pop_next().
        """
        self._patients.pop(patient_id, None)
        self._removed.add(patient_id)

    def tick(self):
        """Increment wait_timer on every patient currently in the queue."""
        for patient in self._patients.values():
            patient.wait_timer += 1

    # ------------------------------------------------------------------
    def peek_next(self):
        """
        Return the highest-priority patient without removing them.
        Useful for the game loop to check acuity before committing to pop.
        """
        while self._heap:
            _, _, pid = self._heap[0]
            if pid in self._removed or pid not in self._patients:
                heapq.heappop(self._heap)
                continue
            return self._patients[pid]
        return None

    @property
    def is_empty(self) -> bool:
        return len(self._patients) == 0

    @property
    def count(self) -> int:
        return len(self._patients)
