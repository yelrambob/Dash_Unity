# Cancellations, Delays, and Tech Errors
## Design Reference

---

## 1. Cancellation Events (permanent removal)

Implemented via `EventManager` as `CANCELLED` terminal state.
Reason strings live in `data/event_reasons.py`.

### MD / Clinical team cancellations
- MD determined exam no longer necessary
- Order superseded by upgraded protocol (e.g., abd/pel → trauma full)
- Patient going directly to surgery
- Patient transferred to OR or outside facility
- Duplicate order corrected
- Wrong patient — order being corrected
- Patient admitted — order placed in error

### Contrast / Lab contraindications
- **GFR < 30**: IV contrast is contraindicated when renal function is too poor.
  The order may not flag this until labs are reviewed during intake.
  *Gameplay mechanic (future)*: when a contrast exam enters the queue, roll for
  "GFR not on file." If flagged, a short delay fires while labs are called.
  On result: GFR < 30 cancels the contrast version; exam either proceeds
  non-contrast (if a non-contrast protocol exists for that body part) or is
  cancelled entirely. Player decision point.

- **Contrast allergy**: see §3 Delay Events below. Severe allergy with no
  pre-med window available in shift → full cancellation.

- **No IV access**: nurse unable to establish access after two attempts →
  contrast exam cancelled; non-contrast version may substitute.

- **NPO violation**: patient ate/drank before a protocol requiring fasting →
  rescheduled (cancellation for current shift).

### Disposition / logistics
- Patient discharged before exam completed
- Patient transferred to outside facility mid-wait
- Patient expired
- Bed assignment change rerouting patient away from CT

---

## 2. Refusal Events (patient-driven, permanent)

Implemented via `EventManager` as `REFUSED` terminal state.

### Key rule: Holding bay lock
If a patient in `IN_HOLDING` state is REFUSED, the bay slot must remain
visually locked and the "pull to scanner" action must be suppressed until
the event is acknowledged. This is architecturally supported via
`patient.pending_acknowledgment` — the UI layer must enforce it visually.

### Left AMA (Against Medical Advice)
`REFUSED` entries tagged as AMA mean the patient self-departed.
- No outbound transport should be dispatched.
- Slot is freed on acknowledgment with no transport call.
- UI should detect AMA reason strings and suppress the "call transport" button.
- *Future*: add an explicit `left_ama: bool` flag to the Patient class rather
  than parsing the reason string.

### Contrast refusal
Patient has the right to refuse IV contrast. Exam may proceed non-contrast
if a protocol exists; otherwise cancellation. This is a sub-decision for
the player (future feature: "proceed non-contrast?" prompt).

---

## 3. Delay Events (patient held, eventual scan)

Not yet implemented. Patients move to a new `DELAYED` state with a countdown
timer. Bay slot remains occupied during the delay.

### Oral contrast
Already implemented (`ORAL_CONTRAST_WAIT = 180 game-seconds`).
Patient is held in `CONTRAST_ORDERED` state until timer expires.

### Allergy pre-medication protocols
Required when a patient with a known or newly-discovered contrast allergy
still needs a contrast study (benefit outweighs risk, ordered by MD).

**4-hour protocol** (standard, usable within a shift):
- Methylprednisolone 40 mg IV q4h × 3 doses
- Diphenhydramine 50 mg IV 1 hour before contrast
- Total delay: ~4 hours game-time
- Mechanic: patient enters `PREMEDICATION_HOLD` state; 4-hour countdown;
  then proceeds to injector as normal.

**13-hour protocol** (overnight prep, effectively next-shift):
- Methylprednisolone 32 mg PO at 13h and 7h before contrast
- Diphenhydramine 50 mg PO 1h before
- Total delay: 13 hours — outside any single shift window
- Mechanic: patient is flagged as `RESCHEDULED` (new terminal state);
  removed from queue; no score penalty but no exam credit either.
  Counts as "handled appropriately" — future level could continue them.

### IV access failure
- Attempt 1 fails → short delay (10–20 game-minutes); retry
- Attempt 2 fails → exam proceeds non-contrast or is cancelled
- Mechanic: single short-delay event; player prompted to decide if attempt 2
  failed (future feature)

### Claustrophobia / anxiety
- Patient distressed but willing to try with reassurance
- Short delay (5–15 game-minutes); tech spends time in room
- If unresolvable after delay → REFUSED
- Mechanic: delay event with small timeout; resolves to either proceed or refuse

---

## 4. Tech Error Events

Two tiers, both fire during the SCAN phase (after setup, before cooldown).
Neither fires during setup or cooldown.

### Written-up error (~1/500 scans at accuracy = 0.5)
- **What it is**: poor image quality requiring partial rescan, minor
  documentation gap, small protocol deviation. Not patient-harming.
- **Consequence**: small score penalty + on-screen "written up" discipline event.
- **Driven by**: `tech.accuracy`
- **Formula**: `P = TECH_WRITEUP_BASE_PROB * (1.0 - accuracy * TECH_ERROR_ATTR_REDUCTION)`
  At accuracy = 1.0: P ≈ 0 (never written up)
  At accuracy = 0.5: P ≈ 0.001 per scan (roughly 1 in 1000)
  At accuracy = 0.0: P = 0.002 (1 in 500)
- **Player visibility**: brief popup ("Alex — documentation written up") +
  point deduction. Not fireable; no workflow interruption.

### Fireable error (very rare; ~1/2500 at diligence = 0.5)
- **What it is**: wrong patient scanned, wrong protocol run, IV contrast
  given to a patient with documented allergy. CT is zero-sum — these are
  career-ending in the real world.
- **Consequence**: large score penalty. Tech flagged. Future: player must
  decide whether to suspend or terminate the tech.
- **Driven by**: `tech.diligence`
- **Formula**: `P = TECH_FIREABLE_BASE_PROB * (1.0 - diligence * TECH_ERROR_ATTR_REDUCTION)`
  At diligence = 1.0 (Riley): P ≈ 0 — essentially never happens.
  At diligence = 0.5: P ≈ 0.0002 per scan.
  At diligence = 0.62 (Morgan): P ≈ 0.00029 — low but real across a heavy shift.
- **Player visibility**: full-screen critical event popup; requires acknowledgment.
  Interrupts scanner (scan result flagged as compromised).

---

## 5. Natural Cancellation Spike Periods

Certain game-time windows have higher cancellation/event activity based on
real-world hospital flow patterns.

| Time window | Reason | Expected effect |
|---|---|---|
| 07:00–09:00 | Overnight orders reviewed at day shift start — many are stale, wrong patient, or for patients now in OR/discharged | High cancellation rate early |
| 09:00–12:00 | Peak volume, minimal logistical changes | Low cancellation, high throughput pressure |
| 12:00–13:30 | Lunch — transport slower, nursing staff transitions | Moderate delay events; slower inbound |
| 15:00–16:30 | Shift change — communication gaps increase wrong-order/wrong-patient risk | Mild cancellation/error spike |
| 17:00–20:00 | Discharge wave — patients leave AMA or are redirected; fatigue in staff | AMA/refusal rate increases |

*Implementation note*: These are handled via `hourly_spawn_weights.py` and
`event_manager.py` probability adjustments. The spawn weight table already
models the volume curve; event probability multipliers by hour are a future
addition.

---

## 6. Non-Contrast Fallback (future feature)

Several cancellation triggers (GFR < 30, IV access failure, contrast refusal)
have a natural fallback: run a non-contrast version if the clinical question
can still be answered.

Design pattern:
- `exam_catalog.py` should include non-contrast variants for key exams
  (e.g., `abdpel_nc`, `chest_nc`, `cta_head` has no non-contrast equivalent).
- When a contrast cancellation trigger fires, prompt player:
  "Proceed non-contrast?" → Yes → swap exam; No → full cancel.
- Score: non-contrast substitution earns partial credit (not full exam score).

---

*Last updated: attributes overhaul (speed/accuracy/willingness/diligence)*
