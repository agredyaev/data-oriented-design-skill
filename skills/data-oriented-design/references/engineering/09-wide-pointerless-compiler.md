# Compiler / Frontend DOD Router

Use this file only to choose the compiler-specific block. Do not read every compiler block by default.

The compiler methodology has one top-level rule:

> Minimize persistent representations and repeated passes. Minimize repeated decoding and unpredictable access on the path to the required semantic result.

## Choose one primary block

| Signal | Read |
| --- | --- |
| Too many AST/IR/lowering stages, duplicate semantic layers, legacy parser path, repeated whole-pipeline passes | [Pipeline elimination](compiler/10-pipeline-elimination.md) |
| Tokenizer/lexer cost, byte-at-a-time classification, mask extraction, compact tokens, direct parser emission | [Wide frontend](compiler/20-wide-frontend.md) |
| Pointer graphs, nested child containers, string ownership, repeated identity resolution, builder→frozen state, hot/cold layout | [Pointerless state](compiler/30-pointerless-state.md) |
| Correctness equivalence, benchmark representativeness, fail-closed behavior, acceptance or rejection of an optimization | [Validation](compiler/40-validation.md) |

Start with one block. Load a second block only when the finding crosses that boundary.

## Decision language

Use these terms consistently:

- `REQUIRED` — the contract or a named consumer requires it.
- `MEASURED` — matched evidence shows the cost or benefit.
- `WITHIN BUDGET` — the path satisfies a declared bound.
- `MEASURE` — evidence needed to choose the branch is missing.

Do not make qualitative cost judgments from intuition. If no contract bound or measurement decides a branch, choose `MEASURE`.

## Route broad redesigns

For a full compiler/frontend redesign:

1. read [Structural analysis](00-structural-analysis.md);
2. read [Pipeline elimination](compiler/10-pipeline-elimination.md);
3. load one additional compiler block only for the first accepted structural candidate.

Do not start with SIMD, SoA, CSR, interning, or packing before the current and candidate pipelines exist.

## Shared decision order

Use this order unless a contract or measurement proves another order:

```text
remove unnecessary stage or representation
    ↓
remove repeated pass / parse / resolve work
    ↓
localize temporary state
    ↓
flatten long-lived identity and relations
    ↓
reduce hot data touched
    ↓
optimize lexical scanning / extraction
    ↓
micro-optimize instructions
```

## Boundary between blocks

- **Pipeline elimination** decides whether a representation or stage should exist.
- **Wide frontend** decides how source bytes become the minimum parser contract.
- **Pointerless state** decides how long-lived compiler data is represented.
- **Validation** decides whether the redesign is correct and whether a claimed improvement is proven.

Do not use a lower-level block to justify a higher-level stage. First establish that the stage must exist. Example: do not optimize AST layout until Pipeline elimination identifies a required AST consumer.

## General rules still apply

Use the existing general DOD packs instead of duplicating them:

| Need | Route |
| --- | --- |
| exact typed-ID / flat-relation rules | `../../performance/20-identity-and-relations.md` |
| exact SoA / side-storage / packing rules | `../../performance/21-layout-and-encoding.md` |
| repeated-work / fusion / blocking rules | `../../performance/30-work-and-access.md` |
| benchmark methodology | `../../performance/00-diagnosis.md`, then `../../performance/01-measurement.md` |
| correctness boundaries | `06-correctness-boundaries.md` |

## Stop rule

If the current question can be answered from the selected block, stop loading references.

If two consecutive local compiler changes fail the declared target acceptance rule, stop local tuning. Return to Structural analysis and Pipeline elimination.
