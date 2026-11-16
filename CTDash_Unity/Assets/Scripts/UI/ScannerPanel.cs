// ScannerPanel — displays live status of each scanner.
// One ScannerPanel instance per scanner in the scene.
// Assign ScannerId in the Inspector to bind to the correct scanner.

using UnityEngine;
using UnityEngine.UI;

namespace CTDash
{
    public class ScannerPanel : MonoBehaviour
    {
        [Header("References")]
        public SimulationController Simulation;
        public string               ScannerId;   // set in Inspector

        [Header("UI Elements")]
        public Text  StatusText;     // e.g. "SCANNING", "IDLE", "LOCKED"
        public Text  PatientText;    // e.g. "PAT_0012  abdpel"
        public Text  TimerText;      // e.g. "00:32 remaining"
        public Image StatusLight;    // coloured indicator

        [Header("Status Colours")]
        public Color IdleColour     = Color.green;
        public Color ScanningColour = Color.cyan;
        public Color CooldownColour = Color.yellow;
        public Color LockedColour   = Color.red;

        private void Update()
        {
            if (Simulation?.Loop == null) return;
            if (!Simulation.Loop.ScannerMgr.Scanners.TryGetValue(ScannerId, out var scanner)) return;

            if (StatusText)
                StatusText.text = scanner.State.ToString().ToUpper();

            if (PatientText)
                PatientText.text = scanner.CurrentPatient ?? "—";

            if (TimerText)
            {
                int t = scanner.State == ScannerState.Scanning ? scanner.ScanTimer : scanner.CooldownTimer;
                TimerText.text = t > 0 ? $"{t}s" : "";
            }

            if (StatusLight)
                StatusLight.color = scanner.State switch
                {
                    ScannerState.Idle     => IdleColour,
                    ScannerState.Scanning => ScanningColour,
                    ScannerState.Cooldown => CooldownColour,
                    ScannerState.Locked   => LockedColour,
                    _                     => Color.white,
                };
        }
    }
}
