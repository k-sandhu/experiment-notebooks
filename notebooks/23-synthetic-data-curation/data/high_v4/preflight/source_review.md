# V4 possible main cohorts: rendered-source audit

Reviewed 2026-10-26. The service-failed pilot has not selected a main level, so I reconstructed and audited every possible level before any main call. The audit used `audit_high_rendered_sources.py`, a separate parser and exact `Fraction` arithmetic over model-visible P01-P06 text. It compared derived answers and evidence needs with evaluator keys only after deriving them. Instruction SHA-256: `0d74782473e7b1b8079f76f004aa87d0d2341bb8c37e4210b5b85acf3d7567b8`.

For each of levels 1-4, I generated the frozen initial block (160 cases, seed 244160, start 0), expansion block (80, seed 244080, start 160), and audit block (24, seed 244024, start 240). All 1,056 possible packets had unique case IDs and semantic hashes. The independent reader found **zero answer mismatches and zero evidence-key mismatches** across all four cohorts.

| Level | Packets | Word range | Initial / extension / audit | Answer or citation mismatches |
| --- | ---: | ---: | ---: | ---: |
| 1 | 264 | 2,749-2,956 | 160 / 80 / 24 | 0 |
| 2 | 264 | 4,217-4,336 | 160 / 80 / 24 | 0 |
| 3 | 264 | 6,931-7,050 | 160 / 80 / 24 | 0 |
| 4 | 264 | 9,645-9,764 | 160 / 80 / 24 | 0 |

Each level contains 43 compound, 45 dated-UOM/return, 43 effective-authority, 45 shipment-revision, 44 split-allocation, and 44 tier/sequential-pricing packets. These labels describe mixed scenario variants; they do not isolate causal effects. All generated orders remain active, so this audit does not add evidence about cancellation handling.

The complete compact per-case record is in `high_all_main_source_audit.json`: packet/document hashes, derived seven-field answer, required evidence groups, term sources, selected-event count, net dispatch, reversal count, exact price calculation, and key-match flags. Recreate it from this directory with:

```powershell
python authoring/run_high_all_main_audit.py
```

The audit supports solvability for the exact frozen generator, instructions and seeds. It does not show that every real procurement workflow uses these authority, return, allocation or pricing rules. The final selected 264-case files should still be checked against the audited IDs and document hashes immediately before calls; any prompt, generator, seed or file difference invalidates this pre-audit for the changed packet.
