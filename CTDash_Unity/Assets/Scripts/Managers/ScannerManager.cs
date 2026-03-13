// ScannerManager — controls scanner assignment and scan lifecycle.
// Zone preference: acuity-1 patients go to ED scanner first.
// Manages multi-exam sequences (patient stays until all exams done).
// Tracks scan timer and cooldown timer per scanner.

using System.Collections.Generic;

namespace CTDash
{
    public class ScannerManager
    {
        public  readonly Dictionary<string, Scanner>  Scanners;
        private readonly Dictionary<string, Tech>     _techs;
        private readonly Dictionary<string, Patient>  _scanningPatients = new Dictionary<string, Patient>();
        public           List<Patient>                CompletedPatients = new List<Patient>();

        public ScannerManager(List<Scanner> scanners, Dictionary<string, Tech> techs = null)
        {
            Scanners = new Dictionary<string, Scanner>();
            foreach (var s in scanners) Scanners[s.ScannerId] = s;
            _techs = techs ?? new Dictionary<string, Tech>();
        }

        public bool TryAssign(Patient patient, Dictionary<string, Exam> catalog)
        {
            bool preferEd = patient.Acuity == 1;

            var candidates = new List<Scanner>(Scanners.Values);
            if (preferEd)
                candidates.Sort((a, b) =>
                    (a.Zone == "ED" ? 0 : 1).CompareTo(b.Zone == "ED" ? 0 : 1));

            foreach (var scanner in candidates)
            {
                if (!scanner.IsAvailable) continue;

                string examKey = patient.ExamList[patient.CurrentExamIndex];

                scanner.State          = ScannerState.Scanning;
                scanner.CurrentPatient = patient.PatientId;
                scanner.ScanTimer      = CalcScanTime(examKey, scanner.AssignedTech);
                scanner.CooldownTimer  = 0;

                patient.State = PatientState.Scanning;
                _scanningPatients[scanner.ScannerId] = patient;
                return true;
            }
            return false;
        }

        public void Tick(Dictionary<string, Exam> catalog)
        {
            foreach (var kvp in Scanners)
            {
                var scanner = kvp.Value;
                var sid     = kvp.Key;

                if (scanner.State == ScannerState.Scanning)
                {
                    scanner.ScanTimer -= 1;
                    if (scanner.ScanTimer <= 0)
                    {
                        scanner.State         = ScannerState.Cooldown;
                        scanner.CooldownTimer = GameConfig.SCANNER_COOLDOWN;
                        if (_scanningPatients.TryGetValue(sid, out var p))
                            p.State = PatientState.Cooldown;
                    }
                }
                else if (scanner.State == ScannerState.Cooldown)
                {
                    scanner.CooldownTimer -= 1;
                    if (scanner.CooldownTimer <= 0)
                    {
                        _scanningPatients.TryGetValue(sid, out var patient);
                        _scanningPatients.Remove(sid);
                        scanner.CurrentPatient = null;

                        if (patient != null)
                        {
                            patient.CurrentExamIndex++;
                            if (patient.CurrentExamIndex < patient.ExamList.Count)
                            {
                                // More exams — re-assign to same scanner immediately.
                                string nextKey    = patient.ExamList[patient.CurrentExamIndex];
                                scanner.ScanTimer = CalcScanTime(nextKey, scanner.AssignedTech);
                                scanner.State     = ScannerState.Scanning;
                                patient.State     = PatientState.Scanning;
                                _scanningPatients[sid] = patient;
                            }
                            else
                            {
                                // All exams done — queue for departure.
                                scanner.State = ScannerState.Idle;
                                CompletedPatients.Add(patient);
                            }
                        }
                        else
                        {
                            scanner.State = ScannerState.Idle;
                        }
                    }
                }
            }
        }

        private int CalcScanTime(string examKey, string techId)
        {
            int baseTime = GameConfig.SCAN_TIMES[examKey];
            if (GameConfig.USE_TECH_SPEED_MODIFIER && techId != null
                && _techs.TryGetValue(techId, out var tech))
            {
                return System.Math.Max(1, (int)(baseTime * (1.0f + (1.0f - tech.Speed) * 0.5f)));
            }
            return baseTime;
        }
    }
}
