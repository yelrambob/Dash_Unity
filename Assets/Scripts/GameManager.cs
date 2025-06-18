public class GameManager : MonoBehaviour
{
    public List<Patient> OrderedPatients;
    public HoldingBay MainHoldingBay;
    public HoldingBay ERHoldingBay; // for CT3
    public List<CTScanner> Scanners;
    public float GameTimer;
    public int ExamsCompleted;
    public int Score;
    // Methods for patient spawning, assignment, scoring, state transitions
}
