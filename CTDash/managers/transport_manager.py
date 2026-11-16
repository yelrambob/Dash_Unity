# [BUILD FIRST]
# TransportManager — handles all patient movement delays.
# Runs the Transport state machine for each active patient.
# Generates random delay values within config ranges on patient spawn.

import random
from config import TRANSPORT_ARRIVAL_DELAY, TRANSPORT_HOLD_WAIT, TRANSPORT_LEAVING_DELAY
from classes.patient import PatientState
from classes.transport import TransportState


class TransportManager:
    def __init__(self):
        self._active = {}    # patient_id -> Patient (those currently in transport)

    def assign_transport(self, patient):
        """Called when a patient is ordered. Sets random delay values and activates."""
        t = patient.transport
        t.arrival_delay  = random.randint(*TRANSPORT_ARRIVAL_DELAY)
        t.hold_wait      = random.randint(*TRANSPORT_HOLD_WAIT)
        t.leaving_delay  = random.randint(*TRANSPORT_LEAVING_DELAY)
        t.timer          = t.arrival_delay
        t.state          = TransportState.WAITING_ASSIGNMENT
        patient.state    = PatientState.IN_TRANSPORT
        self._active[patient.patient_id] = patient

    def tick(self):
        """Advance transport state machines for all active patients."""
        delivered = []

        for pid, patient in self._active.items():
            t = patient.transport
            t.timer -= 1

            if t.timer > 0:
                continue

            # Timer expired — advance state.
            if t.state == TransportState.WAITING_ASSIGNMENT:
                # Transporter acknowledged; now heading to patient.
                t.state = TransportState.ACKNOWLEDGED
                t.timer = t.hold_wait

            elif t.state == TransportState.ACKNOWLEDGED:
                # Transporter at patient, loading and moving.
                t.state = TransportState.ON_WAY
                t.timer = 0

            elif t.state == TransportState.ON_WAY:
                t.state = TransportState.DELIVERED
                # LEAVING patients are departing; all others arrive at holding bay.
                if patient.state == PatientState.LEAVING:
                    patient.state = PatientState.COMPLETED
                else:
                    patient.state = PatientState.IN_HOLDING
                delivered.append(pid)

        for pid in delivered:
            del self._active[pid]

    def begin_leaving(self, patient):
        """Called after scan completes. Patient waits leaving_delay then departs."""
        t = patient.transport
        # Jump straight to ON_WAY with leaving_delay so only one phase runs.
        t.state = TransportState.ON_WAY
        t.timer = t.leaving_delay
        patient.state = PatientState.LEAVING
        self._active[patient.patient_id] = patient
