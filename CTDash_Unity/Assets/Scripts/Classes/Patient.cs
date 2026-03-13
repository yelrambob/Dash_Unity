// Patient — the core game object.
//
// Full state machine:
//   Ordered > InTransport > InHolding >
//   ContrastOrdered > ContrastReady >
//   InjectorReady > Scanning > Cooldown >
//   Leaving > Completed | Refused | Holdover

using System.Collections.Generic;

namespace CTDash
{
    public enum PatientState
    {
        Ordered,
        InTransport,
        InHolding,
        ContrastOrdered,
        ContrastReady,
        InjectorReady,
        Scanning,
        Cooldown,
        Leaving,
        Completed,
        Refused,
        Holdover,
    }

    public class Patient
    {
        public string       PatientId;
        public int          Acuity;             // 1–4
        public float        Personability;      // 0.0–1.0, affects refusal risk
        public string       Mobility;           // "ambulatory", "wheelchair", "stretcher"
        public List<string> ExamList;           // ordered list of exam keys
        public Transport    Transport;

        public PatientState State              = PatientState.Ordered;
        public int          WaitTimer          = 0;    // total game-seconds spent waiting
        public int          ContrastTimer      = 0;    // counts down oral contrast wait
        public int          CurrentExamIndex   = 0;    // index into ExamList for multi-exam

        public Patient(string patientId, int acuity, float personability, string mobility,
                       List<string> examList, Transport transport)
        {
            PatientId    = patientId;
            Acuity       = acuity;
            Personability = personability;
            Mobility     = mobility;
            ExamList     = examList;
            Transport    = transport;
        }
    }
}
