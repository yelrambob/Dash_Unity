import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from classes.scanner import Scanner, ScannerState
from classes.patient import Patient, PatientState
from classes.transport import Transport
from managers.scanner_manager import ScannerManager
from data.exam_catalog import EXAM_CATALOG
from config import SCAN_TIMES, SCANNER_COOLDOWN


def make_scanner(zone="ED", state=ScannerState.IDLE, tech="tech_01"):
    return Scanner(
        scanner_id=f"SCANNER_{zone}_1",
        zone=zone,
        state=state,
        assigned_tech=tech,
    )


def make_patient(pid="PAT_0001", acuity=3, exams=None):
    return Patient(
        patient_id=pid,
        acuity=acuity,
        personability=0.8,
        mobility="ambulatory",
        exam_list=exams or ["head"],
        transport=Transport(),
        state=PatientState.IN_HOLDING,
    )


class TestScannerAssignment(unittest.TestCase):

    def test_try_assign_succeeds_on_idle_scanner(self):
        """A patient is assigned when an IDLE scanner with a tech is available."""
        scanner = make_scanner()
        sm = ScannerManager([scanner])
        patient = make_patient()

        result = sm.try_assign(patient, EXAM_CATALOG)

        self.assertTrue(result)
        self.assertEqual(scanner.state, ScannerState.SCANNING)
        self.assertEqual(scanner.current_patient, patient.patient_id)
        self.assertEqual(patient.state, PatientState.SCANNING)

    def test_try_assign_fails_on_locked_scanner(self):
        """Assignment fails when the scanner is LOCKED."""
        scanner = make_scanner(state=ScannerState.LOCKED)
        sm = ScannerManager([scanner])
        patient = make_patient()

        result = sm.try_assign(patient, EXAM_CATALOG)

        self.assertFalse(result)
        self.assertEqual(scanner.state, ScannerState.LOCKED)

    def test_try_assign_fails_when_no_tech(self):
        """Assignment fails when scanner has no assigned tech."""
        scanner = make_scanner(tech=None)
        sm = ScannerManager([scanner])
        patient = make_patient()

        result = sm.try_assign(patient, EXAM_CATALOG)

        self.assertFalse(result)

    def test_try_assign_sets_correct_scan_timer(self):
        """scan_timer is set to the exam's SCAN_TIMES value."""
        scanner = make_scanner()
        sm = ScannerManager([scanner])
        patient = make_patient(exams=["chest"])   # SCAN_TIMES["chest"] = 25

        sm.try_assign(patient, EXAM_CATALOG)

        self.assertEqual(scanner.scan_timer, SCAN_TIMES["chest"])

    def test_ed_scanner_preferred_for_acuity_1(self):
        """Trauma (acuity 1) patients are assigned to ED scanner first."""
        ed   = make_scanner(zone="ED",   tech="tech_01")
        main = make_scanner(zone="Main", tech="tech_02")
        main.scanner_id = "SCANNER_Main_1"
        sm = ScannerManager([main, ed])   # Main listed first
        patient = make_patient(acuity=1, exams=["trauma_full"])

        sm.try_assign(patient, EXAM_CATALOG)

        self.assertEqual(ed.state, ScannerState.SCANNING)
        self.assertEqual(main.state, ScannerState.IDLE)


class TestScannerTick(unittest.TestCase):

    def _setup(self, exams=None):
        scanner = make_scanner()
        patient = make_patient(exams=exams or ["head"])
        sm = ScannerManager([scanner])
        sm.try_assign(patient, EXAM_CATALOG)
        return sm, scanner, patient

    def _tick_n(self, sm, n):
        for _ in range(n):
            sm.tick(EXAM_CATALOG)

    def test_scan_completes_after_scan_time(self):
        """Scanner enters COOLDOWN exactly after SCAN_TIMES ticks."""
        sm, scanner, patient = self._setup(["head"])
        self._tick_n(sm, SCAN_TIMES["head"])
        self.assertEqual(scanner.state, ScannerState.COOLDOWN)

    def test_cooldown_resolves_to_idle(self):
        """After SCANNER_COOLDOWN ticks in COOLDOWN, scanner returns to IDLE."""
        sm, scanner, patient = self._setup(["head"])
        self._tick_n(sm, SCAN_TIMES["head"] + SCANNER_COOLDOWN)
        self.assertEqual(scanner.state, ScannerState.IDLE)

    def test_patient_in_completed_list_after_cooldown(self):
        """Patient appears in completed_patients once scanner returns to IDLE."""
        sm, scanner, patient = self._setup(["head"])
        self._tick_n(sm, SCAN_TIMES["head"] + SCANNER_COOLDOWN)
        self.assertIn(patient, sm.completed_patients)

    def test_patient_state_scanning_during_scan(self):
        """Patient.state is SCANNING while scan timer is running."""
        sm, scanner, patient = self._setup(["head"])
        sm.tick(EXAM_CATALOG)   # one tick into scan
        self.assertEqual(patient.state, PatientState.SCANNING)

    def test_patient_state_cooldown_during_cooldown(self):
        """Patient.state is COOLDOWN while cooldown timer is running."""
        sm, scanner, patient = self._setup(["head"])
        self._tick_n(sm, SCAN_TIMES["head"])
        self.assertEqual(patient.state, PatientState.COOLDOWN)

    def test_scanner_not_idle_before_cooldown_ends(self):
        """Scanner is still in COOLDOWN one tick before it would clear."""
        sm, scanner, patient = self._setup(["head"])
        self._tick_n(sm, SCAN_TIMES["head"] + SCANNER_COOLDOWN - 1)
        self.assertEqual(scanner.state, ScannerState.COOLDOWN)

    def test_multi_exam_patient_stays_on_scanner(self):
        """A two-exam patient starts the second exam immediately after cooldown."""
        sm, scanner, patient = self._setup(["head", "chest"])
        self._tick_n(sm, SCAN_TIMES["head"] + SCANNER_COOLDOWN)

        self.assertEqual(scanner.state, ScannerState.SCANNING)
        self.assertEqual(patient.current_exam_index, 1)
        self.assertNotIn(patient, sm.completed_patients)

    def test_multi_exam_patient_completes_after_all_exams(self):
        """Patient is only in completed_patients after every exam is done."""
        sm, scanner, patient = self._setup(["head", "chest"])
        total = (SCAN_TIMES["head"] + SCANNER_COOLDOWN
                 + SCAN_TIMES["chest"] + SCANNER_COOLDOWN)
        self._tick_n(sm, total)

        self.assertIn(patient, sm.completed_patients)
        self.assertEqual(scanner.state, ScannerState.IDLE)

    def test_scanner_clears_current_patient_after_cooldown(self):
        """scanner.current_patient is None once the patient leaves."""
        sm, scanner, patient = self._setup(["head"])
        self._tick_n(sm, SCAN_TIMES["head"] + SCANNER_COOLDOWN)
        self.assertIsNone(scanner.current_patient)


if __name__ == "__main__":
    unittest.main()
