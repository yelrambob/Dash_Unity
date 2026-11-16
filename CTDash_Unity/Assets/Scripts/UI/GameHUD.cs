// GameHUD — reads from SimulationController and drives the on-screen display.
// Attach to a Canvas GameObject. Assign references in the Inspector.
//
// Placeholder: UI element references are stubbed — hook up real Text/TMP
// components once the scene is built.

using UnityEngine;
using UnityEngine.UI;

namespace CTDash
{
    public class GameHUD : MonoBehaviour
    {
        [Header("References")]
        public SimulationController Simulation;

        [Header("UI Elements (assign in Inspector)")]
        public Text ClockText;     // current game time e.g. "09:42"
        public Text ScoreText;     // running score
        public Text ExamCountText; // exams completed this shift
        public Text QueueText;     // patients waiting in queue
        public Text HoldingText;   // patients in holding bay

        private void Update()
        {
            if (Simulation == null || Simulation.Loop == null) return;
            var loop = Simulation.Loop;

            if (ClockText)     ClockText.text     = loop.Timer.TimeString;
            if (ScoreText)     ScoreText.text      = $"Score: {loop.ScoringMgr.Score}";
            if (ExamCountText) ExamCountText.text  = $"Exams: {loop.ScoringMgr.ExamsCompleted}";
            if (QueueText)     QueueText.text      = $"Queue: {loop.QueueMgr.Patients.Count}";
        }
    }
}
