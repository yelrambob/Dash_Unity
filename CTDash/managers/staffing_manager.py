# [LATER] — depends on Tech class and tech_roster.py
# StaffingManager — controls tech availability by game-time hour.
# Drives which scanners are open (IDLE) vs locked (LOCKED).
# Handles tech arrival and departure events.
#
# Staffing arc:
#   Early game (06–09): 2–3 techs
#   Peak (10–17):       up to 4 techs
#   Taper (18–20):      2–3 techs

from classes.tech import Tech, TechStatus
from classes.scanner import ScannerState
from data.tech_roster import TECH_ROSTER


class StaffingManager:
    def __init__(self, scanner_manager):
        self.scanner_manager = scanner_manager
        self._active_techs   = {}    # tech_id -> Tech object
        # Pre-build Tech objects from roster; all start off-shift.
        self._all_techs = {
            row["id"]: Tech(
                tech_id        = row["id"],
                name           = row["name"],
                speed          = row["speed"],
                accuracy       = row["accuracy"],
                willingness    = row["willingness"],
                knowledge_base = row["knowledge_base"],
                shift_start    = row["shift_start"],
                shift_end      = row["shift_end"],
            )
            for row in TECH_ROSTER
        }

    def tick(self, game_hour: float):
        """Check for tech arrivals and departures at current game hour."""
        for tech in self._all_techs.values():
            on_shift  = tech.shift_start <= game_hour < tech.shift_end
            is_active = tech.tech_id in self._active_techs

            if on_shift and not is_active:
                # Tech arriving — activate and assign to a LOCKED scanner.
                tech.status = TechStatus.IDLE
                self._active_techs[tech.tech_id] = tech
                self._assign_tech_to_scanner(tech)

            elif not on_shift and is_active:
                # Tech departing — unassign from scanner, lock it.
                self._unassign_tech(tech)
                tech.status = TechStatus.OFF_SHIFT
                del self._active_techs[tech.tech_id]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _assign_tech_to_scanner(self, tech: Tech):
        """Find a LOCKED or unassigned scanner and assign this tech to it."""
        scanners = self.scanner_manager.scanners
        for scanner in scanners.values():
            if scanner.assigned_tech is None:
                scanner.assigned_tech = tech.tech_id
                tech.assigned_scanner = scanner.scanner_id
                if scanner.state == ScannerState.LOCKED:
                    scanner.state = ScannerState.IDLE
                return

    def _unassign_tech(self, tech: Tech):
        """Remove tech from their scanner and lock it if no patient is active."""
        if tech.assigned_scanner is None:
            return
        scanners = self.scanner_manager.scanners
        scanner  = scanners.get(tech.assigned_scanner)
        if scanner:
            scanner.assigned_tech = None
            tech.assigned_scanner = None
            if scanner.state == ScannerState.IDLE:
                scanner.state = ScannerState.LOCKED
