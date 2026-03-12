# [BUILD FIRST]
# ShiftTimer — controls the game clock.
# Tracks current game-time hour and minute.
# Fires hourly events to update spawn rate, staffing, and acuity weights.
# Triggers end-of-shift scoring when time runs out.

from config import TICK_SECONDS, GAME_DURATION_HOURS

GAME_START_HOUR = 7    # simulation starts at 07:00 (first tech clock-in)
                       # TODO: make this level-configurable via shift_window[0]


class ShiftTimer:
    def __init__(self, duration_hours: int = None):
        """
        duration_hours: override GAME_DURATION_HOURS for this run.
        Pass the level's shift window length (shift_window[1] - shift_window[0]).
        """
        self._elapsed_seconds = 0
        hours = duration_hours if duration_hours is not None else GAME_DURATION_HOURS
        self._total_seconds   = hours * 3600

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
