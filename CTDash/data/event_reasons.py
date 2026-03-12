# Event reason strings — displayed in the acknowledgment popup when a
# CANCELLED or REFUSED event fires.
#
# These are intentionally short (one line) for UI display. The UI can append
# the patient name / exam type if needed. Keep each entry under ~60 chars.
#
# CANCELLATION_REASONS — MD pulled the order or logistical conflict.
#   Not the tech's fault. Patient may or may not still be physically present.
#
# REFUSAL_REASONS — Patient or family declined.
#   Rarer than cancellations. If patient is IN_HOLDING, bay slot stays
#   occupied and must be acknowledged before it can accept a new patient.
#   "Left AMA" entries mean no outbound transport — patient self-departed.
#   (UI should suppress "call transport" button for AMA events.)

CANCELLATION_REASONS = [
    # --- MD / clinical team pulled the order ---
    "MD determined exam no longer necessary",
    "Clinical condition changed — exam deferred",
    "Exam superseded by upgraded protocol",
    "Attending cancelled pending further workup",
    "Duplicate order — corrected by team",
    "Patient going directly to surgery",
    "Patient transferred to OR",
    "Patient admitted — order placed in error",
    "Order placed on wrong patient by ED",
    "Wrong patient — order being corrected",
    # --- Contrast / lab contraindications ---
    "IV contrast contraindicated — GFR < 30",       # renal function below threshold
    "Contrast allergy — pre-med protocol required",  # delays 4hr or 13hr; see design notes
    "No IV access — contrast exam not possible",
    "Patient NPO violation — exam rescheduled",
    # --- Logistical / disposition ---
    "Patient discharged before exam completed",
    "Patient expired",
    "Patient transferred to outside facility",
    "Bed assignment changed — transport rerouted",
]

REFUSAL_REASONS = [
    # --- Patient declined ---
    "Patient declined — claustrophobia",
    "Patient declined — does not want contrast",
    "Patient declined — requested second opinion",
    "Patient too agitated to proceed safely",
    "Patient unresponsive to positioning requests",
    # --- Family / proxy ---
    "Family requesting delay pending physician discussion",
    "Healthcare proxy declined on patient's behalf",
    # --- Left AMA (no outbound transport — patient self-departed) ---
    "Patient left against medical advice",
    "Patient walked out during holding wait",
    # --- Physician consultation requested ---
    "Patient requested to speak with ordering physician first",
    "Patient requesting interpreter before proceeding",
]
