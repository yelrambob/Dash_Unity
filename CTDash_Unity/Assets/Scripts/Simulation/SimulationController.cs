// SimulationController — MonoBehaviour that drives the GameLoop from Unity.
// Attach to a single GameObject in your scene (e.g. "GameManager").
// Converts real-time into compressed game-time using TIME_SCALE.
//
// Public fields can be set in the Inspector.

using System.Collections.Generic;
using UnityEngine;

namespace CTDash
{
    public class SimulationController : MonoBehaviour
    {
        [Header("Level")]
        public int Level = 1;

        // Accumulated real-time seconds not yet consumed as game-ticks.
        private float    _tickAccumulator;
        private GameLoop _loop;
        private bool     _running;

        // Read-only access for UI scripts.
        public GameLoop Loop     => _loop;
        public bool     IsRunning => _running;

        private void Start()
        {
            InitLevel(Level);
        }

        private void Update()
        {
            if (!_running || _loop.Timer.IsShiftOver) return;

            // Convert real seconds to game-seconds using TIME_SCALE.
            _tickAccumulator += Time.deltaTime * GameConfig.TIME_SCALE;

            while (_tickAccumulator >= 1f && !_loop.Timer.IsShiftOver)
            {
                _loop.Tick();
                _tickAccumulator -= 1f;
            }

            if (_loop.Timer.IsShiftOver)
                EndShift();
        }

        private void InitLevel(int level)
        {
            if (!GameConfig.LEVELS.TryGetValue(level, out var cfg))
            {
                Debug.LogError($"[SimulationController] Unknown level {level}");
                return;
            }

            // Build scanners — all start Locked until staffing assigns techs.
            var scanners = new List<Scanner>();
            for (int i = 0; i < cfg.Scanners; i++)
            {
                string zone = (i == 0) ? "ED" : "Main";
                scanners.Add(new Scanner(
                    scannerId:    $"SCANNER_{zone}_{i + 1}",
                    zone:         zone,
                    initialState: ScannerState.Locked));
            }

            var queueMgr    = new QueueManager();
            var scannerMgr  = new ScannerManager(scanners);
            var transportMgr = new TransportManager();
            var contrastMgr = new ContrastManager();
            var scoringMgr  = new ScoringManager();
            var spawnMgr    = new SpawnManager(queueMgr);
            var staffingMgr = new StaffingManager(scannerMgr);

            int durationHours = cfg.ShiftEndHour - cfg.ShiftStartHour;

            _loop = new GameLoop(
                spawnMgr, queueMgr, transportMgr, contrastMgr,
                scannerMgr, scoringMgr, staffingMgr,
                ExamCatalog.Catalog,
                durationHours);

            _tickAccumulator = 0f;
            _running         = true;

            Debug.Log($"[SimulationController] Level {level} started — " +
                      $"{cfg.Scanners} scanners, shift {cfg.ShiftStartHour}:00–{cfg.ShiftEndHour}:00");
        }

        private void EndShift()
        {
            _running = false;
            int finalScore = _loop.EndShift();
            Debug.Log($"[SimulationController] Shift over — " +
                      $"Exams: {_loop.ScoringMgr.ExamsCompleted}, " +
                      $"Holdovers: {_loop.ScoringMgr.Holdovers}, " +
                      $"Score: {finalScore}");
        }
    }
}
