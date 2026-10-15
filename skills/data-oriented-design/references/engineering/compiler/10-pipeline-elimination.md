# Compiler Pipeline Elimination

Use this block when a compiler, parser, DSL frontend, query frontend, or lowering pipeline contains several intermediate representations or repeated lowering passes.

## Goal

Minimize the number of persistent representations and full traversals between source input and the required semantic result.

Do not optimize an existing stage before deciding whether the stage belongs in the target pipeline.

## Decision tree

```text
START
  |
  |-- Draw: INPUT -> stages -> REQUIRED OUTPUT.
  |
  |-- For each stage R:
  |      |
  |      |-- Does R add information required downstream?
  |      |      |-- NO -> remove or fuse R.
  |      |      '-- YES
  |      |
  |      |-- Does R have an independent consumer after the next stage?
  |      |      |-- YES -> keep R; name the consumer and lifetime.
  |      |      '-- NO
  |      |
  |      |-- Can the producer emit the next representation directly?
  |             |-- YES -> remove R.
  |             '-- NO -> keep the smallest staging form.
  |
  |-- Does a superseded production path remain?
  |      |-- YES -> migrate/delete it; keep only a temporary test oracle if required.
  |      '-- NO
  |
  '-- Compare current and candidate pipeline counts.
```

If a branch cannot be decided from code and contract evidence, mark it `MEASURE`; do not guess.

## 1. Map the whole transformation

For every stage record:

```text
input type
output type
information added
information discarded
retained state created
consumer(s)
full-pass count
allocations
bytes copied
parse/decode count
hash/normalize count
```

Ask:

```text
Why does this representation exist?
Who consumes it after the next stage?
Can its producer write directly into the consumer representation?
How many times is the same information decoded, normalized, or hashed?
How many representations of the same semantic entity coexist?
```

## 2. Use elimination before local optimization

Default priority:

```text
remove stage
    >
remove repeated pass/work
    >
remove allocation
    >
remove indirection
    >
improve layout
    >
vectorize
    >
micro-optimize instructions
```

Change this order only when a contract or measurement gives a stronger reason.

A representation that is built, traversed once, lowered, and destroyed is a removal candidate.

## 3. Keep an intermediate representation only for a named reason

Keep a syntax tree, AST, or staging IR when at least one condition is true:

- an independent consumer uses it;
- a source-preserving or tooling contract requires it;
- a correctness boundary requires it;
- direct emission would make the producer more complex than one bounded packing pass;
- matched measurement shows that the staging form lowers the declared target cost.

Otherwise remove it.

Do not preserve a layer because existing classes or APIs happen to expose it.

## 4. Detect duplicate semantic layers

A layer is suspicious when input and output encode the same semantic facts under different type names.

Examples:

```text
syntax expression -> semantic expression
catalog row       -> metadata row
parser node       -> lowering node
```

Compare information, not names.

If the layer adds no required information and the producer can emit the target form directly, remove the layer.

## 5. Distinguish semantic stages from layout-only packing

Use this rule:

```text
Does layer L add required information?
  |-- YES -> keep only if a distinct consumer or lifetime requires L.
  '-- NO
       |
       |-- Is L only a layout conversion?
       |      |-- NO -> delete L.
       |      '-- YES
       |
       |-- Can the producer emit the target layout without adding a persistent representation, extra full pass, or new invariant that needs separate acceptance?
              |-- YES -> remove L.
              '-- NO -> keep one bounded packing pass and measure its net cost.
```

A packing pass is accepted only when:

```text
packing cost < downstream savings
```

for the representative workload.

## 6. Keep one canonical production path

After replacement behavior is validated, remove the superseded production implementation unless the product requires both.

Use this deletion test:

```text
If this path/layer is deleted, what required observable behavior disappears?
```

If the answer is `none`, delete it.

A legacy parser may remain temporarily as an independent correctness oracle. Do not keep it as a second production authority.

## 7. Structural comparison

Compare current and candidate with the same measures:

```text
stages
full passes
persistent representations
parse/decode operations
hash/normalize operations
copies
allocations
pointer/key lookups
retained bytes
new invariants
```

Unknown values remain `?`.

Prefer the candidate that preserves the contract and produces the best declared structural/measurement result with the fewest new invariants. If evidence does not distinguish candidates, mark the choice `MEASURE`.

## Related rules

Load only when needed:

- canonical/derived state: `../02-canonical-and-derived.md`
- data shape and typed IDs: `../01-data-shape.md`
- repeated work: `../03-hot-path-work.md`
- performance acceptance: `../../performance/00-diagnosis.md` and `../../performance/01-measurement.md`
