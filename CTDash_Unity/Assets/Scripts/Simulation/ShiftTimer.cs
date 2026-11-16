// ShiftTimer — controls the game clock.
// Tracks current game-time hour and minute.
// Fires hourly flag so callers can update spawn rate and staffing.
// Triggers end-of-shift when elapsed time reaches duration.

namespace CTDash
{
    public class ShiftTimer
    {
        private int _elapsedSeconds;
        private int _totalSeconds;

        public ShiftTimer(int durationHours = GameConfig.GAME_DURATION_HOURS)
        {
            _elapsedSeconds = 0;
            _totalSeconds   = durationHours * 3600;
        }

        public int  GameSecond   => _elapsedSeconds;
        public int  GameHour     => GameConfig.GAME_START_HOUR + (_elapsedSeconds / 3600);
        public int  GameMinute   => (_elapsedSeconds % 3600) / 60;
        public bool IsShiftOver  => _elapsedSeconds >= _totalSeconds;

        // Returns true if the tick crossed into a new game-hour.
        public bool Tick()
        {
            int prevHour = GameHour;
            _elapsedSeconds += GameConfig.TICK_SECONDS;
            return GameHour != prevHour;
        }

        public string TimeString => $"{GameHour:D2}:{GameMinute:D2}";
    }
}
