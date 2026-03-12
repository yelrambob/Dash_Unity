# ScoringManager — tracks all score components in real time.
#
# Components:
#   exams_completed   — +EXAM_BASE_SCORE per completed exam
#   wait_penalties    — per patient, per game-minute over acuity threshold
#                       penalty = WAIT_PENALTY_PER_MINUTE × acuity penalty_mult
#   overflow_penalties — flat OVERFLOW_PENALTY per overflow event
#   holdover_penalties — flat HOLDOVER_PENALTY per patient at shift end
#
# apply_wait_penalty() is called by GameLoop once per game-minute per patient
# whose wait_timer has exceeded their acuity threshold.

from config import EXAM_BASE_SCORE, WAIT_PENALTY_PER_MINUTE, OVERFLOW_PENALTY, HOLDOVER_PENALTY
from data.acuity_table import ACUITY_TABLE


class ScoringManager:
    def __init__(self):
        self.score           = 0
        self.exams_completed = 0
        self.holdovers       = 0

    def exam_completed(self):
        self.exams_completed += 1
        self.score += EXAM_BASE_SCORE

    def apply_wait_penalty(self, acuity: int, excess_seconds: int):
        """
        Called once per game-minute per patient over their wait threshold.
        excess_seconds: seconds over threshold (multiple of 60 from GameLoop).
        Penalty scales by acuity tier's penalty_mult.
        """
        tier          = ACUITY_TABLE.get(acuity, {})
        penalty_mult  = tier.get("penalty_mult", 1.0)
        excess_minutes = excess_seconds // 60
        self.score   -= int(WAIT_PENALTY_PER_MINUTE * penalty_mult * excess_minutes)

    def apply_overflow_penalty(self):
        self.score -= OVERFLOW_PENALTY

    def finalise(self, remaining_patients: list) -> int:
        """Called at end of shift. Applies holdover penalties, returns final score."""
        self.holdovers = len(remaining_patients)
        self.score    -= self.holdovers * HOLDOVER_PENALTY
        return self.score
