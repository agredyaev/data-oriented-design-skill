# Wide, Pointerless Compiler Design

Use this module for compiler, parser, tokenizer, DSL frontend, query frontend, IR-lowering, or similar pipelines where the dominant path transforms source bytes into semantic or canonical state.

This module combines two concerns:

- wide classification and token-boundary discovery over batches of source bytes;
- pointerless/data-oriented compiler state built from dense arrays, typed IDs, offsets, ranges, CSR, sidecars, and byte pools.

Do not use this module as permission to add SIMD, custom token formats, or index-based IR without evidence. Start with the top-down structural workflow and keep only transformations that preserve the contract and improve the intended cost or materially simplify the architecture.

## Core objective

The target is not "use SIMD" or "remove pointers" in isolation.

The target is:

> Transform input into the final semantic representation using the fewest necessary representations, passes, allocations, decodes, and unpredictable memory accesses.

Preferred shape when the grammar and product contract permit it:

```text
source bytes
    ↓
wide classification
    ↓
bit masks
    ↓
mask algebra
    ↓
batch compaction
    ↓
compact token stream
    ↓
index-based parser
    ↓
direct IR emission
    ↓
semantic processing over dense arrays
    ↓
final canonical representation
```

Suspicious shape:

```text
source bytes
    ↓
character tokenizer
    ↓
Token objects
    ↓
parser objects
    ↓
AST object graph
    ↓
recursive traversal
    ↓
second semantic graph
    ↓
IR
    ↓
more graph conversion
    ↓
final representation
```

The second shape is not wrong by definition. Every intermediate representation must, however, justify its consumers, lifetime, and information content.

## 1. Start from the whole process

Before changing a tokenizer, parser function, node type, or instruction layout, draw the complete transformation pipeline.

For every stage record:

```text
input type
output type
information added
information discarded
retained representation created
consumer(s)
full-pass count
allocation count
bytes copied
parse/decode count
hash/normalize count
```

Ask:

```text
Why does this representation exist?
Who consumes it after the next stage?
How many times is the same information decoded?
How many times are names normalized or hashed?
How many representations of the same entity coexist?
Can producer A emit directly into consumer B's representation?
```

Do not optimize one function before this map exists for the dominant path.

## 2. Eliminate representations before local optimization

Use this priority unless a contract or measurement proves a different order:

```text
eliminate stage
    >
eliminate repeated pass/work
    >
eliminate allocation
    >
eliminate indirection
    >
improve layout
    >
vectorize
    >
micro-optimize instructions
```

A representation that is built, traversed once, lowered, and destroyed is a removal candidate. A 2x faster traversal is often less valuable than removing both construction and traversal.

## 3. Decide whether an intermediate representation should exist

Use this decision tree:

```text
Stage A produces representation R
and Stage B consumes R
        │
        ▼
Is R retained after B?
   /             \
 yes              no
  │                │
  ▼                ▼
Does R serve       Can A emit directly
multiple independent into B's representation?
consumers?           /          \
 /      \           yes          no
yes      no           │            │
 │        │            ▼            ▼
KEEP   challenge     REMOVE R    keep the smallest
       R                         staging form
```

Keep an AST, parse tree, or staging IR when it has independent consumers, source-preserving requirements, tooling/debugging contracts, or when direct emission would make the producer materially more complex than one bounded packing pass. Otherwise remove it.

## 4. Wide tokenization: classify batches, not individual bytes

When tokenization is a material frontend cost, test a batch-classification design.

Instead of:

```text
byte → classify → branch → maybe token → advance
```

prefer a parser-facing model such as:

```text
N source bytes
    ↓
wide character classification
    ↓
bitsets for classes
    ↓
mask algebra
    ↓
all token/event boundaries for the batch
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

Boundaries should be derived from transitions in masks when possible. For a word-class bitset, starts and ends are bulk transition operations rather than one branch per character.

Conceptually:

```text
start_mask =
    word
    AND NOT(previous_word_shifted)

end_mask =
    word
    AND NOT(next_word_shifted)
```

This computes all word-run boundaries for the batch together.

The exact vector width is an implementation choice. Do not hard-code a width from an example unless the backend, alignment, fallback path, and measurements justify it.

## 5. Batch extraction instead of branch-per-event extraction

A bitset scan like this is still one event per loop iteration:

```text
while mask != 0:
    bit = trailing_zero(mask)
    emit(bit)
    mask &= mask - 1
```

It may be adequate, but when extraction is hot, test batch/SWAR/vector compaction:

```text
selected_mask
    ↓
compress lane indices
    ↓
packed selected positions
```

The design goal is that token boundaries are produced as bulk data, not rediscovered one token at a time.

Accept batch extraction only if it improves the representative frontend workload or materially simplifies a downstream contract.

## 6. Keep a stable frontend batch contract

A project may choose a fixed frontend block such as 512 bytes when that maps well to its target implementation, for example:

```text
512 bytes
    ↓
classifier
    ↓
8 × u64 masks
    ↓
mask algebra
    ↓
batch compaction
    ↓
tag[] + extent[]
```

Treat `512 bytes`, `@Vector(512, u8)`, and `8 × u64` as a project-specific realization, not a universal DOD rule.

For the Duck Mesh reference design, preserve the concrete mapping:

```text
@Vector(512, u8)
        ↓
512 character lanes
        ↓
@Vector(8, u64)
        ↓
8 × 64-bit classification bitstrings
```

The implementation backend may use:

```text
AVX-512
NEON
SVE
BMI2/SWAR
portable fallback
```

The important invariant is this:

> Backend-specific SIMD/SWAR implementations may differ, but the parser-facing token contract should remain stable unless changing it has an explicit measured or semantic benefit.

Provide a portable fallback when the product must run on targets without the preferred vector instructions.

## 7. Store the minimum token information

Do not store redundant token data by default.

Suspicious:

```text
Token {
    kind
    start
    end
    copied_text
}
```

If source bytes remain available and `end = start + length`, prefer a compact form such as:

```text
tags[]
extents[]
leading_bytes
```

or another representation that lets the parser maintain:

```text
token_ix
byte_cursor
```

with:

```text
byte_cursor += extents[token_ix]
token_ix += 1
```

Store explicit starts/ends only when their consumers and access frequency justify the bytes.

## 8. Fold insignificant bytes into progress metadata

Whitespace and comments should not automatically become persistent token objects.

When they are not semantic consumers, encode their byte contribution in token progress/extents or equivalent metadata:

```text
SELECT   x   /* comment */   FROM t
```

can become conceptually:

```text
tag[]    = [SELECT, IDENT, FROM, IDENT]
extent[] = [bytes-to-next-semantic-token ...]
```

Keep exact source bytes separately if diagnostics, formatting, source maps, or round-tripping require them.

Rule:

> If information has no consumer after a stage, do not give it a persistent representation.

## 9. Decode keywords and lexical identity once

Do not repeatedly compare source slices with keyword strings in the parser if tokenization can classify the keyword once.

Prefer:

```text
bytes → TokenKind::Select → direct parser dispatch
```

instead of:

```text
bytes → string/slice → compare/hash/normalize repeatedly
```

General rule:

> Decode or admit information once, then carry the typed result forward for as long as the contract permits.

This also applies to normalized names, relation identity, identifiers, and function/operator classes.

## 10. Use pointerless parser state

The parser should not require a heap object graph merely to express temporary syntax state.

Prefer bounded or append-only scratch such as:

```text
token_ix
byte_cursor
frame_tags[]
frame_data[]
stack_top
```

and outputs such as:

```text
InstIx
ExprIx
StringIx
RelationIx
```

Relationships in retained parser/IR state should normally be integer IDs, offsets, or ranges rather than memory addresses.

A bounded fixed stack is appropriate when grammar depth has an enforced limit. Use growable scratch when the bound is not known or a fixed limit would change accepted input.

## 11. Emit IR directly when syntax staging adds no independent value

If the parser has enough information to produce the semantic/IR instruction and no independent consumer needs an AST node, emit the IR directly.

Instead of:

```text
ParserNode
    ↓
ASTNode
    ↓
SemanticNode
    ↓
IR
```

prefer:

```text
parser
    ↓
IR instruction tables
```

For an expression:

```text
lhs_ix = ...
rhs_ix = ...

tags[new]    = Binary
data_a[new]  = lhs_ix
data_b[new]  = rhs_ix
payload[new] = operator
```

Do not force direct emission when the AST has required independent consumers or when a simple producer representation plus one linear packing pass is cheaper overall.

## 12. Programming Without Pointers: long-lived relation rule

For long-lived compiler relationships, prefer compact typed handles, indexes, offsets, and ranges.

Prefer:

```text
InstIx
ExprIx
StringIx
RelationIx
ModelIx
ColumnIx
```

instead of retained graph edges based on:

```text
&Node
Box<Node>
Arc<Node>
Vec<Node*>
owned String per entity
```

Pointers, references, `Box`, `Vec`, and arenas are still valid implementation tools. The rule concerns persistent semantic identity and graph topology, not a blanket ban on pointer syntax.

## 13. Decide pointer/object versus index explicitly

Use this decision:

```text
Does the value need independent lifetime/ownership?
        │
   ┌────┴────┐
  yes        no
   │          │
   ▼          ▼
Is stable   dense typed ID /
address     offset / range
required?
  │
 ┌┴─┐
yes no
 │   │
KEEP dense root-owned
pointer storage + ID
```

If a pointer remains, state the specific ownership, address-stability, FFI, concurrency, or lifetime requirement that requires it.

## 14. Flatten nested containers into ranges/CSR

Treat repeated nested containers such as `Vec<Vec<T>>` or per-node child vectors as candidates for flat storage:

```text
offsets[]
values[]
```

For row `r`:

```text
values[offsets[r] .. offsets[r + 1]]
```

Expected benefits can include fewer allocations, smaller relationships, predictable scans, serialization, and bounds validation.

Do not use CSR when mutation patterns or very sparse/random updates make another structure better.

## 15. Pool repeated or numerous strings

Large compiler state should not default to one heap allocation per retained string.

Prefer:

```text
string_bytes[]
string_offsets[]
name_ids[]
```

or an intern pool when deduplication is justified.

Keep the distinction between:

- byte pooling: fewer allocations and compact references;
- interning: canonical identity and deduplication, with lookup cost.

Do not pay interning/hash cost when values are nearly all unique and the workload does not benefit.

## 16. Resolve logical identity once

Do not normalize/hash/resolve the same logical name in multiple later phases when a stable typed identity can be propagated.

Prefer:

```text
source name
    ↓
resolve once
    ↓
RelationIx
    ├── dependency analysis
    ├── semantic analysis
    └── lineage
```

Decision:

```text
Has this logical identity already been resolved?
        │
     ┌──┴──┐
    yes    no
     │      │
carry ID  resolve once,
forward   then carry ID
```

An intentional reparse/re-resolve is valid when retaining the previous representation would cost more memory or complexity than recomputation. State that trade-off explicitly.

## 17. Separate builder and frozen representations

`Vec<T>` is not a DOD violation. Unknown cardinality often requires growable builder storage.

Use a lifecycle such as:

```text
BUILD
Vec<T> / builder maps / parser scratch
    ↓ freeze or pack
READ
Box<[T]> / exact immutable arrays / compact tables
```

After freeze, remove unnecessary growth capacity, mutation machinery, maps, temporary ownership wrappers, and builder-only metadata when the runtime/semantic contract no longer needs them.

## 18. Choose fixed array, exact allocation, or growable builder from cardinality

Decision:

```text
Size known at compile time?
  ├─ yes → [T; N]
  └─ no
      │
      ├─ exact size known before write → exact allocation / boxed slice
      └─ unknown while building → Vec<T>, then freeze if useful
```

Use bounded fixed scratch only when the bound is part of the accepted-input contract or safely enforced.

## 19. Reject benchmark-only optimization layers

An optimization that depends on repeated synthetic structure is not a general architectural win unless that repetition is demonstrated in representative production data.

Decision:

```text
Does the optimization exploit repeated workload shape?
        │
      yes
        │
Is that repetition proven in representative data?
   ├─ yes → measure carefully
   └─ no  → remove/reject as benchmark specialization
```

Do not hide parsing, semantic work, or allocation behind templates/caches that exist only because the benchmark generator repeats shapes.

## 20. Keep one canonical production path

After replacement behavior is validated, remove the superseded production path unless the product explicitly requires both.

Avoid indefinite production states such as:

```text
new parser
old parser
fallback parser
AST parser for edge cases
direct parser for normal cases
```

A legacy parser may temporarily remain as an independent test oracle. It should not remain an alternate production authority once equivalence and migration are complete.

The Duck Mesh canonical production path from the source methodology is explicitly one production path:

```text
ONE production path

SQL
→ direct frontend
→ MeshIR
→ MeshSema
→ CanonicalMesh
```

## 21. Delete legacy code by observable responsibility

Use this test:

```text
If I delete this layer, what required observable behavior disappears?
```

If the answer is `none`, delete it or merge the unique behavior into the canonical path.

Decision:

```text
Reachable from canonical production entry point?
   ├─ yes → does it provide unique required behavior?
   │          ├─ yes → keep/merge responsibility
   │          └─ no  → delete
   └─ no  → required public compatibility API?
              ├─ yes → migrate API, then delete implementation
              └─ no  → delete
```

## 22. Detect duplicate semantic layers

A layer is suspicious when its input and output contain approximately the same semantic information.

Examples:

```text
AST Expr → IR Expr
CatalogRelation → SourceMetadataRelation
ParserNode → SemanticNode
```

Compare fields/meaning, not type names. If the downstream form does not add information and the producer can emit the target layout directly, remove the duplicate layer.

## 23. Decide whether a layer adds information or only changes layout

Use this decision:

```text
Does layer L add information required downstream?
  ├─ yes → does a distinct consumer/lifetime justify L?
  │          ├─ yes → keep
  │          └─ no  → challenge/fuse
  └─ no
      │
      ├─ layout-only transformation?
      │     ├─ producer can emit target layout → remove L
      │     └─ producer would become materially worse → keep one bounded packing pass
      └─ no → delete L
```

A one-time packing representation is acceptable when its cost is lower than the aggregate savings across later scans.

## 24. Separate hot semantic state from cold metadata

Hot passes should touch only data required by those passes.

Prefer:

```text
HOT
expr_tags[]
expr_types[]
expr_a[]
expr_b[]

COLD
source_spans[]
diagnostic strings[]
rare payload[]
```

Source location, pretty names, diagnostics, debug metadata, and rare payload should not inflate every hot record unless measured access patterns require co-location.

## 25. Fuse semantic passes when the same data is already hot

When several passes traverse the same nodes in the same order and later work does not require unavailable global results, test fusion:

```text
resolve
+ type
+ nullability
+ expression construction
+ lineage
```

Decision:

```text
Same nodes in same order?
  ├─ no → keep separate
  └─ yes
      │
      ├─ later pass requires results unavailable until a full boundary completes?
      │     ├─ yes → keep boundary
      │     └─ no  → test fusion
```

Do not fuse merely to reduce the number of functions. Preserve error ordering, fixpoint semantics, global barriers, and correctness boundaries.

## 26. Measure compiler stages independently

For a compiler/frontend pipeline, record separate phase times for relevant stages, for example:

```text
admission
source loading
metadata/header parse
tokenization
parsing/IR emission
dependency graph
semantic evaluation
lineage
freeze/packing
serialization
```

Use representative workloads. Report improvements only against a baseline that exercises the same real work.

An optimization that reduces storage but leaves wall time unchanged is a memory/storage win, not a CPU win.

Keep the source methodology's measured frontend example as a reference for what stage-level evidence looks like:

```text
old AST frontend:
MeshIR ≈ 821 ms

direct parser with intermediate positions:
MeshIR ≈ 215–228 ms

tag + extent after removing synthetic template reuse:
MeshIR ≈ 226 ms

821 / 226 ≈ 3.6×
```

The important comparison is the last one because it does not depend on synthetic shape caching. These numbers are project evidence, not universal expected gains.

## 27. Keep an optimization only after causal validation

Use this gate:

```text
correctness unchanged?
  └─ no → reject
  └─ yes
      ↓
representative workload improves?
  ├─ yes → continue
  └─ no → does architecture materially simplify or memory materially improve?
             ├─ no → reject/revert
             └─ yes → classify honestly; do not claim speed
      ↓
adds a new representation/layer?
  ├─ no → keep if evidence supports it
  └─ yes → require a large/general benefit and an explicit invariant
```

Do not accumulate permanent performance bureaucracy from small local wins.

## 28. Compare semantic outputs when representations change

When replacing a parser, AST, lowering path, or IR layout, compare externally meaningful semantics rather than internal object shape.

Candidate invariants can include:

```text
same accepted/rejected inputs
same relation count
same expression count
same row count
same outputs
same dependencies
same value lineage
same row lineage
same canonical hashes where contractual
same ordering where observable
same diagnostics/error class where contractual
```

Instruction numbers or traversal order need not match unless they are observable or part of a persistence/wire contract.

An old implementation may serve as a temporary oracle if it is independent enough to detect regressions.

## 29. Fail closed on unsupported syntax or semantics

A faster direct parser must not guess when it reaches unsupported syntax.

Prefer:

```text
unknown/unsupported syntax
    ↓
explicit Unsupported / Parse / Semantic error
```

instead of:

```text
unknown syntax
    ↓
guess or reinterpret
    ↓
continue with possibly wrong semantics
```

This rule is mandatory when replacing a mature generic parser with a narrower direct frontend.

## 30. Complete decision process

Use this sequence for a wide/pointerless compiler redesign:

```text
START
  ↓
draw complete typed dataflow
  ↓
list every retained representation
  ↓
does each representation add required downstream information?
  ├─ no  → remove/fuse/derive/localize
  └─ yes → continue
  ↓
are long-lived relationships pointer/key rich?
  ├─ yes → typed IDs / offsets / ranges / CSR
  └─ no  → continue
  ↓
are strings individually owned or repeatedly resolved?
  ├─ yes → byte pool / intern / resolve once
  └─ no  → continue
  ↓
is hot source scanning one item at a time?
  ├─ yes → test wide masks / bitsets
  └─ no  → continue
  ↓
are selected events extracted one-by-one from masks?
  ├─ yes → test batch compaction
  └─ no  → continue
  ↓
does parser build a staging tree only to lower it immediately?
  ├─ yes → direct emit or one minimal staging form
  └─ no  → keep justified consumer representation
  ↓
does a superseded production path remain?
  ├─ yes → migrate/delete; oracle only if needed
  └─ no  → continue
  ↓
correctness gate
  ↓
representative benchmark / memory gate
  ↓
architecture simpler or target materially better?
  ├─ yes → KEEP
  └─ no  → require a large proven compensating benefit or reject
```

## 31. Reference target architecture

A representative target for a SQL/compiler frontend is:

```text
                     source bytes
                         │
                         ▼
              ┌─────────────────────┐
              │ wide classifier     │
              │ class bitsets       │
              └─────────┬───────────┘
                        │
                        ▼
              ┌─────────────────────┐
              │ mask algebra        │
              │ boundaries/comments│
              │ quotes/operators    │
              └─────────┬───────────┘
                        │
                        ▼
              ┌─────────────────────┐
              │ batch compaction    │
              └─────────┬───────────┘
                        │
                        ▼
              ┌─────────────────────┐
              │ compact tokens      │
              │ tags[] / extents[] │
              └─────────┬───────────┘
                        │ token_ix + byte_cursor
                        ▼
              ┌─────────────────────┐
              │ pointerless parser  │
              │ bounded/local scratch│
              └─────────┬───────────┘
                        │ direct emit
                        ▼
              ┌─────────────────────┐
              │ semantic IR         │
              │ typed IDs + SoA     │
              │ sidecars + pools    │
              └─────────┬───────────┘
                        │
                        ▼
              ┌─────────────────────┐
              │ dependency CSR      │
              └─────────┬───────────┘
                        │
                        ▼
              ┌─────────────────────┐
              │ fused semantic work │
              │ over dense arrays   │
              └─────────┬───────────┘
                        │
                        ▼
                canonical result
```

For Duck Mesh, the source methodology defines the more concrete target below. Keep this as a project-specific realization of the generic architecture above:

```text
                       SQL bytes
                           │
                           ▼
              ┌───────────────────────┐
              │ 512-byte classifier   │
              │ 8 × u64 bitstrings    │
              └──────────┬────────────┘
                         │
                         ▼
              ┌───────────────────────┐
              │ mask algebra          │
              │ words / punctuation   │
              │ comments / quotes     │
              │ boundaries            │
              └──────────┬────────────┘
                         │
                         ▼
              ┌───────────────────────┐
              │ batch compression     │
              └──────────┬────────────┘
                         │
                         ▼
              ┌───────────────────────┐
              │ token stream          │
              │ tags[]                │
              │ extents[]             │
              │ leading_bytes         │
              └──────────┬────────────┘
                         │
                 token_ix + byte_cursor
                         │
                         ▼
              ┌───────────────────────┐
              │ pointerless parser    │
              │ bounded scratch       │
              │ token-index ranges    │
              └──────────┬────────────┘
                         │
                    direct emit
                         │
                         ▼
              ┌───────────────────────┐
              │ MeshIR SoA            │
              │ tags[]                │
              │ data_a[]              │
              │ data_b[]              │
              │ payload[]             │
              │ extra[]               │
              │ string_bytes[]        │
              │ model_ranges[]        │
              │ model_roots[]         │
              └──────────┬────────────┘
                         │
                         ▼
              ┌───────────────────────┐
              │ dependency CSR        │
              └──────────┬────────────┘
                         │
                         ▼
              ┌───────────────────────┐
              │ fused MeshSema        │
              │ dense scopes          │
              │ type inference        │
              │ function resolution   │
              │ lineage               │
              └──────────┬────────────┘
                         │
                         ▼
                   CanonicalMesh
```

Central invariant:

> Every arrow must justify the representation on its right. If the representation adds no required information, independent consumer, or measured benefit, remove it or fuse the stages.

## Interaction with the rest of this skill

Use this module as the compiler-specific route. Reuse the existing general rules rather than duplicating their acceptance logic:

| Compiler concern | General route |
| --- | --- |
| eliminate stages / duplicate representations | `engineering/00-structural-analysis.md`, `engineering/02-canonical-and-derived.md` |
| typed handles, flat relations, string IDs | `performance/20-identity-and-relations.md` |
| SoA, hot/cold, sidecars, builder→frozen layout | `performance/21-layout-and-encoding.md` |
| repeated work, pass fusion, blocking, clustering | `performance/30-work-and-access.md` |
| benchmark and causal acceptance | `performance/00-diagnosis.md`, `performance/01-measurement.md`, `performance/10-foundation.md` |
| correctness boundaries and test oracle | `engineering/06-correctness-boundaries.md` |

Do not load all those files automatically. Start with this module plus structural analysis for a redesign, then load only the rule pack required by the diagnosed issue.

## Coverage checklist for this module

The module intentionally covers every topic in the Wide, Pointerless Compiler Design methodology:

| Source topic | Covered here |
| --- | --- |
| whole-process analysis | §1 |
| representation elimination priority | §2 |
| intermediate-representation decision tree | §3 |
| wide bitset tokenization | §4 |
| batch mask extraction/compaction | §5 |
| 512-byte frontend contract | §6, generalized with project-specific width |
| minimal token representation | §7 |
| insignificant bytes folded into extents/progress | §8 |
| keyword decode once | §9 |
| pointerless parsing | §10 |
| direct IR emission | §11 |
| Programming Without Pointers rule | §12 |
| pointer/object versus index decision | §13 |
| flat arrays / CSR | §14 |
| string pools | §15 |
| resolve identity once | §16 |
| builder versus frozen representation | §17 |
| fixed/exact/growable storage decision | §18 |
| reject benchmark-only optimization layers | §19 |
| one canonical production path | §20 |
| delete legacy code decision | §21 |
| duplicate-layer detector | §22 |
| real versus layout-only layer decision | §23 |
| hot/cold split | §24 |
| fused semantic passes | §25 |
| stage-level performance methodology | §26 |
| keep/reject optimization decision | §27 |
| correctness gates for representation changes | §28 |
| fail closed | §29 |
| complete decision process | §30 |
| target architecture | §31 |

The core objective and preferred pipeline are stated before §1. No source topic is intentionally omitted.