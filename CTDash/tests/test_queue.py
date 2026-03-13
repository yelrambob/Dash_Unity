import sys
import os
import unittest

# Add CTDash/ to path so bare imports (from config import ...) resolve
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from managers.queue_manager import QueueManager
from classes.patient import Patient


def make_patient(pid, acuity):
    return Patient(
        patient_id=pid,
        acuity=acuity,
        personability=0.8,
        mobility="ambulatory",
        exam_list=["head"],
    )


class TestQueueManager(unittest.TestCase):

    def test_pop_order_by_acuity(self):
        """Higher-priority (lower acuity number) patients come out first."""
        qm = QueueManager()
        patients = [
            make_patient("PAT_0004", 4),
            make_patient("PAT_0001", 1),
            make_patient("PAT_0003", 3),
            make_patient("PAT_0002", 2),
        ]
        for i, p in enumerate(patients):
            qm.add_patient(p, game_second=i * 10)

        popped = []
        while not qm.is_empty():
            popped.append(qm.pop_next())

        acuities = [p.acuity for p in popped]
        self.assertEqual(acuities, sorted(acuities))

    def test_arrival_time_tiebreak(self):
        """Same acuity — earlier arrival comes out first."""
        qm = QueueManager()
        qm.add_patient(make_patient("PAT_LATE",  3), game_second=200)
        qm.add_patient(make_patient("PAT_EARLY", 3), game_second=100)

        first = qm.pop_next()
        self.assertEqual(first.patient_id, "PAT_EARLY")

    def test_wait_timer_increments(self):
        """tick() increments wait_timer for every queued patient."""
        qm = QueueManager()
        p = make_patient("PAT_0001", 2)
        qm.add_patient(p, game_second=0)

        for t in range(1, 6):
            qm.tick(game_second=t)

        self.assertEqual(p.wait_timer, 5)

    def test_pop_removes_from_queue(self):
        """Popped patient is no longer in the queue."""
        qm = QueueManager()
        qm.add_patient(make_patient("PAT_0001", 1), game_second=0)
        qm.pop_next()
        self.assertTrue(qm.is_empty())

    def test_pop_empty_returns_none(self):
        """pop_next() on an empty queue returns None."""
        qm = QueueManager()
        self.assertIsNone(qm.pop_next())

    def test_wait_timer_stops_after_pop(self):
        """Popped patient's wait_timer is not incremented by subsequent ticks."""
        qm = QueueManager()
        p = make_patient("PAT_0001", 1)
        qm.add_patient(p, game_second=0)
        qm.tick(game_second=1)
        qm.tick(game_second=2)
        popped = qm.pop_next()
        qm.tick(game_second=3)
        # wait_timer should be 2, not 3
        self.assertEqual(popped.wait_timer, 2)


if __name__ == "__main__":
    unittest.main()
