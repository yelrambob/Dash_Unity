# [BUILD FIRST]
# Every exam type available in the game.
# Add new exam types here without touching any other file.
#
# Each entry is a dict — will be used to construct Exam objects in exam.py.
# Keys:
#   scan_time         — base scan duration in game-seconds (tuned in config.py)
#   iv_contrast       — bool, does this exam require IV contrast?
#   oral_contrast     — bool, does this exam require oral contrast (wait timer)?
#   difficulty        — float 1.0–3.0, affects tech accuracy penalty

from classes.exam import Exam

EXAM_CATALOG = {
    "head": Exam(
        name="head",
        scan_time=60,
        iv_contrast=False,
        oral_contrast=False,
        difficulty=1.0,
    ),
    "abdpel": Exam(
        name="abdpel",
        scan_time=90,
        iv_contrast=True,
        oral_contrast=True,
        difficulty=1.5,
    ),
    "trauma_full": Exam(
        name="trauma_full",
        scan_time=120,
        iv_contrast=True,
        oral_contrast=False,
        difficulty=2.5,
    ),
    # TODO: add chest, cta_head, cta_chest, spine, extremity, etc.
}
