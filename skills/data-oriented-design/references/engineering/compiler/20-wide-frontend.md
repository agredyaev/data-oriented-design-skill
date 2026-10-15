# Wide Frontend and Direct Parsing

Use this block when tokenization, lexical classification, token extraction, parser staging, or repeated lexical decoding is measured as part of the target frontend cost, exceeds a declared budget, or is the structural cause under review.

Do not introduce SIMD or a custom token format before the frontend cost is measured, unless the structural change removes a representation without making a performance claim.

## Decision tree

```text
START
  |
  |-- Is tokenization / lexical scanning a measured contributor to the target or over budget?
  |      |-- NO -> do not optimize it.
  |      |-- UNKNOWN -> MEASURE.
  |      '-- YES
  |
  |-- Is input classified one byte/item at a time with branch-per-item work?
  |      |-- YES -> test batch classification into masks/bitsets.
  |      '-- NO -> keep current scan unless another measured cause exists.
  |
  |-- Does profiling show one-by-one mask extraction contributes to the target cost?
  |      |-- UNKNOWN -> MEASURE.
  |      |-- YES -> test batch/SWAR/vector compaction.
  |      '-- NO
  |
  |-- Does the token stream retain redundant source data?
  |      |-- YES -> reduce to the minimum parser contract.
  |      '-- NO
  |
  |-- Are keywords/names decoded repeatedly?
  |      |-- YES -> decode/resolve once and carry typed identity.
  |      '-- NO
  |
  |-- Does parsing build a tree only to lower it immediately?
         |-- YES -> direct emit or minimal staging form.
         '-- NO -> keep the independently consumed representation.
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

Do not keep a more complex compaction scheme unless it passes the declared acceptance rule on the representative workload or removes required complexity elsewhere.

## 3. Keep a stable parser-facing batch contract

The batch width is an implementation choice.

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

If retaining the typed result costs more than intentional recomputation, route that decision to the pointerless-state and measurement blocks instead of applying this rule blindly.

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
- the predicted physical metric changes;
- the target frontend phase improves if speed is claimed;
- end-to-end performance is reported separately.
