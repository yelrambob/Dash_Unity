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

from simulation.shift_timer import ShiftTimer


class GameLoop:
    def __init__(self, managers: dict):
        # managers: dict of {name: manager_instance}
        # e.g. {"spawn": SpawnManager(...), "scanner": ScannerManager(...), ...}
        self.timer    = ShiftTimer()
        self.managers = managers

    def run(self):
        """Main loop — runs until shift is over."""
        while not self.timer.is_shift_over:
            self._tick()
        self._end_shift()

    def _tick(self):
        new_hour = self.timer.tick()
        # TODO: call each manager in order, pass game_hour where needed
        # if new_hour: fire hourly events (spawn rate update, staffing check)

    def _end_shift(self):
        # TODO: call scoring_manager.finalise(), print or return result
        pass
