"""
generate_ctdash.py

Run this script once from wherever you want the project to live.
It creates the full CTDash folder structure with stub files.
All comments and status tags are pre-populated.

Usage:
    python generate_ctdash.py

This will create a CTDash/ folder in your current directory.
If CTDash/ already exists, existing files will NOT be overwritten.
"""

import os

# ---------------------------------------------------------------------------
# Each entry is: (relative_path, file_contents_as_string)
# ---------------------------------------------------------------------------
FILES = [

    # -----------------------------------------------------------------------
    # main.py
    # -----------------------------------------------------------------------
    ("main.py", '''\
# [BUILD FIRST]
# Entry point — runs the simulation.
# Imports everything else and controls the game loop.
# Start here once all class files exist.

from simulation.game_loop import GameLoop


def main():
    # TODO: initialise managers, pass into GameLoop, call loop.run()
    pass


if __name__ == "__main__":
    main()
'''),

    # -----------------------------------------------------------------------
    # config.py
    # -----------------------------------------------------------------------
    ("config.py", '''\
# [BUILD FIRST]
# Central location for all tunable numbers.
# Changing a value here affects the whole simulation.
# No logic lives here — just values.

# --- Scan times (in game-time seconds) ------------------------------------
SCAN_TIMES = {
    "head":        60,
    "abdpel":      90,
    "trauma_full": 120,
    # Add more exam types here as exam_catalog.py grows
}

# --- Delay ranges (min, max) in game-time seconds -------------------------
TRANSPORT_ARRIVAL_DELAY  = (30, 120)   # time from order to transport arriving
TRANSPORT_HOLD_WAIT      = (10,  60)   # time patient waits in transport before being brought up
TRANSPORT_LEAVING_DELAY  = (10,  30)   # time from scan complete to transport leaving

# --- Contrast timings -----------------------------------------------------
ORAL_CONTRAST_WAIT       = 45 * 60     # 45 game-minutes in seconds
INJECTOR_FILL_TIME       = 5  * 60     # 5 game-minutes

# --- Holding bay capacity -------------------------------------------------
HOLDING_PROPER_SLOTS     = 4
HOLDING_OVERFLOW_SLOTS   = 2

# --- Scoring --------------------------------------------------------------
WAIT_PENALTY_PER_MINUTE  = 1           # points lost per minute over threshold
OVERFLOW_PENALTY         = 10          # flat penalty per overflow patient
HOLDOVER_PENALTY         = 25          # flat penalty per holdover at end of shift

# --- Simulation tick ------------------------------------------------------
TICK_SECONDS             = 1           # how many game-seconds pass per tick
GAME_DURATION_HOURS      = 14          # 06:00 – 20:00 window
'''),

    # -----------------------------------------------------------------------
    # data/hourly_spawn_weights.py
    # -----------------------------------------------------------------------
    ("data/hourly_spawn_weights.py", '''\
# [BUILD FIRST]
# The 24-hour spawn rate table derived from real exam volume data.
# Each hour maps to: exams_per_hour, spawn_weight, acuity_bias.
#
# acuity_bias: float 0.0–1.0 — higher = more high-acuity patients that hour.
# spawn_weight: relative probability used by SpawnManager to throttle flow.
#
# Based on 6 months of real hourly data:
#   Quiet overnight: ~4 exams/hr
#   Ramp starts:     hour 08
#   Peak plateau:    hours 11–17 (~16–18 exams/hr)
#   Evening taper:   hours 18–20

HOURLY_SPAWN_TABLE = {
    #  hour: {"exams_per_hour": int, "spawn_weight": float, "acuity_bias": float}
     0: {"exams_per_hour":  4, "spawn_weight": 0.25, "acuity_bias": 0.6},
     1: {"exams_per_hour":  3, "spawn_weight": 0.20, "acuity_bias": 0.6},
     2: {"exams_per_hour":  3, "spawn_weight": 0.20, "acuity_bias": 0.6},
     3: {"exams_per_hour":  3, "spawn_weight": 0.20, "acuity_bias": 0.6},
     4: {"exams_per_hour":  4, "spawn_weight": 0.25, "acuity_bias": 0.5},
     5: {"exams_per_hour":  4, "spawn_weight": 0.25, "acuity_bias": 0.5},
     6: {"exams_per_hour":  5, "spawn_weight": 0.30, "acuity_bias": 0.4},
     7: {"exams_per_hour":  7, "spawn_weight": 0.45, "acuity_bias": 0.4},
     8: {"exams_per_hour": 10, "spawn_weight": 0.65, "acuity_bias": 0.35},
     9: {"exams_per_hour": 13, "spawn_weight": 0.80, "acuity_bias": 0.35},
    10: {"exams_per_hour": 15, "spawn_weight": 0.90, "acuity_bias": 0.30},
    11: {"exams_per_hour": 17, "spawn_weight": 1.00, "acuity_bias": 0.30},
    12: {"exams_per_hour": 18, "spawn_weight": 1.00, "acuity_bias": 0.30},
    13: {"exams_per_hour": 17, "spawn_weight": 1.00, "acuity_bias": 0.30},
    14: {"exams_per_hour": 16, "spawn_weight": 0.95, "acuity_bias": 0.30},
    15: {"exams_per_hour": 16, "spawn_weight": 0.95, "acuity_bias": 0.30},
    16: {"exams_per_hour": 16, "spawn_weight": 0.95, "acuity_bias": 0.30},
    17: {"exams_per_hour": 15, "spawn_weight": 0.90, "acuity_bias": 0.35},
    18: {"exams_per_hour": 12, "spawn_weight": 0.75, "acuity_bias": 0.40},
    19: {"exams_per_hour":  9, "spawn_weight": 0.55, "acuity_bias": 0.45},
    20: {"exams_per_hour":  7, "spawn_weight": 0.45, "acuity_bias": 0.50},
    21: {"exams_per_hour":  6, "spawn_weight": 0.38, "acuity_bias": 0.55},
    22: {"exams_per_hour":  5, "spawn_weight": 0.30, "acuity_bias": 0.60},
    23: {"exams_per_hour":  4, "spawn_weight": 0.25, "acuity_bias": 0.60},
}
'''),

    # -----------------------------------------------------------------------
    # data/exam_catalog.py
    # -----------------------------------------------------------------------
    ("data/exam_catalog.py", '''\
# [BUILD FIRST]
# Every exam type available in the game.
# Add new exam types here without touching any other file.
#
# Each entry is a dict — will be used to construct Exam objects in exam.py.
# Keys:
#   scan_time         — base scan duration in game-seconds (tuned in config.py)
#   iv_contrast       — bool, does this exam require IV contrast?
#   oral_contrast     — bool, does this exam require oral contrast (wait timer)?
#   difficulty        — float 1.0–3.0, affects tech accuracy penalty

from classes.exam import Exam

EXAM_CATALOG = {
    "head": Exam(
        name="head",
        scan_time=60,
        iv_contrast=False,
        oral_contrast=False,
        difficulty=1.0,
    ),
    "abdpel": Exam(
        name="abdpel",
        scan_time=90,
        iv_contrast=True,
        oral_contrast=True,
        difficulty=1.5,
    ),
    "trauma_full": Exam(
        name="trauma_full",
        scan_time=120,
        iv_contrast=True,
        oral_contrast=False,
        difficulty=2.5,
    ),
    # TODO: add chest, cta_head, cta_chest, spine, extremity, etc.
}
'''),

    # -----------------------------------------------------------------------
    # data/acuity_table.py
    # -----------------------------------------------------------------------
    ("data/acuity_table.py", '''\
# [BUILD FIRST]
# Defines acuity levels 1–5 (1 = most critical, 5 = routine).
# Each level controls spawn weighting, queue priority,
# typical exam types, and wait penalty calculation.

ACUITY_TABLE = {
    1: {
        "label":           "Trauma / Critical",
        "queue_priority":  1,          # lower = higher priority in queue
        "spawn_weight":    0.10,       # base fraction of spawns at this acuity
        "typical_exams":  ["trauma_full", "head"],
        "wait_threshold":  5 * 60,     # seconds before wait penalty kicks in
        "penalty_mult":    3.0,        # multiplier on WAIT_PENALTY_PER_MINUTE
    },
    2: {
        "label":           "Emergent",
        "queue_priority":  2,
        "spawn_weight":    0.20,
        "typical_exams":  ["head", "abdpel"],
        "wait_threshold":  10 * 60,
        "penalty_mult":    2.0,
    },
    3: {
        "label":           "Urgent",
        "queue_priority":  3,
        "spawn_weight":    0.35,
        "typical_exams":  ["abdpel", "head"],
        "wait_threshold":  20 * 60,
        "penalty_mult":    1.5,
    },
    4: {
        "label":           "Semi-urgent",
        "queue_priority":  4,
        "spawn_weight":    0.25,
        "typical_exams":  ["abdpel"],
        "wait_threshold":  30 * 60,
        "penalty_mult":    1.0,
    },
    5: {
        "label":           "Routine",
        "queue_priority":  5,
        "spawn_weight":    0.10,
        "typical_exams":  ["abdpel"],
        "wait_threshold":  45 * 60,
        "penalty_mult":    0.5,
    },
}
'''),

    # -----------------------------------------------------------------------
    # data/tech_roster.py
    # -----------------------------------------------------------------------
    ("data/tech_roster.py", '''\
# [LATER] — depends on tech.py being built first
# Pre-built tech profiles for early game levels.
# Each tech has: speed, accuracy, willingness, knowledge_base (all 0.0–1.0).
# Arrival and departure times are in game-time hours (e.g. 7.0 = 07:00).
# Later difficulty levels will have worse stat distributions.

TECH_ROSTER = [
    {
        "id":             "tech_01",
        "name":           "Alex",
        "speed":          0.85,
        "accuracy":       0.90,
        "willingness":    0.80,
        "knowledge_base": 0.85,
        "shift_start":    7.0,
        "shift_end":      15.5,
    },
    {
        "id":             "tech_02",
        "name":           "Jordan",
        "speed":          0.70,
        "accuracy":       0.75,
        "willingness":    0.65,
        "knowledge_base": 0.70,
        "shift_start":    7.0,
        "shift_end":      15.5,
    },
    # TODO: add afternoon and evening techs
]
'''),

    # -----------------------------------------------------------------------
    # classes/exam.py
    # -----------------------------------------------------------------------
    ("classes/exam.py", '''\
# [BUILD FIRST]
# Exam class — represents a single scan type.
# No logic here; just holds data about what an exam IS.

from dataclasses import dataclass


@dataclass
class Exam:
    name: str            # short key matching exam_catalog.py
    scan_time: int       # base duration in game-seconds
    iv_contrast: bool    # requires IV contrast injection
    oral_contrast: bool  # requires oral contrast wait timer
    difficulty: float    # 1.0–3.0, affects tech accuracy penalty
'''),

    # -----------------------------------------------------------------------
    # classes/transport.py
    # -----------------------------------------------------------------------
    ("classes/transport.py", '''\
# [BUILD FIRST]
# Transport class — handles patient movement delays.
#
# States:
#   WaitingAssignment — order placed, no transporter yet
#   Acknowledged      — transporter accepted the job
#   OnWay             — transporter en route to patient
#   Delivered         — patient arrived at holding bay

from dataclasses import dataclass, field
from enum import Enum, auto


class TransportState(Enum):
    WAITING_ASSIGNMENT = auto()
    ACKNOWLEDGED       = auto()
    ON_WAY             = auto()
    DELIVERED          = auto()


@dataclass
class Transport:
    state: TransportState = field(default=TransportState.WAITING_ASSIGNMENT)

    # Delay timers (in game-seconds) — set randomly within config ranges on spawn
    arrival_delay:  int = 0    # time until transporter arrives at patient
    hold_wait:      int = 0    # extra wait at pick-up before moving
    leaving_delay:  int = 0    # time after scan before transporter picks up

    timer: int = 0             # counts down current active delay
'''),

    # -----------------------------------------------------------------------
    # classes/patient.py
    # -----------------------------------------------------------------------
    ("classes/patient.py", '''\
# [BUILD FIRST]
# Patient class — the core game object.
#
# Full state machine:
#   Ordered > InTransport > InHolding >
#   ContrastOrdered > ContrastReady >
#   InjectorReady > Scanning > Cooldown >
#   Leaving > Completed | Refused | Holdover

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional
from classes.transport import Transport


class PatientState(Enum):
    ORDERED          = auto()
    IN_TRANSPORT     = auto()
    IN_HOLDING       = auto()
    CONTRAST_ORDERED = auto()
    CONTRAST_READY   = auto()
    INJECTOR_READY   = auto()
    SCANNING         = auto()
    COOLDOWN         = auto()
    LEAVING          = auto()
    COMPLETED        = auto()
    REFUSED          = auto()
    HOLDOVER         = auto()


@dataclass
class Patient:
    patient_id:   str
    acuity:       int                   # 1–5
    personability: float                # 0.0–1.0, affects refusal risk
    mobility:     str                   # "ambulatory", "wheelchair", "stretcher"
    exam_list:    List[str] = field(default_factory=list)   # ordered list of exam keys
    transport:    Optional[Transport] = None

    state:         PatientState = field(default=PatientState.ORDERED)
    wait_timer:    int = 0              # total game-seconds spent waiting
    contrast_timer: int = 0            # counts down oral contrast wait
    current_exam_index: int = 0        # index into exam_list for multi-exam patients
'''),

    # -----------------------------------------------------------------------
    # classes/scanner.py
    # -----------------------------------------------------------------------
    ("classes/scanner.py", '''\
# [BUILD FIRST]
# Scanner class — represents one CT machine.
#
# States:
#   Idle     — available, no patient
#   Scanning — patient actively being scanned
#   Cooldown — post-scan reset period
#   Locked   — no tech assigned, cannot accept patients

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class ScannerState(Enum):
    IDLE     = auto()
    SCANNING = auto()
    COOLDOWN = auto()
    LOCKED   = auto()


@dataclass
class Scanner:
    scanner_id:      str
    zone:            str          # "ED" or "Main"
    state:           ScannerState = field(default=ScannerState.IDLE)
    current_patient: Optional[str] = None    # patient_id or None
    assigned_tech:   Optional[str] = None    # tech_id or None
    scan_timer:      int = 0
    cooldown_timer:  int = 0

    @property
    def is_available(self) -> bool:
        # A scanner can accept a patient only if idle AND a tech is assigned
        return self.state == ScannerState.IDLE and self.assigned_tech is not None
'''),

    # -----------------------------------------------------------------------
    # classes/holding_bay.py
    # -----------------------------------------------------------------------
    ("classes/holding_bay.py", '''\
# [BUILD FIRST]
# HoldingBay class — waiting area before scanner assignment.
# Tracks proper slots and overflow slots separately.
# Overflow triggers a penalty via scoring_manager.

from dataclasses import dataclass, field
from typing import List


@dataclass
class HoldingBay:
    zone:           str              # "ED" or "Main"
    proper_slots:   int = 4
    overflow_slots: int = 2

    patients: List[str] = field(default_factory=list)   # list of patient_ids

    @property
    def is_overflowing(self) -> bool:
        return len(self.patients) > self.proper_slots

    @property
    def is_full(self) -> bool:
        # True when even overflow is exhausted
        return len(self.patients) >= (self.proper_slots + self.overflow_slots)
'''),

    # -----------------------------------------------------------------------
    # classes/tech.py
    # -----------------------------------------------------------------------
    ("classes/tech.py", '''\
# [LATER] — depends on staffing_manager.py
# Tech class — represents a CT technologist.
#
# Status values: "scanning", "paperwork", "idle", "off_shift"

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class TechStatus(Enum):
    SCANNING   = auto()
    PAPERWORK  = auto()
    IDLE       = auto()
    OFF_SHIFT  = auto()


@dataclass
class Tech:
    tech_id:        str
    name:           str
    speed:          float           # 0.0–1.0, affects scan time modifier
    accuracy:       float           # 0.0–1.0, affects error/repeat rate
    willingness:    float           # 0.0–1.0, affects refusal to take patients
    knowledge_base: float           # 0.0–1.0, affects contrast and protocol decisions
    shift_start:    float           # game-time hour, e.g. 7.0
    shift_end:      float           # game-time hour, e.g. 15.5

    assigned_scanner: Optional[str] = None   # scanner_id or None
    status: TechStatus = field(default=TechStatus.OFF_SHIFT)
'''),

    # -----------------------------------------------------------------------
    # managers/spawn_manager.py
    # -----------------------------------------------------------------------
    ("managers/spawn_manager.py", '''\
# [BUILD FIRST]
# SpawnManager — controls when and what patients appear.
# Reads hourly_spawn_weights.py for timing and acuity bias.
# Assigns acuity, mobility type, and exam list on spawn.
# Adds new Patient objects to the ordered queue.

from data.hourly_spawn_weights import HOURLY_SPAWN_TABLE
from data.acuity_table import ACUITY_TABLE


class SpawnManager:
    def __init__(self, queue_manager):
        self.queue_manager = queue_manager
        self._patient_counter = 0    # used to generate unique patient IDs

    def tick(self, game_hour: int, game_second: int):
        """Called every simulation tick. Decides whether to spawn a patient."""
        # TODO: use spawn_weight and game_hour to probabilistically spawn
        pass

    def _spawn_patient(self, game_hour: int):
        """Creates a new Patient and adds it to the queue."""
        # TODO: pick acuity using acuity_bias, pick exam from acuity_table,
        #       assign random mobility, create Transport, build Patient
        pass

    def _next_patient_id(self) -> str:
        self._patient_counter += 1
        return f"PAT_{self._patient_counter:04d}"
'''),

    # -----------------------------------------------------------------------
    # managers/queue_manager.py
    # -----------------------------------------------------------------------
    ("managers/queue_manager.py", '''\
# [BUILD FIRST]
# QueueManager — manages the ordered queue of waiting patients.
# Handles priority ordering by acuity (1 = highest priority).
# Moves patients from queue into a holding bay when space is available.
# Tracks per-patient wait times.

import heapq


class QueueManager:
    def __init__(self):
        # Min-heap: (acuity, arrival_time, patient_id)
        # Lower acuity number = higher priority
        self._heap = []
        self._patients = {}    # patient_id -> Patient object

    def add_patient(self, patient):
        """Add a newly spawned patient to the priority queue."""
        # TODO: push onto heap, store in _patients dict
        pass

    def tick(self, game_second: int):
        """Advance wait timers for all queued patients."""
        # TODO: increment wait_timer on each queued patient
        pass

    def pop_next(self):
        """Return the highest-priority patient and remove from queue."""
        # TODO: pop from heap, return Patient object
        pass

    def is_empty(self) -> bool:
        return len(self._heap) == 0
'''),

    # -----------------------------------------------------------------------
    # managers/transport_manager.py
    # -----------------------------------------------------------------------
    ("managers/transport_manager.py", '''\
# [BUILD FIRST]
# TransportManager — handles all patient movement delays.
# Runs the Transport state machine for each active patient.
# Generates random delay values within config ranges on patient spawn.

import random
from config import TRANSPORT_ARRIVAL_DELAY, TRANSPORT_HOLD_WAIT, TRANSPORT_LEAVING_DELAY
from classes.transport import TransportState


class TransportManager:
    def __init__(self):
        self._active = {}    # patient_id -> Patient (those currently in transport)

    def assign_transport(self, patient):
        """Called when a patient is ordered. Sets random delay values."""
        patient.transport.arrival_delay = random.randint(*TRANSPORT_ARRIVAL_DELAY)
        patient.transport.hold_wait     = random.randint(*TRANSPORT_HOLD_WAIT)
        patient.transport.leaving_delay = random.randint(*TRANSPORT_LEAVING_DELAY)
        self._active[patient.patient_id] = patient

    def tick(self):
        """Advance transport state machines for all active patients."""
        # TODO: count down timers, advance TransportState, fire delivery event
        pass
'''),

    # -----------------------------------------------------------------------
    # managers/scanner_manager.py
    # -----------------------------------------------------------------------
    ("managers/scanner_manager.py", '''\
# [BUILD FIRST]
# ScannerManager — controls scanner assignment and scan lifecycle.
# Zone preference: trauma/acuity-1 patients go to ED CT first.
# Checks tech availability before assigning a patient to a scanner.
# Manages multi-exam sequences (patient stays until all exams done).
# Tracks scan timer and cooldown timer per scanner.

from classes.scanner import ScannerState


class ScannerManager:
    def __init__(self, scanners: list):
        # scanners: list of Scanner objects, passed in from game_loop
        self.scanners = {s.scanner_id: s for s in scanners}

    def try_assign(self, patient, exam_catalog: dict):
        """Try to assign patient to an available scanner. Returns True if successful."""
        # TODO: pick scanner by zone preference, check is_available,
        #       set scanner state to SCANNING, attach patient
        pass

    def tick(self, exam_catalog: dict):
        """Advance scan and cooldown timers on all scanners."""
        # TODO: count down scan_timer, transition to COOLDOWN,
        #       count down cooldown_timer, transition back to IDLE,
        #       handle multi-exam: if more exams remain, re-enter SCANNING
        pass
'''),

    # -----------------------------------------------------------------------
    # managers/contrast_manager.py
    # -----------------------------------------------------------------------
    ("managers/contrast_manager.py", '''\
# [LATER] — depends on patient states being stable
# ContrastManager — tracks oral contrast timers and injector fill status.
# Fires ContrastReady state change when oral contrast timer completes.
# Applies a penalty if IV scan starts before injector is filled.

from config import ORAL_CONTRAST_WAIT, INJECTOR_FILL_TIME


class ContrastManager:
    def __init__(self):
        self._oral_timers    = {}    # patient_id -> remaining game-seconds
        self._injector_ready = {}    # patient_id -> bool

    def start_oral_contrast(self, patient):
        """Begin oral contrast wait timer for a patient."""
        self._oral_timers[patient.patient_id] = ORAL_CONTRAST_WAIT

    def tick(self):
        """Count down timers. Fire ContrastReady when timer hits zero."""
        # TODO: decrement timers, update patient state on completion
        pass
'''),

    # -----------------------------------------------------------------------
    # managers/staffing_manager.py
    # -----------------------------------------------------------------------
    ("managers/staffing_manager.py", '''\
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
'''),

    # -----------------------------------------------------------------------
    # managers/scoring_manager.py
    # -----------------------------------------------------------------------
    ("managers/scoring_manager.py", '''\
# [LATER] — depends on most other systems being functional
# ScoringManager — tracks all score components in real time.
#
# Components:
#   exams_completed   — positive score
#   wait_penalties    — per-patient, per-minute over threshold
#   overflow_penalties — flat hit per overflow patient per tick
#   holdover_penalties — flat hit per patient still in system at shift end
#   combo_multiplier   — future feature, streak bonus for fast throughput
#
# Drives level-up / level-down logic at end of shift.

from config import WAIT_PENALTY_PER_MINUTE, OVERFLOW_PENALTY, HOLDOVER_PENALTY


class ScoringManager:
    def __init__(self):
        self.score = 0
        self.exams_completed = 0
        self.holdovers = 0

    def exam_completed(self):
        self.exams_completed += 1
        self.score += 10    # TODO: tune base score per exam

    def apply_wait_penalty(self, acuity: int, excess_seconds: int):
        """Called when a patient\'s wait exceeds their acuity threshold."""
        # TODO: use acuity_table penalty_mult and WAIT_PENALTY_PER_MINUTE
        pass

    def apply_overflow_penalty(self):
        self.score -= OVERFLOW_PENALTY

    def finalise(self, remaining_patients: list) -> int:
        """Called at end of shift. Applies holdover penalties, returns final score."""
        self.holdovers = len(remaining_patients)
        self.score -= self.holdovers * HOLDOVER_PENALTY
        return self.score
'''),

    # -----------------------------------------------------------------------
    # simulation/shift_timer.py
    # -----------------------------------------------------------------------
    ("simulation/shift_timer.py", '''\
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
'''),

    # -----------------------------------------------------------------------
    # simulation/game_loop.py
    # -----------------------------------------------------------------------
    ("simulation/game_loop.py", '''\
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
'''),

    # -----------------------------------------------------------------------
    # tests/test_spawn.py
    # -----------------------------------------------------------------------
    ("tests/test_spawn.py", '''\
# [LATER]
# Spawns 10 patients and prints their stats.
# Verify acuity distribution looks correct.
# Run from project root: python tests/test_spawn.py

# TODO: instantiate SpawnManager with a mock QueueManager,
#       call _spawn_patient() 10 times, print results
'''),

    # -----------------------------------------------------------------------
    # tests/test_scanner.py
    # -----------------------------------------------------------------------
    ("tests/test_scanner.py", '''\
# [LATER]
# Runs a single patient through a scanner.
# Verify scan timer, cooldown, and state transitions.
# Run from project root: python tests/test_scanner.py

# TODO: create one Scanner, one Patient with one exam,
#       call scanner_manager.try_assign(), then tick until IDLE,
#       assert state sequence is correct
'''),

    # -----------------------------------------------------------------------
    # tests/test_queue.py
    # -----------------------------------------------------------------------
    ("tests/test_queue.py", '''\
# [LATER]
# Fills queue with mixed-acuity patients.
# Verify that pop_next() always returns the highest-priority patient.
# Run from project root: python tests/test_queue.py

# TODO: create ~10 patients with random acuities 1–5,
#       add all to QueueManager, pop them all,
#       assert the order comes out lowest-acuity-number first
'''),

    # -----------------------------------------------------------------------
    # tests/test_full_shift.py
    # -----------------------------------------------------------------------
    ("tests/test_full_shift.py", '''\
# [LATER]
# Runs a complete simulated shift with no UI.
# Prints an event log and final score.
# This is the main validation tool before building the Unity front-end.
# Run from project root: python tests/test_full_shift.py

# TODO: wire up all BUILD FIRST managers, run GameLoop.run(),
#       collect event log from each manager, print summary
'''),
]


# ---------------------------------------------------------------------------
# Script execution
# ---------------------------------------------------------------------------

def generate(root: str = "CTDash"):
    """Create the full project tree under `root/`."""
    created = 0
    skipped = 0

    for rel_path, content in FILES:
        full_path = os.path.join(root, rel_path)
        dir_path  = os.path.dirname(full_path)

        # Make sure all parent directories exist
        os.makedirs(dir_path, exist_ok=True)

        # Also create __init__.py in every package directory so Python
        # can import across folders without extra setup
        init = os.path.join(dir_path, "__init__.py")
        if not os.path.exists(init):
            open(init, "w").close()

        # Don't overwrite files that already exist
        if os.path.exists(full_path):
            print(f"  SKIP  {full_path}  (already exists)")
            skipped += 1
            continue

        with open(full_path, "w") as f:
            f.write(content)

        print(f"  CREATE {full_path}")
        created += 1

    # Root-level __init__ isn't needed for a runnable project, but tidy to have
    root_init = os.path.join(root, "__init__.py")
    if not os.path.exists(root_init):
        open(root_init, "w").close()

    print(f"\nDone. {created} files created, {skipped} skipped.")
    print(f"Project root: {os.path.abspath(root)}/")


if __name__ == "__main__":
    generate()