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

from config import EXAM_BASE_SCORE, WAIT_PENALTY_PER_MINUTE, OVERFLOW_PENALTY, HOLDOVER_PENALTY
from data.acuity_table import ACUITY_TABLE


class ScoringManager:
    def __init__(self):
        self.score = 0
        self.exams_completed = 0
        self.holdovers = 0

    def exam_completed(self, acuity: int = None):
        """Award base score for a completed exam."""
        self.exams_completed += 1
        self.score += EXAM_BASE_SCORE

    def apply_wait_penalty(self, acuity: int, excess_seconds: int):
        """Called when a patient's wait exceeds their acuity threshold."""
        penalty_mult   = ACUITY_TABLE[acuity]["penalty_mult"]
        excess_minutes = excess_seconds / 60.0
        penalty        = int(excess_minutes * WAIT_PENALTY_PER_MINUTE * penalty_mult)
        self.score    -= penalty

    def apply_overflow_penalty(self):
        self.score -= OVERFLOW_PENALTY

    def finalise(self, remaining_patients: list) -> int:
        """Called at end of shift. Applies holdover penalties, returns final score."""
        self.holdovers  = len(remaining_patients)
        self.score     -= self.holdovers * HOLDOVER_PENALTY
        return self.score
