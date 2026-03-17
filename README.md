# CLAUDE.md — Dash_Unity / CTDash

This file documents the codebase structure, conventions, and development guidance for AI assistants working in this repository.

---

## Project Overview

**CTDash** is a real-time CT department management simulation game written in pure Python. Players manage patient flow through a radiology CT department across a simulated work shift. The domain model is derived from real-world CT department volume and acuity data.

The project currently has a **complete structural scaffold** (all classes, interfaces, data tables, and configuration) but **no implemented logic** — all manager methods are stubs marked `TODO`. The immediate development goal is filling in the manager implementations in the correct build order.

---

## Repository Layout

```
Dash_Unity/
├── README.md               # This file (AI assistant guidance — was originally CLAUDE.md)
├── file_tree.py            # One-time scaffold generator (do not re-run)
└── CTDash/                 # Entire Python simulation package
    ├── __init__.py
    ├── main.py             # Entry point: initialises managers, starts GameLoop
    ├── config.py           # All tunable numbers (scan times, penalties, levels)
    ├── classes/            # Pure data structures — no business logic
    │   ├── patient.py
    │   ├── exam.py
    │   ├── scanner.py
    │   ├── tech.py
    │   ├── transport.py
    │   └── holding_bay.py
    ├── managers/           # Simulation logic — all currently stubs
    │   ├── spawn_manager.py
    │   ├── queue_manager.py
    │   ├── scanner_manager.py
    │   ├── transport_manager.py
    │   ├── contrast_manager.py
    │   ├── scoring_manager.py
    │   └── staffing_manager.py
    ├── data/               # Game balance tables — do not hardcode these in logic
    │   ├── exam_catalog.py
    │   ├── acuity_table.py
    │   ├── hourly_spawn_weights.py
    │   └── tech_roster.py
    ├── simulation/         # Game clock and main loop orchestration
    │   ├── shift_timer.py
    │   └── game_loop.py
    └── tests/              # Test stubs — implement alongside managers
        ├── test_spawn.py
        ├── test_queue.py
        ├── test_scanner.py
        └── test_full_shift.py
```

---

## Tech Stack

- **Language**: Python 3.11+ (standard library only — zero external dependencies)
- **Type hints**: `dataclasses`, `enum`, `typing` throughout
- **Data structures**: `heapq` for priority queue, `random` for transport delays
- **No build step**: run directly with `python -m CTDash.main` from the repo root

---

## Running the Simulation

```bash
# From repo root
cd /home/user/Dash_Unity
python -m CTDash.main
```

## Running Tests

```bash
# From repo root
python -m unittest CTDash.tests.test_spawn
python -m unittest CTDash.tests.test_queue
python -m unittest CTDash.tests.test_scanner
python -m unittest CTDash.tests.test_full_shift

# Or all at once
python -m unittest discover -s CTDash/tests
```

Tests are currently stubs. Implement them alongside their corresponding managers.

---

## Architecture

### Design Patterns

**Manager pattern** — Each subsystem is owned by a dedicated manager class. Managers hold state and handle all transitions for their domain. Classes are plain data containers; managers contain all logic.

**State machines** — Every game entity has an `Enum`-based state field. Never mutate state directly in classes; state transitions belong in the relevant manager.

**Data-driven config** — All numbers (timings, penalties, level definitions) live in `config.py` or the `data/` tables. Logic files must not hardcode numeric values; always import from config.

**Tick-based simulation** — The game loop advances by one `TICK_SECONDS` step per iteration. Every manager exposes a `tick(game_second)` method called by `GameLoop._tick()` in a fixed order.

### The Tick Order (critical — do not change without understanding dependencies)

```
1. shift_timer   — advance the clock; returns True if a new hour began
2. spawn         — maybe spawn a patient this tick
3. transport     — advance transport state machines
4. queue         — increment wait timers for queued patients
5. contrast      — count down oral/IV contrast timers
6. scanner       — advance scan and cooldown timers, assign next patient
7. scoring       — check thresholds, apply penalties, update score
```

Managers later in the order may depend on state set by earlier managers in the same tick. Keep this order.

### Time Model

- `TIME_SCALE = 210` — game-seconds that pass per real second
- All timers in the code are in **game-seconds** (integers)
- A 14-hour shift runs in ~24 real minutes at default TIME_SCALE
- Staffing uses float hours (`shift_start=7.0`); everything else uses int seconds
- Adjust `TIME_SCALE` in `config.py` to speed up or slow down the whole game — no other changes needed

---

## Key Domain Concepts

### Patient Acuity (4 tiers)

| Tier | Label    | Spawn weight | Wait threshold |
|------|----------|-------------|----------------|
| 1    | Trauma   | ~2%         | Strict (high penalty) |
| 2    | Critical | ~3%         | High |
| 3    | STAT     | ~80%        | Moderate |
| 4    | Routine  | ~15%        | Lenient |

Lower acuity number = higher priority = penalised more heavily for waiting.

### Patient State Machine

```
ORDERED → IN_TRANSPORT → IN_HOLDING
       → CONTRAST_ORDERED → CONTRAST_READY
       → INJECTOR_READY → SCANNING → COOLDOWN
       → LEAVING → COMPLETED
                → REFUSED
                → HOLDOVER
```

### Exam Types (8 defined in `data/exam_catalog.py`)

`head` (20s), `chest` (25s), `spine` (30s), `cta_chest` (35s), `extremity` (35s),
`cta_head` (45s), `abdpel` (50s), `trauma_full` (70s)

Times are in game-seconds and come from `config.SCAN_TIMES` — never from the exam catalog directly.

### Scanner States

`IDLE → SCANNING → COOLDOWN → IDLE` (can also be `LOCKED`)

Cooldown is `SCANNER_COOLDOWN = 20` game-seconds between scans.

### Scoring

- `+100` per completed exam (`EXAM_BASE_SCORE`) — note: the stub in `scoring_manager.py` currently hardcodes `+10`; replace with `EXAM_BASE_SCORE` from `config.py` when implementing
- `-10` per game-minute over the acuity wait threshold (`WAIT_PENALTY_PER_MINUTE`)
- `-50` flat per overflow patient (`OVERFLOW_PENALTY`)
- `-150` flat per holdover at shift end (`HOLDOVER_PENALTY`)

### Levels (5 levels)

| Level | Real time | Shift window | Scanners | Techs |
|-------|-----------|-------------|---------|-------|
| 1     | 8 min     | 07–11       | 2       | 2     |
| 2     | 10 min    | 07–13       | 2       | 2     |
| 3     | 12 min    | 07–15       | 3       | 3     |
| 4     | 15 min    | 07–17       | 3       | 3     |
| 5     | 20 min    | 07–20       | 4       | 4     |

---

## Conventions

### Naming

| Thing | Convention | Example |
|-------|-----------|---------|
| Config constants | `UPPER_SNAKE_CASE` | `SCAN_TIMES`, `ORAL_CONTRAST_WAIT` |
| Exam/data keys | `lower_snake_case` strings | `"cta_chest"`, `"trauma_full"` |
| Entity IDs | Prefixed strings | `"PAT_0001"`, `"tech_01"`, `"SCANNER_ED_1"` |
| Private manager state | Leading underscore | `self._heap`, `self._active_techs` |
| Boolean properties | `is_` prefix via `@property` | `is_available`, `is_overflowing` |
| Lists of entities | Plural nouns | `exam_list`, `_patients` |

### Build Phase Comments

Source files are tagged with their build priority:

- `# [BUILD FIRST]` — foundation files; implement these before anything else
- `# [LATER]` — depends on BUILD FIRST being stable
- `# [LATER — depends on X]` — has a blocking dependency on another file

When implementing stubs, work through `[BUILD FIRST]` files completely before touching `[LATER]` files.

### No Business Logic in Classes

`classes/` files are pure data containers (dataclasses + enums). Do not add methods with simulation logic there. All logic goes in the matching manager.

### No Hardcoded Numbers in Logic

Any numeric constant that affects gameplay must live in `config.py`. Import it:
```python
from config import SCAN_TIMES, SCANNER_COOLDOWN
```

### State Transitions

When a manager changes a patient's or scanner's state, set the `.state` field directly on the object. State changes should be accompanied by resetting the relevant timer fields (e.g., `patient.contrast_timer = ORAL_CONTRAST_WAIT` when entering `CONTRAST_ORDERED`).

---

## Implementation Guide (for filling in stubs)

### Recommended build order

1. `classes/` — already complete; review before touching managers
2. `data/` — already complete; understand `exam_catalog.py` and `acuity_table.py`
3. `config.py` — already complete; all constants available
4. `managers/queue_manager.py` — `add_patient`, `tick`, `pop_next`
5. `managers/spawn_manager.py` — `tick`, `_spawn_patient`
6. `managers/transport_manager.py` — `tick`, transport state transitions
7. `managers/scanner_manager.py` — `try_assign`, `tick`
8. `managers/contrast_manager.py` — contrast timer countdown
9. `managers/scoring_manager.py` — penalty checks, `finalise`
10. `managers/staffing_manager.py` — tech availability (marked `[LATER]`)
11. `simulation/game_loop.py` — wire everything together in `_tick` and `_end_shift`
12. `main.py` — instantiate managers and call `GameLoop.run()`
13. Tests — implement alongside each manager

### QueueManager heap tuple format

The min-heap stores `(acuity, arrival_time, patient_id)` tuples. Acuity 1 sorts first (highest priority). Use `arrival_time` as a tiebreaker so earlier arrivals of equal acuity are served first.

### GameLoop._tick() skeleton

```python
def _tick(self):
    new_hour = self.timer.tick()
    self.managers["spawn"].tick(self.timer.game_second)
    self.managers["transport"].tick(self.timer.game_second)
    self.managers["queue"].tick(self.timer.game_second)
    self.managers["contrast"].tick(self.timer.game_second)
    self.managers["scanner"].tick(self.timer.game_second)
    self.managers["scoring"].tick(self.timer.game_second)
    if new_hour:
        # fire hourly events: update spawn rate, check staffing
        pass
```

---

## What NOT to Do

- Do not re-run `file_tree.py` — it is a one-time scaffold generator
- Do not add external dependencies — keep it stdlib only
- Do not put logic in `classes/` files
- Do not hardcode scan times, penalties, or delays in manager files
- Do not change the tick order without tracing all manager dependencies
- Do not modify `data/` tables to fix a logic bug — fix the logic
- Do not add new level definitions to `LEVELS` without adjusting `shift_window` and staffing counts consistently

---

## Git Workflow

The current development branch is `claude/update-dash-unity-docs-F4tGm`.

```bash
git add <files>
git commit -m "descriptive message"
git push -u origin claude/update-dash-unity-docs-F4tGm
```

All commits go to this branch. Do not push to `main` or other branches.
