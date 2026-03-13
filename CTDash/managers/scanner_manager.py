# [BUILD FIRST]
# ScannerManager — controls scanner assignment and scan lifecycle.
# Zone preference: trauma/acuity-1 patients go to ED CT first.
# Checks tech availability before assigning a patient to a scanner.
# Manages multi-exam sequences (patient stays until all exams done).
# Tracks scan timer and cooldown timer per scanner.

from classes.patient import PatientState
from classes.scanner import ScannerState
from config import SCAN_TIMES, SCANNER_COOLDOWN


class ScannerManager:
    def __init__(self, scanners: list):
        # scanners: list of Scanner objects, passed in from game_loop
        self.scanners = {s.scanner_id: s for s in scanners}
        # Holds Patient objects currently on a scanner, keyed by scanner_id.
        self._scanning_patients = {}
        # Patients whose all exams are done, ready for the game_loop to process.
        self.completed_patients = []

    def try_assign(self, patient, exam_catalog: dict) -> bool:
        """Try to assign patient to an available scanner. Returns True if successful."""
        # Prefer ED zone for highest-acuity patients.
        prefer_ed = patient.acuity == 1

        candidates = list(self.scanners.values())
        if prefer_ed:
            candidates.sort(key=lambda s: (0 if s.zone == "ED" else 1))

        for scanner in candidates:
            if not scanner.is_available:
                continue

            exam_key  = patient.exam_list[patient.current_exam_index]
            exam      = exam_catalog[exam_key]

            scanner.state           = ScannerState.SCANNING
            scanner.current_patient = patient.patient_id
            scanner.scan_timer      = SCAN_TIMES[exam_key]
            scanner.cooldown_timer  = 0

            patient.state           = PatientState.SCANNING
            self._scanning_patients[scanner.scanner_id] = patient
            return True

        return False

    def tick(self, exam_catalog: dict):
        """Advance scan and cooldown timers on all scanners."""
        for sid, scanner in self.scanners.items():
            if scanner.state == ScannerState.SCANNING:
                scanner.scan_timer -= 1
                if scanner.scan_timer <= 0:
                    # Scan finished — enter cooldown.
                    scanner.state         = ScannerState.COOLDOWN
                    scanner.cooldown_timer = SCANNER_COOLDOWN
                    patient = self._scanning_patients.get(sid)
                    if patient:
                        patient.state = PatientState.COOLDOWN

            elif scanner.state == ScannerState.COOLDOWN:
                scanner.cooldown_timer -= 1
                if scanner.cooldown_timer <= 0:
                    patient = self._scanning_patients.pop(sid, None)
                    scanner.current_patient = None

                    if patient is not None:
                        patient.current_exam_index += 1
                        if patient.current_exam_index < len(patient.exam_list):
                            # More exams to do — re-assign to same scanner immediately.
                            next_key           = patient.exam_list[patient.current_exam_index]
                            scanner.scan_timer = SCAN_TIMES[next_key]
                            scanner.state      = ScannerState.SCANNING
                            patient.state      = PatientState.SCANNING
                            self._scanning_patients[sid] = patient
                        else:
                            # All exams complete — queue for departure.
                            scanner.state = ScannerState.IDLE
                            self.completed_patients.append(patient)
