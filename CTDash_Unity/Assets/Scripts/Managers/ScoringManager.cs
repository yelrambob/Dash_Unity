// ScoringManager — tracks all score components in real time.
//
// Components:
//   ExamsCompleted   — positive score
//   WaitPenalties    — per-patient, per-minute over threshold
//   OverflowPenalty  — flat hit per overflow patient (one-time)
//   HoldoverPenalty  — flat hit per patient still in system at shift end

using System.Collections.Generic;

namespace CTDash
{
    public class ScoringManager
    {
        public int Score          = 0;
        public int ExamsCompleted = 0;
        public int Holdovers      = 0;

        public void ExamCompleted()
        {
            ExamsCompleted++;
            Score += GameConfig.EXAM_BASE_SCORE;
        }

        public void ApplyWaitPenalty(int acuity, int excessSeconds)
        {
            float penaltyMult   = AcuityData.Table[acuity].PenaltyMult;
            float excessMinutes = excessSeconds / 60.0f;
            int   penalty       = (int)(excessMinutes * GameConfig.WAIT_PENALTY_PER_MINUTE * penaltyMult);
            Score -= penalty;
        }

        public void ApplyOverflowPenalty()
        {
            Score -= GameConfig.OVERFLOW_PENALTY;
        }

        public int Finalise(List<Patient> remainingPatients)
        {
            Holdovers  = remainingPatients.Count;
            Score     -= Holdovers * GameConfig.HOLDOVER_PENALTY;
            return Score;
        }
    }
}
