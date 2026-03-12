# TransportManager — handles all patient movement delays.
# Runs the Transport state machine for each active patient.
# Generates random delay values within config ranges on patient spawn,
# then scales them by the patient's mobility multiplier.
#
# State flow per patient:
#   WAITING_ASSIGNMENT -> (arrival_delay elapses) -> ACKNOWLEDGED
#   ACKNOWLEDGED       -> (hold_wait elapses)      -> ON_WAY
#   ON_WAY             -> timer=0                  -> DELIVERED  (patient moves to holding)
#   [post-scan]        -> re-registered            -> DELIVERED  (leaving_delay used externally)

import random
from config import (
    TRANSPORT_ARRIVAL_DELAY, TRANSPORT_HOLD_WAIT,
    TRANSPORT_LEAVING_DELAY, MOBILITY_TRANSPORT_MULT,
)
from classes.transport import TransportState
from classes.patient import PatientState


class TransportManager:
    def __init__(self):
        self._active = {}    # patient_id -> Patient

    def assign_transport(self, patient):
        """Called when a patient is ordered. Rolls random delays then scales by mobility."""
        mult = MOBILITY_TRANSPORT_MULT.get(patient.mobility, 1.0)

        patient.transport.arrival_delay = int(random.randint(*TRANSPORT_ARRIVAL_DELAY) * mult)
        patient.transport.hold_wait     = int(random.randint(*TRANSPORT_HOLD_WAIT)     * mult)
        patient.transport.leaving_delay = int(random.randint(*TRANSPORT_LEAVING_DELAY) * mult)

        # Kick off the first phase
        patient.transport.timer = patient.transport.arrival_delay
        self._active[patient.patient_id] = patient

    def tick(self, game_seconds=1):
        """
        Advance transport timers for all active patients by game_seconds.
        State transitions:
            WAITING_ASSIGNMENT: count down arrival_delay -> ACKNOWLEDGED, load hold_wait
            ACKNOWLEDGED:       count down hold_wait     -> ON_WAY  (timer=0, immediate advance)
            ON_WAY:             no further timer here; delivery is instant on transition
        Patients are removed from _active once DELIVERED.
        Returns list of patients that reached DELIVERED this tick (caller queues them to holding).
        """
        delivered = []

        for pid, patient in list(self._active.items()):
            t = patient.transport
            t.timer -= game_seconds

            if t.timer > 0:
                continue

            # Timer expired — advance state
            if t.state == TransportState.WAITING_ASSIGNMENT:
                t.state = TransportState.ACKNOWLEDGED
                t.timer = t.hold_wait

            elif t.state == TransportState.ACKNOWLEDGED:
                t.state = TransportState.ON_WAY
                t.timer = 0
                # ON_WAY is instantaneous in this model — transporter is already
                # moving; we mark delivery immediately and let the caller handle
                # placing the patient into the holding bay.
                t.state = TransportState.DELIVERED
                patient.state = PatientState.IN_HOLDING
                delivered.append(patient)
                del self._active[pid]

        return delivered
