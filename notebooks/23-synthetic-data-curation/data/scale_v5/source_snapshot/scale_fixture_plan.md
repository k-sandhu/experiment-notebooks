# V5 procurement source plan and wrapper contract

Created 2026-10-26. This is authoring material. No model calls or repository writes are part of this wrapper. Earlier fixtures, responses, notebook cells and audit helpers remain unchanged.

## Approved scope and realistic limits

Use the same explicit procurement rules with fresh facts and longer histories. The two tiers contain 128 or 192 logical SH-* shipments, compared with 64 in the preceding completed main cohort. Corrections, exact ingestion copies, reversals, returns and same-SKU order/line distractors add more register rows. These are ordinary tables and approval registers, rather than new ambiguous instructions. All orders remain active.

Longer histories do not guarantee mistakes. A pilot calibrates difficulty for this Sol configuration. It does not establish a causal effect of length, general accounting competence, training gains or a repair advantage. The six family labels are overlapping scenario variants, not isolated causal ablations. The audit uses a different heading format within the same semantic families.

The twelve prototype sources have 6,931â€“7,026 words at 128 shipments and 9,645â€“9,740 at 192. Independent audit of all twelve took about 1.1 seconds locally. Six complete sources, including structured evaluator facts, compressed to about 44.9 KB and 54.1 KB in a shared gzip stream. These are source-storage measurements, not model input-token counts, latency or spend estimates. The final frozen cohorts must be measured independently.

## Independent business-scope review

The larger packets remain plausible as high-volume standardized-component reconciliation exports. Resolved target-line demand is 110,550–112,099 individual units at 128 shipments and 126,550–128,099 at 192, depending on seeded values and the controlling approval. The order is issued on October 15; base shipments are dated October 18, 22 and 23, with returns and revision controls available through the October 26 noon cutoff. The histories therefore represent dense, short-window warehouse activity, rather than years of arbitrary arithmetic.

The concentration of movements on a few repeated dates and regular injected correction patterns is controlled experimental design, not a claim about normal warehouse event frequencies. Authority, partial amendments, dated packaging, allocations, reversal identity and pricing remain explicitly stated and uniquely resolvable. Every answer-relevant join and rule is visible in the text. The twelve prototype independent readers agree; that supports their solvability, while the full source gates remain required.

The scope is clean, active-only table reconciliation. Sol has external tools disabled by the separately frozen CLI profile, so this measures text-only reconciliation under that restriction rather than an accountant using a ledger, calculator or database. The sources omit OCR, missing contracts, tax, currency conversion, unspecified policies and unresolved conflicts. Calling these packets realistic means their business operations and magnitudes are plausible within that narrow setting; it does not make them representative production records.

## Frozen sampling decisions

Audit all 32 potential pilot sources before any pilot call. Call 16 at 128 shipments. If at least six replies have valid schema and wrong typed values, select 128. Otherwise call 16 at 192 and select 192 if at least six qualify. There is no upper failure cutoff. If neither tier qualifies, use the declared 192 fallback and report that the pilot did not demonstrate the desired headroom. Citation-only rejection is not a genuine value failure.

After selection, generate and audit only that tier's entire potential main cohort before its first main call: 2,048 collection sources and 96 separate audit sources. The collection starts with 512 and can add predetermined 256-source chunks until it has 600 genuine value failures or reaches 2,048 originals. The cap can stop the study below 600 failures. Uncalled sources remain potential sources, not failed predictions or result denominators. The separate audit does not select failures or determine stopping.

The generator/code and master seeds are frozen before pilot results. Tier selection activates a predetermined generator setting. All collection chunks use the same master seed and stable index ranges from the frozen source corpus. Main collection indices are 0â€“2047; the audit uses indices 2048â€“2143 and its own seed.

| Purpose | Seed |
|---|---:|
| Pilot, 128 shipments | 255128 |
| Pilot, 192 shipments | 255192 |
| Main collection | 255600 |
| Separate audit | 255096 |
| Failure ranking, owned by pipeline | 255777 |
| Dispatch, owned by pipeline | 255888 |
| Bootstrap, owned by pipeline | 246600 |

These seed roles are separate. The wrapper additionally hashes version, tier, split and case index into each case RNG seed. It uses a deterministic permutation of the six family labels within every six consecutive indices. Generating indices in one call, individually or in chunks produces exactly the same documents and metadata. This differs from the older batch-dependent sampler, without changing business facts or accounting rules.

## Sources and business rules

The byte-frozen core is high_fixtures.py. P01 gives signed lines and order defaults; P02 is partial field-level approvals; P03 gives effective-dated handling units; P04 gives dated line allocation percentages; P05 gives pricing packs and tiers; P06 is the movement revision register. A second line shares the target SKU, so SKU equality alone does not merge demand accounts. Every structured source fact is rendered and reparsed.

Both approval effective time and recording time must be available at the inclusive 2026-10-26T12:00:00Z cutoff. Field precedence is line scope, authority, effective timestamp, then revision. Partial approvals retain unspecified fields. The selected top-priority value must be unique. The source creation date is 2026-10-26, while historical business timestamps remain in the packet. Future and late rows are deliberate visible exclusions under the rules, not missing data.

For each movement identity, choose the highest revision recorded by cutoff, count identical ingestion copies once, then test state, order and occurrence. A selected VOID or future-occurring revision does not restore the older row. A timely active reversal removes the referenced selected shipment once. A return against an inactive shipment contributes zero. Otherwise the return uses its referenced selected shipment's dated SKU/UOM factor and allocation version, including any selected correction, rather than return-day rates. Accepted returns cannot exceed original selected shipment quantity. Every allocated contribution is an integer.

Open units are current approved ordered demand minus net allocated dispatch, with accepted returns reducing dispatch. Pricing tiers use ordered demand before movements. Gross cents are for a pricing pack. Divide by pack_units; multiply by sequential rebate-A and rebate-B factors; add per-unit fee and pack_fee/pack_units; subtract per-unit credit; round only the final per-unit cents half up. Warehouse cartons and pricing packs have separate meanings. No new order status, ambiguous approval, partial reversal or undisclosed rounding rule is introduced.

The seven outputs and response schema remain unchanged. A wrong value, wrong schema and insufficient evidence are separate outcomes. Group-level evidence policy is unchanged, including harmless P01â€“P06 context. Exact truth, family, tier, source record and traces are evaluator-only. `scale_model_input` returns exactly case_id, task_instructions and documents.

## Public API

All new public constants and functions use SCALE_ or scale_ names. The wrapper executes the three frozen helper sources in separate private namespaces. It does not replace HIGH_* variables or any previous notebook function. SHA256 locks validate original source bytes; explicit embedded strings use corresponding LF-normalized source hashes.

- `scale_load_cores(core_dir=None, core_sources=None)` loads high_fixtures.py, high_material_audit.py and audit_high_rendered_sources.py. Default paths are authoring-local. A self-contained notebook must embed those exact source strings and pass them explicitly; it needs no repository import or __file__ lookup.
- `scale_iter_cases(n, seed, tier=128, split='pilot', start_index=0)` streams full case dictionaries. `scale_make_cases` returns the same sequence as a list. Zero cases are supported; booleans are not accepted as integer controls.
- `scale_validate_answer`, `scale_correct_response`, `scale_independent_reference`, `scale_calculation_trace` and `scale_make_verifier_controls` delegate to unchanged frozen rule implementations. `scale_model_input` exposes only the solver inputs.
- `scale_audit_case(case, include_traces=False)` returns a compact JSON-safe source audit. Setting include_traces=True adds the complete per-event fixture trace, separate SQL/Decimal trace and separate text/Fraction trace. `scale_audit_fixtures(cases)` accepts a stream and enforces exact identity/normalized-semantic uniqueness.
- `scale_write_corpus(path, cases, audit_path=None, manifest_path=None)` audits every case before writing it to deterministic gzip UTF8 LF JSONL. Existing outputs are rejected. A failed stream removes its incomplete outputs. Default compact audit path is source-name+.audit.jsonl.gz; default manifest path is source-name+.manifest.json. No uncompressed source copy is written.
- `scale_iter_corpus(path, manifest=None)` streams one complete case dictionary per line. With a manifest it checks gzip hash and final row count. The caller must consume the stream fully to execute the count check. `scale_verify_corpus(path, manifest_path=None, full_audit=True)` checks hashes, per-case index and uniqueness; by default it reruns every material audit.
- `scale_previous_corpus_keys(paths)` streams explicitly enumerated previous source JSONL/gzip corpora into ID/hash sets and records file hashes/counts. Repeated historical snapshots are deduplicated. `scale_check_previous_overlap(manifest_or_case_index, inventory)` rejects either an ID or normalized-semantic overlap. `scale_check_cohort_overlap(manifests)` handles new pilot/main/audit manifests.
- `scale_preflight_cohorts(output_dir, blocks)` accepts explicit block dictionaries with name,n,seed,tier,split,start_index. It freezes each compressed source/audit/manifest bundle and checks cross-block overlap. Destination directories must already exist; it has no model-call branch.

The source manifest contains complete/all_passed, n_cases, corpus_file/audit_file, compressed_sha256/uncompressed_sha256, audit_compressed_sha256/audit_uncompressed_sha256, core and instruction hashes, family/tier/word counts and a compact case_index. Each index row has case_id, content_hash, semantic_hash, generation_index, split and base_shipments. The longer corpus_* and audit_* hash names remain aliases for precise inspection. Audit paths are relative to the source directory. Pipeline can look up IDs and hashes without decoding all documents. Full traces are reproducible from the one compressed source copy rather than duplicated thousands of times.

## Solvability gate and overlap scope

Every source is checked by the frozen full rendered-text parser and reconstructs its complete source_record. Constructor Decimal truth agrees with an independently implemented Fraction reducer. A separately authored visible-text parser with SQL movement selection/joins and Decimal pricing must agree. A second separately authored text/Fraction audit checks values, evidence needs and source integrity before comparison with stored truth. These are separate implementations of the same declared rules, not evidence that those rules cover every real business.

Checks include unique identities and current terms, revision and duplicate-copy handling, reversal references, original-date return joins and return bounds, dated handling/allocation coverage and share totals, integral event contributions, exact price rounding, complete source tables, typed dates, nonnegative answers and accepted correct-response controls. Compact per-source summaries include content/semantic hashes, derived ordered/net/open units, exact unrounded price, source-integrity counts and hashes of full traces.

Before calls, pipeline must inventory all earlier source corpora and pilots, record the enumerated paths/hashes, and check new pilot/main sources against them. An incomplete supplied path inventory cannot establish no overlap with omitted files. Semantic hashes normalize table order and exact copies while preserving actual values; they test exact normalized fact overlap, not broad prose or task-program novelty. No claim of independent semantic-family holdout is made.

## Verification and readiness

`python -m unittest test_scale_fixtures -v` passes 12 meaningful wrapper tests. They cover both history sizes and all six variants, independent source equations, batch/index invariance, seed/split/tier separation, solver-input isolation, schema/value/evidence separation, source/key mutations, embedded hash locks and namespace isolation, zero/invalid controls, deterministic compressed LF roundtrips, manifest tampering, failed-write cleanup, cross-cohort overlap, prior compressed/plain inventories and generic preflight blocks.

The compact prototype audits are in scale_fixture_plan.json. They are checks of generated sources, not observed model answers. The full 32-source pilot and selected 2,144-source main material gates remain required after parent protocol freeze. Live budget, model version/effort, request handling, selection and paired statistics belong to the separate frozen pipeline.
