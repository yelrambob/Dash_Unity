// GameLoop — the main simulation tick.
// Each tick advances all timers by one game-second (GameConfig.TICK_SECONDS).
// Managers are called in a fixed order each tick — order matters.
//
// Tick order:
//   1. ShiftTimer     — advance clock, check for hourly events
//   2. SpawnManager   — maybe spawn a new patient
//   3. TransportManager — advance transport state machines
//   4. QueueManager   — advance wait timers
//   5. ContrastManager — advance contrast timers
//   6. ScannerManager — advance scan/cooldown timers
//   7. Scoring        — check for penalties, update score

using System.Collections.Generic;

namespace CTDash
{
    public class GameLoop
    {
        public readonly ShiftTimer       Timer;
        public readonly SpawnManager     SpawnMgr;
        public readonly QueueManager     QueueMgr;
        public readonly TransportManager TransportMgr;
        public readonly ContrastManager  ContrastMgr;
        public readonly ScannerManager   ScannerMgr;
        public readonly ScoringManager   ScoringMgr;
        public readonly StaffingManager  StaffingMgr;

        // Master patient registry.
        private readonly Dictionary<string, Patient> _patients        = new Dictionary<string, Patient>();
        private readonly HashSet<string>             _overflowCharged = new HashSet<string>();

        private readonly Dictionary<string, Exam> _examCatalog;

        public GameLoop(
            SpawnManager    spawnMgr,
            QueueManager    queueMgr,
            TransportManager transportMgr,
            ContrastManager contrastMgr,
            ScannerManager  scannerMgr,
            ScoringManager  scoringMgr,
            StaffingManager staffingMgr,
            Dictionary<string, Exam> examCatalog,
            int durationHours = GameConfig.GAME_DURATION_HOURS)
        {
            SpawnMgr     = spawnMgr;
            QueueMgr     = queueMgr;
            TransportMgr = transportMgr;
            ContrastMgr  = contrastMgr;
            ScannerMgr   = scannerMgr;
            ScoringMgr   = scoringMgr;
            StaffingMgr  = staffingMgr;
            _examCatalog = examCatalog;
            Timer        = new ShiftTimer(durationHours);
        }

        // Call once per Unity Update (or FixedUpdate) to advance one game-tick.
        public void Tick()
        {
            if (Timer.IsShiftOver) return;

            // 1. Advance clock.
            bool newHour = Timer.Tick();
            int  gs      = Timer.GameSecond;
            int  gh      = Timer.GameHour;

            // 2. Spawn.
            SpawnMgr.Tick(gh, gs);

            // Sync newly spawned patients into master registry and start transport.
            foreach (var kvp in QueueMgr.Patients)
            {
                if (!_patients.ContainsKey(kvp.Key))
                {
                    _patients[kvp.Key] = kvp.Value;
                    TransportMgr.AssignTransport(kvp.Value);
                }
            }

            // 3. Transport.
            TransportMgr.Tick();

            // 4. Queue wait timers.
            QueueMgr.Tick();

            // 5. Contrast timers.
            ContrastMgr.Tick();

            // 6. Order oral contrast for newly arrived patients that need it.
            OrderContrastIfNeeded();

            // 7. Scanner timers.
            ScannerMgr.Tick(_examCatalog);

            // 8. Process patients whose entire exam list is finished.
            HandleCompletedScans();

            // 9. Assign highest-priority ready patients to idle scanners.
            TryAssignToScanners();

            // 10. Wait penalties.
            ApplyWaitPenalties();

            // 11. Overflow check.
            CheckOverflow();

            // 12. Staffing — fires only on new game-hour boundary.
            if (newHour)
                StaffingMgr.Tick((float)gh);
        }

        public int EndShift()
        {
            var remaining = new List<Patient>();
            foreach (var p in _patients.Values)
            {
                if (p.State != PatientState.Completed && p.State != PatientState.Refused)
                    remaining.Add(p);
            }
            return ScoringMgr.Finalise(remaining);
        }

        // --- Helpers -------------------------------------------------------

        private void OrderContrastIfNeeded()
        {
            foreach (var patient in _patients.Values)
            {
                if (patient.State != PatientState.InHolding) continue;
                if (patient.CurrentExamIndex >= patient.ExamList.Count) continue;

                string examKey = patient.ExamList[patient.CurrentExamIndex];
                if (_examCatalog[examKey].OralContrast)
                    ContrastMgr.StartOralContrast(patient);
            }
        }

        private void TryAssignToScanners()
        {
            var ready = new List<Patient>();
            foreach (var p in _patients.Values)
            {
                bool isReady = p.State == PatientState.InHolding
                            || p.State == PatientState.ContrastReady
                            || p.State == PatientState.InjectorReady;

                if (isReady && p.CurrentExamIndex < p.ExamList.Count)
                    ready.Add(p);
            }

            // Highest priority first (lowest acuity number, then longest wait).
            ready.Sort((a, b) =>
            {
                if (a.Acuity != b.Acuity) return a.Acuity.CompareTo(b.Acuity);
                return b.WaitTimer.CompareTo(a.WaitTimer);
            });

            foreach (var patient in ready)
            {
                string examKey = patient.ExamList[patient.CurrentExamIndex];
                var    exam    = _examCatalog[examKey];

                // Fill injector if IV contrast needed and contrast is ready.
                if (patient.State == PatientState.ContrastReady && exam.IvContrast)
                {
                    ContrastMgr.FillInjector(patient);
                    continue;
                }

                bool assigned = ScannerMgr.TryAssign(patient, _examCatalog);
                if (assigned)
                    QueueMgr.Patients.Remove(patient.PatientId);
            }
        }

        private void HandleCompletedScans()
        {
            foreach (var patient in ScannerMgr.CompletedPatients)
            {
                ScoringMgr.ExamCompleted();
                TransportMgr.BeginLeaving(patient);
            }
            ScannerMgr.CompletedPatients.Clear();
        }

        private void ApplyWaitPenalties()
        {
            foreach (var patient in _patients.Values)
            {
                if (patient.State == PatientState.Completed  ||
                    patient.State == PatientState.Refused    ||
                    patient.State == PatientState.Scanning   ||
                    patient.State == PatientState.Cooldown   ||
                    patient.State == PatientState.Leaving) continue;

                int threshold = AcuityData.Table[patient.Acuity].WaitThreshold;
                int excess    = patient.WaitTimer - threshold;
                if (excess > 0 && excess % 60 == 0)
                    ScoringMgr.ApplyWaitPenalty(patient.Acuity, 60);
            }
        }

        private void CheckOverflow()
        {
            var inHolding = new List<Patient>();
            foreach (var p in _patients.Values)
                if (p.State == PatientState.InHolding) inHolding.Add(p);

            inHolding.Sort((a, b) =>
            {
                if (a.Acuity != b.Acuity) return a.Acuity.CompareTo(b.Acuity);
                return b.WaitTimer.CompareTo(a.WaitTimer);
            });

            for (int i = 0; i < inHolding.Count; i++)
            {
                if (i >= GameConfig.HOLDING_PROPER_SLOTS)
                {
                    if (_overflowCharged.Add(inHolding[i].PatientId))
                        ScoringMgr.ApplyOverflowPenalty();
                }
            }
        }
    }
}
