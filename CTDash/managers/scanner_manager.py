# [BUILD FIRST]
# ScannerManager — controls scanner assignment and scan lifecycle.
# Zone preference: trauma/acuity-1 patients go to ED CT first.
# Checks tech availability before assigning a patient to a scanner.
# Manages multi-exam sequences (patient stays until all exams done).
# Tracks scan timer and cooldown timer per scanner.

from classes.scanner import ScannerState


class ScannerManager:
    def __init__(self, scanners: list):
        # scanners: list of Scanner objects, passed in from game_loop
        self.scanners = {s.scanner_id: s for s in scanners}

    def try_assign(self, patient, exam_catalog: dict):
        """Try to assign patient to an available scanner. Returns True if successful."""
        # TODO: pick scanner by zone preference, check is_available,
        #       set scanner state to SCANNING, attach patient
        pass

    def tick(self, exam_catalog: dict):
        """Advance scan and cooldown timers on all scanners."""
        # TODO: count down scan_timer, transition to COOLDOWN,
        #       count down cooldown_timer, transition back to IDLE,
        #       handle multi-exam: if more exams remain, re-enter SCANNING
        pass
