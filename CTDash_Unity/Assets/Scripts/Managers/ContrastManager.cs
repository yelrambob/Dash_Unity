// ContrastManager — tracks oral contrast timers and injector fill status.
// Fires ContrastReady state change when oral contrast timer completes.

using System.Collections.Generic;

namespace CTDash
{
    public class ContrastManager
    {
        private readonly Dictionary<string, Patient> _oralPatients  = new Dictionary<string, Patient>();
        private readonly HashSet<string>             _injectorReady = new HashSet<string>();

        public void StartOralContrast(Patient patient)
        {
            patient.ContrastTimer = GameConfig.ORAL_CONTRAST_WAIT;
            patient.State         = PatientState.ContrastOrdered;
            _oralPatients[patient.PatientId] = patient;
        }

        public void FillInjector(Patient patient)
        {
            _injectorReady.Add(patient.PatientId);
            patient.State = PatientState.InjectorReady;
        }

        public bool IsInjectorReady(string patientId) => _injectorReady.Contains(patientId);

        public void Tick()
        {
            var ready = new List<string>();
            foreach (var kvp in _oralPatients)
            {
                kvp.Value.ContrastTimer -= 1;
                if (kvp.Value.ContrastTimer <= 0)
                {
                    kvp.Value.ContrastTimer = 0;
                    kvp.Value.State         = PatientState.ContrastReady;
                    ready.Add(kvp.Key);
                }
            }
            foreach (var pid in ready)
                _oralPatients.Remove(pid);
        }
    }
}
