# [BUILD FIRST]
# Central location for all tunable numbers.
# Changing a value here affects the whole simulation.
# No logic lives here — just values.
#
# TIME COMPRESSION: 1 real second = ~3.5 game-minutes
# Full 14-hour shift = ~24 real minutes at this ratio.
# Adjust TIME_SCALE to speed up or slow down the whole game.

TIME_SCALE = 210   # game-seconds per real second (210 = 3.5 game-minutes per real second)
                   # Increase to make the game run faster, decrease to slow it down.

# --- Scan times (in game-seconds) -----------------------------------------
# These feel like 2-8 real seconds to the player at default TIME_SCALE.
# Possible change: add a tech speed modifier that multiplies these values.
SCAN_TIMES = {
    "head":        20,    # simple, fast — should feel almost instant
    "abdpel":      50,    # bread and butter exam, moderate weight
    "trauma_full": 70,    # longest single exam, high stakes
    "chest":       25,    # quick, common
    "cta_head":    45,    # contrast dependent, slightly longer
    "cta_chest":   35,
    "spine":       30,
    "extremity":   35,
}

# --- Cooldown between scans (in game-seconds) -----------------------------
# Time scanner is unavailable after a scan completes (table reset, etc).
# Possible change: tech skill could reduce this.
SCANNER_COOLDOWN = 20

# --- Transport delays (min, max) in game-seconds --------------------------
# Three phases. At TIME_SCALE these feel like brief pauses to the player.
# Possible change: level difficulty could shift ranges upward.
TRANSPORT_INBOUND  = (30,  90)   # call for patient + deliver to scanner area
                                  #   (absorbs old arrival + hold_wait — one clean timer)
SCANNER_SETUP      = (20,  55)   # table on / position / scan / table off
                                  #   meaty middle phase; mobility matters most here
TRANSPORT_OUTBOUND = (10,  30)   # transporter arrives post-scan, patient leaves dept

# --- Contrast timings (in game-seconds) -----------------------------------
# Oral contrast is a major pacing mechanic — patient is stuck waiting.
# Possible change: acuity 1 patients could bypass oral contrast requirement.
ORAL_CONTRAST_WAIT   = 180    # ~45 real game-minutes compressed; feels like ~12 real seconds
INJECTOR_FILL_TIME   =  20    # short but requires player attention

# --- Holding bay capacity -------------------------------------------------
HOLDING_PROPER_SLOTS  = 4
HOLDING_OVERFLOW_SLOTS = 3

# --- Scoring --------------------------------------------------------------
EXAM_BASE_SCORE          = 100    # points per completed exam
WAIT_PENALTY_PER_MINUTE  =  10    # points lost per game-minute over wait threshold
OVERFLOW_PENALTY         =  50    # flat penalty per overflow patient
HOLDOVER_PENALTY         = 150    # flat penalty per patient left at shift end
                                   # Possible change: holdover penalty scales with acuity

# --- Level definitions ----------------------------------------------------
# Each level unlocks more of the shift window and adds scanners/complexity.
# play_duration is real seconds. shift_window is (start_hour, end_hour) game time.
# Possible change: add a "randomise staff quality" flag per level.
LEVELS = {
    1: {"play_duration":  8 * 60, "shift_window": ( 7, 11), "scanners": 2, "techs": 2},
    2: {"play_duration": 10 * 60, "shift_window": ( 7, 13), "scanners": 2, "techs": 2},
    3: {"play_duration": 12 * 60, "shift_window": ( 7, 15), "scanners": 3, "techs": 3},
    4: {"play_duration": 15 * 60, "shift_window": ( 7, 17), "scanners": 3, "techs": 3},
    5: {"play_duration": 20 * 60, "shift_window": ( 7, 20), "scanners": 4, "techs": 4},
    # Level 5 = your real Monday/Friday full shift. Endgame.
}

# --- Mobility multipliers -------------------------------------------------
# Rolled delays are multiplied after the random draw, so variance is preserved
# but the mean shifts. Two separate tables because setup is where it really bites.
#
# MOBILITY_TRANSPORT_MULT — applied to inbound_delay and leaving_delay.
#   Ambulatory patients can meet the transporter / walk out; stretcher needs
#   full bed logistics at each end.
MOBILITY_TRANSPORT_MULT = {
    "ambulatory": 0.75,   # can meet the transporter, walks out on own
    "wheelchair": 1.0,    # baseline
    "stretcher":  1.35,   # bed logistics add time but transport is mostly waiting
}

# MOBILITY_SETUP_MULT — applied to setup_delay (table on / position / table off).
#   This is where mobility really bites: stretcher → bed-to-table transfer,
#   positioning aids, extra staff. Ambulatory just hops on.
MOBILITY_SETUP_MULT = {
    "ambulatory": 0.55,   # hops on table, minimal positioning
    "wheelchair": 1.0,    # baseline — transfer assist needed
    "stretcher":  1.9,    # full lateral transfer + positioning + reverse — the real cost
}

# --- Event probabilities (per patient per game-second) --------------------
# Checked once per patient per tick against all pre-terminal patients.
# At ~300 game-second average patient lifetime and ~20 concurrent patients:
#   CANCEL: ~2% lifetime chance → roughly 1–2 cancellations per full shift
#   REFUSE: ~0.5% lifetime chance → roughly 0–1 refusals per full shift
# REFUSED is rarer than CANCELLED — it is genuinely uncommon for a patient
# to refuse a CT that was ordered.  Cancellations are the more common surprise.
EVENT_CANCEL_PROB = 0.000067   # per patient per game-second
EVENT_REFUSE_PROB = 0.000017   # per patient per game-second

# --- Simulation tick ------------------------------------------------------
TICK_SECONDS = 1    # how many game-seconds pass per simulation tick
                    # Keep this at 1 unless performance becomes a problem.