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
  add          Spawn a random test patient
  speed <f>    Set time multiplier (default 0.15: 1 game-sec = 0.15 real-sec)
  clear        Remove completed orders from the list
  q / quit     Exit

Timing (at default speed 0.15):
  Transport arrival:  20-60 gs  →  3.0-9.0 real seconds
  En-route to bay:     5-30 gs  →  0.75-4.5 real seconds
  Head CT scan:          20 gs  →  3.0 real seconds
  Abdomen/Pelvis scan:   50 gs  →  7.5 real seconds
  Trauma scan:           70 gs  →  10.5 real seconds
  Post-scan cooldown:    20 gs  →  3.0 real seconds
  Oral contrast wait:   180 gs  →  27.0 real seconds
  Leaving transport:   5-20 gs  →  0.75-3.0 real seconds
"""

import curses
import threading
import time
import random
import os
import sys

# ---------------------------------------------------------------------------
# Allow importing config from the CTDash/ directory regardless of cwd
# ---------------------------------------------------------------------------
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

try:
    import config as cfg
    SCAN_TIMES      = cfg.SCAN_TIMES
    COOLDOWN_GS     = cfg.SCANNER_COOLDOWN
    ARRIVAL_RANGE   = cfg.TRANSPORT_ARRIVAL_DELAY
    HOLDWAIT_RANGE  = cfg.TRANSPORT_HOLD_WAIT
    LEAVING_RANGE   = cfg.TRANSPORT_LEAVING_DELAY
    ORAL_GS         = cfg.ORAL_CONTRAST_WAIT
    INJECTOR_GS     = cfg.INJECTOR_FILL_TIME
    BAY_PROPER      = cfg.HOLDING_PROPER_SLOTS
    BAY_OVERFLOW    = cfg.HOLDING_OVERFLOW_SLOTS
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
# Lookup tables
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
ACUITY_EXAMS = {
    1: ["trauma_full", "cta_head"],
    2: ["cta_chest", "cta_head", "abdpel"],
    3: ["head", "chest", "spine", "abdpel", "extremity", "cta_chest"],
    4: ["head", "chest", "spine", "extremity"],
}

DEFAULT_SPEED = 0.15   # real-seconds per game-second

# ---------------------------------------------------------------------------
# Patient status constants
# ---------------------------------------------------------------------------
class S:
    WAITING        = "WAITING"
    TRANS_ARRIVING = "TRANS_ARRIVING"   # transporter walking to patient
    TRANS_ENROUTE  = "TRANS_ENROUTE"    # patient being brought to bay
    IN_HOLDING     = "IN_HOLDING"
    ORAL_CONTRAST  = "ORAL_CONTRAST"
    INJECTOR       = "INJECTOR"         # IV injector fill before scan
    SCANNING       = "SCANNING"
    COOLDOWN       = "COOLDOWN"
    SCAN_COMPLETE  = "SCAN_COMPLETE"    # waiting for 'leave' command
    LEAVING        = "LEAVING"
    DONE           = "DONE"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
class TUIPatient:
    def __init__(self, number: int, patient_id: str, acuity: int, exam: str):
        self.number       = number
        self.patient_id   = patient_id
        self.acuity       = acuity
        self.exam         = exam
        self.scan_gs      = SCAN_TIMES[exam]
        self.iv_contrast  = EXAM_META[exam]["iv"]
        self.oral_contrast = EXAM_META[exam]["oral"]

        self.status       = S.WAITING
        self.timer        = 0.0    # real-seconds remaining in current phase
        self.holding_slot = -1     # 0-indexed bay slot (-1 = not in bay)
        self.scanner_idx  = -1     # 0-indexed scanner (-1 = not on scanner)
        self.oral_done    = False  # tracks whether oral contrast has elapsed

        # Pre-rolled transport times (game-seconds)
        self.arrival_gs   = random.randint(*ARRIVAL_RANGE)
        self.holdwait_gs  = random.randint(*HOLDWAIT_RANGE)
        self.leaving_gs   = random.randint(*LEAVING_RANGE)

    def status_line(self) -> str:
        s, t = self.status, self.timer
        if s == S.WAITING:
            return "  WAITING"
        elif s == S.TRANS_ARRIVING:
            return f"  TRANSPORT — transporter arriving  ({_fmt(t)})"
        elif s == S.TRANS_ENROUTE:
            return f"  TRANSPORT — en route to bay       ({_fmt(t)})"
        elif s == S.IN_HOLDING:
            slot = self.holding_slot + 1
            label = f"Overflow {slot - BAY_PROPER}" if self.holding_slot >= BAY_PROPER else f"Bay {slot}"
            return f"  IN HOLDING [{label}]"
        elif s == S.ORAL_CONTRAST:
            return f"  ORAL CONTRAST  ({_fmt(t)} remaining)"
        elif s == S.INJECTOR:
            return f"  INJECTOR FILL  ({_fmt(t)} remaining)"
        elif s == S.SCANNING:
            sc = self.scanner_idx + 1
            return f"  SCANNING [Scanner {sc}]  ({_fmt(t)} remaining)"
        elif s == S.COOLDOWN:
            sc = self.scanner_idx + 1
            return f"  COOLDOWN [Scanner {sc}]  ({_fmt(t)} remaining)"
        elif s == S.SCAN_COMPLETE:
            return f"  SCAN DONE  \u2190 type: leave {self.number}"
        elif s == S.LEAVING:
            return f"  LEAVING  ({_fmt(t)} remaining)"
        elif s == S.DONE:
            return "  COMPLETED \u2713"
        return f"  {s}"

    @property
    def is_active(self) -> bool:
        return self.status not in (S.DONE,)


class ScannerInfo:
    def __init__(self, scanner_id: str, zone: str, tech: str):
        self.scanner_id  = scanner_id
        self.zone        = zone
        self.tech        = tech
        self.patient_num = None    # None = IDLE

    @property
    def is_idle(self) -> bool:
        return self.patient_num is None


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------
def _fmt(secs: float) -> str:
    """Format real-seconds as m:ss."""
    s = max(0, int(secs))
    return f"{s // 60}:{s % 60:02d}"


def _saddstr(win, y: int, x: int, text: str, attr: int = 0):
    """addstr clipped to window bounds."""
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
        self.speed    = speed
        self.patients : list = []
        self.holding  : list = [None] * (BAY_PROPER + BAY_OVERFLOW)

        _scanner_defs = [
            ("ED-1",   "ED",   "Alice"),
            ("Main-1", "Main", "Bob"),
            ("Main-2", "Main", "Carol"),
            ("Main-3", "Main", "Dan"),
        ]
        self.scanners : list = [ScannerInfo(*_scanner_defs[i]) for i in range(min(num_scanners, 4))]

        self.log      : list = []
        self.lock     = threading.Lock()
        self._next_n  = 1
        self._last_t  = time.monotonic()
        self._running = True
        self._thread  = threading.Thread(target=self._tick_loop, daemon=True)
        self._thread.start()

    # ------------------------------------------------------------------
    # Helpers (call under lock)
    # ------------------------------------------------------------------
    def _gs(self, game_seconds: int) -> float:
        return game_seconds * self.speed

    def _log(self, msg: str):
        self.log.append(msg)
        if len(self.log) > 60:
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

    # ------------------------------------------------------------------
    # Public: spawn patient
    # ------------------------------------------------------------------
    def add_patient(self, acuity=None, exam=None):
        if acuity is None:
            acuity = random.choices([1, 2, 3, 4], weights=[2, 3, 80, 15])[0]
        if exam is None:
            exam = random.choice(ACUITY_EXAMS[acuity])
        with self.lock:
            n = self._next_n
            self._next_n += 1
            p = TUIPatient(n, f"PAT_{n:04d}", acuity, exam)
            self.patients.append(p)
            self._log(f"Order #{n} arrived — {p.patient_id}  [{ACUITY_LABEL[acuity]}]  {exam.upper()}")

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
            self._log(f"#{num} {p.patient_id} — transport initiated  "
                      f"(transporter arriving in {_fmt(p.timer)})")
            return ""

    def cmd_scan(self, num: int) -> str:
        with self.lock:
            p = self._get(num)
            if p is None:
                return f"No order #{num}"
            if p.status != S.IN_HOLDING:
                return f"#{num} must be IN_HOLDING to scan (currently: {p.status})"

            # Oral contrast first (if not done yet)
            if p.oral_contrast and not p.oral_done:
                p.status = S.ORAL_CONTRAST
                p.timer  = self._gs(ORAL_GS)
                self._log(f"#{num} {p.patient_id} — oral contrast started  "
                          f"({_fmt(p.timer)} wait) — scan again when complete")
                return ""

            # Claim a scanner
            idx = self._free_scanner()
            if idx == -1:
                return "No scanner available right now"
            sc = self.scanners[idx]
            sc.patient_num = num
            p.scanner_idx  = idx

            if p.iv_contrast:
                p.status = S.INJECTOR
                p.timer  = self._gs(INJECTOR_GS)
                self._log(f"#{num} {p.patient_id} — injector fill on Scanner {idx+1}  "
                          f"({_fmt(p.timer)} fill, then {_fmt(self._gs(p.scan_gs))} scan)")
            else:
                p.status = S.SCANNING
                p.timer  = self._gs(p.scan_gs)
                self._log(f"#{num} {p.patient_id} — scanning on Scanner {idx+1}  "
                          f"({_fmt(p.timer)} remaining)")
            return ""

    def cmd_leave(self, num: int) -> str:
        with self.lock:
            p = self._get(num)
            if p is None:
                return f"No order #{num}"
            if p.status != S.SCAN_COMPLETE:
                return f"#{num} must be SCAN_COMPLETE (currently: {p.status})"
            # Free holding bay
            if p.holding_slot >= 0:
                self.holding[p.holding_slot] = None
                p.holding_slot = -1
            p.status = S.LEAVING
            p.timer  = self._gs(p.leaving_gs)
            self._log(f"#{num} {p.patient_id} — leaving, transport arriving in {_fmt(p.timer)}")
            return ""

    def cmd_clear(self) -> str:
        with self.lock:
            before = len(self.patients)
            self.patients = [p for p in self.patients if p.status != S.DONE]
            removed = before - len(self.patients)
            return f"Cleared {removed} completed order(s)" if removed else "No completed orders to clear"

    def cmd_speed(self, factor: float) -> str:
        with self.lock:
            self.speed = max(0.01, min(20.0, factor))
            return f"Speed set to {self.speed:.2f}x"

    # ------------------------------------------------------------------
    # Timer thread
    # ------------------------------------------------------------------
    def _tick_loop(self):
        while self._running:
            time.sleep(0.05)
            now = time.monotonic()
            with self.lock:
                dt = now - self._last_t
                self._last_t = now
                for p in self.patients:
                    self._advance(p, dt)

    def _advance(self, p: TUIPatient, dt: float):
        s = p.status
        if s in (S.WAITING, S.IN_HOLDING, S.SCAN_COMPLETE, S.DONE):
            return  # no countdown running

        p.timer = max(0.0, p.timer - dt)

        if s == S.TRANS_ARRIVING and p.timer <= 0:
            p.status = S.TRANS_ENROUTE
            p.timer  = self._gs(p.holdwait_gs)

        elif s == S.TRANS_ENROUTE and p.timer <= 0:
            slot = self._free_bay()
            if slot == -1:
                self._log(f"\u26a0  HOLDING FULL — #{p.number} {p.patient_id} waiting outside!")
                p.timer = self._gs(15)   # retry in 15 game-seconds
            else:
                self.holding[slot] = p.number
                p.holding_slot = slot
                label = (f"Overflow {slot - BAY_PROPER + 1}"
                         if slot >= BAY_PROPER else f"Bay {slot + 1}")
                p.status = S.IN_HOLDING
                self._log(f"#{p.number} {p.patient_id} — arrived in {label}")

        elif s == S.ORAL_CONTRAST and p.timer <= 0:
            p.oral_done = True
            p.status    = S.IN_HOLDING
            self._log(f"#{p.number} {p.patient_id} — oral contrast complete, ready to scan")

        elif s == S.INJECTOR and p.timer <= 0:
            p.status = S.SCANNING
            p.timer  = self._gs(p.scan_gs)
            self._log(f"#{p.number} {p.patient_id} — injector done, now scanning  "
                      f"({_fmt(p.timer)} remaining)")

        elif s == S.SCANNING and p.timer <= 0:
            p.status = S.COOLDOWN
            p.timer  = self._gs(COOLDOWN_GS)
            sc = self.scanners[p.scanner_idx]
            self._log(f"#{p.number} {p.patient_id} — scan complete, cooldown  ({_fmt(p.timer)})")

        elif s == S.COOLDOWN and p.timer <= 0:
            # Release scanner
            sc = self.scanners[p.scanner_idx]
            sc.patient_num = None
            p.scanner_idx  = -1
            p.status       = S.SCAN_COMPLETE
            self._log(f"#{p.number} {p.patient_id} — SCAN COMPLETE  \u2190 type: leave {p.number}")

        elif s == S.LEAVING and p.timer <= 0:
            p.status = S.DONE
            self._log(f"#{p.number} {p.patient_id} — departed, exam complete \u2713")

    def stop(self):
        self._running = False


# ---------------------------------------------------------------------------
# Curses colour pairs
# ---------------------------------------------------------------------------
CP_TITLE    = 1
CP_TRAUMA   = 2    # red
CP_CRITICAL = 3    # yellow
CP_STAT     = 4    # green
CP_ROUTINE  = 5    # default
CP_DONE     = 6    # dim
CP_HEADER   = 7    # cyan headers
CP_WARN     = 8    # red warnings
CP_SCANNER  = 9    # magenta
CP_CMD      = 10   # yellow prompt
CP_TRANS    = 11   # blue for transport

ACUITY_CP = {1: CP_TRAUMA, 2: CP_CRITICAL, 3: CP_STAT, 4: CP_ROUTINE}

STATUS_CP = {
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
    curses.init_pair(CP_TITLE,    curses.COLOR_BLACK,  curses.COLOR_CYAN)
    curses.init_pair(CP_TRAUMA,   curses.COLOR_RED,    -1)
    curses.init_pair(CP_CRITICAL, curses.COLOR_YELLOW, -1)
    curses.init_pair(CP_STAT,     curses.COLOR_GREEN,  -1)
    curses.init_pair(CP_ROUTINE,  -1,                  -1)
    curses.init_pair(CP_DONE,     curses.COLOR_BLACK,  -1)
    curses.init_pair(CP_HEADER,   curses.COLOR_CYAN,   -1)
    curses.init_pair(CP_WARN,     curses.COLOR_RED,    -1)
    curses.init_pair(CP_SCANNER,  curses.COLOR_MAGENTA,-1)
    curses.init_pair(CP_CMD,      curses.COLOR_YELLOW, -1)
    curses.init_pair(CP_TRANS,    curses.COLOR_BLUE,   -1)


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------
def _hline(win, y: int, x: int, width: int, title: str = "", cp: int = CP_HEADER):
    attr = curses.color_pair(cp) | curses.A_BOLD
    _saddstr(win, y, x, "\u2500" * width, attr)
    if title:
        _saddstr(win, y, x + 2, f" {title} ", attr)


def _draw_orders(win, state: TUIState, x: int, w: int, y0: int, y1: int):
    total = len(state.patients)
    _hline(win, y0, x, w, f"ORDERS [{total}]")
    row = y0 + 1
    lim = y1 - 1

    for p in state.patients:
        if row >= lim:
            break
        # Line 1: number + ID + acuity badge
        cp   = ACUITY_CP.get(p.acuity, CP_ROUTINE)
        attr = curses.color_pair(cp) | curses.A_BOLD
        if p.status == S.DONE:
            attr = curses.color_pair(CP_DONE) | curses.A_DIM
        badge = ACUITY_LABEL[p.acuity]
        _saddstr(win, row, x, f" #{p.number:<2} {p.patient_id}  [{badge}]", attr)
        row += 1
        if row >= lim:
            break

        # Line 2: exam name
        _saddstr(win, row, x + 5, p.exam.upper(),
                 curses.color_pair(CP_DONE if p.status == S.DONE else CP_ROUTINE))
        row += 1
        if row >= lim:
            break

        # Line 3: status label
        s_cp   = STATUS_CP.get(p.status, CP_ROUTINE)
        s_attr = curses.color_pair(s_cp)
        if p.status == S.DONE:
            s_attr = curses.color_pair(CP_DONE) | curses.A_DIM
        elif p.status == S.SCAN_COMPLETE:
            s_attr = curses.color_pair(CP_CMD) | curses.A_BOLD
        _saddstr(win, row, x, p.status_line(), s_attr)
        row += 1

        # Blank separator
        row += 1


def _draw_holding(win, state: TUIState, x: int, w: int, y0: int, y1: int):
    _hline(win, y0, x, w, "HOLDING BAYS")
    row = y0 + 1
    lim = y1 - 1

    # Proper slots
    _saddstr(win, row, x + 1, f"\u2500\u2500 Proper ({BAY_PROPER} slots) \u2500\u2500",
             curses.color_pair(CP_HEADER))
    row += 1

    for i in range(BAY_PROPER):
        if row >= lim:
            break
        occ = state.holding[i]
        if occ is None:
            _saddstr(win, row, x + 1, f"  Slot {i+1}: (empty)",
                     curses.color_pair(CP_DONE) | curses.A_DIM)
        else:
            p = state._get(occ)
            if p:
                cp = ACUITY_CP.get(p.acuity, CP_ROUTINE)
                flag = " \u26a0 OVERFLOW" if i >= BAY_PROPER else ""
                _saddstr(win, row, x + 1,
                         f"  Slot {i+1}: #{occ} {p.exam.upper()}{flag}",
                         curses.color_pair(cp) | curses.A_BOLD)
        row += 1

    if row < lim:
        row += 1
        _saddstr(win, row, x + 1, f"\u2500\u2500 Overflow ({BAY_OVERFLOW} slots) \u2500\u2500",
                 curses.color_pair(CP_WARN))
        row += 1

    for i in range(BAY_OVERFLOW):
        si = BAY_PROPER + i
        if row >= lim:
            break
        occ = state.holding[si]
        if occ is None:
            _saddstr(win, row, x + 1, f"  OVR {i+1}: (empty)",
                     curses.color_pair(CP_DONE) | curses.A_DIM)
        else:
            p = state._get(occ)
            if p:
                _saddstr(win, row, x + 1,
                         f"  OVR {i+1}: #{occ} {p.exam.upper()} \u26a0 PENALTY",
                         curses.color_pair(CP_WARN) | curses.A_BOLD)
        row += 1


def _draw_scanners(win, state: TUIState, x: int, w: int, y0: int, y1: int):
    _hline(win, y0, x, w, "SCANNERS")
    row = y0 + 1
    lim = y1 - 1

    for i, sc in enumerate(state.scanners):
        if row + 4 >= lim:
            break

        # Scanner header
        label = f"Scanner {i+1}  [{sc.zone}]  Tech: {sc.tech}"
        _saddstr(win, row, x + 1, label,
                 curses.color_pair(CP_SCANNER) | curses.A_BOLD)
        row += 1

        p = state._get(sc.patient_num) if sc.patient_num is not None else None

        if sc.is_idle:
            _saddstr(win, row, x + 3, "\u25cf IDLE",
                     curses.color_pair(CP_STAT) | curses.A_BOLD)
            row += 1
        elif p:
            # Show phase
            phase_map = {
                S.INJECTOR: ("INJECTOR FILL", CP_CRITICAL),
                S.SCANNING: ("SCANNING",      CP_SCANNER),
                S.COOLDOWN: ("COOLDOWN",      CP_CRITICAL),
            }
            phase_label, phase_cp = phase_map.get(p.status, (p.status, CP_ROUTINE))
            timer_str = f"  ({_fmt(p.timer)} rem)" if p.status in (S.INJECTOR, S.SCANNING, S.COOLDOWN) else ""
            _saddstr(win, row, x + 3,
                     f"\u25c8 {phase_label}{timer_str}",
                     curses.color_pair(phase_cp) | curses.A_BOLD)
            row += 1

            # Patient info
            if row < lim:
                cp = ACUITY_CP.get(p.acuity, CP_ROUTINE)
                _saddstr(win, row, x + 5,
                         f"#{p.number} {p.patient_id}  {p.exam.upper()}",
                         curses.color_pair(cp))
                row += 1
        else:
            row += 1

        row += 1   # gap between scanners


def _draw_log(win, state: TUIState, y: int, log_h: int, width: int):
    _hline(win, y, 0, width, "LOG")
    entries = state.log[-(log_h):]
    for i, entry in enumerate(reversed(entries)):
        ly = y + log_h - i
        if ly <= y:
            break
        _saddstr(win, ly, 2, entry, curses.color_pair(CP_ROUTINE))


def _draw_cmdbar(win, cmd_buf: str, err: str, speed: float, height: int, width: int):
    y_sep = height - 3
    y_hlp = height - 2
    y_inp = height - 1
    _hline(win, y_sep, 0, width)
    help_txt = "trans <n>  scan <n>  leave <n>  add  clear  speed <f>  quit"
    _saddstr(win, y_hlp, 2, help_txt, curses.color_pair(CP_HEADER))
    spd_txt = f"speed: {speed:.2f}x"
    _saddstr(win, y_hlp, width - len(spd_txt) - 2, spd_txt, curses.color_pair(CP_HEADER))
    _hline(win, y_inp - 1 if y_inp > 0 else y_inp, 0, 0)   # suppress, use separator above
    prompt = f"> {cmd_buf}"
    if err:
        _saddstr(win, y_inp, 1, prompt, curses.color_pair(CP_ROUTINE))
        _saddstr(win, y_inp, len(prompt) + 3, f"  \u2190 {err}", curses.color_pair(CP_WARN))
    else:
        _saddstr(win, y_inp, 1, prompt + "\u2588", curses.color_pair(CP_CMD))


def render(win, state: TUIState, cmd_buf: str, err: str):
    win.erase()
    height, width = win.getmaxyx()

    # Title bar
    title = "  CTDash  TUI Test Runner  "
    _saddstr(win, 0, 0, " " * (width - 1), curses.color_pair(CP_TITLE) | curses.A_BOLD)
    _saddstr(win, 0, (width - len(title)) // 2, title,
             curses.color_pair(CP_TITLE) | curses.A_BOLD)

    # Layout: 3 columns | log strip | cmd bar
    log_h    = 4
    cmd_h    = 3
    panel_h  = height - 1 - log_h - cmd_h
    y0, y1   = 1, 1 + panel_h
    log_y    = y1

    ow = max(28, int(width * 0.36))
    hw = max(20, int(width * 0.26))
    sw = width - ow - hw

    ox, hx, sx = 0, ow, ow + hw

    # Vertical dividers
    for r in range(y0, y1):
        try:
            win.addch(r, hx - 1, curses.ACS_VLINE, curses.color_pair(CP_HEADER))
            win.addch(r, sx - 1, curses.ACS_VLINE, curses.color_pair(CP_HEADER))
        except curses.error:
            pass

    with state.lock:
        _draw_orders(win, state, ox, ow - 1, y0, y1)
        _draw_holding(win, state, hx, hw - 1, y0, y1)
        _draw_scanners(win, state, sx, sw - 1, y0, y1)
        _draw_log(win, state, log_y, log_h - 1, width)
        _draw_cmdbar(win, cmd_buf, err, state.speed, height, width)

    win.refresh()


# ---------------------------------------------------------------------------
# Command parser
# ---------------------------------------------------------------------------
def handle_command(raw: str, state: TUIState) -> str:
    """Parse and execute a command. Returns error string or '' on success."""
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
            elif key == 27:   # ESC clears buffer
                cmd_buf = ""


def run(num_scanners: int = 2, speed: float = DEFAULT_SPEED):
    state = TUIState(speed=speed, num_scanners=num_scanners)

    # Pre-load a realistic set of starting orders
    state.add_patient(3, "head")
    state.add_patient(2, "cta_chest")
    state.add_patient(1, "trauma_full")
    state.add_patient(3, "abdpel")
    state.add_patient(4, "chest")

    try:
        curses.wrapper(lambda scr: _main(scr, state))
    finally:
        state.stop()

    print("CTDash TUI Test Runner exited.")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="CTDash TUI Test Runner")
    ap.add_argument("--scanners", type=int, default=2, choices=[1, 2, 3, 4],
                    help="Number of scanners to use (default: 2)")
    ap.add_argument("--speed", type=float, default=DEFAULT_SPEED,
                    help=f"Time multiplier: real-secs per game-sec (default: {DEFAULT_SPEED})")
    args = ap.parse_args()
    run(num_scanners=args.scanners, speed=args.speed)
