# Measurement and Review

Use this block to decide what evidence is required for the claim. The canonical verification matrix is [Workflow verification](../workflow.md#7-verify-proportionally). Do not require unrelated metrics.

## Decision tree: evidence for the claimed result

```text
What result is being claimed?
  behavior preserved
      -> relevant tests/code evidence.
  structural simplification only
      -> code/structure inspection + affected-behavior verification.
  retained/peak memory reduced
      -> matched evidence for that memory metric + affected guardrails.
  allocations reduced
      -> allocation evidence + affected guardrails.
  phase latency/throughput improved
      -> matched phase benchmark including work moved outside the phase.
  end-to-end latency/throughput improved
      -> matched end-to-end benchmark.
  scaling improved
      -> multi-load or multi-thread scaling evidence.
Is required evidence missing?
  YES -> UNVERIFIED; name the smallest missing measurement/check.
  NO -> classify only the result actually supported.
```

### Example: memory win without speed claim

If retained memory falls from 200 MB to 140 MB while latency remains within its required bound, report a memory result. Do not require latency to improve, and do not call it a speed win.

## Decision tree: accept or reject an optimization

```text
Did required behavior/correctness fail?
  YES -> REJECT.
Did a required budget/guardrail fail?
  YES -> REJECT adoption; report the regression.
Is acceptance evidence missing?
  YES -> UNVERIFIED.
Did the declared target pass?
  YES -> ACCEPT only for that target/result class.
  NO -> TARGET UNMET; retain only for a separately justified benefit or
        named structural simplification.
```

### Example: local improvement, target unmet

Extraction falls 8 ms -> 4 ms, but total workload remains ~100 ms and the target is <90 ms. Report the local phase improvement only; the end-to-end target remains unmet and the next step is to reprofile/rerank.

## Decision tree: review a suspicious construct

```text
Is the construct a known smell (Arc<Mutex> domain graph, repeated parse,
clone in dominant loop, duplicate state, generic mode-heavy executor, global cache)?
  NO -> no finding from shape alone.
  YES
    |
    |-- Is there a concrete responsibility/consumer/contract that requires it?
          YES -> KEEP that responsibility; evaluate its cost only if relevant.
          NO -> apply the matching engineering decision tree and propose removal/change.
          UNKNOWN -> inspect before reporting a defect.
```

### Example: `Arc<T>`

`Arc<T>` for immutable cross-thread ownership can be correct. `Arc<Mutex<T>>` around ordinary frozen domain state should route to the ownership decision tree rather than being rejected automatically.

## Review output

Report only:

1. the decision/result;
2. the evidence that supports it;
3. the exact candidate or removed element when applicable;
4. blocking `UNKNOWN`/`UNVERIFIED` facts.

Use [Performance measurement](../performance/01-measurement.md) for matched benchmark mechanics and result classes. Use [Correctness boundaries](06-correctness-boundaries.md) before removing checks that may have independent authority, wire, recovery, migration, or oracle responsibilities.
