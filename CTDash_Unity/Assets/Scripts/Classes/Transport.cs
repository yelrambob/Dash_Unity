// Transport — handles patient movement delays.
//
// State machine:
//   WaitingAssignment — order placed, no transporter yet
//   Acknowledged      — transporter accepted the job
//   OnWay             — transporter en route to patient
//   Delivered         — patient arrived at holding bay

namespace CTDash
{
    public enum TransportState
    {
        WaitingAssignment,
        Acknowledged,
        OnWay,
        Delivered,
    }

    public class Transport
    {
        public TransportState State = TransportState.WaitingAssignment;

        // Delay timers (in game-seconds) — set randomly within config ranges on spawn
        public int ArrivalDelay;    // time until transporter arrives at patient
        public int HoldWait;        // extra wait at pick-up before moving
        public int LeavingDelay;    // time after scan before transporter picks up

        public int Timer;           // counts down current active delay
    }
}
