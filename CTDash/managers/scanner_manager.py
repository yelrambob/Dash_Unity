# ScannerManager — controls the full lifecycle of a patient at the scanner.
#
# Sequence per patient visit:
#   1. try_assign()  — pick an available scanner, start SETUP phase
#   2. SETUP timer   — setup_delay (mobility-scaled) × willingness_mult
#   3. SCAN timer    — exam scan_time × speed_mult
#   4. COOLDOWN      — SCANNER_COOLDOWN × speed_mult × accuracy_mult
#   5. More exams?   — if patient.exam_list has remaining exams, go to step 2
#   6. Done          — call transport_manager.register_outbound(patient)
#                      scanner returns to IDLE
#
# Tech attribute → phase mapping:
#   willingness → setup   (hustle getting patient on table)
#   speed       → scan    (drives protocol execution speed)
#   speed       → cooldown (minor — fast tech doesn't linger)
#   accuracy    → cooldown (major — clean positioning = fast room reset)
#
# Zone preference:
#   Acuity tier 1 (Trauma/Stroke) → ED scanner first, fall back to Main
#   All others                    → Main scanners first, fall back to ED
#
# Tech requirement:
#   scanner.is_available requires assigned_tech is not None.
#   Tech assignment is handled by StaffingManager — this class only checks.

from classes.scanner import ScannerState
from classes.patient import PatientState
from config import (
    SCANNER_COOLDOWN,
    TECH_SCAN_SPEED_RANGE, TECH_SETUP_WILLINGNESS_RANGE,
    TECH_COOLDOWN_SPEED_RANGE, TECH_COOLDOWN_ACCURACY_RANGE,
)


# Internal marker stored in scanner to distinguish SETUP phase from SCAN phase.
# Avoids adding a new ScannerState to the enum just for this.
_PHASE_SETUP = "setup"
_PHASE_SCAN  = "scan"


class ScannerManager:
    def __init__(self, scanners: list, transport_manager):
        self.scanners          = {s.scanner_id: s for s in scanners}
        self.transport_manager = transport_manager
        # Track which phase each scanner is in: scanner_id -> _PHASE_SETUP | _PHASE_SCAN
        self._phase            = {}
        # Patient objects for patients currently on a scanner
        self._active_patients  = {}   # scanner_id -> Patient

    # ------------------------------------------------------------------
    def try_assign(self, patient, exam_catalog: dict) -> bool:
        """
        Attempt to assign patient to an available scanner.
        Respects zone preference and tech availability.
        Returns True if assigned, False if no scanner is available.
        """
        scanner = self._pick_scanner(patient.acuity)
        if scanner is None:
            return False

        exam_key = patient.exam_list[patient.current_exam_index]
        exam     = exam_catalog[exam_key]
        tech     = scanner.assigned_tech   # Tech object (guaranteed non-None by is_available)

        # Setup: mobility-scaled by TransportManager, then further scaled by tech willingness.
        # Scan: scaled by tech speed.
        setup     = int(patient.transport.setup_delay * self._setup_mult(tech))
        scan_time = int(exam.scan_time * self._scan_mult(tech))
        scanner.scan_timer      = setup + scan_time
        scanner.cooldown_timer  = 0
        scanner.current_patient = patient.patient_id
        scanner.state           = ScannerState.SCANNING

        self._phase[scanner.scanner_id]           = _PHASE_SETUP
        self._active_patients[scanner.scanner_id] = patient
        patient.state = PatientState.SCANNING

        return True

    # ------------------------------------------------------------------
    def tick(self, exam_catalog: dict, game_seconds: int = 1):
        """
        Advance all scanner timers by game_seconds.

        Handles state transitions:
          SCANNING (setup+scan) → COOLDOWN → IDLE (or next exam's SCANNING)
        Calls transport_manager.register_outbound() when all exams are done.
        """
        for sid, scanner in self.scanners.items():

            # If the active patient has a pending acknowledgment (REFUSED/CANCELLED),
            # freeze the scanner until EventManager.acknowledge() calls release_patient().
            active = self._active_patients.get(sid)
            if active is not None and active.pending_acknowledgment:
                continue

            if scanner.state == ScannerState.SCANNING:
                scanner.scan_timer -= game_seconds
                if scanner.scan_timer <= 0:
                    tech = scanner.assigned_tech
                    scanner.state          = ScannerState.COOLDOWN
                    scanner.cooldown_timer = int(SCANNER_COOLDOWN * self._cooldown_mult(tech))

            elif scanner.state == ScannerState.COOLDOWN:
                scanner.cooldown_timer -= game_seconds
                if scanner.cooldown_timer <= 0:
                    patient = self._active_patients.get(sid)
                    if patient is None:
                        scanner.state = ScannerState.IDLE
                        continue

                    patient.current_exam_index += 1
                    remaining = patient.current_exam_index < len(patient.exam_list)

                    if remaining:
                        # More exams — reload with tech scaling for next exam
                        exam_key  = patient.exam_list[patient.current_exam_index]
                        exam      = exam_catalog[exam_key]
                        tech      = scanner.assigned_tech
                        setup     = int(patient.transport.setup_delay * self._setup_mult(tech))
                        scan_time = int(exam.scan_time * self._scan_mult(tech))
                        scanner.scan_timer = setup + scan_time
                        scanner.state      = ScannerState.SCANNING
                    else:
                        # All done — free scanner, hand patient back to transport
                        scanner.state           = ScannerState.IDLE
                        scanner.current_patient = None
                        scanner.scan_timer      = 0
                        self._phase.pop(sid, None)
                        self._active_patients.pop(sid, None)
                        self.transport_manager.register_outbound(patient)

    # ------------------------------------------------------------------
    def release_patient(self, scanner_id: str):
        """
        Free a scanner that is holding a REFUSED or CANCELLED patient.
        Called by EventManager.acknowledge() after the player dismisses the event.
        The patient's outbound transport is handled separately by EventManager.
        """
        scanner = self.scanners.get(scanner_id)
        if scanner:
            scanner.state           = ScannerState.IDLE
            scanner.current_patient = None
            scanner.scan_timer      = 0
            scanner.cooldown_timer  = 0
        self._phase.pop(scanner_id, None)
        self._active_patients.pop(scanner_id, None)

    # ------------------------------------------------------------------
    def _setup_mult(self, tech) -> float:
        """Setup time multiplier from tech willingness."""
        if tech is None:
            return 1.0
        return self._attr_mult(tech.willingness, TECH_SETUP_WILLINGNESS_RANGE)

    def _scan_mult(self, tech) -> float:
        """Scan time multiplier from tech speed."""
        if tech is None:
            return 1.0
        return self._attr_mult(tech.speed, TECH_SCAN_SPEED_RANGE)

    def _cooldown_mult(self, tech) -> float:
        """Combined cooldown multiplier from tech speed and accuracy."""
        if tech is None:
            return 1.0
        speed_m = self._attr_mult(tech.speed,    TECH_COOLDOWN_SPEED_RANGE)
        acc_m   = self._attr_mult(tech.accuracy, TECH_COOLDOWN_ACCURACY_RANGE)
        return speed_m * acc_m

    @staticmethod
    def _attr_mult(attr: float, attr_range: tuple) -> float:
        """
        Map a tech attribute (0.0–1.0) to a timing multiplier.
        attr=1.0 (best) → attr_range[0] (fastest)
        attr=0.0 (worst) → attr_range[1] (slowest)
        """
        low, high = attr_range
        return high - attr * (high - low)

    # ------------------------------------------------------------------
    def _pick_scanner(self, acuity: int):
        """
        Return the best available scanner for this acuity tier, or None.
        Tier 1 → prefer ED; all others → prefer Main.
        Falls back to any available scanner if preferred zone is full.
        """
        prefer_ed = (acuity == 1)
        preferred = "ED"   if prefer_ed else "Main"
        fallback  = "Main" if prefer_ed else "ED"

        for zone in (preferred, fallback):
            for scanner in self.scanners.values():
                if scanner.zone == zone and scanner.is_available:
                    return scanner
        return None
