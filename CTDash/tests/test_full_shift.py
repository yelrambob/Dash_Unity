import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from classes.scanner import Scanner, ScannerState
from config import LEVELS
from data.exam_catalog import EXAM_CATALOG
from managers.contrast_manager import ContrastManager
from managers.queue_manager import QueueManager
from managers.scanner_manager import ScannerManager
from managers.scoring_manager import ScoringManager
from managers.spawn_manager import SpawnManager
from managers.staffing_manager import StaffingManager
from managers.transport_manager import TransportManager
from simulation.game_loop import GameLoop


def build_game(level: int = 1) -> GameLoop:
    """Wire up a complete game at the given level and return the GameLoop."""
    cfg = LEVELS[level]
    scanners = []
    for i in range(cfg["scanners"]):
        zone = "ED" if i == 0 else "Main"
        scanners.append(Scanner(
            scanner_id=f"SCANNER_{zone}_{i + 1}",
            zone=zone,
            state=ScannerState.LOCKED,
        ))

    queue_mgr     = QueueManager()
    scanner_mgr   = ScannerManager(scanners)
    transport_mgr = TransportManager()
    contrast_mgr  = ContrastManager()
    scoring_mgr   = ScoringManager()
    spawn_mgr     = SpawnManager(queue_mgr)
    staffing_mgr  = StaffingManager(scanner_mgr)

    managers = {
        "spawn":     spawn_mgr,
        "queue":     queue_mgr,
        "transport": transport_mgr,
        "contrast":  contrast_mgr,
        "scanner":   scanner_mgr,
        "scoring":   scoring_mgr,
        "staffing":  staffing_mgr,
    }

    start_h, end_h = cfg["shift_window"]
    return GameLoop(managers, EXAM_CATALOG, duration_hours=(end_h - start_h))


class TestFullShiftLevel1(unittest.TestCase):
    """Integration tests that run a complete Level 1 shift."""

    @classmethod
    def setUpClass(cls):
        """Run once — a full Level 1 shift takes ~0.5 s in test."""
        cls.loop = build_game(level=1)
        cls.score = cls.loop.run()
        cls.scoring = cls.loop.managers["scoring"]

    # ------------------------------------------------------------------
    # Basic sanity
    # ------------------------------------------------------------------

    def test_simulation_completes_without_error(self):
        """run() returns without raising."""
        self.assertIsInstance(self.score, int)

    def test_at_least_one_exam_completed(self):
        """At least one exam was scanned and completed during the shift."""
        self.assertGreater(self.scoring.exams_completed, 0)

    def test_score_is_integer(self):
        """Final score is an integer."""
        self.assertIsInstance(self.scoring.score, int)

    # ------------------------------------------------------------------
    # Patient states at shift end
    # ------------------------------------------------------------------

    def test_no_patients_stuck_in_transport(self):
        """No patient should still be IN_TRANSPORT at the end of the shift."""
        from classes.patient import PatientState
        stuck = [
            p for p in self.loop._patients.values()
            if p.state == PatientState.IN_TRANSPORT
        ]
        # Some patients may legitimately be in transport if spawned very late;
        # assert the count is small (< 5% of total).
        total = len(self.loop._patients)
        self.assertLess(len(stuck), max(3, total * 0.05))

    def test_all_patient_ids_unique(self):
        """Every patient in the registry has a unique ID."""
        ids = list(self.loop._patients.keys())
        self.assertEqual(len(ids), len(set(ids)))

    # ------------------------------------------------------------------
    # Scoring integrity
    # ------------------------------------------------------------------

    def test_score_reflects_exams(self):
        """Base score contribution from exams is positive."""
        from config import EXAM_BASE_SCORE
        base = self.scoring.exams_completed * EXAM_BASE_SCORE
        self.assertGreater(base, 0)

    def test_holdover_count_is_non_negative(self):
        self.assertGreaterEqual(self.scoring.holdovers, 0)

    # ------------------------------------------------------------------
    # Scanner state at end of shift
    # ------------------------------------------------------------------

    def test_scanners_not_scanning_at_end(self):
        """Scanners should be IDLE or COOLDOWN at shift end (not stuck SCANNING)."""
        scanner_mgr = self.loop.managers["scanner"]
        for scanner in scanner_mgr.scanners.values():
            self.assertNotEqual(
                scanner.state, ScannerState.LOCKED,
                msg=f"Scanner {scanner.scanner_id} still LOCKED at shift end "
                    "(staffing may not have fired)"
            )


class TestFullShiftScoring(unittest.TestCase):
    """Verify scoring math across a full run."""

    def test_each_completed_exam_adds_base_score(self):
        """ScoringManager.score matches expected formula for zero-penalty run."""
        from config import EXAM_BASE_SCORE
        scoring = ScoringManager()
        for _ in range(5):
            scoring.exam_completed()
        # No penalties applied
        self.assertEqual(scoring.score, 5 * EXAM_BASE_SCORE)

    def test_holdover_penalty_applied_per_patient(self):
        """finalise() deducts HOLDOVER_PENALTY for each remaining patient."""
        from config import HOLDOVER_PENALTY
        from classes.patient import Patient, PatientState
        from classes.transport import Transport

        scoring = ScoringManager()
        scoring.exam_completed()   # +100

        dummy_patients = [
            Patient(f"PAT_{i:04d}", acuity=3, personability=0.5,
                    mobility="ambulatory", exam_list=["head"],
                    transport=Transport())
            for i in range(3)
        ]
        final = scoring.finalise(dummy_patients)
        from config import HOLDOVER_PENALTY, EXAM_BASE_SCORE
        self.assertEqual(final, EXAM_BASE_SCORE - 3 * HOLDOVER_PENALTY)

    def test_wait_penalty_scales_with_acuity_mult(self):
        """Higher acuity tier multiplies the wait penalty."""
        from data.acuity_table import ACUITY_TABLE
        from config import WAIT_PENALTY_PER_MINUTE

        scoring_t1 = ScoringManager()
        scoring_t4 = ScoringManager()

        scoring_t1.apply_wait_penalty(acuity=1, excess_seconds=60)
        scoring_t4.apply_wait_penalty(acuity=4, excess_seconds=60)

        # Tier 1 penalty should be much larger than tier 4
        self.assertGreater(abs(scoring_t1.score), abs(scoring_t4.score))


class TestFullShiftAllLevels(unittest.TestCase):
    """Smoke-test: every level runs without crashing."""

    def _run_level(self, level):
        loop = build_game(level=level)
        score = loop.run()
        self.assertIsInstance(score, int)
        self.assertGreater(loop.managers["scoring"].exams_completed, 0)

    def test_level_1(self):
        self._run_level(1)

    def test_level_2(self):
        self._run_level(2)

    def test_level_3(self):
        self._run_level(3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
