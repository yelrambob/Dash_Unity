// GameConfig — central location for all tunable numbers.
// Changing a value here affects the whole simulation.
// No logic lives here — just values.
//
// TIME COMPRESSION: 1 real second = ~3.5 game-minutes
// Full 14-hour shift = ~24 real minutes at this ratio.
// Adjust TIME_SCALE to speed up or slow down the whole game.

using System.Collections.Generic;

namespace CTDash
{
    public static class GameConfig
    {
        public const int TIME_SCALE = 210;   // game-seconds per real second

        // --- Scan times (in game-seconds) --------------------------------
        public static readonly Dictionary<string, int> SCAN_TIMES = new Dictionary<string, int>
        {
            { "head",        20 },
            { "abdpel",      50 },
            { "trauma_full", 70 },
            { "chest",       25 },
            { "cta_head",    45 },
            { "cta_chest",   35 },
            { "spine",       30 },
            { "extremity",   35 },
        };

        // --- Cooldown between scans (in game-seconds) --------------------
        public const int SCANNER_COOLDOWN = 20;

        // --- Transport delays (min, max) in game-seconds -----------------
        public static readonly (int Min, int Max) TRANSPORT_ARRIVAL_DELAY  = (20, 60);
        public static readonly (int Min, int Max) TRANSPORT_HOLD_WAIT      = ( 5, 30);
        public static readonly (int Min, int Max) TRANSPORT_LEAVING_DELAY  = ( 5, 20);

        // --- Contrast timings (in game-seconds) --------------------------
        public const int ORAL_CONTRAST_WAIT  = 120;
        public const int INJECTOR_FILL_TIME  =  20;

        // --- Holding bay capacity ----------------------------------------
        public const int HOLDING_PROPER_SLOTS   = 4;
        public const int HOLDING_OVERFLOW_SLOTS = 3;

        // --- Scoring ---------------------------------------------------------
        public const int   EXAM_BASE_SCORE         = 100;
        public const int   WAIT_PENALTY_PER_MINUTE =   5;
        public const int   OVERFLOW_PENALTY        =  50;
        public const int   HOLDOVER_PENALTY        = 150;

        // --- Level definitions -------------------------------------------
        public struct LevelConfig
        {
            public int PlayDuration;         // real seconds
            public int ShiftStartHour;
            public int ShiftEndHour;
            public int Scanners;
            public int Techs;
        }

        public static readonly Dictionary<int, LevelConfig> LEVELS = new Dictionary<int, LevelConfig>
        {
            { 1, new LevelConfig { PlayDuration =  8 * 60, ShiftStartHour = 7, ShiftEndHour = 11, Scanners = 2, Techs = 2 } },
            { 2, new LevelConfig { PlayDuration = 10 * 60, ShiftStartHour = 7, ShiftEndHour = 13, Scanners = 2, Techs = 2 } },
            { 3, new LevelConfig { PlayDuration = 12 * 60, ShiftStartHour = 7, ShiftEndHour = 15, Scanners = 3, Techs = 3 } },
            { 4, new LevelConfig { PlayDuration = 15 * 60, ShiftStartHour = 7, ShiftEndHour = 17, Scanners = 3, Techs = 3 } },
            { 5, new LevelConfig { PlayDuration = 20 * 60, ShiftStartHour = 7, ShiftEndHour = 20, Scanners = 4, Techs = 4 } },
        };

        // --- Tech speed modifier -----------------------------------------
        // Formula: scan_time * (1.0 + (1.0 - tech.speed) * 0.5)
        public const bool USE_TECH_SPEED_MODIFIER = false;

        // --- Simulation tick ----------------------------------------------
        public const int TICK_SECONDS = 1;

        // --- Shift length ------------------------------------------------
        // Full playable span: 06:00 – 21:00 (15 hours covers every level's window).
        public const int  GAME_DURATION_HOURS = 15;
        public const int  GAME_START_HOUR     =  6;
    }
}
