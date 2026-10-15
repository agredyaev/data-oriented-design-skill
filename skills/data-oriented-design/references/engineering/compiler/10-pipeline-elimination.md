# Compiler Pipeline Elimination

Use this block when a compiler/frontend has several intermediate representations or repeated lowering passes. It also applies to parser, DSL, and query frontends.

## Goal

Minimize the number of persistent representations and full traversals between source input and the required semantic result.

Do not optimize an existing stage before deciding whether the stage belongs in the target pipeline.

## Decision tree

```text
START
  |
  |-- Draw: INPUT -> stages -> REQUIRED OUTPUT.
  |
  |-- For each intermediate representation R and the stage producing it:
  |      |
  |      |-- Are required computations, validation, consumers and lifetimes known?
  |      |      |-- NO -> UNKNOWN; inspect them before proposing removal.
  |      |      '-- YES -> preserve those responsibilities even if R is removed.
  |      |
  |      |-- Does a consumer/boundary require R separately from the next form?
  |      |      |-- YES -> KEEP the required form; name consumer and lifetime.
  |      |      '-- NO
  |      |
  |      |-- Can the producer emit the next form preserving the required computation?
  |      |      |-- NO -> KEEP staging required by dependencies/validation.
  |      |      '-- YES -> compare a direct-emission candidate with current staging.
  |      |
  |      '-- Does the candidate pass correctness and the declared cost/structural goal?
  |             |-- UNKNOWN -> prototype/verify; MEASURE disputed costs.
  |             |-- YES -> REMOVE R's storage/pass; retain required computation.
  |             '-- NO -> KEEP the current form or test a smaller staging form.
  |
  |-- Does a superseded production path remain?
  |      |-- YES -> MIGRATE/DELETE; keep only a temporary oracle if required.
  |      '-- NO -> continue.
  |
  '-- Compare current and candidate pipeline counts.
```

Missing consumer/semantic facts are `UNKNOWN`; missing costs require `MEASURE`. Neither means that a stage is unnecessary.

### Example: remove storage, preserve semantic work

`parse → Ast → typecheck → TypedTree → lower → Ir` has no AST consumer after lowering. This makes the AST a candidate, not permission to delete type checking. Direct emission must still resolve names, reject invalid types and preserve contractual diagnostics. A formatter needing the AST keeps a syntax form. A later pass requiring a whole-program symbol table may require staging even without an external AST consumer.

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

If none applies and required computation can move safely, test removal. Unknown dependencies or costs are unresolved prerequisites, not a removal decision.

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
Does L compute or validate required facts?
  |-- YES -> Preserve that computation; use the main tree to decide separate storage.
  '-- NO -> Does L provide a required boundary or consumer representation?
              |-- YES -> Preserve that responsibility; test how it is produced.
              '-- NO -> Is L a layout conversion for a measured downstream benefit?
                           |-- NO -> Test deletion after verifying all consumers.
                           '-- YES -> Compare direct production with one packing pass.
                                      Accept only the option meeting the declared target
                                      and guardrails, including producer/packing costs.
```

A packing pass introduced for speed must satisfy:

```text
packing cost < downstream savings
```

for the representative workload.

For example, a layout-only pass adds no semantic information, but its 2 ms packing cost can repay 8 ms across repeated consumers. Keep it for that measured benefit if direct production does not perform better within the same budgets. For a memory target, measure retained and peak bytes instead of requiring a speed win; retain the latency guardrail.

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

Prefer the candidate that preserves the contract and passes the declared target with fewer new invariants.

If evidence does not distinguish candidates, mark the choice `MEASURE`.

## Related rules

Load only when needed:

- canonical/derived state: `../02-canonical-and-derived.md`
- data shape and typed IDs: `../01-data-shape.md`
- repeated work: `../03-hot-path-work.md`
- performance acceptance: `../../performance/00-diagnosis.md` and `../../performance/01-measurement.md`
