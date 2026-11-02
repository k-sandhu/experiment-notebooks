# Scale-v5 main source material review

**Gate: passed.** This is a read-only pre-call audit of the frozen source packs. It does not read candidate responses or intervention outcomes, makes no model calls, and writes only its two reports under `authoring/`.

The prepared main cohort contains 2048 collection sources and 96 separate audit sources. The collection cap, audit count, seeds and tier match the adopted protocol. Each source was streamed through a complete integrity check, re-generated from the exact seed/tier/split/index specification, and re-audited from its rendered text with the separate SQL/Decimal and text/Fraction implementations. Each saved compact audit row was compared with a fresh recomputation.

The pilot, main collection and audit blocks have no duplicate case IDs or normalized semantic hashes. The main prior-corpus inventory recomputes exactly from its listed files and equals the pilot inventory. The main sources have zero ID or semantic-hash overlap with that inventory.

I constructed 2144 source-only prospective requests and 2144 synthetic no-gold repair-request controls in memory. Each source input contains only `case_id`, `task_instructions` and `documents`. Six offline verifier controls were built for each source; they remained in evaluator memory and were not included in requests. The synthetic sentinel outputs only test the generic-feedback builder and are not study responses.

| Pack | Sources | Tier | Seed | Index range | Source SHA256 |
|---|---:|---:|---:|---:|---|
| collection | 2048 | 192 | 255600 | 0–2047 | `b3c55dea2099c0abc51bacf194874f2e0858a8407e65ff4b3eef234ad0d192ac` |
| audit | 96 | 192 | 255096 | 2048–2143 | `cbe10b59a43e4ffc6ad694aca2c2bbcf6c76ec07682803908975fdb8f6fd4af7` |

All pre-call material checks passed. The main source gate is clear. The detailed hashes and individual checks are in [scale_main_material_review.json](scale_main_material_review.json).
