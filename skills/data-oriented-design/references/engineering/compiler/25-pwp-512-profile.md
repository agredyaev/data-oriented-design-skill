# PWP and 512-Byte Frontend Profile

Use this optional profile when the task explicitly selects a 512-byte frontend or the diagnosed lexical bottleneck warrants testing it. Use [Pointerless state](30-pointerless-state.md) independently for PWP ownership/data design. PWP does not prescribe a tokenizer width.

## Sources and scope

- PWP: Andrew Kelley's [Programming without pointers](https://www.hytradboi.com/2025/05c72e39-c07e-41bc-ac40-85e8308f2917-programming-without-pointers).
- Wide frontend mechanisms: Validark's [Accelerated-Zig-Parser source](https://github.com/Validark/Accelerated-Zig-Parser/blob/8782a1924573641dc1f4a146afd530bf47838987/src/main.zig), inspected at commit `8782a1924573641dc1f4a146afd530bf47838987`. Relevant symbols include `Tokenizer`, `U512_IMPL`, `classifier_strategy`, `Operators`, and `Keywords`.

The source supports several vector shapes; its inspected defaults are 64 bytes. The 512-byte shape is an explicitly selectable profile here, not a claim that every tokenizer or current upstream default uses it. These instructions adapt the techniques to the task's grammar; do not copy Zig keyword/operator tables into another language.

## Apply PWP independently

PWP applies to retained data beyond compiler frontends. Use [Data shape](../01-data-shape.md), [Canonical state](../02-canonical-and-derived.md), and [Ownership](../04-ownership-and-concurrency.md) for general code. Use [Pointerless compiler state](30-pointerless-state.md) only for compiler-specific detail. No 512-byte classifier is required.

Preserve the original goals: low retained memory/cache traffic, explicit memory ownership, and serialization-friendly data. Select typed IDs/offsets/ranges, dense root-owned records, compact flags/side payloads, and derivation of deterministic values only where the contract and access pattern permit them. Address-independent data still requires bounds, version, identity, and wire validation before serialization or loading.

## Inputs and result

Inputs: selected logical batch contract, source lifetime, grammar/lexical rules, target machines, profile/budget when claiming speed.

Result: classifier/compactor candidate or decision that preserves the parser contract, plus the correctness and measurement evidence applicable to the claim. No AST/IR redesign is required for a classifier-only experiment.

## Decision tree

```text
512-byte contract explicitly selected?
  YES -> preserve 512 source bytes + 8 u64 lanes per class mask.
  NO  -> test this profile only if measured lexical cost selects it.
Missing grammar/boundary semantics?
  YES -> establish them before replacing classification.
Measured cause?
  classification -> compare global and on-demand class masks.
  event extraction -> compare batched compaction with scalar extraction.
  lexical lookup -> test compact operator/keyword lookup.
  retained parser state -> use Pointerless state.
Validate semantics and the claimed metric.
Reprofile; keep only the result supported by evidence.
```

## Logical contract and interchangeable backends

One logical input batch contains up to 512 valid source bytes. Each lexical class mask has 512 bits represented as 8 lanes of `u64`; mask bit i corresponds to source byte i. Define valid-byte masking, lane order, bit order, tail handling, and carry state before implementing a backend.

512 bytes is not a 512-bit hardware vector. A backend can process multiple smaller vectors or scalar/SWAR chunks while preserving the logical mask and parser-facing contract. Select AVX-512/BMI2, NEON, portable SWAR, or scalar mechanisms only where supported. Replacing a classifier/compactor backend must not require changing the parser.

Do not silently replace a selected 512-byte contract with a 64-byte contract merely because a machine has a different ISA. Backend parity is a semantic requirement; equivalent speed across machines is not assumed.

## Techniques that may be applied separately

| Technique | Candidate mechanism | Required checks |
| --- | --- | --- |
| Wide classification | produce class masks for a logical batch, then combine masks rather than branch per byte | valid tails, non-ASCII handling, strings/comments/escapes |
| Boundary algebra | derive start/end events from adjacent class bits and carried lexical state | carry across 64-bit lanes and 512-byte batches; tokens longer than one batch |
| Batch extraction | compact selected tags/positions in groups instead of a dependent trailing-zero loop | event count/order, empty/full masks, output capacity; keep a scalar oracle |
| On-demand classification | compute only class information needed by the current lexical operation; compare with a global classifier | identical class semantics and contextual exclusions; benchmark both strategies |
| Compact operator lookup | bounded candidate encoding/hash and dense lookup for the grammar's operator set | longest-match rules, prefixes, unknown operators, collisions, bounds and endianness |
| Dense keyword lookup | compact byte pool plus offsets/lengths and bounded candidate lookup | verify candidate length/content; identifiers sharing a hash must remain identifiers |
| Compact parser stream | emit tags plus extents; fold insignificant whitespace/comments only when semantics permit | source reconstruction for diagnostics, required comments, trailing trivia, long extent encoding |
| Pointerless parsing/direct emission | use local indices/scratch and emit the required semantic representation directly | keep staging representations with named consumers; preserve errors/order and fail closed |

A hash or compact tag is not proof of token equality. Preserve original bytes or another sufficient representation until all required checks finish. Do not allow invalid inputs to alias a valid operator or keyword.

## Connect to the existing modules

Use [Wide frontend](20-wide-frontend.md) for mask algebra, compact extents, and direct parsing; [Pointerless state](30-pointerless-state.md) for IDs/offsets/ranges and frozen data; [Pipeline elimination](10-pipeline-elimination.md) when an intermediate representation has no required consumer; and [Compiler validation](40-validation.md) before acceptance.

For the profiler route, select only the technique matching the measured cause, change one mechanism, then measure and rerank. For a broad redesign, use the structural route. Follow [Module composition](../../modules.md#choose-and-switch-routes) and shared [Reporting](../../workflow.md#proportional-result-format). A width/ISA choice alone proves no speedup.

