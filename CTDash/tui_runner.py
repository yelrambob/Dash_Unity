#!/usr/bin/env python3
"""
CTDash TUI Test Runner
======================
Interactive terminal UI for testing the CT department simulation flow.

Layout:
  Left   — ORDERS        all patients with live status tags
  Middle — HOLDING BAYS  slots 1-4 proper, 5-7 overflow
  Right  — SCANNERS      ED and Main zone machines with timers

Commands:
  trans <n>    Initiate transport for order #n        (status must be WAITING)
  scan <n>     Assign order #n to a scanner           (status must be IN_HOLDING)
  leave <n>    Start leaving transport for order #n   (status must be SCAN_COMPLETE)
  add          Manually spawn a random patient
  pause        Toggle auto-spawning on/off
  speed <f>    Set time multiplier (default 0.15: 1 game-sec = 0.15 real-sec)
  clear        Remove completed orders from the list
  q / quit     Exit

Auto-spawning:
  Patients appear automatically based on the HOURLY_SPAWN_TABLE (real dept data).
  The game clock starts at 07:00. Volume is low at first (~7/hr) and ramps up
  toward the midday peak (~17-18/hr between 11:00-16:00).

Timing (at default speed 0.15):
  Transport arrival:  20-60 gs  →  3.0-9.0 real seconds
  En-route to bay:     5-30 gs  →  0.75-4.5 real seconds
  Head CT scan:          20 gs  →  3.0 real seconds
  Abdomen/Pelvis scan:   50 gs  →  7.5 real seconds
  Trauma scan:           70 gs  →  10.5 real seconds
  Post-scan cooldown:    20 gs  →  3.0 real seconds
  Oral contrast wait:   180 gs  →  27.0 real seconds
  Leaving transport:   5-20 gs  →  0.75-3.0 real seconds

  One game-hour passes every 9 real minutes at speed 0.15.
  (3600 gs × 0.15 real-sec/gs = 540 real seconds = 9 min)
  Use 'speed 0.5' to make the clock run faster and stress-test the spawn rate.
"""

import curses
import threading
import time
import random
import os
import sys

# ---------------------------------------------------------------------------
# Path setup — allow importing CTDash modules regardless of working directory
# ---------------------------------------------------------------------------
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

# ---------------------------------------------------------------------------
# Config import
# ---------------------------------------------------------------------------
try:
    import config as cfg
    SCAN_TIMES     = cfg.SCAN_TIMES
    COOLDOWN_GS    = cfg.SCANNER_COOLDOWN
    ARRIVAL_RANGE  = cfg.TRANSPORT_ARRIVAL_DELAY
    HOLDWAIT_RANGE = cfg.TRANSPORT_HOLD_WAIT
    LEAVING_RANGE  = cfg.TRANSPORT_LEAVING_DELAY
    ORAL_GS        = cfg.ORAL_CONTRAST_WAIT
    INJECTOR_GS    = cfg.INJECTOR_FILL_TIME
    BAY_PROPER     = cfg.HOLDING_PROPER_SLOTS
    BAY_OVERFLOW   = cfg.HOLDING_OVERFLOW_SLOTS
except ImportError:
    SCAN_TIMES     = {"head": 20, "chest": 25, "spine": 30, "abdpel": 50,
                      "trauma_full": 70, "cta_head": 45, "cta_chest": 35, "extremity": 35}
    COOLDOWN_GS    = 20
    ARRIVAL_RANGE  = (20, 60)
    HOLDWAIT_RANGE = (5, 30)
    LEAVING_RANGE  = (5, 20)
    ORAL_GS        = 180
    INJECTOR_GS    = 20
    BAY_PROPER     = 4
    BAY_OVERFLOW   = 3

# ---------------------------------------------------------------------------
# Spawn table import
# ---------------------------------------------------------------------------
try:
    from data.hourly_spawn_weights import HOURLY_SPAWN_TABLE
except ImportError:
    HOURLY_SPAWN_TABLE = {
        7:  {"exams_per_hour":  7, "acuity_bias": 0.40},
        8:  {"exams_per_hour": 10, "acuity_bias": 0.35},
        9:  {"exams_per_hour": 13, "acuity_bias": 0.35},
        10: {"exams_per_hour": 15, "acuity_bias": 0.30},
        11: {"exams_per_hour": 17, "acuity_bias": 0.30},
        12: {"exams_per_hour": 18, "acuity_bias": 0.30},
        13: {"exams_per_hour": 17, "acuity_bias": 0.30},
        14: {"exams_per_hour": 16, "acuity_bias": 0.30},
        15: {"exams_per_hour": 16, "acuity_bias": 0.30},
        16: {"exams_per_hour": 16, "acuity_bias": 0.35},
        17: {"exams_per_hour": 15, "acuity_bias": 0.35},
        18: {"exams_per_hour": 12, "acuity_bias": 0.40},
        19: {"exams_per_hour":  9, "acuity_bias": 0.45},
        20: {"exams_per_hour":  7, "acuity_bias": 0.50},
    }

try:
    from data.acuity_table import ACUITY_TABLE
    ACUITY_SPAWN_WEIGHTS = [
        ACUITY_TABLE[1]["spawn_weight"],
        ACUITY_TABLE[2]["spawn_weight"],
        ACUITY_TABLE[3]["spawn_weight"],
        ACUITY_TABLE[4]["spawn_weight"],
    ]
    ACUITY_EXAMS = {
        1: ACUITY_TABLE[1]["typical_exams"],
        2: ACUITY_TABLE[2]["typical_exams"],
        3: ACUITY_TABLE[3]["typical_exams"],
        4: ACUITY_TABLE[4]["typical_exams"],
    }
except ImportError:
    ACUITY_SPAWN_WEIGHTS = [0.02, 0.03, 0.80, 0.15]
    ACUITY_EXAMS = {
        1: ["trauma_full", "head", "cta_head"],
        2: ["cta_chest", "cta_head", "abdpel", "head"],
        3: ["head", "abdpel", "chest", "spine", "cta_chest", "extremity"],
        4: ["abdpel", "chest", "spine", "extremity", "head"],
    }

# ---------------------------------------------------------------------------
# Static lookup tables
# ---------------------------------------------------------------------------
EXAM_META = {
    "head":        {"iv": False, "oral": False},
    "chest":       {"iv": False, "oral": False},
    "spine":       {"iv": False, "oral": False},
    "extremity":   {"iv": False, "oral": False},
    "cta_chest":   {"iv": True,  "oral": False},
    "cta_head":    {"iv": True,  "oral": False},
    "abdpel":      {"iv": True,  "oral": True},
    "trauma_full": {"iv": True,  "oral": False},
}

ACUITY_LABEL = {1: "TRAUMA", 2: "CRITICAL", 3: "STAT", 4: "ROUTINE"}

# Score constants — pulled from config/acuity_table where available
try:
    EXAM_BASE_SCORE = cfg.EXAM_BASE_SCORE
    WAIT_PENALTY_PM = cfg.WAIT_PENALTY_PER_MINUTE
except (NameError, AttributeError):
    EXAM_BASE_SCORE = 100
    WAIT_PENALTY_PM = 10

try:
    PENALTY_MULTS = {k: v["penalty_mult"] for k, v in ACUITY_TABLE.items()}
except NameError:
    PENALTY_MULTS = {1: 5.0, 2: 3.0, 3: 1.5, 4: 0.5}

# All tiers begin losing points at 1:30 game-time (90 gs).
# Differentiation comes from penalty rate — trauma craters fast, routine barely moves.
WAIT_THRESHOLDS = {1: 90, 2: 90, 3: 90, 4: 90}

SHIFT_START_HOUR = 7    # game clock starts at 07:00
DEFAULT_SPEED    = 0.15  # real-seconds per game-second

# Transport delay mechanics
# Each transport roll (arrival and leaving) has an independent chance of being
# significantly longer — simulating a backed-up transporter, elevator wait, etc.
TRANSPORT_DELAY_CHANCE        = 0.25          # 25% chance per transport request
TRANSPORT_ARRIVAL_DELAY_MULT  = (3.0, 6.0)   # multiply normal arrival time by this
TRANSPORT_LEAVING_DELAY_MULT  = (3.0, 8.0)   # leaving delays can be even worse


# ---------------------------------------------------------------------------
# Patient status constants
# ---------------------------------------------------------------------------
class S:
    WAITING        = "WAITING"
    TRANS_ARRIVING = "TRANS_ARRIVING"
    TRANS_ENROUTE  = "TRANS_ENROUTE"
    IN_HOLDING     = "IN_HOLDING"
    ORAL_CONTRAST  = "ORAL_CONTRAST"
    INJECTOR       = "INJECTOR"
    SCANNING       = "SCANNING"
    COOLDOWN       = "COOLDOWN"
    SCAN_COMPLETE  = "SCAN_COMPLETE"
    LEAVING        = "LEAVING"
    DONE           = "DONE"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
class TUIPatient:
    def __init__(self, number: int, patient_id: str, acuity: int, exam: str):
        self.number        = number
        self.patient_id    = patient_id
        self.acuity        = acuity
        self.exam          = exam
        self.scan_gs       = SCAN_TIMES[exam]
        self.iv_contrast   = EXAM_META[exam]["iv"]
        self.oral_contrast = EXAM_META[exam]["oral"]

        self.status        = S.WAITING
        self.timer         = 0.0
        self.holding_slot  = -1
        self.scanner_idx   = -1
        self.oral_done     = False
        self.wait_gs       = 0.0   # game-seconds waited (order placed → scan start)

        # Arrival transport — 25% chance of significant delay
        _arr = random.randint(*ARRIVAL_RANGE)
        if random.random() < TRANSPORT_DELAY_CHANCE:
            self.arrival_gs      = int(_arr * random.uniform(*TRANSPORT_ARRIVAL_DELAY_MULT))
            self.arrival_delayed = True
        else:
            self.arrival_gs      = _arr
            self.arrival_delayed = False

        self.holdwait_gs   = random.randint(*HOLDWAIT_RANGE)

        # Leaving transport — independent 25% chance of significant delay
        _lv = random.randint(*LEAVING_RANGE)
        if random.random() < TRANSPORT_DELAY_CHANCE:
            self.leaving_gs      = int(_lv * random.uniform(*TRANSPORT_LEAVING_DELAY_MULT))
            self.leaving_delayed = True
        else:
            self.leaving_gs      = _lv
            self.leaving_delayed = False

    def status_line(self) -> str:
        s, t = self.status, self.timer
        if s == S.WAITING:
            return "  WAITING"
        elif s == S.TRANS_ARRIVING:
            tag = "  \u26a0 SIGNIFICANT DELAY" if self.arrival_delayed else ""
            return f"  TRANSPORT \u2014 transporter arriving  ({_fmt(t)}){tag}"
        elif s == S.TRANS_ENROUTE:
            tag = "  \u26a0 DELAYED" if self.arrival_delayed else ""
            return f"  TRANSPORT \u2014 en route to bay      ({_fmt(t)}){tag}"
        elif s == S.IN_HOLDING:
            slot = self.holding_slot + 1
            label = f"Overflow {slot - BAY_PROPER}" if self.holding_slot >= BAY_PROPER else f"Bay {slot}"
            return f"  IN HOLDING [{label}]"
        elif s == S.ORAL_CONTRAST:
            return f"  ORAL CONTRAST  ({_fmt(t)} remaining)"
        elif s == S.INJECTOR:
            return f"  INJECTOR FILL  ({_fmt(t)} remaining)"
        elif s == S.SCANNING:
            return f"  SCANNING [Scanner {self.scanner_idx + 1}]  ({_fmt(t)} remaining)"
        elif s == S.COOLDOWN:
            return f"  COOLDOWN [Scanner {self.scanner_idx + 1}]  ({_fmt(t)} remaining)"
        elif s == S.SCAN_COMPLETE:
            return f"  SCAN DONE  \u2190 type: leave {self.number}"
        elif s == S.LEAVING:
            tag = "  \u26a0 SIGNIFICANT DELAY" if self.leaving_delayed else ""
            return f"  LEAVING  ({_fmt(t)} remaining){tag}"
        elif s == S.DONE:
            return "  COMPLETED \u2713"
        return f"  {s}"

    def calc_score(self) -> int:
        """Score starts at EXAM_BASE_SCORE and drops once wait exceeds threshold.
        Rate of drop is weighted by acuity — trauma loses points fastest."""
        threshold = WAIT_THRESHOLDS.get(self.acuity, 900)
        mult      = PENALTY_MULTS.get(self.acuity, 1.5)
        excess_gs = max(0.0, self.wait_gs - threshold)
        penalty   = (excess_gs / 60.0) * WAIT_PENALTY_PM * mult
        return round(EXAM_BASE_SCORE - penalty)


class ScannerInfo:
    def __init__(self, scanner_id: str, zone: str, tech: str):
        self.scanner_id  = scanner_id
        self.zone        = zone
        self.tech        = tech
        self.patient_num = None

    @property
    def is_idle(self) -> bool:
        return self.patient_num is None


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------
def _fmt(secs: float) -> str:
    s = max(0, int(secs))
    return f"{s // 60}:{s % 60:02d}"


def _saddstr(win, y: int, x: int, text: str, attr: int = 0):
    try:
        h, w = win.getmaxyx()
        if y < 0 or y >= h or x >= w:
            return
        clip = w - x - 1
        if clip > 0:
            win.addstr(y, x, text[:clip], attr)
    except curses.error:
        pass


# ---------------------------------------------------------------------------
# Core state
# ---------------------------------------------------------------------------
class TUIState:
    def __init__(self, speed: float = DEFAULT_SPEED, num_scanners: int = 2):
        self.speed       = speed
        self.patients    : list = []
        self.holding     : list = [None] * (BAY_PROPER + BAY_OVERFLOW)

        _defs = [
            ("ED-1",   "ED",   "Alice"),
            ("Main-1", "Main", "Bob"),
            ("Main-2", "Main", "Carol"),
            ("Main-3", "Main", "Dan"),
        ]
        self.scanners    : list = [ScannerInfo(*_defs[i]) for i in range(min(num_scanners, 4))]

        self.log         : list = []
        self.lock        = threading.Lock()
        self._next_n     = 1

        # Game clock
        self.game_elapsed_gs = 0.0   # game-seconds since 07:00
        self._spawn_accum    = 0.0   # accumulated spawn probability
        self.auto_spawn      = True

        self._last_t     = time.monotonic()
        self._running    = True
        self._thread     = threading.Thread(target=self._tick_loop, daemon=True)
        self._thread.start()

    # ------------------------------------------------------------------
    # Clock helpers
    # ------------------------------------------------------------------
    def _current_game_hour(self) -> int:
        return min(23, SHIFT_START_HOUR + int(self.game_elapsed_gs / 3600))

    def clock_str(self) -> str:
        total_gs = int(self.game_elapsed_gs)
        hour     = SHIFT_START_HOUR + total_gs // 3600
        minute   = (total_gs % 3600) // 60
        return f"{hour:02d}:{minute:02d}"

    def exams_per_hour(self) -> float:
        """Interpolated rate between current and next hour for smooth display."""
        hour     = self._current_game_hour()
        fraction = (self.game_elapsed_gs % 3600) / 3600
        cur_rate = HOURLY_SPAWN_TABLE.get(hour,     {"exams_per_hour": 4})["exams_per_hour"]
        nxt_rate = HOURLY_SPAWN_TABLE.get(hour + 1, {"exams_per_hour": 4})["exams_per_hour"]
        return cur_rate + (nxt_rate - cur_rate) * fraction

    # ------------------------------------------------------------------
    # Internal helpers (call under lock)
    # ------------------------------------------------------------------
    def _gs(self, game_seconds: int) -> float:
        return game_seconds * self.speed

    def _log(self, msg: str):
        self.log.append(msg)
        if len(self.log) > 80:
            self.log.pop(0)

    def _get(self, num: int):
        for p in self.patients:
            if p.number == num:
                return p
        return None

    def _free_bay(self) -> int:
        for i, occ in enumerate(self.holding):
            if occ is None:
                return i
        return -1

    def _free_scanner(self) -> int:
        for i, sc in enumerate(self.scanners):
            if sc.is_idle:
                return i
        return -1

    def _make_patient(self, acuity=None, exam=None) -> TUIPatient:
        if acuity is None:
            acuity = random.choices([1, 2, 3, 4], weights=ACUITY_SPAWN_WEIGHTS)[0]
        if exam is None:
            exam = random.choice(ACUITY_EXAMS[acuity])
        n = self._next_n
        self._next_n += 1
        return TUIPatient(n, f"PAT_{n:04d}", acuity, exam)

    # ------------------------------------------------------------------
    # Public: manual spawn
    # ------------------------------------------------------------------
    def add_patient(self, acuity=None, exam=None):
        with self.lock:
            p = self._make_patient(acuity, exam)
            self.patients.append(p)
            self._log(f"[{self.clock_str()}] Order #{p.number} \u2014 "
                      f"{p.patient_id}  [{ACUITY_LABEL[p.acuity]}]  {p.exam.upper()}")

    # ------------------------------------------------------------------
    # Auto-spawn (called under lock from tick loop)
    # ------------------------------------------------------------------
    def _try_spawn(self, dt_gs: float):
        if not self.auto_spawn:
            return
        prob_per_gs = self.exams_per_hour() / 3600.0   # interpolated, smooth ramp
        self._spawn_accum += prob_per_gs * dt_gs
        # Spawn once per accumulator tick (one at a time, avoids bursts)
        if self._spawn_accum >= 1.0:
            self._spawn_accum -= 1.0
            p = self._make_patient()
            self.patients.append(p)
            self._log(f"[{self.clock_str()}] Order #{p.number} \u2014 "
                      f"{p.patient_id}  [{ACUITY_LABEL[p.acuity]}]  {p.exam.upper()}")

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------
    def cmd_trans(self, num: int) -> str:
        with self.lock:
            p = self._get(num)
            if p is None:
                return f"No order #{num}"
            if p.status != S.WAITING:
                return f"#{num} is not WAITING (currently: {p.status})"
            p.status = S.TRANS_ARRIVING
            p.timer  = self._gs(p.arrival_gs)
            delay_note = "  \u26a0 SIGNIFICANT DELAY" if p.arrival_delayed else ""
            self._log(f"[{self.clock_str()}] #{num} {p.patient_id} \u2014 "
                      f"transport initiated  ({_fmt(p.timer)}){delay_note}")
            return ""

    def cmd_scan(self, num: int) -> str:
        with self.lock:
            p = self._get(num)
            if p is None:
                return f"No order #{num}"
            if p.status != S.IN_HOLDING:
                return f"#{num} must be IN_HOLDING to scan (currently: {p.status})"
            if p.oral_contrast and not p.oral_done:
                p.status = S.ORAL_CONTRAST
                p.timer  = self._gs(ORAL_GS)
                self._log(f"[{self.clock_str()}] #{num} {p.patient_id} \u2014 "
                          f"oral contrast started  ({_fmt(p.timer)} wait)")
                return ""
            idx = self._free_scanner()
            if idx == -1:
                return "No scanner available right now"
            sc = self.scanners[idx]
            sc.patient_num = num
            p.scanner_idx  = idx
            if p.iv_contrast:
                p.status = S.INJECTOR
                p.timer  = self._gs(INJECTOR_GS)
                self._log(f"[{self.clock_str()}] #{num} {p.patient_id} \u2014 "
                          f"injector fill on Scanner {idx+1}  "
                          f"({_fmt(p.timer)} fill \u2192 {_fmt(self._gs(p.scan_gs))} scan)")
            else:
                p.status = S.SCANNING
                p.timer  = self._gs(p.scan_gs)
                self._log(f"[{self.clock_str()}] #{num} {p.patient_id} \u2014 "
                          f"scanning on Scanner {idx+1}  ({_fmt(p.timer)} remaining)")
            return ""

    def cmd_leave(self, num: int) -> str:
        with self.lock:
            p = self._get(num)
            if p is None:
                return f"No order #{num}"
            if p.status != S.SCAN_COMPLETE:
                return f"#{num} must be SCAN_COMPLETE (currently: {p.status})"
            if p.holding_slot >= 0:
                self.holding[p.holding_slot] = None
                p.holding_slot = -1
            p.status = S.LEAVING
            p.timer  = self._gs(p.leaving_gs)
            delay_note = "  \u26a0 SIGNIFICANT DELAY" if p.leaving_delayed else ""
            self._log(f"[{self.clock_str()}] #{num} {p.patient_id} \u2014 "
                      f"leaving  ({_fmt(p.timer)} remaining){delay_note}")
            return ""

    def cmd_clear(self) -> str:
        with self.lock:
            before = len(self.patients)
            self.patients = [p for p in self.patients if p.status != S.DONE]
            n = before - len(self.patients)
            return f"Cleared {n} completed order(s)" if n else "No completed orders"

    def cmd_speed(self, factor: float) -> str:
        with self.lock:
            self.speed = max(0.01, min(20.0, factor))
            return f"Speed set to {self.speed:.2f}x"

    def cmd_pause(self) -> str:
        with self.lock:
            self.auto_spawn = not self.auto_spawn
            state = "ON" if self.auto_spawn else "OFF"
            self._log(f"[{self.clock_str()}] Auto-spawn {state}")
            return f"Auto-spawn {state}"

    # ------------------------------------------------------------------
    # Timer thread
    # ------------------------------------------------------------------
    def _tick_loop(self):
        while self._running:
            time.sleep(0.05)
            now = time.monotonic()
            with self.lock:
                dt      = now - self._last_t
                self._last_t = now
                dt_gs   = dt / self.speed       # game-seconds elapsed this tick
                self.game_elapsed_gs += dt_gs
                self._try_spawn(dt_gs)
                for p in self.patients:
                    self._advance(p, dt, dt_gs)

    def _advance(self, p: TUIPatient, dt: float, dt_gs: float):
        # Accumulate wait time until the scan actually begins
        if p.status not in (S.SCANNING, S.COOLDOWN, S.SCAN_COMPLETE, S.LEAVING, S.DONE):
            p.wait_gs += dt_gs

        s = p.status
        if s in (S.WAITING, S.IN_HOLDING, S.SCAN_COMPLETE, S.DONE):
            return
        p.timer = max(0.0, p.timer - dt)

        if s == S.TRANS_ARRIVING and p.timer <= 0:
            p.status = S.TRANS_ENROUTE
            p.timer  = self._gs(p.holdwait_gs)

        elif s == S.TRANS_ENROUTE and p.timer <= 0:
            slot = self._free_bay()
            if slot == -1:
                self._log(f"[{self.clock_str()}] \u26a0  HOLDING FULL \u2014 "
                          f"#{p.number} {p.patient_id} waiting outside!")
                p.timer = self._gs(15)
            else:
                self.holding[slot] = p.number
                p.holding_slot = slot
                label = (f"Overflow {slot - BAY_PROPER + 1}"
                         if slot >= BAY_PROPER else f"Bay {slot + 1}")
                p.status = S.IN_HOLDING
                self._log(f"[{self.clock_str()}] #{p.number} {p.patient_id} \u2014 "
                          f"arrived in {label}")

        elif s == S.ORAL_CONTRAST and p.timer <= 0:
            p.oral_done = True
            p.status    = S.IN_HOLDING
            self._log(f"[{self.clock_str()}] #{p.number} {p.patient_id} \u2014 "
                      f"oral contrast complete, ready to scan")

        elif s == S.INJECTOR and p.timer <= 0:
            p.status = S.SCANNING
            p.timer  = self._gs(p.scan_gs)
            self._log(f"[{self.clock_str()}] #{p.number} {p.patient_id} \u2014 "
                      f"injector done, now scanning  ({_fmt(p.timer)} remaining)")

        elif s == S.SCANNING and p.timer <= 0:
            p.status = S.COOLDOWN
            p.timer  = self._gs(COOLDOWN_GS)
            self._log(f"[{self.clock_str()}] #{p.number} {p.patient_id} \u2014 "
                      f"scan complete, cooldown  ({_fmt(p.timer)})")

        elif s == S.COOLDOWN and p.timer <= 0:
            sc = self.scanners[p.scanner_idx]
            sc.patient_num = None
            p.scanner_idx  = -1
            p.status       = S.SCAN_COMPLETE
            self._log(f"[{self.clock_str()}] #{p.number} {p.patient_id} \u2014 "
                      f"SCAN COMPLETE  \u2190 type: leave {p.number}")

        elif s == S.LEAVING and p.timer <= 0:
            p.status = S.DONE
            self._log(f"[{self.clock_str()}] #{p.number} {p.patient_id} \u2014 "
                      f"departed, exam complete \u2713")

    def stop(self):
        self._running = False


# ---------------------------------------------------------------------------
# Curses colour pairs
# ---------------------------------------------------------------------------
CP_TITLE    = 1
CP_TRAUMA   = 2
CP_CRITICAL = 3
CP_STAT     = 4
CP_ROUTINE  = 5
CP_DONE     = 6
CP_HEADER   = 7
CP_WARN     = 8
CP_SCANNER  = 9
CP_CMD      = 10
CP_TRANS    = 11

ACUITY_CP = {1: CP_TRAUMA, 2: CP_CRITICAL, 3: CP_STAT, 4: CP_ROUTINE}
STATUS_CP  = {
    S.WAITING:        CP_ROUTINE,
    S.TRANS_ARRIVING: CP_TRANS,
    S.TRANS_ENROUTE:  CP_TRANS,
    S.IN_HOLDING:     CP_STAT,
    S.ORAL_CONTRAST:  CP_CRITICAL,
    S.INJECTOR:       CP_CRITICAL,
    S.SCANNING:       CP_SCANNER,
    S.COOLDOWN:       CP_SCANNER,
    S.SCAN_COMPLETE:  CP_CMD,
    S.LEAVING:        CP_TRANS,
    S.DONE:           CP_DONE,
}


def init_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(CP_TITLE,    curses.COLOR_BLACK,   curses.COLOR_CYAN)
    curses.init_pair(CP_TRAUMA,   curses.COLOR_RED,     -1)
    curses.init_pair(CP_CRITICAL, curses.COLOR_YELLOW,  -1)
    curses.init_pair(CP_STAT,     curses.COLOR_GREEN,   -1)
    curses.init_pair(CP_ROUTINE,  -1,                   -1)
    curses.init_pair(CP_DONE,     curses.COLOR_BLACK,   -1)
    curses.init_pair(CP_HEADER,   curses.COLOR_CYAN,    -1)
    curses.init_pair(CP_WARN,     curses.COLOR_RED,     -1)
    curses.init_pair(CP_SCANNER,  curses.COLOR_MAGENTA, -1)
    curses.init_pair(CP_CMD,      curses.COLOR_YELLOW,  -1)
    curses.init_pair(CP_TRANS,    curses.COLOR_BLUE,    -1)


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------
def _score_attr(score: int) -> int:
    if score > 50:
        return curses.color_pair(CP_STAT) | curses.A_BOLD      # green — healthy
    elif score > 0:
        return curses.color_pair(CP_CRITICAL) | curses.A_BOLD  # yellow — fading
    else:
        return curses.color_pair(CP_TRAUMA) | curses.A_BOLD    # red — penalty


def _score_str(score: int) -> str:
    return f"+{score}" if score >= 0 else str(score)


def _hline(win, y: int, x: int, w: int, title: str = "", cp: int = CP_HEADER):
    attr = curses.color_pair(cp) | curses.A_BOLD
    _saddstr(win, y, x, "\u2500" * w, attr)
    if title:
        _saddstr(win, y, x + 2, f" {title} ", attr)


def _draw_orders(win, state: TUIState, x: int, w: int, y0: int, y1: int):
    # Orders panel shows only patients not yet in a holding bay
    pre_bay = [p for p in state.patients
               if p.status in (S.WAITING, S.TRANS_ARRIVING, S.TRANS_ENROUTE)]
    in_bay  = sum(1 for p in state.patients if p.status == S.IN_HOLDING)
    header  = f"ORDERS  queued:{len(pre_bay)}  in-bay:{in_bay}"
    _hline(win, y0, x, w - 1, header)
    row, lim = y0 + 1, y1 - 1

    def _draw_patient(p):
        nonlocal row
        if row >= lim:
            return False
        score = p.calc_score()
        cp    = ACUITY_CP.get(p.acuity, CP_ROUTINE)
        # Line 1: number, ID, acuity tag, score
        id_part    = f" #{p.number:<3} {p.patient_id}  [{ACUITY_LABEL[p.acuity]}]"
        score_part = f"  {_score_str(score):>5}"
        _saddstr(win, row, x, id_part, curses.color_pair(cp) | curses.A_BOLD)
        _saddstr(win, row, x + len(id_part), score_part, _score_attr(score))
        row += 1
        if row >= lim:
            return False
        # Line 2: exam  waited: X:XX game-time
        waited = f"  waited: {_fmt(p.wait_gs)}"
        _saddstr(win, row, x + 5, p.exam.upper(), curses.color_pair(CP_ROUTINE))
        _saddstr(win, row, x + 5 + len(p.exam) + 2, waited,
                 curses.color_pair(CP_HEADER))
        row += 1
        if row >= lim:
            return False
        # Line 3: status
        s_attr = curses.color_pair(STATUS_CP.get(p.status, CP_ROUTINE))
        _saddstr(win, row, x, p.status_line(), s_attr)
        row += 2
        return True

    # --- Group 1: TRAUMA + CRITICAL (time-ordered, most urgent first) ---
    urgent = sorted([p for p in pre_bay if p.acuity in (1, 2)], key=lambda p: p.number)
    if urgent:
        _saddstr(win, row, x + 1, "\u2500\u2500 TRAUMA / CRITICAL \u2500\u2500",
                 curses.color_pair(CP_TRAUMA) | curses.A_BOLD)
        row += 1
        for p in urgent:
            if not _draw_patient(p):
                break

    # --- Group 2: STAT ---
    stats = sorted([p for p in pre_bay if p.acuity == 3], key=lambda p: p.number)
    if stats and row < lim:
        _saddstr(win, row, x + 1, "\u2500\u2500 STAT \u2500\u2500",
                 curses.color_pair(CP_STAT) | curses.A_BOLD)
        row += 1
        for p in stats:
            if not _draw_patient(p):
                break

    # --- Group 3: ROUTINE ---
    routine = sorted([p for p in pre_bay if p.acuity == 4], key=lambda p: p.number)
    if routine and row < lim:
        _saddstr(win, row, x + 1, "\u2500\u2500 ROUTINE \u2500\u2500",
                 curses.color_pair(CP_ROUTINE) | curses.A_BOLD)
        row += 1
        for p in routine:
            if not _draw_patient(p):
                break


def _draw_holding(win, state: TUIState, x: int, w: int, y0: int, y1: int):
    _hline(win, y0, x, w - 1, "HOLDING BAYS")
    row, lim = y0 + 1, y1 - 1

    def _draw_slot(label: str, occ, overflow: bool = False):
        nonlocal row
        if row >= lim:
            return
        if occ is None:
            dim = curses.color_pair(CP_WARN if overflow else CP_DONE) | curses.A_DIM
            _saddstr(win, row, x + 1, f"  {label}: (empty)", dim)
            row += 1
        else:
            p = state._get(occ)
            if not p:
                row += 1
                return
            score = p.calc_score()
            cp    = ACUITY_CP.get(p.acuity, CP_ROUTINE)
            ovr_tag = "  \u26a0 OVERFLOW" if overflow else ""
            # Line 1: slot label, patient ID, acuity, score
            _saddstr(win, row, x + 1,
                     f"  {label}: #{p.number} [{ACUITY_LABEL[p.acuity]}]{ovr_tag}",
                     curses.color_pair(CP_WARN if overflow else cp) | curses.A_BOLD)
            _saddstr(win, row, x + w - 9, f"{_score_str(score):>6}", _score_attr(score))
            row += 1
            if row >= lim:
                return
            # Line 2: exam + wait time + scan hint
            waited = f"waited {_fmt(p.wait_gs)}"
            hint   = f"scan {p.number}"
            _saddstr(win, row, x + 4, p.exam.upper(), curses.color_pair(cp))
            _saddstr(win, row, x + 4 + len(p.exam) + 2, waited,
                     curses.color_pair(CP_HEADER))
            _saddstr(win, row, x + w - len(hint) - 3, hint,
                     curses.color_pair(CP_CMD) | curses.A_BOLD)
            row += 1
            # Line 3: status (oral contrast, injector, scanning, etc.)
            if p.status != S.IN_HOLDING:
                s_attr = curses.color_pair(STATUS_CP.get(p.status, CP_ROUTINE))
                _saddstr(win, row, x + 4, p.status_line().strip(), s_attr)
                row += 1
            row += 1   # gap

    _saddstr(win, row, x + 1, f"\u2500\u2500 Proper ({BAY_PROPER} slots) \u2500\u2500",
             curses.color_pair(CP_HEADER))
    row += 1
    for i in range(BAY_PROPER):
        _draw_slot(f"Bay {i+1}", state.holding[i], overflow=False)

    if row < lim:
        _saddstr(win, row, x + 1, f"\u2500\u2500 Overflow ({BAY_OVERFLOW} slots) \u2500\u2500",
                 curses.color_pair(CP_WARN))
        row += 1
    for i in range(BAY_OVERFLOW):
        _draw_slot(f"OVR {i+1}", state.holding[BAY_PROPER + i], overflow=True)


def _draw_scanners(win, state: TUIState, x: int, w: int, y0: int, y1: int):
    _hline(win, y0, x, w - 1, "SCANNERS")
    row, lim = y0 + 1, y1 - 1

    for i, sc in enumerate(state.scanners):
        if row + 3 >= lim:
            break
        _saddstr(win, row, x + 1, f"Scanner {i+1}  [{sc.zone}]  Tech: {sc.tech}",
                 curses.color_pair(CP_SCANNER) | curses.A_BOLD)
        row += 1

        p = state._get(sc.patient_num) if sc.patient_num is not None else None
        if sc.is_idle:
            _saddstr(win, row, x + 3, "\u25cf IDLE",
                     curses.color_pair(CP_STAT) | curses.A_BOLD)
            row += 1
        elif p:
            phase_map = {
                S.INJECTOR: ("INJECTOR FILL", CP_CRITICAL),
                S.SCANNING: ("SCANNING",      CP_SCANNER),
                S.COOLDOWN: ("COOLDOWN",      CP_CRITICAL),
            }
            label, pcp = phase_map.get(p.status, (p.status, CP_ROUTINE))
            timer_str = (f"  ({_fmt(p.timer)} rem)"
                         if p.status in (S.INJECTOR, S.SCANNING, S.COOLDOWN) else "")
            _saddstr(win, row, x + 3, f"\u25c8 {label}{timer_str}",
                     curses.color_pair(pcp) | curses.A_BOLD)
            row += 1
            if row < lim:
                cp = ACUITY_CP.get(p.acuity, CP_ROUTINE)
                _saddstr(win, row, x + 5,
                         f"#{p.number} {p.patient_id}  {p.exam.upper()}",
                         curses.color_pair(cp))
                row += 1
        else:
            row += 1
        row += 1


def _draw_log(win, state: TUIState, y: int, log_h: int, width: int):
    _hline(win, y, 0, width, "LOG")
    entries = state.log[-(log_h - 1):]
    for i, entry in enumerate(reversed(entries)):
        ly = y + log_h - 1 - i
        if ly <= y:
            break
        _saddstr(win, ly, 2, entry, curses.color_pair(CP_ROUTINE))


def _draw_title(win, state: TUIState, width: int):
    _saddstr(win, 0, 0, " " * (width - 1),
             curses.color_pair(CP_TITLE) | curses.A_BOLD)
    clock    = state.clock_str()
    rate     = state.exams_per_hour()
    paused   = "  \u23f8 SPAWNING PAUSED" if not state.auto_spawn else ""
    left     = f"  CTDash TUI Test Runner"
    right    = f"[\u23f0 {clock}]  [{rate:.1f}/hr]{paused}  speed:{state.speed:.2f}x  "
    _saddstr(win, 0, 0, left,  curses.color_pair(CP_TITLE) | curses.A_BOLD)
    _saddstr(win, 0, max(0, width - len(right) - 1), right,
             curses.color_pair(CP_TITLE) | curses.A_BOLD)


def _draw_cmdbar(win, cmd_buf: str, err: str, height: int, width: int):
    y_sep = height - 3
    y_hlp = height - 2
    y_inp = height - 1
    _hline(win, y_sep, 0, width)
    help_txt = "trans <n>  scan <n>  leave <n>  add  pause  clear  speed <f>  quit"
    _saddstr(win, y_hlp, 2, help_txt, curses.color_pair(CP_HEADER))
    prompt = f"> {cmd_buf}"
    if err:
        _saddstr(win, y_inp, 1, prompt, curses.color_pair(CP_ROUTINE))
        _saddstr(win, y_inp, len(prompt) + 3, f"  \u2190 {err}",
                 curses.color_pair(CP_WARN))
    else:
        _saddstr(win, y_inp, 1, prompt + "\u2588", curses.color_pair(CP_CMD))


def render(win, state: TUIState, cmd_buf: str, err: str):
    win.erase()
    height, width = win.getmaxyx()

    log_h   = 5
    cmd_h   = 3
    panel_h = height - 1 - log_h - cmd_h
    y0, y1  = 1, 1 + panel_h
    log_y   = y1

    ow = max(28, int(width * 0.36))
    hw = max(20, int(width * 0.26))
    sw = width - ow - hw
    ox, hx, sx = 0, ow, ow + hw

    for r in range(y0, y1):
        try:
            win.addch(r, hx - 1, curses.ACS_VLINE, curses.color_pair(CP_HEADER))
            win.addch(r, sx - 1, curses.ACS_VLINE, curses.color_pair(CP_HEADER))
        except curses.error:
            pass

    with state.lock:
        _draw_title(win, state, width)
        _draw_orders(win, state, ox, ow, y0, y1)
        _draw_holding(win, state, hx, hw, y0, y1)
        _draw_scanners(win, state, sx, sw, y0, y1)
        _draw_log(win, state, log_y, log_h, width)
        _draw_cmdbar(win, cmd_buf, err, height, width)

    win.refresh()


# ---------------------------------------------------------------------------
# Command parser
# ---------------------------------------------------------------------------
def handle_command(raw: str, state: TUIState) -> str:
    parts = raw.strip().split()
    if not parts:
        return ""
    cmd = parts[0].lower()

    if cmd in ("q", "quit", "exit"):
        return "__QUIT__"
    elif cmd == "trans":
        if len(parts) < 2 or not parts[1].isdigit():
            return "Usage: trans <order_number>"
        return state.cmd_trans(int(parts[1]))
    elif cmd == "scan":
        if len(parts) < 2 or not parts[1].isdigit():
            return "Usage: scan <order_number>"
        return state.cmd_scan(int(parts[1]))
    elif cmd == "leave":
        if len(parts) < 2 or not parts[1].isdigit():
            return "Usage: leave <order_number>"
        return state.cmd_leave(int(parts[1]))
    elif cmd == "add":
        state.add_patient()
        return ""
    elif cmd == "pause":
        return state.cmd_pause()
    elif cmd == "clear":
        return state.cmd_clear()
    elif cmd == "speed":
        if len(parts) < 2:
            return "Usage: speed <factor>  e.g. 0.1 | 0.5 | 2.0"
        try:
            return state.cmd_speed(float(parts[1]))
        except ValueError:
            return "Speed must be a number"
    else:
        return f"Unknown command: {cmd!r}"


# ---------------------------------------------------------------------------
# Main curses loop
# ---------------------------------------------------------------------------
def _main(stdscr, state: TUIState):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(80)
    init_colors()

    cmd_buf = ""
    err     = ""
    err_exp = 0.0

    while True:
        now = time.monotonic()
        if err and now >= err_exp:
            err = ""
        render(stdscr, state, cmd_buf, err)
        try:
            key = stdscr.get_wch()
        except curses.error:
            continue
        if isinstance(key, str):
            if key in ("\n", "\r"):
                result  = handle_command(cmd_buf, state)
                cmd_buf = ""
                if result == "__QUIT__":
                    break
                elif result:
                    err     = result
                    err_exp = time.monotonic() + 4.0
                else:
                    err = ""
            elif key in ("\x7f", "\x08"):
                cmd_buf = cmd_buf[:-1]
            elif key.isprintable():
                cmd_buf += key
        elif isinstance(key, int):
            if key == curses.KEY_BACKSPACE:
                cmd_buf = cmd_buf[:-1]
            elif key == 27:
                cmd_buf = ""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def run(num_scanners: int = 2, speed: float = DEFAULT_SPEED):
    state = TUIState(speed=speed, num_scanners=num_scanners)
    # Two starting orders so there's something to do while 07:00 is still quiet
    state.add_patient(3, "head")
    state.add_patient(2, "cta_chest")
    try:
        curses.wrapper(lambda scr: _main(scr, state))
    finally:
        state.stop()
    print("CTDash TUI Test Runner exited.")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="CTDash TUI Test Runner")
    ap.add_argument("--scanners", type=int, default=2, choices=[1, 2, 3, 4],
                    help="Number of scanners (default: 2)")
    ap.add_argument("--speed", type=float, default=DEFAULT_SPEED,
                    help=f"Real-seconds per game-second (default: {DEFAULT_SPEED})")
    args = ap.parse_args()
    run(num_scanners=args.scanners, speed=args.speed)
