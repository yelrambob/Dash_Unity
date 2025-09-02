public class Patient
{
    public string Name;
    public int Age;
    public string Gender;
    public string Urgency; // STAT or Routine
    public List<ExamBundle> Exams;
    public float ReadyInSeconds; // cooldown before entering holding bay
    public float HoldingBayTimer;
    public float ScanTimer;
    public float PostScanCooldown;
    // Methods to randomize demographics and assign exams
}

