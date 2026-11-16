// Exam — represents a single scan type.
// No logic here; just holds data about what an exam IS.

namespace CTDash
{
    public class Exam
    {
        public string Name;          // short key matching ExamCatalog
        public int    ScanTime;      // base duration in game-seconds
        public bool   IvContrast;    // requires IV contrast injection
        public bool   OralContrast;  // requires oral contrast wait timer
        public float  Difficulty;    // 1.0–3.0, affects tech accuracy penalty

        public Exam(string name, int scanTime, bool ivContrast, bool oralContrast, float difficulty)
        {
            Name         = name;
            ScanTime     = scanTime;
            IvContrast   = ivContrast;
            OralContrast = oralContrast;
            Difficulty   = difficulty;
        }
    }
}
