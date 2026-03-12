# Event reason strings — displayed in the acknowledgment popup when a
# CANCELLED or REFUSED event fires.
#
# These are intentionally short (one line) for UI display. The UI can append
# the patient name / exam type if needed. Keep each entry under ~60 chars.
#
# CANCELLATION_REASONS — MD pulled the order. Not the tech's fault.
# REFUSAL_REASONS      — Patient declined. Rarer; personability score influences
#                        likelihood but does not guarantee or prevent it.

CANCELLATION_REASONS = [
    "MD determined exam no longer necessary",
    "Patient transferred to OR",
    "Duplicate order — corrected by team",
    "Patient admitted, order placed in error",
    "Clinical condition changed, exam deferred",
    "Wrong patient — order being corrected",
    "Attending cancelled pending further labs",
    "Order placed on wrong patient by ED",
    "Patient going directly to surgery",
    "Exam superseded by upgraded protocol",
]

REFUSAL_REASONS = [
    "Patient declined — claustrophobia",
    "Patient too agitated to proceed safely",
    "Patient requested to speak with physician first",
    "Family requesting delay pending discussion",
    "Patient declined — does not want contrast",
    "Patient left against medical advice",
    "Patient unresponsive to positioning requests",
]
