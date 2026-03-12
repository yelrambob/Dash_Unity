# Acuity table based on real departmental priority hierarchy.
#
# 4 tiers instead of 5 — reflects how the department actually operates:
#
#   Tier 1 — True emergencies: Trauma, Stroke. Non-negotiable, always first.
#   Tier 2 — Critical protocols: Aortic Dissection, AAA, PE, SAH.
#             Legitimate emergencies but subject to priority creep/abuse.
#             Player must judge legitimacy on higher difficulty levels.
#   Tier 3 — Inflated STATs: The ~80% of orders labeled STAT that aren't.
#             After Tier 1 and 2, these are treated in order of arrival time.
#   Tier 4 — Routine: Urgent, Routine inpatient, Scheduled outpatient,
#             Pending discharge. All treated the same in practice.
#
# spawn_weights are derived from 6 months of real volume data:
#   ~48,000 total exams: STAT ~82%, Routine/Urgent ~16%, critical ~2%
#
# exam_packages (tier 1 only):
#   Tier 1 patients arrive with a pre-set exam bundle. The package is picked
#   randomly by SpawnManager (weighted by volume). Each package sets the
#   patient's full exam_list — ScannerManager runs them sequentially.
#
# typical_exams (tier 2, 3, 4):
#   Pool of single-exam keys SpawnManager draws from, weighted by volume
#   in exam_catalog. SpawnManager filters by current level's min_level.
#
# min_tier_level: lowest game level at which this tier can spawn.
#   Tier 1 and 2 are locked until the player is ready for emergencies.
#
# Priority creep mechanic (future):
#   On higher difficulty levels, a fraction of Tier 3 orders will be
#   falsely labeled as Tier 2. Player can downgrade them but risks
#   a penalty if they're wrong.

ACUITY_TABLE = {
    1: {
        "label":          "Trauma / Stroke",
        "queue_priority": 1,              # always first, no exceptions
        "spawn_weight":   0.02,           # rare but highest stakes
        "wait_threshold": 2 * 60,         # 2 game-minutes before penalty — very tight
        "penalty_mult":   5.0,            # harshest penalty in the game
        "can_downgrade":  False,
        "min_tier_level": 5,              # tier 1 locked until level 5
        # Exam packages — picked randomly on spawn, weighted by volume.
        # "exams" sets the patient's full exam_list (run sequentially).
        "exam_packages": [
            {
                "name":   "trauma_full",
                "exams":  ["trauma_head", "trauma_chest", "trauma_abdpel"],
                "weight": 37,             # trauma activation count
            },
            {
                "name":   "stroke_simple",
                "exams":  ["stroke_head"],
                "weight": 135,            # code stroke head only (confirmed non-LVO)
            },
            {
                "name":   "stroke_full",
                "exams":  ["stroke_head", "stroke_cta"],
                "weight": 406,            # full stroke protocol with CTA perfusion
            },
        ],
        "notes": "Trauma and Medical Alert Stroke. Time is brain / time is life.",
    },

    2: {
        "label":          "Critical Protocol",
        "queue_priority": 2,
        "spawn_weight":   0.03,
        "wait_threshold": 5 * 60,         # 5 game-minutes
        "penalty_mult":   3.0,
        "can_downgrade":  True,           # player can challenge legitimacy
        "min_tier_level": 3,              # tier 2 unlocks at level 3
        # Single-exam pool — weights pulled from exam_catalog volume at runtime.
        "typical_exams": ["cta_chest_pe", "sah_head", "cta_neck_crit"],
        "notes": "Aortic Dissection, AAA, PE Protocol, SAH. Legitimate but "
                 "subject to abuse. SAH in particular used to bypass STAT queue.",
    },

    3: {
        "label":          "Inflated STAT",
        "queue_priority": 3,
        "spawn_weight":   0.80,           # bulk of real volume
        "wait_threshold": 15 * 60,
        "penalty_mult":   1.5,
        "can_downgrade":  False,
        "min_tier_level": 1,
        # Full general pool — SpawnManager filters by current level's min_level
        # and weights by exam volume. High-volume exams dominate naturally.
        "typical_exams": [
            "head_wo", "c_spine", "chest_wo", "chest_w", "extremity",
            "abdpel_wo", "l_spine", "maxfac", "t_spine",
            "abdpel_w", "cta_chest", "soft_neck_w",
            "cardiac_cta", "cta_abdpel", "arteriogram",
        ],
        "notes": "Everything labeled STAT that isn't Tier 1 or 2. "
                 "Priority creep means nothing is actually STAT when everything is STAT.",
    },

    4: {
        "label":          "Routine",
        "queue_priority": 4,
        "spawn_weight":   0.15,           # ~16% of real volume
        "wait_threshold": 30 * 60,
        "penalty_mult":   0.5,
        "can_downgrade":  False,
        "min_tier_level": 1,
        # Routine patients lean toward lower-complexity exams
        "typical_exams": [
            "head_wo", "abdpel_wo", "abdpel_w", "chest_wo",
            "l_spine", "c_spine", "extremity", "maxfac", "t_spine",
        ],
        "notes": "Urgent, Routine inpatient, Scheduled outpatient, Pending discharge. "
                 "Taken in order after STATs are clear.",
    },
}
