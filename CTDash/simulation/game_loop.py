# GameLoop — the main simulation tick.
# Each tick advances all timers by one game-second (TICK_SECONDS).
#
# Tick order (order matters — each step feeds the next):
#   1. staffing     — clock techs in/out (checked every tick for precision)
#   2. spawn        — probabilistic patient arrival
#   3. transport    — advance inbound/outbound timers; deliver to holding bay
#   4. queue        — increment wait_timers for all queued patients
#   5. contrast     — count down oral contrast timers; fire transport on expiry
#   6. scanner      — advance scan/cooldown timers; register outbound when done
#   7. assignment   — fill idle scanners from IN_HOLDING queue
#   8. events       — random REFUSED/CANCELLED checks
#   9. scoring      — wait penalty checks (once per game-minute per patient)

from simulation.shift_timer import ShiftTimer
from classes.patient import PatientState
from data.acuity_table import ACUITY_TABLE

# Terminal states — patients here need no further processing.
_TERMINAL = frozenset({
    PatientState.COMPLETED,
    PatientState.REFUSED,
    PatientState.CANCELLED,
    PatientState.HOLDOVER,
    PatientState.LEAVING,
})


class GameLoop:
    def __init__(self, managers: dict, duration_hours: int = None):
        """
        managers keys expected:
          spawn, transport, queue, contrast, scanner, staffing,
          scoring, event, holding, exam_catalog
        duration_hours: shift length in game-hours; drives ShiftTimer.
          Pass LEVELS[level]["shift_window"][1] - [0] from main.py.
        """
        self.timer    = ShiftTimer(duration_hours)
        self.managers = managers

    def run(self) -> int:
        """Main loop — runs until shift is over. Returns final score."""
        m = self.managers
        # Prime staffing so techs whose shift_start <= GAME_START_HOUR clock in
        # before the first patient can spawn.
        m["staffing"].tick(self.timer.game_hour, self.timer.game_minute)

        while not self.timer.is_shift_over:
            self._tick()
        return self._end_shift()

    # ------------------------------------------------------------------
    def _tick(self):
        self.timer.tick()
        game_hour   = self.timer.game_hour
        game_minute = self.timer.game_minute
        game_time   = self.timer._elapsed_seconds
        m           = self.managers

        # 1. Staffing — precise per-second check for clock-in/out boundaries
        m["staffing"].tick(game_hour, game_minute)

        # 2. Spawn
        m["spawn"].tick(game_hour, game_time)

        # 3. Transport
        delivered, departed = m["transport"].tick()
        for patient in delivered:
            try:
                in_overflow = m["holding"].admit(patient)
                if in_overflow:
                    m["scoring"].apply_overflow_penalty()
            except OverflowError:
                # Bay completely full — patient stays in corridor (IN_HOLDING state)
                # but is not tracked in bay capacity. Edge case; log in future.
                pass

        # Score exams on departure — once per exam for COMPLETED patients.
        # Multi-exam patients count each study individually.
        # REFUSED/CANCELLED patients that required outbound do not count.
        for patient in departed:
            if patient.state == PatientState.COMPLETED:
                for _ in patient.exam_list:
                    m["scoring"].exam_completed()

        # 4. Queue wait timers
        m["queue"].tick()

        # 5. Contrast timers
        m["contrast"].tick()

        # 6. Scanner timers
        m["scanner"].tick(m["exam_catalog"])

        # 7. Scanner assignment — fill all idle scanners
        while True:
            patient = m["queue"].peek_holding()
            if patient is None:
                break
            if m["scanner"].try_assign(patient, m["exam_catalog"]):
                m["queue"].remove(patient.patient_id)
                m["holding"].remove(patient.patient_id)
            else:
                break   # no scanner free; try again next tick

        # 8. Events
        scanner_patients = list(m["scanner"]._active_patients.values())
        m["event"].tick(m["queue"].all_patients + scanner_patients)

        # 9. Wait penalties — fire once per game-minute per over-threshold patient
        for patient in m["queue"].all_patients:
            if patient.state in _TERMINAL:
                continue
            threshold = ACUITY_TABLE.get(patient.acuity, {}).get("wait_threshold", 99999)
            if patient.wait_timer > threshold:
                excess = patient.wait_timer - threshold
                if excess % 60 == 0:
                    m["scoring"].apply_wait_penalty(patient.acuity, 60)

    # ------------------------------------------------------------------
    def _end_shift(self) -> int:
        m = self.managers

        # Collect every patient still in the system, dedup by patient_id.
        seen      = set()
        remaining = []
        sources   = (
            m["queue"].all_patients
            + list(m["scanner"]._active_patients.values())
            + m["holding"].all_patients()
        )
        for patient in sources:
            if patient.patient_id not in seen and patient.state not in _TERMINAL:
                patient.state = PatientState.HOLDOVER
                remaining.append(patient)
                seen.add(patient.patient_id)

        return m["scoring"].finalise(remaining)
