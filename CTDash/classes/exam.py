# [BUILD FIRST]
# Exam class — represents a single scan type.
# No logic here; just holds data about what an exam IS.

from dataclasses import dataclass


@dataclass
class Exam:
    name: str            # short key matching exam_catalog.py
    scan_time: int       # base duration in game-seconds
    iv_contrast: bool    # requires IV contrast injection
    oral_contrast: bool  # requires oral contrast wait timer
    difficulty: float    # 1.0–3.0, affects tech accuracy penalty
