# [LATER] — depends on patient states being stable
# ContrastManager — tracks oral contrast timers and injector fill status.
# Fires ContrastReady state change when oral contrast timer completes.
# Applies a penalty if IV scan starts before injector is filled.

from config import ORAL_CONTRAST_WAIT, INJECTOR_FILL_TIME


class ContrastManager:
    def __init__(self):
        self._oral_timers    = {}    # patient_id -> remaining game-seconds
        self._injector_ready = {}    # patient_id -> bool

    def start_oral_contrast(self, patient):
        """Begin oral contrast wait timer for a patient."""
        self._oral_timers[patient.patient_id] = ORAL_CONTRAST_WAIT

    def tick(self):
        """Count down timers. Fire ContrastReady when timer hits zero."""
        # TODO: decrement timers, update patient state on completion
        pass
