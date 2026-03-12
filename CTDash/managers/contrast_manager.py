# ContrastManager — tracks oral contrast timers and IV injector fill status.
#
# Oral contrast flow (corrected — contrast happens BEFORE transport):
#   1. On spawn, if exam needs oral_contrast → start_oral_contrast(patient)
#      Patient stays CONTRAST_ORDERED in the order queue with a visible countdown.
#   2. tick() counts down contrast_timer each game-second.
#   3. On expiry → patient.state = IN_TRANSPORT, transport_manager.assign_transport() called.
#      Transport is only dispatched AFTER the oral contrast wait is complete.
#
# IV injector flow (scanner-side, unchanged):
#   Handled separately — see ScannerManager.
#
# UI note (future): patient.contrast_timer / ORAL_CONTRAST_WAIT gives the 0→1 fraction
#   for a circular pie timer on each CONTRAST_ORDERED card in the order list.

from config import ORAL_CONTRAST_WAIT
from classes.patient import PatientState


class ContrastManager:
    def __init__(self, transport_manager):
        self._transport_manager = transport_manager
        self._oral_timers = {}   # patient_id -> Patient

    def start_oral_contrast(self, patient):
        """
        Begin oral contrast wait. Patient stays in their room — do NOT call
        assign_transport yet. Called at spawn for any exam with oral_contrast=True.
        """
        patient.state = PatientState.CONTRAST_ORDERED
        patient.contrast_timer = ORAL_CONTRAST_WAIT
        self._oral_timers[patient.patient_id] = patient

    def tick(self):
        """
        Decrement oral contrast timers. When a timer expires, dispatch transport.
        Returns list of patients whose oral contrast finished this tick.
        """
        ready = []
        for pid, patient in list(self._oral_timers.items()):
            patient.contrast_timer -= 1
            if patient.contrast_timer <= 0:
                patient.contrast_timer = 0
                ready.append(patient)
                del self._oral_timers[pid]

        for patient in ready:
            self._transport_manager.assign_transport(patient)

        return ready

    def timer_for(self, patient_id):
        """Return remaining oral contrast seconds, or None if not tracking."""
        p = self._oral_timers.get(patient_id)
        return p.contrast_timer if p else None

    @property
    def active_count(self):
        return len(self._oral_timers)
