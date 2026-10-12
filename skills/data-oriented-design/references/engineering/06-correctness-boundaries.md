# Correctness Boundaries

# 8. Correctness Rules That Override Cleanup

DOD/YAGNI cleanup must never remove correctness boundaries.

## SAFE-01 — Preserve live authority checks

Snapshot validation does not replace transaction-local checks.

Claims, leases, epochs, fences, readiness, and finalization may require separate checks because they have different authority and isolation responsibilities.

Do not combine them into a generic transaction wrapper merely because they look repetitive.

---

## SAFE-02 — Preserve distinct invariants

SCD2 checks such as:

- source uniqueness;
- current-row uniqueness;
- monotonic change time;
- history validity;
- affected-row count;

protect different invariants.

Do not deduplicate them into one vague "validate SCD2" check if doing so weakens or obscures the individual guarantees.

---

## SAFE-03 — Preserve upgrade migrations

Old migrations required to upgrade a supported installation are not dead code.

Do not delete them because the current schema no longer needs them during a fresh install.

---

## SAFE-04 — Preserve independent test oracles

An intentionally independent implementation used as a test oracle may look duplicated but serves a distinct validation responsibility.

Do not consolidate the oracle with the implementation under test.

---

## SAFE-05 — Preserve wire-level validation

Do not remove checks that depend on original input bytes merely because an internal typed representation exists.

Examples include:

- duplicate JSON key detection;
- exact framing;
- truncation detection;
- version rejection;
- canonical-byte constraints.

---
