// Tech — represents a CT technologist.

namespace CTDash
{
    public enum TechStatus
    {
        Scanning,
        Paperwork,
        Idle,
        OffShift,
    }

    public class Tech
    {
        public string     TechId;
        public string     Name;
        public float      Speed;           // 0.0–1.0, affects scan time modifier
        public float      Accuracy;        // 0.0–1.0, affects error/repeat rate
        public float      Willingness;     // 0.0–1.0, affects refusal to take patients
        public float      KnowledgeBase;   // 0.0–1.0, affects contrast/protocol decisions
        public float      ShiftStart;      // game-time hour, e.g. 7.0
        public float      ShiftEnd;        // game-time hour, e.g. 15.5

        public string     AssignedScanner; // ScannerId or null
        public TechStatus Status = TechStatus.OffShift;

        public Tech(string techId, string name, float speed, float accuracy,
                    float willingness, float knowledgeBase,
                    float shiftStart, float shiftEnd)
        {
            TechId        = techId;
            Name          = name;
            Speed         = speed;
            Accuracy      = accuracy;
            Willingness   = willingness;
            KnowledgeBase = knowledgeBase;
            ShiftStart    = shiftStart;
            ShiftEnd      = shiftEnd;
        }
    }
}
