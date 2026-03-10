# [BUILD FIRST]
# SpawnManager — controls when and what patients appear.
# Reads hourly_spawn_weights.py for timing and acuity bias.
# Assigns acuity, mobility type, and exam list on spawn.
# Adds new Patient objects to the ordered queue.

from data.hourly_spawn_weights import HOURLY_SPAWN_TABLE
from data.acuity_table import ACUITY_TABLE


class SpawnManager:
    def __init__(self, queue_manager):
        self.queue_manager = queue_manager
        self._patient_counter = 0    # used to generate unique patient IDs

    def tick(self, game_hour: int, game_second: int):
        """Called every simulation tick. Decides whether to spawn a patient."""
        # TODO: use spawn_weight and game_hour to probabilistically spawn
        pass

    def _spawn_patient(self, game_hour: int):
        """Creates a new Patient and adds it to the queue."""
        # TODO: pick acuity using acuity_bias, pick exam from acuity_table,
        #       assign random mobility, create Transport, build Patient
        pass

    def _next_patient_id(self) -> str:
        self._patient_counter += 1
        return f"PAT_{self._patient_counter:04d}"
