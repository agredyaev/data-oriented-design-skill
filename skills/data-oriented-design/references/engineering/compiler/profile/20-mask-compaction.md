# Mask Compaction Decisions

## Decision tree: replace scalar event extraction

```text
Does the profile attribute target cost to mask-to-event extraction?
  NO -> KEEP scalar extraction; investigate the measured cause.
  UNKNOWN -> MEASURE extraction separately from classification and output writes.
  YES -> must emitted events preserve source order?
          YES -> candidate must compact lanes and bits in ascending source order.
          NO -> preserve the actual output contract; do not invent an ordering need.
Is the candidate instruction supported on every target using this backend?
  NO -> use supported SWAR/scalar compaction or dispatch to a supported backend.
  YES -> test the vector/BMI-style candidate.
Do event count, positions/tags, capacity bounds, and parser results match?
  NO -> REJECT candidate.
  YES -> do extraction cost and declared target pass the acceptance rule?
          NO -> reject the speed claim; keep only a separately justified simplification.
          YES -> KEEP candidate and reprofile/rerank.
```

### Example: preserve order across mask lanes

Input mask: set bits at absolute positions `0, 63, 64, 511`. Scalar extraction emits `[0, 63, 64, 511]`.

Candidate: compact each lane, add the lane base, then concatenate lanes in order. Lane 0 emits `[0,63]`, lane 1 emits `[64]`, lane 7 emits `[511]`. Concatenating in completion order `[511,0,63,64]` is invalid for an ordered token stream even if the event set matches.

An output reservation must cover the number and encoding width of emitted events. An all-zero mask emits zero events; an all-one valid 512-bit mask can emit 512 events. Do not use a 256-entry output buffer merely because the average mask is sparse.

## Decision tree: keep a batched extractor after measurement

```text
Are before/after inputs, backend conditions, and parser outputs matched?
  NO -> rerun a valid comparison.
Did the predicted extraction metric improve beyond declared uncertainty?
  NO -> REJECT the causal hypothesis.
Did the declared phase/end-to-end target improve as required?
  NO -> report only the proven local effect; do not declare the target solved.
Does the candidate add dispatch, scratch, or a second retained representation?
  YES -> include its build/lifetime/maintenance cost in the acceptance comparison.
Can that added cost be justified by a passed budget or removed structure?
  NO -> KEEP the existing extractor.
```

### Example: compaction improves locally, not the target

Illustrative result: extraction drops from 8 to 4 ms, but total workload remains 100 ms within ±5 ms uncertainty. Report a local extraction improvement only. If the goal was total time below 90 ms, it remains unmet. Reprofile before the next change; do not repeatedly tune the old top entry.

Check the scalar reference against masks with no bits, one bit, every bit, bit 63/64 transitions, partial tails, and random masks. Check grammar-level outputs as well as mask positions. Use [Compiler validation](../40-validation.md) for acceptance.
