# Identity, Handles, and Flat Relations

### DOD-005 decision tree

```text
Do retained rows use pointers or one allocation per node?
 |-- NO -> N/A.
 '-- YES
      |
      |-- Does profiling show pointer, cache, TLB, or memory cost?
      |      |-- NO -> UNVERIFIED.
      |      '-- YES
      |
      |-- Can one owner address every row by a bounded slot?
      |      |-- NO -> Keep pointers or use another stable handle.
      |      '-- YES -> Test typed IDs.
```

### DOD-005 — Replace retained row pointers with checked IDs
- **Symptom:** Rows retain pointer links or use one heap allocation per node; link width and pointer traversal recur across `N` rows.
- **Action:** Put rows in one owner array and store typed slot IDs in links. Choose a narrower ID only under a validated capacity bound (DOD-009). If deleted slots can be reused, add a generation; if rows are compacted, preserve or remap every live ID. Resolve IDs through the owner, and do not retain direct references across owner relocation.
- **Check:** Compare actual row width, allocations, and traversal time. Reject wrong-domain, out-of-range, deleted, and stale IDs; define generation-wrap behavior if slots are reused.
- **Example:** On a machine with 8 B pointers, `next: pointer` in 10,000 rows uses 80 KB of raw link fields. With at most `2^32-1` slots and no reuse, `next: checked 4 B NodeId` uses 40 KB before row padding. If slots are reused, `NodeId(slot, generation)` rejects a deleted node's old ID; recalculate its width.

### DOD-007 decision tree

```text
Does each parent own a separate child allocation?
 |-- NO -> N/A.
 '-- YES
      |
      |-- Is child traversal mostly sequential and stable?
      |      |-- NO -> Keep a dynamic structure.
      |      '-- YES
      |
      |-- Do arbitrary parent appends need O(1)?
             |-- YES -> Use another append-friendly representation.
             '-- NO -> Test one child array plus ranges.
```

### DOD-007 — Flatten stable relations
- **Symptom:** Each parent owns a separately allocated child list and traversal is sequential.
- **Action:** Append children to one owner array, and put `(offset, length)` in each parent. As an alternative for fixed adjacency lists, store `N+1` offsets instead of `(offset, length)` per parent. Rebuild or use another representation when arbitrary per-parent append must take O(1) time.
- **Check:** Include child order, empty parents, offset overflow, allocation count, and rebuild/update cost. Do not claim O(1) append to an arbitrary middle range.
- **Example:** `before: parents[i].children = separate_array`; `after: children = [a,b,c]; ranges = [(0,2),(2,0),(2,1)]`. Parent 1 reads `children[2:2]`; one array owns all children. Sequential traversal stays O(total children).

### DOD-008 decision tree

```text
Does runtime traversal resolve internal links from strings?
 |-- NO -> N/A.
 '-- YES
      |
      |-- Can build validate and resolve the name once?
      |      |-- NO -> Keep runtime lookup.
      |      '-- YES
      |
      '-- Are names still required for output?
             |-- YES -> Keep names at the output boundary.
             '-- NO -> Retain only typed IDs.
```

### DOD-008 — Resolve external strings to internal IDs at build time
- **Symptom:** Relations retain names and each runtime traversal searches a string-key map for the target row.
- **Action:** Validate names and duplicates at build time. Assign typed dense IDs and store them in relations. Keep names for output or diagnostics. Retain the string lookup only for runtime name queries or inserts. If rows move, update an ID-to-slot map or remap stored IDs.
- **Check:** Preserve unknown-name errors, duplicate-name policy, output order, and spelling. Count build lookups, retained bytes, and runtime traversal, including name and ID-to-slot maps.
- **Example:** `before: edge.target = "cat"; visit(edge) => map[edge.target]`. `after: edge.target = EntityId(7); visit(edge) => owner.resolve(edge.target)`. Retain `names[7] = "cat"` only for output. An ID-to-slot map keeps `EntityId(7)` stable as rows move. For `E` edges visited `Q` times, resolve names once per edge during build instead of `Q × E` runtime lookups.

### DOD-022 decision tree

```text
Do retained rows repeat string keys or hash the same bytes?
 |-- NO -> N/A.
 '-- YES
      |
      |-- Is pool + ID + lookup storage smaller than the current retained string storage?
      |      |-- NO -> Keep strings unless CPU evidence justifies interning.
      |      '-- YES
      |
      |-- Can one owned pool keep stable string identity?
             |-- NO -> Keep strings.
             '-- YES -> Test StringId plus byte pool.
```

### DOD-022 — Replace retained string keys with integer IDs
- **Symptom:** Rows or indexes retain owned or borrowed string keys, and internal operations repeatedly hash or compare their bytes.
- **Action:** Store each distinct string once in an owned byte pool with its length. Intern incoming bytes to a typed unsigned `StringId` containing the pool offset. Use that ID in rows and internal maps. Resolve a temporary byte view only when text content is needed. Keep the string-to-ID table while new strings or external string lookups are accepted.
- **Check:** Strings equivalent under the declared equality policy receive one ID; non-equivalent strings remain distinct despite hash collisions. Validate offset width, length encoding, and pool lifetime; keep offsets stable or remap IDs if the pool is compacted. Count pool bytes, IDs, retained lookup tables and maps, and allocations; compare build and runtime lookup costs. Persist the pool alongside IDs or remap IDs on load. Pool offsets are not dense ordinals: compact direct arrays require a separate dense ID mapping.
- **Example:** `before: string_key_map["cat"] = value; row.name = owned_string("cat")`. `after: id = intern("cat"); integer_key_map[id] = value; row.name = id`. If the pool entry for `cat` starts at byte offset 37, repeated uses of `cat` share `StringId(37)`; `integer_key_map` uses integer keys rather than string bytes. A 32-bit offset is valid only while pool size and reserved values fit its declared range.

### DOD-028 decision tree

```text
Do non-string canonical values repeat across retained data?
 |-- NO -> N/A.
 '-- YES
      |
      |-- Can equality use one stable canonical identity?
      |      |-- NO -> Keep explicit values.
      |      '-- YES
      |
      '-- Does pool + ID + lookup cost beat retained value and comparison cost?
             |-- NO -> Keep explicit values.
             '-- YES -> Test a typed canonical-value ID.
```

### DOD-028 — Intern repeated canonical values
- **Symptom:** Non-string values repeat, and internal work repeatedly stores, hashes, or compares the same structure.
- **Action:** Store one canonical value and use a typed ID for repeated references.
- **Check:** Define canonical equality. Measure pool bytes, lookup cost, comparison cost, build time, and retained bytes.
- **Example:** Store one canonical type description and use `TypeId` in rows that refer to that type.
