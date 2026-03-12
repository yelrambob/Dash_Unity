# EventManager — random REFUSED and CANCELLED events.
#
# Events can fire on any patient that is not yet at a terminal state.
# Both require player acknowledgment before the slot or queue entry is freed.
#
# Acknowledgment flow by patient location at event time:
#
#   Pre-holding (ORDERED, CONTRAST_ORDERED, IN_TRANSPORT):
#     → patient.requires_outbound = False
#     → On acknowledge: remove from queue and contrast timer tracking.
#       No transport needed — patient never arrived.
#
#   Physically present (IN_HOLDING, INJECTOR_READY, SCANNING, COOLDOWN):
#     → patient.requires_outbound = True
#     → Slot (bay or scanner) remains occupied and blocked until acknowledged.
#     → On acknowledge: scanner released (if scanning), bay slot freed,
#       outbound transport dispatched. Patient departs as REFUSED/CANCELLED
#       (not COMPLETED) so scoring can distinguish.
#
# Terminal states are REFUSED and CANCELLED — not COMPLETED.
# The transport_manager uses patient.terminal_state on outbound completion.

import random
from config import EVENT_CANCEL_PROB, EVENT_REFUSE_PROB
from classes.patient import PatientState
from data.event_reasons import CANCELLATION_REASONS, REFUSAL_REASONS


# States where a patient is physically present in the CT area.
_PHYSICAL_STATES = frozenset({
    PatientState.IN_HOLDING,
    PatientState.INJECTOR_READY,
    PatientState.SCANNING,
    PatientState.COOLDOWN,
})

# States where an event can fire.
# COOLDOWN is excluded — the scan has already run, images exist, the requisition
# is legally complete. A patient cannot refuse or an MD cancel at that point.
_ELIGIBLE_STATES = frozenset({
    PatientState.ORDERED,
    PatientState.CONTRAST_ORDERED,
    PatientState.IN_TRANSPORT,
    PatientState.IN_HOLDING,
    PatientState.INJECTOR_READY,
    PatientState.SCANNING,
})


class EventManager:
    def __init__(self, queue_manager, transport_manager, contrast_manager,
                 scanner_manager, holding_bays: list):
        """
        holding_bays: list of HoldingBay instances (one per zone).
        All other managers passed by reference — EventManager calls into them
        during acknowledge() to free occupied resources.
        """
        self._queue      = queue_manager
        self._transport  = transport_manager
        self._contrast   = contrast_manager
        self._scanner    = scanner_manager
        self._bays       = holding_bays

        self._pending = {}   # patient_id -> Patient (awaiting acknowledgment)

    # ------------------------------------------------------------------
    def tick(self, all_active_patients: list):
        """
        Check every active, non-pending patient for a random event.
        Call once per game tick. all_active_patients should be the full
        live patient list (from queue_manager.all_patients + any in scanner).
        """
        for patient in all_active_patients:
            if patient.pending_acknowledgment:
                continue
            if patient.state not in _ELIGIBLE_STATES:
                continue

            r = random.random()
            if r < EVENT_REFUSE_PROB:
                self._trigger(patient, PatientState.REFUSED)
            elif r < EVENT_REFUSE_PROB + EVENT_CANCEL_PROB:
                self._trigger(patient, PatientState.CANCELLED)

    # ------------------------------------------------------------------
    def acknowledge(self, patient_id: str):
        """
        Called when the player taps the acknowledgment prompt.
        Frees the occupied slot and dispatches outbound transport if needed.
        """
        patient = self._pending.pop(patient_id, None)
        if patient is None:
            return

        patient.pending_acknowledgment = False

        if patient.requires_outbound:
            # Free the scanner if this patient is on one.
            for sid, active in list(self._scanner._active_patients.items()):
                if active.patient_id == patient_id:
                    self._scanner.release_patient(sid)
                    break

            # Free the holding bay slot.
            for bay in self._bays:
                bay.remove(patient_id)

            # Dispatch outbound — terminal_state is already set (REFUSED/CANCELLED).
            self._transport.register_outbound(patient)

        else:
            # Patient never arrived — remove from queue and contrast tracking.
            self._queue.remove(patient_id)
            self._contrast.cancel_patient(patient_id)

    # ------------------------------------------------------------------
    @property
    def pending_events(self) -> list:
        """All patients awaiting acknowledgment — for UI popup list."""
        return list(self._pending.values())

    @property
    def has_pending(self) -> bool:
        return bool(self._pending)

    # ------------------------------------------------------------------
    def _trigger(self, patient, event_type: PatientState):
        reasons = (REFUSAL_REASONS if event_type == PatientState.REFUSED
                   else CANCELLATION_REASONS)

        patient.requires_outbound = patient.state in _PHYSICAL_STATES
        patient.event_reason      = random.choice(reasons)
        patient.terminal_state    = event_type
        patient.pending_acknowledgment = True
        patient.state             = event_type

        self._pending[patient.patient_id] = patient
