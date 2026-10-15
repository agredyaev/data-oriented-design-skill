# Batch Contract and Classification Decisions

## Decision tree: choose logical width and backend

```text
Does the task/API explicitly require 512 source bytes + 8×u64 masks?
  YES -> KEEP that logical contract; choose only the implementation backend.
  NO -> Is changing width necessary for a measured lexical cost or stated budget?
          NO -> KEEP current width.
          UNKNOWN -> MEASURE lexical cost; do not select 512 from its name.
          YES -> compare candidate widths under the same workload/acceptance rule.
Does the target support the instructions used by this backend?
  YES -> test that backend against the scalar reference.
  NO -> implement with supported vectors/SWAR/scalar chunks under the same contract.
Do masks, event order, carry state, and errors match the reference?
  NO -> REJECT backend.
  YES -> accept semantic portability; claim speed only after matched measurement.
```

### Example: ARM with a selected 512-byte contract

Input: logical block size 512, `mask: [8]u64`, target has NEON but no AVX-512.

Decision: process the block in 16-byte chunks if appropriate; combine their class bits into the same eight lanes. Do not change the parser API to 64 bytes. The number of NEON operations and resulting speed remain measurement questions.

Tail example: `valid_len=70` permits all 64 bits of lane 0 and only bits 0–5 of lane 1. Clear other bits before boundary algebra or compaction. Padding bytes must not emit tokens.

## Decision tree: derive boundaries across lanes and blocks

```text
Can this class be identified without lexical context?
  YES -> form its raw class mask.
  NO -> carry the required string/comment/escape state and mask contextual exclusions.
Do adjacent class bits cross a 64-bit lane?
  YES -> shift with neighbor-lane carry, not eight independent lane shifts.
Does a token remain open at the end of a logical block?
  YES -> retain its state/extent and defer its final event until termination or EOF.
  NO -> emit complete events.
Is next-byte information needed to decide the last boundary?
  YES -> use a validated lookahead or defer that decision to the next block.
Do grammar cases or carry semantics remain unknown?
  YES -> KEEP the existing scanner for those cases until semantics are established.
```

### Example: one identifier crossing bit 63

Identifier bytes occupy global positions 62, 63, and 64. Lane 0 has bits 62–63 set; lane 1 has bit 0 set. There is one start at 62 and one end at 64, not a second identifier at 64.

For a context-free word mask, compute starts as `word & ~previous_word_bits`, where `previous_word_bits[i] = word[i-1]`, including lane/batch carry. Compute ends from the next-bit relation or defer the last decision. Never apply this formula to quoted content without the grammar's contextual mask.

Check tokens of length 0/1/63/64/65/511/512/513 where valid, escaped quotes at boundaries, comments spanning blocks, non-ASCII, truncated input, and the final partial block.

## Decision tree: global versus on-demand classification

```text
Do downstream operations consume exactly the same class result?
  NO -> retain distinct semantics; do not merge classifiers.
  YES -> can one admitted result be reused for their entire lifetime?
          YES -> candidate: classify once and propagate it.
          NO -> keep the required lifetime/context boundary.
Is global/on-demand classification selected by an explicit platform/contract constraint?
  YES -> implement that choice and verify equivalence.
  NO -> do matched timings identify a lower total cost?
          UNKNOWN -> compare both over the selected phase and end-to-end target.
          YES -> select the passing candidate, including reused masks and writes.
          NO -> KEEP the simpler existing implementation.
```

### Example: a classification change that loses

Illustrative matched phase times: global classification plus consumers = 3.0 ms; on-demand classification plus the same consumers = 4.5 ms because three consumers repeat the class computation. Both produce identical results. If the acceptance rule is lower phase time with no target regression, keep global classification. A smaller lookup table alone does not justify on-demand classification.

Use [Validation](../40-validation.md) for semantic/measurement acceptance and [Measurement](../../../performance/01-measurement.md) for matched runs.
