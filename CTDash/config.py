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
