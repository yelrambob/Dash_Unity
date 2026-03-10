# [BUILD FIRST]
# ShiftTimer — controls the game clock.
# Tracks current game-time hour and minute.
# Fires hourly events to update spawn rate, staffing, and acuity weights.
# Triggers end-of-shift scoring when time runs out.

from config import TICK_SECONDS, GAME_DURATION_HOURS

GAME_START_HOUR = 6    # simulation starts at 06:00


class ShiftTimer:
    def __init__(self):
        self._elapsed_seconds = 0
        self._total_seconds   = GAME_DURATION_HOURS * 3600

    @property
    def game_hour(self) -> int:
        """Current game hour (0–23)."""
        return GAME_START_HOUR + (self._elapsed_seconds // 3600)

    @property
    def game_minute(self) -> int:
        return (self._elapsed_seconds % 3600) // 60

    @property
    def is_shift_over(self) -> bool:
        return self._elapsed_seconds >= self._total_seconds

    def tick(self):
        """Advance the clock by one tick. Returns True if a new hour just started."""
        prev_hour = self.game_hour
        self._elapsed_seconds += TICK_SECONDS
        return self.game_hour != prev_hour    # True = hourly event should fire
