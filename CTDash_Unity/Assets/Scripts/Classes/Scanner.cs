// Scanner — represents one CT machine.
//
// States:
//   Idle     — available, no patient
//   Scanning — patient actively being scanned
//   Cooldown — post-scan reset period
//   Locked   — no tech assigned, cannot accept patients

namespace CTDash
{
    public enum ScannerState
    {
        Idle,
        Scanning,
        Cooldown,
        Locked,
    }

    public class Scanner
    {
        public string       ScannerId;
        public string       Zone;               // "ED" or "Main"
        public ScannerState State      = ScannerState.Idle;
        public string       CurrentPatient;     // PatientId or null
        public string       AssignedTech;       // TechId or null
        public int          ScanTimer     = 0;
        public int          CooldownTimer = 0;

        public bool IsAvailable =>
            State == ScannerState.Idle && AssignedTech != null;

        public Scanner(string scannerId, string zone, ScannerState initialState = ScannerState.Idle)
        {
            ScannerId = scannerId;
            Zone      = zone;
            State     = initialState;
        }
    }
}
