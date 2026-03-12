# StaffingManager — controls tech clock-in/out and scanner assignment.
#
# Each tick receives the current game hour and minute.
# When a tech's shift_start is reached → clock them in and assign to a scanner.
# When shift_end is reached → unassign and lock the scanner.
#
# Assignment strategy: first available LOCKED scanner (no zone preference —
# zone routing is handled by ScannerManager._pick_scanner at scan time).
# If more techs than scanners: excess techs remain unassigned (edge case).
# If mid-scan at clock-out: tech departs but scanner finishes the scan;
# the scanner then sits unassigned and won't accept new patients until
# is_available is True again (requires assigned_tech is not None).
#
# Staffing arc (default roster):
#   07:00 – 15:30  day shift techs
#   Additional afternoon/evening techs defined in tech_roster.py

from classes.tech import Tech, TechStatus
from classes.scanner import ScannerState
from data.tech_roster import TECH_ROSTER


class StaffingManager:
    def __init__(self, scanner_manager):
        self.scanner_manager = scanner_manager

        # Build Tech objects from roster at init.
        self._all_techs = {
            row["id"]: Tech(
                tech_id     = row["id"],
                name        = row["name"],
                speed       = row["speed"],
                accuracy    = row["accuracy"],
                willingness = row["willingness"],
                diligence   = row["diligence"],
                shift_start = row["shift_start"],
                shift_end   = row["shift_end"],
            )
            for row in TECH_ROSTER
        }

        self._active_techs = {}    # tech_id -> Tech (currently on shift)

    # ------------------------------------------------------------------
    def tick(self, game_hour: int, game_minute: int):
        """
        Check for tech arrivals and departures at the current game time.
        Called once per game-second from GameLoop (and once at init).
        """
        current = game_hour + game_minute / 60.0

        for tech in self._all_techs.values():
            if tech.status == TechStatus.OFF_SHIFT:
                if current >= tech.shift_start:
                    self._clock_in(tech)
            else:
                if current >= tech.shift_end:
                    self._clock_out(tech)

    # ------------------------------------------------------------------
    @property
    def active_techs(self) -> list:
        return list(self._active_techs.values())

    # ------------------------------------------------------------------
    def _clock_in(self, tech: Tech):
        tech.status = TechStatus.IDLE
        self._active_techs[tech.tech_id] = tech

        # Assign to the first unassigned (LOCKED) scanner.
        scanner = self._find_unassigned_scanner()
        if scanner:
            scanner.assigned_tech = tech
            scanner.state         = ScannerState.IDLE
            tech.assigned_scanner = scanner.scanner_id

    def _clock_out(self, tech: Tech):
        tech.status = TechStatus.OFF_SHIFT
        self._active_techs.pop(tech.tech_id, None)

        if tech.assigned_scanner:
            scanner = self.scanner_manager.scanners.get(tech.assigned_scanner)
            if scanner:
                scanner.assigned_tech = None
                # Only hard-lock if idle — mid-scan, let it finish naturally.
                # is_available will return False (no tech) so no new patients.
                if scanner.state == ScannerState.IDLE:
                    scanner.state = ScannerState.LOCKED
            tech.assigned_scanner = None

    def _find_unassigned_scanner(self):
        """Return the first scanner with no assigned tech, or None."""
        for scanner in self.scanner_manager.scanners.values():
            if scanner.assigned_tech is None:
                return scanner
        return None
