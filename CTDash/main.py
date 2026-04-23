# [BUILD FIRST]
# Entry point — runs the simulation.
# Imports everything else and controls the game loop.
# Start here once all class files exist.

from classes.scanner import Scanner, ScannerState
from config import LEVELS
from data.exam_catalog import EXAM_CATALOG
from managers.contrast_manager import ContrastManager
from managers.queue_manager import QueueManager
from managers.scanner_manager import ScannerManager
from managers.scoring_manager import ScoringManager
from managers.spawn_manager import SpawnManager
from managers.staffing_manager import StaffingManager
from managers.transport_manager import TransportManager
from simulation.game_loop import GameLoop


def main(level: int = 1):
    cfg = LEVELS[level]

    # Build scanners — all start LOCKED until staffing assigns techs.
    scanners = []
    for i in range(cfg["scanners"]):
        zone = "ED" if i == 0 else "Main"
        scanners.append(Scanner(
            scanner_id=f"SCANNER_{zone}_{i + 1}",
            zone=zone,
            state=ScannerState.LOCKED,
        ))

    # Wire up managers.
    queue_mgr     = QueueManager()
    scanner_mgr   = ScannerManager(scanners)
    transport_mgr = TransportManager()
    contrast_mgr  = ContrastManager()
    scoring_mgr   = ScoringManager()
    spawn_mgr     = SpawnManager(queue_mgr)
    staffing_mgr  = StaffingManager(scanner_mgr)

    managers = {
        "spawn":     spawn_mgr,
        "queue":     queue_mgr,
        "transport": transport_mgr,
        "contrast":  contrast_mgr,
        "scanner":   scanner_mgr,
        "scoring":   scoring_mgr,
        "staffing":  staffing_mgr,
    }

    start_h, end_h = cfg["shift_window"]
    duration_hours  = end_h - start_h
    loop = GameLoop(managers, EXAM_CATALOG, duration_hours=duration_hours)
    loop.run()


if __name__ == "__main__":
    main()
