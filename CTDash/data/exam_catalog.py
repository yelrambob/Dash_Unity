# Exam catalog — every scan type available in the game.
#
# Derived from 6 months / 45,297 real exams. Similar studies consolidated:
#   - All extremity types (ankle/wrist/knee/hip/etc) → "extremity"
#   - Chest w + chest wo kept separate (contrast workflow differs)
#   - abdpel w/wo kept separate (oral contrast is a major pacing difference)
#   - Arteriogram head + neck combined → "arteriogram" (same IV workflow)
#   - All cardiac CTA variants → "cardiac_cta"
#   - Trauma is a package (3 exams) defined in acuity_table.py
#
# scan_time: scanner acquisition only. Contrast wait timers are SEPARATE —
#   see ORAL_CONTRAST_WAIT and INJECTOR_FILL_TIME in config.py.
#
# volume: real 6-month count. SpawnManager uses this to weight the pool.
#   Do not fake these — they determine how often each exam appears in game.
#
# min_level: when this exam first enters the spawn pool.
#   Level 1 = tutorial basics (no contrast, fast turnaround)
#   Level 2 = more variety, still no IV contrast
#   Level 3 = oral and IV contrast mechanics unlocked
#   Level 4 = complex long studies, vascular protocols
#   Level 5 = full shift including emergencies and trauma

from classes.exam import Exam
from config import SCAN_TIMES

EXAM_CATALOG = {

    # -----------------------------------------------------------------------
    # LEVEL 1 — core, no contrast, fast. Player learns queue and transport.
    # -----------------------------------------------------------------------

    "head_wo": Exam(
        name="head_wo",
        scan_time=SCAN_TIMES["head"],           # 20s — instant feel
        iv_contrast=False,
        oral_contrast=False,
        difficulty=1.0,
        volume=10_915,                          # CT head wo contrast (dominant exam)
        min_level=1,
    ),

    "c_spine": Exam(
        name="c_spine",
        scan_time=SCAN_TIMES["spine"],          # 30s
        iv_contrast=False,
        oral_contrast=False,
        difficulty=1.2,
        volume=3_783,                           # CT cervical spine w + wo
        min_level=1,
    ),

    "chest_wo": Exam(
        name="chest_wo",
        scan_time=SCAN_TIMES["chest"],          # 25s
        iv_contrast=False,
        oral_contrast=False,
        difficulty=1.0,
        volume=1_552,
        min_level=1,
    ),

    "chest_w": Exam(
        name="chest_w",
        scan_time=SCAN_TIMES["chest"],          # 25s — same acq time, IV adds injector wait
        iv_contrast=True,
        oral_contrast=False,
        difficulty=1.0,
        volume=1_647,
        min_level=1,
    ),

    "extremity": Exam(
        name="extremity",
        scan_time=SCAN_TIMES["extremity"],      # 35s — positioning overhead included
        iv_contrast=False,
        oral_contrast=False,
        difficulty=1.0,
        volume=853,                             # ankle/wrist/knee/hip/shoulder/hand/foot/etc
        min_level=1,
    ),

    # -----------------------------------------------------------------------
    # LEVEL 2 — more variety, still no contrast pressure
    # -----------------------------------------------------------------------

    "abdpel_wo": Exam(
        name="abdpel_wo",
        scan_time=SCAN_TIMES["abdpel"],         # 50s
        iv_contrast=False,
        oral_contrast=False,
        difficulty=1.3,
        volume=2_413,
        min_level=2,
    ),

    "l_spine": Exam(
        name="l_spine",
        scan_time=SCAN_TIMES["spine"],          # 30s
        iv_contrast=False,
        oral_contrast=False,
        difficulty=1.2,
        volume=1_338,                           # lumbosacral spine w + wo
        min_level=2,
    ),

    "maxfac": Exam(
        name="maxfac",
        scan_time=SCAN_TIMES["chest"],          # 25s — similar acquisition
        iv_contrast=False,
        oral_contrast=False,
        difficulty=1.3,
        volume=946,                             # CT maxillofacial w + wo
        min_level=2,
    ),

    "t_spine": Exam(
        name="t_spine",
        scan_time=SCAN_TIMES["spine"],          # 30s
        iv_contrast=False,
        oral_contrast=False,
        difficulty=1.2,
        volume=410,                             # CT thoracic spine w + wo
        min_level=2,
    ),

    # -----------------------------------------------------------------------
    # LEVEL 3 — contrast mechanics introduced (oral contrast, IV pressure)
    # -----------------------------------------------------------------------

    "abdpel_w": Exam(
        name="abdpel_w",
        scan_time=SCAN_TIMES["abdpel"],         # 50s acq; ORAL_CONTRAST_WAIT added before scan
        iv_contrast=True,
        oral_contrast=True,                     # the big pacing mechanic
        difficulty=1.5,
        volume=8_047,                           # CT abdomen pelvis w contrast (dominant contrast exam)
        min_level=3,
    ),

    "cta_chest": Exam(
        name="cta_chest",
        scan_time=SCAN_TIMES["cta_chest"],      # 35s — IV contrast, injector required
        iv_contrast=True,
        oral_contrast=False,
        difficulty=1.5,
        volume=3_067,                           # CTA chest (general, non-PE-protocol)
        min_level=3,
    ),

    "soft_neck_w": Exam(
        name="soft_neck_w",
        scan_time=SCAN_TIMES["chest"],          # 25s — IV contrast, neck series
        iv_contrast=True,
        oral_contrast=False,
        difficulty=1.3,
        volume=453,
        min_level=3,
    ),

    # -----------------------------------------------------------------------
    # LEVEL 4 — long studies, complex vascular, cardiac
    # -----------------------------------------------------------------------

    "cardiac_cta": Exam(
        name="cardiac_cta",
        scan_time=SCAN_TIMES["trauma_full"],    # 70s — gating, multiple phases
        iv_contrast=True,
        oral_contrast=False,
        difficulty=2.5,
        volume=3_549,                           # coronary CTA + TAVR + cardiac lung + CA quant
        min_level=4,
    ),

    "cta_abdpel": Exam(
        name="cta_abdpel",
        scan_time=SCAN_TIMES["abdpel"],         # 50s — multiphase vascular
        iv_contrast=True,
        oral_contrast=False,
        difficulty=2.0,
        volume=1_390,                           # CTA abdomen/pelvis, aorta, lower extremity runoff
        min_level=4,
    ),

    "arteriogram": Exam(
        name="arteriogram",
        scan_time=SCAN_TIMES["cta_head"],       # 45s — head + neck CTA combined
        iv_contrast=True,
        oral_contrast=False,
        difficulty=2.0,
        volume=1_791,                           # CT arteriogram head + neck (non-emergency)
        min_level=4,
    ),

    # -----------------------------------------------------------------------
    # TIER 2 CRITICAL PROTOCOLS — level 3+, highest-stakes non-trauma orders
    # These spawn as tier 2 acuity only. NOT in the general exam pool.
    # -----------------------------------------------------------------------

    "cta_chest_pe": Exam(
        name="cta_chest_pe",
        scan_time=SCAN_TIMES["cta_chest"],      # 35s — same acq as cta_chest but tier 2 priority
        iv_contrast=True,
        oral_contrast=False,
        difficulty=1.5,
        volume=767,                             # true PE protocol orders (~20% of all CTA chest)
        min_level=3,
    ),

    "sah_head": Exam(
        name="sah_head",
        scan_time=SCAN_TIMES["head"],           # 20s — fast non-contrast head
        iv_contrast=False,
        oral_contrast=False,
        difficulty=2.0,
        volume=48,
        min_level=3,
    ),

    "cta_neck_crit": Exam(
        name="cta_neck_crit",
        scan_time=SCAN_TIMES["cta_head"],       # 45s — dissection / AAA protocol
        iv_contrast=True,
        oral_contrast=False,
        difficulty=2.5,
        volume=300,                             # critical arteriogram neck (dissection, AAA)
        min_level=3,
    ),

    # -----------------------------------------------------------------------
    # TIER 1 EMERGENCY — level 5 only. Arrive as bundled exam packages.
    # Individual entries here so scanner_manager can run them sequentially.
    # -----------------------------------------------------------------------

    "stroke_head": Exam(
        name="stroke_head",
        scan_time=SCAN_TIMES["head"],           # 20s — non-contrast head, first in stroke bundle
        iv_contrast=False,
        oral_contrast=False,
        difficulty=3.0,
        volume=541,
        min_level=5,
    ),

    "stroke_cta": Exam(
        name="stroke_cta",
        scan_time=SCAN_TIMES["cta_head"],       # 45s — CTA head w perfusion, follows stroke_head
        iv_contrast=True,
        oral_contrast=False,
        difficulty=3.0,
        volume=406,
        min_level=5,
    ),

    # Trauma bundle components — always arrive together as exam_list
    "trauma_head": Exam(
        name="trauma_head",
        scan_time=SCAN_TIMES["head"],           # 20s
        iv_contrast=False,
        oral_contrast=False,
        difficulty=2.5,
        volume=37,
        min_level=5,
    ),

    "trauma_chest": Exam(
        name="trauma_chest",
        scan_time=SCAN_TIMES["chest"],          # 25s — chest wo contrast in trauma
        iv_contrast=False,
        oral_contrast=False,
        difficulty=2.5,
        volume=37,
        min_level=5,
    ),

    "trauma_abdpel": Exam(
        name="trauma_abdpel",
        scan_time=SCAN_TIMES["abdpel"],         # 50s — abdpel w contrast in trauma
        iv_contrast=True,
        oral_contrast=False,                    # trauma bypasses oral contrast
        difficulty=2.5,
        volume=37,
        min_level=5,
    ),
}
