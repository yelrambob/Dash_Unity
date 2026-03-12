# Entry point — builds the simulation and runs it.
#
# Level controls:
#   - which exam tiers/types can spawn (min_level gating)
#   - shift window length (via GAME_DURATION_HOURS in config for now)
#   - number of scanners and techs (from LEVELS table)
#
# To run: python main.py  (defaults to level 1)

from classes.scanner import Scanner, ScannerState
from classes.holding_bay import HoldingBay
from managers.queue_manager import QueueManager
from managers.transport_manager import TransportManager
from managers.contrast_manager import ContrastManager
from managers.scanner_manager import ScannerManager
from managers.spawn_manager import SpawnManager
from managers.staffing_manager import StaffingManager
from managers.scoring_manager import ScoringManager
from managers.event_manager import EventManager
from simulation.game_loop import GameLoop
from data.exam_catalog import EXAM_CATALOG
from config import LEVELS


def build_scanners(level: int) -> list:
    """Create scanner instances based on level config. All start LOCKED."""
    n = LEVELS[level]["scanners"]
    scanners = []
    # First scanner is ED zone; remainder are Main.
    # StaffingManager unlocks each scanner as a tech clocks in.
    for i in range(n):
        zone = "ED" if i == 0 else "Main"
        scanners.append(Scanner(
            scanner_id = f"{zone.lower()}_{i + 1}",
            zone       = zone,
            state      = ScannerState.LOCKED,
        ))
    return scanners


def main(level: int = 1):
    scanners    = build_scanners(level)
    holding_bay = HoldingBay(zone="Main")

    queue       = QueueManager()
    transport   = TransportManager()
    contrast    = ContrastManager(transport)
    scanner_mgr = ScannerManager(scanners, transport)
    staffing    = StaffingManager(scanner_mgr)
    scoring     = ScoringManager()
    spawn       = SpawnManager(level, queue, transport, contrast)
    event       = EventManager(queue, transport, contrast, scanner_mgr, [holding_bay])

    managers = {
        "spawn":        spawn,
        "transport":    transport,
        "queue":        queue,
        "contrast":     contrast,
        "scanner":      scanner_mgr,
        "staffing":     staffing,
        "scoring":      scoring,
        "event":        event,
        "holding":      holding_bay,
        "exam_catalog": EXAM_CATALOG,
    }

    level_cfg   = LEVELS[level]
    start, end  = level_cfg["shift_window"]
    loop        = GameLoop(managers, duration_hours=(end - start))
    final_score = loop.run()

    print(f"Shift complete.")
    print(f"  Exams completed : {scoring.exams_completed}")
    print(f"  Holdovers       : {scoring.holdovers}")
    print(f"  Final score     : {final_score}")
    return final_score


if __name__ == "__main__":
    main(level=1)
