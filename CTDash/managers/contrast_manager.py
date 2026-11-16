# [LATER] — depends on patient states being stable
# ContrastManager — tracks oral contrast timers and injector fill status.
# Fires ContrastReady state change when oral contrast timer completes.
# Applies a penalty if IV scan starts before injector is filled.

from classes.patient import PatientState
from config import ORAL_CONTRAST_WAIT, INJECTOR_FILL_TIME


class ContrastManager:
    def __init__(self):
        self._oral_patients  = {}    # patient_id -> Patient (oral contrast waiting)
        self._injector_ready = {}    # patient_id -> bool

    def start_oral_contrast(self, patient):
        """Begin oral contrast wait timer for a patient."""
        patient.contrast_timer = ORAL_CONTRAST_WAIT
        patient.state          = PatientState.CONTRAST_ORDERED
        self._oral_patients[patient.patient_id] = patient

    def fill_injector(self, patient):
        """Signal that the IV injector has been filled for a patient."""
        self._injector_ready[patient.patient_id] = True
        patient.state = PatientState.INJECTOR_READY

    def tick(self):
        """Count down oral contrast timers. Fire ContrastReady when timer hits zero."""
        ready = []
        for pid, patient in self._oral_patients.items():
            patient.contrast_timer -= 1
            if patient.contrast_timer <= 0:
                patient.contrast_timer = 0
                patient.state          = PatientState.CONTRAST_READY
                ready.append(pid)

        for pid in ready:
            del self._oral_patients[pid]
