# [BUILD FIRST]
# Every exam type available in the game.
# Add new exam types here without touching any other file.
#
# Scan times here must match SCAN_TIMES in config.py — keep them in sync.
# iv_contrast: requires injector fill before scan can start.
# oral_contrast: triggers a timed wait (ORAL_CONTRAST_WAIT in config.py).
# difficulty: 1.0–3.0, affects tech accuracy penalty (used later by staffing system).
#
# Possible change: pull scan_time directly from config.SCAN_TIMES at runtime
# instead of hardcoding here, to avoid having to update two places.

from classes.exam import Exam
from config import SCAN_TIMES

EXAM_CATALOG = {
    "head": Exam(
        name="head",
        scan_time=SCAN_TIMES["head"],   # 20s — simple, no contrast
        iv_contrast=False,
        oral_contrast=False,
        difficulty=1.0,
    ),
    "chest": Exam(
        name="chest",
        scan_time=SCAN_TIMES["chest"],  # 25s — quick, common
        iv_contrast=False,
        oral_contrast=False,
        difficulty=1.0,
    ),
    "spine": Exam(
        name="spine",
        scan_time=SCAN_TIMES["spine"],  # 30s — no contrast typically
        iv_contrast=False,
        oral_contrast=False,
        difficulty=1.2,
    ),
    "cta_chest": Exam(
        name="cta_chest",
        scan_time=SCAN_TIMES["cta_chest"],  # 35s — IV contrast required
        iv_contrast=True,
        oral_contrast=False,
        difficulty=1.5,
    ),
    "extremity": Exam(
        name="extremity",
        scan_time=SCAN_TIMES["extremity"],  # 35s — no contrast, positioning adds time
        iv_contrast=False,
        oral_contrast=False,
        difficulty=1.2,
    ),
    "cta_head": Exam(
        name="cta_head",
        scan_time=SCAN_TIMES["cta_head"],   # 45s — IV contrast, time sensitive
        iv_contrast=True,
        oral_contrast=False,
        difficulty=2.0,
    ),
    "abdpel": Exam(
        name="abdpel",
        scan_time=SCAN_TIMES["abdpel"],     # 50s — bread and butter, often oral contrast
        iv_contrast=True,
        oral_contrast=True,
        difficulty=1.5,
    ),
    "trauma_full": Exam(
        name="trauma_full",
        scan_time=SCAN_TIMES["trauma_full"], # 70s — longest exam, highest stakes
        iv_contrast=True,
        oral_contrast=False,                 # trauma bypasses oral contrast wait
        difficulty=2.5,
    ),
    # TODO: add cta_abdpel, myelogram, angio, pediatric variants
}