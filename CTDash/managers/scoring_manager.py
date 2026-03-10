# [LATER] — depends on most other systems being functional
# ScoringManager — tracks all score components in real time.
#
# Components:
#   exams_completed   — positive score
#   wait_penalties    — per-patient, per-minute over threshold
#   overflow_penalties — flat hit per overflow patient per tick
#   holdover_penalties — flat hit per patient still in system at shift end
#   combo_multiplier   — future feature, streak bonus for fast throughput
#
# Drives level-up / level-down logic at end of shift.

from config import WAIT_PENALTY_PER_MINUTE, OVERFLOW_PENALTY, HOLDOVER_PENALTY


class ScoringManager:
    def __init__(self):
        self.score = 0
        self.exams_completed = 0
        self.holdovers = 0

    def exam_completed(self):
        self.exams_completed += 1
        self.score += 10    # TODO: tune base score per exam

    def apply_wait_penalty(self, acuity: int, excess_seconds: int):
        """Called when a patient's wait exceeds their acuity threshold."""
        # TODO: use acuity_table penalty_mult and WAIT_PENALTY_PER_MINUTE
        pass

    def apply_overflow_penalty(self):
        self.score -= OVERFLOW_PENALTY

    def finalise(self, remaining_patients: list) -> int:
        """Called at end of shift. Applies holdover penalties, returns final score."""
        self.holdovers = len(remaining_patients)
        self.score -= self.holdovers * HOLDOVER_PENALTY
        return self.score
