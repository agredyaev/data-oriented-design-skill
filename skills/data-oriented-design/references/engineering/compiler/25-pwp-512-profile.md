# PWP / 512 Decision Router

Choose one question below. Each block contains decision trees, concrete before/after examples, rejection cases, and acceptance checks. Do not load the entire profile by default.

## Decision tree

```text
What decision must be made?
  owner / pointer / child / builder lifetime -> PWP retained-state block
  stored derived field / canonical authority -> Canonical and derived block
  batch width / backend / lexical masks -> batch and classification block
  scalar mask extraction -> compaction block
  operator / keyword dispatch -> lexical lookup block
  token positions / trivia / AST-to-IR -> token stream block
Question spans several blocks?
  inspect the primary cause first; load the next block only for its missing input.
No code, contract, or measurement selects a branch?
  identify the missing fact; do not choose a representation from the label PWP/512.
```

## Select a decision block

| Decision | Read | Minimum input |
| --- | --- | --- |
| Preserve 512 on another ISA; global vs on-demand classification; lane/batch carry | [Batch contract and classification](profile/10-batch-and-classification.md) | batch contract, grammar, target machines; timing for cost choices |
| Replace a trailing-zero loop with batch extraction | [Mask compaction](profile/20-mask-compaction.md) | mask/event ordering, output contract, profile or cost target |
| Replace operator branches or string-keyword searches | [Lexical lookup](profile/30-lexical-lookup.md) | complete grammar vocabulary, equality and longest-match rules |
| Drop start/end arrays, fold trivia, or emit IR directly | [Token stream and direct emission](profile/40-token-stream.md) | token consumers, source lifetime, diagnostic/trivia requirements |
| Replace pointers, flatten children, or discard builders | [PWP retained state](profile/50-pwp-retained-state.md) | owners/lifetimes, mutation, consumers, affected contract |
| Store/derive a retained field or choose canonical authority | [Canonical and derived](../02-canonical-and-derived.md) | retained inputs/version, authority, consumers, read budget |

PWP can be applied without a lexer. A selected 512-byte input block has 512 source bytes and 8×u64 per class mask; it is not a 512-bit instruction requirement.

Use [Route selection](../../modules.md#choose-and-switch-routes) for structural or profiler-led execution. Apply [Compiler validation](40-validation.md) when compiler behavior changes and [Workflow reporting](../../workflow.md#proportional-result-format) to the selected result only.
