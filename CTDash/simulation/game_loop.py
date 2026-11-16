# [BUILD FIRST]
# GameLoop — the main simulation tick.
# Each tick advances all timers by one time step (defined in config.TICK_SECONDS).
# Managers are called in a fixed order each tick — order matters.
#
# Correct tick order:
#   1. shift_timer  — advance clock, check for hourly events
#   2. spawn        — maybe spawn a new patient
#   3. transport    — advance transport state machines
#   4. queue        — advance wait timers
#   5. contrast     — advance contrast timers
#   6. scanner      — advance scan/cooldown timers
#   7. scoring      — check for penalties, update score display

from classes.patient import PatientState
from config import HOLDING_PROPER_SLOTS
from data.acuity_table import ACUITY_TABLE
from simulation.shift_timer import ShiftTimer


class GameLoop:
    def __init__(self, managers: dict, exam_catalog: dict, duration_hours: int = None):
        # managers: dict of {name: manager_instance}
        # e.g. {"spawn": SpawnManager(...), "scanner": ScannerManager(...), ...}
        self.timer        = ShiftTimer(duration_hours) if duration_hours else ShiftTimer()
        self.managers     = managers
        self.exam_catalog = exam_catalog

        # Master patient registry: patient_id -> Patient.
        self._patients = {}
        # Patients that have already been charged the overflow penalty.
        self._overflow_charged = set()

    def run(self) -> int:
        """Main loop — runs until shift is over. Returns final score."""
        while not self.timer.is_shift_over:
            self._tick()
        self._end_shift()
        return self.managers["scoring"].score

    def _tick(self):
        # 1. Advance clock.
        new_hour = self.timer.tick()
        gs = self.timer.game_second
        gh = self.timer.game_hour

        # 2. Spawn — may add patients to queue_manager.
        self.managers["spawn"].tick(gh, gs)

        # Sync newly spawned patients into our master registry and start transport.
        for pid, patient in list(self.managers["queue"]._patients.items()):
            if pid not in self._patients:
                self._patients[pid] = patient
                self.managers["transport"].assign_transport(patient)

        # 3. Transport — advance state machines; sets IN_HOLDING on delivery.
        self.managers["transport"].tick()

        # 4. Queue — increment wait timers for all queued patients.
        self.managers["queue"].tick(gs)

        # 5. Contrast — count down oral contrast timers.
        self.managers["contrast"].tick()

        # 6. Start oral contrast for newly arrived patients that need it.
        self._order_contrast_if_needed()

        # 7. Scanner — advance scan/cooldown timers.
        self.managers["scanner"].tick(self.exam_catalog)

        # 8. Process patients whose all exams are done.
        self._handle_completed_scans()

        # 9. Assign highest-priority ready patients to idle scanners.
        self._try_assign_to_scanners()

        # 10. Apply wait penalties.
        self._apply_wait_penalties()

        # 11. Overflow check.
        self._check_overflow()

        # 12. Staffing — fires only on new game-hour boundary.
        if new_hour:
            self.managers["staffing"].tick(float(gh))

    def _end_shift(self):
        remaining = [
            p for p in self._patients.values()
            if p.state not in (PatientState.COMPLETED, PatientState.REFUSED)
        ]
        final_score = self.managers["scoring"].finalise(remaining)
        print(f"\n=== Shift Over ===")
        print(f"Exams completed : {self.managers['scoring'].exams_completed}")
        print(f"Holdovers       : {self.managers['scoring'].holdovers}")
        print(f"Final score     : {final_score}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _order_contrast_if_needed(self):
        """Kick off oral contrast for IN_HOLDING patients whose exam requires it."""
        contrast_mgr = self.managers["contrast"]
        for patient in self._patients.values():
            if patient.state != PatientState.IN_HOLDING:
                continue
            if patient.current_exam_index >= len(patient.exam_list):
                continue
            exam_key = patient.exam_list[patient.current_exam_index]
            exam     = self.exam_catalog[exam_key]
            if exam.oral_contrast:
                contrast_mgr.start_oral_contrast(patient)

    def _try_assign_to_scanners(self):
        """Assign highest-priority ready patients to idle scanners."""
        scanner_mgr  = self.managers["scanner"]
        contrast_mgr = self.managers["contrast"]

        ready = sorted(
            [p for p in self._patients.values()
             if p.state in (PatientState.IN_HOLDING, PatientState.CONTRAST_READY,
                            PatientState.INJECTOR_READY)
             and p.current_exam_index < len(p.exam_list)],
            key=lambda p: (p.acuity, -p.wait_timer),
        )

        for patient in ready:
            exam_key = patient.exam_list[patient.current_exam_index]
            exam     = self.exam_catalog[exam_key]

            # If IV contrast needed and injector not yet filled, fill it first.
            if patient.state == PatientState.CONTRAST_READY and exam.iv_contrast:
                contrast_mgr.fill_injector(patient)
                continue

            assigned = scanner_mgr.try_assign(patient, self.exam_catalog)
            if assigned:
                # Remove from queue once assigned; no longer needs wait-timer tracking.
                self.managers["queue"]._patients.pop(patient.patient_id, None)

    def _handle_completed_scans(self):
        """Handle patients whose entire exam list is finished."""
        scanner_mgr = self.managers["scanner"]
        for patient in scanner_mgr.completed_patients:
            self.managers["scoring"].exam_completed(patient.acuity)
            self.managers["transport"].begin_leaving(patient)
        scanner_mgr.completed_patients.clear()
        # TransportManager.tick() marks LEAVING patients COMPLETED on delivery.

    def _apply_wait_penalties(self):
        """Deduct points for patients waiting past their acuity threshold."""
        for patient in self._patients.values():
            if patient.state in (PatientState.COMPLETED, PatientState.REFUSED,
                                  PatientState.SCANNING, PatientState.COOLDOWN,
                                  PatientState.LEAVING):
                continue
            threshold = ACUITY_TABLE[patient.acuity]["wait_threshold"]
            excess = patient.wait_timer - threshold
            if excess > 0 and excess % 60 == 0:
                self.managers["scoring"].apply_wait_penalty(patient.acuity, 60)

    def _check_overflow(self):
        """One-time flat penalty when a patient first occupies an overflow slot."""
        holding = sorted(
            [p for p in self._patients.values() if p.state == PatientState.IN_HOLDING],
            key=lambda p: (p.acuity, -p.wait_timer),
        )
        for i, patient in enumerate(holding):
            if i >= HOLDING_PROPER_SLOTS:
                if patient.patient_id not in self._overflow_charged:
                    self._overflow_charged.add(patient.patient_id)
                    self.managers["scoring"].apply_overflow_penalty()
