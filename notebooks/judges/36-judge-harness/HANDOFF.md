# Engineering handoff: notebook 36

## Status: Live selection in progress; descriptive audits checked offline

Updated 2026-10-30T19:06:54.138595+00:00. Selection outcomes cached: 1121/3870. Confirmation outcomes cached: 0/720. Imported baseline reply entries: 1440. New final reply entries: 1039.

## Design as built and choices

- Source commit supplied by owner: cf854303; claim #97 supplied. No git or gh commands were run. Writes are confined to this notebook folder. No README.md or PROTOCOL.md is authored here. Claude owns all reader-facing prose; markdown cells are structured TODOs.

- Exam is unchanged: all 240 test pairs and 24 source development pairs copied under data/from_33. All source freeze hashes are checked after CRLF-to-LF normalization. data/from_33/SOURCE.md and data/source_manifest.json list copy hashes. baseline_cache.jsonl.gz contains the 1440 relevant final replies; data/cache_imported.jsonl.gz preserves their original full requests/keys and adds origin metadata. Original candidates and source files are never modified.

- Fixed seed 3610302026 splits test pairs 120/120, 30 per family and 6 traps per split. Baseline better-position is exactly balanced 15/15 in each family per split; orders need not balance within the tiny trap subset. data/split.csv is the authoritative item/order list.

- Supplied amendment replaces Haiku with Luna because Haiku had 73 provider-filter blocks among 120 instruction judgments and near-ceiling other families. Sol, Luna and Granite retain notebook 33 pins/provider; Granite baseline effort is none, not medium. Granite supports none/low/high, so the two effort conditions are explicitly compared with none, not a fictional medium. Sol has room primarily on code/instructions; report family tables.

- Baseline, both-orders, and vote 1 of majority5 reuse source replies. Baseline confirmation also reuses source replies. Source latency/attempt/dollar metrics come from source judgments.csv because only final replies are needed for replay. Incremental new cost is zero for imported entries; nominal cost treats their historic cost as the cost of operating that harness.

- Single-answer grades each original candidate independently. Pass beats fail; for same verdict, higher confidence wins even when both failed, as requested. Exact confidence tie is undecided. Both orders disagreements are undecided. Undecided scores 0.5; any required unreadable component makes the aggregate unreadable (0 score), never an answer-based abstention. Majority requires all 5 readable; it does not silently discard formatting failures.

- All original pairwise strict/lenient readers are copied byte-for-byte in notebook code from the frozen source reader, including conservative token-truncated-prefix recovery. Two predeclared adapters are necessary for unary verdicts and labelled free text; data/analysis_plan.json records them. Analysis-first and solve-first use the unchanged readers, so strict rejects prose before the JSON. Lenient still reads the first complete JSON, not a post-hoc last-object repair.

- New CLI calls use a temporary empty cwd under ignored data/tmp to obey the folder-only write restriction. project_doc_max_bytes=0 disables ancestor AGENTS injection, matching source 33’s effective empty out-of-repo cwd; this extra config option is recorded in every full request. Baseline imported options remain exactly unchanged.

- Baseline Granite already uses native json_object transport mode in notebook 33. Native-schema condition strengthens this to json_schema; Codex uses supported --output-schema. Free-text and analysis/solve-first Granite conditions remove json_object mode so prose can be returned. This is a necessary transport adaptation to the requested format and an explicit limitation of a pure prompt-only comparison. CLI options were checked with local help; no Anthropic judge remains so no Claude capability call is needed.

- Reference key: worked/grounded get only exact_answer scalar; code gets reference solution; instructions excluded (no extra key beyond constraints). data/reference_copy_audit.csv reports exact-text and normalized-AST reference matching plus source construction fields, not an unsupported near-copy claim. Reference is excluded from recommendation eligibility.

- Selection rule fixed in data/analysis_plan.json before new exam calls: choose a variant with positive paired 95% lower bound for at least 2 judges, or cheaper on all with strict savings on >=2 and no observed loss for all. Rank by mean gain, cost ratio, name. At most one aggregator, effort, and presentation choice, avoiding incompatible analysis-first/free-text/schema instructions. If none qualifies, retain baseline; recommended is then the identical cached condition, not an independent repeat. Independent confirmation is a new held-out split for choosing this notebook’s combination, but notebook 33 aggregate findings were already supplied.

- Development uses 4 unchanged source development cases, one per family. No regeneration or generator adjustments. Prior notebook 33 already established difficulty. These calls validate new formats and end-to-end flow; no per-item response-based amendments are allowed. CLI deterministic settings cannot be controlled like Granite temperature 0; majority at temperature 0 can be uninformative.

- Size knobs are at the top; live defaults to tiny smoke; explicit NB_PROFILE=full runs all methods. OpenRouter <=$5 is enforced before requests using usage costs plus conservative reservations, including unpriced/nonfinal calls. Global concurrent CLI calls <=2 and Granite <=3. Quota markers stop globally without a final-cache write or retries; policy filters are cached unreadable outcomes. In-flight replies after a stop go to the nonfinal ledger.

## Counts and headline-number sources

The result tables separate wrong, unreadable and undecided for BOTH readers. Accuracy includes unreadables at 0 and ties at 0.5. readable_accuracy uses only readable items, including undecided ties at 0.5. Bootstrap intervals resample items, not component calls. Paired gains resample the identical item-level differences. All intervals are 95%; eligibility intervals are exploratory without multiplicity correction.

- data/summary.csv: stage, judge, method, reader, n, correct, wrong, unreadable, undecided, accuracy, ci_low/ci_high, readable_accuracy, readable_ci_low/high, all_agree_rate, order_consistency, mean_calls, mean_dollars, mean_seconds, ceiling/floor.

- data/paired_comparisons.csv: gain, ci_low/high, fixed, broke, same, baseline_accuracy/method_accuracy, cost_ratio and dollar difference, using only paired complete outcome rows (reference n=90 per judge).

- data/family_summary.csv and trap_summary.csv: same fields by family/trap. Only 6 trap items per split; treat as descriptive. data/component_outcomes.csv and unreadable_summary.csv: physical component parsing categories, preserving returned keys. Compound outcome unreadable types in outcomes.csv mean multiple required components failed.

- data/outcomes.csv: stable item IDs, displayed order, better candidate, all raw keys, component parsed reads, score, time and dollars. data/request_usage.csv: every imported/new final request, model, origin, purpose, timestamps, cost and usage; data/nonfinal_attempts.jsonl is separate. data/results_ledger.jsonl is resumable outcomes, not primary raw cache.

| stage | judge | method | reader | n | accuracy | ci_low | ci_high | wrong | unreadable | undecided | readable_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| development | Granite 8B | baseline | strict | 4 | 0.75 | 0.25 | 1 | 1 | 0 | 0 | 0.75 |
| development | Granite 8B | baseline | lenient | 4 | 0.75 | 0.25 | 1 | 1 | 0 | 0 | 0.75 |
| development | Granite 8B | both_orders | strict | 4 | 0.625 | 0.5 | 0.875 | 0 | 0 | 3 | 0.625 |
| development | Granite 8B | both_orders | lenient | 4 | 0.625 | 0.5 | 0.875 | 0 | 0 | 3 | 0.625 |
| development | Granite 8B | effort_high | strict | 4 | 0.25 | 0 | 0.75 | 0 | 3 | 0 | 1 |
| development | Granite 8B | effort_high | lenient | 4 | 0.25 | 0 | 0.75 | 0 | 3 | 0 | 1 |
| development | Granite 8B | effort_low | strict | 4 | 0.5 | 0 | 1 | 1 | 1 | 0 | 0.66666667 |
| development | Granite 8B | effort_low | lenient | 4 | 0.5 | 0 | 1 | 1 | 1 | 0 | 0.66666667 |
| development | Granite 8B | free_text | strict | 4 | 0.5 | 0 | 1 | 1 | 1 | 0 | 0.66666667 |
| development | Granite 8B | free_text | lenient | 4 | 0.75 | 0.25 | 1 | 1 | 0 | 0 | 0.75 |
| development | Granite 8B | majority5 | strict | 4 | 0.5 | 0 | 1 | 1 | 1 | 0 | 0.66666667 |
| development | Granite 8B | majority5 | lenient | 4 | 0.75 | 0.25 | 1 | 1 | 0 | 0 | 0.75 |
| development | Granite 8B | native_schema | strict | 4 | 0.75 | 0.25 | 1 | 1 | 0 | 0 | 0.75 |
| development | Granite 8B | native_schema | lenient | 4 | 0.75 | 0.25 | 1 | 1 | 0 | 0 | 0.75 |
| development | Granite 8B | reason_first | strict | 4 | 0 | 0 | 0 | 0 | 4 | 0 |  |
| development | Granite 8B | reason_first | lenient | 4 | 0.25 | 0 | 0.75 | 0 | 3 | 0 | 1 |
| development | Granite 8B | reference | strict | 3 | 1 | 1 | 1 | 0 | 0 | 0 | 1 |
| development | Granite 8B | reference | lenient | 3 | 1 | 1 | 1 | 0 | 0 | 0 | 1 |
| development | Granite 8B | single_answer | strict | 4 | 0.375 | 0.125 | 0.5 | 1 | 0 | 3 | 0.375 |
| development | Granite 8B | single_answer | lenient | 4 | 0.375 | 0.125 | 0.5 | 1 | 0 | 3 | 0.375 |
| development | Granite 8B | solve_first | strict | 4 | 0 | 0 | 0 | 0 | 4 | 0 |  |
| development | Granite 8B | solve_first | lenient | 4 | 0 | 0 | 0 | 0 | 4 | 0 |  |
| development | Luna | baseline | strict | 4 | 0.75 | 0.25 | 1 | 1 | 0 | 0 | 0.75 |
| development | Luna | baseline | lenient | 4 | 0.75 | 0.25 | 1 | 1 | 0 | 0 | 0.75 |
| development | Luna | both_orders | strict | 4 | 0.75 | 0.5 | 1 | 0 | 0 | 2 | 0.75 |
| development | Luna | both_orders | lenient | 4 | 0.75 | 0.5 | 1 | 0 | 0 | 2 | 0.75 |
| development | Luna | effort_high | strict | 4 | 0.75 | 0.25 | 1 | 1 | 0 | 0 | 0.75 |
| development | Luna | effort_high | lenient | 4 | 0.75 | 0.25 | 1 | 1 | 0 | 0 | 0.75 |
| development | Luna | effort_low | strict | 4 | 0.75 | 0.25 | 1 | 1 | 0 | 0 | 0.75 |
| development | Luna | effort_low | lenient | 4 | 0.75 | 0.25 | 1 | 1 | 0 | 0 | 0.75 |
| development | Luna | free_text | strict | 4 | 0.75 | 0.25 | 1 | 1 | 0 | 0 | 0.75 |
| development | Luna | free_text | lenient | 4 | 0.75 | 0.25 | 1 | 1 | 0 | 0 | 0.75 |
| development | Luna | majority5 | strict | 4 | 0.75 | 0.25 | 1 | 1 | 0 | 0 | 0.75 |
| development | Luna | majority5 | lenient | 4 | 0.75 | 0.25 | 1 | 1 | 0 | 0 | 0.75 |
| development | Luna | native_schema | strict | 4 | 0.75 | 0.25 | 1 | 1 | 0 | 0 | 0.75 |
| development | Luna | native_schema | lenient | 4 | 0.75 | 0.25 | 1 | 1 | 0 | 0 | 0.75 |
| development | Luna | reason_first | strict | 4 | 0 | 0 | 0 | 0 | 4 | 0 |  |
| development | Luna | reason_first | lenient | 4 | 1 | 1 | 1 | 0 | 0 | 0 | 1 |
| development | Luna | reference | strict | 3 | 1 | 1 | 1 | 0 | 0 | 0 | 1 |
| development | Luna | reference | lenient | 3 | 1 | 1 | 1 | 0 | 0 | 0 | 1 |
| development | Luna | single_answer | strict | 4 | 0.375 | 0.125 | 0.5 | 1 | 0 | 3 | 0.375 |
| development | Luna | single_answer | lenient | 4 | 0.375 | 0.125 | 0.5 | 1 | 0 | 3 | 0.375 |
| development | Luna | solve_first | strict | 4 | 0 | 0 | 0 | 1 | 3 | 0 | 0 |
| development | Luna | solve_first | lenient | 4 | 0.75 | 0.25 | 1 | 1 | 0 | 0 | 0.75 |
| development | Sol | baseline | strict | 4 | 1 | 1 | 1 | 0 | 0 | 0 | 1 |
| development | Sol | baseline | lenient | 4 | 1 | 1 | 1 | 0 | 0 | 0 | 1 |
| development | Sol | both_orders | strict | 4 | 1 | 1 | 1 | 0 | 0 | 0 | 1 |
| development | Sol | both_orders | lenient | 4 | 1 | 1 | 1 | 0 | 0 | 0 | 1 |
| development | Sol | effort_high | strict | 4 | 1 | 1 | 1 | 0 | 0 | 0 | 1 |
| development | Sol | effort_high | lenient | 4 | 1 | 1 | 1 | 0 | 0 | 0 | 1 |
| development | Sol | effort_low | strict | 4 | 1 | 1 | 1 | 0 | 0 | 0 | 1 |
| development | Sol | effort_low | lenient | 4 | 1 | 1 | 1 | 0 | 0 | 0 | 1 |
| development | Sol | free_text | strict | 4 | 1 | 1 | 1 | 0 | 0 | 0 | 1 |
| development | Sol | free_text | lenient | 4 | 1 | 1 | 1 | 0 | 0 | 0 | 1 |
| development | Sol | majority5 | strict | 4 | 1 | 1 | 1 | 0 | 0 | 0 | 1 |
| development | Sol | majority5 | lenient | 4 | 1 | 1 | 1 | 0 | 0 | 0 | 1 |
| development | Sol | native_schema | strict | 4 | 1 | 1 | 1 | 0 | 0 | 0 | 1 |
| development | Sol | native_schema | lenient | 4 | 1 | 1 | 1 | 0 | 0 | 0 | 1 |
| development | Sol | reason_first | strict | 4 | 0 | 0 | 0 | 0 | 4 | 0 |  |
| development | Sol | reason_first | lenient | 4 | 1 | 1 | 1 | 0 | 0 | 0 | 1 |
| development | Sol | reference | strict | 3 | 1 | 1 | 1 | 0 | 0 | 0 | 1 |
| development | Sol | reference | lenient | 3 | 1 | 1 | 1 | 0 | 0 | 0 | 1 |
| development | Sol | single_answer | strict | 4 | 0.75 | 0.5 | 1 | 0 | 0 | 2 | 0.75 |
| development | Sol | single_answer | lenient | 4 | 0.75 | 0.5 | 1 | 0 | 0 | 2 | 0.75 |
| development | Sol | solve_first | strict | 4 | 0 | 0 | 0 | 0 | 4 | 0 |  |
| development | Sol | solve_first | lenient | 4 | 1 | 1 | 1 | 0 | 0 | 0 | 1 |
| selection | Granite 8B | baseline | strict | 120 | 0.575 | 0.48333333 | 0.65833333 | 51 | 0 | 0 | 0.575 |
| selection | Granite 8B | baseline | lenient | 120 | 0.575 | 0.48333333 | 0.66666667 | 51 | 0 | 0 | 0.575 |
| selection | Granite 8B | both_orders | strict | 120 | 0.5875 | 0.54166667 | 0.63333333 | 5 | 3 | 83 | 0.6025641 |
| selection | Granite 8B | both_orders | lenient | 120 | 0.6 | 0.55822917 | 0.64583333 | 5 | 0 | 86 | 0.6 |
| selection | Granite 8B | reason_first | strict | 11 | 0 | 0 | 0 | 0 | 11 | 0 |  |
| selection | Granite 8B | reason_first | lenient | 11 | 0.45454545 | 0.18181818 | 0.72727273 | 0 | 6 | 0 | 1 |
| selection | Granite 8B | single_answer | strict | 120 | 0.43333333 | 0.4 | 0.46666667 | 12 | 5 | 102 | 0.45217391 |
| selection | Granite 8B | single_answer | lenient | 120 | 0.4375 | 0.40416667 | 0.46666667 | 12 | 4 | 103 | 0.45258621 |
| selection | Luna | baseline | strict | 120 | 0.7 | 0.61666667 | 0.78333333 | 36 | 0 | 0 | 0.7 |
| selection | Luna | baseline | lenient | 120 | 0.7 | 0.61666667 | 0.78333333 | 36 | 0 | 0 | 0.7 |
| selection | Luna | both_orders | strict | 120 | 0.70833333 | 0.65416667 | 0.7625 | 8 | 0 | 54 | 0.70833333 |
| selection | Luna | both_orders | lenient | 120 | 0.70833333 | 0.65416667 | 0.7625 | 8 | 0 | 54 | 0.70833333 |
| selection | Luna | reason_first | strict | 15 | 0 | 0 | 0 | 0 | 15 | 0 |  |
| selection | Luna | reason_first | lenient | 15 | 0.86666667 | 0.66666667 | 1 | 2 | 0 | 0 | 0.86666667 |
| selection | Luna | single_answer | strict | 120 | 0.53333333 | 0.48333333 | 0.58333333 | 13 | 1 | 84 | 0.53781513 |
| selection | Luna | single_answer | lenient | 120 | 0.53333333 | 0.48333333 | 0.58333333 | 13 | 1 | 84 | 0.53781513 |
| selection | Sol | baseline | strict | 120 | 0.95833333 | 0.91666667 | 0.99166667 | 5 | 0 | 0 | 0.95833333 |
| selection | Sol | baseline | lenient | 120 | 0.95833333 | 0.91666667 | 0.99166667 | 5 | 0 | 0 | 0.95833333 |
| selection | Sol | both_orders | strict | 120 | 0.95833333 | 0.925 | 0.98333333 | 2 | 0 | 6 | 0.95833333 |
| selection | Sol | both_orders | lenient | 120 | 0.95833333 | 0.925 | 0.98333333 | 2 | 0 | 6 | 0.95833333 |
| selection | Sol | reason_first | strict | 15 | 0 | 0 | 0 | 0 | 15 | 0 |  |
| selection | Sol | reason_first | lenient | 15 | 1 | 1 | 1 | 0 | 0 | 0 | 1 |
| selection | Sol | single_answer | strict | 120 | 0.825 | 0.775 | 0.875 | 4 | 1 | 32 | 0.83193277 |
| selection | Sol | single_answer | lenient | 120 | 0.825 | 0.775 | 0.875 | 4 | 1 | 32 | 0.83193277 |

### Unreadable physical replies by condition/type
| stage | judge | method | reader | unreadable_type | calls |
| --- | --- | --- | --- | --- | --- |
| development | Granite 8B | effort_high | lenient | empty | 3 |
| development | Granite 8B | effort_high | strict | empty | 3 |
| development | Granite 8B | effort_low | lenient | empty | 1 |
| development | Granite 8B | effort_low | strict | empty | 1 |
| development | Granite 8B | free_text | strict | no_parseable_text | 1 |
| development | Granite 8B | majority5 | strict | no_parseable_json | 1 |
| development | Granite 8B | reason_first | lenient | no_parseable_json | 3 |
| development | Granite 8B | reason_first | strict | no_parseable_json | 4 |
| development | Granite 8B | solve_first | lenient | no_parseable_json | 2 |
| development | Granite 8B | solve_first | lenient | timeout | 2 |
| development | Granite 8B | solve_first | strict | no_parseable_json | 2 |
| development | Granite 8B | solve_first | strict | timeout | 2 |
| development | Luna | reason_first | strict | no_parseable_json | 4 |
| development | Luna | solve_first | strict | no_parseable_json | 3 |
| development | Sol | reason_first | strict | no_parseable_json | 4 |
| development | Sol | solve_first | strict | no_parseable_json | 4 |
| selection | Granite 8B | both_orders | strict | no_parseable_json | 3 |
| selection | Granite 8B | reason_first | lenient | no_parseable_json | 2 |
| selection | Granite 8B | reason_first | lenient | schema_failure | 3 |
| selection | Granite 8B | reason_first | lenient | transport_error | 1 |
| selection | Granite 8B | reason_first | strict | no_parseable_json | 10 |
| selection | Granite 8B | reason_first | strict | transport_error | 1 |
| selection | Granite 8B | single_answer | lenient | no_parseable_json | 4 |
| selection | Granite 8B | single_answer | strict | no_parseable_json | 4 |
| selection | Granite 8B | single_answer | strict | schema_failure | 1 |
| selection | Luna | reason_first | strict | no_parseable_json | 15 |
| selection | Luna | single_answer | lenient | timeout | 1 |
| selection | Luna | single_answer | strict | timeout | 1 |
| selection | Sol | reason_first | strict | no_parseable_json | 15 |
| selection | Sol | single_answer | lenient | transport_error | 1 |
| selection | Sol | single_answer | strict | transport_error | 1 |

### Completed outcomes and required component calls
| stage | judge | method | items | logical_calls | attempts |
| --- | --- | --- | --- | --- | --- |
| development | Granite 8B | baseline | 4 | 4 | 5 |
| development | Granite 8B | both_orders | 4 | 8 | 11 |
| development | Granite 8B | effort_high | 4 | 4 | 12 |
| development | Granite 8B | effort_low | 4 | 4 | 6 |
| development | Granite 8B | free_text | 4 | 4 | 6 |
| development | Granite 8B | majority5 | 4 | 20 | 23 |
| development | Granite 8B | native_schema | 4 | 4 | 5 |
| development | Granite 8B | reason_first | 4 | 4 | 10 |
| development | Granite 8B | reference | 3 | 3 | 3 |
| development | Granite 8B | single_answer | 4 | 8 | 8 |
| development | Granite 8B | solve_first | 4 | 4 | 12 |
| development | Luna | baseline | 4 | 4 | 4 |
| development | Luna | both_orders | 4 | 8 | 8 |
| development | Luna | effort_high | 4 | 4 | 4 |
| development | Luna | effort_low | 4 | 4 | 4 |
| development | Luna | free_text | 4 | 4 | 4 |
| development | Luna | majority5 | 4 | 20 | 20 |
| development | Luna | native_schema | 4 | 4 | 4 |
| development | Luna | reason_first | 4 | 4 | 4 |
| development | Luna | reference | 3 | 3 | 3 |
| development | Luna | single_answer | 4 | 8 | 8 |
| development | Luna | solve_first | 4 | 4 | 4 |
| development | Sol | baseline | 4 | 4 | 4 |
| development | Sol | both_orders | 4 | 8 | 8 |
| development | Sol | effort_high | 4 | 4 | 4 |
| development | Sol | effort_low | 4 | 4 | 4 |
| development | Sol | free_text | 4 | 4 | 4 |
| development | Sol | majority5 | 4 | 20 | 20 |
| development | Sol | native_schema | 4 | 4 | 4 |
| development | Sol | reason_first | 4 | 4 | 4 |
| development | Sol | reference | 3 | 3 | 3 |
| development | Sol | single_answer | 4 | 8 | 8 |
| development | Sol | solve_first | 4 | 4 | 4 |
| selection | Granite 8B | baseline | 120 | 120 | 128 |
| selection | Granite 8B | both_orders | 120 | 240 | 260 |
| selection | Granite 8B | reason_first | 11 | 11 | 27 |
| selection | Granite 8B | single_answer | 120 | 240 | 252 |
| selection | Luna | baseline | 120 | 120 | 120 |
| selection | Luna | both_orders | 120 | 240 | 240 |
| selection | Luna | reason_first | 15 | 15 | 15 |
| selection | Luna | single_answer | 120 | 240 | 240 |
| selection | Sol | baseline | 120 | 120 | 120 |
| selection | Sol | both_orders | 120 | 240 | 240 |
| selection | Sol | reason_first | 15 | 15 | 15 |
| selection | Sol | single_answer | 120 | 240 | 240 |

## Recommendation
Not selected yet; no confirmation claim may be made.

## Candidate worked examples
Full input, both candidates, ground truth, exact prompt, raw text, strict/lenient parsed reads and cache keys: data/worked_examples.json. Stable-first automatic selection is recorded in each entry. Categories absent from this export were not yet observed; never invent an error.

- typical_code: test-code-000, Granite 8B, baseline, selection; better=B, lenient score=1.0, strict=1.0, unreadable=none. Raw keys: ["7c6e39adbb86cddd6d3085f01d0ced9a69d024dfe1da9a708bf0d16c3c929b03"].

- typical_worked: test-worked-008, Luna, baseline, selection; better=B, lenient score=1.0, strict=1.0, unreadable=none. Raw keys: ["a738d28733f8ef43c28a04f76ebe6e77c17145692117ef2b6ed6f134a4a22117"].

- typical_instructions: test-instructions-000, Granite 8B, baseline, selection; better=A, lenient score=1.0, strict=1.0, unreadable=none. Raw keys: ["1673c8e8485a8241f76e96f1c796ec2ed992c134be902f03c5ce5500cff642f6"].

- typical_grounded: test-grounded-000, Sol, baseline, selection; better=A, lenient score=1.0, strict=1.0, unreadable=none. Raw keys: ["35a399db51159837a04ad9caf88288762512fcee4433a54470209290db47d71c"].

- end_to_end: test-code-000, Granite 8B, single_answer, selection; better=B, lenient score=0.5, strict=0.5, unreadable=none. Raw keys: ["756fe5d733a2f94376041e720d36a198b4fa310682f6f60616ae631ad2606a09", "6a610c722c5e1345aa62fd0d227ed6a5051a5e59ab81cd23ef76981e0aa85e0a"].

- fixed: test-code-017, Luna, both_orders, selection; better=A, lenient score=0.5, strict=0.5, unreadable=none. Raw keys: ["10970a1cb1803b2974f361f9ffc4fa02c3aae789bf5e163b2b29fdc404106267", "00ce9ff01370983eb4554a50da93850525f344f16f1e677ccfe790b68ea64fa9"].

- fixed: test-code-017, Luna, reason_first, selection; better=A, lenient score=1.0, strict=0.0, unreadable=none. Raw keys: ["5faefc9137bda93ba21ffc7184c9a161e37130372495348d6f885d800c0cf7aa"].

- fixed: test-code-017, Luna, single_answer, selection; better=A, lenient score=0.5, strict=0.5, unreadable=none. Raw keys: ["2111e0ba89be2df21088ec1ea7ffefa5a866462a8e2149f6d26c7812a1dca8dc", "320d66e4ca70c5157508642544aa8adad8928e5af60480b7e28bb54a7d368602"].

- broke: test-code-000, Granite 8B, both_orders, selection; better=B, lenient score=0.5, strict=0.5, unreadable=none. Raw keys: ["7c6e39adbb86cddd6d3085f01d0ced9a69d024dfe1da9a708bf0d16c3c929b03", "bdaddd5857e69a8af25bd51729043a4bfde2261f728c1652004024e6ce3945db"].

- broke: test-code-000, Granite 8B, single_answer, selection; better=B, lenient score=0.5, strict=0.5, unreadable=none. Raw keys: ["756fe5d733a2f94376041e720d36a198b4fa310682f6f60616ae631ad2606a09", "6a610c722c5e1345aa62fd0d227ed6a5051a5e59ab81cd23ef76981e0aa85e0a"].

- broke: test-code-000, Luna, single_answer, selection; better=B, lenient score=0.0, strict=0.0, unreadable=none. Raw keys: ["4f0db1f65cbad87cde24021fd23f7319affead758980e60affb0689438c3a2ec", "9493dbbe827c7ab650771255d9479827e3805c74691ed4a1ad1f3c7ac5a1fd21"].

- wrong: dev10d-code-000, Luna, single_answer, development; better=B, lenient score=0.0, strict=0.0, unreadable=none. Raw keys: ["5f96fd91c9543fa8ef9866521be40d4e3bc234bc83165d4c344967de87a5c0ed", "dcb9b46b6c5682cce51cf5ba99088f186a6b572ec5678f4525887709e455447d"].

- wrong: dev10d-grounded-000, Granite 8B, single_answer, development; better=B, lenient score=0.0, strict=0.0, unreadable=none. Raw keys: ["8e176a755cf15b830e492bd2904c6981d4eefcd1347c14d9f5f1b43243777150", "7b2c67f27cd937cd104053bc0edcc45ba5d7eccc2ef98158efd7820f83813256"].

- wrong: dev10d-instructions-000, Luna, baseline, development; better=B, lenient score=0.0, strict=0.0, unreadable=none. Raw keys: ["1786710b37196902a4022b41148e2f7959f2a0c4812566f8f0fd6628dfafb9f6"].

- unreadable_lenient: dev10d-code-000, Granite 8B, solve_first, development; better=B, lenient score=0.0, strict=0.0, unreadable=no_parseable_json. Raw keys: ["2a2b71d2cf50b84c56f395a3dc313d2836cfe67e366880cb5b3db6f2ebeb9745"].

  Raw excerpt: "I will now carefully analyze the task and both candidate answers to determine which is correct.\n\nFirst, let's restate the task clearly and precisely as given:\n\n> Write Python 3 function solve(rows). Before the main rule, perform this audit scan in ORIGINAL zero-based order. For an integer row its weight is that integer. For a log-string row its weight is the signed integer between pipes. For a list row its weight is the sum of integer fields excluding booleans plus the lengths of all string fields. Start state at 11. Keep a row if (state + weight + original_index) modulo 13 is not 10, or if it is the last original row. After deciding, update state for EVERY row, including omitted rows: reset"

- unreadable_lenient: dev10d-grounded-000, Granite 8B, effort_high, development; better=B, lenient score=0.0, strict=0.0, unreadable=empty. Raw keys: ["f73e863974d5db1bd5c3c7eef3754e4ac08654fdfd5aa27aff008a5e526fb709"].

  Raw excerpt: ''

- unreadable_lenient: dev10d-grounded-000, Granite 8B, effort_low, development; better=B, lenient score=0.0, strict=0.0, unreadable=empty. Raw keys: ["de0a6baa7f225e6e8fd7e41b72e02e4a9244b7021d23bd442316ae1d3b885967"].

  Raw excerpt: ''

- strict_format_recovery: dev10d-code-000, Granite 8B, reason_first, development; better=B, lenient score=1.0, strict=0.0, unreadable=none. Raw keys: ["515656dd8c1c6f4cad1af82a3864f55073f4b842bbe8ac74bf1693195a19b1c9"].

  Raw excerpt: 'The task specifies a complex preprocessing step involving a state machine that filters rows based on weights and indices, updates the state for every row (including omitted ones), rotates the kept list left by `final_state % kept_length`, and then applies a "main rule" to compute expiry days from `[day, lifetime]` pairs.\n\nBoth answers attempt to implement the full task but differ in the main rule logic. Answer A uses `while x % 7 in (4, 5): x += 1`, while Answer B uses `while x % 7 in (5, 6): x += 1`.\n\nThe main rule states: "Move that expiry forward past Saturday/Sunday (remainders 5,6)." In zero-based days where day 0 = Monday, days 5 = Saturday and 6 = Sunday. Thus, if the expiry falls on '

- strict_format_recovery: dev10d-code-000, Luna, reason_first, development; better=B, lenient score=1.0, strict=0.0, unreadable=none. Raw keys: ["66c41f7b35eba8015d94877c9fac64cca824f175523597ec9999bce88f8552ed"].

  Raw excerpt: 'Answer A is incorrect because it moves expiries forward when the remainder is 4 or 5, but with day zero as Monday, Saturday and Sunday have remainders 5 and 6. Answer B uses the correct weekend remainders and otherwise implements the audit scan, state updates, rotation, and input-order expiry calculation as specified.\n\n{"winner":"B","confidence":100,"reason":"B correctly moves expiries past remainders 5 and 6 (Saturday and Sunday). A incorrectly uses remainders 4 and 5; both answers otherwise implement the audit and rotation rules."}'

- strict_format_recovery: dev10d-code-000, Luna, solve_first, development; better=B, lenient score=1.0, strict=0.0, unreadable=none. Raw keys: ["0aab65b4df3d4c097d29d0f877548f1274894220af5e91f026ac800b43e5c4ee"].

  Raw excerpt: 'The audit must keep rows based on the original-order state and weight, update the state for every row, then rotate kept rows left by the final state modulo their count. For each remaining `[day, lifetime]`, compute `day + lifetime` and advance it until its remainder modulo 7 is not 5 or 6.\n\n{"winner":"B","confidence":100,"reason":"B implements the audit scan, state updates, and final rotation correctly, and advances expiries past weekend remainders 5 and 6. A incorrectly treats remainders 4 and 5 as weekends."}'

- undecided: dev10d-code-000, Granite 8B, single_answer, development; better=B, lenient score=0.5, strict=0.5, unreadable=none. Raw keys: ["49c50895aead1387c43c4700f7ac2cf2c49bb5196e4d838398dcfa1df7f0a978", "4c068c0eeba7522584ed383e7034cb9116ac19249fdc2d9cac5b9ac8bc065c64"].

- undecided: dev10d-grounded-000, Granite 8B, both_orders, development; better=B, lenient score=0.5, strict=0.5, unreadable=none. Raw keys: ["2f2eb6f1691b61297bb2c2d0e722a997dc43dde47733f0bbbb6fdb724ce22ae0", "d5c51bccbe0c5d068815e3389c3646a01cd272048a42d2c9e41296888329b59e"].

## Exact prompts

data/prompt_templates.json holds all exact template texts. data/analysis_plan.json fixes format readers and combination construction. Full rendered prompt AND model/settings/payload are in every keyed cache request; worked_examples.json repeats selected prompts. data/pair_schema.json and single_schema.json hold native schemas. No hidden task labels are included except the explicit reference condition.

## Model table

| name | pinned_version | provider | access | size | precision | license | hugging_face_id | settings | date | date_basis | date_source | why_included | pin_limitation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Sol | gpt-6.1-sol | OpenAI | codex exec | Not published | Not published | Proprietary |  | reasoning effort medium; no tools; isolated empty cwd; harness varies effort, response format and prompt as recorded per request | 2026-04-30 | training cutoff | https://developers.openai.com/api/docs/models/gpt-6.1-sol | Strong judge; effects have room mainly in code and instructions | Requested version ID; not independently verified immutable |
| Luna | gpt-6-luna | OpenAI | codex exec | Not published | Not published | Proprietary |  | reasoning effort medium; no tools; isolated empty cwd; harness varies effort, response format and prompt as recorded per request | 2026-05-18 | training cutoff | https://developers.openai.com/api/docs/models/gpt-6-luna | Mid judge replacing policy-blocked Haiku; worked and instructions below ceiling | Requested version ID; not independently verified immutable |
| Granite 8B | ibm-granite/granite-4.2-8b-20260831 | coreweave/bf16 | OpenRouter chat | 8.8B dense | BF16 | Apache-2.0 | ibm-granite/granite-4.2-8b | reasoning none; temperature 0; max_tokens 1600 judgments / 2600 solves; native JSON object mode; harness varies effort, response format and prompt as recorded per request | 2026-08-31 | catalog release fallback | https://openrouter.ai/ibm-granite/granite-4.2-8b | Small cheap open-weight judge; same pin/provider as notebook 33 |  |

Metadata is copied from frozen notebook 33 (checked 2026-10-30); CLI version IDs are requested pins, not independently verified immutable dated IDs. Pricing is the same inherited reported-token estimate, not actual CLI billing. Granite catalog/endpoints are copied and a live catalog verification snapshot is saved when probes run.

## Chronological run log for Claude’s PROTOCOL.md

data/run_log.jsonl contains timestamped preparation, probes, development, freeze, selection, recommendation, confirmation, retry and stop events. data/attempt_lifecycle.jsonl records each started/returned new call; data/nonfinal_attempts.jsonl preserves nonfinal quota streams. data/freeze_record.json contains all pre-test hashes; data/source_manifest.json records source hashes. No generator parameter amendments were made. data/transport_amendments.json records the pre-selection hard-deadline change after two development requests hung beyond their socket timeout. data/interrupted_attempts.json includes conservative reservations for unreturned requests. These unknown-charge interrupted sends must be added to returned-attempt counts; their actual usage/latency is unknown.

```json
{
  "version": "judge-harness-v1.0",
  "at": "2026-10-30T17:56:52.053008+00:00",
  "hash_normalization": "CRLF to LF",
  "seed": 3610302026,
  "source_commit": "cf854303",
  "hashes": {
    "from_33/exam_v1.jsonl": "c1c88cfb0bfee1ea0724579c1324f1b0903170afd8ccebec5c183de7c4fe5ae0",
    "from_33/reading_rules_v1.py": "d21f4f77671fd8dbe5825c123f48b26d9ff5e4c9474046ba7986ee64340b6a14",
    "split.csv": "4fdd8d768ee0da0aa309ed39b7c6cd6b6f4055f4ebbf776699d957683831e8e5",
    "prompt_templates.json": "6fd63fa4b1bb916deda32d92187b030becb2d7064df8c79455cd994aa94f6327",
    "analysis_plan.json": "cdce41458dbeece3ec5c525aefb71c5187aa381e17d0ade9387ef87b79d97e77",
    "models.json": "192d815a04b676405fda09466b3ba07ac0ed9a0db157be4820976aae86c43606",
    "date_provenance.json": "2a20a211d46f717072574cd8e496c98064da71738a657d58a053dd5af4110dbf",
    "pair_schema.json": "9a853064ca88ce8b01d01ed7b181a7ba276780224641e8883a4aca76f9a8e030",
    "single_schema.json": "2f50830d7b093f68311bccb0ae24a74713291ff3d4abb3ebfc55d1a5392d5f00",
    "harness_code.py": "5ff86a10bdcce82109b3fde79ce4812919b4dd630fce1aeb91b5d1a31d2dcb30"
  },
  "development_ids": [
    "dev10d-code-000",
    "dev10d-worked-000",
    "dev10d-instructions-000",
    "dev10d-grounded-000"
  ],
  "no_generator_changes": true,
  "code_amendment_at": "2026-10-30T18:40:07.659205+00:00",
  "code_amendment_record": "client_transport_amendment.json",
  "prior_freeze": "freeze_before_client_resource_fix.json"
}
```

### client_transport_amendment.json
```json
{
  "at": "2026-10-30T18:39:33.576580+00:00",
  "phase": "Selection unary condition in progress; no choices selected, no confirmation results",
  "reason": "Luna test-grounded-043 original B produced Tokio panic: OS cannot spawn worker thread, insufficient system resources os error 1450. Timeout/failed response retained and not rescored.",
  "changes": [
    "Set TOKIO_WORKER_THREADS=2 on new CLI client processes; same model/options/prompt bytes; client environment included in new request keys",
    "Use local file handles for stdin/stdout/stderr and process.wait(timeout=600), avoiding blocking Windows pipe writes or EOF waits that can bypass communicate timeout; prompt text written with same native newline translation as prior text pipe",
    "Retain all completed outcomes and all caches; record interrupted sends and conservative reservations; resume missing outcomes only"
  ],
  "unchanged": [
    "240 items",
    "120/120 split",
    "prompt templates",
    "judge models/pins",
    "reasoning conditions",
    "strict and lenient readers",
    "accuracy/tie rules",
    "recommendation rule"
  ],
  "interrupted_sends": 3,
  "interrupted_keys": [
    "52a804f27012944d7242209905e31a3adff53e7d2cc1504b453769df3a1d6712",
    "b28260ccce077636af49a49a2adfaab8382dbc1e1b3873abd55c325a9acdcd62",
    "25bcbb53eb64e9edb071a4cc7bf3b3784bfe17cd2840dd6760865098f6ceb05d"
  ],
  "documentation": "https://docs.rs/tokio/latest/tokio/runtime/struct.Builder.html#method.worker_threads",
  "doc_checked_on": "2026-10-30",
  "doc_note": "Tokio documents TOKIO_WORKER_THREADS as override for default core worker count; applying to Codex is an implementation inference verified by subsequent tiny CLI calls.",
  "old_freeze": "freeze_before_client_resource_fix.json",
  "old_code": "harness_code_before_client_resource_fix.py",
  "comparison_limitation": "Local transport startup/deadline changed after collection began. Retain failures and report diagnostic subtype and era; do not describe local OS failure as judge reasoning error."
}
```

### reporting_amendments.json
```json
{
  "at": "2026-10-30T17:53:39.359028+00:00",
  "phase": "After completed development, before any selection model calls/outcomes",
  "changes": [
    "logger permits a timestamp in an event record",
    "normalize NumPy group-key booleans to Python bool before bootstrap-label JSON serialization"
  ],
  "reason": "Development freeze logger raised duplicate at keyword; exception handoff then found subgroup exporter NumPy JSON type error",
  "unchanged": [
    "items",
    "prompts",
    "request settings",
    "readers",
    "scores",
    "recommendation rule"
  ],
  "prior_freeze": "freeze_before_reporting_fix.json",
  "no_new_calls_needed": true
}
```

### manual_timeout_enforcement.json
```json
{
  "at": "2026-10-30T18:22:36.009901+00:00",
  "event": "manual_cli_deadline_enforcement",
  "collector_pid": 40204,
  "cli_wrapper_pid": 20196,
  "key": "b37f9b87b69e6e832979e07facc11493b0c3a6c2ba72ca28420f9e42d0671a50",
  "purpose": "selection:single_answer:test-grounded-043:BA:0:B",
  "model": "gpt-6-luna",
  "configured_timeout_s": 600,
  "observed_age_s": 753.670134,
  "reason": "Verified notebook-owned cmd/node process tree exceeded configured timeout; terminated only this tree so collector can capture stdout/stderr. Other collections untouched. Cause of delayed timeout unknown; no parser or prompt change."
}
```

### manual_timeout_reply_audit.json
```json
{
  "at": "2026-10-30T18:35:40.896601+00:00",
  "key": "02e361723c5f47be337c20d17840f2d121ce28a8666b7267997ac2fe5b74a6c8",
  "item_id": "test-grounded-043",
  "judge": "Luna",
  "method": "single_answer",
  "component": "original B",
  "returncode": null,
  "error": "TimeoutExpired: CLI timeout",
  "returned_text": "",
  "stdout_excerpt": "",
  "stderr_excerpt": "\nthread 'codex-main' (56696) panicked at C:\\Users\\runneradmin\\.cargo\\registry\\src\\index.crates.io-1949cf8c6b5b557f\\tokio-1.52.3\\src\\runtime\\scheduler\\multi_thread\\worker.rs:503:13:\nOS can't spawn worker thread: Insufficient system resources exist to complete the requested service. (os error 1450)\nnote: run with `RUST_BACKTRACE=1` environment variable to display a backtrace\n",
  "usage": {},
  "seconds": 770.1352470999991,
  "note": "Manual enforcement of configured timeout is recorded separately; frozen readers unchanged. Inspect cache for full returned stream."
}
```

### reporting_caveats.json
```json
{
  "latency": "Baseline/both-orders use historical notebook 33 latency; new Granite calls include isolated-worker startup. Timing is contextual and should not be read as a randomized service-latency comparison. Per-item seconds are sums of timed transport durations (including client startup), excluding semaphore/queue waits. Whole-run wall time is reported separately.",
  "unknown_cost": "Returned OpenRouter charges are known costs only. Unpriced/timeout requests carry conservative reservations in request_usage.csv and interrupted_attempts.json and in spend.json accounted_openrouter_usd; nominal_dollars in outcomes is known OpenRouter charges plus CLI estimate, not an upper bound when usage is missing. Report these counts rather than claiming missing usage is free.",
  "intervals": "Empirical item bootstrap can be degenerate [1,1] at a ceiling or [0,0] at a floor. This does not prove perfect population accuracy.",
  "replay_environment": "Exact package versions recorded in environment.json and requirements-replay.txt.",
  "reporting_amendments": "Pre-selection logger/NumPy serialization fixes and chart sizing; clarification that readable-only intervals use the implemented bootstrap and strict free text permits whitespace; no item, prompt, reader or score change.",
  "paired_fixed_broke_columns": "paired_comparisons.csv fixed counts any positive score change, including wrong to undecided (0 to 0.5); broke counts any negative score change, including correct to undecided. These are score improvements/regressions, not necessarily full corrections/errors. Use outcome score and undecided fields when choosing examples.",
  "unary_call_order": "Unary calls grade original candidate A then original candidate B in fresh independent sessions; the two replies are mapped to original candidate IDs. Pairwise conditions use the frozen displayed baseline order. No unary prompt contains the other answer or a displayed position label.",
  "source_retry_archive": "All 27 prior Granite baseline retry attempts recovered from a byte-identical notebook 33 archive copied in notebook 34. Original source worktree disappeared during collection; source_retry_manifest.json records the cryptographic match and hashes. No files in notebook 34 were modified."
}
```

Recent events (full chronology in run_log.jsonl):
```json
[
 {
  "at": "2026-10-30T18:26:37.609084+00:00",
  "event": "retry",
  "key": "2b963afe642c9c5b436c8020a48fb9766e7ac74756b5308f3d32f48575771f0f",
  "purpose": "selection:single_answer:test-instructions-035:BA:0:A",
  "reason": "  "
 },
 {
  "at": "2026-10-30T18:27:17.188852+00:00",
  "event": "retry",
  "key": "aac867cbe3ecf3ef9fdbe2c9cc5ae116a9b00beb03ad0887f7b1aad61b1948c0",
  "purpose": "selection:single_answer:test-instructions-035:BA:0:A",
  "reason": "  "
 },
 {
  "at": "2026-10-30T18:36:20.582278+00:00",
  "event": "retry",
  "key": "c7c04fbb354ad8658f713d342653047cbb7ddd3fe2fd432e61d03f881daf828c",
  "purpose": "selection:single_answer:test-worked-019:BA:0:A",
  "reason": "  "
 },
 {
  "at": "2026-10-30T18:37:09.001756+00:00",
  "event": "retry",
  "key": "f4ba5d1d1541cceb3ad819478f9d2b39bbf4668d7b0c09e6390207b2924142c1",
  "purpose": "selection:single_answer:test-worked-019:BA:0:A",
  "reason": "  "
 },
 {
  "event": "client_transport_amendment",
  "at": "2026-10-30T18:39:33.576580+00:00",
  "phase": "Selection unary condition in progress; no choices selected, no confirmation results",
  "reason": "Luna test-grounded-043 original B produced Tokio panic: OS cannot spawn worker thread, insufficient system resources os error 1450. Timeout/failed response retained and not rescored.",
  "changes": [
   "Set TOKIO_WORKER_THREADS=2 on new CLI client processes; same model/options/prompt bytes; client environment included in new request keys",
   "Use local file handles for stdin/stdout/stderr and process.wait(timeout=600), avoiding blocking Windows pipe writes or EOF waits that can bypass communicate timeout; prompt text written with same native newline translation as prior text pipe",
   "Retain all completed outcomes and all caches; record interrupted sends and conservative reservations; resume missing outcomes only"
  ],
  "unchanged": [
   "240 items",
   "120/120 split",
   "prompt templates",
   "judge models/pins",
   "reasoning conditions",
   "strict and lenient readers",
   "accuracy/tie rules",
   "recommendation rule"
  ],
  "interrupted_sends": 3,
  "interrupted_keys": [
   "52a804f27012944d7242209905e31a3adff53e7d2cc1504b453769df3a1d6712",
   "b28260ccce077636af49a49a2adfaab8382dbc1e1b3873abd55c325a9acdcd62",
   "25bcbb53eb64e9edb071a4cc7bf3b3784bfe17cd2840dd6760865098f6ceb05d"
  ],
  "documentation": "https://docs.rs/tokio/latest/tokio/runtime/struct.Builder.html#method.worker_threads",
  "doc_checked_on": "2026-10-30",
  "doc_note": "Tokio documents TOKIO_WORKER_THREADS as override for default core worker count; applying to Codex is an implementation inference verified by subsequent tiny CLI calls.",
  "old_freeze": "freeze_before_client_resource_fix.json",
  "old_code": "harness_code_before_client_resource_fix.py",
  "comparison_limitation": "Local transport startup/deadline changed after collection began. Retain failures and report diagnostic subtype and era; do not describe local OS failure as judge reasoning error."
 },
 {
  "at": "2026-10-30T18:40:56.471097+00:00",
  "event": "invocation",
  "plan_hash": "cdce41458dbeece3ec5c525aefb71c5187aa381e17d0ade9387ef87b79d97e77",
  "profile": "full"
 },
 {
  "at": "2026-10-30T18:40:56.586915+00:00",
  "event": "retry",
  "key": "c7c04fbb354ad8658f713d342653047cbb7ddd3fe2fd432e61d03f881daf828c",
  "purpose": "selection:single_answer:test-worked-019:BA:0:A",
  "reason": "  "
 },
 {
  "at": "2026-10-30T18:40:59.588425+00:00",
  "event": "retry",
  "key": "f4ba5d1d1541cceb3ad819478f9d2b39bbf4668d7b0c09e6390207b2924142c1",
  "purpose": "selection:single_answer:test-worked-019:BA:0:A",
  "reason": "  "
 },
 {
  "at": "2026-10-30T18:57:11.598460+00:00",
  "event": "retry",
  "key": "1f9ea38035f194fd16442906ebf19df375e801861e181539539952adcd1e825d",
  "purpose": "selection:reason_first:test-code-002:AB:0:pair",
  "reason": "  "
 },
 {
  "at": "2026-10-30T18:57:29.057572+00:00",
  "event": "retry",
  "key": "1819804410fcadf408edc7d46ec9bc9ec1925b059523bee9856559328d6512f0",
  "purpose": "selection:reason_first:test-code-003:AB:0:pair",
  "reason": "  "
 },
 {
  "at": "2026-10-30T18:57:50.268369+00:00",
  "event": "retry",
  "key": "0781d1ce0686f500ac4ee352f658be4305384bc6383f018ab90039763ee17227",
  "purpose": "selection:reason_first:test-code-007:BA:0:pair",
  "reason": "  "
 },
 {
  "at": "2026-10-30T18:58:20.610117+00:00",
  "event": "retry",
  "key": "105e5677be75c006b95f6535754c216750463b544d5777657c4bb3cad42c7068",
  "purpose": "selection:reason_first:test-code-002:AB:0:pair",
  "reason": "  "
 },
 {
  "at": "2026-10-30T18:58:32.552553+00:00",
  "event": "retry",
  "key": "7ecafb9efc7c80d1a442cb9a2e86943faaf1e514f774e5fa12e2c23389d38ac0",
  "purpose": "selection:reason_first:test-code-013:BA:0:pair",
  "reason": " {'message': 'Provider returned error', 'code': 429, 'metadata': {'raw': 'ibm-granite/granite-4.2-8b is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate your rate limits: https://openrouter.ai/settings/integrations', 'provider_name': 'CoreWeave', 'is_byok': False, 'provider_error_code': 'rate_limit_exceeded', 'limit_source': 'upstream_provider_shared_pool', 'remedy_hint': 'Retry shortly, add your own provider key (https://openrouter.ai/settings/integrati"
 },
 {
  "at": "2026-10-30T18:58:55.850194+00:00",
  "event": "retry",
  "key": "a24ca4efca66a48725a654a9c85b1bf46f72e117c31225f1099869561b80fec1",
  "purpose": "selection:reason_first:test-code-011:AB:0:pair",
  "reason": "  "
 },
 {
  "at": "2026-10-30T18:59:03.150340+00:00",
  "event": "retry",
  "key": "1a9aa5f83f9a48ee1b16d78a1175c6d38e388aefe3147817c105fb389e0c5597",
  "purpose": "selection:reason_first:test-code-007:BA:0:pair",
  "reason": "  "
 },
 {
  "at": "2026-10-30T18:59:34.305173+00:00",
  "event": "retry",
  "key": "f74fc60ca7c2b246590b7e5d7d6e76c903e74391860d4696827e1b242011f530",
  "purpose": "selection:reason_first:test-code-017:BA:0:pair",
  "reason": "  "
 },
 {
  "at": "2026-10-30T18:59:51.883605+00:00",
  "event": "retry",
  "key": "653d8fc3e1c4de1153df1f497d6d8616b2f9a34afe5b2b7dad937d8dd1f53f6c",
  "purpose": "selection:reason_first:test-code-013:BA:0:pair",
  "reason": "  "
 },
 {
  "at": "2026-10-30T19:00:17.023527+00:00",
  "event": "retry",
  "key": "478deb281410833987757b3e4e369fe5cfab09df20f93d6a8713caa9db612f06",
  "purpose": "selection:reason_first:test-code-018:AB:0:pair",
  "reason": "  "
 },
 {
  "at": "2026-10-30T19:01:06.784211+00:00",
  "event": "retry",
  "key": "1564e8a359367b94aabf581ff859f7e52480c35263ed96f9d6366eee7e0630e3",
  "purpose": "selection:reason_first:test-code-017:BA:0:pair",
  "reason": "  "
 },
 {
  "at": "2026-10-30T19:01:18.379815+00:00",
  "event": "retry",
  "key": "b5cf9008fb48a50f26de0159d65226875b5093b3aed4a452affb40f540d4f45d",
  "purpose": "selection:reason_first:test-code-018:AB:0:pair",
  "reason": "  "
 },
 {
  "at": "2026-10-30T19:01:43.045884+00:00",
  "event": "retry",
  "key": "f280a0d8738616127e909cebbfbe8c8606f34073c0ce33055ba3739ffb075521",
  "purpose": "selection:reason_first:test-code-020:AB:0:pair",
  "reason": "  "
 },
 {
  "at": "2026-10-30T19:01:54.137923+00:00",
  "event": "retry",
  "key": "7a8c6ed457871f1398f7b9c52f31cfbe8c02770e2653174c00873000509c2ffb",
  "purpose": "selection:reason_first:test-code-022:BA:0:pair",
  "reason": "  "
 },
 {
  "at": "2026-10-30T19:03:20.337353+00:00",
  "event": "retry",
  "key": "081e3617276e45ed84bf8730a8a672d5552f7949f6193c79bfa32b334ec39ee3",
  "purpose": "selection:reason_first:test-code-020:AB:0:pair",
  "reason": "  "
 },
 {
  "at": "2026-10-30T19:04:15.255120+00:00",
  "event": "retry",
  "key": "5d58ed3577681d0d7a6c132235923fcb0815cfc919046908b3df8fa7e1fa6b5a",
  "purpose": "selection:reason_first:test-code-025:AB:0:pair",
  "reason": "  "
 },
 {
  "at": "2026-10-30T19:04:22.941126+00:00",
  "event": "retry",
  "key": "c207ebb2c66a8f940889b3e5b13e36259baa2f5633941248b1a19aa5fdc96261",
  "purpose": "selection:reason_first:test-code-022:BA:0:pair",
  "reason": "  "
 },
 {
  "at": "2026-10-30T19:04:45.696213+00:00",
  "event": "retry",
  "key": "197611b6dca3633cc0680c78cdcd7db329c1f4cd38d8ce1f654a25172dd6aaea",
  "purpose": "selection:reason_first:test-code-027:AB:0:pair",
  "reason": "  "
 },
 {
  "at": "2026-10-30T19:04:46.558131+00:00",
  "event": "retry",
  "key": "c148558829b92fdd92dfcc766eb09248028808b17ee3e63d7bc2365d38c75f1e",
  "purpose": "selection:reason_first:test-code-025:AB:0:pair",
  "reason": " {'message': 'Provider returned error', 'code': 429, 'metadata': {'raw': 'ibm-granite/granite-4.2-8b is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate your rate limits: https://openrouter.ai/settings/integrations', 'provider_name': 'CoreWeave', 'is_byok': False, 'provider_error_code': 'rate_limit_exceeded', 'limit_source': 'upstream_provider_shared_pool', 'remedy_hint': 'Retry shortly, add your own provider key (https://openrouter.ai/settings/integrati"
 },
 {
  "at": "2026-10-30T19:04:54.164559+00:00",
  "event": "retry",
  "key": "7209abf59a0b88b723546da52e919f9a2730a343f7cd6a9c7c91d35671279d09",
  "purpose": "selection:reason_first:test-code-028:BA:0:pair",
  "reason": "  "
 },
 {
  "at": "2026-10-30T19:05:57.449780+00:00",
  "event": "retry",
  "key": "5517ac92116908fc2956b0a929445e4940d8c0ac75e37b146cb56dd8ffb1edbe",
  "purpose": "selection:reason_first:test-code-027:AB:0:pair",
  "reason": "  "
 },
 {
  "at": "2026-10-30T19:06:54.038656+00:00",
  "event": "retry",
  "key": "b48a002a8de37ab217782ece12e365dd17bf066409bf15dc52487e2c7f32193c",
  "purpose": "selection:reason_first:test-code-028:BA:0:pair",
  "reason": "  "
 }
]
```

## Spend and wall time

| origin | model | backend | calls | openrouter_usd | cli_estimated_usd | unpriced_reservation | cli_usage_missing | summed_call_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 33 | gpt-6-luna | codex | 480 | 0 | 0.24207972 | 0 | 0 | 2698.9226 |
| 33 | gpt-6.1-sol | codex | 480 | 0 | 7.8850036 | 0 | 0 | 7340.9 |
| 33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | 507 | 0.07272309 | 0 | 0 | 0 | 3363.6698 |
| 36 | gpt-6-luna | codex | 325 | 0 | 0.1452831 | 0 | 1 | 2549.4316 |
| 36 | gpt-6.1-sol | codex | 327 | 0 | 5.406112 | 0 | 0 | 6247.2722 |
| 36 | ibm-granite/granite-4.2-8b-20260831 | openrouter | 387 | 0.07396113 | 0 | 0.0085427 | 0 | 6298.8598 |

data/spend.json has notebook 36 actual OpenRouter costs, conservative accounting bound, imported cost distinction, CLI list estimates and missing usage flags. CLI input/cached/output rates per million: Sol $2/$0.10/$10, Luna $0.10/$0.005/$0.50, inherited from 33. Nonfinal attempts may incur charges and are tracked separately. Source cache cost is not new spend.

Elapsed first started through last lifecycle event: 6469.7 seconds, including pauses. Sum of per-call seconds is parallel work, not wall time.

## Replay and live commands

From this notebook folder, default replay (zero model/network calls, fail on missing outcome/cache):
```powershell
Remove-Item Env:NB_LIVE -ErrorAction SilentlyContinue
$env:NB_PROFILE="full"
python -m nbconvert --to notebook --execute --inplace 36_judge_harness.ipynb --ExecutePreprocessor.timeout=-1
```

Live full/resume:
```powershell
$env:NB_LIVE="1"
$env:NB_PROFILE="full"
python -X utf8 -E -P data/tmp/run_live.py
```
The ignored run_live.py executes notebook code cells in order and logs failure/status. It can be recreated by reading each code cell and exec(compile(source,cell_label,"exec"), shared_namespace). Alternatively NB_LIVE=1 + NB_PROFILE=full with nbconvert collects the same cache keys. A stopped quota attempt is intentionally retried only on an explicit new live invocation, never automatically in the same collector.

## Raw-reply surprises and narrative limits

- Existing source test failures are concentrated in specific families. Do not describe small overall gains without the family counts. Check prefix-recovery markers before quoting truncated reasons as complete explanations.

- Analysis and own-solution formats can make strict parsing fail despite a usable verdict; compare strict with lenient, and show the actual reply. Labelled free-text parser scores that requested format, rather than demanding JSON.

- Two independently failed single answers can produce a confident wrong winner under the requested confidence tie-break. Check unary examples and report this as a property of the built rule.

- No causal claim about traps follows from 6 pairs per split; traps are descriptive, not randomized. References can turn code comparison into matching; report exact/AST match audits.

- Outputs still contain NARRATIVE TODO placeholders by explicit division of work. Claude must write README, PROTOCOL and markdown teaching narrative, then delete HANDOFF before committing. No git operations were performed.


## Additional reporting audits

{
  "at": "2026-10-30T19:06:56.689304+00:00",
  "scored_reader_rows_checked": 2500,
  "physical_attempt_records": 2515,
  "historical_source_attempts": 1467,
  "notebook36_started_attempts": 1048,
  "new_calls_before": 0,
  "new_calls_after": 0,
  "primary_scores_unchanged": true,
  "no_model_calls": true,
  "scope": "Descriptive postcollection diagnostics; not used by selection rule",
  "files": [
    "attempt_audit.csv",
    "physical_attempt_counts.csv",
    "transport_diagnostics.csv",
    "request_reading_summary.csv",
    "paired_transitions.csv",
    "paired_comparisons.csv",
    "condition_audit.csv",
    "unary_grades.csv",
    "unary_grade_summary.csv",
    "unary_comparisons.csv",
    "unary_pattern_summary.csv"
  ]
}

physical_attempt_counts.csv counts every cached return, nonfinal return and interrupted start exactly once. Source 33 is historical, not new spend. Cached source retries are included. Unknown charges and usage are marked explicitly; known sums are lower bounds when usage is absent.

paired_comparisons.csv now includes baseline/method correct, wrong, unreadable and undecided counts on matched items. fixed/broke retain their original score-change meaning. full_corrections/full_regressions distinguish wrong-to-correct from partial-credit tie transitions; paired_transitions.csv preserves all transitions.

unary_grade_summary.csv separates wrong individual grades from unreadable grades; unary_pattern_summary.csv counts both-pass, both-fail and separating verdicts. unary_grading_patterns.png is the descriptive error-analysis figure.

Physical attempts by stage, model and condition:

| origin | stage | judge | method | backend | started_attempts | returned_attempts | retry_attempts | final_component_attempts | openrouter_known_usd | openrouter_usage_missing | openrouter_known_or_reserved_usd | cli_estimated_usd | cli_usage_missing | returned_seconds | unreturned_attempts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 33 | source33 | Granite 8B | original_baseline | openrouter | 507 | 507 | 27 | 240 | 0.07272309 | 0 | 0.07272309 | 0 | 0 | 3363.6698 | 0 |
| 33 | source33 | Luna | original_baseline | codex | 480 | 480 | 0 | 240 | 0 | 0 | 0 | 0.24207972 | 0 | 2698.9226 | 0 |
| 33 | source33 | Sol | original_baseline | codex | 480 | 480 | 0 | 240 | 0 | 0 | 0 | 7.8850036 | 0 | 7340.9 | 0 |
| 36 | development | Granite 8B | baseline | openrouter | 5 | 5 | 1 | 4 | 0.00101904 | 0 | 0.00101904 | 0 | 0 | 90.575062 | 0 |
| 36 | development | Granite 8B | both_orders | openrouter | 11 | 11 | 3 | 8 | 0.00243834 | 0 | 0.00243834 | 0 | 0 | 330.76695 | 0 |
| 36 | development | Granite 8B | effort_high | openrouter | 12 | 12 | 8 | 4 | 0.00626925 | 0 | 0.00626925 | 0 | 0 | 412.75463 | 0 |
| 36 | development | Granite 8B | effort_low | openrouter | 6 | 6 | 2 | 4 | 0.00220194 | 0 | 0.00220194 | 0 | 0 | 125.03482 | 0 |
| 36 | development | Granite 8B | free_text | openrouter | 6 | 6 | 2 | 4 | 0.00192399 | 0 | 0.00192399 | 0 | 0 | 143.05803 | 0 |
| 36 | development | Granite 8B | majority5 | openrouter | 23 | 23 | 3 | 20 | 0.00345621 | 0 | 0.00345621 | 0 | 0 | 169.31119 | 0 |
| 36 | development | Granite 8B | native_schema | openrouter | 5 | 5 | 1 | 4 | 0.00052836 | 0 | 0.00052836 | 0 | 0 | 28.781757 | 0 |
| 36 | development | Granite 8B | reason_first | openrouter | 10 | 10 | 6 | 4 | 0.00624021 | 0 | 0.00624021 | 0 | 0 | 618.16479 | 0 |
| 36 | development | Granite 8B | reference | openrouter | 3 | 3 | 0 | 3 | 0.00016959 | 0 | 0.00016959 | 0 | 0 | 4.8447395 | 0 |
| 36 | development | Granite 8B | single_answer | openrouter | 8 | 8 | 0 | 8 | 0.00095385 | 0 | 0.00095385 | 0 | 0 | 43.784894 | 0 |
| 36 | development | Granite 8B | solve_first | openrouter | 18 | 12 | 8 | 10 | 0.00523056 | 8 | 0.0249048 | 0 | 0 | 817.02218 | 6 |
| 36 | development | Luna | baseline | codex | 4 | 4 | 0 | 4 | 0 | 0 | 0 | 0.00251672 | 0 | 23.869967 | 0 |
| 36 | development | Luna | both_orders | codex | 8 | 8 | 0 | 8 | 0 | 0 | 0 | 0.00307462 | 0 | 42.563144 | 0 |
| 36 | development | Luna | effort_high | codex | 4 | 4 | 0 | 4 | 0 | 0 | 0 | 0.0084361 | 0 | 69.1269 | 0 |
| 36 | development | Luna | effort_low | codex | 4 | 4 | 0 | 4 | 0 | 0 | 0 | 0.00448734 | 0 | 28.396069 | 0 |
| 36 | development | Luna | free_text | codex | 4 | 4 | 0 | 4 | 0 | 0 | 0 | 0.00249582 | 0 | 18.802772 | 0 |
| 36 | development | Luna | majority5 | codex | 20 | 20 | 0 | 20 | 0 | 0 | 0 | 0.0076703 | 0 | 157.36315 | 0 |
| 36 | development | Luna | native_schema | codex | 4 | 4 | 0 | 4 | 0 | 0 | 0 | 0.0056102 | 0 | 25.054526 | 0 |
| 36 | development | Luna | reason_first | codex | 4 | 4 | 0 | 4 | 0 | 0 | 0 | 0.00179276 | 0 | 25.740437 | 0 |
| 36 | development | Luna | reference | codex | 3 | 3 | 0 | 3 | 0 | 0 | 0 | 0.00120002 | 0 | 15.287659 | 0 |
| 36 | development | Luna | single_answer | codex | 8 | 8 | 0 | 8 | 0 | 0 | 0 | 0.00370588 | 0 | 36.252784 | 0 |
| 36 | development | Luna | solve_first | codex | 4 | 4 | 0 | 4 | 0 | 0 | 0 | 0.00203596 | 0 | 37.808187 | 0 |
| 36 | development | Sol | baseline | codex | 4 | 4 | 0 | 4 | 0 | 0 | 0 | 0.0528112 | 0 | 71.811133 | 0 |
| 36 | development | Sol | both_orders | codex | 8 | 8 | 0 | 8 | 0 | 0 | 0 | 0.1041084 | 0 | 117.17318 | 0 |
| 36 | development | Sol | effort_high | codex | 4 | 4 | 0 | 4 | 0 | 0 | 0 | 0.150646 | 0 | 74.486549 | 0 |
| 36 | development | Sol | effort_low | codex | 4 | 4 | 0 | 4 | 0 | 0 | 0 | 0.136142 | 0 | 63.632836 | 0 |
| 36 | development | Sol | free_text | codex | 4 | 4 | 0 | 4 | 0 | 0 | 0 | 0.0971016 | 0 | 58.001028 | 0 |
| 36 | development | Sol | majority5 | codex | 20 | 20 | 0 | 20 | 0 | 0 | 0 | 0.356296 | 0 | 309.44607 | 0 |
| 36 | development | Sol | native_schema | codex | 4 | 4 | 0 | 4 | 0 | 0 | 0 | 0.1228896 | 0 | 70.992053 | 0 |
| 36 | development | Sol | reason_first | codex | 4 | 4 | 0 | 4 | 0 | 0 | 0 | 0.0803732 | 0 | 123.98997 | 0 |
| 36 | development | Sol | reference | codex | 3 | 3 | 0 | 3 | 0 | 0 | 0 | 0.0298808 | 0 | 22.775171 | 0 |
| 36 | development | Sol | single_answer | codex | 8 | 8 | 0 | 8 | 0 | 0 | 0 | 0.1263524 | 0 | 176.42768 | 0 |
| 36 | development | Sol | solve_first | codex | 4 | 4 | 0 | 4 | 0 | 0 | 0 | 0.0688592 | 0 | 101.53215 | 0 |
| 36 | probe | Granite 8B | capability | openrouter | 2 | 2 | 0 | 0 | 9.66e-06 | 0 | 9.66e-06 | 0 | 0 | 7.9002252 | 0 |
| 36 | probe | Luna | capability | codex | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0.00131084 | 0 | 8.1602477 | 0 |
| 36 | probe | Luna | resource_client_probe | codex | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0.00015934 | 0 | 3.7113151 | 0 |
| 36 | probe | Sol | capability | codex | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0.0277768 | 0 | 16.398056 | 0 |
| 36 | probe | Sol | resource_client_probe | codex | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0.0033588 | 0 | 5.7243621 | 0 |
| 36 | selection | Granite 8B | reason_first | openrouter | 32 | 32 | 18 | 11 | 0.01398246 | 3 | 0.0176066 | 0 | 0 | 1662.1071 | 0 |
| 36 | selection | Granite 8B | single_answer | openrouter | 253 | 252 | 13 | 241 | 0.02953767 | 1 | 0.03100407 | 0 | 0 | 1844.7535 | 1 |
| 36 | selection | Luna | reason_first | codex | 15 | 15 | 0 | 15 | 0 | 0 | 0 | 0.0053371 | 0 | 89.690981 | 0 |
| 36 | selection | Luna | single_answer | codex | 241 | 240 | 0 | 240 | 0 | 0 | 0 | 0.0954501 | 2 | 1967.6035 | 1 |
| 36 | selection | Sol | reason_first | codex | 15 | 15 | 0 | 15 | 0 | 0 | 0 | 0.14357 | 0 | 261.59606 | 0 |
| 36 | selection | Sol | single_answer | codex | 243 | 242 | 0 | 240 | 0 | 0 | 0 | 3.905946 | 1 | 4773.2859 | 1 |


Transport diagnostic subtypes:

| origin | stage | judge | method | backend | disposition | diagnostic_subtype | attempts |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 33 | source33 | Granite 8B | original_baseline | openrouter | cached_return | returned_text | 476 |
| 33 | source33 | Granite 8B | original_baseline | openrouter | cached_return | token_limit | 31 |
| 33 | source33 | Luna | original_baseline | codex | cached_return | returned_text | 480 |
| 33 | source33 | Sol | original_baseline | codex | cached_return | returned_text | 480 |
| 36 | development | Granite 8B | baseline | openrouter | cached_return | returned_text | 4 |
| 36 | development | Granite 8B | baseline | openrouter | cached_return | token_limit | 1 |
| 36 | development | Granite 8B | both_orders | openrouter | cached_return | returned_text | 8 |
| 36 | development | Granite 8B | both_orders | openrouter | cached_return | token_limit | 3 |
| 36 | development | Granite 8B | effort_high | openrouter | cached_return | empty | 1 |
| 36 | development | Granite 8B | effort_high | openrouter | cached_return | returned_text | 1 |
| 36 | development | Granite 8B | effort_high | openrouter | cached_return | token_limit | 10 |
| 36 | development | Granite 8B | effort_low | openrouter | cached_return | returned_text | 3 |
| 36 | development | Granite 8B | effort_low | openrouter | cached_return | token_limit | 3 |
| 36 | development | Granite 8B | free_text | openrouter | cached_return | returned_text | 3 |
| 36 | development | Granite 8B | free_text | openrouter | cached_return | token_limit | 3 |
| 36 | development | Granite 8B | majority5 | openrouter | cached_return | returned_text | 19 |
| 36 | development | Granite 8B | majority5 | openrouter | cached_return | token_limit | 4 |
| 36 | development | Granite 8B | native_schema | openrouter | cached_return | returned_text | 4 |
| 36 | development | Granite 8B | native_schema | openrouter | cached_return | token_limit | 1 |
| 36 | development | Granite 8B | reason_first | openrouter | cached_return | returned_text | 1 |
| 36 | development | Granite 8B | reason_first | openrouter | cached_return | token_limit | 9 |
| 36 | development | Granite 8B | reference | openrouter | cached_return | returned_text | 3 |
| 36 | development | Granite 8B | single_answer | openrouter | cached_return | returned_text | 8 |
| 36 | development | Granite 8B | solve_first | openrouter | cached_return | timeout | 2 |
| 36 | development | Granite 8B | solve_first | openrouter | cached_return | token_limit | 10 |
| 36 | development | Granite 8B | solve_first | openrouter | interrupted_no_reply | interrupted_no_reply | 6 |
| 36 | development | Luna | baseline | codex | cached_return | returned_text | 4 |
| 36 | development | Luna | both_orders | codex | cached_return | returned_text | 8 |
| 36 | development | Luna | effort_high | codex | cached_return | returned_text | 4 |
| 36 | development | Luna | effort_low | codex | cached_return | returned_text | 4 |
| 36 | development | Luna | free_text | codex | cached_return | returned_text | 4 |
| 36 | development | Luna | majority5 | codex | cached_return | returned_text | 20 |
| 36 | development | Luna | native_schema | codex | cached_return | returned_text | 4 |
| 36 | development | Luna | reason_first | codex | cached_return | returned_text | 4 |
| 36 | development | Luna | reference | codex | cached_return | returned_text | 3 |
| 36 | development | Luna | single_answer | codex | cached_return | returned_text | 8 |
| 36 | development | Luna | solve_first | codex | cached_return | returned_text | 4 |
| 36 | development | Sol | baseline | codex | cached_return | returned_text | 4 |
| 36 | development | Sol | both_orders | codex | cached_return | returned_text | 8 |
| 36 | development | Sol | effort_high | codex | cached_return | returned_text | 4 |
| 36 | development | Sol | effort_low | codex | cached_return | returned_text | 4 |
| 36 | development | Sol | free_text | codex | cached_return | returned_text | 4 |
| 36 | development | Sol | majority5 | codex | cached_return | returned_text | 20 |
| 36 | development | Sol | native_schema | codex | cached_return | returned_text | 4 |
| 36 | development | Sol | reason_first | codex | cached_return | returned_text | 4 |
| 36 | development | Sol | reference | codex | cached_return | returned_text | 3 |
| 36 | development | Sol | single_answer | codex | cached_return | returned_text | 8 |
| 36 | development | Sol | solve_first | codex | cached_return | returned_text | 4 |
| 36 | probe | Granite 8B | capability | openrouter | cached_return | returned_text | 2 |
| 36 | probe | Luna | capability | codex | cached_return | returned_text | 2 |
| 36 | probe | Luna | resource_client_probe | codex | cached_return | returned_text | 1 |
| 36 | probe | Sol | capability | codex | cached_return | returned_text | 2 |
| 36 | probe | Sol | resource_client_probe | codex | cached_return | returned_text | 1 |
| 36 | selection | Granite 8B | reason_first | openrouter | cached_return | rate_limit | 3 |
| 36 | selection | Granite 8B | reason_first | openrouter | cached_return | returned_text | 6 |
| 36 | selection | Granite 8B | reason_first | openrouter | cached_return | token_limit | 23 |
| 36 | selection | Granite 8B | single_answer | openrouter | cached_return | returned_text | 238 |
| 36 | selection | Granite 8B | single_answer | openrouter | cached_return | token_limit | 14 |
| 36 | selection | Granite 8B | single_answer | openrouter | interrupted_no_reply | interrupted_no_reply | 1 |
| 36 | selection | Luna | reason_first | codex | cached_return | returned_text | 15 |
| 36 | selection | Luna | single_answer | codex | cached_return | local_resource_exhaustion | 1 |
| 36 | selection | Luna | single_answer | codex | cached_return | returned_text | 239 |
| 36 | selection | Luna | single_answer | codex | interrupted_no_reply | interrupted_no_reply | 1 |
| 36 | selection | Sol | reason_first | codex | cached_return | returned_text | 15 |
| 36 | selection | Sol | single_answer | codex | cached_return | returned_text | 241 |
| 36 | selection | Sol | single_answer | codex | cached_return | transport_error | 1 |
| 36 | selection | Sol | single_answer | codex | interrupted_no_reply | interrupted_no_reply | 1 |


source_retry_manifest.json

```json
{
  "at": "2026-10-30T18:50:21.678619+00:00",
  "source_commit": "cf854303",
  "source_path": "C:\\Users\\sandh\\nb-worktrees\\34-weak-tiebreakers\\notebooks\\judges\\34-weak-tiebreakers\\data\\from_33\\cache_requests.jsonl.gz",
  "final_replies": 1440,
  "additional_prior_attempts": 27,
  "copied_file": "from_33/prior_baseline_attempts.jsonl.gz",
  "sha256_bytes": "ddbe7a8da1572e19e7e4519d67a175624e29370ffa19ae6dff0fa99d8f30d15a",
  "working_archive_sha256_bytes": "fe1fab6d1658511391b3ee950009e714bd18c70a3964242ce1555e6d3a292fc5",
  "selection": "All earlier cached attempts sharing (model,purpose) with the 1440 reused final judgments; original records preserved",
  "no_new_model_calls": true,
  "status": "Recovered all 27 prior baseline attempts from byte-identical notebook 33 archive copy in notebook 34; only read the backup",
  "backup_sha256_bytes": "83596a8899816247771b6d6d1b416a66350c7dc6a87ccd55ad471e7aba3c493e",
  "initial_source_sha256_bytes": "83596a8899816247771b6d6d1b416a66350c7dc6a87ccd55ad471e7aba3c493e",
  "backup_matches_initial_source": true,
  "original_source_removed": true
}
```

client_resource_smoke.json

```json
[
  {
    "judge": "Sol",
    "key": "28377d91e0fd6d52b8b1f495074090683104db221805a23462a475409e41f3a4",
    "parsed": {
      "winner": "A",
      "confidence": 99.0,
      "reason": "Four is correct.",
      "unreadable_type": "",
      "recovery_type": "complete_json"
    },
    "client_environment": {
      "TOKIO_WORKER_THREADS": "2"
    },
    "seconds": 5.724362100008875
  },
  {
    "judge": "Luna",
    "key": "45238676f26961a3754f958a84bdb91a49267d2639a9d288fe76ab42e2a8bb18",
    "parsed": {
      "winner": "A",
      "confidence": 99.0,
      "reason": "Four is correct.",
      "unreadable_type": "",
      "recovery_type": "complete_json"
    },
    "client_environment": {
      "TOKIO_WORKER_THREADS": "2"
    },
    "seconds": 3.7113151000085054
  }
]
```
