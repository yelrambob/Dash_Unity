// TechRoster — pre-built tech profiles for early game levels.
// Each entry maps directly to a Tech object via StaffingManager.
// Later difficulty levels will have worse stat distributions.

namespace CTDash
{
    public struct TechRosterEntry
    {
        public string Id;
        public string Name;
        public float  Speed;
        public float  Accuracy;
        public float  Willingness;
        public float  KnowledgeBase;
        public float  ShiftStart;    // game-time hour, e.g. 7.0
        public float  ShiftEnd;      // game-time hour, e.g. 15.5
    }

    public static class TechRoster
    {
        public static readonly TechRosterEntry[] Roster = new TechRosterEntry[]
        {
            new TechRosterEntry
            {
                Id            = "tech_01",
                Name          = "Alex",
                Speed         = 0.85f,
                Accuracy      = 0.90f,
                Willingness   = 0.80f,
                KnowledgeBase = 0.85f,
                ShiftStart    = 7.0f,
                ShiftEnd      = 15.5f,
            },
            new TechRosterEntry
            {
                Id            = "tech_02",
                Name          = "Jordan",
                Speed         = 0.70f,
                Accuracy      = 0.75f,
                Willingness   = 0.65f,
                KnowledgeBase = 0.70f,
                ShiftStart    = 7.0f,
                ShiftEnd      = 15.5f,
            },
            // TODO: add afternoon and evening techs
        };
    }
}
