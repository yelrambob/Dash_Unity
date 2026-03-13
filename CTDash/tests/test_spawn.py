import sys
import os
import unittest
from collections import Counter
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from managers.spawn_manager import SpawnManager
from data.acuity_table import ACUITY_TABLE
from data.hourly_spawn_weights import HOURLY_SPAWN_TABLE


class TestSpawnManager(unittest.TestCase):

    def _make_spawn_manager(self):
        """SpawnManager with a mock queue so we can inspect added patients."""
        mock_queue = MagicMock()
        mock_queue.add_patient = MagicMock()
        sm = SpawnManager(mock_queue)
        return sm, mock_queue

    # ------------------------------------------------------------------
    # Patient ID generation
    # ------------------------------------------------------------------

    def test_patient_ids_are_unique(self):
        """Each spawned patient gets a unique, incrementing ID."""
        sm, queue = self._make_spawn_manager()
        for _ in range(10):
            sm._spawn_patient(game_hour=9, game_second=0)

        ids = [call.args[0].patient_id for call in queue.add_patient.call_args_list]
        self.assertEqual(len(ids), len(set(ids)))

    def test_patient_id_format(self):
        """IDs follow the PAT_NNNN format."""
        sm, queue = self._make_spawn_manager()
        sm._spawn_patient(game_hour=9, game_second=0)
        patient = queue.add_patient.call_args.args[0]
        self.assertRegex(patient.patient_id, r'^PAT_\d{4}$')

    # ------------------------------------------------------------------
    # Acuity range
    # ------------------------------------------------------------------

    def test_acuity_in_valid_range(self):
        """All spawned patients have acuity 1–4."""
        sm, queue = self._make_spawn_manager()
        for _ in range(200):
            sm._spawn_patient(game_hour=9, game_second=0)
        for call in queue.add_patient.call_args_list:
            patient = call.args[0]
            self.assertIn(patient.acuity, (1, 2, 3, 4))

    def test_acuity_3_dominates(self):
        """Tier 3 (STAT) should be the most common across many spawns."""
        sm, queue = self._make_spawn_manager()
        for _ in range(1000):
            sm._spawn_patient(game_hour=9, game_second=0)  # low acuity_bias hour
        acuities = [call.args[0].acuity
                    for call in queue.add_patient.call_args_list]
        counts = Counter(acuities)
        # Tier 3 should outnumber any other single tier
        self.assertGreater(counts[3], counts[1])
        self.assertGreater(counts[3], counts[2])
        self.assertGreater(counts[3], counts[4])

    # ------------------------------------------------------------------
    # Exam assignment
    # ------------------------------------------------------------------

    def test_exam_matches_acuity_catalog(self):
        """Each patient's exam is drawn from their acuity tier's typical_exams list."""
        sm, queue = self._make_spawn_manager()
        for _ in range(100):
            sm._spawn_patient(game_hour=9, game_second=0)
        for call in queue.add_patient.call_args_list:
            patient = call.args[0]
            allowed = ACUITY_TABLE[patient.acuity]["typical_exams"]
            self.assertIn(patient.exam_list[0], allowed)

    # ------------------------------------------------------------------
    # Mobility
    # ------------------------------------------------------------------

    def test_mobility_is_valid(self):
        """Mobility must be one of the three known values."""
        valid = {"ambulatory", "wheelchair", "stretcher"}
        sm, queue = self._make_spawn_manager()
        for _ in range(50):
            sm._spawn_patient(game_hour=9, game_second=0)
        for call in queue.add_patient.call_args_list:
            self.assertIn(call.args[0].mobility, valid)

    # ------------------------------------------------------------------
    # Transport initialisation
    # ------------------------------------------------------------------

    def test_transport_is_attached(self):
        """Spawned patient has a Transport object with non-zero arrival_delay."""
        sm, queue = self._make_spawn_manager()
        sm._spawn_patient(game_hour=9, game_second=0)
        patient = queue.add_patient.call_args.args[0]
        self.assertIsNotNone(patient.transport)
        self.assertGreater(patient.transport.arrival_delay, 0)

    # ------------------------------------------------------------------
    # Tick — probabilistic spawn
    # ------------------------------------------------------------------

    def test_tick_spawns_at_peak_hour(self):
        """Over many ticks at peak hour (12), at least one patient is spawned."""
        sm, queue = self._make_spawn_manager()
        # Hour 12: exams_per_hour=18, prob=18/3600=0.005 per tick
        # Over 3600 ticks the expected count is ~18; very unlikely to be 0.
        for tick in range(3600):
            sm.tick(game_hour=12, game_second=tick)
        self.assertGreater(queue.add_patient.call_count, 0)

    def test_tick_adds_patient_to_queue(self):
        """tick() passes game_second to queue_manager.add_patient."""
        sm, queue = self._make_spawn_manager()
        # Force a spawn by mocking random
        import random
        original = random.random
        random.random = lambda: 0.0   # always below any probability
        try:
            sm.tick(game_hour=10, game_second=500)
        finally:
            random.random = original
        queue.add_patient.assert_called_once()
        _patient, gs = queue.add_patient.call_args.args
        self.assertEqual(gs, 500)

    # ------------------------------------------------------------------
    # Acuity bias — high-acuity hour vs low-acuity hour
    # ------------------------------------------------------------------

    def test_high_acuity_bias_produces_more_tier1_2(self):
        """Overnight hours (high acuity_bias) yield proportionally more tier 1–2."""
        sm_high, q_high = self._make_spawn_manager()
        sm_low,  q_low  = self._make_spawn_manager()

        n = 500
        # Hour 0: acuity_bias=0.6 (high); hour 10: acuity_bias=0.30 (lower)
        for _ in range(n):
            sm_high._spawn_patient(game_hour=0,  game_second=0)
            sm_low._spawn_patient(game_hour=10, game_second=0)

        high_acuity_calls = sum(
            1 for c in q_high.add_patient.call_args_list
            if c.args[0].acuity in (1, 2)
        )
        low_acuity_calls = sum(
            1 for c in q_low.add_patient.call_args_list
            if c.args[0].acuity in (1, 2)
        )
        self.assertGreater(high_acuity_calls, low_acuity_calls)


if __name__ == "__main__":
    unittest.main()
