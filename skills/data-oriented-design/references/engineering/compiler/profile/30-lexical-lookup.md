# Lexical Lookup Decisions

## Decision tree: compact operator lookup

```text
Is the complete operator set and longest-match rule known?
  NO -> establish the grammar; do not invent an encoding.
Do measured dispatch cost or a stated storage budget justify a new lookup?
  NO -> KEEP current dispatch.
  UNKNOWN -> measure the existing lookup or calculate its storage budget.
Can bounded source bytes select a candidate operator safely?
  NO -> KEEP a grammar-correct scanner for that case.
  YES -> candidate: packed bytes/hash -> compact table -> exact validation.
Do different valid operators collide in the proposed key space?
  YES -> change the mapping or add explicit collision resolution.
Can arbitrary invalid input reach the same candidate slot?
  YES -> compare length/content before accepting the candidate.
Does the chosen candidate preserve longest-match and EOF behavior?
  NO -> REJECT lookup; a hash is not an accepted token.
```

### Example: longest match and short input

Grammar operators: `>`, `>=`, `>>`, `>>=`. For input `>>=x`, emit `>>=` then identifier `x`; accepting `>` at the first table hit is wrong.

For a one-byte input `>`, a 4-byte packed load is legal only with an enforced readable-padding contract. Without one, use bounded loading or the existing short-input path. Masking bytes after an out-of-bounds load does not make the load valid.

## Decision tree: dense keyword candidate lookup

```text
Is keyword identity defined by exact bytes/length or a specified normalization?
  UNKNOWN -> resolve that contract first.
Can the fixed keyword set map to candidate slots without unresolved collisions?
  NO -> keep explicit lookup or resolve collisions.
Do sparse hash slots breach the table budget or measured cache target?
  YES -> candidate: occupancy bitmap + rank -> packed candidate table.
  NO -> keep direct slots; do not add rank work just to shrink the table.
Does lookup validate membership and exact normalized bytes/length?
  NO -> REJECT: non-keyword identifiers can share a keyword hash.
Does total lookup cost, including validation, meet the acceptance rule?
  NO -> KEEP existing lookup.
  UNKNOWN -> MEASURE; table size alone does not prove speed.
```

### Example: bitmap rank and a false keyword candidate

Occupied hash slots: `{2,5,7}`, bitmap `0b10100100`, packed candidates `[kw2,kw5,kw7]`.

For hash 5, check bit 5, then compute `rank = popcount(bitmap & ((1 << 5) - 1)) = 1`; read packed candidate 1. For hash 3, the occupancy bit is clear: no keyword match. For any identifier hashing to slot 5, compare the candidate's full length and normalized bytes. If the candidate is `if` and input is `ix`, return identifier, not keyword.

A compact byte pool with `(offset,length)` can replace padded keyword strings when its measured bytes/cache cost justifies the extra lookup. Keep the pool alive through all comparisons. On pool compaction, remap offsets or reject stale references.

### Example: changing the grammar invalidates a perfect hash

Adding a keyword that collides with an existing keyword must fail table generation or produce a collision-resolving table. Do not keep the old “perfect” mapping and let one keyword overwrite the other. Recheck vocabulary coverage, non-keywords, prefixes, unknown operators, endianness, EOF, and malformed/non-ASCII inputs required by the grammar.

Use [Compiler validation](../40-validation.md); acceptance must preserve rejected inputs as well as valid token tags.
