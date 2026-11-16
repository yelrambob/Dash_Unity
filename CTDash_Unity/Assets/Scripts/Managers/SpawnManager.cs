// SpawnManager — controls when and what patients appear.
// Reads HourlySpawnTable for timing and acuity bias.
// Assigns acuity, mobility type, and exam list on spawn.
// Adds new Patient objects to the QueueManager.

using System;
using System.Collections.Generic;

namespace CTDash
{
    public class SpawnManager
    {
        private readonly QueueManager _queueManager;
        private readonly Random       _rng = new Random();
        private          int          _patientCounter = 0;

        private static readonly string[] MobilityTypes = { "ambulatory", "wheelchair", "stretcher" };
        private static readonly int[]    HighTiers = { 1, 2 };
        private static readonly int[]    LowTiers  = { 3, 4 };

        public SpawnManager(QueueManager queueManager)
        {
            _queueManager = queueManager;
        }

        public void Tick(int gameHour, int gameSecond)
        {
            if (!HourlySpawnTable.Table.TryGetValue(gameHour, out var row))
                row = HourlySpawnTable.Table[0];

            double prob = row.ExamsPerHour / 3600.0;
            if (_rng.NextDouble() < prob)
                SpawnPatient(gameHour, gameSecond, row);
        }

        private void SpawnPatient(int gameHour, int gameSecond, SpawnHourEntry row)
        {
            // Pick acuity tier
            int[] pool   = (_rng.NextDouble() < row.AcuityBias) ? HighTiers : LowTiers;
            float total  = 0f;
            foreach (int t in pool) total += AcuityData.Table[t].SpawnWeight;

            double roll = _rng.NextDouble() * total;
            int acuity  = pool[pool.Length - 1];
            float acc   = 0f;
            foreach (int t in pool)
            {
                acc += AcuityData.Table[t].SpawnWeight;
                if (roll <= acc) { acuity = t; break; }
            }

            var tier    = AcuityData.Table[acuity];
            string exam = tier.TypicalExams[_rng.Next(tier.TypicalExams.Length)];
            string mob  = MobilityTypes[_rng.Next(MobilityTypes.Length)];

            int arrivalDelay  = _rng.Next(GameConfig.TRANSPORT_ARRIVAL_DELAY.Min,  GameConfig.TRANSPORT_ARRIVAL_DELAY.Max  + 1);
            int holdWait      = _rng.Next(GameConfig.TRANSPORT_HOLD_WAIT.Min,      GameConfig.TRANSPORT_HOLD_WAIT.Max      + 1);
            int leavingDelay  = _rng.Next(GameConfig.TRANSPORT_LEAVING_DELAY.Min,  GameConfig.TRANSPORT_LEAVING_DELAY.Max  + 1);

            var transport = new Transport
            {
                State        = TransportState.WaitingAssignment,
                ArrivalDelay = arrivalDelay,
                HoldWait     = holdWait,
                LeavingDelay = leavingDelay,
                Timer        = arrivalDelay,
            };

            var patient = new Patient(
                patientId:    NextPatientId(),
                acuity:       acuity,
                personability: (float)Math.Round(_rng.NextDouble(), 2),
                mobility:     mob,
                examList:     new List<string> { exam },
                transport:    transport
            );

            _queueManager.AddPatient(patient, gameSecond);
        }

        private string NextPatientId()
        {
            _patientCounter++;
            return $"PAT_{_patientCounter:D4}";
        }
    }
}
