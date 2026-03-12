# SpawnManager — controls when and what patients appear.
#
# Spawning pipeline each tick:
#   1. Per-second probability = exams_per_hour / 3600 (from hourly table)
#   2. Roll against that probability → spawn or skip
#   3. Pick acuity tier (weighted by spawn_weight × hourly acuity_bias)
#      — tiers above min_tier_level for this level are excluded
#   4. Pick exam package (tier 1) or single exam (tier 2/3/4)
#      — exam pool is filtered to exams with min_level <= current_level
#      — weighted by real volume from exam_catalog
#   5. Roll mobility (distribution shifts toward stretcher for high acuity)
#   6. Create Patient + Transport, hand to QueueManager
#      If first exam requires oral contrast → ContrastManager starts timer (transport deferred)
#      Otherwise → TransportManager dispatches immediately
#
# Level gating:
#   - min_tier_level on each tier controls when emergencies unlock
#   - min_level on each exam controls when complex studies appear
#   - Early levels get simpler, faster, no-contrast exams naturally
#     because high-volume contrast exams are level 3+

import random
from data.hourly_spawn_weights import HOURLY_SPAWN_TABLE
from data.acuity_table import ACUITY_TABLE
from data.exam_catalog import EXAM_CATALOG
from classes.patient import Patient, PatientState
from classes.transport import Transport


# Mobility distribution per acuity tier.
# Tier 1 (trauma/stroke): mostly stretcher — these patients are not walking in.
# Tier 3/4 (routine): mostly ambulatory.
_MOBILITY_BY_TIER = {
    1: [("ambulatory", 0.05), ("wheelchair", 0.20), ("stretcher", 0.75)],
    2: [("ambulatory", 0.15), ("wheelchair", 0.35), ("stretcher", 0.50)],
    3: [("ambulatory", 0.45), ("wheelchair", 0.35), ("stretcher", 0.20)],
    4: [("ambulatory", 0.55), ("wheelchair", 0.35), ("stretcher", 0.10)],
}


class SpawnManager:
    def __init__(self, level: int, queue_manager, transport_manager, contrast_manager):
        self.level             = level
        self.queue_manager     = queue_manager
        self.transport_manager = transport_manager
        self.contrast_manager  = contrast_manager
        self._patient_counter  = 0

        # Build per-tier weighted exam pools at init (not every tick).
        # Pools are dicts: exam_key -> volume, filtered by min_level <= level.
        self._exam_pools = self._build_exam_pools()

    # ------------------------------------------------------------------
    def tick(self, game_hour: int, game_time: int):
        """
        Called every game-second tick.
        game_hour:  current hour (0–23) for spawn rate lookup
        game_time:  absolute game-seconds since shift start (used as arrival tiebreaker)
        """
        row = HOURLY_SPAWN_TABLE.get(game_hour, HOURLY_SPAWN_TABLE[0])
        spawn_prob = row["exams_per_hour"] / 3600.0

        if random.random() < spawn_prob:
            self._spawn_patient(row["acuity_bias"], game_time)

    # ------------------------------------------------------------------
    def _spawn_patient(self, acuity_bias: float, game_time: int):
        acuity   = self._pick_acuity(acuity_bias)
        exams    = self._pick_exams(acuity)
        mobility = self._pick_mobility(acuity)

        patient = Patient(
            patient_id=self._next_patient_id(),
            acuity=acuity,
            personability=round(random.uniform(0.0, 1.0), 2),
            mobility=mobility,
            exam_list=exams,
            transport=Transport(),
            state=PatientState.ORDERED,
        )

        # Oral contrast must complete before transport is dispatched.
        # Patient appears in the order queue immediately regardless.
        first_exam = EXAM_CATALOG.get(patient.exam_list[0])
        if first_exam and first_exam.oral_contrast:
            self.contrast_manager.start_oral_contrast(patient)
        else:
            self.transport_manager.assign_transport(patient)

        self.queue_manager.add_patient(patient, game_time)

    # ------------------------------------------------------------------
    def _pick_acuity(self, acuity_bias: float) -> int:
        """
        Pick a tier weighted by spawn_weight, adjusted by hourly acuity_bias.
        acuity_bias boosts tier 1+2 relative weight (higher overnight when
        proportionally more of the low volume IS emergencies).
        Tiers above their min_tier_level are excluded for this level.
        """
        eligible = {
            t: data for t, data in ACUITY_TABLE.items()
            if data["min_tier_level"] <= self.level
        }

        weights = {}
        for t, data in eligible.items():
            w = data["spawn_weight"]
            if t <= 2:
                w *= (1.0 + acuity_bias * 2.0)   # emergency boost scales with bias
            weights[t] = w

        total = sum(weights.values())
        r     = random.uniform(0, total)
        cumulative = 0.0
        for t, w in weights.items():
            cumulative += w
            if r <= cumulative:
                return t
        return max(eligible.keys())   # fallback: lowest priority tier

    # ------------------------------------------------------------------
    def _pick_exams(self, acuity: int) -> list:
        """
        Tier 1 → pick from exam_packages (multi-exam bundles).
        Tier 2/3/4 → pick one exam from the level-filtered pool, weighted by volume.
        """
        tier = ACUITY_TABLE[acuity]

        if "exam_packages" in tier:
            packages = tier["exam_packages"]
            weights  = [p["weight"] for p in packages]
            package  = random.choices(packages, weights=weights, k=1)[0]
            return list(package["exams"])

        pool = self._exam_pools.get(acuity, {})
        if not pool:
            return ["head_wo"]   # safe fallback; should not happen in normal play

        keys    = list(pool.keys())
        volumes = list(pool.values())
        return [random.choices(keys, weights=volumes, k=1)[0]]

    # ------------------------------------------------------------------
    def _pick_mobility(self, acuity: int) -> str:
        options   = _MOBILITY_BY_TIER.get(acuity, _MOBILITY_BY_TIER[4])
        mobilities = [m for m, _ in options]
        weights    = [w for _, w in options]
        return random.choices(mobilities, weights=weights, k=1)[0]

    # ------------------------------------------------------------------
    def _build_exam_pools(self) -> dict:
        """
        Pre-compute {tier: {exam_key: volume}} for tier 2/3/4.
        Filters each tier's typical_exams list to exams with min_level <= self.level.
        Tier 1 uses packages (handled separately in _pick_exams).
        """
        pools = {}
        for tier, data in ACUITY_TABLE.items():
            if "typical_exams" not in data:
                continue
            pool = {}
            for key in data["typical_exams"]:
                exam = EXAM_CATALOG.get(key)
                if exam and exam.min_level <= self.level:
                    pool[key] = exam.volume
            pools[tier] = pool
        return pools

    # ------------------------------------------------------------------
    def _next_patient_id(self) -> str:
        self._patient_counter += 1
        return f"PAT_{self._patient_counter:04d}"
