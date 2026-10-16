# Pipeline Materialization

Use this block when a route performs boundary work per element, resolves known identities one by one, builds a plan that still points back into admitted input, materializes wide payload before a narrowing selection, or persists a temporary computation graph.

This block owns **when data crosses an expensive boundary and which pipeline representation survives**. It does not own canonical identity/layout selection; route those decisions to their existing owners.

## Decision tree: boundary call inside a bounded collection

```text
Does one logical collection cause a DB/file/network/serialization call per element?
  NO -> no batching finding.
  YES
    |
    |-- Are all required keys known before those calls begin?
    |     NO -> keep the dependency; inspect whether an earlier pass can expose them.
    |     YES
    |
    |-- Must element i observe side effects produced by element i-1?
          YES -> keep the required ordered boundary operations.
          NO  -> BATCH candidate; continue to batch admission/resolve-once tree.
```

Per-element boundary work is a batching candidate, not proof that batching is legal. Count the collection bound and boundary-call multiplicity before proposing the replacement.

### Example: bounded SQL lookups

Before:

```rust
for id in input.item_ids() {
    let row = db.query_row(SELECT_ITEM, [id], ItemRow::from_row)?;
    use_row(row)?;
}
```

If all IDs are admitted before any mutation and the reads share one transaction snapshot, collect the IDs first and use one/few set-oriented reads. If each lookup depends on a write from the prior iteration, keep the ordered path.

## Decision tree: batch admission and resolve once

```text
Are the external/raw identities known before mutation/output emission?
  NO -> keep incremental resolution only where the dependency is real.
  YES
    |
    |-- Can one snapshot/version observe all referenced state consistently?
    |     NO -> preserve the required version/transaction boundary.
    |     YES
    |
    |-- Can the loaded rows be indexed request-locally by admitted identity?
          NO -> keep the simplest correct lookup.
          YES
            -> collect keys once
            -> batch-load canonical rows
            -> build request-local lookup/slot map
            -> resolve every relation once
            -> discard lookup after the operation.
```

Do not promote the request-local resolver into a retained cache without an independent cross-operation consumer.

### Example: raw IDs to concrete writes

```rust
let keys = collect_referenced_item_ids(&request);
let rows = load_items_batch(tx, &keys)?;
let by_id = index_request_rows(rows);

let writes: Vec<EvidenceWrite> = request
    .evidence
    .iter()
    .map(|e| EvidenceWrite {
        item_id: by_id[&e.item_id].id.clone(),
        success: e.success,
    })
    .collect();
```

The target write pass consumes `EvidenceWrite`; it does not perform another database or string-key lookup.

## Decision tree: compile-to-apply representation

```text
Does a validated/planned representation retain source_index, raw map key,
pointer/reference into the ordinary wire object, or unresolved temporary identity?
  NO -> the plan may already be apply-ready.
  YES
    |
    |-- Is exact source access required for signature verification,
    |   audit/replay bytes, source-position diagnostics, or another named contract?
    |     YES -> retain only that exact boundary reference and name the consumer.
    |     NO
    |
    |-- Can final IDs/values be assigned before mutation begins?
          NO -> keep the minimum unresolved state and name the blocking dependency.
          YES -> compile final IDs/values into the plan and remove the back-reference.
```

A compiled apply plan must not require ordinary lookups back into the admitted wire object. Retain a raw/source reference only when exact bytes, positions, signatures, or audit semantics require it.

### Example: remove source_index

Before:

```rust
struct PlannedEvidence {
    source_index: usize,
    item: ItemRef,
}

for planned in plan.evidence {
    let source = &request.evidence[planned.source_index];
    let item_id = resolve_item(planned.item, &inserted_ids)?;
    insert_evidence(item_id, source.success)?;
}
```

Candidate:

```rust
struct EvidenceWrite {
    item_id: LearningItemId,
    success: bool,
}

for write in compiled.evidence {
    insert_evidence(write.item_id, write.success)?;
}
```

The compile phase can allocate final IDs before writes when the ID scheme does not require database-generated identity.

## Decision tree: late materialization

```text
Does ranking/filtering/selecting require only a narrow subset of a wider payload?
  NO -> materialize the normal representation.
  YES
    |
    |-- Does selection materially reduce cardinality before wide fields are consumed?
    |     NO -> keep one materialization unless measurement supports a split.
    |     YES
    |
    |-- Can selection and later payload fetch observe one valid version/snapshot?
          NO -> keep one consistent materialization or establish a stronger snapshot.
          YES
            -> load narrow selection fields
            -> select stable IDs/slots
            -> materialize wide payload only for selected IDs.
```

Late materialization requires a consistent version/snapshot across selection and materialization. Do not trade correctness for fewer bytes.

### Example: queue 500, render 50

Before:

```rust
let rows: Vec<WideCardRow> = load_500_full_cards(db)?;
let selected = rank(&rows).take(50);
render(selected);
```

Candidate:

```rust
let entries: Vec<QueueEntry> = load_500_schedule_fields(db)?;
let ids = rank(entries).take(50).map(|e| e.card_id).collect::<Vec<_>>();
let cards = load_full_cards_by_id(db, &ids)?;
render(cards);
```

The narrow projection should contain only fields required to decide selection plus identity/version fields required to fetch the same logical rows safely.

## Decision tree: persisted history projection

```text
Is a build/request/pass intermediate persisted beyond its computation lifetime?
  NO -> ordinary local/retained lifetime rules apply.
  YES
    |
    |-- Is the exact historical representation itself the audit/replay/legal contract?
    |     YES -> persist it with explicit version/retention semantics.
    |     NO
    |
    |-- Which future consumers actually read the persisted data?
          UNKNOWN -> inspect them before changing history.
          KNOWN
            |
            |-- Can their required fields be represented as a smaller stable projection?
                  NO -> keep the required representation.
                  YES -> persist that projection and discard the temporary computation graph.
```

Persist the smallest stable projection required by future consumers. Exact audit/replay artifacts are allowed when exact historical representation is itself the contract.

### Example: calibration history

Before:

```rust
struct PlannerSnapshot {
    capability_states: Vec<ItemCapabilityState>,
    task_candidates: Vec<TaskCandidate>,
    focus_threads: Vec<FocusThread>,
}
```

If future calibration reads only chosen item/capability, baseline score, action, and evidence watermark:

```rust
struct CalibrationDecision {
    item_id: LearningItemId,
    capability: CapabilityKind,
    action: TaskAction,
    baseline_score: Option<f32>,
    evidence_watermark: Timestamp,
}
```

Persist `CalibrationDecision[]`; keep the temporary planner graph request-local.

## Route integration

Use this block from broad Stage 1/2 when any signature appears:

```text
boundary call per collection element
known keys resolved one by one
plan contains source_index/raw-key/input back-reference
wide payload loaded before a narrowing selection
temporary computation graph persisted for later consumers
```

The resulting structural action may be `BATCH`, `MERGE`, `LOCALIZE`, `DERIVE`, or `REMOVE`. A speed claim remains `UNVERIFIED` until matched measurement.

## Guardrails

- Batch only across a boundary whose transaction/version/order semantics remain valid.
- If element `i` must observe effects from element `i-1`, keep the ordered boundary operations.
- Do not keep both the raw and compiled representation unless a named consumer requires both.
- Do not make a request-local batch lookup a process-wide cache without an independent lifetime/cost case.
- Late materialization must preserve identity, authorization, snapshot/version, and output-order requirements.
- Persisted history is a separate authority decision: shrinking it must preserve replay/audit/calibration contracts.
- Static call/row/byte counts justify eliminating avoidable work; they do not prove end-to-end speedup.
