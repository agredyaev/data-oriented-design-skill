# Token Stream and Direct Emission Decisions

## Decision tree: positions versus extents

```text
Do consumers need random token access or exact absolute positions?
  NO -> candidate: tags[] + variable-width extents + sequential byte cursor.
  YES -> can their positions be derived within the declared read budget?
          YES -> use retained source plus a measured sparse index if needed.
          NO -> KEEP the required position fields/index.
Will the source remain alive until the last lexical/diagnostic derivation?
  NO -> KEEP sufficient owned token text/positions or extend source ownership.
Is token extent fully defined, including leading/trailing trivia and EOF?
  NO -> define the encoding before removing start/end arrays.
Does the new representation reproduce all required token spans and errors?
  NO -> REJECT replacement.
```

### Example: a precise compact stream

Source is `  a + b`, length 7 bytes. Assume this grammar does not consume spaces. Define extent = token bytes plus following discarded spaces. Store:

- `leading_bytes = 2`;
- `tags = [identifier, plus, identifier]`;
- `extents = [2,2,1]`.

The cursor starts at 2, then advances to 4, 6, and 7. These are token starts and final source end. The lexeme of `a` ends at 3, not 4: derive that end from retained source/lexical rules or retain its length if a required consumer cannot derive it within budget. Never equate extent-with-trivia to lexeme length.

For an optional one-byte length format, reserve zero as an escape only when zero-length tokens cannot occur. Example: extent 500 becomes `[0,244,1,0,0]` with an explicitly little-endian u32 escape. Check truncation, overflow, valid bounds, and cursor progress. If zero-length events exist, choose another encoding.

For encoded extents, keep a decoding cursor distinct from the token index: this escape consumes five encoded bytes but advances one token and 500 source bytes. Do not index the encoded byte stream by token index as if every extent occupied one byte.

## Decision tree: fold whitespace and comments

```text
Does any current consumer require the trivia itself?
  YES -> retain its source/range or explicit token as required.
  NO -> does trivia affect grammar state, separators, directives, or diagnostics?
          YES -> process that effect before dropping persistent trivia objects.
          NO -> fold its byte contribution into the declared extent contract.
Can the consumer recover required source positions afterward?
  NO -> KEEP the missing metadata/source lifetime.
Does folding preserve token boundaries, error location, and final cursor?
  NO -> REJECT encoding.
```

### Example: ordinary space versus a required comment

A parser-only consumer of `a + b` can omit space tokens after preserving the byte extents. A documentation extractor consuming `/// description` needs that comment's content/range. Do not discard it because the parser ignores it. If the grammar treats a newline as a terminator, process that event before folding the newline bytes.

## Decision tree: remove staging AST and emit directly

```text
Is the staging representation consumed after lowering by an independent consumer?
  YES -> KEEP the representation required by that consumer.
  UNKNOWN -> inspect consumers; do not delete it.
Does it add a required semantic/diagnostic/ordering boundary?
  YES -> preserve that boundary, even if its implementation changes.
Can the producer emit the required target without adding a rejected cost/invariant?
  UNKNOWN -> prototype the affected path and compare the declared costs.
  NO -> KEEP one bounded staging/packing form.
  YES -> candidate: producer -> required IR; remove the superseded staging form.
Do accepted/rejected inputs, diagnostics, ordering, and required recovery match?
  NO -> REJECT replacement.
```

### Example: two different AST decisions

`parse -> Ast -> ExprRows`, where only lowering reads `Ast`: emit `ExprRows` directly if the parser has the required information and verification passes. Remove the old production path; an independent test oracle may remain.

`parse -> Ast -> ExprRows`, where formatter and refactoring tools also read source-preserving `Ast`: keep their required syntax representation. “Direct IR is faster” does not remove those product consumers.

Use [Pipeline elimination](../10-pipeline-elimination.md) for cross-stage redesign and [Compiler validation](../40-validation.md) for acceptance. A smaller stream is a storage result until matched timing supports a speed claim.
