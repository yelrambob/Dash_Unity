// AcuityData — 4-tier patient acuity classification.
//
// Tier 1 — True emergencies: Trauma, Stroke.
// Tier 2 — Critical protocols: Aortic Dissection, AAA, PE, SAH.
// Tier 3 — Inflated STATs: ~80% of all orders.
// Tier 4 — Routine: Urgent, Routine inpatient, Scheduled outpatient.

using System.Collections.Generic;

namespace CTDash
{
    public struct AcuityEntry
    {
        public string   Label;
        public int      QueuePriority;
        public float    SpawnWeight;
        public string[] TypicalExams;
        public int      WaitThreshold;     // game-seconds before penalty
        public float    PenaltyMult;
        public bool     CanDowngrade;
    }

    public static class AcuityData
    {
        public static readonly Dictionary<int, AcuityEntry> Table = new Dictionary<int, AcuityEntry>
        {
            {
                1, new AcuityEntry
                {
                    Label         = "Trauma / Stroke",
                    QueuePriority = 1,
                    SpawnWeight   = 0.02f,
                    TypicalExams  = new[] { "trauma_full", "head", "cta_head" },
                    WaitThreshold = 2 * 60,
                    PenaltyMult   = 5.0f,
                    CanDowngrade  = false,
                }
            },
            {
                2, new AcuityEntry
                {
                    Label         = "Critical Protocol",
                    QueuePriority = 2,
                    SpawnWeight   = 0.03f,
                    TypicalExams  = new[] { "cta_chest", "cta_head", "abdpel", "head" },
                    WaitThreshold = 5 * 60,
                    PenaltyMult   = 3.0f,
                    CanDowngrade  = true,
                }
            },
            {
                3, new AcuityEntry
                {
                    Label         = "Inflated STAT",
                    QueuePriority = 3,
                    SpawnWeight   = 0.80f,
                    TypicalExams  = new[] { "head", "abdpel", "chest", "spine", "cta_chest", "extremity" },
                    WaitThreshold = 25 * 60,
                    PenaltyMult   = 1.5f,
                    CanDowngrade  = false,
                }
            },
            {
                4, new AcuityEntry
                {
                    Label         = "Routine",
                    QueuePriority = 4,
                    SpawnWeight   = 0.15f,
                    TypicalExams  = new[] { "abdpel", "chest", "spine", "extremity", "head" },
                    WaitThreshold = 30 * 60,
                    PenaltyMult   = 0.5f,
                    CanDowngrade  = false,
                }
            },
        };
    }
}
