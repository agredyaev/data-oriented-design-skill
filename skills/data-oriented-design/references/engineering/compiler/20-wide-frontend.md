# Wide Frontend and Direct Parsing

Use this block for tokenizer and parser-front-end costs. Typical signals are lexical classification, token extraction, parser staging, or repeated lexical decoding.

For a speed claim, measure the frontend cost before selecting SIMD or a custom token format. For a memory goal, establish retained-state evidence and the latency guardrail. A representation-removal change may proceed as structural simplification from code and behavior evidence, without a speed claim.

## Decision tree

```text
START
  |
  |-- Does this frontend representation/operation affect the requested result?
  |      |-- UNKNOWN -> inspect consumers for structural tasks; measure cost for cost claims.
  |      |-- NO -> STOP; do not optimize this block.
  |      '-- YES
  |
  |-- Which cause is demonstrated?
         |
         |-- branch-per-byte/item classification
         |      -> TEST batch classification into masks/bitsets.
         |
         |-- one-by-one extraction from a hot mask
         |      -> TEST batch/SWAR/vector compaction.
         |
         |-- redundant token source data
         |      -> REDUCE to the minimum parser contract.
         |
         |-- repeated keyword/name decode
         |      -> DECODE/RESOLVE once and carry typed identity.
         |
         |-- staging tree immediately lowered with no independent consumer
         |      -> TEST direct emission; REMOVE staging only after validation.
         |
         |-- none of the above
         |      -> KEEP current frontend; diagnose another cause.
         |
         '-- evidence missing for the suspected cause
                -> inspect semantic facts or MEASURE the missing cost before adopting.
```

Any transformation that changes lexical or parsing semantics must pass the semantic-equivalence and fail-closed gates in `40-validation.md`.

## 1. Classify batches only after diagnosis selects lexical scanning

A scalar branch-per-byte shape is:

```text
byte -> classify -> branch -> maybe token -> advance
```

A wide candidate is:

```text
N source bytes
    ↓
wide classification
    ↓
class masks / bitsets
    ↓
mask algebra
    ↓
event boundaries for the batch
```

Useful logical masks can include:

```text
word_char
whitespace
quote
comment
punctuation
operator
escape
newline
```

For a word mask, boundaries can be derived from transitions:

```text
start_mask =
    word AND NOT(previous_word_shifted)

end_mask =
    word AND NOT(next_word_shifted)
```

This is a method, not a required instruction set.

## 2. Extract selected events in batches when extraction is hot

This form is still one event per dependency chain:

```text
while mask != 0:
    bit = trailing_zero(mask)
    emit(bit)
    mask &= mask - 1
```

When matched profiling attributes target cost to this loop, test:

```text
selected mask
    ↓
compress lane indices
    ↓
packed selected positions
```

Use vector, SWAR, BMI-style, or scalar fallback techniques as appropriate. Keep the parser-facing result independent of the backend when practical.

Keep a more complex compaction scheme only if it passes the declared acceptance rule.

A separate structural simplification can also justify it. Name the removed structure explicitly.

## 3. Keep a stable parser-facing batch contract

The generic methodology leaves batch width to the task. If the task selects the 512-byte contract, use the [PWP/512-byte profile](25-pwp-512-profile.md); preserve that logical width across backend changes. That profile also covers on-demand classification and compact operator/keyword lookup.

A concrete implementation may use a fixed byte block and several machine-word bitsets. The methodology requires only:

- the classifier and backend can change without forcing parser redesign when practical;
- boundaries between batches preserve lexical state;
- strings, comments, escapes, and other cross-block constructs are correct;
- a portable fallback exists when the product requires it.

Do not encode one benchmark's vector width into the architecture without a target requirement.

## 4. Store the minimum token information

Avoid redundant token state such as:

```text
Token {
    kind
    start
    end
    copied_text
}
```

when source bytes remain available and one field can be derived from another.

A compact parser contract can be:

```text
tags[]
extents[]
leading_bytes
```

with parser state:

```text
token_ix
byte_cursor
```

and advancement:

```text
byte_cursor += extents[token_ix]
token_ix += 1
```

Keep explicit starts, ends, or copied text only for a named consumer whose access pattern justifies them.

## 5. Do not persist insignificant lexical objects without a consumer

Whitespace and comments should not automatically become persistent token objects.

When downstream semantics do not consume them, fold their byte contribution into extents/progress metadata.

Keep exact source bytes separately when diagnostics, formatting, source maps, or round-tripping require them.

Rule:

> No downstream consumer means no persistent representation.

## 6. Decode lexical identity once

Prefer:

```text
bytes -> typed token/name identity -> direct dispatch
```

over:

```text
bytes -> slice/string -> compare/hash/normalize repeatedly
```

Carry the typed result forward while its identity remains valid.

If propagation versus recomputation is not decided by the contract, route the trade-off to Pointerless state and measurement. Do not guess.

## 7. Keep parser state pointerless when the grammar permits it

Prefer local or append-only scratch:

```text
token_ix
byte_cursor
frame_tags[]
frame_data[]
stack_top
```

and typed outputs such as:

```text
InstIx
ExprIx
StringIx
RelationIx
```

Use a fixed parser stack only when the depth bound is part of the accepted-input contract or is safely enforced.

## 8. Emit IR directly when syntax staging has no independent value

Prefer:

```text
parser
    ↓
IR tables
```

over:

```text
ParserNode
    ↓
ASTNode
    ↓
SemanticNode
    ↓
IR
```

when the parser already has enough information and no required consumer needs the intermediate node.

Do not force direct emission when:

- tooling or diagnostics require the syntax representation;
- multiple independent consumers use it;
- direct emission complicates the producer more than one bounded packing pass;
- matched measurement shows that the staging form has lower total cost under the declared acceptance rule.

## Acceptance

A wide frontend change is accepted only when:

- accepted and rejected inputs remain correct;
- cross-block lexical state is covered;
- unsupported syntax fails explicitly;
- cost claims have the predicted causal evidence and pass the declared target;
- a structural-only change removes a named unnecessary representation or pass;
- required memory/latency guardrails pass;
- the target frontend phase improves if phase speed is claimed;
- end-to-end performance is reported separately.

