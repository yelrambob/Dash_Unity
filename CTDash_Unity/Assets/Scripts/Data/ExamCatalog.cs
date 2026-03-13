// ExamCatalog — every exam type available in the game.
// Add new exam types here without touching any other file.
// Scan times pull from GameConfig.SCAN_TIMES to stay in sync.

using System.Collections.Generic;

namespace CTDash
{
    public static class ExamCatalog
    {
        public static readonly Dictionary<string, Exam> Catalog = new Dictionary<string, Exam>
        {
            {
                "head", new Exam(
                    name:         "head",
                    scanTime:     GameConfig.SCAN_TIMES["head"],
                    ivContrast:   false,
                    oralContrast: false,
                    difficulty:   1.0f)
            },
            {
                "chest", new Exam(
                    name:         "chest",
                    scanTime:     GameConfig.SCAN_TIMES["chest"],
                    ivContrast:   false,
                    oralContrast: false,
                    difficulty:   1.0f)
            },
            {
                "spine", new Exam(
                    name:         "spine",
                    scanTime:     GameConfig.SCAN_TIMES["spine"],
                    ivContrast:   false,
                    oralContrast: false,
                    difficulty:   1.2f)
            },
            {
                "cta_chest", new Exam(
                    name:         "cta_chest",
                    scanTime:     GameConfig.SCAN_TIMES["cta_chest"],
                    ivContrast:   true,
                    oralContrast: false,
                    difficulty:   1.5f)
            },
            {
                "extremity", new Exam(
                    name:         "extremity",
                    scanTime:     GameConfig.SCAN_TIMES["extremity"],
                    ivContrast:   false,
                    oralContrast: false,
                    difficulty:   1.2f)
            },
            {
                "cta_head", new Exam(
                    name:         "cta_head",
                    scanTime:     GameConfig.SCAN_TIMES["cta_head"],
                    ivContrast:   true,
                    oralContrast: false,
                    difficulty:   2.0f)
            },
            {
                "abdpel", new Exam(
                    name:         "abdpel",
                    scanTime:     GameConfig.SCAN_TIMES["abdpel"],
                    ivContrast:   true,
                    oralContrast: true,
                    difficulty:   1.5f)
            },
            {
                "trauma_full", new Exam(
                    name:         "trauma_full",
                    scanTime:     GameConfig.SCAN_TIMES["trauma_full"],
                    ivContrast:   true,
                    oralContrast: false,   // trauma bypasses oral contrast wait
                    difficulty:   2.5f)
            },
        };
    }
}
