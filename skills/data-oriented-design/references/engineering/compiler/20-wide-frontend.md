# Wide Frontend and Direct Parsing

Use this block for the compiler-specific question "what is the minimum parser-facing lexical representation?" It owns lexical masks/contracts, compact token state, repeated lexical decoding, and direct parser emission. It does not own the general SIMD backend or explicit 512-byte mechanics.

For speed claims, measure the frontend cause first. Structural removal of a representation may proceed from consumer/lifetime evidence without a speed claim.

## Decision tree

```text
Which demonstrated frontend cause must be changed?
  branch-per-byte/item classification
      -> define the required lexical classes/boundary semantics here;
         explicit 512 contract -> PWP/512 router;
         otherwise SIMD backend -> General SIMD.
  one-by-one extraction from a hot lexical mask
      -> explicit 512 mask -> PWP/512 compaction;
         otherwise backend compaction -> General SIMD.
  redundant token source/position state
      -> reduce to the minimum parser contract.
  repeated keyword/name decode
      -> resolve/admit lexical identity once; use compact lookup only when that lookup itself is selected.
  staging syntax tree immediately lowered with no independent consumer
      -> test direct emission.
  none / evidence missing
      -> keep current representation or establish the missing consumer/cost fact.
```

Any semantic change must pass [Compiler validation](40-validation.md).

## Lexical batch contract

A lexical batch candidate may represent source-byte classes as masks/bitsets plus cross-batch state. This file defines which classes and parser-visible events are required; it does not choose machine lane width.

For a non-512 vector backend, use [General SIMD](../10-simd-and-dense-processing.md) after the lexical contract is fixed. For an explicit logical 512-byte contract, use the [PWP/512 router](25-pwp-512-profile.md), which owns lane carry, tails, classification reuse, and 512-specific compaction.

Required cross-block semantics such as strings, comments, escapes, and token order must be explicit before either backend route.

## Minimum token information

Avoid redundant token state such as:

```text
Token {
    kind
    start
    end
    copied_text
}
```

when source bytes remain available and consumers need only a smaller contract. A candidate may use tags/extents plus a byte cursor, but retain starts, ends, text, trivia, or source bytes whenever diagnostics, formatting, source maps, or round-tripping consume them.

## Lexical identity

Prefer:

```text
bytes -> admitted token/name identity -> parser/semantic consumers
```

over repeated parse/normalize/hash of the same identity. The general authority/store decision belongs to [Canonical and derived data](../02-canonical-and-derived.md); explicit compact lexical lookup under the 512 profile belongs to the [PWP/512 router](25-pwp-512-profile.md).

## Pointerless parser scratch

Local parser scratch may use indices, append-only arrays, slices, or ordinary references whose lifetime ends with the operation. Long-lived pointer/child/builder questions route through [Pointerless compiler state](30-pointerless-state.md), which delegates to the general PWP owner.

## Direct emission

Test:

```text
parser -> required IR tables
```

instead of:

```text
ParserNode -> ASTNode -> SemanticNode -> IR
```

only when no required tooling/diagnostic/independent consumer needs the intermediate representation and producer complexity remains bounded. Pipeline stage existence is owned by [Pipeline elimination](10-pipeline-elimination.md).

## Acceptance

Preserve accepted/rejected input behavior, lexical state across blocks, required diagnostics/order, and fail-closed handling. Performance claims require matched phase/target evidence through the shared measurement route.
