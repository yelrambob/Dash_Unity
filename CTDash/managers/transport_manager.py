# TransportManager — patient movement: inbound and outbound only.
# Setup (table on / scan / table off) is owned by ScannerManager.
#
# Phase ownership:
#   TransportManager  →  inbound_delay   (call + deliver to scanner area)
#   ScannerManager    →  setup_delay     (table on / position / table off)
#   TransportManager  →  leaving_delay   (post-scan pickup + exit from dept)
#
# State flow managed here:
#   INBOUND  — counting down inbound_delay
#              expires → patient.state = IN_HOLDING, removed from _inbound
#   OUTBOUND — counting down leaving_delay  (re-registered by ScannerManager post-scan)
#              expires → patient.state = COMPLETED, removed from _outbound
#
# assign_transport()    : called on patient spawn — rolls and scales all three delays
# register_outbound()   : called by ScannerManager when scan + setup are done
# tick()                : advances both inbound and outbound queues each game tick

import random
from config import (
    TRANSPORT_INBOUND, SCANNER_SETUP, TRANSPORT_OUTBOUND,
    MOBILITY_TRANSPORT_MULT, MOBILITY_SETUP_MULT,
)
from classes.transport import TransportState
from classes.patient import PatientState


class TransportManager:
    def __init__(self):
        self._inbound  = {}   # patient_id -> Patient  (INBOUND phase)
        self._outbound = {}   # patient_id -> Patient  (OUTBOUND phase)

    # ------------------------------------------------------------------
    def assign_transport(self, patient):
        """
        Dispatch transport for a patient.
        Called at spawn for non-oral-contrast exams, or by ContrastManager
        once the oral contrast timer has expired.
        Rolls all three delay values and kicks off the INBOUND phase.
        """
        t_mult = MOBILITY_TRANSPORT_MULT.get(patient.mobility, 1.0)
        s_mult = MOBILITY_SETUP_MULT.get(patient.mobility, 1.0)

        t = patient.transport
        t.inbound_delay  = int(random.randint(*TRANSPORT_INBOUND)  * t_mult)
        t.setup_delay    = int(random.randint(*SCANNER_SETUP)       * s_mult)
        t.leaving_delay  = int(random.randint(*TRANSPORT_OUTBOUND)  * t_mult)

        t.state = TransportState.INBOUND
        t.timer = t.inbound_delay
        patient.state = PatientState.IN_TRANSPORT
        self._inbound[patient.patient_id] = patient

    # ------------------------------------------------------------------
    def register_outbound(self, patient):
        """
        Called by ScannerManager when setup + scan are done.
        Starts the OUTBOUND phase — patient is waiting for pickup to leave dept.
        """
        t = patient.transport
        t.state = TransportState.OUTBOUND
        t.timer = t.leaving_delay
        patient.state = PatientState.LEAVING
        self._outbound[patient.patient_id] = patient

    # ------------------------------------------------------------------
    def tick(self, game_seconds=1):
        """
        Advance inbound and outbound timers.

        Returns:
            delivered  — list of patients that finished INBOUND this tick
                         (caller should hand to HoldingBay / ScannerManager)
            departed   — list of patients that finished OUTBOUND this tick
                         (caller should mark as COMPLETED and remove from sim)
        """
        delivered = []
        departed  = []

        for pid, patient in list(self._inbound.items()):
            patient.transport.timer -= game_seconds
            if patient.transport.timer <= 0:
                patient.transport.state = TransportState.IN_SETUP  # ScannerManager takes over
                patient.state = PatientState.IN_HOLDING
                delivered.append(patient)
                del self._inbound[pid]

        for pid, patient in list(self._outbound.items()):
            patient.transport.timer -= game_seconds
            if patient.transport.timer <= 0:
                patient.transport.state = TransportState.DONE
                # Use terminal_state if set (REFUSED/CANCELLED); default to COMPLETED.
                patient.state = patient.terminal_state or PatientState.COMPLETED
                departed.append(patient)
                del self._outbound[pid]

        return delivered, departed
