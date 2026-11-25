# Scale-v5 pilot source material review

**Gate: passed.** This review read the frozen pilot materials, re-ran full source audits, and built prospective inputs in memory. It made no CLI calls and did not modify repository data.

The frozen pilot packs contain **32 cases**: 16 at 128 base shipments and 16 at 192. Both compressed source hashes match their manifests and frozen protocol. All cases pass a fresh full rendered-text audit: the frozen constructor audit, independent SQL/Decimal reducer, and independently implemented text/Fraction audit agree with stored keys and evidence needs. Saved audit rows exactly match recomputation. All 32 cases also regenerate exactly from the declared seed, tier, split and stable index range.

The saved previous-corpus inventory contains 2132 rows, 1468 unique IDs and 1450 unique normalized semantic hashes. I recomputed it from the listed source files and compared file hashes and case/semantic inventories. The pilot has zero ID or semantic-hash overlap with that inventory; its two tier packs are also disjoint.

I constructed **32 one-case source-only requests** in memory and generated 192 offline verifier controls across all 32 cases. Each request contains exactly `case_id`, `task_instructions` and `documents`; none contains gold or an answer key. The controls stayed in evaluator memory and were not added to requests.

| Pack | Cases | Tier | Seed | Compressed source SHA256 | Visible-text audit |
|---|---:|---:|---:|---|---|
| tier_128 | 16 | 128 | 255128 | `0cd1239cca5a1aa41aad13bb1cfecb06953a765d44c790fa3be7048145a56644` | pass; saved audit rows match recomputation |
| tier_192 | 16 | 192 | 255192 | `9bafe7ea95a1cd24bbe2a1e54804cc65c0c2a9996ee9dda02c5ef8fb206b693a` | pass; saved audit rows match recomputation |

Protocol SHA256: `17c9dd9bd82df95d828226e6dd41de8c0b7fa9bc61981626beec1bf36a99eac6`. Code, source, manifest and audit hashes are recorded in [scale_pilot_material_review.json](scale_pilot_material_review.json). Prospective request-key set SHA256: `f5e9248ccb9c5112516c2a2f6e6c8c1a8f1ca96e1ade1fc4d51e325662c663ab`.

All material checks passed; the pilot source gate is clear.
