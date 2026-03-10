# [BUILD FIRST]
# TransportManager — handles all patient movement delays.
# Runs the Transport state machine for each active patient.
# Generates random delay values within config ranges on patient spawn.

import random
from config import TRANSPORT_ARRIVAL_DELAY, TRANSPORT_HOLD_WAIT, TRANSPORT_LEAVING_DELAY
from classes.transport import TransportState


class TransportManager:
    def __init__(self):
        self._active = {}    # patient_id -> Patient (those currently in transport)

    def assign_transport(self, patient):
        """Called when a patient is ordered. Sets random delay values."""
        patient.transport.arrival_delay = random.randint(*TRANSPORT_ARRIVAL_DELAY)
        patient.transport.hold_wait     = random.randint(*TRANSPORT_HOLD_WAIT)
        patient.transport.leaving_delay = random.randint(*TRANSPORT_LEAVING_DELAY)
        self._active[patient.patient_id] = patient

    def tick(self):
        """Advance transport state machines for all active patients."""
        # TODO: count down timers, advance TransportState, fire delivery event
        pass
