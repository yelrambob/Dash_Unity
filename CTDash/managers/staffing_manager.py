# [LATER] — depends on Tech class and tech_roster.py
# StaffingManager — controls tech availability by game-time hour.
# Drives which scanners are open (IDLE) vs locked (LOCKED).
# Handles tech arrival and departure events.
#
# Staffing arc:
#   Early game (06–09): 2–3 techs
#   Peak (10–17):       up to 4 techs
#   Taper (18–20):      2–3 techs

from data.tech_roster import TECH_ROSTER


class StaffingManager:
    def __init__(self, scanner_manager):
        self.scanner_manager = scanner_manager
        self._active_techs = {}    # tech_id -> Tech object

    def tick(self, game_hour: float):
        """Check for tech arrivals and departures at current game hour."""
        # TODO: iterate TECH_ROSTER, activate techs on shift_start,
        #       deactivate on shift_end, update scanner locked/unlocked state
        pass
