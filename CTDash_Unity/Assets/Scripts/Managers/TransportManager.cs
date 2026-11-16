// TransportManager — handles all patient movement delays.
// Runs the Transport state machine for each active patient.

using System.Collections.Generic;

namespace CTDash
{
    public class TransportManager
    {
        private readonly Dictionary<string, Patient> _active = new Dictionary<string, Patient>();

        public void AssignTransport(Patient patient)
        {
            var t         = patient.Transport;
            t.State       = TransportState.WaitingAssignment;
            t.Timer       = t.ArrivalDelay;
            patient.State = PatientState.InTransport;
            _active[patient.PatientId] = patient;
        }

        public void Tick()
        {
            var delivered = new List<string>();

            foreach (var kvp in _active)
            {
                var patient = kvp.Value;
                var t       = patient.Transport;
                t.Timer    -= 1;

                if (t.Timer > 0) continue;

                switch (t.State)
                {
                    case TransportState.WaitingAssignment:
                        t.State = TransportState.Acknowledged;
                        t.Timer = t.HoldWait;
                        break;

                    case TransportState.Acknowledged:
                        t.State = TransportState.OnWay;
                        t.Timer = 0;
                        break;

                    case TransportState.OnWay:
                        t.State = TransportState.Delivered;
                        if (patient.State == PatientState.Leaving)
                            patient.State = PatientState.Completed;
                        else
                            patient.State = PatientState.InHolding;
                        delivered.Add(kvp.Key);
                        break;
                }
            }

            foreach (var pid in delivered)
                _active.Remove(pid);
        }

        public void BeginLeaving(Patient patient)
        {
            var t         = patient.Transport;
            t.State       = TransportState.OnWay;
            t.Timer       = t.LeavingDelay;
            patient.State = PatientState.Leaving;
            _active[patient.PatientId] = patient;
        }
    }
}
