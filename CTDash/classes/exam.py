# Exam class — represents a single scan type.
# No logic here; just holds data about what an exam IS.
#
# Contrast fields define what the exam REQUIRES — timing is in config.py,
# the countdown state machines live in contrast_manager.py:
#   iv_contrast   → patient must wait at injector (INJECTOR_FILL_TIME) before scan
#   oral_contrast → patient waits in holding (ORAL_CONTRAST_WAIT) before they can scan
#
# volume: real 6-month count from department data. Used by SpawnManager to
# compute normalized spawn weights within each level's available pool.
# Keeping it here means weights stay coupled to the exam definition.
#
# min_level: lowest game level this exam type can appear.
# SpawnManager filters the pool by level before computing weights.

from dataclasses import dataclass, field


@dataclass
class Exam:
    name:         str            # short key matching exam_catalog.py
    scan_time:    int            # scanner acquisition time in game-seconds (NOT including contrast waits)
    iv_contrast:  bool           # requires IV contrast + injector fill before scan
    oral_contrast: bool          # requires oral contrast wait before scan
    difficulty:   float          # 1.0–3.0, scales tech accuracy penalty
    volume:       int   = 0      # real 6-month exam count — drives spawn weight derivation
    min_level:    int   = 1      # minimum game level this exam appears in
