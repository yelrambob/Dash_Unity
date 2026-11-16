# [BUILD FIRST]
# SpawnManager — controls when and what patients appear.
# Reads hourly_spawn_weights.py for timing and acuity bias.
# Assigns acuity, mobility type, and exam list on spawn.
# Adds new Patient objects to the ordered queue.

import random

from classes.patient import Patient
from classes.transport import Transport, TransportState
from config import TRANSPORT_ARRIVAL_DELAY, TRANSPORT_HOLD_WAIT, TRANSPORT_LEAVING_DELAY
from data.hourly_spawn_weights import HOURLY_SPAWN_TABLE
from data.acuity_table import ACUITY_TABLE

_MOBILITY_TYPES = ["ambulatory", "wheelchair", "stretcher"]

# High-acuity tiers (1–2) vs low-acuity tiers (3–4).
# acuity_bias rolls against the high-tier pool first; within each pool
# the base spawn_weights are used as relative weights.
_HIGH_TIERS = [1, 2]
_LOW_TIERS  = [3, 4]


class SpawnManager:
    def __init__(self, queue_manager):
        self.queue_manager = queue_manager
        self._patient_counter = 0    # used to generate unique patient IDs

    def tick(self, game_hour: int, game_second: int):
        """Called every simulation tick. Decides whether to spawn a patient."""
        row = HOURLY_SPAWN_TABLE.get(game_hour, HOURLY_SPAWN_TABLE[0])
        # Convert exams_per_hour to a per-tick probability.
        # At TICK_SECONDS=1 each tick is one game-second, so prob = n / 3600.
        prob = row["exams_per_hour"] / 3600.0
        if random.random() < prob:
            self._spawn_patient(game_hour, game_second)

    def _spawn_patient(self, game_hour: int, game_second: int):
        """Creates a new Patient and adds it to the queue."""
        row = HOURLY_SPAWN_TABLE.get(game_hour, HOURLY_SPAWN_TABLE[0])
        acuity_bias = row["acuity_bias"]

        # Pick acuity tier: acuity_bias = probability of drawing from high-acuity pool.
        pool = _HIGH_TIERS if random.random() < acuity_bias else _LOW_TIERS
        weights = [ACUITY_TABLE[t]["spawn_weight"] for t in pool]
        total   = sum(weights)
        norm    = [w / total for w in weights]
        acuity  = random.choices(pool, weights=norm, k=1)[0]

        tier    = ACUITY_TABLE[acuity]
        exam    = random.choice(tier["typical_exams"])
        mobility = random.choice(_MOBILITY_TYPES)

        arrival_delay = random.randint(*TRANSPORT_ARRIVAL_DELAY)
        transport = Transport(
            state=TransportState.WAITING_ASSIGNMENT,
            arrival_delay=arrival_delay,
            hold_wait=random.randint(*TRANSPORT_HOLD_WAIT),
            leaving_delay=random.randint(*TRANSPORT_LEAVING_DELAY),
            timer=arrival_delay,   # start counting down immediately
        )

        patient = Patient(
            patient_id=self._next_patient_id(),
            acuity=acuity,
            personability=round(random.random(), 2),
            mobility=mobility,
            exam_list=[exam],
            transport=transport,
        )

        self.queue_manager.add_patient(patient, game_second)

    def _next_patient_id(self) -> str:
        self._patient_counter += 1
        return f"PAT_{self._patient_counter:04d}"
