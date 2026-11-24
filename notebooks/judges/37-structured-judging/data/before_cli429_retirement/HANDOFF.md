# Notebook 37 engineering handoff

## Status

Complete: live collection and executed zero-call replay verified.

Written UTC: 2026-11-24T09:25:58.969773+00:00. Final cache entries currently on disk: 8584. Replay audit: `data/replay_audit.json`.

**Material availability caveat:** Sol has 795 unreadable outcomes among 1380 newly collected pair-condition rows (lenient reader; all variants, excluding reused original baseline). Sustained generic HTTP429s dominate its transport failures. Comparison with its historical, fully readable baseline cannot isolate instruction effects. Use `summary.csv` columns unreadable/wrong/readable_accuracy and the transport-period ledger; do not describe these failures as wrong answers.

## Design as built and choices

- Claim issue #98 and source commit `cf854303` were supplied. No git/gh, issues, branches, PRs or commits were run. Repository edits are confined to this notebook folder. Claude must write README.md, PROTOCOL.md and all narrative, then handle git and root/group indexes. Notebook markdown consists of headings, required diagrams and `NARRATIVE TODO:` instructions.
- All 240 test pairs and 24 development pairs are copied unchanged in `data/from_33/exam_v1.jsonl`. All source freeze entries are copied and checked using CRLF-to-LF SHA-256. `data/from_33/SOURCE.md` records source paths, supplied commit and hashes. The notebook embeds copies of only the four checkers it needs and the exact notebook33 strict/lenient verdict readers. No repo helper is imported.
- Judges are Sol and Luna at CLI medium, and Granite 4.2 8B at its exact notebook33 pin/provider/settings: `ibm-granite/granite-4.2-8b-20260831`, `coreweave/bf16`, reasoning **none**, temperature zero, native JSON object mode, 1600 output tokens with transport truncation escalation to3200/6400. The amended brief explicitly preserves notebook33 settings; Granite does not support medium. Luna replaces Haiku because 73/120 Haiku instruction judgments were provider-filtered in notebook33, whereas Luna's overall0.715 leaves room to improve. No Haiku or Muse calls.
- Seed3710302026 balances displayed better-first exactly within family and trap status:120/240 overall,30/60 per family,6/12 code traps. Orders are identical across methods and polished copies. The selected120 controls have30/family,15 source-better A and15 source-better B, and15 displayed-better-first per family. Selection seed3710302063 fills fixed7/8 joint cells. The initial displayed-only selection was amended before test freeze without using any judge outcomes; data/design_amendments.json preserves old/new hashes and the reason. See order_assignment.json and polished_selection.json.
- Five methods on all240 items: free form, exact exam prompt, general rubric, item checklist, separate scoring. Own requirements adds60 instruction-family pairs; the task already lists these seven rules, so this repeats them in checklist form. General rubric scores five criteria0..2 for each answer, encoding the score arrays in `reason` so the exact three-field notebook33 verdict schema is retained. The fixed score-prefix reader additionally marks missing rubric scores schema_failure; this rule was fixed before test. Separate scoring uses two independent calls with a boolean array and a reason; code counts true values and keeps equal totals undecided. It adapts notebook33 JSON extraction and error taxonomy to this new response schema; no invented winner/confidence is requested for a single answer.
- Strict and lenient verdict readers are copied without modification. Complete-JSON-only is also reported so prefix recovery can be inspected. For separate scoring, either unreadable component makes the pair unreadable; equal readable totals are undecided. Readable-only accuracy still counts an undecided outcome as failure. Wrong excludes both unreadable and undecided. The rubric's auxiliary score prefix is required under every reader.
- Exact exam-prompt original baselines reuse720 selected final replies from notebook33, marked `origin` in the local cache; no original-baseline call is made again. Model, task, order, prompt, options/provider are asserted. Historical baseline resources describe its final retained attempt, not all historical retries; incremental baseline cost is zero. The entire original cache archive is also immutable under from_33 for audit.
- Deterministic polish only changes the worse answer. Code gains a module docstring and comments restating task rules. Worked answers gain a heading, three plan bullets and a claim the result was checked. Grounded answers gain a claim that every entry was checked against review date. Instructions gain markdown emphasis around a middle existing word, preserving words, digits, paragraphs and exact ends. Compare the entire checker signature excluding only normalized text; all120 passed, so all four families are retained. These claims are part of the presentation treatment; do not claim all added text is semantically empty. No original item or candidate is edited.
- Opus authors one3-8-question checklist per test task without either candidate, via medium `claude -p`. All240 are frozen before test judging. Eight duplicate instruction task prompts share the first full-request cache entry, giving232 unique author calls for240 checklists. This applies the required identical-request cache lock; no candidate text is included. No answer-based retries or per-item generator changes. Quality: instructions use a conservative keyword-and-value recognizer against seven exact rules; this measures named rules approximately, not semantic equivalence. Other180 items use one Opus fixed-category audit (`present`, `partial`, `absent`, `unclear`) using task, checklist and decisive checker evidence. Audits are model judgments, not a second executable oracle. Exact quality prompt and code are frozen when freeze_record.json is present.
- Before test collection, Codex additionally disables ancestor project instructions with project_doc_max_bytes=0 because the D: temporary directories are inside this checkout. Offline prompt inspection confirmed repository guidance would otherwise enter; the zero-byte setting removes it. Source baselines were collected outside the repo and are reused with every original option checked apart from this equivalent isolation safeguard. All development and new test Codex calls use the isolation setting. Earlier smoke calls remain diagnostic history, with their original settings recorded; they never supply test verdicts. No extra data generation or difficulty tuning: reuse the fixed level10 exam. Development uses notebook33's24 frozen dev pairs on free form and checklist for each judge, with separate smoke fixtures. Any smoke/development reading issues are reported; prompts are not tuned to test failures.
- Wilson95% intervals for proportions;5000 paired item-bootstrap percentile95% intervals for differences, fixed seed. Exact two-sided sign p-values are exploratory and unadjusted over many comparisons. Main paired comparisons are against the exam prompt; family and original trap subgroups are included.12 original traps, all code, are too few to rank methods. Controlled polish comparisons share items/order but use independent stochastic calls; no same-prompt repeat control exists.
- CLI concurrency2 codex and2 claude; OpenRouter3 per model; no Muse. Full-request per-key locks prevent duplicate in-flight requests. Transport retries only transient429/5xx/capacity/rate-limit and truncation, at most3 attempts. Policy refusals remain unreadable cached outcomes without retry. Usage/quota/credit-limit messages in error channels stop cleanly, keeping blocked and drained requests nonfinal. The pretest2026-10-30 transport amendment excludes successful model content from quota and transient-error matching;13 guard/cache tests pass in transport_amendment_validation.json. The prior false-positive and drained attempts stay in nonfinal_attempts.jsonl and were re-requested normally. OpenRouter guard reserves conservatively before each request and accounts returned usage, including capability/development/smoke. CLI estimates use returned tokens at Sol$2/$10 and Luna$0.10/$0.50 per million with cached input at5%; Claude uses reported CLI list cost. Estimates are not subscription charges.

## Exact planned counts and current cached counts

Main test design: 4860 pair-condition rows;5580 logical judge calls, comprising4860 new calls and720 reused baseline final replies. Per judge: free form240, exam prompt240 reused, general rubric240, item checklist240, separate scoring480 calls for240 pairs, own requirements60; polished free form120, exam prompt120, checklist120. This is1620 new calls plus240 reused per judge. Opus adds240 logical test checklist requests (232 unique task prompts,8 reused because task strings are identical) and180 quality audits. Retries, smoke, development and capabilities are extra and included in the actual ledger below. Do not present planned counts as finished collection when status is incomplete.

Actual final cache entries by model, purpose and origin:

| model | purpose | origin | calls |
|---|---|---|---|
| claude-opus-5-5 | capability:Opus | 37 new | 1 |
| claude-opus-5-5 | development:checklist_author | 37 new | 24 |
| claude-opus-5-5 | smoke:checklist_author | 37 new | 4 |
| claude-opus-5-5 | smoke:checklist_quality | 37 new | 3 |
| claude-opus-5-5 | test:checklist_author | 37 new | 232 |
| claude-opus-5-5 | test:checklist_quality | 37 new | 180 |
| claude-opus-5-5 | transport_check:2026-11-24:Opus | 37 new | 1 |
| gpt-6-luna | capability:Luna | 37 new | 1 |
| gpt-6-luna | development:free_form:original | 37 new | 24 |
| gpt-6-luna | development:item_checklist:original | 37 new | 24 |
| gpt-6-luna | smoke:exam_prompt:original | 37 new | 4 |
| gpt-6-luna | smoke:exam_prompt:polished | 37 new | 4 |
| gpt-6-luna | smoke:free_form:original | 37 new | 4 |
| gpt-6-luna | smoke:free_form:polished | 37 new | 4 |
| gpt-6-luna | smoke:general_rubric:original | 37 new | 4 |
| gpt-6-luna | smoke:item_checklist:original | 37 new | 4 |
| gpt-6-luna | smoke:item_checklist:polished | 37 new | 4 |
| gpt-6-luna | smoke:own_requirements:original | 37 new | 1 |
| gpt-6-luna | smoke:separate_scoring:original:A | 37 new | 4 |
| gpt-6-luna | smoke:separate_scoring:original:B | 37 new | 4 |
| gpt-6-luna | test:exam_prompt:polished | 37 new | 120 |
| gpt-6-luna | test:free_form:original | 37 new | 240 |
| gpt-6-luna | test:free_form:polished | 37 new | 120 |
| gpt-6-luna | test:general_rubric:original | 37 new | 240 |
| gpt-6-luna | test:item_checklist:original | 37 new | 240 |
| gpt-6-luna | test:item_checklist:polished | 37 new | 120 |
| gpt-6-luna | test:judge:test-code-000:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-001:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-002:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-003:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-004:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-005:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-006:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-007:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-008:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-009:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-010:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-011:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-012:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-013:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-014:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-015:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-016:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-017:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-018:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-019:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-020:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-021:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-022:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-023:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-024:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-025:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-026:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-027:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-028:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-029:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-030:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-031:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-032:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-033:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-034:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-035:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-036:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-037:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-038:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-039:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-040:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-041:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-042:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-043:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-044:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-045:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-046:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-047:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-048:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-049:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-050:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-051:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-052:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-053:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-054:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-055:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-056:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-057:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-058:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-code-059:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-000:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-001:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-002:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-003:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-004:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-005:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-006:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-007:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-008:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-009:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-010:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-011:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-012:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-013:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-014:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-015:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-016:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-017:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-018:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-019:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-020:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-021:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-022:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-023:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-024:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-025:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-026:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-027:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-028:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-029:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-030:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-031:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-032:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-033:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-034:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-035:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-036:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-037:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-038:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-039:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-040:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-041:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-042:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-043:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-044:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-045:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-046:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-047:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-048:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-049:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-050:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-051:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-052:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-053:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-054:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-055:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-056:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-057:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-058:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-grounded-059:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-000:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-001:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-002:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-003:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-004:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-005:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-006:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-007:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-008:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-009:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-010:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-011:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-012:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-013:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-014:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-015:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-016:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-017:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-018:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-019:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-020:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-021:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-022:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-023:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-024:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-025:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-026:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-027:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-028:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-029:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-030:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-031:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-032:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-033:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-034:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-035:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-036:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-037:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-038:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-039:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-040:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-041:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-042:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-043:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-044:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-045:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-046:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-047:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-048:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-049:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-050:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-051:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-052:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-053:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-054:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-055:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-056:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-057:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-058:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-instructions-059:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-000:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-001:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-002:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-003:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-004:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-005:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-006:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-007:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-008:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-009:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-010:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-011:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-012:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-013:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-014:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-015:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-016:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-017:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-018:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-019:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-020:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-021:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-022:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-023:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-024:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-025:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-026:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-027:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-028:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-029:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-030:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-031:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-032:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-033:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-034:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-035:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-036:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-037:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-038:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-039:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-040:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-041:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-042:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-043:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-044:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-045:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-046:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-047:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-048:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-049:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-050:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-051:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-052:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-053:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-054:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-055:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-056:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-057:AB | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-058:BA | 33 reused | 1 |
| gpt-6-luna | test:judge:test-worked-059:BA | 33 reused | 1 |
| gpt-6-luna | test:own_requirements:original | 37 new | 60 |
| gpt-6-luna | test:separate_scoring:original:A | 37 new | 240 |
| gpt-6-luna | test:separate_scoring:original:B | 37 new | 240 |
| gpt-6-luna | transport_check:2026-11-24:Luna | 37 new | 1 |
| gpt-6.1-sol | capability:Sol | 37 new | 1 |
| gpt-6.1-sol | development:free_form:original | 37 new | 24 |
| gpt-6.1-sol | development:item_checklist:original | 37 new | 24 |
| gpt-6.1-sol | smoke:exam_prompt:original | 37 new | 4 |
| gpt-6.1-sol | smoke:exam_prompt:polished | 37 new | 4 |
| gpt-6.1-sol | smoke:free_form:original | 37 new | 4 |
| gpt-6.1-sol | smoke:free_form:polished | 37 new | 4 |
| gpt-6.1-sol | smoke:general_rubric:original | 37 new | 4 |
| gpt-6.1-sol | smoke:item_checklist:original | 37 new | 4 |
| gpt-6.1-sol | smoke:item_checklist:polished | 37 new | 4 |
| gpt-6.1-sol | smoke:own_requirements:original | 37 new | 1 |
| gpt-6.1-sol | smoke:separate_scoring:original:A | 37 new | 4 |
| gpt-6.1-sol | smoke:separate_scoring:original:B | 37 new | 4 |
| gpt-6.1-sol | test:exam_prompt:polished | 37 new | 263 |
| gpt-6.1-sol | test:free_form:original | 37 new | 547 |
| gpt-6.1-sol | test:free_form:polished | 37 new | 260 |
| gpt-6.1-sol | test:general_rubric:original | 37 new | 542 |
| gpt-6.1-sol | test:item_checklist:original | 37 new | 558 |
| gpt-6.1-sol | test:item_checklist:polished | 37 new | 253 |
| gpt-6.1-sol | test:judge:test-code-000:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-001:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-002:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-003:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-004:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-005:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-006:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-007:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-008:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-009:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-010:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-011:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-012:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-013:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-014:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-015:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-016:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-017:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-018:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-019:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-020:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-021:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-022:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-023:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-024:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-025:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-026:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-027:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-028:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-029:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-030:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-031:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-032:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-033:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-034:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-035:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-036:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-037:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-038:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-039:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-040:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-041:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-042:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-043:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-044:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-045:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-046:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-047:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-048:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-049:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-050:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-051:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-052:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-053:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-054:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-055:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-056:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-057:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-058:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-code-059:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-000:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-001:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-002:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-003:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-004:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-005:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-006:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-007:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-008:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-009:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-010:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-011:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-012:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-013:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-014:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-015:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-016:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-017:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-018:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-019:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-020:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-021:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-022:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-023:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-024:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-025:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-026:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-027:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-028:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-029:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-030:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-031:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-032:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-033:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-034:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-035:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-036:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-037:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-038:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-039:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-040:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-041:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-042:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-043:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-044:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-045:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-046:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-047:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-048:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-049:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-050:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-051:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-052:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-053:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-054:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-055:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-056:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-057:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-058:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-grounded-059:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-000:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-001:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-002:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-003:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-004:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-005:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-006:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-007:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-008:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-009:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-010:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-011:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-012:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-013:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-014:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-015:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-016:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-017:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-018:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-019:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-020:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-021:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-022:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-023:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-024:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-025:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-026:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-027:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-028:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-029:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-030:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-031:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-032:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-033:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-034:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-035:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-036:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-037:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-038:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-039:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-040:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-041:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-042:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-043:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-044:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-045:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-046:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-047:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-048:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-049:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-050:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-051:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-052:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-053:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-054:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-055:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-056:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-057:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-058:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-instructions-059:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-000:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-001:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-002:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-003:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-004:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-005:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-006:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-007:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-008:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-009:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-010:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-011:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-012:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-013:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-014:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-015:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-016:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-017:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-018:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-019:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-020:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-021:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-022:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-023:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-024:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-025:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-026:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-027:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-028:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-029:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-030:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-031:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-032:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-033:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-034:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-035:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-036:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-037:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-038:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-039:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-040:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-041:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-042:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-043:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-044:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-045:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-046:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-047:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-048:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-049:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-050:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-051:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-052:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-053:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-054:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-055:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-056:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-057:AB | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-058:BA | 33 reused | 1 |
| gpt-6.1-sol | test:judge:test-worked-059:BA | 33 reused | 1 |
| gpt-6.1-sol | test:own_requirements:original | 37 new | 134 |
| gpt-6.1-sol | test:separate_scoring:original:A | 37 new | 554 |
| gpt-6.1-sol | test:separate_scoring:original:B | 37 new | 523 |
| gpt-6.1-sol | transport_check:2026-11-24:Sol | 37 new | 1 |
| ibm-granite/granite-4.2-8b-20260831 | capability:Granite 8B | 37 new | 1 |
| ibm-granite/granite-4.2-8b-20260831 | development:free_form:original | 37 new | 26 |
| ibm-granite/granite-4.2-8b-20260831 | development:item_checklist:original | 37 new | 25 |
| ibm-granite/granite-4.2-8b-20260831 | smoke:exam_prompt:original | 37 new | 6 |
| ibm-granite/granite-4.2-8b-20260831 | smoke:exam_prompt:polished | 37 new | 6 |
| ibm-granite/granite-4.2-8b-20260831 | smoke:free_form:original | 37 new | 6 |
| ibm-granite/granite-4.2-8b-20260831 | smoke:free_form:polished | 37 new | 6 |
| ibm-granite/granite-4.2-8b-20260831 | smoke:general_rubric:original | 37 new | 4 |
| ibm-granite/granite-4.2-8b-20260831 | smoke:item_checklist:original | 37 new | 5 |
| ibm-granite/granite-4.2-8b-20260831 | smoke:item_checklist:polished | 37 new | 4 |
| ibm-granite/granite-4.2-8b-20260831 | smoke:own_requirements:original | 37 new | 1 |
| ibm-granite/granite-4.2-8b-20260831 | smoke:separate_scoring:original:A | 37 new | 4 |
| ibm-granite/granite-4.2-8b-20260831 | smoke:separate_scoring:original:B | 37 new | 6 |
| ibm-granite/granite-4.2-8b-20260831 | test:exam_prompt:polished | 37 new | 129 |
| ibm-granite/granite-4.2-8b-20260831 | test:free_form:original | 37 new | 255 |
| ibm-granite/granite-4.2-8b-20260831 | test:free_form:polished | 37 new | 127 |
| ibm-granite/granite-4.2-8b-20260831 | test:general_rubric:original | 37 new | 271 |
| ibm-granite/granite-4.2-8b-20260831 | test:item_checklist:original | 37 new | 269 |
| ibm-granite/granite-4.2-8b-20260831 | test:item_checklist:polished | 37 new | 129 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-000:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-001:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-002:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-003:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-004:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-005:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-006:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-007:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-008:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-009:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-010:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-011:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-012:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-013:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-014:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-015:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-016:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-017:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-018:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-019:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-020:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-021:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-022:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-023:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-024:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-025:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-026:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-027:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-028:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-029:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-030:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-031:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-032:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-033:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-034:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-035:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-036:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-037:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-038:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-039:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-040:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-041:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-042:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-043:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-044:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-045:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-046:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-047:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-048:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-049:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-050:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-051:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-052:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-053:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-054:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-055:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-056:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-057:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-058:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-code-059:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-000:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-001:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-002:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-003:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-004:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-005:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-006:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-007:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-008:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-009:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-010:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-011:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-012:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-013:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-014:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-015:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-016:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-017:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-018:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-019:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-020:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-021:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-022:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-023:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-024:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-025:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-026:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-027:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-028:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-029:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-030:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-031:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-032:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-033:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-034:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-035:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-036:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-037:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-038:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-039:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-040:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-041:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-042:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-043:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-044:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-045:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-046:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-047:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-048:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-049:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-050:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-051:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-052:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-053:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-054:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-055:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-056:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-057:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-058:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-grounded-059:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-000:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-001:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-002:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-003:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-004:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-005:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-006:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-007:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-008:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-009:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-010:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-011:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-012:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-013:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-014:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-015:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-016:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-017:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-018:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-019:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-020:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-021:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-022:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-023:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-024:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-025:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-026:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-027:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-028:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-029:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-030:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-031:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-032:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-033:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-034:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-035:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-036:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-037:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-038:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-039:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-040:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-041:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-042:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-043:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-044:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-045:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-046:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-047:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-048:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-049:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-050:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-051:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-052:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-053:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-054:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-055:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-056:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-057:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-058:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-instructions-059:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-000:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-001:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-002:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-003:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-004:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-005:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-006:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-007:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-008:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-009:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-010:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-011:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-012:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-013:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-014:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-015:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-016:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-017:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-018:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-019:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-020:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-021:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-022:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-023:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-024:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-025:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-026:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-027:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-028:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-029:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-030:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-031:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-032:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-033:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-034:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-035:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-036:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-037:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-038:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-039:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-040:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-041:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-042:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-043:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-044:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-045:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-046:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-047:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-048:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-049:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-050:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-051:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-052:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-053:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-054:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-055:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-056:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-057:AB | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-058:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:judge:test-worked-059:BA | 33 reused | 1 |
| ibm-granite/granite-4.2-8b-20260831 | test:own_requirements:original | 37 new | 73 |
| ibm-granite/granite-4.2-8b-20260831 | test:separate_scoring:original:A | 37 new | 316 |
| ibm-granite/granite-4.2-8b-20260831 | test:separate_scoring:original:B | 37 new | 321 |
| ibm-granite/granite-4.2-8b-20260831 | transport_check:2026-11-24:Granite 8B | 37 new | 1 |


## Headline numbers and result provenance

`data/summary.csv`: n, correct, wrong, unreadable, undecided, accuracy, ci_low/high, readable_accuracy, ceiling/floor, split by variant/judge/method/parser. Values below are lenient original conditions.


| judge | method | n | correct | wrong | unreadable | undecided | accuracy | ci_low | ci_high | readable_accuracy |
|---|---|---|---|---|---|---|---|---|---|---|
| Granite 8B | exam_prompt | 240 | 143 | 97 | 0 | 0 | 0.5958333333333333 | 0.5327112876809579 | 0.6559358776635766 | 0.5958333333333333 |
| Granite 8B | free_form | 240 | 145 | 95 | 0 | 0 | 0.6041666666666666 | 0.5411234183615983 | 0.6639278483172435 | 0.6041666666666666 |
| Granite 8B | general_rubric | 240 | 148 | 89 | 3 | 0 | 0.6166666666666667 | 0.5537760294828047 | 0.6758813891974984 | 0.6244725738396625 |
| Granite 8B | item_checklist | 240 | 152 | 87 | 1 | 0 | 0.6333333333333333 | 0.5707115541361134 | 0.6917540672128042 | 0.6359832635983264 |
| Granite 8B | own_requirements | 60 | 31 | 29 | 0 | 0 | 0.5166666666666667 | 0.39307810032592494 | 0.6382495046026722 | 0.5166666666666667 |
| Granite 8B | separate_scoring | 240 | 43 | 10 | 36 | 151 | 0.17916666666666667 | 0.13582257478833457 | 0.23261952384083237 | 0.2107843137254902 |
| Luna | exam_prompt | 240 | 166 | 74 | 0 | 0 | 0.6916666666666667 | 0.6306052871856103 | 0.7466890435034588 | 0.6916666666666667 |
| Luna | free_form | 240 | 160 | 80 | 0 | 0 | 0.6666666666666666 | 0.6048146243471211 | 0.723267402339026 | 0.6666666666666666 |
| Luna | general_rubric | 240 | 173 | 66 | 1 | 0 | 0.7208333333333333 | 0.6609424090249535 | 0.7737662763341914 | 0.7238493723849372 |
| Luna | item_checklist | 240 | 171 | 69 | 0 | 0 | 0.7125 | 0.6522462362116623 | 0.7660583478131753 | 0.7125 |
| Luna | own_requirements | 60 | 32 | 28 | 0 | 0 | 0.5333333333333333 | 0.4089342702715789 | 0.6537209395856151 | 0.5333333333333333 |
| Luna | separate_scoring | 240 | 135 | 37 | 0 | 68 | 0.5625 | 0.49924250699978995 | 0.6237882530075151 | 0.5625 |
| Sol | exam_prompt | 240 | 231 | 9 | 0 | 0 | 0.9625 | 0.9302797673678065 | 0.9801478566862516 | 0.9625 |
| Sol | free_form | 240 | 92 | 7 | 141 | 0 | 0.38333333333333336 | 0.3241186108025017 | 0.4462239705171954 | 0.9292929292929293 |
| Sol | general_rubric | 240 | 92 | 8 | 140 | 0 | 0.38333333333333336 | 0.3241186108025017 | 0.4462239705171954 | 0.92 |
| Sol | item_checklist | 240 | 88 | 7 | 145 | 0 | 0.36666666666666664 | 0.30824593278719575 | 0.42928844586388654 | 0.9263157894736842 |
| Sol | own_requirements | 60 | 21 | 5 | 34 | 0 | 0.35 | 0.24167774406017556 | 0.47637381158245135 | 0.8076923076923077 |
| Sol | separate_scoring | 240 | 66 | 0 | 149 | 25 | 0.275 | 0.2223885797371556 | 0.3347006842365459 | 0.7252747252747253 |


- `family_summary.csv`: same outcome columns by family; own_requirements has only instructions.
- `paired_comparisons.csv`: judge, condition_a/b, subgroup, parser, n, accuracy_a/b, difference_b_minus_a, ci_low/high, gains/losses, exact_sign_p. Positive difference means the named condition_b improved on exam_prompt. Intervals are unadjusted.
- `polish_paired.csv`: same paired columns, condition_a original and condition_b polished. Positive difference means polishing the worse answer improved judge accuracy; negative means it hurt. Show counts and intervals; do not rank n12 traps.
- `trap_summary.csv`: trap flag, correct/wrong/unreadable/undecided and n. All true traps are code; no cross-family generalization.
- `unreadable_summary.csv`: parser, variant, judge, method, unreadable_type, count. `judgments.csv`: diagnostic_subtype and per-reader reasons, raw cache keys, scores/checks and recovery types. Strict versus lenient results use the identical raw replies. No post-test parser amendment is intended.
- `instruction_coverage.csv`: item_id plus seven boolean rule columns; sum per row is constraints named. `checklist_quality.json` includes full per-item evidence and audit keys; `quality_categories.csv` gives fixed-category counts for each family. Relate coverage to observed rescue/failure without treating it as causal.
- `resources.csv`: judge_calls, checklist_calls, calls_per_item, judge_seconds_per_item, including_checklist_seconds_per_item, costs and reused_judge_calls. Standalone method costs charge checklist construction once per item; run totals count the shared generation only once and separately include quality auditing.
- `date_provenance.json`: item_dates, model cutoffs/releases and sources; event dates in grounded documents are fictional and are not item creation dates.

## Unreadable replies by type


| parser | variant | judge | method | unreadable_type | count |
|---|---|---|---|---|---|
| strict | original | Granite 8B | exam_prompt | no_parseable_json | 2 |
| strict | original | Granite 8B | free_form | no_parseable_json | 1 |
| strict | original | Granite 8B | free_form | schema_failure | 2 |
| strict | original | Granite 8B | general_rubric | no_parseable_json | 6 |
| strict | original | Granite 8B | general_rubric | schema_failure | 3 |
| strict | original | Granite 8B | item_checklist | no_parseable_json | 5 |
| strict | original | Granite 8B | item_checklist | schema_failure | 1 |
| strict | original | Granite 8B | own_requirements | no_parseable_json | 3 |
| strict | original | Granite 8B | separate_scoring | no_parseable_json | 27 |
| strict | original | Granite 8B | separate_scoring | no_parseable_json;schema_failure | 1 |
| strict | original | Granite 8B | separate_scoring | schema_failure | 9 |
| strict | original | Luna | general_rubric | schema_failure | 1 |
| strict | original | Sol | free_form | transport_error | 141 |
| strict | original | Sol | general_rubric | transport_error | 140 |
| strict | original | Sol | item_checklist | transport_error | 145 |
| strict | original | Sol | own_requirements | transport_error | 34 |
| strict | original | Sol | separate_scoring | transport_error | 149 |
| strict | polished | Granite 8B | exam_prompt | no_parseable_json | 2 |
| strict | polished | Granite 8B | exam_prompt | schema_failure | 1 |
| strict | polished | Granite 8B | free_form | no_parseable_json | 1 |
| strict | polished | Granite 8B | free_form | schema_failure | 1 |
| strict | polished | Granite 8B | item_checklist | schema_failure | 1 |
| strict | polished | Sol | exam_prompt | transport_error | 62 |
| strict | polished | Sol | free_form | transport_error | 64 |
| strict | polished | Sol | item_checklist | transport_error | 60 |
| lenient | original | Granite 8B | general_rubric | schema_failure | 3 |
| lenient | original | Granite 8B | item_checklist | schema_failure | 1 |
| lenient | original | Granite 8B | separate_scoring | no_parseable_json | 28 |
| lenient | original | Granite 8B | separate_scoring | schema_failure | 8 |
| lenient | original | Luna | general_rubric | schema_failure | 1 |
| lenient | original | Sol | free_form | transport_error | 141 |
| lenient | original | Sol | general_rubric | transport_error | 140 |
| lenient | original | Sol | item_checklist | transport_error | 145 |
| lenient | original | Sol | own_requirements | transport_error | 34 |
| lenient | original | Sol | separate_scoring | transport_error | 149 |
| lenient | polished | Sol | exam_prompt | transport_error | 62 |
| lenient | polished | Sol | free_form | transport_error | 64 |
| lenient | polished | Sol | item_checklist | transport_error | 60 |
| complete_json | original | Granite 8B | exam_prompt | no_parseable_json | 2 |
| complete_json | original | Granite 8B | free_form | no_parseable_json | 1 |
| complete_json | original | Granite 8B | general_rubric | no_parseable_json | 6 |
| complete_json | original | Granite 8B | general_rubric | schema_failure | 3 |
| complete_json | original | Granite 8B | item_checklist | no_parseable_json | 4 |
| complete_json | original | Granite 8B | item_checklist | schema_failure | 1 |
| complete_json | original | Granite 8B | own_requirements | no_parseable_json | 3 |
| complete_json | original | Granite 8B | separate_scoring | no_parseable_json | 28 |
| complete_json | original | Granite 8B | separate_scoring | schema_failure | 8 |
| complete_json | original | Luna | general_rubric | schema_failure | 1 |
| complete_json | original | Sol | free_form | transport_error | 141 |
| complete_json | original | Sol | general_rubric | transport_error | 140 |
| complete_json | original | Sol | item_checklist | transport_error | 145 |
| complete_json | original | Sol | own_requirements | transport_error | 34 |
| complete_json | original | Sol | separate_scoring | transport_error | 149 |
| complete_json | polished | Granite 8B | exam_prompt | no_parseable_json | 2 |
| complete_json | polished | Granite 8B | free_form | no_parseable_json | 1 |
| complete_json | polished | Sol | exam_prompt | transport_error | 62 |
| complete_json | polished | Sol | free_form | transport_error | 64 |
| complete_json | polished | Sol | item_checklist | transport_error | 60 |


## Paired headlines


| judge | condition_b | n | accuracy_a | accuracy_b | difference_b_minus_a | ci_low | ci_high | gains | losses |
|---|---|---|---|---|---|---|---|---|---|
| Sol | free_form | 240 | 0.9625 | 0.38333333333333336 | -0.5791666666666667 | -0.6458333333333334 | -0.5125 | 5 | 144 |
| Sol | general_rubric | 240 | 0.9625 | 0.38333333333333336 | -0.5791666666666667 | -0.6416666666666667 | -0.5166666666666667 | 0 | 139 |
| Sol | item_checklist | 240 | 0.9625 | 0.36666666666666664 | -0.5958333333333333 | -0.6625 | -0.525 | 4 | 147 |
| Sol | separate_scoring | 240 | 0.9625 | 0.275 | -0.6875 | -0.7458333333333333 | -0.625 | 2 | 167 |
| Sol | own_requirements | 60 | 0.8833333333333333 | 0.35 | -0.5333333333333333 | -0.6666666666666666 | -0.4166666666666667 | 0 | 32 |
| Luna | free_form | 240 | 0.6916666666666667 | 0.6666666666666666 | -0.025 | -0.075 | 0.025 | 16 | 22 |
| Luna | general_rubric | 240 | 0.6916666666666667 | 0.7208333333333333 | 0.029166666666666667 | -0.020833333333333332 | 0.08333333333333333 | 24 | 17 |
| Luna | item_checklist | 240 | 0.6916666666666667 | 0.7125 | 0.020833333333333332 | -0.029166666666666667 | 0.07083333333333333 | 21 | 16 |
| Luna | separate_scoring | 240 | 0.6916666666666667 | 0.5625 | -0.12916666666666668 | -0.20416666666666666 | -0.05 | 32 | 63 |
| Luna | own_requirements | 60 | 0.5166666666666667 | 0.5333333333333333 | 0.016666666666666666 | -0.13333333333333333 | 0.18333333333333332 | 12 | 11 |
| Granite 8B | free_form | 240 | 0.5958333333333333 | 0.6041666666666666 | 0.008333333333333333 | -0.0375 | 0.05416666666666667 | 17 | 15 |
| Granite 8B | general_rubric | 240 | 0.5958333333333333 | 0.6166666666666667 | 0.020833333333333332 | -0.03333333333333333 | 0.075 | 26 | 21 |
| Granite 8B | item_checklist | 240 | 0.5958333333333333 | 0.6333333333333333 | 0.0375 | -0.004166666666666667 | 0.07916666666666666 | 18 | 9 |
| Granite 8B | separate_scoring | 240 | 0.5958333333333333 | 0.17916666666666667 | -0.4166666666666667 | -0.49166666666666664 | -0.3458333333333333 | 9 | 109 |
| Granite 8B | own_requirements | 60 | 0.55 | 0.5166666666666667 | -0.03333333333333333 | -0.15 | 0.08333333333333333 | 6 | 8 |


Controlled polish:


| judge | method | n | accuracy_a | accuracy_b | difference_b_minus_a | ci_low | ci_high | gains | losses |
|---|---|---|---|---|---|---|---|---|---|
| Sol | free_form | 120 | 0.35 | 0.4666666666666667 | 0.11666666666666667 | -0.016666666666666666 | 0.25 | 40 | 26 |
| Sol | exam_prompt | 120 | 0.9916666666666667 | 0.4666666666666667 | -0.525 | -0.6166666666666667 | -0.43333333333333335 | 0 | 63 |
| Sol | item_checklist | 120 | 0.35833333333333334 | 0.48333333333333334 | 0.125 | 0.008333333333333333 | 0.24166666666666667 | 36 | 21 |
| Luna | free_form | 120 | 0.7083333333333334 | 0.8166666666666667 | 0.10833333333333334 | 0.041666666666666664 | 0.18333333333333332 | 16 | 3 |
| Luna | exam_prompt | 120 | 0.7416666666666667 | 0.8 | 0.058333333333333334 | -0.008333333333333333 | 0.125 | 12 | 5 |
| Luna | item_checklist | 120 | 0.725 | 0.8333333333333334 | 0.10833333333333334 | 0.041666666666666664 | 0.175 | 16 | 3 |
| Granite 8B | free_form | 120 | 0.6083333333333333 | 0.6 | -0.008333333333333333 | -0.10833333333333334 | 0.08333333333333333 | 17 | 18 |
| Granite 8B | exam_prompt | 120 | 0.6166666666666667 | 0.525 | -0.09166666666666666 | -0.15 | -0.041666666666666664 | 1 | 12 |
| Granite 8B | item_checklist | 120 | 0.6416666666666667 | 0.6083333333333333 | -0.03333333333333333 | -0.125 | 0.058333333333333334 | 13 | 17 |


## Reader comparisons and checklist coverage


| parser | judge | method | n | correct | wrong | unreadable | undecided | accuracy | readable_accuracy |
|---|---|---|---|---|---|---|---|---|---|
| strict | Granite 8B | exam_prompt | 240 | 142 | 96 | 2 | 0 | 0.5916666666666667 | 0.5966386554621849 |
| lenient | Granite 8B | exam_prompt | 240 | 143 | 97 | 0 | 0 | 0.5958333333333333 | 0.5958333333333333 |
| complete_json | Granite 8B | exam_prompt | 240 | 142 | 96 | 2 | 0 | 0.5916666666666667 | 0.5966386554621849 |
| strict | Granite 8B | free_form | 240 | 143 | 94 | 3 | 0 | 0.5958333333333333 | 0.6033755274261603 |
| lenient | Granite 8B | free_form | 240 | 145 | 95 | 0 | 0 | 0.6041666666666666 | 0.6041666666666666 |
| complete_json | Granite 8B | free_form | 240 | 145 | 94 | 1 | 0 | 0.6041666666666666 | 0.606694560669456 |
| strict | Granite 8B | general_rubric | 240 | 143 | 88 | 9 | 0 | 0.5958333333333333 | 0.6190476190476191 |
| lenient | Granite 8B | general_rubric | 240 | 148 | 89 | 3 | 0 | 0.6166666666666667 | 0.6244725738396625 |
| complete_json | Granite 8B | general_rubric | 240 | 143 | 88 | 9 | 0 | 0.5958333333333333 | 0.6190476190476191 |
| strict | Granite 8B | item_checklist | 240 | 151 | 83 | 6 | 0 | 0.6291666666666667 | 0.6452991452991453 |
| lenient | Granite 8B | item_checklist | 240 | 152 | 87 | 1 | 0 | 0.6333333333333333 | 0.6359832635983264 |
| complete_json | Granite 8B | item_checklist | 240 | 151 | 84 | 5 | 0 | 0.6291666666666667 | 0.6425531914893617 |
| strict | Granite 8B | own_requirements | 60 | 30 | 27 | 3 | 0 | 0.5 | 0.5263157894736842 |
| lenient | Granite 8B | own_requirements | 60 | 31 | 29 | 0 | 0 | 0.5166666666666667 | 0.5166666666666667 |
| complete_json | Granite 8B | own_requirements | 60 | 30 | 27 | 3 | 0 | 0.5 | 0.5263157894736842 |
| strict | Granite 8B | separate_scoring | 240 | 42 | 10 | 37 | 151 | 0.175 | 0.20689655172413793 |
| lenient | Granite 8B | separate_scoring | 240 | 43 | 10 | 36 | 151 | 0.17916666666666667 | 0.2107843137254902 |
| complete_json | Granite 8B | separate_scoring | 240 | 43 | 10 | 36 | 151 | 0.17916666666666667 | 0.2107843137254902 |
| strict | Luna | exam_prompt | 240 | 166 | 74 | 0 | 0 | 0.6916666666666667 | 0.6916666666666667 |
| lenient | Luna | exam_prompt | 240 | 166 | 74 | 0 | 0 | 0.6916666666666667 | 0.6916666666666667 |
| complete_json | Luna | exam_prompt | 240 | 166 | 74 | 0 | 0 | 0.6916666666666667 | 0.6916666666666667 |
| strict | Luna | free_form | 240 | 160 | 80 | 0 | 0 | 0.6666666666666666 | 0.6666666666666666 |
| lenient | Luna | free_form | 240 | 160 | 80 | 0 | 0 | 0.6666666666666666 | 0.6666666666666666 |
| complete_json | Luna | free_form | 240 | 160 | 80 | 0 | 0 | 0.6666666666666666 | 0.6666666666666666 |
| strict | Luna | general_rubric | 240 | 173 | 66 | 1 | 0 | 0.7208333333333333 | 0.7238493723849372 |
| lenient | Luna | general_rubric | 240 | 173 | 66 | 1 | 0 | 0.7208333333333333 | 0.7238493723849372 |
| complete_json | Luna | general_rubric | 240 | 173 | 66 | 1 | 0 | 0.7208333333333333 | 0.7238493723849372 |
| strict | Luna | item_checklist | 240 | 171 | 69 | 0 | 0 | 0.7125 | 0.7125 |
| lenient | Luna | item_checklist | 240 | 171 | 69 | 0 | 0 | 0.7125 | 0.7125 |
| complete_json | Luna | item_checklist | 240 | 171 | 69 | 0 | 0 | 0.7125 | 0.7125 |
| strict | Luna | own_requirements | 60 | 32 | 28 | 0 | 0 | 0.5333333333333333 | 0.5333333333333333 |
| lenient | Luna | own_requirements | 60 | 32 | 28 | 0 | 0 | 0.5333333333333333 | 0.5333333333333333 |
| complete_json | Luna | own_requirements | 60 | 32 | 28 | 0 | 0 | 0.5333333333333333 | 0.5333333333333333 |
| strict | Luna | separate_scoring | 240 | 135 | 37 | 0 | 68 | 0.5625 | 0.5625 |
| lenient | Luna | separate_scoring | 240 | 135 | 37 | 0 | 68 | 0.5625 | 0.5625 |
| complete_json | Luna | separate_scoring | 240 | 135 | 37 | 0 | 68 | 0.5625 | 0.5625 |
| strict | Sol | exam_prompt | 240 | 231 | 9 | 0 | 0 | 0.9625 | 0.9625 |
| lenient | Sol | exam_prompt | 240 | 231 | 9 | 0 | 0 | 0.9625 | 0.9625 |
| complete_json | Sol | exam_prompt | 240 | 231 | 9 | 0 | 0 | 0.9625 | 0.9625 |
| strict | Sol | free_form | 240 | 92 | 7 | 141 | 0 | 0.38333333333333336 | 0.9292929292929293 |
| lenient | Sol | free_form | 240 | 92 | 7 | 141 | 0 | 0.38333333333333336 | 0.9292929292929293 |
| complete_json | Sol | free_form | 240 | 92 | 7 | 141 | 0 | 0.38333333333333336 | 0.9292929292929293 |
| strict | Sol | general_rubric | 240 | 92 | 8 | 140 | 0 | 0.38333333333333336 | 0.92 |
| lenient | Sol | general_rubric | 240 | 92 | 8 | 140 | 0 | 0.38333333333333336 | 0.92 |
| complete_json | Sol | general_rubric | 240 | 92 | 8 | 140 | 0 | 0.38333333333333336 | 0.92 |
| strict | Sol | item_checklist | 240 | 88 | 7 | 145 | 0 | 0.36666666666666664 | 0.9263157894736842 |
| lenient | Sol | item_checklist | 240 | 88 | 7 | 145 | 0 | 0.36666666666666664 | 0.9263157894736842 |
| complete_json | Sol | item_checklist | 240 | 88 | 7 | 145 | 0 | 0.36666666666666664 | 0.9263157894736842 |
| strict | Sol | own_requirements | 60 | 21 | 5 | 34 | 0 | 0.35 | 0.8076923076923077 |
| lenient | Sol | own_requirements | 60 | 21 | 5 | 34 | 0 | 0.35 | 0.8076923076923077 |
| complete_json | Sol | own_requirements | 60 | 21 | 5 | 34 | 0 | 0.35 | 0.8076923076923077 |
| strict | Sol | separate_scoring | 240 | 66 | 0 | 149 | 25 | 0.275 | 0.7252747252747253 |
| lenient | Sol | separate_scoring | 240 | 66 | 0 | 149 | 25 | 0.275 | 0.7252747252747253 |
| complete_json | Sol | separate_scoring | 240 | 66 | 0 | 149 | 25 | 0.275 | 0.7252747252747253 |


Checklist quality categories (`quality_categories.csv`, n):


| family | method | category | n |
|---|---|---|---|
| code | Opus fixed-category audit | partial | 1 |
| code | Opus fixed-category audit | present | 59 |
| grounded | Opus fixed-category audit | partial | 1 |
| grounded | Opus fixed-category audit | present | 59 |
| instructions | code keyword-and-value coverage |  | 60 |
| worked | Opus fixed-category audit | absent | 2 |
| worked | Opus fixed-category audit | partial | 15 |
| worked | Opus fixed-category audit | present | 43 |


Instruction-rule naming (`instruction_coverage.csv`, boolean rule columns; code-based approximate coverage):


| rule | named | items |
|---|---|---|
| word_count | 60 | 60 |
| required | 60 | 60 |
| forbidden | 60 | 60 |
| no_digits | 60 | 60 |
| paragraphs | 60 | 60 |
| opening | 60 | 60 |
| closing | 60 | 60 |


## Per-item resources

Standalone logical costs charge checklist generation once per item. Deduplicated columns amortize shared identical-task requests. Seconds sum timed transport calls, including retry attempts, but exclude semaphore queue waits and retry backoff; this is serial model-service time, not end-to-end batch latency. The overall collection timestamp span is reported separately. Baseline cost/time is historical; incremental original-baseline calls are zero. Source: resources.csv.


| variant | judge | method | n | calls_per_item | deduplicated_calls_per_item | judge_seconds_per_item | including_checklist_seconds_per_item | list_usd_per_item | deduplicated_list_usd_per_item | openrouter_usd | cli_estimated_list_usd | checklist_list_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| original | Granite 8B | exam_prompt | 240 | 1.0 | 1.0 | 4.457808938332891 | 4.457808938332891 | 0.00013066249999999998 | 0.00013066249999999998 | 0.031359 | 0.0 | 0.0 |
| original | Granite 8B | free_form | 240 | 1.0625 | 1.0625 | 4.509734927916967 | 4.509734927916967 | 0.00016686775 | 0.00016686775 | 0.04004826 | 0.0 | 0.0 |
| original | Granite 8B | general_rubric | 240 | 1.1291666666666667 | 1.1291666666666667 | 9.792391215833474 | 9.792391215833474 | 0.000234649 | 0.000234649 | 0.05631576 | 0.0 | 0.0 |
| original | Granite 8B | item_checklist | 240 | 2.120833333333333 | 2.0875 | 7.448925160000848 | 19.49000691708352 | 0.03130838620833333 | 0.030786926208333332 | 0.053352689999999994 | 0.0 | 7.46066 |
| original | Granite 8B | own_requirements | 60 | 1.2166666666666666 | 1.2166666666666666 | 13.569018023329651 | 13.569018023329651 | 0.00027336900000000003 | 0.00027336900000000003 | 0.016402140000000003 | 0.0 | 0.0 |
| original | Granite 8B | separate_scoring | 240 | 3.654166666666667 | 3.620833333333333 | 39.58711191124736 | 51.628193668330034 | 0.03171063833333333 | 0.031189178333333335 | 0.1498932 | 0.0 | 7.46066 |
| original | Luna | exam_prompt | 240 | 1.0 | 1.0 | 5.602984248333511 | 5.602984248333511 | 0.0004879949166666667 | 0.0004879949166666667 | 0.0 | 0.11711878 | 0.0 |
| original | Luna | free_form | 240 | 1.0 | 1.0 | 5.001546290415839 | 5.001546290415839 | 0.0004172173333333334 | 0.0004172173333333334 | 0.0 | 0.10013216000000001 | 0.0 |
| original | Luna | general_rubric | 240 | 1.0 | 1.0 | 5.234318442497957 | 5.234318442497957 | 0.0004596606666666667 | 0.0004596606666666667 | 0.0 | 0.11031856000000001 | 0.0 |
| original | Luna | item_checklist | 240 | 2.0 | 1.9666666666666666 | 4.902409681664964 | 16.943491438747635 | 0.03153276666666667 | 0.03101130666666667 | 0.0 | 0.10720400000000001 | 7.46066 |
| original | Luna | own_requirements | 60 | 1.0 | 1.0 | 5.0194176299994675 | 5.0194176299994675 | 0.0004775376666666667 | 0.0004775376666666667 | 0.0 | 0.028652260000000002 | 0.0 |
| original | Luna | separate_scoring | 240 | 3.0 | 2.966666666666667 | 10.942423323332878 | 22.98350508041555 | 0.0319873635 | 0.031465903499999996 | 0.0 | 0.21630724 | 7.46066 |
| original | Sol | exam_prompt | 240 | 1.0 | 1.0 | 15.492854106249858 | 15.492854106249858 | 0.016056684999999998 | 0.016056684999999998 | 0.0 | 3.8536043999999996 | 0.0 |
| original | Sol | free_form | 240 | 2.279166666666667 | 2.279166666666667 | 9.457456165833538 | 9.457456165833538 | 0.005929903333333334 | 0.005929903333333334 | 0.0 | 1.4231768000000002 | 0.0 |
| original | Sol | general_rubric | 240 | 2.2583333333333333 | 2.2583333333333333 | 11.526922581248618 | 11.526922581248618 | 0.0069920450000000006 | 0.0069920450000000006 | 0.0 | 1.6780908 | 0.0 |
| original | Sol | item_checklist | 240 | 3.325 | 3.2916666666666665 | 11.343840262500695 | 23.384922019583367 | 0.03790433333333333 | 0.03738287333333334 | 0.0 | 1.63638 | 7.46066 |
| original | Sol | own_requirements | 60 | 2.2333333333333334 | 2.2333333333333334 | 19.200131850001828 | 19.200131850001828 | 0.011404906666666666 | 0.011404906666666666 | 0.0 | 0.6842944 | 0.0 |
| original | Sol | separate_scoring | 240 | 5.4875 | 5.454166666666667 | 28.922729254582737 | 40.963811011665406 | 0.047719566666666664 | 0.04719810666666667 | 0.0 | 3.9920360000000006 | 7.46066 |
| polished | Granite 8B | exam_prompt | 120 | 1.075 | 1.075 | 7.2381639200006855 | 7.2381639200006855 | 0.00019909249999999998 | 0.00019909249999999998 | 0.0238911 | 0.0 | 0.0 |
| polished | Granite 8B | free_form | 120 | 1.0583333333333333 | 1.0583333333333333 | 5.944245775000672 | 5.944245775000672 | 0.00018063275 | 0.00018063275 | 0.02167593 | 0.0 | 0.0 |
| polished | Granite 8B | item_checklist | 120 | 2.075 | 2.066666666666667 | 5.4887511333317285 | 15.963474387497506 | 0.03127362091666667 | 0.031139880916666664 | 0.02449851 | 0.0 | 3.728336 |
| polished | Luna | exam_prompt | 120 | 1.0 | 1.0 | 4.752620031667296 | 4.752620031667296 | 0.00043403 | 0.00043403 | 0.0 | 0.0520836 | 0.0 |
| polished | Luna | free_form | 120 | 1.0 | 1.0 | 4.901845055834323 | 4.901845055834323 | 0.0004357255 | 0.0004357255 | 0.0 | 0.052287059999999996 | 0.0 |
| polished | Luna | item_checklist | 120 | 2.0 | 1.9916666666666667 | 5.00978227667171 | 15.484505530837486 | 0.03152974916666667 | 0.03139600916666667 | 0.0 | 0.0552339 | 3.728336 |
| polished | Sol | exam_prompt | 120 | 2.191666666666667 | 2.191666666666667 | 10.466694952499287 | 10.466694952499287 | 0.00760787 | 0.00760787 | 0.0 | 0.9129444 | 0.0 |
| polished | Sol | free_form | 120 | 2.1666666666666665 | 2.1666666666666665 | 9.890160792501895 | 9.890160792501895 | 0.007007616666666667 | 0.007007616666666667 | 0.0 | 0.840914 | 0.0 |
| polished | Sol | item_checklist | 120 | 3.1083333333333334 | 3.1 | 10.460739943334799 | 20.935463197500574 | 0.037952349999999996 | 0.037818609999999996 | 0.0 | 0.8259459999999998 | 3.728336 |


## Candidate worked examples

Selection is deterministic: the first stable sorted item/judge row in each family satisfying each outcome pattern, at most one per family and pattern. The case figure prioritizes distinct IDs and different outcome patterns. All details, exact input, expected winner, checklist, raw replies and every condition are in `data/worked_examples.json`; no absent category is invented.


| purpose | item_id | judge | method | matching_item_judge_cases | matching_items | matching_judgments |
|---|---|---|---|---|---|---|
| end_to_end | test-code-000 | Granite 8B | None | None | None | None |
| checklist_caught_error | test-code-000 | Granite 8B | None | 55 | None | None |
| checklist_caught_error | test-worked-019 | Granite 8B | None | 55 | None | None |
| checklist_caught_error | test-instructions-000 | Sol | None | 55 | None | None |
| checklist_caught_error | test-grounded-000 | Luna | None | 55 | None | None |
| structure_made_worse | test-code-005 | Granite 8B | None | 37 | None | None |
| structure_made_worse | test-worked-004 | Granite 8B | None | 37 | None | None |
| structure_made_worse | test-instructions-005 | Luna | None | 37 | None | None |
| structure_made_worse | test-grounded-005 | Granite 8B | None | 37 | None | None |
| rubric_made_worse | test-code-025 | Luna | None | 31 | None | None |
| rubric_made_worse | test-worked-004 | Granite 8B | None | 31 | None | None |
| rubric_made_worse | test-instructions-002 | Luna | None | 31 | None | None |
| rubric_made_worse | test-grounded-001 | Luna | None | 31 | None | None |
| typical_success | test-code-000 | Luna | None | 285 | None | None |
| typical_success | test-worked-000 | Granite 8B | None | 285 | None | None |
| typical_success | test-instructions-000 | Granite 8B | None | 285 | None | None |
| typical_success | test-grounded-000 | Granite 8B | None | 285 | None | None |
| typical_failure | test-code-008 | Granite 8B | None | 124 | None | None |
| typical_failure | test-worked-000 | Luna | None | 124 | None | None |
| typical_failure | test-instructions-000 | Luna | None | 124 | None | None |
| typical_failure | test-grounded-002 | Granite 8B | None | 124 | None | None |
| checklist_missed_decisive_check | test-worked-009 | None | None | None | 2 | None |
| checklist_missed_decisive_check | test-worked-014 | None | None | None | 2 | None |
| unreadable | test-code-000 | Granite 8B | separate_scoring | None | None | 836 |
| unreadable | test-code-000 | Sol | general_rubric | None | None | 836 |
| unreadable | test-code-000 | Sol | item_checklist | None | None | 836 |
| unreadable | test-code-001 | Sol | free_form | None | None | 836 |
| unreadable | test-code-002 | Sol | free_form | None | None | 836 |
| unreadable | test-code-002 | Sol | general_rubric | None | None | 836 |
| strict_failure_lenient_recovery | test-code-031 | Granite 8B | exam_prompt | None | None | 26 |
| strict_failure_lenient_recovery | test-code-033 | Granite 8B | separate_scoring | None | None | 26 |
| strict_failure_lenient_recovery | test-code-037 | Granite 8B | exam_prompt | None | None | 26 |
| strict_failure_lenient_recovery | test-grounded-016 | Granite 8B | general_rubric | None | None | 26 |


Raw unreadable/recovered sample test-code-000 Granite 8B separate_scoring:

- Cache `14185f0b5767d7f51f43e45b796a0a05a10289b07f540474ef7a0a858fc4e0ab`: '{"answers":[true,true,true,true,true,true,true],"reason":"All checklist items are satisfied: audit scan processes rows in original zero-based order with correct weight calculation; row keeping uses (state+weight+index)%7!=4 or last row condition before state update; state updates after every row including omitted rows with reset to 4 for weight=0 and (5*state+weight)%7 otherwise; rotation is left by final_state%len(kept) with empty kept handled safely; integer times are sorted and deduplicated, sessions start only on gap >8 (gap=8 stays same session); sessions returned as [first,last,count] wi'; error None

- Cache `3c398911adc29dbf0d78a967c12d5f9295a7a40e1acce2ba654e99571f32b3f6`: '{"answers":[true,true,true,true,false,true],"reason":"Checklist 5 fails: the main rule requires starting a new session only when the gap is GREATER than 8 (i.e., gap > 8), meaning a gap of exactly 8 should NOT start a new session. However, the code uses `if deduplicated_times[i] - end >= 8:` which starts a new session when the gap is >= 8, including exactly 8. This violates the strict \'greater than 8\' condition."}'; error None


Raw unreadable/recovered sample test-code-000 Sol general_rubric:

- Cache `d1cc26fcea30ea6f3df10e56a3759aea4d97e2bcd04b0745084475024370b2c0`: ''; error None


Raw unreadable/recovered sample test-code-000 Sol item_checklist:

- Cache `2d125cf71cd4cfeb1dd720e6b82ad100fdcb9453797accc7de79921bce853ee6`: ''; error None


Raw unreadable/recovered sample test-code-001 Sol free_form:

- Cache `19a85027f79c3db8747196a4cc2cce0bb743f6e42f704c29ac5d6b516b88352b`: ''; error None


Raw unreadable/recovered sample test-code-002 Sol free_form:

- Cache `ea14dae2ad417fd5e4721b109c96db647a1de0b723f66c7756bb30950fe6e93d`: ''; error None


Raw unreadable/recovered sample test-code-002 Sol general_rubric:

- Cache `6ff97954bbe2e59c0984acca0df95b6273cc7e48e8cfd49881a08dce4eed9ff3`: ''; error None


Raw unreadable/recovered sample test-code-031 Granite 8B exam_prompt:

- Cache `fdf6fd6390f9e882d9c0ad40bfe71ce657cd4b9f5ea0bdc8155a063ff1a617aa`: '{"winner": "B", "confidence": 95, "reason": "Answer B correctly implements the audit scan and rotation logic, while Answer A incorrectly clamps balance to [0,18] instead of [-18,18] and has duplicate solve definitions. Answer B\'s core solve uses max(0, min(18, x)) which is wrong, but the main rule requires clamping to [-18,18]; however, Answer B\'s outer solve uses the correct clamping in the inner _core_solve? Wait — no: in Answer B, the inner _core_solve uses max(0, min(18, x)), which is incorrect. But Answer A also uses max(-18, min(18, x)) in its _core_solve, which is correct. However, Answ'; error None


Raw unreadable/recovered sample test-code-033 Granite 8B separate_scoring:

- Cache `412ac107f5a0396c1dbf045faa25d7b3a203571858022f709d21709859970815`: '{"answers":[true,true,true,true,true,false,true],"reason":"Checklist 6 fails because the function returns None for expiry when no lot is eligible, but the spec says \'using null expiry\' — in Python, null is None, which is correct; however, it says \'and 0 for the quantity\' when none. The function returns [0, None] when no kept rows, but only when no kept rows — not necessarily when no eligible lots. However, the main issue: when there are kept rows but no eligible lots (expiry > 19), the function returns [0, None], which matches \'0 for quantity\' and \'null expiry\'. But the spec says \'using null e'; error None

- Cache `3486086472d699bc6c8fb6c0b22ce53de99906336f2dd99a0e61b4fa7df35c2a`: '{"answers":[false,false,false,false,false,false,false],"reason":"Multiple critical errors: weight calculation for list rows incorrectly sums all integers and string lengths without excluding booleans (checklist 1); log-string rows detection only checks start/end pipes but does not ensure signed integer between pipes (e.g., \'-5\' should work); keep condition uses `i == len(rows) - 1` but should keep last row regardless of test — however state update uses current state before decision for all rows including omitted rows? Actually state update happens after keep decision but uses current state; ho'; error None


Raw unreadable/recovered sample test-code-037 Granite 8B exam_prompt:

- Cache `c57359075154f48595f62b10e0e90a17eae05fe15e449d4fc6bc6de8eb7b45d4`: '{"winner": "B", "confidence": 95, "reason": "Answer B correctly implements the audit scan rule with \'or if it is the last original row\' (i == len(rows) - 1), while Answer A incorrectly uses \'or if it is the last original row\' as \'or i == len(rows) - 1\' in the condition but actually uses \'or i == len(rows) - 1\' in the condition check? Wait: Answer A says \'or if it is the last original row\' in the description but in code: Answer A uses \'or i == len(rows) - 1\'? Let\'s re-read carefully. Answer A: \'if (state + weight + original_index) modulo 13 is not 1, or if it is the last original row.\' Answer A'; error None


Raw unreadable/recovered sample test-grounded-016 Granite 8B general_rubric:

- Cache `aa81af6dac854490285de13d3ef958664b6cd2ae1211d9452524389d67189089`: '{\n  "winner": "B",\n  "confidence": 99,\n  "reason": "A=[1,2,1,2,1]; B=[2,2,2,2,2]; A incorrectly selects A-154 (effective 2026-09-24, signed 2026-09-27) over A-153 (effective 2026-09-13) for unit rate at Marlow East despite tie-breaking by larger revision (both revision 153 and 154 have same effective date 2026-09-24? Wait: A-153 effective 2026-09-13, A-154 effective 2026-09-24, A-155 effective 2026-09-24? Let\'s compute correctly: Need to evaluate per site Marlow East, service filter replacement, fields: unit rate, eligible units, service credit. Use signed amendment with latest effective date '; error None


Checklist-coverage cases (`checklist_quality.json`; join item_id to checklists_v1.json and judgments.csv):


| item_id | family | category | reason | raw_reply_cache_key |
|---|---|---|---|---|
| test-worked-009 | worked | absent | The decisive failure is a digit slip in the numerator at adjustment 17, carried consistently through 18, 19 and the final answer. No question asks the judge to check that each intermediate value or the final value is arithmetically correct. Q1-Q2 cover only base-levy setup. Q3-Q5 cover exactness, order and the meaning of each operation, which the slipped answer satisfies. Q6-Q7 cover format. Q8 checks only that the final answer matches adjustment 19, and the propagated slip passes that check. | 9379caa54d7fe2b93b0f52a74ebc8cc2584ca1acb521263789a8f1852dc12ec9 |
| test-worked-014 | worked | absent | The decisive failure is a carried digit slip in the adjustment 17 numerator (…903… became …912…), which propagates to adjustments 18, 19 and the final answer. No checklist question asks whether any intermediate value or the final answer is arithmetically correct. Q3 and Q4 check step order and how percentages are interpreted, not the computed values. Q5 checks exactness, not correctness. Q6 checks line format. Q7 checks only that the final answer matches adjustment 19 and is reduced, which the faulty answer satisfies. | 28695a463214068ae121ab21e64971cc3206fed467047e350c3b8119e6fa0417 |
| test-code-054 | code | partial | The mutation uses abs(v) > 7 instead of >= 7, so amounts of exactly ±7 are wrongly skipped. Q5 restates the rule 'skip amounts with absolute value below 7', which implicitly sets the threshold. It is one clause in a bundled question, though, and never asks explicitly whether amounts of exactly 7 are kept (strict versus inclusive comparison). | 7cfd1a5e92afb84aa0cdb5a9c31ae8283f42b81988c432a69908a4c84166ec4c |
| test-grounded-009 | grounded | partial | The decisive failure is choosing A-138 (16 units, effective 2026-09-13) instead of A-139 (18 units, effective 2026-09-24). Question 5 could catch it only through a generic latest-effective-date check across all three fields; it never names A-139 or the units choice. Question 2 covers only excluding the future-effective A-162, and questions 6–7 would accept 16 * 573 - 14 = 9154 as well-formed and arithmetically correct. | d3a0e0e53b0c174f747926bf8df17f5e5b0a2f0ff8e6dce6f2b8092bc4422a3a |
| test-worked-001 | worked | partial | The decisive failure is an arithmetic slip in one numerator digit at adjustment 17, which carries through adjustments 18–19 and the final answer. No question asks for the exact value at each stage to be checked. Q3 only checks that the operations are applied in the right order and sequence. Q7 broadly asks whether the final value equals the exact correct result, which would catch the slip but does not explicitly require stage-by-stage verification of the intermediate values. | b26ffbd7111f02aa960a8a3a91ab0f7fecd60dbe0fbd30a1635b36c4a9f04aa3 |


## Exact prompts

All template texts are in `data/prompt_templates.json`. Full exact prompts, settings, model IDs, provider payloads and returned replies are in `data/cache_requests.jsonl` (or its lossless `.jsonl.gz` archive), keyed by canonical full-request SHA-256. `checklists_v1.json` holds each task-only question list and author cache key; `baseline_index.json` maps reused originals. `pipeline_v1.py:prompt_for` supplies displayed order. Checklist quality includes only task/checklist and checker decisive evidence, never a prior judge verdict. No outside model HTTP/SDK access is used.

## Models table


| name | pinned_version | provider | access | size | precision | settings | date | date_basis | date_source | why_included |
|---|---|---|---|---|---|---|---|---|---|---|
| Opus | claude-opus-5-5 | Anthropic | claude -p | Not published | Not published | reasoning effort medium; no tools; isolated empty cwd | 2026-09-22 | release | https://www.anthropic.com/claude-opus-5-5 | Top judge writes task-only checklists and audits non-instruction checklist coverage. |
| Sol | gpt-6.1-sol | OpenAI | codex exec | Not published | Not published | reasoning effort medium; no tools; isolated empty cwd; project_doc_max_bytes=0 prevents ancestor instructions after D: temp relocation (same intended empty-cwd context) | 2026-04-30 | training cutoff | https://developers.openai.com/api/docs/models/gpt-6.1-sol | Strong OpenAI judge and development difficulty check |
| Luna | gpt-6-luna | OpenAI | codex exec | Not published | Not published | reasoning effort medium; no tools; isolated empty cwd; project_doc_max_bytes=0 prevents ancestor instructions after D: temp relocation (same intended empty-cwd context) | 2026-05-18 | training cutoff | https://developers.openai.com/api/docs/models/gpt-6-luna | Replaces Haiku after provider safety blocks; 0.715 baseline leaves room to improve. |
| Granite 8B | ibm-granite/granite-4.2-8b-20260831 | coreweave/bf16 | OpenRouter chat | 8.8B dense | BF16 | reasoning none; temperature 0; max_tokens 1600 judgments / 2600 solves; native JSON object mode | 2026-08-31 | catalog release fallback | https://openrouter.ai/ibm-granite/granite-4.2-8b | Recent small open-weight dense judge; low cost; AA small size class |


Model metadata was inherited from notebook33's checked2026-10-30 sources. `granite_catalog.json` and `catalog_snapshot.json` are the fresh capability-run OpenRouter snapshots. CLI pins are the supplied IDs; immutability is not independently guaranteed. Granite is Apache-2.0, BF16, HF `ibm-granite/granite-4.2-8b`,8.8B dense. Synthetic candidates were written by Google Gemma models in notebook33, a different vendor from all judges and the Opus checklist author.

## Chronological run log for PROTOCOL.md

-2026-10-30: read AGENTS.md, notebook33 notebook/handoff, transport/readers/generator and notebook11/31/18/17 helper patterns. Source commit supplied as cf854303, no git verification performed because user prohibited git operations. On resume, all13 copied artifacts were reverified against the moved D:/projects/experiment_notebooks/worktrees/33-judge-exam checkout; source_manifest.json and from_33/SOURCE.md now name the D: source paths. Old paths inside immutable historical stdout are retained as evidence and are never used operationally. All large temporary storage is under this notebook data/tmp on D:.
- Copied immutable source artifacts and verified every hash in notebook33's freeze record after CRLF-to-LF normalization. Imported720 exact selected baseline replies, keeping original request keys and an origin marker.
- Ran one tiny capability call per Sol, Luna, Granite and Opus. All four returned strictly readable correct JSON. Fresh catalog GET verified Granite's canonical pin; no fallback provider was permitted.
- Fixed seed/order selection, all method templates, strict/lenient and rubric/array schema rules, separate-score tie handling, deterministic polish rules and coverage categories before test. Polished all120 controls; every full checker signature unchanged, including instruction word count. No generator parameters or original candidates changed.
- Smoke uses four frozen development pairs and all methods; development uses24 frozen pairs for free form versus checklist. Exact request starts/returns are in attempt_lifecycle.jsonl; retries and quota events in run_log.jsonl; raw attempts in cache and nonfinal ledger. Smoke/development responses never replace test responses.
- Test checklist generation uses task text only. The final freeze_record.json hashes include original source manifest, prompts, checklists, order, polish, models, analysis plan and code. Test judgments may start only after that record exists. Source freeze time is retained in from_33/freeze_record.json.
- Implementation was simplified before freeze to embed only the four needed source checkers and exact verdict readers. Analysis and export code were completed before the test freeze. Notebook narrative remains for Claude.


Freeze record:
```json
{
  "version": "structured-judging-v1.0",
  "source_commit": "cf854303",
  "seed": 3710302026,
  "hash_normalization": "CRLF to LF",
  "hashes": {
    "order_assignment.json": "c64ef7565316efecbe556e565fe1994bd9959791f8da4496072c9713d5bdf537",
    "polished_selection.json": "c6b4ece74e5fc05995271d0d9142059382028dc38f432e255a9813e05ae3dfc9",
    "polished_v1.json": "5b5f2b262c7d21bf320ee5e7af2f4ae4e0bee1c40273a4737ec95311f195a23e",
    "polish_validation.json": "c8714246eeb92bc1ac6562c71afa6e9a9cf060e64ba8042398f13a96d8a904b4",
    "checklists_v1.json": "d8cd456a2874552b55c1a984fd663bd2851d39bcbfb2eb95c54377c5777c715a",
    "prompt_templates.json": "148374c6c9cf2b4250b766c0b731cfed16ff273a1dbaef69defcccba549775b6",
    "analysis_plan.json": "0400399e3b0ee8d5ac7963fa66cbdd89bf3633763fea810d180b64279c73ffbd",
    "models.json": "8df9ec8c62b92d8f75e51529f39c024ca16234a06e5cd8382665b954be306013",
    "date_provenance.json": "46717e77eb6bd258a1854de11d0d6da66135903f7ee19490112ee9a5a65ea139",
    "source_manifest.json": "2732be4581fb0610498c4eb636e6e7a47e9e9b3306cca894c48c4a01fc0475b1",
    "implementation_v1.py": "df3fe46ef5d34283bd4697723181f63af67f92574d652b4a69045d2e0a400e6b",
    "pipeline_v1.py": "63d91d453931953af17299a91ab85a487d78acc9693b795578128178e2a564ee",
    "design_amendments.json": "23c5ee1b602af89bf5f4f2d2284b9770beb85d953c3fe4b3573ed9a4bd9b0762",
    "environment.json": "af22c78f64e29d89fea97735a9ce63bb321e01cbc762ba188fca66024d49d8b0",
    "preflight_validation.json": "806a8cd251134d10d013d02f81b3062c105e2ca4a214f92e0ef2a96825bbb86c",
    "transport_amendment_validation.json": "0b3612487df26c154873f960fdd0c5760daccd6fbd0bf62ef87cfe39fc27c148"
  },
  "items": 240,
  "polished": 120,
  "checklist_candidates_visible": false,
  "frozen_at": "2026-10-30T18:13:27.384219+00:00"
}
```


Pretest design amendment details are in data/design_amendments.json (joint source/display order balance, with zero model calls and unchanged checker signatures).

Run events (complete machine log remains in data/run_log.jsonl):


| at | event | family | n | purpose | model | key | message |
|---|---|---|---|---|---|---|---|
| 2026-10-30T17:14:43.250304+00:00 | polish_family_validation | code | 30 |  |  |  |  |
| 2026-10-30T17:14:43.253211+00:00 | polish_family_validation | worked | 30 |  |  |  |  |
| 2026-10-30T17:14:43.355030+00:00 | polish_family_validation | instructions | 30 |  |  |  |  |
| 2026-10-30T17:14:43.356773+00:00 | polish_family_validation | grounded | 30 |  |  |  |  |
| 2026-10-30T17:19:12.483099+00:00 | retry |  |  | smoke:exam_prompt:original |  | 32e4d11afd7aaa8e32c6d1b88c6eefe8b89ed9a1fceebc16dabb871b188c9c9f |  |
| 2026-10-30T17:19:27.194197+00:00 | retry |  |  | smoke:exam_prompt:original |  | 2395ce3b302aa2cd6aa3dc29f1d4025751d669f92f46e1911e242df640ac293b |  |
| 2026-10-30T17:19:27.943462+00:00 | retry |  |  | smoke:free_form:original |  | 17448fe8340c6ec652276f4a6060c5b210609dbae8409ada18956ebec8f6c5d0 |  |
| 2026-10-30T17:20:22.660498+00:00 | retry |  |  | smoke:item_checklist:original |  | daacfa674bb3d5f56417ebfab9d1a1ab216b8a278b4126debb12af61ea57daf5 |  |
| 2026-10-30T17:20:31.405602+00:00 | retry |  |  | smoke:separate_scoring:original:B |  | a8172d1936f822c06ea2953b35ab01010aefb31e6e02d252a746f56f08722d1a |  |
| 2026-10-30T17:21:25.371371+00:00 | retry |  |  | smoke:free_form:original |  | bf7ac38220c3ea5f0679021c136d63eea67e13ac7e1afba2d7e9cfe3a67579d8 |  |
| 2026-10-30T17:23:05.698798+00:00 | retry |  |  | smoke:separate_scoring:original:B |  | 61a56f57eaef9618e74f6e44449f815bd29ef3943d91e3e42a40ef558cf25df0 |  |
| 2026-10-30T17:30:25.397299+00:00 | polish_family_validation | code | 30 |  |  |  |  |
| 2026-10-30T17:30:25.400156+00:00 | polish_family_validation | worked | 30 |  |  |  |  |
| 2026-10-30T17:30:25.420068+00:00 | polish_family_validation | instructions | 30 |  |  |  |  |
| 2026-10-30T17:30:25.421602+00:00 | polish_family_validation | grounded | 30 |  |  |  |  |
| 2026-10-30T17:33:22.198946+00:00 | quota_limit_stop |  |  | test:checklist_author | claude-opus-5-5 | 7c4a76b2bcae36ccfa64ec000e9dcb8029a66d15e7b2c675593ae5e7e7a8436f | {"questions":["Does the answer compute the first grant as 17% of the original 5492-credit balance and count only the 62% that is not returned (i.e., subtract 38% of the grant) as spending?","Does the answer compute the second grant as 8% of (5492 − 8), subtracting the 8 credits before applying the percentage rather than after?","Is the base total spending, before any settlement adjustment, the sum of the retained portion of the first grant and the full second grant, expressed exactly?","Does the answer apply all 19 adjustments in the stated order, each with the correct operation sequence (for 'add then discount', add credits first then multiply the whole amount by (1 − rate); for 'surcharge then subtract', multiply by (1 + rate) first then subtract credits)?","Are all intermediate values kept exact, as fractions or exact decimals, with no rounding or truncation at any stage?","Does the answer show exactly one line per adjustment in the form 'Amount after adjustment <n>: <exact value>' for n = 1 through 19?","Does the response end with 'Final answer:' followed by a fully reduced fraction, or an integer if the denominator is 1?","Is the final answer numerically equal to the exact result of correctly applying all 19 adjustments in order to the correct base spending total?"]} {"du |
| 2026-10-30T17:56:41.869597+00:00 | retry |  |  | smoke:separate_scoring:original:B |  | a8172d1936f822c06ea2953b35ab01010aefb31e6e02d252a746f56f08722d1a |  |
| 2026-10-30T17:56:44.871507+00:00 | retry |  |  | smoke:separate_scoring:original:B |  | 61a56f57eaef9618e74f6e44449f815bd29ef3943d91e3e42a40ef558cf25df0 |  |
| 2026-10-30T17:56:47.281830+00:00 | retry |  |  | smoke:exam_prompt:original |  | 32e4d11afd7aaa8e32c6d1b88c6eefe8b89ed9a1fceebc16dabb871b188c9c9f |  |
| 2026-10-30T17:56:50.283138+00:00 | retry |  |  | smoke:exam_prompt:original |  | 2395ce3b302aa2cd6aa3dc29f1d4025751d669f92f46e1911e242df640ac293b |  |
| 2026-10-30T17:56:53.408085+00:00 | retry |  |  | smoke:free_form:original |  | bf7ac38220c3ea5f0679021c136d63eea67e13ac7e1afba2d7e9cfe3a67579d8 |  |
| 2026-10-30T17:57:17.873939+00:00 | retry |  |  | smoke:exam_prompt:polished |  | 8826da1c0191c6e8d6843fea32f4b73178924c2c780e301c074b3d0e96cfe9e5 |  |
| 2026-10-30T17:57:20.868776+00:00 | retry |  |  | smoke:item_checklist:original |  | daacfa674bb3d5f56417ebfab9d1a1ab216b8a278b4126debb12af61ea57daf5 |  |
| 2026-10-30T17:57:21.547890+00:00 | retry |  |  | smoke:exam_prompt:polished |  | 5493f6bbeab374312b6b1411ef9f77282ef8a7377ab70e2011a7fc8db8265e02 |  |
| 2026-10-30T17:57:24.515765+00:00 | retry |  |  | smoke:free_form:polished |  | e2d1c8bea7ed2bebdfcdf467cf0d640b820c44cdf8d839714a23aac696b3686d |  |
| 2026-10-30T17:58:17.368091+00:00 | retry |  |  | smoke:free_form:original |  | 17448fe8340c6ec652276f4a6060c5b210609dbae8409ada18956ebec8f6c5d0 |  |
| 2026-10-30T18:00:07.917748+00:00 | retry |  |  | smoke:free_form:polished |  | 54bc1bbf63f74d9cbdab937fb73f84399bbe71dbc010dd83d5aa6d32e1c6d68d |  |
| 2026-10-30T18:06:57.447856+00:00 | retry |  |  | development:free_form:original |  | 04b3c0f772932f0a455102e44658dd3dab78daaa89bd6537018a6900c8857c7c |  |
| 2026-10-30T18:09:21.680596+00:00 | retry |  |  | development:free_form:original |  | f542a1b40be6f70709260ce030bc6a1a93d5d745368954fdab437c501d892af6 |  |
| 2026-10-30T18:10:37.408542+00:00 | retry |  |  | development:item_checklist:original |  | dcb3be30f00fe358ab6e2b5ff251a357f7a2d08078d1223e1c7bc553d9b36c39 |  |
| 2026-10-30T18:13:27.384621+00:00 | test_frozen |  |  |  |  |  |  |
| 2026-10-30T18:14:16.770970+00:00 | retry |  |  | test:separate_scoring:original:A |  | c9b7774f7eeadbbbb62e9228d6ca4941caf06491b4837f92736481649dc85785 |  |
| 2026-10-30T18:14:47.381345+00:00 | retry |  |  | test:separate_scoring:original:B |  | 0eb1e873c7a440d18bd3a0c3e1fa3b922a912d8e9b14ae05a4020c7903d60f57 |  |
| 2026-10-30T18:15:30.909758+00:00 | retry |  |  | test:separate_scoring:original:B |  | 768b415cb2f7d8339d4fa54940aeecf75b57bd7bffb5214ff3a9a4da28b906de |  |
| 2026-10-30T18:15:56.714275+00:00 | retry |  |  | test:separate_scoring:original:A |  | 886345f36fd169d05e83ba125f1e21ac670b41887fe5bca634ae9eaa72d7a165 |  |
| 2026-10-30T18:16:32.408587+00:00 | retry |  |  | test:separate_scoring:original:A |  | 8bf360b8ca2ba4097d521dd3df3c9b5f85301b5d6cb137d302161d47a8718a5f |  |
| 2026-10-30T18:18:19.368170+00:00 | retry |  |  | test:separate_scoring:original:B |  | 898a33904b963ea16f37c7e91b53161619a4e289d916a1c6a0cdc6cdfb5df954 |  |
| 2026-10-30T18:23:57.556885+00:00 | retry |  |  | test:separate_scoring:original:A |  | 6f12bde282399d32080f59f6ed9896556ebb3811ff0742a6eb75843284aee85c |  |
| 2026-10-30T18:24:35.961108+00:00 | retry |  |  | test:separate_scoring:original:B |  | 618c28584622035f2de3753065a0f5221bdb6c135fa852f854a4dff819ff5877 |  |
| 2026-10-30T18:25:12.132266+00:00 | retry |  |  | test:separate_scoring:original:B |  | abf56c491ad987f533fdbf46ff7058b28a88d7c4c0be8a243c590200e724f99c |  |
| 2026-10-30T18:25:34.948829+00:00 | retry |  |  | test:separate_scoring:original:A |  | 443f60445469613f567315c937aa51c00240c6270a488185786d883a22e9ab18 |  |
| 2026-10-30T18:26:05.437001+00:00 | retry |  |  | test:separate_scoring:original:A |  | 00cd407aade742f10f4d8de5d59cb32d500f97118971d77b7cbfef2020461c68 |  |
| 2026-10-30T18:27:32.378036+00:00 | retry |  |  | test:separate_scoring:original:B |  | ab75b43a79ff00fc1c2ba230329e36dce65c49d4754d36a66f1fb4b28e289d0f |  |
| 2026-10-30T18:27:44.600649+00:00 | retry |  |  | test:item_checklist:original |  | f68676af5edbc19ec46dbd78aac9cddc88ee1e9ee86c5b59e64f162ab9a3e047 |  |
| 2026-10-30T18:28:10.680732+00:00 | retry |  |  | test:separate_scoring:original:B |  | c1f7162cb5f23f15606c09db6249b8c55773fecd5e1d9579d537b6eb3850fcc7 |  |
| 2026-10-30T18:28:22.823747+00:00 | retry |  |  | test:item_checklist:original |  | dd711bdfebc0d8e30e57a02ba4b128fe8c2ef90c86b3a7f2efa782c58a24e448 |  |
| 2026-10-30T18:31:44.781854+00:00 | retry |  |  | test:separate_scoring:original:A |  | 3eef490e5d376fabcdbc8d8bbcd79a0ec085efffebda49269f9a9a487eb6fb91 |  |
| 2026-10-30T18:31:48.649147+00:00 | retry |  |  | test:separate_scoring:original:A |  | 29cf90036568de7ded4d33b109d7324283cc64e1bbc5e4ed68817a87b76af695 |  |
| 2026-10-30T18:32:30.806914+00:00 | retry |  |  | test:separate_scoring:original:A |  | 7228862cc1a42b56e8951124cdd538a42c191511b5698bc92be0300295931947 |  |
| 2026-10-30T18:32:34.994307+00:00 | retry |  |  | test:separate_scoring:original:A |  | deda378f457b1afaa07e9e5e0a8297723451642c0ef3eb824600211dc05d2aab |  |
| 2026-10-30T18:32:42.586582+00:00 | retry |  |  | test:separate_scoring:original:A |  | 381a5ba3541929b0caaedc80c713afd070f31442c2e857535b6ebcb295f2f18c |  |
| 2026-10-30T18:33:04.283753+00:00 | retry |  |  | test:separate_scoring:original:B |  | 97c61f299fc3c848493cdcecb802de4f16b91a78162a03d672f9d45881507759 |  |
| 2026-10-30T18:33:23.217628+00:00 | retry |  |  | test:separate_scoring:original:B |  | bbfab51aed43da1d65d3ab2bc363dee538dfc832e6e2459cc61a95d8616f004e |  |
| 2026-10-30T18:33:26.398909+00:00 | retry |  |  | test:separate_scoring:original:A |  | 0737ffadef55de26393f842e7f5402744827d667c63061f6b5044ae9996309b6 |  |
| 2026-10-30T18:33:50.131609+00:00 | retry |  |  | test:exam_prompt:polished |  | 362bd2721ab38f89b10b57060ee19722798f5ab12cbb5e9da96b32097cd18aa5 |  |
| 2026-10-30T18:34:00.964037+00:00 | retry |  |  | test:separate_scoring:original:B |  | d10b59b443d08ab419b6b211c28d9744428fe1543c68808ed78ae421f7f0bcae |  |
| 2026-10-30T18:34:33.174164+00:00 | retry |  |  | test:exam_prompt:polished |  | 86c45806adf0d9631f6edcc4add8821f021991d5c5e6db74c76a5b73ea3c4edd |  |
| 2026-10-30T18:36:24.120319+00:00 | retry |  |  | test:separate_scoring:original:B |  | 4180228ff8965423a9659ddb1befba67ffcf93ee56bacb272f8d6624f67c5115 |  |
| 2026-10-30T18:37:16.924332+00:00 | retry |  |  | test:item_checklist:original |  | 177f1ade8d44fea63900f2e547448f810cf488ec30cae74d4a199742cc83ac4b |  |
| 2026-10-30T18:37:20.496381+00:00 | retry |  |  | test:item_checklist:original |  | 8622ee489ca910c99bd7656879c14c79f8b8b8da354eafdd69c660b36085f017 |  |
| 2026-10-30T18:41:37.975289+00:00 | retry |  |  | test:general_rubric:original |  | efdc1d616c28043df58d4b24c3a55c725c931a5bf7be5a0ef3da373e040b1cdb |  |
| 2026-10-30T18:42:22.855274+00:00 | retry |  |  | test:general_rubric:original |  | 4ee9efa4a0dcda089e8d296886be0d47029479b07e9a270e48fc956bff9d83ab |  |
| 2026-10-30T18:42:33.504873+00:00 | retry |  |  | test:separate_scoring:original:A |  | 7a0d71c7b1930e68a002eeced958435866270ce5b4ca7345e06545c4b8df21dc |  |
| 2026-10-30T18:42:58.980279+00:00 | retry |  |  | test:item_checklist:polished |  | 62afcf0fdd1d0686f692ec83297aef5f08d9bdeb7c33fb7f49ecb587b96078c9 |  |
| 2026-10-30T18:43:31.499153+00:00 | retry |  |  | test:separate_scoring:original:A |  | 8b24b5a375ea14845bb17a6c1c9c4afb0a5a86b7bb221f9cc7332530e23756fa |  |
| 2026-10-30T18:44:36.724323+00:00 | retry |  |  | test:separate_scoring:original:B |  | 9647d3ddb9aa61ac193ec16ad0bdf103c10255f58de7664b0d98816338ecbb8f |  |
| 2026-10-30T18:47:06.472809+00:00 | retry |  |  | test:separate_scoring:original:A |  | 0a897e02285cfb01a42d5775f927d40f76e88c980286fd4c82cbd3fb2805c866 |  |
| 2026-10-30T18:48:28.334044+00:00 | retry |  |  | test:separate_scoring:original:A |  | 0333b32f30fca30e5eff41a05f2b6782fd1fbd580b041f11e48977f52524f838 |  |
| 2026-10-30T18:50:05.416234+00:00 | retry |  |  | test:separate_scoring:original:A |  | 1694efbc82b38c58d0b90e79dcc9214fa456d9c14d326d657494fb643362642c |  |
| 2026-10-30T18:50:24.258128+00:00 | retry |  |  | test:separate_scoring:original:A |  | 86a3e526f9f49998057e9143b4d9e5be57eb51ab364f5240ef9dbda34601f0de |  |
| 2026-10-30T18:50:44.327056+00:00 | retry |  |  | test:separate_scoring:original:B |  | d555131ab483c81e899808f154936d23fcb8c405d0b29d6e7f4549d126dcfc5c |  |
| 2026-10-30T18:50:56.686121+00:00 | retry |  |  | test:separate_scoring:original:B |  | 3fb17951deff9383d60b16b60f7f6eae38e0d64c41ae6882988f363dc002aecf |  |
| 2026-10-30T18:51:17.007226+00:00 | retry |  |  | test:separate_scoring:original:A |  | 416ec5e8acf7209534bd154c6985e7526088149199eed636d5d41943dce86e67 |  |
| 2026-10-30T18:51:40.781285+00:00 | retry |  |  | test:separate_scoring:original:B |  | b40b1522a73ac9261f4c5590d9858f47d18b77bc56c4bb445c6fb7a14621da95 |  |
| 2026-10-30T18:51:52.627057+00:00 | retry |  |  | test:separate_scoring:original:B |  | d183efde89279a2a525328db6bc26ea7fa19bfde41b8846159832485ecfd905a |  |
| 2026-10-30T18:55:04.361410+00:00 | retry |  |  | test:item_checklist:polished |  | f2f8a33d419d788c64c5fd6f6007a0eb62761706dc4317ee1e6422b73aba4eaf |  |
| 2026-10-30T18:55:47.228831+00:00 | retry |  |  | test:item_checklist:original |  | 048877cd4c858f847fd04ef24ab35e4674802555e0f5c68bb2f3590f2e02c7d6 |  |
| 2026-10-30T18:56:16.280585+00:00 | retry |  |  | test:general_rubric:original |  | a9a679ae7295c17f654e336871827741c385d8c50ea8cf9d8ba99d739047faa8 |  |
| 2026-10-30T18:56:30.686276+00:00 | retry |  |  | test:exam_prompt:polished |  | b4d95f4cac10b029be76ddd4a1ef4c5642f4cfe7a03adf9bf6804535a24633b3 |  |
| 2026-10-30T18:57:15.860296+00:00 | retry |  |  | test:general_rubric:original |  | 0c7a382dd3e963fdd6214b95f2ad592fbc92738c435241bfeda49e51e9f53f40 |  |
| 2026-10-30T18:57:33.596596+00:00 | retry |  |  | test:exam_prompt:polished |  | 0e0fd87be7b4c830759864fdf7668aa96ddf504ed72ef963132724ad4fd71c63 |  |
| 2026-10-30T18:59:25.872090+00:00 | retry |  |  | test:item_checklist:original |  | 57eba93605dfbc429ed124f9dc972795c95d63b3e89385236561e1a2fa7da63b |  |
| 2026-10-30T18:59:41.270698+00:00 | retry |  |  | test:item_checklist:original |  | 4621b3beb345a493cd6f046905ce539d1815195dd716608ae3689e8202142ad9 |  |
| 2026-10-30T19:01:23.345383+00:00 | retry |  |  | test:free_form:original |  | 9cecfdf6bf3e078fbb90026db4c4b376e860cb5579a9a989fdac54a51db449e0 |  |
| 2026-10-30T19:01:50.325872+00:00 | retry |  |  | test:separate_scoring:original:B |  | 0f21719db0ad7d270178759bf5566700a12c2675dc0b6b66c2986278eff29e59 |  |
| 2026-10-30T19:04:34.546374+00:00 | retry |  |  | test:separate_scoring:original:A |  | 5e99179fc2b8a816804b9eb1c3c190f124d83b53c965fa0b8737558a25d69af0 |  |
| 2026-10-30T19:04:46.421332+00:00 | retry |  |  | test:free_form:polished |  | a592fb6bc2039ee4b458eaf89f3b5d468f69a5c7b01ecca03d3ecf6095cf97bc |  |
| 2026-10-30T19:05:23.749674+00:00 | retry |  |  | test:separate_scoring:original:B |  | b7f03f6f43f2a0b6e3f2639090cd9a00ffb13de9fb81c9e3c9da0680c16c5020 |  |
| 2026-10-30T19:06:49.475540+00:00 | retry |  |  | test:separate_scoring:original:A |  | e914d7f7208e463dcc334a808731409d301cefdfd053b132d755b9e06130703f |  |
| 2026-10-30T19:07:47+00:00 | manual_pause |  |  |  |  |  |  |
| 2026-11-24T06:05:21.459849+00:00 | manual_resume |  |  |  |  |  |  |
| 2026-11-24T06:06:36.821824+00:00 | resume_transport_check |  |  |  | gpt-6.1-sol |  |  |
| 2026-11-24T06:06:41.218640+00:00 | resume_transport_check |  |  |  | gpt-6-luna |  |  |
| 2026-11-24T06:06:44.668248+00:00 | resume_transport_check |  |  |  | ibm-granite/granite-4.2-8b-20260831 |  |  |
| 2026-11-24T06:06:48.831260+00:00 | resume_transport_check |  |  |  | claude-opus-5-5 |  |  |
| 2026-11-24T06:08:11.514127+00:00 | test_collection_resumed |  |  |  |  |  |  |
| 2026-11-24T06:08:14.699120+00:00 | retry |  |  | test:separate_scoring:original:A |  | c9b7774f7eeadbbbb62e9228d6ca4941caf06491b4837f92736481649dc85785 |  |
| 2026-11-24T06:08:14.746575+00:00 | retry |  |  | test:separate_scoring:original:A |  | 886345f36fd169d05e83ba125f1e21ac670b41887fe5bca634ae9eaa72d7a165 |  |
| 2026-11-24T06:08:15.000623+00:00 | retry |  |  | test:separate_scoring:original:A |  | 6f12bde282399d32080f59f6ed9896556ebb3811ff0742a6eb75843284aee85c |  |
| 2026-11-24T06:08:15.012924+00:00 | retry |  |  | test:separate_scoring:original:B |  | 618c28584622035f2de3753065a0f5221bdb6c135fa852f854a4dff819ff5877 |  |
| 2026-11-24T06:08:15.039653+00:00 | retry |  |  | test:separate_scoring:original:A |  | 443f60445469613f567315c937aa51c00240c6270a488185786d883a22e9ab18 |  |
| 2026-11-24T06:08:15.078127+00:00 | retry |  |  | test:item_checklist:original |  | f68676af5edbc19ec46dbd78aac9cddc88ee1e9ee86c5b59e64f162ab9a3e047 |  |
| 2026-11-24T06:08:15.203240+00:00 | retry |  |  | test:separate_scoring:original:A |  | 3eef490e5d376fabcdbc8d8bbcd79a0ec085efffebda49269f9a9a487eb6fb91 |  |
| 2026-11-24T06:08:17.719940+00:00 | retry |  |  | test:separate_scoring:original:B |  | 0eb1e873c7a440d18bd3a0c3e1fa3b922a912d8e9b14ae05a4020c7903d60f57 |  |
| 2026-11-24T06:08:17.760315+00:00 | retry |  |  | test:separate_scoring:original:A |  | 8bf360b8ca2ba4097d521dd3df3c9b5f85301b5d6cb137d302161d47a8718a5f |  |
| 2026-11-24T06:08:18.015838+00:00 | retry |  |  | test:separate_scoring:original:A |  | 29cf90036568de7ded4d33b109d7324283cc64e1bbc5e4ed68817a87b76af695 |  |
| 2026-11-24T06:08:18.021462+00:00 | retry |  |  | test:separate_scoring:original:B |  | abf56c491ad987f533fdbf46ff7058b28a88d7c4c0be8a243c590200e724f99c |  |
| 2026-11-24T06:08:18.042733+00:00 | retry |  |  | test:separate_scoring:original:A |  | 00cd407aade742f10f4d8de5d59cb32d500f97118971d77b7cbfef2020461c68 |  |
| 2026-11-24T06:08:18.080012+00:00 | retry |  |  | test:item_checklist:original |  | dd711bdfebc0d8e30e57a02ba4b128fe8c2ef90c86b3a7f2efa782c58a24e448 |  |
| 2026-11-24T06:08:18.204347+00:00 | retry |  |  | test:separate_scoring:original:A |  | 7228862cc1a42b56e8951124cdd538a42c191511b5698bc92be0300295931947 |  |
| 2026-11-24T06:08:20.721594+00:00 | retry |  |  | test:separate_scoring:original:B |  | 768b415cb2f7d8339d4fa54940aeecf75b57bd7bffb5214ff3a9a4da28b906de |  |
| 2026-11-24T06:08:21.018006+00:00 | retry |  |  | test:separate_scoring:original:A |  | deda378f457b1afaa07e9e5e0a8297723451642c0ef3eb824600211dc05d2aab |  |
| 2026-11-24T06:08:23.762970+00:00 | retry |  |  | test:separate_scoring:original:B |  | 898a33904b963ea16f37c7e91b53161619a4e289d916a1c6a0cdc6cdfb5df954 |  |
| 2026-11-24T06:08:24.048824+00:00 | retry |  |  | test:separate_scoring:original:B |  | ab75b43a79ff00fc1c2ba230329e36dce65c49d4754d36a66f1fb4b28e289d0f |  |
| 2026-11-24T06:08:24.051814+00:00 | retry |  |  | test:separate_scoring:original:A |  | 381a5ba3541929b0caaedc80c713afd070f31442c2e857535b6ebcb295f2f18c |  |
| 2026-11-24T06:08:24.111346+00:00 | retry |  |  | test:exam_prompt:polished |  | 362bd2721ab38f89b10b57060ee19722798f5ab12cbb5e9da96b32097cd18aa5 |  |
| 2026-11-24T06:08:24.207352+00:00 | retry |  |  | test:separate_scoring:original:B |  | bbfab51aed43da1d65d3ab2bc363dee538dfc832e6e2459cc61a95d8616f004e |  |
| 2026-11-24T06:08:26.886167+00:00 | retry |  |  | test:separate_scoring:original:B |  | 4180228ff8965423a9659ddb1befba67ffcf93ee56bacb272f8d6624f67c5115 |  |
| 2026-11-24T06:08:26.937588+00:00 | retry |  |  | test:item_checklist:original |  | 177f1ade8d44fea63900f2e547448f810cf488ec30cae74d4a199742cc83ac4b |  |
| 2026-11-24T06:08:27.022948+00:00 | retry |  |  | test:separate_scoring:original:B |  | 97c61f299fc3c848493cdcecb802de4f16b91a78162a03d672f9d45881507759 |  |
| 2026-11-24T06:08:27.051719+00:00 | retry |  |  | test:separate_scoring:original:B |  | c1f7162cb5f23f15606c09db6249b8c55773fecd5e1d9579d537b6eb3850fcc7 |  |
| 2026-11-24T06:08:27.053700+00:00 | retry |  |  | test:separate_scoring:original:A |  | 0737ffadef55de26393f842e7f5402744827d667c63061f6b5044ae9996309b6 |  |
| 2026-11-24T06:08:27.119431+00:00 | retry |  |  | test:exam_prompt:polished |  | 86c45806adf0d9631f6edcc4add8821f021991d5c5e6db74c76a5b73ea3c4edd |  |
| 2026-11-24T06:08:27.208936+00:00 | retry |  |  | test:separate_scoring:original:B |  | d10b59b443d08ab419b6b211c28d9744428fe1543c68808ed78ae421f7f0bcae |  |
| 2026-11-24T06:08:29.941054+00:00 | retry |  |  | test:item_checklist:original |  | 8622ee489ca910c99bd7656879c14c79f8b8b8da354eafdd69c660b36085f017 |  |
| 2026-11-24T06:08:29.973437+00:00 | retry |  |  | test:general_rubric:original |  | efdc1d616c28043df58d4b24c3a55c725c931a5bf7be5a0ef3da373e040b1cdb |  |
| 2026-11-24T06:08:30.061505+00:00 | retry |  |  | test:separate_scoring:original:A |  | 7a0d71c7b1930e68a002eeced958435866270ce5b4ca7345e06545c4b8df21dc |  |
| 2026-11-24T06:08:32.974854+00:00 | retry |  |  | test:general_rubric:original |  | 4ee9efa4a0dcda089e8d296886be0d47029479b07e9a270e48fc956bff9d83ab |  |
| 2026-11-24T06:08:33.069056+00:00 | retry |  |  | test:separate_scoring:original:A |  | 8b24b5a375ea14845bb17a6c1c9c4afb0a5a86b7bb221f9cc7332530e23756fa |  |
| 2026-11-24T06:08:33.077971+00:00 | retry |  |  | test:item_checklist:polished |  | 62afcf0fdd1d0686f692ec83297aef5f08d9bdeb7c33fb7f49ecb587b96078c9 |  |
| 2026-11-24T06:08:33.242521+00:00 | retry |  |  | test:separate_scoring:original:A |  | 0a897e02285cfb01a42d5775f927d40f76e88c980286fd4c82cbd3fb2805c866 |  |
| 2026-11-24T06:08:33.303915+00:00 | retry |  |  | test:separate_scoring:original:A |  | 1694efbc82b38c58d0b90e79dcc9214fa456d9c14d326d657494fb643362642c |  |
| 2026-11-24T06:08:33.312362+00:00 | retry |  |  | test:separate_scoring:original:A |  | 86a3e526f9f49998057e9143b4d9e5be57eb51ab364f5240ef9dbda34601f0de |  |
| 2026-11-24T06:08:36.044348+00:00 | retry |  |  | test:item_checklist:polished |  | f2f8a33d419d788c64c5fd6f6007a0eb62761706dc4317ee1e6422b73aba4eaf |  |
| 2026-11-24T06:08:36.111537+00:00 | retry |  |  | test:item_checklist:original |  | 048877cd4c858f847fd04ef24ab35e4674802555e0f5c68bb2f3590f2e02c7d6 |  |
| 2026-11-24T06:08:36.249723+00:00 | retry |  |  | test:separate_scoring:original:A |  | 0333b32f30fca30e5eff41a05f2b6782fd1fbd580b041f11e48977f52524f838 |  |
| 2026-11-24T06:08:36.307661+00:00 | retry |  |  | test:separate_scoring:original:B |  | d555131ab483c81e899808f154936d23fcb8c405d0b29d6e7f4549d126dcfc5c |  |
| 2026-11-24T06:08:36.313928+00:00 | retry |  |  | test:separate_scoring:original:A |  | 416ec5e8acf7209534bd154c6985e7526088149199eed636d5d41943dce86e67 |  |
| 2026-11-24T06:08:38.985474+00:00 | retry |  |  | test:general_rubric:original |  | a9a679ae7295c17f654e336871827741c385d8c50ea8cf9d8ba99d739047faa8 |  |
| 2026-11-24T06:08:39.053604+00:00 | retry |  |  | test:exam_prompt:polished |  | b4d95f4cac10b029be76ddd4a1ef4c5642f4cfe7a03adf9bf6804535a24633b3 |  |
| 2026-11-24T06:08:39.074436+00:00 | retry |  |  | test:separate_scoring:original:B |  | 9647d3ddb9aa61ac193ec16ad0bdf103c10255f58de7664b0d98816338ecbb8f |  |
| 2026-11-24T06:08:39.180467+00:00 | retry |  |  | test:item_checklist:original |  | 57eba93605dfbc429ed124f9dc972795c95d63b3e89385236561e1a2fa7da63b |  |
| 2026-11-24T06:08:39.309779+00:00 | retry |  |  | test:separate_scoring:original:B |  | b40b1522a73ac9261f4c5590d9858f47d18b77bc56c4bb445c6fb7a14621da95 |  |
| 2026-11-24T06:08:41.987249+00:00 | retry |  |  | test:general_rubric:original |  | 0c7a382dd3e963fdd6214b95f2ad592fbc92738c435241bfeda49e51e9f53f40 |  |
| 2026-11-24T06:08:42.055846+00:00 | retry |  |  | test:exam_prompt:polished |  | 0e0fd87be7b4c830759864fdf7668aa96ddf504ed72ef963132724ad4fd71c63 |  |
| 2026-11-24T06:08:42.087886+00:00 | retry |  |  | test:item_checklist:original |  | 4621b3beb345a493cd6f046905ce539d1815195dd716608ae3689e8202142ad9 |  |
| 2026-11-24T06:08:42.212406+00:00 | retry |  |  | test:separate_scoring:original:B |  | 0f21719db0ad7d270178759bf5566700a12c2675dc0b6b66c2986278eff29e59 |  |
| 2026-11-24T06:08:42.252704+00:00 | retry |  |  | test:separate_scoring:original:B |  | 3fb17951deff9383d60b16b60f7f6eae38e0d64c41ae6882988f363dc002aecf |  |
| 2026-11-24T06:08:42.322878+00:00 | retry |  |  | test:free_form:original |  | 9cecfdf6bf3e078fbb90026db4c4b376e860cb5579a9a989fdac54a51db449e0 |  |
| 2026-11-24T06:08:45.150249+00:00 | retry |  |  | test:separate_scoring:original:A |  | 5e99179fc2b8a816804b9eb1c3c190f124d83b53c965fa0b8737558a25d69af0 |  |
| 2026-11-24T06:08:45.245209+00:00 | retry |  |  | test:free_form:polished |  | a592fb6bc2039ee4b458eaf89f3b5d468f69a5c7b01ecca03d3ecf6095cf97bc |  |
| 2026-11-24T06:08:45.254561+00:00 | retry |  |  | test:separate_scoring:original:B |  | d183efde89279a2a525328db6bc26ea7fa19bfde41b8846159832485ecfd905a |  |
| 2026-11-24T06:08:45.372542+00:00 | retry |  |  | test:separate_scoring:original:A |  | e914d7f7208e463dcc334a808731409d301cefdfd053b132d755b9e06130703f |  |
| 2026-11-24T06:08:48.152732+00:00 | retry |  |  | test:separate_scoring:original:B |  | b7f03f6f43f2a0b6e3f2639090cd9a00ffb13de9fb81c9e3c9da0680c16c5020 |  |
| 2026-11-24T06:08:51.176390+00:00 | retry |  |  | test:free_form:original |  | 834b505924e3cb57030d179f986bdf82392ae503a0b8578887a6ecfdadba6d9d |  |
| 2026-11-24T06:09:09.667086+00:00 | retry |  |  | test:own_requirements:original |  | afc2ed088a16fdeaf97b77318cf4f02f6a5370d2309802255483f057a1167cb3 |  |
| 2026-11-24T06:09:19.228264+00:00 | retry |  |  | test:separate_scoring:original:B |  | 79ea426759da5e8fb8b3263b084a792afb5203685ce938f6bbbcd6846ba2ed38 |  |
| 2026-11-24T06:09:57.040969+00:00 | retry |  |  | test:own_requirements:original |  | af9edec7eb9e832c06aa59b65ab1c8fb3c3f7f20ad6e8625490611e7c216e51d |  |
| 2026-11-24T06:10:04.934992+00:00 | retry |  |  | test:separate_scoring:original:B |  | eb175694d5a219895b4695c0098c80698914293fdbac68f0a8454781aee77d8c |  |
| 2026-11-24T06:12:22.302477+00:00 | retry |  |  | test:item_checklist:polished |  | 8b17cce48380a6d7dc1318e7dad09e614650b4fb729a1027acc792b21b882818 |  |
| 2026-11-24T06:13:39.306110+00:00 | retry |  |  | test:separate_scoring:original:B |  | 4324ae504f12a5b4f6d420da5379bb2a378bd970ef28b1ae6ef742f371d298e0 |  |
| 2026-11-24T06:14:20.189382+00:00 | retry |  |  | test:separate_scoring:original:B |  | b4707109c874c4d67281d7ddb72523f296b090651a4824b2ab9a0551a3be85de |  |
| 2026-11-24T06:14:29.234920+00:00 | retry |  |  | test:free_form:original |  | 4637255d3e3aa849ca2fd62f61513995251cb53861594368363c497f70d9dd32 |  |
| 2026-11-24T06:15:20.013098+00:00 | retry |  |  | test:free_form:original |  | abb225d0a088bc2460cb36c597e567be5ea3800aa58a46e9355f35218ea86b8c |  |
| 2026-11-24T06:19:06.662587+00:00 | retry |  |  | test:separate_scoring:original:A |  | 64236ebdbc069f30f20ab11a3af1ac6274b9889f1cab53959c907b883865ca9d |  |
| 2026-11-24T06:19:38.263971+00:00 | retry |  |  | test:separate_scoring:original:A |  | fd1d800a1e57f6e3ab4fa0df8bf12cd3b6e5ff1eab97c1a423d4d0d2ac43326f |  |
| 2026-11-24T06:20:33.712068+00:00 | retry |  |  | test:separate_scoring:original:B |  | 8fdb1be643f405785eca3a9bad6ce8cdcea9fca508845e1ba1be2135fb8fadea |  |
| 2026-11-24T06:22:32.178804+00:00 | retry |  |  | test:separate_scoring:original:A |  | 25559249002b3160f1808cd885872185f23f78cdda6746f311af81855e7b6bec |  |
| 2026-11-24T06:22:59.628517+00:00 | retry |  |  | test:exam_prompt:polished |  | b7a9f830271418cf6155107f8bb113ee10f31052ea0b7bb98b2a3270788173c7 |  |
| 2026-11-24T06:23:17.942727+00:00 | retry |  |  | test:separate_scoring:original:A |  | 45ca9342aee5cca5e7bb8ea137555580250f9f1a3b25bd3f165dde537d6600a6 |  |
| 2026-11-24T06:32:57.579269+00:00 | retry |  |  | test:separate_scoring:original:B |  | fbfbef94bacfd23fccb3f00213c1a26b1fd46dff8f28199b52c990c62582ffdf |  |
| 2026-11-24T06:32:59.911298+00:00 | retry |  |  | test:free_form:polished |  | 956035df4433bd11aa6bb77e221991757e2121f011acbe38291db2a0cb6bf1d8 |  |
| 2026-11-24T06:33:06.791621+00:00 | retry |  |  | test:item_checklist:original |  | aff06738818889af70dd19317029525dddbf8d8f95c8b33d085a2b5a70281292 |  |
| 2026-11-24T06:33:07.103751+00:00 | retry |  |  | test:free_form:original |  | bed31423a4d17a858f41f1c65246614ffd044493e77f1e39c678cf43d09e147d |  |
| 2026-11-24T06:33:09.296142+00:00 | retry |  |  | test:separate_scoring:original:B |  | abe01c54dc55f748d247fd248a0910a53bd2a96dd9cd3c7d8cbba80070e8bd72 |  |
| 2026-11-24T06:33:11.678983+00:00 | retry |  |  | test:free_form:polished |  | 8905427aac7b232665f8d25b138ef3efd83bebf63f11680524019e87de9abf0b |  |
| 2026-11-24T06:33:14.037805+00:00 | retry |  |  | test:item_checklist:original |  | df2e2ce8d54c657398aaa25706b07f64651784df8bd63756fdf39d92eb3a1956 |  |
| 2026-11-24T06:33:16.538090+00:00 | retry |  |  | test:exam_prompt:polished |  | d6bd051bd699a890dc54a56dc231531c57aba40acb79e49986358541dd00954c |  |
| 2026-11-24T06:34:54.927733+00:00 | retry |  |  | test:item_checklist:polished |  | b02e3b079b1a0cae3823dee0f45a905a5a3ce24a04a3f0cc04327b238f34632e |  |
| 2026-11-24T06:34:57.162330+00:00 | retry |  |  | test:separate_scoring:original:A |  | f26f85bec605277154d10b4a7cfd0a1ccc7a3254d3999fbb4dca6f4e3c23087b |  |
| 2026-11-24T06:34:59.510959+00:00 | retry |  |  | test:free_form:original |  | 150bddfb86080f5cb963deb816db48efbecc92b5bcad55b14588dcd7df2cdb10 |  |
| 2026-11-24T06:35:01.801347+00:00 | retry |  |  | test:free_form:original |  | c60f77bd2642f070635a35c423654e3fef7c20c3698c44c57c016ebc6be96cc9 |  |
| 2026-11-24T06:35:04.772961+00:00 | retry |  |  | test:item_checklist:polished |  | 02981b7ef981c53e9d3fae97e2d0d3e622cf52324baa2832958ce064c9394699 |  |
| 2026-11-24T06:35:07.242902+00:00 | retry |  |  | test:item_checklist:original |  | aaf9c824e10fdfe5a6b2a981e98c20b77c06c6bba921a33d03089b79c4944a83 |  |
| 2026-11-24T06:35:08.524577+00:00 | retry |  |  | test:separate_scoring:original:A |  | 7a7df8c7f8cdf18654467cedaff89aad8528dfc19206b25ad21f3d5d911ec7d3 |  |
| 2026-11-24T06:35:09.945287+00:00 | retry |  |  | test:free_form:original |  | 4bad084857e1580bf4136408b2a8e4ffdafc255ca6d1d5be8889c056ae166b42 |  |
| 2026-11-24T06:35:11.330474+00:00 | retry |  |  | test:own_requirements:original |  | f617f45f0b132226f08784a180bf04c541880359aaca3c0f738d0fb37fd6baa1 |  |
| 2026-11-24T06:35:12.805461+00:00 | retry |  |  | test:free_form:original |  | d5567addb9efb72822b33a272b31daae6fc8376829d64fd7a58cecb467255017 |  |
| 2026-11-24T06:35:13.605203+00:00 | retry |  |  | test:item_checklist:original |  | 27fb4327805d0616b8f8143f3910e4d33ec08a56ea3e3a9afd3344e274b8e09d |  |
| 2026-11-24T06:35:16.670908+00:00 | retry |  |  | test:own_requirements:original |  | fcc9a5af0c618cc5fe8d390d055783d1d5cc20d949c40f51427d78105d8335d3 |  |
| 2026-11-24T06:35:20.407599+00:00 | retry |  |  | test:item_checklist:polished |  | 1583220aa0c941b4e6d6faa95d291a7bf40da4333f9305af21b118c9426d6f25 |  |
| 2026-11-24T06:36:17.142227+00:00 | retry |  |  | test:free_form:polished |  | 2969f586fcac868840519c3cf8358758154a8e442c401c653a7329709019d687 |  |
| 2026-11-24T06:36:19.675371+00:00 | retry |  |  | test:free_form:polished |  | 87a575f94155c4e1178ac4a74e7bb53e39ba5fea1701681c01280c48bc5a9b50 |  |
| 2026-11-24T06:36:39.259816+00:00 | retry |  |  | test:free_form:polished |  | dfea7a92cf24cba55b0906d59827eb75302e8e3257fd8b2cb3f788b06fdbd599 |  |
| 2026-11-24T06:36:46.709332+00:00 | retry |  |  | test:exam_prompt:polished |  | 0944e707721065e8481a517683b39a28a3353f95cbea9ee54fb681e75cc8d3d4 |  |
| 2026-11-24T06:36:48.933494+00:00 | retry |  |  | test:separate_scoring:original:A |  | a32b1e9523c72cc0056a8a35f933e5925039f8caabcd23a78c7eb73060d16b83 |  |
| 2026-11-24T06:36:55.233473+00:00 | retry |  |  | test:separate_scoring:original:A |  | 933360ae037b5ee0cabe0540bf8ed2af26b9d8fe9c1f90afc653690e1c31b450 |  |
| 2026-11-24T06:36:56.270096+00:00 | retry |  |  | test:item_checklist:original |  | 8576e5a7109a4886fb343f2718f53baf8d1abfb9af58094cabf9cdbeaa861fc9 |  |
| 2026-11-24T06:36:58.187885+00:00 | retry |  |  | test:exam_prompt:polished |  | e13174505352290261ce4c0af15b5498dca1150633009d80af93d3da3faccf58 |  |
| 2026-11-24T06:36:59.690965+00:00 | retry |  |  | test:item_checklist:original |  | ba2b1513747fc068a439ed007cf7515c79c78a0db24fc03186e76583fe1a668b |  |
| 2026-11-24T06:37:01.173006+00:00 | retry |  |  | test:separate_scoring:original:A |  | 7fc6286842c7a89a5cc5888440738e766947a979ed5c9587b08d21484457584c |  |
| 2026-11-24T06:37:04.889926+00:00 | retry |  |  | test:free_form:original |  | f835a6260bbf4aa6b11e33e3aa112a08ab7e4fef63479fa76608fb4c11c29167 |  |
| 2026-11-24T06:37:07.587346+00:00 | retry |  |  | test:separate_scoring:original:A |  | 6a0ef58ef024b618cc9134597393cec4994a8aa7235453fa621d38aee7095257 |  |
| 2026-11-24T06:37:09.271000+00:00 | retry |  |  | test:item_checklist:original |  | 6d28f0e4ce026f55c53ed4be74fe9aa5888acfb93884f188649a0e48fd98a58e |  |
| 2026-11-24T06:37:10.904480+00:00 | retry |  |  | test:item_checklist:original |  | 63b92a90dc4788ef6559442b74260b5e3de4c01e2ee4a1b78704eef814bbd8af |  |
| 2026-11-24T06:37:18.447408+00:00 | retry |  |  | test:free_form:original |  | e03d99a430eb9a75fe65d2511998d77878d9b8baa831bdd547c11e8354a31be8 |  |
| 2026-11-24T06:37:18.862672+00:00 | retry |  |  | test:separate_scoring:original:A |  | 39c1060d01827ba95ea9ca4e0c8580b908972ccc091a2cfc83219072d8945149 |  |
| 2026-11-24T06:39:03.995242+00:00 | retry |  |  | test:separate_scoring:original:A |  | 0ef139b2cadbd10ffdb0e7c0e9357531113d99aa6d59f704e9c94f3cf09df0fd |  |
| 2026-11-24T06:39:11.428425+00:00 | retry |  |  | test:free_form:original |  | 82a66f9b89eb2f97847ea51d6c4682026ad4c6808e94579397458ade3909cfa6 |  |
| 2026-11-24T06:39:12.622209+00:00 | retry |  |  | test:separate_scoring:original:A |  | b6b786f9b431093c9f9b7ff046cf7af06de9a72098357e23ad280ec0accf5ae5 |  |
| 2026-11-24T06:39:13.680625+00:00 | retry |  |  | test:separate_scoring:original:B |  | aebc391b2419150908cbf5c0f105e151f48f6470ee75f518fed88518908befa0 |  |
| 2026-11-24T06:39:16.528293+00:00 | retry |  |  | test:separate_scoring:original:A |  | aff430831f542fdb7b30769391eab16073d92bcd8b6aa8852669a8bd1278aefe |  |
| 2026-11-24T06:39:19.612068+00:00 | retry |  |  | test:separate_scoring:original:B |  | fa6a4e8c9712e301d3bd2b1c1eddfa9982a97cb70c3ce68432dbe513ae4580f4 |  |
| 2026-11-24T06:39:22.255966+00:00 | retry |  |  | test:free_form:original |  | f815e093ce537c1785d9cef2bedde2d9d38cb419f4b9d1abab32026b51f2f1fd |  |
| 2026-11-24T06:39:42.475734+00:00 | retry |  |  | test:separate_scoring:original:A |  | 4d9f427d0361b3d546aa21e133a2550b2f6ec1c6ea30fbc85fafd6284b2820dd |  |
| 2026-11-24T06:40:03.773938+00:00 | retry |  |  | test:separate_scoring:original:A |  | ce5268dc6d1c120f52cca4e8b82819aa9699843a7944d6b6beb56ba6f3be40de |  |
| 2026-11-24T06:40:06.083333+00:00 | retry |  |  | test:separate_scoring:original:B |  | 26e7df845f411e1bf03672b993c8667b0a535eefc6ab0cd33c7fca20e8003d48 |  |
| 2026-11-24T06:40:08.791850+00:00 | retry |  |  | test:item_checklist:polished |  | 325abb92a539be4ab962b01b6dc99d21e8bc83048600995b1f3c73655dec3f88 |  |
| 2026-11-24T06:40:11.282506+00:00 | retry |  |  | test:free_form:original |  | e0f71955801edc4e2e29d0532d40ee4e95a1ea328f2670385061994e069224c8 |  |
| 2026-11-24T06:40:13.761753+00:00 | retry |  |  | test:separate_scoring:original:A |  | 579ca15cff05a69ae6581a2b2de8275dedb7c2bec37b474c9d852be1c2636fd9 |  |
| 2026-11-24T06:40:15.661209+00:00 | retry |  |  | test:general_rubric:original |  | b10d06922bcbcd09f4ee5a768a5afa595124c1b0430576530ef7ee7a95e27e03 |  |
| 2026-11-24T06:40:17.996397+00:00 | retry |  |  | test:separate_scoring:original:B |  | 7994bdb0ce72f1d585c39e97337a2fe2461172295436bb3e8dfb7aa1f2eb3382 |  |
| 2026-11-24T06:40:20.578697+00:00 | retry |  |  | test:item_checklist:polished |  | b236bacaeea43a1a42007f6b11af60c9fedd688e543ac25f84edd1d8b884de76 |  |
| 2026-11-24T06:40:20.968957+00:00 | retry |  |  | test:free_form:original |  | 1a6e647084990f1ac6e97167a174eb5325e18c8a74b1d1a8a458fb78f78dfcf4 |  |
| 2026-11-24T06:40:23.511945+00:00 | retry |  |  | test:general_rubric:original |  | dd477ecbdcedabfb3f812ce18d573305c751df85c9daa395ab74f42d66f08dbd |  |
| 2026-11-24T06:40:56.251199+00:00 | retry |  |  | test:separate_scoring:original:B |  | 7734bd5ecff94297ee0a70d18685c564b567f6aacfc8208bbb94c2a1602a3291 |  |
| 2026-11-24T06:41:19.186292+00:00 | retry |  |  | test:item_checklist:original |  | 59553ee5df00ef0f88aca95a4feeb819dc90b6f8961875a48d433d1c1dfa6948 |  |
| 2026-11-24T06:41:19.235944+00:00 | retry |  |  | test:separate_scoring:original:B |  | bbcbfeec1a736db16341b79944b3eb2358021a104de4852e1adcdcfb7887a9d2 |  |
| 2026-11-24T06:41:21.604109+00:00 | retry |  |  | test:separate_scoring:original:A |  | 39b2826b879a0858358254e6ca339cff7e6e0666e8a9fb76f07d12dd7613702e |  |
| 2026-11-24T06:41:24.432361+00:00 | retry |  |  | test:item_checklist:original |  | 7ba91f3c81ad34ea04bfad8ad7a0abaf65fcd43d5efd1094e2d6f276f6084f40 |  |
| 2026-11-24T06:42:09.024591+00:00 | retry |  |  | test:item_checklist:original |  | 6aca2d62ad22e215bc553f5239b56fc99c76e9f55fefae917d48c8bef5f94626 |  |
| 2026-11-24T06:42:45.802802+00:00 | retry |  |  | test:separate_scoring:original:B |  | 7ea2ab56df80d36ddc979e4249d5e5e04f4ba12b9c87a09f996302368a34c560 |  |
| 2026-11-24T06:42:46.312125+00:00 | retry |  |  | test:separate_scoring:original:B |  | 6c223f02844048a77b34b10b6f1f0e6f97c7d6304f5bea44e7a8aed1476f69cf |  |
| 2026-11-24T06:43:06.241529+00:00 | retry |  |  | test:separate_scoring:original:B |  | 7b852bdce447e87adbb8064a6ff8ffdb2ade03f849ccee3d2bbe36a73707a6a0 |  |
| 2026-11-24T06:43:10.602707+00:00 | retry |  |  | test:exam_prompt:polished |  | 6ce08039042971d71d0185d8e163fdce5e9a64016195eb30ce9353b0c081c4b5 |  |
| 2026-11-24T06:43:12.987228+00:00 | retry |  |  | test:general_rubric:original |  | 801b600b878f039cb412deda4bbb8c573f777fae94dacd1c104584ccaa74b959 |  |
| 2026-11-24T06:43:15.220857+00:00 | retry |  |  | test:separate_scoring:original:A |  | ed8bd0105c914f0a063e03ee5f7f238d44834183cc0e56c30368b09a4f71608e |  |
| 2026-11-24T06:43:19.767449+00:00 | retry |  |  | test:exam_prompt:polished |  | 604f76d962ec2a34003b248aff5381e1851cc090167e9988ed6e1439a203e9b9 |  |
| 2026-11-24T06:43:21.398743+00:00 | retry |  |  | test:general_rubric:original |  | c692e4cb7fe9c88e1eed94bbc7be745c70978eb03585f38ed2bc0b00ad59ad40 |  |
| 2026-11-24T06:43:22.098160+00:00 | retry |  |  | test:general_rubric:original |  | 43fec803320974965bbde0bd91c49d645c333b05fa9101d814b84ef11a92c44e |  |
| 2026-11-24T06:43:24.490360+00:00 | retry |  |  | test:separate_scoring:original:A |  | 6dee63429a66b4a258a07e42ce17116825e3ceaacfc209a96dd57ba4dbcf1739 |  |
| 2026-11-24T06:43:26.567430+00:00 | retry |  |  | test:exam_prompt:polished |  | 8352c467881c50756e52ee8aa21262133b81df035e63904a6e7a87b76d74f7ef |  |
| 2026-11-24T06:43:46.590909+00:00 | retry |  |  | test:exam_prompt:polished |  | d389d8d2aca815139183f80474ff4a8c4be290b95579217f68b04044b3a2864a |  |
| 2026-11-24T06:43:59.280748+00:00 | retry |  |  | test:free_form:polished |  | 858c9f000b5f45fdc99726a186e5000f015ddeceabb7593f1fee6251149efd6a |  |
| 2026-11-24T06:44:00.693455+00:00 | retry |  |  | test:separate_scoring:original:B |  | 0757f3965352afdcc4ddfbeaa96e7da9b4fca05f51d3d70e19cae24041db12f1 |  |
| 2026-11-24T06:44:07.699531+00:00 | retry |  |  | test:separate_scoring:original:A |  | 38653b948b9208ceb1871c2e01473648193c697d19690809142aab1fb6acf025 |  |
| 2026-11-24T06:44:09.772015+00:00 | retry |  |  | test:free_form:polished |  | 6311114883b3d5dcfbf833f39b08b83baa96db6ba30a5ee44c88f127d7a09a19 |  |
| 2026-11-24T06:44:11.963592+00:00 | retry |  |  | test:separate_scoring:original:B |  | 9daf98486e82f7a03a80c3b3ad8b12222dbb02337abfda998824e74700108715 |  |
| 2026-11-24T06:44:20.339197+00:00 | retry |  |  | test:separate_scoring:original:A |  | f974ed813f51045812421169765d8bec552963363ca52166ae2a854c066ede26 |  |
| 2026-11-24T06:44:22.528107+00:00 | retry |  |  | test:free_form:original |  | f1481972e129972d48f37dc4bd5e568f22fc9e967a9431130d75b16fe0d8c0af |  |
| 2026-11-24T06:44:43.434304+00:00 | retry |  |  | test:item_checklist:original |  | 074919aa490224ffc750b77f95def3369a491357b108b6d1ec1f6cbafe5fd074 |  |
| 2026-11-24T06:44:45.471131+00:00 | retry |  |  | test:general_rubric:original |  | 44f113f255f5b2fae6f99c952e01c9a43ab78a9bcb71bf08999f2563dd512ac3 |  |
| 2026-11-24T06:44:47.907599+00:00 | retry |  |  | test:own_requirements:original |  | 9d613c80252403a38b153dbd7a42752ad37b42b1b7d45c03dcfcd3dacdace80a |  |
| 2026-11-24T06:44:48.523209+00:00 | retry |  |  | test:separate_scoring:original:B |  | f7211f3c0118a85cec276818f982c1edd164ba92920af9e95d0eddc20499d3b2 |  |
| 2026-11-24T06:44:50.889849+00:00 | retry |  |  | test:item_checklist:original |  | dfc33ef108495238027a406c1ab76bd5960f0faf4156ffe3f696b9a9a2613d35 |  |
| 2026-11-24T06:44:53.032682+00:00 | retry |  |  | test:item_checklist:original |  | adb88654f85ad30c80a1412b030c46c585251e82573f786652446a6500fa9824 |  |
| 2026-11-24T06:44:54.414243+00:00 | retry |  |  | test:general_rubric:original |  | 507b95eff29c8d184a197ba413360215794665d881e7fc66af88ef4f8ec48dde |  |
| 2026-11-24T06:44:55.258162+00:00 | retry |  |  | test:own_requirements:original |  | 46d5c5564961a939580fccc8b8c497d1f75528cfaa264c88682769cacd6f1fcc |  |
| 2026-11-24T06:44:56.771812+00:00 | retry |  |  | test:separate_scoring:original:B |  | 715e5e2e9e7b5056b8ed83d70cb0d2f05ea7bf40a6028e0ab88d1015c0883efb |  |
| 2026-11-24T06:44:57.450338+00:00 | retry |  |  | test:exam_prompt:polished |  | f28a793cd8fa8b86d1e78ee52c56cfd54dd9e8bc0792720f2d9e46222e3c1d6d |  |
| 2026-11-24T06:44:58.967892+00:00 | retry |  |  | test:item_checklist:original |  | c19de7b4e2d338624552d8d4381d4dbd06b0ad3671a6b01d1ac88815c5995a5a |  |
| 2026-11-24T06:44:59.213790+00:00 | retry |  |  | test:general_rubric:original |  | 5ac37bb57d186dd8ec10f7c2c8219a09ec2ca8786167486178f868580ea2d712 |  |
| 2026-11-24T06:45:03.462197+00:00 | retry |  |  | test:exam_prompt:polished |  | 69984d335cef0004de7a91abfdb62c55ead51ea52adbc8cfaa347d5259293260 |  |
| 2026-11-24T06:45:05.671533+00:00 | retry |  |  | test:general_rubric:original |  | ab7484fd5107a8dfe1eed28fac7328a372880a2f118888925e4fdbe0903cf798 |  |
| 2026-11-24T06:45:07.778887+00:00 | retry |  |  | test:item_checklist:polished |  | 3b3412926d3470816875587e127a3b9f9a5bf4824f74d028f2f9482a48bb20c7 |  |
| 2026-11-24T06:45:10.720290+00:00 | retry |  |  | test:general_rubric:original |  | f9c4fe5ff72422dd2181fa0f02fc3ba355191deb21fd6b3052fc652ae5e70aab |  |
| 2026-11-24T06:45:15.120417+00:00 | retry |  |  | test:free_form:original |  | 0865fbf106e90619e10998734b9e70707b832229acd92b771b9315ff51e8a4c1 |  |
| 2026-11-24T06:45:17.600727+00:00 | retry |  |  | test:item_checklist:polished |  | 55d1f394b8cb13281da257978435d07b4b96e6f077c908dda2a18089337da4da |  |
| 2026-11-24T06:45:19.749869+00:00 | retry |  |  | test:free_form:polished |  | c5951915d06c943fb3d1505174c28e05b73115685bfeefe308bb445a80504f7d |  |
| 2026-11-24T06:45:24.021029+00:00 | retry |  |  | test:item_checklist:original |  | db99c408f439bb6518d0e5dbc8d151c872b3cff6a25dad6ddd5b65a63d9c6f71 |  |
| 2026-11-24T06:45:24.322141+00:00 | retry |  |  | test:free_form:original |  | c7655845d2b2451a0024def519bb2318567838854dfa6dd956f96bbafe4ea336 |  |
| 2026-11-24T06:45:26.717932+00:00 | retry |  |  | test:free_form:polished |  | 99455d8a170c1a800ae1b0829f2d5cf73f76674b500baff8ba25b88f74f53a64 |  |
| 2026-11-24T06:45:35.116832+00:00 | retry |  |  | test:general_rubric:original |  | 6adc8376c24730bcd249a8f9daf6aabaa5d26156dd4080e5a5bfc31f6c9695ba |  |
| 2026-11-24T06:45:48.854482+00:00 | retry |  |  | test:item_checklist:polished |  | a02a1a2e811544019342469e3a5b24137914d317f2a5eb704b7e3b167898b8c6 |  |
| 2026-11-24T06:45:59.089490+00:00 | retry |  |  | test:item_checklist:polished |  | 5fddff9982558c5fd187226b7b69edfb3d7f36bf760067cf3a7e04c4526f56ef |  |
| 2026-11-24T06:46:05.218135+00:00 | retry |  |  | test:separate_scoring:original:A |  | 92211b0861724cde777828a4a8c3fec317b397fd212d48b2f2d83dbc4de88980 |  |
| 2026-11-24T06:46:06.354315+00:00 | retry |  |  | test:general_rubric:original |  | d3de15e3529195c19eaa24bb317f8508d18ef1beddeb0050226c08ab195a8117 |  |
| 2026-11-24T06:46:10.925792+00:00 | retry |  |  | test:item_checklist:polished |  | 669ebfdcf97951c37860b8ac99410e3a9d6bdb3a3f1df1ee3c0456b3610c6844 |  |
| 2026-11-24T06:46:11.814922+00:00 | retry |  |  | test:general_rubric:original |  | f15bd9a5fdc89285b5a777499bff7552d7b16fe4b6a33493b77e247e8b0f59f9 |  |
| 2026-11-24T06:46:13.168742+00:00 | retry |  |  | test:free_form:original |  | 3c3b4b95b232ba48eedf74fe1186f8633b79548399d67832282b15fc5d975cdf |  |
| 2026-11-24T06:46:14.099559+00:00 | retry |  |  | test:general_rubric:original |  | 953174b3ed40657d8e2ed74611a2a0708493fbc63646a55b4c2c9b3abf554cca |  |
| 2026-11-24T06:46:16.183957+00:00 | retry |  |  | test:item_checklist:polished |  | a45668b2fcec2a86fc3047dbfa4cd1e0ba6d6e08daffb6cf089d3590153647b3 |  |
| 2026-11-24T06:46:18.198477+00:00 | retry |  |  | test:free_form:original |  | 1d754d3dcb8a6906f54d0ac8c3a81c3f795e785639d91ce2a6b07a8b32c936ef |  |
| 2026-11-24T06:46:26.556750+00:00 | retry |  |  | test:general_rubric:original |  | ee806f06c72eb4b33efda98c86e8c64193d8541b3bd0fcd7afaff20af87a64fa |  |
| 2026-11-24T06:46:30.293772+00:00 | retry |  |  | test:general_rubric:original |  | 11f864d97014291c62e4ba6370d01291f803cad15006500a33fd191ceec64621 |  |
| 2026-11-24T06:46:47.539617+00:00 | retry |  |  | test:general_rubric:original |  | 196ba10c85457fefcbd677cba2e3a4e8373fe18882d39677ca3823a6e1827ce1 |  |
| 2026-11-24T06:46:48.770555+00:00 | retry |  |  | test:general_rubric:original |  | 03faf9cd204f08c51268733089891af7a34df2a78ff0153aefd0c41c9270a076 |  |
| 2026-11-24T06:47:00.595919+00:00 | retry |  |  | test:item_checklist:original |  | 710189561e2542a5d12ee1ffe1d8a514cfdca7f3869670b36779532aefbd7560 |  |
| 2026-11-24T06:47:03.093037+00:00 | retry |  |  | test:exam_prompt:polished |  | 492b00b554e268c2dd6e76b6eca22c4cf9c08368e634fddf41b9f447a1abb4a8 |  |
| 2026-11-24T06:47:19.788973+00:00 | retry |  |  | test:item_checklist:original |  | cd658b88af6fc2d480c74c364d5245e470f0ff4d2984282a67840f1c89d5bbee |  |
| 2026-11-24T06:47:22.760011+00:00 | retry |  |  | test:exam_prompt:polished |  | c0ae18aa5aa768d9ab77d112dd96356af5d4e99810e4cf567a2b2323ed337d7b |  |
| 2026-11-24T06:47:24.945152+00:00 | retry |  |  | test:free_form:polished |  | 08f47ecdf9b81a03bd1763ce40188c438293c82c6d7d83267749a4d6e42e6524 |  |
| 2026-11-24T06:47:38.629749+00:00 | retry |  |  | test:free_form:polished |  | 74dc28f58e374663f3cab6b5dc0c60b3273dd656e0051b559e21bf1bf8e1eb3a |  |
| 2026-11-24T06:47:43.271972+00:00 | retry |  |  | test:own_requirements:original |  | e345615041550d0594c375cae01f9f9edf5b018dcaf8f993fcd51097923aa134 |  |
| 2026-11-24T06:47:45.333063+00:00 | retry |  |  | test:item_checklist:polished |  | 346fc5213c1055903ef18fb01536115539bbc34b8cd52cbf53347f1e547aed20 |  |
| 2026-11-24T06:47:52.238048+00:00 | retry |  |  | test:own_requirements:original |  | 5fed0742ad7f26e6163c53fcacc2725ab813b155e5d102afaf7666b542e02bc0 |  |
| 2026-11-24T06:47:54.712846+00:00 | retry |  |  | test:own_requirements:original |  | 257b7b829401447370527d356f5ecc4db28a5892b660a4e82d79d30647196ced |  |
| 2026-11-24T06:47:56.793215+00:00 | retry |  |  | test:item_checklist:polished |  | 44b30d241ce43ea61971f8a781f388fc72f4516a7c7c9c558341464e9c554248 |  |
| 2026-11-24T06:47:59.251551+00:00 | retry |  |  | test:general_rubric:original |  | 71adf40cfb64120375145f843ce6bd3920aa2240232ed31363517a6d2ed121c6 |  |
| 2026-11-24T06:48:00.752026+00:00 | retry |  |  | test:general_rubric:original |  | 5fc3d14e73b114c1bbea16aeed946c8813410683c05bd0c819b49fb1f8c148ad |  |
| 2026-11-24T06:48:01.555473+00:00 | retry |  |  | test:own_requirements:original |  | bd5727e32ed285acae18802d926046f58a1da0988f211a4e21086c2cac641c34 |  |
| 2026-11-24T06:48:05.713757+00:00 | retry |  |  | test:general_rubric:original |  | e53f5b6f9e1e08d20617c7df53a8a0db39b58e5b0cc94c145768560643471ae9 |  |
| 2026-11-24T06:48:10.149623+00:00 | retry |  |  | test:own_requirements:original |  | 5f3dc64e1729737e773053a7ccbb509771aa66dc0648b4fdf13af3fc22358e28 |  |
| 2026-11-24T06:48:12.649738+00:00 | retry |  |  | test:general_rubric:original |  | 12228fd67c5d6aabe087033dfef7d75a052beabde8938258cd4e5d350b9fa0e1 |  |
| 2026-11-24T06:48:13.040408+00:00 | retry |  |  | test:separate_scoring:original:A |  | 865ba0cace3501ac3e0a69a2c6e75bf4533067567b4930ce467c33deac313950 |  |
| 2026-11-24T06:48:15.466383+00:00 | retry |  |  | test:item_checklist:original |  | 380f1e68f5260979be42f38367c8483e43e47dd70b7c53ac8ca082ce415cb3b8 |  |
| 2026-11-24T06:48:19.029737+00:00 | retry |  |  | test:own_requirements:original |  | a02c01857d4dc5ba0595f87ae3353b91935161fade8fcaf5c8dcb7438ffdac86 |  |
| 2026-11-24T06:48:21.147467+00:00 | retry |  |  | test:separate_scoring:original:A |  | 77b9583fb9e218d756ec2640dc68adba5941b5bbc3aca52bd7cb4c134b51bc9b |  |
| 2026-11-24T06:48:23.250879+00:00 | retry |  |  | test:exam_prompt:polished |  | a526ca055b776950bbd7b11ea5f469039d9f6df364ced575c5b41c7cb8d522da |  |
| 2026-11-24T06:48:24.402156+00:00 | retry |  |  | test:item_checklist:original |  | 5df7d3fdb89b61047aa402c8d9096465169a406f63631cde41dd97206e2f23c9 |  |
| 2026-11-24T06:48:26.380673+00:00 | retry |  |  | test:exam_prompt:polished |  | 7f5f680e69c5c20b669b48e1a2f3386665727deb3ad32d4ae104350c6fdcc9e4 |  |
| 2026-11-24T06:48:28.548572+00:00 | retry |  |  | test:exam_prompt:polished |  | b6f75359a8ae5ceeeb42722bcf066604af4028d1db719bb74a7dd703f053d1f5 |  |
| 2026-11-24T06:48:41.477163+00:00 | retry |  |  | test:separate_scoring:original:B |  | e112fe3d3c0674827da2f09191c1f8443890d45895efc12ec5b85096a0a3200b |  |
| 2026-11-24T06:48:50.259396+00:00 | retry |  |  | test:exam_prompt:polished |  | e31e38a727516cd2b71d21ec3cf7e6fa9ec6949ccda1d291ad8b532b346208ae |  |
| 2026-11-24T06:48:52.355257+00:00 | retry |  |  | test:general_rubric:original |  | b23dabb6979dce90209b3be3fe84b087a763fd0a48c97244e28314fbf95a2f5b |  |
| 2026-11-24T06:48:54.597034+00:00 | retry |  |  | test:item_checklist:original |  | ad9337a8704ff699db5431f17b96ad109fb112d29f306bdb255c398f7213a433 |  |
| 2026-11-24T06:48:56.610026+00:00 | retry |  |  | test:separate_scoring:original:B |  | 6e5864b2b5fc1135fba7ceb2aa83a579c222180aab05cc811aebd6ec7f54c73a |  |
| 2026-11-24T06:48:58.735287+00:00 | retry |  |  | test:item_checklist:original |  | ffced0d0482afe2462b595c83a419834fc05737fbb630908a3081961760a39de |  |
| 2026-11-24T06:49:00.785344+00:00 | retry |  |  | test:separate_scoring:original:A |  | 930c65a12860883ae919339491be3e158e94b0440a0cf585357dcd7b555bca8c |  |
| 2026-11-24T06:49:02.914401+00:00 | retry |  |  | test:exam_prompt:polished |  | 2c8098935c300d350d53dfcc208378b67f158ad272d6603382a985b7859e8a75 |  |
| 2026-11-24T06:49:04.864646+00:00 | retry |  |  | test:general_rubric:original |  | bce5a48539dc15e1ea60316b5cb7c9a616fad6c55fc6581a7e2a45946d0cda38 |  |
| 2026-11-24T06:49:07.038259+00:00 | retry |  |  | test:item_checklist:original |  | ed416f61defedb072f952d03b6471d535dff205ee5e75f3730b6c8b20ffd7293 |  |
| 2026-11-24T06:49:09.046345+00:00 | retry |  |  | test:item_checklist:original |  | 305b7617ee67a2ff2d8ce8a6daf1b76e245d043699d630a8d1c4902aaf9ccaf3 |  |
| 2026-11-24T06:49:13.462131+00:00 | retry |  |  | test:separate_scoring:original:A |  | b86e9028121b6e095741c8b1ed0500dce2a939ee11b57514846a222dc8cd6958 |  |
| 2026-11-24T06:49:28.729772+00:00 | retry |  |  | test:item_checklist:original |  | 17f34237d77b4b35cbdba2d23d1dbe897bb30c34fe6b980ee7029cbf8ecc05fb |  |
| 2026-11-24T06:49:55.519743+00:00 | retry |  |  | test:item_checklist:original |  | c972de7b05702e935b2f614338d806d5fb90ce7f091c9144118461d30e113828 |  |
| 2026-11-24T06:49:57.592691+00:00 | retry |  |  | test:item_checklist:original |  | 2ce2db805d3d208c79630c0db17131f4dad0c10d88dd67b5fe2df356289be7cd |  |
| 2026-11-24T06:49:59.659427+00:00 | retry |  |  | test:item_checklist:polished |  | 37b2d7a926bfd72c6dbd217d5fe5e7d46daf1a2bc9e5f57c323285a5040c8acc |  |
| 2026-11-24T06:49:59.991583+00:00 | retry |  |  | test:item_checklist:original |  | 7c7c2692b4bd1ddb19e90cf1c7f86f9e9d6ab825e6b2806f97cf771b59395193 |  |
| 2026-11-24T06:50:02.013623+00:00 | retry |  |  | test:item_checklist:original |  | a61f8bccf7040b6bfe6838f232f4dcf30dfc20cb9242a2c49e2e7a97fa20c789 |  |
| 2026-11-24T06:50:04.536890+00:00 | retry |  |  | test:item_checklist:original |  | 0144be2f1038b911002adf5fd5786316e17134e7440321cb09feb0edd4a1c352 |  |
| 2026-11-24T06:50:06.657799+00:00 | retry |  |  | test:item_checklist:original |  | 469efe76f81f2f0040d75c22e57f0476cbb214b390d5ae246179d1b308193889 |  |
| 2026-11-24T06:50:06.795197+00:00 | retry |  |  | test:item_checklist:polished |  | fcf7e63055e5c3b3af81a3ba57faa065f69b814a479b0d46a6b53ddb06f9ba39 |  |
| 2026-11-24T06:50:08.731902+00:00 | retry |  |  | test:item_checklist:original |  | c151f16898305b09237d8f817b76a4c6469addadc9ad6cc765bcd38e5df96df5 |  |
| 2026-11-24T06:50:10.851655+00:00 | retry |  |  | test:item_checklist:original |  | 73169f1caf249f118f2050162bda7bfd6f10255911c1bffaf607f05071bd583e |  |
| 2026-11-24T06:50:13.455014+00:00 | retry |  |  | test:free_form:original |  | c7c754aa2a9016bbc4cdb28d27bf3f6bc66dcc861452f8cc0869828f8196b77f |  |
| 2026-11-24T06:50:25.806512+00:00 | retry |  |  | test:free_form:original |  | c277f4c2d43ec9cbf6369d1ba0e2498e8d81937f6ae9a0f8402a35bdfbaa3b78 |  |
| 2026-11-24T06:50:31.610220+00:00 | retry |  |  | test:general_rubric:original |  | 41141042517ece947f7a0165d3b38329ab856a493cfa8a225ed84140851fb21e |  |
| 2026-11-24T06:50:32.499416+00:00 | retry |  |  | test:separate_scoring:original:A |  | 5dec79384ddbfe6c08b142e099871eb0fd0a6bdd7b7dc33175f9f55868ca6901 |  |
| 2026-11-24T06:50:34.488135+00:00 | retry |  |  | test:free_form:original |  | 9825bea61af0bac4f76df231e52c8b0384f779548163db6939fc48da88560db6 |  |
| 2026-11-24T06:50:36.758271+00:00 | retry |  |  | test:own_requirements:original |  | 19943f27f984c293de07e6b1f93b2f187ec7c76ea8d54a61a129a129e39ea8f6 |  |
| 2026-11-24T06:50:36.917282+00:00 | retry |  |  | test:free_form:polished |  | c3f1fbd671edd16a229bf5e9c6d7a9c3337a798505474b188973fca97cfac797 |  |
| 2026-11-24T06:50:38.561611+00:00 | retry |  |  | test:free_form:original |  | 9e70ae86beeaaf99ea871ae351e197456dd031d3a29ef9d0c6324b9d4f22e56a |  |
| 2026-11-24T06:50:39.668701+00:00 | retry |  |  | test:general_rubric:original |  | 359899ae7798f3e38229bfb3528a86831f7ea4a3d9405d172cdca1c97e2e0d4e |  |
| 2026-11-24T06:50:41.643110+00:00 | retry |  |  | test:separate_scoring:original:A |  | b4ba801bdb347a651deb843c9a04efa99f9c963d9e0f079a1ad905d3808f6d5d |  |
| 2026-11-24T06:50:42.239832+00:00 | retry |  |  | test:free_form:polished |  | 607b8affca4cbff12e0d7a9d56e23b3dbd0e36ef31149bf201d101876bbae3d9 |  |
| 2026-11-24T06:50:44.479618+00:00 | retry |  |  | test:free_form:original |  | 9898e4ac0412b848d145b0a39ca5d757970b61375066f187dc0c2e58fb690f78 |  |
| 2026-11-24T06:50:46.448837+00:00 | retry |  |  | test:free_form:polished |  | deea97a19d81e3a4bf960ebc9bc9713bf3a8bec48f7573833eac8714c60aa692 |  |
| 2026-11-24T06:50:48.705326+00:00 | retry |  |  | test:free_form:original |  | 4bd394767e54dd0c30d5a7fd4315fcf246e81d7f9a5835856a5ae54fd1e3b3e6 |  |
| 2026-11-24T06:50:53.957592+00:00 | retry |  |  | test:free_form:polished |  | 881e1b659d4716cea8ab461630ba2efb30f1a6c3b16dc5a69616bc25493a367c |  |
| 2026-11-24T06:50:56.317379+00:00 | retry |  |  | test:separate_scoring:original:A |  | d989a6173e6a26874bcd3915eccf0d17037803e1ffc5e416f684ed54fb62139e |  |
| 2026-11-24T06:50:58.285477+00:00 | retry |  |  | test:item_checklist:original |  | 0256b860e2d986e3c7b80dc2a59bc93c98aefb9881c61e45e7b64d8ea63e9820 |  |
| 2026-11-24T06:50:58.710121+00:00 | retry |  |  | test:separate_scoring:original:B |  | d3c23448a5b77e956ca7912724d349db97e549612f623a3eb107e8abb1d20575 |  |
| 2026-11-24T06:51:00.788637+00:00 | retry |  |  | test:separate_scoring:original:A |  | b6f4e238c308dd173acb59468c86f0f2afd981dae41a3e69478dd021b0a37971 |  |
| 2026-11-24T06:51:01.410244+00:00 | retry |  |  | test:free_form:original |  | 0b7d2a663653906ffa80940e03ac7acc0b76622e26276b3fa84073a80073739b |  |
| 2026-11-24T06:51:03.576959+00:00 | retry |  |  | test:separate_scoring:original:A |  | 9543b7afc2dce621425923c4deea2f5f3a39790326d86ab2f39deb27ee1dbf68 |  |
| 2026-11-24T06:51:07.486306+00:00 | retry |  |  | test:item_checklist:original |  | fe37d0f0d67cdbfdf7476123a3b136a36d53dcc8fddada9c5637a54f26d0b13c |  |
| 2026-11-24T06:51:07.572327+00:00 | retry |  |  | test:separate_scoring:original:B |  | 793617f1517e3cdb81f8ab94587e21f1548a60fd85dbfd67df9980b323e9c586 |  |
| 2026-11-24T06:51:09.451415+00:00 | retry |  |  | test:separate_scoring:original:A |  | d69338a7fb9dffc5197a7d8316bf861a2871f5e8a63a7d9223081b0dff508e1b |  |
| 2026-11-24T06:51:11.544215+00:00 | retry |  |  | test:separate_scoring:original:A |  | 52eddc1ca3ad3ef99de7085c975d89c49de2d3aefac9b347c6b6088ab481f69f |  |
| 2026-11-24T06:51:20.775955+00:00 | retry |  |  | test:general_rubric:original |  | b6c50fe5c463e7ccb5745333e2053e7481eb5bdea8825df4f941046c6271e047 |  |
| 2026-11-24T06:51:21.124473+00:00 | retry |  |  | test:separate_scoring:original:B |  | b4781576208d871ebcf2ca8ba7132640f8c98513ebf378d06f9a6bb92f4cf030 |  |
| 2026-11-24T06:51:22.879759+00:00 | retry |  |  | test:separate_scoring:original:A |  | c518c600ac92938cf3d6533b9967dd248d8e7b24074f1de3c61da138ed97c197 |  |
| 2026-11-24T06:52:30.488301+00:00 | retry |  |  | test:separate_scoring:original:A |  | 6b2d959f7908a8a4ed0242627289a427e421f29b91b44aa03cbb6ad18bb0006b |  |
| 2026-11-24T06:52:32.584575+00:00 | retry |  |  | test:general_rubric:original |  | 8e46f05c0fe98ed5345a51621d76e84137679466d70f21ead7087b8db0e89396 |  |
| 2026-11-24T06:52:38.999551+00:00 | retry |  |  | test:item_checklist:polished |  | 16772874ab9a41f206e1d4becebdc1638d5d80403f229d82a3d893b95b945b36 |  |
| 2026-11-24T06:52:40.976331+00:00 | retry |  |  | test:separate_scoring:original:A |  | 52c8ec68ac175217937b58e0918559beb9e560bc4e50c30ad0d691601fb2e0e2 |  |
| 2026-11-24T06:52:42.093831+00:00 | retry |  |  | test:separate_scoring:original:B |  | 1be25bf768a6e85b561f933954ba9c4eb5f54cf46a741e2b68c8f986f6e5f54a |  |
| 2026-11-24T06:52:42.977266+00:00 | retry |  |  | test:separate_scoring:original:A |  | 6e1b1bfc01254e505fec1972d1974961229e8e8d6b8edc02ceb2e6ec96fcc2b4 |  |
| 2026-11-24T06:52:44.151458+00:00 | retry |  |  | test:general_rubric:original |  | 267229083aeb031dc84652d65c0a36d4566e44737a6778b7f8be5100cfbaa173 |  |
| 2026-11-24T06:52:49.685544+00:00 | retry |  |  | test:item_checklist:polished |  | 49a14f478e064342d5f8c6622ee4d30dd2b173c8b756240d52891a5c59c77e19 |  |
| 2026-11-24T06:52:50.826987+00:00 | retry |  |  | test:separate_scoring:original:A |  | 5e8ef2e9d734de2a17e8a9df20d02c5b3809eb030b5168a8ab4b1866a150b04c |  |
| 2026-11-24T06:52:51.767815+00:00 | retry |  |  | test:separate_scoring:original:B |  | 3b82e29e498be6a58251a8c9196187af580a46c5f0efcb32990c5e74e11df4ca |  |
| 2026-11-24T06:52:52.966205+00:00 | retry |  |  | test:separate_scoring:original:A |  | f8d6a0db3881295380e6bdc2ca9ea964f779fbaa1f6664f36dd09d4cbf40642c |  |
| 2026-11-24T06:52:58.205967+00:00 | retry |  |  | test:separate_scoring:original:B |  | a39170225e6793af80f2584eb29ff5ac6a4458ecf40a264f8593d9529e9aa56d |  |
| 2026-11-24T06:53:00.409528+00:00 | retry |  |  | test:exam_prompt:polished |  | 26c4eb580f1e1b7c96223fb04c44e2ee6b40ea776e1085342a9d413fbdece07a |  |
| 2026-11-24T06:53:02.883639+00:00 | retry |  |  | test:separate_scoring:original:A |  | 4bbd3eb475ec0ce1290feac25c90f6a7e9172e2611690b71ba47d2717581b784 |  |
| 2026-11-24T06:53:04.906295+00:00 | retry |  |  | test:separate_scoring:original:B |  | bd585179e85714fedc23ff86c00706b806390c6cc66c84c95a1227807ccd477b |  |
| 2026-11-24T06:53:07.268685+00:00 | retry |  |  | test:item_checklist:original |  | d32178c9c4117ec99a413c60cc7160fbd5a1e5ed061baf3089534ee57018f571 |  |
| 2026-11-24T06:53:09.068737+00:00 | retry |  |  | test:separate_scoring:original:B |  | d2f11583292280fdf7b6164d0c122f7faec0ecca8be69b08428b80f9d94bb586 |  |
| 2026-11-24T06:53:11.091575+00:00 | retry |  |  | test:exam_prompt:polished |  | 90a222422d44f5a74058a23edb42e369dc623bb30f2438b3d2b11b68da79bac1 |  |
| 2026-11-24T06:53:12.590066+00:00 | retry |  |  | test:separate_scoring:original:B |  | 38f02019cc8e9c6881c77b7583508c6099bdddd4a3576b904a6e4af4cbf1e24d |  |
| 2026-11-24T06:53:15.328102+00:00 | retry |  |  | test:item_checklist:original |  | de3173c554a9af9ffb7a95614811345550e74fcddf55be8ae302cf057f99b4de |  |
| 2026-11-24T06:53:17.416054+00:00 | retry |  |  | test:separate_scoring:original:A |  | 9a78d16f5f3ec593c3b880482c99c18d971e3c82d87e03a8d2a5175e5bacdd78 |  |
| 2026-11-24T06:53:19.476523+00:00 | retry |  |  | test:separate_scoring:original:B |  | a458cd84ace6bf650eb48ec118ad3a21b9a289a3b0ab6376527c246df9316bdd |  |
| 2026-11-24T06:53:26.261883+00:00 | retry |  |  | test:separate_scoring:original:A |  | 04080cc6f043a550d4187f3f1206d1dbed990b93935b5395365e31bfa7796ced |  |
| 2026-11-24T06:54:27.761055+00:00 | retry |  |  | test:item_checklist:original |  | 26b895426917f303e82a775b654b1ba702d0ee7c9549e509f9190d1f294ec123 |  |
| 2026-11-24T06:54:34.504353+00:00 | retry |  |  | test:item_checklist:original |  | db33f0d9a4ac133d7bc54caad359f8a334c217cca4b9c2441afbf8ea79874c53 |  |
| 2026-11-24T06:54:37.113829+00:00 | retry |  |  | test:free_form:polished |  | 483d2a7532fc4474b42137916a01b8160c479a20aa3ee1f7b5ef85a20a0bc927 |  |
| 2026-11-24T06:54:41.369786+00:00 | retry |  |  | test:item_checklist:original |  | 1e21a8c64975dbf62eaeea04ed92fded2d659feee22b831f04841da2e2932134 |  |
| 2026-11-24T06:54:44.027977+00:00 | retry |  |  | test:separate_scoring:original:B |  | ee69ac358dd4c89f237fa42ac44a3bbf8b7167da03ae075ca100f2bff2c19aa4 |  |
| 2026-11-24T06:54:46.063524+00:00 | retry |  |  | test:item_checklist:original |  | 0e08016c203ca0fa68dd628ccdb58178b64e78ae6bc7087fcdc12ed8fe79034b |  |
| 2026-11-24T06:54:48.267273+00:00 | retry |  |  | test:free_form:polished |  | 9fddb0a23031be60c8246b874731f4a16fa1772f6e73a0cd53715af9f201ad91 |  |
| 2026-11-24T06:54:50.298289+00:00 | retry |  |  | test:item_checklist:original |  | 0f95c438a9f8b3d4e88a2d364f3a1181f3657318f6f9f9bb9022aabac863fdbb |  |
| 2026-11-24T06:54:52.033729+00:00 | retry |  |  | test:free_form:polished |  | 67d0e4371074435ca93860a5263578309a3d5be33d43cce33f5abb9bcbc5d065 |  |
| 2026-11-24T06:54:52.549690+00:00 | retry |  |  | test:separate_scoring:original:B |  | 061556cdc7ab09569de4adfd5b619d8f7caa0d6715b2d86f95fd307a15ccb11b |  |
| 2026-11-24T06:54:54.487192+00:00 | retry |  |  | test:separate_scoring:original:A |  | 71b69efb7a873299357a24c0f9dd411a4680f62fc90b1c74ca0c6dea4a0d07b8 |  |
| 2026-11-24T06:54:56.591836+00:00 | retry |  |  | test:item_checklist:original |  | 8a2aceb12df94364b612c33d274bbea2284491b998eb2812f5259d5406c57e98 |  |
| 2026-11-24T06:55:00.792994+00:00 | retry |  |  | test:free_form:polished |  | a67741d2203a0061997213004b1365ba2ca3ac000b46d90c635fb2c202250318 |  |
| 2026-11-24T06:55:02.989882+00:00 | retry |  |  | test:separate_scoring:original:A |  | afb1e98bdd72fa0cb96befcaab78d69f8c96a7cccebfe6c61af7d691d92ea3ab |  |
| 2026-11-24T06:55:03.103214+00:00 | retry |  |  | test:general_rubric:original |  | b8dcd13209d9a6340e0db9a23a9648da893b84ea2b9c808c58c4d2d2a5f314ab |  |
| 2026-11-24T06:55:07.357032+00:00 | retry |  |  | test:item_checklist:original |  | 05a298d41b75d1a7bdad45f40d946752c9fb45821149e486a38b35fe89fecbb9 |  |
| 2026-11-24T06:55:09.254469+00:00 | retry |  |  | test:general_rubric:original |  | 2b3c6bdc4adb355b6b7ad508503d16ff5a241ae833d790af1b27bb665e2fc835 |  |
| 2026-11-24T06:55:11.471470+00:00 | retry |  |  | test:item_checklist:polished |  | 348576bc715c0a076f443c30a5b4f1e6171ab927cf8c772ae23953ec5fe49204 |  |
| 2026-11-24T06:55:13.472594+00:00 | retry |  |  | test:item_checklist:original |  | 95477a989b0a56ed155c7cc2f40dda6fc1c8cab766b88a3a9c37f1fc3b8213c5 |  |
| 2026-11-24T06:55:15.635231+00:00 | retry |  |  | test:general_rubric:original |  | 80aad51832325d486f6953a51c1e0c5a6e9831b3d88f678b13595fccfc0f3668 |  |
| 2026-11-24T06:55:15.839175+00:00 | retry |  |  | test:separate_scoring:original:B |  | 0731c08bfd5b6e3108e849cace523f9bf59ebfe6a79937d9fa2185eee92ef804 |  |
| 2026-11-24T06:55:18.044521+00:00 | retry |  |  | test:item_checklist:polished |  | bcefd094ce6a6e497d19b20ecbdbf33f45565df9566e0c7d44f3aca25afa901f |  |
| 2026-11-24T06:55:22.030573+00:00 | retry |  |  | test:general_rubric:original |  | d3cbd6b2187cf2ae3ac49e698c7bf97acbb4f983d32e7f34e180a02c4fc9dffd |  |
| 2026-11-24T06:55:22.609715+00:00 | retry |  |  | test:separate_scoring:original:B |  | 4a501126398fe31a5e2d2f5e36a96f7e638c79b4064bde5ec799b8ddd73ec2a8 |  |
| 2026-11-24T06:55:23.803587+00:00 | retry |  |  | test:free_form:original |  | 21abfe572469f08241fbb701219715e13f3ea703331edb8dd3e8aeda7f3415e1 |  |
| 2026-11-24T06:55:54.742850+00:00 | retry |  |  | test:item_checklist:original |  | 4d7a2ee81c1ee05d7d16b434c82399a09a79fe2962e37c7fd7addccb5b816aec |  |
| 2026-11-24T06:56:02.485112+00:00 | retry |  |  | test:separate_scoring:original:A |  | e76d3ae05e4ca3ae234b0f66d8ccfcf29bb04b8730910d5374da2ffcdd5da5b0 |  |
| 2026-11-24T06:56:04.433628+00:00 | retry |  |  | test:general_rubric:original |  | 3924fe3fd134bbb63870084ef39e057a5d4297e581fb17821ee1c283e3cc5e5e |  |
| 2026-11-24T06:56:11.261120+00:00 | retry |  |  | test:separate_scoring:original:A |  | a909acda78f7f467ad07f04643d97b69887003e89c9c33f78100a2391068daae |  |
| 2026-11-24T06:56:13.284065+00:00 | retry |  |  | test:free_form:polished |  | 1d19a98f8cfce14df3e8247c39f354bfb08c9f64174171fbb1e460683c7b1c46 |  |
| 2026-11-24T06:56:15.406138+00:00 | retry |  |  | test:separate_scoring:original:A |  | 0d24fd33dd79afcd5955c03cd072097cfcd18b2601c1098386cbe67430244e70 |  |
| 2026-11-24T06:56:17.578030+00:00 | retry |  |  | test:general_rubric:original |  | 3b50e233f2f71598846209157a5fc07fd0dcc87bd9d5dbfcf9003cab2ae239bb |  |
| 2026-11-24T06:56:19.668493+00:00 | retry |  |  | test:separate_scoring:original:A |  | 448ca215cf116eaf3c6fe25a67d3d96786683c44c0e399343dab855cb44f6bff |  |
| 2026-11-24T06:56:21.727939+00:00 | retry |  |  | test:separate_scoring:original:A |  | c999924f3c8e769564b41b6ba5cc0980d6402e39d8e9b4e43781363faa466e8c |  |
| 2026-11-24T06:56:24.103791+00:00 | retry |  |  | test:free_form:polished |  | af7dd50468d64c645aa285542691b2b1139355d9a2532bbe5a0688d3d9bac376 |  |
| 2026-11-24T06:56:28.781447+00:00 | retry |  |  | test:separate_scoring:original:A |  | d5a815f253cc7501c88fa704d20549e6a5c11a432a783f80bcf95e302ac2f399 |  |
| 2026-11-24T06:56:29.790726+00:00 | retry |  |  | test:item_checklist:original |  | 7408ad2229d3672978a5d3c75043548383addac6bee523b7fdbba7c76b77c3e0 |  |
| 2026-11-24T06:57:12.967173+00:00 | retry |  |  | test:general_rubric:original |  | cf3d95cf183f9c1cb6bdfaa46efbc467e8c04108c93c4215d54aa2baabcce138 |  |
| 2026-11-24T06:57:22.506972+00:00 | retry |  |  | test:own_requirements:original |  | 846d68e56dbc63286ce91b738bda96528556e75c355d69a9f231e79499653eba |  |
| 2026-11-24T06:57:29.235782+00:00 | retry |  |  | test:separate_scoring:original:B |  | f6de1b5f585e3b64602c82dcfb59e2131fa6c5277f5f9a56f2e248e46ae5af8f |  |
| 2026-11-24T06:57:31.470592+00:00 | retry |  |  | test:general_rubric:original |  | 428a92b0e79cd6c0e9f8fa7d4b1a2d83cdf18aac71ae6ee4f06c9e0528540de2 |  |
| 2026-11-24T06:57:38.098127+00:00 | retry |  |  | test:own_requirements:original |  | fb8ccca64850a8e47686c327106318ba997b540dda0f8d86b9ca9d7586b9391e |  |
| 2026-11-24T06:57:38.643423+00:00 | retry |  |  | test:general_rubric:original |  | 78e6adfc14780c1f7620bfb4a3c4245481c79cb6c1d43d04cf3dc24da82569e4 |  |
| 2026-11-24T06:57:40.236824+00:00 | retry |  |  | test:separate_scoring:original:B |  | 414255c2134a153c5d6a02c0de3d2168519c5fe7d87d8f098394b2546b01f450 |  |
| 2026-11-24T06:57:44.667978+00:00 | retry |  |  | test:general_rubric:original |  | ff5f55e08a52653d1ef674f12734b6f5d1ca3465f0a913d6441957c7f3c08868 |  |
| 2026-11-24T06:57:47.007415+00:00 | retry |  |  | test:own_requirements:original |  | 3e0b5d7fba09e341026e625f3baf3713fd65280cc4af61699d1fcc5547f20ffa |  |
| 2026-11-24T06:57:51.253319+00:00 | retry |  |  | test:separate_scoring:original:A |  | c72019904a55922799ef27e62cd69c7317bd38ea7e253424e4c03458ef9fffea |  |
| 2026-11-24T06:57:52.123280+00:00 | retry |  |  | test:item_checklist:original |  | b73cce0d1a7722bf99ceb7987a7bb1267bf4ccdf943f344f17fe404577b079a7 |  |
| 2026-11-24T06:57:53.471152+00:00 | retry |  |  | test:own_requirements:original |  | 49c49c6591c1e121fd2b886a527fcac50539e94c5108759304b2ab42467a3884 |  |
| 2026-11-24T06:57:58.388766+00:00 | retry |  |  | test:separate_scoring:original:A |  | 923e3485d93f234ec067fb4afa96a47844a7933782d0c81a422e43f808b39632 |  |
| 2026-11-24T06:58:04.325320+00:00 | retry |  |  | test:item_checklist:original |  | 9fa869f3695caef09241f1258868f6ed2801dc2efda455b69ec30b7fac5fa370 |  |
| 2026-11-24T06:58:08.051813+00:00 | retry |  |  | test:general_rubric:original |  | d106d4833d7afae724f8a97a7b1091ba15d6bcc9f8c1b254c98f22f60f10c042 |  |
| 2026-11-24T06:58:08.594073+00:00 | retry |  |  | test:free_form:original |  | 57e2097f93e3c56f4dfc94c8804aaa30741ac1779f52745190cd8bffb94f2a81 |  |
| 2026-11-24T06:58:15.758010+00:00 | retry |  |  | test:item_checklist:original |  | b5e738be967138a76a73c5c26ab70910fd71c63806a720c04be15d9f478d5114 |  |
| 2026-11-24T06:58:18.935156+00:00 | retry |  |  | test:general_rubric:original |  | 91d8857b329a68fb645aa79100faede4e266f059edc2ac641fabe3b06756f376 |  |
| 2026-11-24T06:58:21.139904+00:00 | retry |  |  | test:separate_scoring:original:B |  | 725a04e224540431d7bf04c6594fbe28c134e2132049edc67c1791ab44247bae |  |
| 2026-11-24T06:58:23.175465+00:00 | retry |  |  | test:item_checklist:original |  | 3e411f6c4f55e1f5860ff37963e771b3def419f2664d7670e9c2a983c6c603a4 |  |
| 2026-11-24T06:58:25.217830+00:00 | retry |  |  | test:item_checklist:original |  | f62fa974214608114a21b2f3f280cfee26267d43776295084fb5e97528627cbc |  |
| 2026-11-24T06:58:27.342584+00:00 | retry |  |  | test:separate_scoring:original:B |  | 41e531d96690bb248d7b43d0d0cad7a08b2ec72701a54cdc10e2bbde8021c59d |  |
| 2026-11-24T06:58:31.801511+00:00 | retry |  |  | test:item_checklist:original |  | 15289e71d9379a353ffc6c65caa421c9a951555873a56bd0f8c68dadeb237252 |  |
| 2026-11-24T06:58:36.608278+00:00 | retry |  |  | test:separate_scoring:original:A |  | 0f048a16bf8f937305fadf208fa39e94dd87f8abdb8cf9c06d2993d97e45fb36 |  |
| 2026-11-24T06:58:49.572002+00:00 | retry |  |  | test:separate_scoring:original:A |  | 3cdf50906099a5e85a8ec9edf72b31b492cc9d2573c9124679ce51517519e2c7 |  |
| 2026-11-24T06:58:51.772759+00:00 | retry |  |  | test:item_checklist:polished |  | 601b6aa158ab269806ae4a6b0b6beeadf6e15326b6a0ea52cac699d7faf69e11 |  |
| 2026-11-24T06:58:54.069707+00:00 | retry |  |  | test:free_form:original |  | 0e5f4f67f8d1cc528dccff5535c66b1c6efd26f2b192c417b528af39f4a1ae3d |  |
| 2026-11-24T06:58:56.226466+00:00 | retry |  |  | test:separate_scoring:original:A |  | de4d026ae372ac994f6360625f009333601348d1d1c8d130497697c8b45824fc |  |
| 2026-11-24T06:58:58.451142+00:00 | retry |  |  | test:item_checklist:polished |  | 7dad17c34cadcbb69ab8dc05c9925e27bf853b7d9976a55cea69e201280e287a |  |
| 2026-11-24T06:59:00.554123+00:00 | retry |  |  | test:free_form:original |  | 1af6fe5a424eddaca2d4d297ef11050753402297e0056b5e18bf96d688fad0f3 |  |
| 2026-11-24T06:59:00.834271+00:00 | retry |  |  | test:free_form:original |  | 5c959c588eacecce9e75d61d05795e18c97a62dd845b1f157404738f83ec4a33 |  |
| 2026-11-24T06:59:13.362479+00:00 | retry |  |  | test:separate_scoring:original:B |  | 4ff09d7446b225fa86c75171c1f2fdb4cd85c2590fd2a8431095c468f2be61c6 |  |
| 2026-11-24T06:59:17.112880+00:00 | retry |  |  | test:free_form:polished |  | b9445d9dbf22086f0e6a0920a222163ef9c99fa341103db5b89039fa9f8027fe |  |
| 2026-11-24T06:59:19.517402+00:00 | retry |  |  | test:separate_scoring:original:A |  | 7c7d3f2e80f3dec5790941883b883c520f4e321f266d617e9e4842265ecdda9a |  |
| 2026-11-24T06:59:22.136762+00:00 | retry |  |  | test:separate_scoring:original:B |  | 348abcba9281e052287d85d2ce82d97f0eaa3a79017f686e314c8439cb5b1e96 |  |
| 2026-11-24T06:59:25.219314+00:00 | retry |  |  | test:free_form:polished |  | cba8d4fce7b958655e90db792d6d2ac83dd5bdd5d7091b400252d6f404c744aa |  |
| 2026-11-24T06:59:27.584892+00:00 | retry |  |  | test:separate_scoring:original:A |  | cc15fe8b0f8a8938f24a7b6daae6b63e7ca6eec56c086cf02c85d8a581347cce |  |
| 2026-11-24T06:59:37.258360+00:00 | retry |  |  | test:free_form:original |  | 274df809b81b616a7dfcb06513fdc7d6d3552e3948f93a8510c0ced5c4b9fa4f |  |
| 2026-11-24T06:59:53.012089+00:00 | retry |  |  | test:free_form:original |  | 7c892ea5de12489c9d0e4b66bf9f8734e762e1fb669ac4ce9fcac0f86761eab6 |  |
| 2026-11-24T06:59:55.280446+00:00 | retry |  |  | test:separate_scoring:original:A |  | 677d1be65aee14fa14faa210016771b46176889859a7a9e6d3bc257248c625a3 |  |
| 2026-11-24T06:59:57.364615+00:00 | retry |  |  | test:separate_scoring:original:B |  | 0539ae3599b4ad6bc298b63c0100fbd3a947bc56389d367c8c228d7baaf116ed |  |
| 2026-11-24T06:59:59.640716+00:00 | retry |  |  | test:separate_scoring:original:A |  | 87cdd24d10d28803b11256c23d9547610859e30b3939a798ae9d1fa35af91050 |  |
| 2026-11-24T07:00:04.205426+00:00 | retry |  |  | test:separate_scoring:original:A |  | 502a885cefd638302aa3303259cd1aaeea615e9251f7d255b1413f68d63ecf52 |  |
| 2026-11-24T07:00:06.741751+00:00 | retry |  |  | test:separate_scoring:original:B |  | c9106d9acbf17ce18b94dbc1ce0b3dfc199126b532de261a3580928f66a60076 |  |
| 2026-11-24T07:00:08.543402+00:00 | retry |  |  | test:separate_scoring:original:A |  | 012f3b2c02a702cdda59b1791b5c41d69a222f8a4ef309dd81b412316149b265 |  |
| 2026-11-24T07:00:08.947410+00:00 | retry |  |  | test:separate_scoring:original:A |  | f8a0a1d97d168fc0fe1f1ae90d5c7c43bc28b99fa2711b6e0fe554ff1aa65717 |  |
| 2026-11-24T07:00:11.023452+00:00 | retry |  |  | test:item_checklist:polished |  | 89cbf7ceb04204bb9dd941aee874fd47004b0e79cc97d0af01bfc95964989059 |  |
| 2026-11-24T07:00:15.157734+00:00 | retry |  |  | test:separate_scoring:original:A |  | 69d13c9a279223fb43af42e0588829d400e9c1f6ad329618ff8e78d74878a987 |  |
| 2026-11-24T07:00:18.102379+00:00 | retry |  |  | test:separate_scoring:original:B |  | 07e1115c377902337b68b323f3114889236c8e7a35b15db91cea2544a200390c |  |
| 2026-11-24T07:00:19.458070+00:00 | retry |  |  | test:item_checklist:polished |  | 81113e67126b87e4c7a56b766fe74a835e80768fdda74fa6e0c00ac17e911de7 |  |
| 2026-11-24T07:00:21.495451+00:00 | retry |  |  | test:general_rubric:original |  | cd8272dcb3aa923b60de891f36ffdc23fcd334570caed599297f776884e32c21 |  |
| 2026-11-24T07:00:23.574009+00:00 | retry |  |  | test:separate_scoring:original:B |  | a5ca785ea6af65080205bccf68764a16fd683434a91b4504de0a61a5b041be1d |  |
| 2026-11-24T07:00:23.975991+00:00 | retry |  |  | test:separate_scoring:original:A |  | d4135343c997c88458e0788a63d654ec360afb9bdb738bd484365c618790fb62 |  |
| 2026-11-24T07:00:25.621132+00:00 | retry |  |  | test:separate_scoring:original:B |  | 03fd0cbb533f5258e1fcfa1a1a42a6501a91c07175506f575556eaad21f0ce85 |  |
| 2026-11-24T07:00:29.786969+00:00 | retry |  |  | test:general_rubric:original |  | 1a22bcc27048283c8f7f2494eff718a2dc7571ae23839de9472f825343d2e5f9 |  |
| 2026-11-24T07:00:34.726301+00:00 | retry |  |  | test:separate_scoring:original:B |  | 725b73afea1aa0cdd07d1e94d56fa8b56893684951e660c12d72eb1691582190 |  |
| 2026-11-24T07:00:38.350325+00:00 | retry |  |  | test:separate_scoring:original:B |  | 642be5bb91fc50660cc0b36aee3c428970ee0005ecf82d9cc727758e5b8e1715 |  |
| 2026-11-24T07:00:40.225569+00:00 | retry |  |  | test:item_checklist:original |  | 6be7561bb2a7fb109a01b0791d5eae62e08a35dba46c356e623fac89f76d7fa0 |  |
| 2026-11-24T07:00:50.166795+00:00 | retry |  |  | test:separate_scoring:original:B |  | 63766f07d862abfd02aaaeeb484beaab45ae5ab3ed241cd1acc1e14ea25fcb3c |  |
| 2026-11-24T07:00:52.281371+00:00 | retry |  |  | test:item_checklist:original |  | d27412dffb57672f882aa6db8d4e9ae93692cbc29c47287d536d906c570fc394 |  |
| 2026-11-24T07:01:09.145001+00:00 | retry |  |  | test:free_form:original |  | cd0629c4dbe136182ceff11449ef3cab55ad864e28a58636228614e88cac5a3e |  |
| 2026-11-24T07:01:11.243919+00:00 | retry |  |  | test:separate_scoring:original:A |  | 6eca78f4481e327f02d111cc1d2c048d659f00686ae90c5c951cca86c9c7ad27 |  |
| 2026-11-24T07:01:18.056943+00:00 | retry |  |  | test:free_form:original |  | 9c9e660ce668423faf66099082d1eb28187f5361ce726305fe0db18571ede066 |  |
| 2026-11-24T07:01:20.449012+00:00 | retry |  |  | test:separate_scoring:original:A |  | 2abf89f4bdd1e42187d93c67a8560fdbf233a454d592f27f1f9a3f05926a42bb |  |
| 2026-11-24T07:01:22.524702+00:00 | retry |  |  | test:own_requirements:original |  | fad205fc89417186891b561b39d58d3f7e34724ece65d37f6f42906b3ea786b0 |  |
| 2026-11-24T07:01:23.241140+00:00 | retry |  |  | test:separate_scoring:original:A |  | 25c980597e6bc1ed41d1d44ca842f479d900da211bf58d3e02784a08668ca6a7 |  |
| 2026-11-24T07:01:25.427626+00:00 | retry |  |  | test:separate_scoring:original:A |  | f4b5b923490f455d684f695c87188647a8730f58490d9688631308ef0293c1cd |  |
| 2026-11-24T07:01:29.857112+00:00 | retry |  |  | test:separate_scoring:original:A |  | 49f26e48636165560a7797cb9715b1057d9d2e3fe687acb501a66b437c67bc4c |  |
| 2026-11-24T07:02:33.015937+00:00 | retry |  |  | test:separate_scoring:original:B |  | 27eb3849d59004b6b5c4456d2dc1cc2becb8354da9e157f159bfc4af9f55bc59 |  |
| 2026-11-24T07:02:35.205366+00:00 | retry |  |  | test:separate_scoring:original:B |  | c63b73fd172efea2b930e8f8ba05c4c7efa0923cd10276b2999dadaf1a3512a0 |  |
| 2026-11-24T07:02:41.838928+00:00 | retry |  |  | test:separate_scoring:original:B |  | 159396974e17f5745b28c79d00eedc856af57b2691d8cb770d56fad994a0c80b |  |
| 2026-11-24T07:02:48.501122+00:00 | retry |  |  | test:separate_scoring:original:A |  | f767d667e9b94754efb9edf25f300208886defba2c364c3a4a6fee1a9d277ca2 |  |
| 2026-11-24T07:02:50.665248+00:00 | retry |  |  | test:separate_scoring:original:B |  | d6fa278d4e9b989ada3c3f55df1cec0e48a337df4e0fd65147643f56d3158338 |  |
| 2026-11-24T07:02:52.816170+00:00 | retry |  |  | test:separate_scoring:original:B |  | e20ce30b538845026bac3b9ba0e42e828b796bf5a053aa91529e2b6fa78d7079 |  |
| 2026-11-24T07:02:54.805327+00:00 | retry |  |  | test:separate_scoring:original:B |  | 88550aa449c48711aec9b0800109f6272f2428e498568dcd3dcfa3252645a3ca |  |
| 2026-11-24T07:02:54.861376+00:00 | retry |  |  | test:own_requirements:original |  | bce0e22760885fb0d9adaf1e1d775ff7543f04bf8d9439758acb1e17edf14b8d |  |
| 2026-11-24T07:02:56.850780+00:00 | retry |  |  | test:general_rubric:original |  | bcff3a3a205486779c5e50660a05b52cdefd7537290ab5f5f624b5cddc17cad0 |  |
| 2026-11-24T07:02:56.926242+00:00 | retry |  |  | test:separate_scoring:original:A |  | 4987a39da3fdb1d5c6226960687210a4f843906a84db4f2bde28212917df4a02 |  |
| 2026-11-24T07:03:00.069309+00:00 | retry |  |  | test:own_requirements:original |  | de4df876439a9c795d3ed3e9da3056784ae442675dfa4cb001926e684a5f4afd |  |
| 2026-11-24T07:03:02.041986+00:00 | retry |  |  | test:general_rubric:original |  | bddec64830e7982c72c6665f50366fc5aaf6151d279ec89220751eac82069609 |  |
| 2026-11-24T07:03:02.808995+00:00 | retry |  |  | test:general_rubric:original |  | 2d593fc96d28adf18f711be5e66485555da04fbba15b109a5d789c3c8b6b4ba9 |  |
| 2026-11-24T07:03:09.453907+00:00 | retry |  |  | test:separate_scoring:original:A |  | 67ccc06ebb7bf7362e00d1b715258e0ec630d1d4da00bf1ee7b3dafcb3061755 |  |
| 2026-11-24T07:03:11.766999+00:00 | retry |  |  | test:general_rubric:original |  | e9d8a3fbf0833ad50cd6e8c7ff1654e85130f02a67d4af400fd8567c5760e643 |  |
| 2026-11-24T07:03:15.883242+00:00 | retry |  |  | test:separate_scoring:original:B |  | 6b597a4d34d1f2b9c57d2169acd84b8f0a26b4938dd86bd3e004bbb7f1c525dc |  |
| 2026-11-24T07:03:17.983172+00:00 | retry |  |  | test:free_form:polished |  | 47c2fde363382709df3ce12358ab031bdd58aa3c964d97fae9eff76d2e0777fc |  |
| 2026-11-24T07:03:18.889029+00:00 | retry |  |  | test:separate_scoring:original:A |  | 077f09a661a5047f05df735db9f5a6ab6e850a264da4a8d910a7a83e809036c9 |  |
| 2026-11-24T07:03:20.990682+00:00 | retry |  |  | test:separate_scoring:original:A |  | 40df3ac29579879372dfbf186b6ce5c240457815f5ca1863b7d22cbb0a52dead |  |
| 2026-11-24T07:03:25.225718+00:00 | retry |  |  | test:separate_scoring:original:B |  | f7c0a8d3610ce66dd3b9f9c9a16b75d722da848a99fef5aa047fabe68c8b463d |  |
| 2026-11-24T07:03:26.087476+00:00 | retry |  |  | test:free_form:polished |  | b7d1b9778ed5fd32b1713d5b45e73f6bcfa24c6a2adae4f87d109329aa4c7e8f |  |
| 2026-11-24T07:03:27.233418+00:00 | retry |  |  | test:separate_scoring:original:A |  | a780a3ac95f7b3954759aab66e4f1f43dca51d6c16dd0b08e7ba416b5e28e830 |  |
| 2026-11-24T07:03:28.283429+00:00 | retry |  |  | test:free_form:original |  | 268c57d0cb21e19e2213b653e9801e22f60a85bcd220b3371ab576e085c47cb5 |  |
| 2026-11-24T07:03:30.645895+00:00 | retry |  |  | test:separate_scoring:original:A |  | 981b95a3f782feca18ec6074512f7c40473a6b7a758105f85b5ea2ccdde449f3 |  |
| 2026-11-24T07:03:33.106847+00:00 | retry |  |  | test:separate_scoring:original:A |  | 4701fded21c6662487c60a1f508440c38c75b281b4363970ec83e1202f1f1467 |  |
| 2026-11-24T07:03:38.311162+00:00 | retry |  |  | test:free_form:original |  | d44ccba3fcdaba61963aa1c6f1bbad4670d55f2c3233b591552f1eb85a82396e |  |
| 2026-11-24T07:03:44.853678+00:00 | retry |  |  | test:free_form:original |  | a5a9df7bc83e00e5421c6f7d4a3318dfb774cfc9bc2e17bffd1ce1d9c9f3de75 |  |
| 2026-11-24T07:04:32.957161+00:00 | retry |  |  | test:separate_scoring:original:B |  | 5f671254865dbe3412690234fe054b35fe4896369a7afa018026550c7c7f7a02 |  |
| 2026-11-24T07:04:34.578080+00:00 | retry |  |  | test:free_form:original |  | f2da0b9bf020e3512406a78ca4cfa69e27791049b25ce3bf2b0ebdd0fc10ab72 |  |
| 2026-11-24T07:04:36.798680+00:00 | retry |  |  | test:separate_scoring:original:B |  | 5a058a86cd469af9bba4567bd21f65bcd088155789fae0f0f5e094a9e4e14738 |  |
| 2026-11-24T07:04:38.947071+00:00 | retry |  |  | test:separate_scoring:original:B |  | c381c97221e3e9a2468060fef7b692847ea5fecf272ba6ebd65959aab5ce167b |  |
| 2026-11-24T07:04:39.152084+00:00 | retry |  |  | test:item_checklist:original |  | 5088f04ea61df392f1ba99beded50604a67868f9020daed370f5fa4e9b548914 |  |
| 2026-11-24T07:04:41.695368+00:00 | retry |  |  | test:separate_scoring:original:B |  | 1dd319210830318383f2a62300ef094b700370b616dc018d33c44bfc654526ba |  |
| 2026-11-24T07:04:41.834818+00:00 | retry |  |  | test:separate_scoring:original:A |  | b08781513816041b343981b6d7c92877801f31aea067780b765a2e0cf73cbfef |  |
| 2026-11-24T07:04:42.083785+00:00 | retry |  |  | test:free_form:original |  | 57947cbcee24a738b560bcce572ce44cd3ee57f42237135fd88ad3d71cffaeb2 |  |
| 2026-11-24T07:04:44.177280+00:00 | retry |  |  | test:item_checklist:original |  | 3c77128c6906aa57f6637f884df7a6bdea01030f131be9465e9698eb3387c253 |  |
| 2026-11-24T07:04:47.780252+00:00 | retry |  |  | test:general_rubric:original |  | 03bd2b0c618e5bf3d6d23857cf4fc795ed1200f43fdba370e93213fd08927c3c |  |
| 2026-11-24T07:04:48.737765+00:00 | retry |  |  | test:free_form:original |  | a913cea2a8f6eeae6021bdb31a7285c81a7c8c3bd7baf2cd3e66347deb81b519 |  |
| 2026-11-24T07:05:05.149598+00:00 | retry |  |  | test:separate_scoring:original:A |  | 684e8c46d2d720b6413880ddea229c36f4289acc6d34fde62ac2dd90d92dcc8d |  |
| 2026-11-24T07:05:07.610091+00:00 | retry |  |  | test:free_form:original |  | 6361956b66cab8ac9ac8dfd477305772078ebcbc35d168ce27864a6585949b14 |  |
| 2026-11-24T07:05:10.496028+00:00 | retry |  |  | test:separate_scoring:original:A |  | 17361ad3539f34c0c1de0b8feea55ee59389c2052b732c6b0b8dd433cdad3f18 |  |
| 2026-11-24T07:05:12.683107+00:00 | retry |  |  | test:free_form:original |  | f499a459eae139b34c60bec213d08a8d0e9a3571cf8c2146566f738c64cae0a8 |  |
| 2026-11-24T07:05:14.602666+00:00 | retry |  |  | test:separate_scoring:original:B |  | 19d48d4f1ebdfad3b1cbf191a52097704049c32961f977f299ffb8ba4f9ccd4e |  |
| 2026-11-24T07:05:17.784836+00:00 | retry |  |  | test:separate_scoring:original:A |  | 4905286ea186f6264a1ef889b93c07223a7c139cb3429114a8c45ce2d6bd76ce |  |
| 2026-11-24T07:05:20.984396+00:00 | retry |  |  | test:separate_scoring:original:B |  | 298d5d41f260d1a26043aafe7c20c0f9dcaabf5cc7b47f4d4c2e9b22d3eff60a |  |
| 2026-11-24T07:05:22.210352+00:00 | retry |  |  | test:item_checklist:original |  | fc9c369216a3c638681aa5f573516e4e49d5755169a7b71029d6b49c7aa48d28 |  |
| 2026-11-24T07:05:23.562139+00:00 | retry |  |  | test:general_rubric:original |  | b55f5bf48bba2a311983248dbeb0213fffb73f2948acd80b9b53f33ac15f3b88 |  |
| 2026-11-24T07:05:24.477221+00:00 | retry |  |  | test:separate_scoring:original:A |  | daa40adbe3497e4b8dee6232ff8aeca825655ba8a6330303b597d783acc55a07 |  |
| 2026-11-24T07:05:26.020232+00:00 | retry |  |  | test:separate_scoring:original:B |  | 8abe79b57eb9e1085fdd2c2488a82c52a6ad9df618e53124bde68b9611f08697 |  |
| 2026-11-24T07:05:27.521502+00:00 | retry |  |  | test:item_checklist:original |  | 3dc42ee4fcf7c0d5607c968901ab2e2488b677efe442df6bb186526d6b689a04 |  |
| 2026-11-24T07:05:29.197880+00:00 | retry |  |  | test:separate_scoring:original:A |  | 323c7127fd6ad0bdd05a5d5f0ea9b341d0d02c0867ad42fcfbeec95910ef1e52 |  |
| 2026-11-24T07:05:29.580092+00:00 | retry |  |  | test:separate_scoring:original:A |  | 4d98f09d4f43199d04092da1fc474d94345c4e31b4af0f22c51d4c9347c3c292 |  |
| 2026-11-24T07:05:34.268618+00:00 | retry |  |  | test:separate_scoring:original:A |  | 3fda5e5add283797782c29c4dbb00fc176106063ff797e5c2ab6da88dbfa9d30 |  |
| 2026-11-24T07:05:39.670713+00:00 | retry |  |  | test:separate_scoring:original:B |  | 22798b967c87f1b5c71e63cda88ea1f5d1078cdad2beda2e80e5c46796b4faf3 |  |
| 2026-11-24T07:05:41.259703+00:00 | retry |  |  | test:separate_scoring:original:A |  | 34979f272df49e4a80b6103807993044ca1efab358558631a40877a9d7108e14 |  |
| 2026-11-24T07:05:44.411198+00:00 | retry |  |  | test:separate_scoring:original:B |  | 16b69e8a5357c507e628e07e42528c8901dd6c1558f0939b6f23fe9bea85dc5f |  |
| 2026-11-24T07:05:46.730524+00:00 | retry |  |  | test:separate_scoring:original:B |  | 506e3ee89f2a093c07ec2a83983dc41e1a2ff44b5ca59f1bd2fdd17d6616e7da |  |
| 2026-11-24T07:05:49.931412+00:00 | retry |  |  | test:separate_scoring:original:B |  | d2c33cc4d8e4b82461bae261d0560a38d69b010036227cb52f23947f206f2a59 |  |
| 2026-11-24T07:06:07.939051+00:00 | retry |  |  | test:general_rubric:original |  | 0c1900dc906847676a92037092b7473c318a99bad03c0c296c5d6bf4b3976e28 |  |
| 2026-11-24T07:06:13.889005+00:00 | retry |  |  | test:general_rubric:original |  | 5d8d12457d0adbaf4d0a8b86b9225377e1c0e5a1dc5883e0490fd73a3ec8ede7 |  |
| 2026-11-24T07:06:19.850282+00:00 | retry |  |  | test:separate_scoring:original:A |  | f678f1bc5acb453228449601b69d10539720645ffb211970507322526d77495b |  |
| 2026-11-24T07:06:23.314251+00:00 | retry |  |  | test:separate_scoring:original:A |  | e55aa1bbb1f55bdb7316228c14da88619560cae31be80183e2f2c3ced0a5dbab |  |
| 2026-11-24T07:06:26.507283+00:00 | retry |  |  | test:free_form:original |  | e9148d5ddc0ce03df08ebce66029b58428fc204272db431dbb996857ff6ffdb0 |  |
| 2026-11-24T07:06:28.551325+00:00 | retry |  |  | test:free_form:original |  | 1241896b84977fbaca4391d41f0182bcce6e6872badf3aaa0d50b688767e102a |  |
| 2026-11-24T07:06:34.647726+00:00 | retry |  |  | test:free_form:original |  | 0afbfab30d56cd9c59ed1f55a63a55e7cf373e04065e88ddfb7b505c11700c11 |  |
| 2026-11-24T07:06:35.209847+00:00 | retry |  |  | test:free_form:original |  | 4594438759c48f9d3524083427f306957d716b84a644a1710e0871983f480ac5 |  |
| 2026-11-24T07:06:42.598123+00:00 | retry |  |  | test:general_rubric:original |  | 2f2e371278ba1b9734689c7c9e088d1e899a952a22d3a9d7223f407324cecd90 |  |
| 2026-11-24T07:06:47.601640+00:00 | retry |  |  | test:item_checklist:original |  | 23727b257a858e5258e6324a3028083e3f5707dca4166a5fce3f15e38ed9e458 |  |
| 2026-11-24T07:06:51.670325+00:00 | retry |  |  | test:exam_prompt:polished |  | 7d7e487ef44de20aae38342ef8620be017fdb7fb3c83acf29a512afebfafa502 |  |
| 2026-11-24T07:06:53.617703+00:00 | retry |  |  | test:general_rubric:original |  | 054f7eb477727721c0a5bf8e1637eebce79cb9b10515b77039b8702d031f7e7c |  |
| 2026-11-24T07:06:53.911595+00:00 | retry |  |  | test:item_checklist:original |  | f67444127901380f8a92e7d967cc36ca03f458064f96cfe565523d47566c63f7 |  |
| 2026-11-24T07:06:55.813794+00:00 | retry |  |  | test:free_form:original |  | 1e2bad5e0a599c14568d65d9e54c16e78104ff9f7e7930c7095eaa68698faff5 |  |
| 2026-11-24T07:06:56.797893+00:00 | retry |  |  | test:exam_prompt:polished |  | 69928fae94a0d8baffa6be9bae1c51985e1e9e1fd9c76e90c3c81e14287cb1ff |  |
| 2026-11-24T07:06:59.449955+00:00 | retry |  |  | test:item_checklist:original |  | 5bfa80df500881a5d5a6806c1cd1f9da6778cd8d1437b8e52b6cd1e9026ca316 |  |
| 2026-11-24T07:06:59.939989+00:00 | retry |  |  | test:separate_scoring:original:B |  | 669dab9e33394dbb5d381f2269fa8158736e66b5dc77f8e97137968d24513e0a |  |
| 2026-11-24T07:07:00.882465+00:00 | retry |  |  | test:free_form:original |  | 69031c7653c8a666867b726b76c871d896994b63e474b468ecd96edd98367487 |  |
| 2026-11-24T07:07:01.048983+00:00 | retry |  |  | test:separate_scoring:original:A |  | 002a6f183fbc13df576fad7feb25fb3f86aa8373c32fb6cce7d42cf508ee3db2 |  |
| 2026-11-24T07:07:04.842040+00:00 | retry |  |  | test:item_checklist:original |  | eb2a5b59772e4ed027db5ec2a96639c42983d7862b5197e2b8ad5428de6bd5c8 |  |
| 2026-11-24T07:07:05.654093+00:00 | retry |  |  | test:item_checklist:original |  | 9fa8f9392c7355b00bc488e1734d1c55c5670ab7538cbd9e49dcbc5506020dad |  |
| 2026-11-24T07:07:09.379189+00:00 | retry |  |  | test:exam_prompt:polished |  | 5f2e01220436049b85daeed71cdd4cb01ff009d28750026df47dd061e357c4e2 |  |
| 2026-11-24T07:07:11.087023+00:00 | retry |  |  | test:item_checklist:original |  | d8f48178036933c7f65bc829eeeb9dcb51c6458a810fdbf2b279a799984fa1cf |  |
| 2026-11-24T07:07:14.444642+00:00 | retry |  |  | test:exam_prompt:polished |  | 86ab7eac081749dc153778b07a6d2271a12b8e02d3f7f1b1271ddd5a822bced6 |  |
| 2026-11-24T07:07:18.914681+00:00 | retry |  |  | test:general_rubric:original |  | 84adbde1f9989e2d0d59cd8cc7003db5e79966096993d9d1598159cad5f7d1e9 |  |
| 2026-11-24T07:07:28.375175+00:00 | retry |  |  | test:free_form:original |  | 82825a6e12c0f382752c88f1692ef1d54c1bb43f334b9928d3b968bd32b50798 |  |
| 2026-11-24T07:07:32.580270+00:00 | retry |  |  | test:separate_scoring:original:B |  | 3e4afa10ff92c9bd3c4642c70c45cf97528a71869e992d485071d87794ef2e62 |  |
| 2026-11-24T07:07:33.379571+00:00 | retry |  |  | test:free_form:original |  | 6bac8544de6d4c2f924b592a1b8ea54e4b31b38dfb53b031ac8314c15e947b96 |  |
| 2026-11-24T07:07:38.793296+00:00 | retry |  |  | test:separate_scoring:original:A |  | e7d98312d735c28a0800f519e235feab56784e223ed63d077ab7122965a2b1b6 |  |
| 2026-11-24T07:07:43.837145+00:00 | retry |  |  | test:separate_scoring:original:A |  | b54fada42041e5db8e1d2f151c1768fa3d2203185e24608ecd1a02976332718c |  |
| 2026-11-24T07:07:54.455522+00:00 | retry |  |  | test:separate_scoring:original:B |  | 481e74640729150f6de69b970a6c878b1e8eae059c23e267418d01ccd03917af |  |
| 2026-11-24T07:07:56.729061+00:00 | retry |  |  | test:separate_scoring:original:A |  | b94bb1191616da061b99e426405041102832566bd0527ab1df37f8dafd4d49ad |  |
| 2026-11-24T07:07:59.487822+00:00 | retry |  |  | test:separate_scoring:original:B |  | 9a969be0ab612ba9a1e0926d2f7add2a3ef6769eb06d44517a66ce8a988719a9 |  |
| 2026-11-24T07:08:16.574346+00:00 | retry |  |  | test:separate_scoring:original:B |  | e7dc032fb1b638b77ba771e9b4eb40f431a76c30970f924fc91fa7c0aec70104 |  |
| 2026-11-24T07:08:20.144431+00:00 | retry |  |  | test:general_rubric:original |  | 0af5ecc50d82f2815623810cf716d3c9c498920b2e74237a6bfdab7cab27c387 |  |
| 2026-11-24T07:08:22.165524+00:00 | retry |  |  | test:free_form:polished |  | 3e5195f2d6445e58bb3ac4aeb4c5c2df163d5abaef693586e38e09450a02498d |  |
| 2026-11-24T07:08:23.295030+00:00 | retry |  |  | test:item_checklist:original |  | 208e3d8f4dcf7c71ba5a89f602d516173103c758ace17cea1a5c4588ff65084c |  |
| 2026-11-24T07:08:25.241323+00:00 | retry |  |  | test:general_rubric:original |  | 1900af7cdb80773278d15696ce917f7be624ff24be7048b7e5316954c68e35f9 |  |
| 2026-11-24T07:08:27.101748+00:00 | retry |  |  | test:free_form:polished |  | 034bc8399b48ecc92dc32ad19f5537fcf0782139b939bff6c9ddfd1b0285e21b |  |
| 2026-11-24T07:08:30.687436+00:00 | retry |  |  | test:general_rubric:original |  | 7d1d1f43f1802fc6cfcde1d22552c6edab90228d04153566bc4f902c4c0c9373 |  |
| 2026-11-24T07:08:32.842273+00:00 | retry |  |  | test:free_form:polished |  | 477fe0da4e63bbfe2a56eb0deb406af9690831cfcbe495e4190ade671aa5b991 |  |
| 2026-11-24T07:08:35.985027+00:00 | retry |  |  | test:general_rubric:original |  | 572c3a90c1912c6f22f51699bd091c2ceeacdbf6611a9d70f05fc3344de5d1ba |  |
| 2026-11-24T07:08:38.139037+00:00 | retry |  |  | test:item_checklist:polished |  | c907198d9d3d859dfa5c043c51279ef64b63f8671a42df1bfd8f183e5b347f93 |  |
| 2026-11-24T07:08:38.493305+00:00 | retry |  |  | test:free_form:polished |  | 8d0b29bf958265b898dbfd3bcd1d4b9c7bff54e41ac3fa0e5e8a84dedd782daf |  |
| 2026-11-24T07:08:41.124651+00:00 | retry |  |  | test:item_checklist:original |  | 1738993bb6a56b84d9eb1c83d3a9373ae362c69d58e7f196fd0e136c379e558a |  |
| 2026-11-24T07:08:43.295963+00:00 | retry |  |  | test:item_checklist:polished |  | 1c2a43201f1f4a86ee3f1f2b0b7b189b361dd52765a25eb908c0a85f701a7241 |  |
| 2026-11-24T07:08:47.775671+00:00 | retry |  |  | test:general_rubric:original |  | 075cc005d80b25889ec558e7e9357b75e8d37cf6ca0b4086b3262cf1ca69ce9b |  |
| 2026-11-24T07:08:50.187829+00:00 | retry |  |  | test:item_checklist:original |  | 78d3dc3b64e965ceafabb4ab1d90b2081a6f0ae970b4c40204edc232f8cc4cc1 |  |
| 2026-11-24T07:08:57.221182+00:00 | retry |  |  | test:separate_scoring:original:B |  | d6c756fa356de773f92a12ec37f71cb2a32de277f9b7413d6c014367f12ac310 |  |
| 2026-11-24T07:08:58.089025+00:00 | retry |  |  | test:free_form:original |  | 4f66b5f209c065150490bd796679a230d2e5af149c28a683ee38434d8e007f21 |  |
| 2026-11-24T07:09:01.497869+00:00 | retry |  |  | test:general_rubric:original |  | c91a0cd088a9afb0f44bf45979f38d89610912224bdede4dc76575e2917360e1 |  |
| 2026-11-24T07:09:06.407564+00:00 | retry |  |  | test:separate_scoring:original:A |  | cedacd234f4ea67719ff8b449ea4c604dfa030fe3c493e0525f92f1faf6dac10 |  |
| 2026-11-24T07:09:08.171843+00:00 | retry |  |  | test:free_form:original |  | 193f04b3521e4e40a718b7ef9be1da580b798f4e72bd2deae4713366f14a8b52 |  |
| 2026-11-24T07:09:09.316858+00:00 | retry |  |  | test:separate_scoring:original:A |  | 4c16e23ec6f9a6b8ca7a30ca94f8dff661beeb7a9111c2a3de759b7b34ae8654 |  |
| 2026-11-24T07:09:12.100954+00:00 | retry |  |  | test:separate_scoring:original:A |  | da5cbe123aba59edd7e7d3b4095d988cc8cdfc28c7793d4b78d7833a87d59ece |  |
| 2026-11-24T07:09:14.706826+00:00 | retry |  |  | test:separate_scoring:original:A |  | ce90b9ac865aba997bad61a699faf089cdf813a052c22c6ad2b8744eaf31a63e |  |
| 2026-11-24T07:09:18.156881+00:00 | retry |  |  | test:item_checklist:original |  | 54bc0453a5d98c31616b92271cac898250acb0af99d83b06bdc512e900b0be9c |  |
| 2026-11-24T07:09:24.773078+00:00 | retry |  |  | test:separate_scoring:original:B |  | 43ab36d16ed97652dd7a83b0bc41338a274bc187a3cc6f4faa174273ceae3dff |  |
| 2026-11-24T07:09:27.963150+00:00 | retry |  |  | test:item_checklist:original |  | b76a99f33d4dd4c9eb95128df98069cfde59c34dc5d6f62ea4552248de39367f |  |
| 2026-11-24T07:09:31.430619+00:00 | retry |  |  | test:exam_prompt:polished |  | 17ead862c38a5387298ab1b11592a2673de8853b23971661e4ad631cd6da2f55 |  |
| 2026-11-24T07:09:34.185187+00:00 | retry |  |  | test:item_checklist:original |  | 26cf15954bfcf19710fe38da3e75bc1287d6480631cbce1a4c9449960956286a |  |
| 2026-11-24T07:09:36.527089+00:00 | retry |  |  | test:separate_scoring:original:B |  | 46940826468c38f999fd958d422ba5c642b567f15def3f11b130708fe0574d6e |  |
| 2026-11-24T07:09:39.005764+00:00 | retry |  |  | test:separate_scoring:original:B |  | f30154dd4be34a7ee958460d22a88fb1deaca681da5bc4dc8924759d34b574f8 |  |
| 2026-11-24T07:09:43.331331+00:00 | retry |  |  | test:exam_prompt:polished |  | 46165d962be7e1d1f3cf0d8eeb1391856dcca53dbb7059b8f528fe0848f9a2a6 |  |
| 2026-11-24T07:09:44.707846+00:00 | retry |  |  | test:item_checklist:original |  | 70aef237b95047e7def155c5f5ee26d9321b1092adb184d59d8776d326d5dc0d |  |
| 2026-11-24T07:09:45.852109+00:00 | retry |  |  | test:item_checklist:original |  | 52f5fe393fb9dce488bd5c5d63b7edf0fd7ec021ae1ab035bc378824cce89548 |  |
| 2026-11-24T07:09:47.081858+00:00 | retry |  |  | test:general_rubric:original |  | 50ca749fc9be67b7f90b3e6162295a625b7024b05887733f71543a41ae31f7f8 |  |
| 2026-11-24T07:09:49.081714+00:00 | retry |  |  | test:separate_scoring:original:B |  | 02960066be9ef0d0de30f3c2ecd28203495ed65d22ef53400c0e8701805f1627 |  |
| 2026-11-24T07:09:51.856454+00:00 | retry |  |  | test:item_checklist:original |  | 462a3ed72df3bf49f54aae7f225f1edfdd50583bf662e8c4320485a511f5be74 |  |
| 2026-11-24T07:09:55.624569+00:00 | retry |  |  | test:exam_prompt:polished |  | 6831a25fe6c294ec7db260abea72a6d11893ed2f4f59b3c1ad37d53b456a2d0d |  |
| 2026-11-24T07:09:55.993781+00:00 | retry |  |  | test:general_rubric:original |  | ef2b00e4ad3b2053d9b9cfed92aa41e01f9a241f243acc0fea71d9abe1d23d4d |  |
| 2026-11-24T07:10:00.526696+00:00 | retry |  |  | test:general_rubric:original |  | f1ec9f3cb5e03c5d8b80529b5ddf90880d8491f8a03afee47b7ca8ebda60a364 |  |
| 2026-11-24T07:10:04.479599+00:00 | retry |  |  | test:separate_scoring:original:A |  | e963bbee4337eb948a66bc3b445c5086de7b01ed396bad039fd60e7359111a37 |  |
| 2026-11-24T07:10:05.308815+00:00 | retry |  |  | test:exam_prompt:polished |  | 6f3f357f7f118935bb462f8acccd5527b2c5b75ab1f7499c4867fbd858db3ba1 |  |
| 2026-11-24T07:10:07.252699+00:00 | retry |  |  | test:item_checklist:original |  | 02767b6ea4db0513d28b367ca58c4dc92748404a429609e649b92f7f36b76d7a |  |
| 2026-11-24T07:10:11.467580+00:00 | retry |  |  | test:separate_scoring:original:A |  | bb9ec41be965efd2f1d00576cfea1fd0ace5c4715b53ece10cf5e2fe7febf509 |  |
| 2026-11-24T07:10:11.847791+00:00 | retry |  |  | test:general_rubric:original |  | 824316c4dd563966cb5c49d21752feea9031bc991f0a309154302de4bdbabe16 |  |
| 2026-11-24T07:10:13.863210+00:00 | retry |  |  | test:free_form:original |  | 3b7215c7069cf77835550ea734beaec633d0caa5c742b8f2915a19cfcf9e8091 |  |
| 2026-11-24T07:10:13.978188+00:00 | retry |  |  | test:item_checklist:original |  | 4453986b24c628bd09d89f0859a0ea942f177eba81ff722316ef21598aaa6524 |  |
| 2026-11-24T07:10:15.998181+00:00 | retry |  |  | test:free_form:polished |  | 183ed6de4a5d574871578f0f758c201b640a553da3171ca37490c994dfaa5b94 |  |
| 2026-11-24T07:10:18.192572+00:00 | retry |  |  | test:separate_scoring:original:A |  | ab65ecb56bde4b9100055457d3e27998757308a369479cf2f167ee750ef0cb35 |  |
| 2026-11-24T07:10:19.005705+00:00 | retry |  |  | test:free_form:original |  | baff3d562b0631f34f6690c032e02a5c3ec11ec86da4a4c754bfd50fd5ae7395 |  |
| 2026-11-24T07:10:23.272650+00:00 | retry |  |  | test:free_form:polished |  | db0247b709dfb1501b7a0bca31224e882ca9fa8a144f53780957a7b947454940 |  |
| 2026-11-24T07:10:25.397052+00:00 | retry |  |  | test:separate_scoring:original:B |  | 0cc59d74f49673319a59132247902093b7f4c673ee6b1edd50c7335a17f46ddb |  |
| 2026-11-24T07:10:32.846995+00:00 | retry |  |  | test:separate_scoring:original:B |  | 15d3561528384904c4c74f64aad803931d3012d0965143104c3bff8efb9a3f0d |  |
| 2026-11-24T07:10:35.399518+00:00 | retry |  |  | test:separate_scoring:original:A |  | 095de192ebd7d86250c4cb888c60c5d734aedc3bef976a9bf9d6d7064301a855 |  |
| 2026-11-24T07:10:38.715384+00:00 | retry |  |  | test:item_checklist:polished |  | 1cf74a6c1b2bbe0a891dd35c40fe7b2901fbe2def8e9a542ba5ca4d997411064 |  |
| 2026-11-24T07:10:40.804314+00:00 | retry |  |  | test:free_form:original |  | 8b182355428d2053c13baf21e25bb118089b1a28536aeb49a9b6ec935813e705 |  |
| 2026-11-24T07:10:44.670598+00:00 | retry |  |  | test:item_checklist:original |  | f2ba7c57d87a6a6def40b90fba884222c0eebbd5e88ac6e7f01f7ade248398e1 |  |
| 2026-11-24T07:10:46.769042+00:00 | retry |  |  | test:item_checklist:polished |  | 70d7369e8660d2ee61e6d6d3869e3781292cde3e98703fd6316f1024d14c1be7 |  |
| 2026-11-24T07:10:47.640881+00:00 | retry |  |  | test:free_form:original |  | 64729e0d739cee5e0a558cac949ecd12ac050766de84ceb5c1efb44bf0d99a70 |  |
| 2026-11-24T07:10:49.612729+00:00 | retry |  |  | test:separate_scoring:original:A |  | adaccbc5e16f5c1e158fd646b0d2937f04cdf6d0a465f92d9ebb12028a2a61cf |  |
| 2026-11-24T07:10:50.093316+00:00 | retry |  |  | test:item_checklist:original |  | 0fbe079fa8b23972e577fe1e12906b1e4b04e974026c89808d2401fe5463ae78 |  |
| 2026-11-24T07:10:54.931422+00:00 | retry |  |  | test:separate_scoring:original:B |  | 5a39db6d53c1e8990ecd7f9b32a948adec419477a7cc678f72b79a196d9c24cb |  |
| 2026-11-24T07:10:57.139194+00:00 | retry |  |  | test:free_form:original |  | 830605db3900cb9307d92c285ebc561463fa3d0c17aa99be3c5c9eb62612e138 |  |
| 2026-11-24T07:10:57.729776+00:00 | retry |  |  | test:own_requirements:original |  | 8863ae88777d17d13fd5629a78ba6d00803fcf5f73cafb8c48380b49734e210e |  |
| 2026-11-24T07:10:59.519192+00:00 | retry |  |  | test:own_requirements:original |  | f697ce3ff04b46baed52fc32391c9e2fb3db4f5f1949c19ee63d82bd1a67a3a3 |  |
| 2026-11-24T07:11:03.998436+00:00 | retry |  |  | test:free_form:original |  | f2fcb35c840500eff513de20db47591f7de590838bda325a26af71899c1337a8 |  |
| 2026-11-24T07:11:06.728493+00:00 | retry |  |  | test:item_checklist:polished |  | 6079648df01d047346ab2d6173ca7a08fc04530d9fe5691c8868dd87f2f249b8 |  |
| 2026-11-24T07:11:08.021328+00:00 | retry |  |  | test:own_requirements:original |  | 77c34d0f72b509c23a340ccde03d65b0302b3297ba071c3b40abda1d67f6067e |  |
| 2026-11-24T07:11:14.105294+00:00 | retry |  |  | test:item_checklist:polished |  | 2532ecfc86404de70ba087b05568d437d659d5e632967df617f957aeaa849120 |  |
| 2026-11-24T07:11:16.092062+00:00 | retry |  |  | test:separate_scoring:original:B |  | 0b8021d85c14fc21649c65ce18d33246b291888c2665e915b8d4259870ce2efc |  |
| 2026-11-24T07:11:17.942085+00:00 | retry |  |  | test:item_checklist:original |  | 524fa345939bbf6197caf37626f14c82352147e903edbb9538e87af56976ea6a |  |
| 2026-11-24T07:11:27.391261+00:00 | retry |  |  | test:separate_scoring:original:A |  | 250c389ca84914341d37991cb7df3f553d7617fe61f83b4cadc09b53b3f961f1 |  |
| 2026-11-24T07:11:28.813380+00:00 | retry |  |  | test:item_checklist:original |  | 89b1e4e241425252ffc9dc5afaed20f837dbff7788e9c591690fe34be127e161 |  |
| 2026-11-24T07:11:29.165109+00:00 | retry |  |  | test:separate_scoring:original:B |  | b3eb0bfbdbbc9300bfe7429ac7b3a99b8b427b3234f9ab7fe916e52af83c70c5 |  |
| 2026-11-24T07:11:29.484742+00:00 | retry |  |  | test:free_form:original |  | f29aa45f11128607d3d7baca149c8bb694d7e8aa32eeb3e392a24d477db55f95 |  |
| 2026-11-24T07:11:32.486032+00:00 | retry |  |  | test:separate_scoring:original:A |  | af45d57865bb2dda4919889aef564c512f717e7230792cb42b86b60ebfb521bf |  |
| 2026-11-24T07:11:35.447177+00:00 | retry |  |  | test:free_form:original |  | e494b27a3132c7887cf90849f962bb90e1df1494e3e514cd9b3e4f2d1bfccd4f |  |
| 2026-11-24T07:11:47.258763+00:00 | retry |  |  | test:separate_scoring:original:B |  | 528e2d91de6dc125c3e4b5acb9cc858913033e58fb545ed87eb86acd43504dd6 |  |
| 2026-11-24T07:11:50.541955+00:00 | retry |  |  | test:separate_scoring:original:B |  | 97603f811bf3072f8301c53691c400afc67713b1f7ea7571c6b0d0f1d3dd367f |  |
| 2026-11-24T07:11:53.709381+00:00 | retry |  |  | test:separate_scoring:original:B |  | 53dd6175fec1a7338e0f483ea5810e63c5ef13eafd242c712e356fa1a73001f5 |  |
| 2026-11-24T07:12:07.840001+00:00 | retry |  |  | test:general_rubric:original |  | 96c936a420eed4509132f9d6225cef10a834d7e552dcf56833dda41ad3df4af6 |  |
| 2026-11-24T07:12:12.050784+00:00 | retry |  |  | test:own_requirements:original |  | 281e8bbcf0531a0321fea9aa12a0790ebd428d9c9a5b46378742fba846c90435 |  |
| 2026-11-24T07:12:17.000334+00:00 | retry |  |  | test:general_rubric:original |  | 10ad39533be4d35df7a4a670aa4c5fc53e15742615b41de27ccdfb87f684ea5a |  |
| 2026-11-24T07:12:19.129266+00:00 | retry |  |  | test:item_checklist:original |  | 8c5b5adf5e363a2159fcd555faf459c1b7eb82bbabf4f03625c33accc00714df |  |
| 2026-11-24T07:12:21.204498+00:00 | retry |  |  | test:own_requirements:original |  | e2d57853642de9a6daa57c7afb97fcb88ac9466a65677b1e71ab17f94633f6d7 |  |
| 2026-11-24T07:12:24.069587+00:00 | retry |  |  | test:item_checklist:original |  | a5c310fe37e45ce224d739622b7bce59369af90c7c1529365f1b55dabcfb7328 |  |
| 2026-11-24T07:12:39.643979+00:00 | retry |  |  | test:separate_scoring:original:B |  | ab6043ce3148aaa4d6317711209542137aea4d162f28a9aef1d856841c550413 |  |
| 2026-11-24T07:12:48.200251+00:00 | retry |  |  | test:free_form:original |  | 0fa6600c828280db1985d31ccab53eb700f1c26a4e9c1505fafab8d301325329 |  |
| 2026-11-24T07:12:50.281652+00:00 | retry |  |  | test:free_form:original |  | 33665fae17bcb54e135e64928535e7200b5bbf980582ec33776bc773c0d0f867 |  |
| 2026-11-24T07:12:52.519927+00:00 | retry |  |  | test:item_checklist:polished |  | c74ca3bdec53a9f4ef608804a4fb6d0c90379a1148d0c0feaf0bab1aa89ff658 |  |
| 2026-11-24T07:12:54.549728+00:00 | retry |  |  | test:free_form:original |  | 9efa20934d7f1009e218a16606a0e62aa408e1f18126d45d85f972a96e9f9f96 |  |
| 2026-11-24T07:12:56.629091+00:00 | retry |  |  | test:free_form:original |  | 00cd9d0eeb2aeb8bba796fd7bd626c8f06422cd8b81884d0bba89f7fdd596098 |  |
| 2026-11-24T07:12:58.545439+00:00 | retry |  |  | test:item_checklist:polished |  | 59e8bb95020356881264c29cbe6477e614094660e5bbd328e1279cd8ca6c078f |  |
| 2026-11-24T07:13:10.049106+00:00 | retry |  |  | test:separate_scoring:original:B |  | 23b9af665305fec9ad765d504e6ba11a778d59bf8b19c7c26e4f1b0f5a055364 |  |
| 2026-11-24T07:13:11.617419+00:00 | retry |  |  | test:free_form:original |  | abeda5033d860fe5f861dcc378e6b45da62642d9038ef24b90650c1c16d8897c |  |
| 2026-11-24T07:13:11.989023+00:00 | retry |  |  | test:exam_prompt:polished |  | 62bf00e360cd5acfee17acd9a8134e5e4cd2cadedc1769b84ed03d33d926cdc9 |  |
| 2026-11-24T07:13:12.810158+00:00 | retry |  |  | test:separate_scoring:original:B |  | 3eff62675988bd9d454046365d7b51d7893e261f6231d1665caeeb81c57ad16a |  |
| 2026-11-24T07:13:13.701522+00:00 | retry |  |  | test:own_requirements:original |  | 72881ff4d12ae2dd1a95a525ae2e70f660fa62d0d9174a965975d131b1cbf2ba |  |
| 2026-11-24T07:13:13.917587+00:00 | retry |  |  | test:item_checklist:original |  | 48bc55789a04c7d994734e1e80fc62594bba4164af98ad009eb6a8c105201978 |  |
| 2026-11-24T07:13:17.107512+00:00 | retry |  |  | test:free_form:original |  | 1bfcf0f1435941068135ec52faaf5a6898b33ef266b2e2a0d98a1d2b248abb02 |  |
| 2026-11-24T07:13:19.151187+00:00 | retry |  |  | test:exam_prompt:polished |  | 28e0696662d19aaf7daeb4cff790fc126f13544cd89ef24156b6a4bf999d460f |  |
| 2026-11-24T07:13:20.519620+00:00 | retry |  |  | test:own_requirements:original |  | 7dda702fef197fdb5a3d1344645a0b876a62fc7a4092ce735c75f8d5ef1f4896 |  |
| 2026-11-24T07:13:21.238322+00:00 | retry |  |  | test:item_checklist:original |  | 725e331e6a42f0f35b7046be8d3603b6a1f8538cf656d076670d841015a29584 |  |
| 2026-11-24T07:13:22.435870+00:00 | retry |  |  | test:free_form:polished |  | 2be95840c46d489e9b0302fae3f15842acb213158b868c65f361f8aeeaebc679 |  |
| 2026-11-24T07:13:27.455229+00:00 | retry |  |  | test:free_form:polished |  | f2391f18846caec724c321b0ba875f772d9c055ac4c61536b5264e7bc81e3723 |  |
| 2026-11-24T07:13:29.452321+00:00 | retry |  |  | test:free_form:original |  | 0e9257d1077af1cc82e0e3a1f9702c6bacc5ccea2be3ffb5fa630784f4499060 |  |
| 2026-11-24T07:13:31.162896+00:00 | retry |  |  | test:general_rubric:original |  | cee9cdab1bed4740aba8ca6e0c6ea73271c15c4d4d96669edb8b9e6568885d5a |  |
| 2026-11-24T07:13:33.160687+00:00 | retry |  |  | test:general_rubric:original |  | 2313bdd8da9e8befb5578984c422e5de480d2e9762b33e0e68d09eafa4264dd7 |  |
| 2026-11-24T07:13:34.519230+00:00 | retry |  |  | test:free_form:original |  | 82668010f631ea05b567b30eeefaae34af485e676679afcf0f8dbbaa2c2cd8e3 |  |
| 2026-11-24T07:13:35.371891+00:00 | retry |  |  | test:general_rubric:original |  | 1a48263b94ebf8d7a4654eaa32fd963a68a074c97df27b6b5eac6bc535c0abf5 |  |
| 2026-11-24T07:13:37.307804+00:00 | retry |  |  | test:general_rubric:original |  | 1805927da1db57b260f539b16a0685b65fb492a17f6d34d32b26385d576df825 |  |
| 2026-11-24T07:13:38.632272+00:00 | retry |  |  | test:general_rubric:original |  | 4d321b4647b527377ac13a63b63f74e0034edf608acd8ad4b705a27eaba5ee24 |  |
| 2026-11-24T07:13:39.411658+00:00 | retry |  |  | test:exam_prompt:polished |  | 73682e57c01da5306ad0cc22908a5f508ce77aad99777c5049185887a5faeedd |  |
| 2026-11-24T07:13:45.657082+00:00 | retry |  |  | test:separate_scoring:original:B |  | 6e8f3a37f9532b7a844e2bfe07fa5f55418ff49a0118ef85e94d5873272fb8d3 |  |
| 2026-11-24T07:13:49.210443+00:00 | retry |  |  | test:separate_scoring:original:B |  | 560bde902c432e742bcf0dc2f10f8f94b46ba8731e0e030776698693a508a148 |  |
| 2026-11-24T07:14:06.693391+00:00 | retry |  |  | test:separate_scoring:original:A |  | 1d3b099ca930f6f1d7cd2acc0b49db24ef1888fa9f702307b375971e53db0aa4 |  |
| 2026-11-24T07:14:08.678250+00:00 | retry |  |  | test:item_checklist:original |  | a7945616c79ed8ec14ae2921fe7836df45f57b815305b9e9ca5ade72e4fc92c2 |  |
| 2026-11-24T07:14:10.651085+00:00 | retry |  |  | test:free_form:original |  | 53bb919bb9abb6519f861368b392899bd503d247a2b80e7b617074be15057c19 |  |
| 2026-11-24T07:14:21.417858+00:00 | retry |  |  | test:item_checklist:polished |  | bd3df7e05297ae02aa4874e2b090175c23dfda3bb756533beaf9f8c16da9dd54 |  |
| 2026-11-24T07:14:23.412674+00:00 | retry |  |  | test:separate_scoring:original:A |  | e249188017116d0f41f089f3ec20bea38a3bb6268a6b63aea12d38fe5b073e50 |  |
| 2026-11-24T07:14:25.654196+00:00 | retry |  |  | test:item_checklist:original |  | 561bc8ab841ffb2ae3fd86d0fd684bf064408b318453a8b5629be09c612a41db |  |
| 2026-11-24T07:14:27.666056+00:00 | retry |  |  | test:free_form:original |  | 3dba1e6366f23f4567790a730ecdc91f856f832be3d067130b38dd19dd029a56 |  |
| 2026-11-24T07:14:40.713601+00:00 | retry |  |  | test:item_checklist:polished |  | 02aa11f324bec2ed8458641d71967d025300dfed80dc798b1ee4e5f5d7066535 |  |
| 2026-11-24T07:14:47.968948+00:00 | retry |  |  | test:separate_scoring:original:B |  | c8c00b88483ca2aa44632ba811bdf1afce0148adb7ee15b86a6afc68f8a65a39 |  |
| 2026-11-24T07:14:52.689072+00:00 | retry |  |  | test:free_form:original |  | 7f2e902d643ef903159c13eaa105c19e0ffa50f919eab92019f02fc2423fd780 |  |
| 2026-11-24T07:14:57.782372+00:00 | retry |  |  | test:item_checklist:original |  | 52fd04fca18e0150b0dd93ba407558b283a04abc78503d0e84f309507eff664a |  |
| 2026-11-24T07:14:59.993850+00:00 | retry |  |  | test:separate_scoring:original:B |  | 97759e44575c4133c868ea1784153cccc29f398f78292dbccbfbe836259b603c |  |
| 2026-11-24T07:15:03.656883+00:00 | retry |  |  | test:free_form:original |  | ac0c77ce2208df2505d5ba8cf061cbadf0bb89b82356213fe067be09abd15172 |  |
| 2026-11-24T07:15:06.031000+00:00 | retry |  |  | test:separate_scoring:original:A |  | ccd83cde64fcd4f7c867c470c1088565268328cd0e8e53c1c4698fc7c2bfce0d |  |
| 2026-11-24T07:15:06.265404+00:00 | retry |  |  | test:free_form:original |  | dd70b7b9934feef93c83c7be6341d829d13ff69140642bf9235c7abddd7bb7c1 |  |
| 2026-11-24T07:15:08.557306+00:00 | retry |  |  | test:item_checklist:original |  | 78783c8e7b78dd4e5356d83e7ebe205140925994eb903531db47a0af57ffc6bb |  |
| 2026-11-24T07:15:15.647328+00:00 | retry |  |  | test:free_form:original |  | d64e30b75aa7a35cc9523c7a67ac1c44424cf283a31fd0d3c4c8975ae76efea2 |  |
| 2026-11-24T07:15:15.663524+00:00 | retry |  |  | test:separate_scoring:original:A |  | 6b7965228c15fec07576f53865a08b36b193c4c01373e3f580df94c48941ddb2 |  |
| 2026-11-24T07:15:26.043472+00:00 | retry |  |  | test:free_form:polished |  | 02afe0978df2bf01d68103c1b3dcde8ea611e688e4674c48c3c5e45271d14859 |  |
| 2026-11-24T07:15:32.449145+00:00 | retry |  |  | test:item_checklist:original |  | e26e675cc297512141dc44b2e5c44c8d085a5c8e7a22e5b684e9ca22e5d159e1 |  |
| 2026-11-24T07:15:34.489069+00:00 | retry |  |  | test:free_form:polished |  | 7b0c71886ff621f90863ac434d5554b81393ef559c2bbaf51c52223097f6b71e |  |
| 2026-11-24T07:15:36.417150+00:00 | retry |  |  | test:general_rubric:original |  | a0bb375280460ab4895a92d95db40bbe6d2412486498d831eda877199274c29b |  |
| 2026-11-24T07:15:36.666435+00:00 | retry |  |  | test:separate_scoring:original:B |  | 460a1364dd0d3074c8d6f25755c7917b2e600940baf799c714b31e55b5145b4a |  |
| 2026-11-24T07:15:38.523531+00:00 | retry |  |  | test:item_checklist:original |  | a75d3a24984085b16f62cf0379cfc810d11b26ce5ffb1bc1bbab8b69283c58ef |  |
| 2026-11-24T07:15:41.775487+00:00 | retry |  |  | test:separate_scoring:original:B |  | 20c1c6937045f860e259e3a566776e1f5051796cb051818b2d3c28b19ef3bd9c |  |
| 2026-11-24T07:15:41.792906+00:00 | retry |  |  | test:general_rubric:original |  | e90c64215e09986d63f5df8ee1cecb8f532644a7cfc053ece798ecbcff60feec |  |
| 2026-11-24T07:15:43.557628+00:00 | retry |  |  | test:item_checklist:polished |  | 0b2aec60839d3a81311c7c3261bef169c1371e595b3c2e1e832d52ff4aef3a65 |  |
| 2026-11-24T07:15:45.913248+00:00 | retry |  |  | test:item_checklist:original |  | bc38fa12d48ff78192591bfcc593e06efd4afe11831df55ba38a59007e1c23ec |  |
| 2026-11-24T07:15:51.834146+00:00 | retry |  |  | test:item_checklist:original |  | 743500d1bbb7b40f8d8666efbb134855f3ec900f0c503345b0af34562948e6ed |  |
| 2026-11-24T07:15:52.389452+00:00 | retry |  |  | test:general_rubric:original |  | dfbd583411d51273e8a645f93d80af9307a218fc6c1094149e3cdec3869ef546 |  |
| 2026-11-24T07:15:59.173747+00:00 | retry |  |  | test:general_rubric:original |  | e1f804f5d5867c5416bb98e2f27726aaf2dc4c92dbd683b0223fc7896ab92135 |  |
| 2026-11-24T07:16:03.572942+00:00 | retry |  |  | test:separate_scoring:original:A |  | 50c9e7ba473a0ab2bb5eb702db2b591a638cd3b877a5c7d6811b5ab9a11c6f68 |  |
| 2026-11-24T07:16:08.249294+00:00 | retry |  |  | test:free_form:original |  | 77648ef7e23ecd5d791472639e743a40dc79d6b8cbe58b1ceaa54da42a14ffc6 |  |
| 2026-11-24T07:16:12.445558+00:00 | retry |  |  | test:separate_scoring:original:A |  | 76394c67d035f61711130805d3b0877c15628293535c849e04091238265a90e9 |  |
| 2026-11-24T07:16:13.321299+00:00 | retry |  |  | test:exam_prompt:polished |  | 7297128f3f75c8dfc35a9606d93e04cfea4a00279c6fafbed32ad97aa56a970a |  |
| 2026-11-24T07:16:15.524831+00:00 | retry |  |  | test:free_form:original |  | 2739d124946bb2190cc2011a42487f8d2ba507a457b3ae5705ecb77f9efd7973 |  |
| 2026-11-24T07:16:17.598769+00:00 | retry |  |  | test:separate_scoring:original:A |  | fb5fe2d0b8f6f0ec0aea929403e5944ddc4c900bbb9f0816f7a828be59122bfd |  |
| 2026-11-24T07:16:19.572718+00:00 | retry |  |  | test:exam_prompt:polished |  | ba8bb59e1c2cc5aba7614556e5edd54c996ae61765ade3627bdc6db540185d5b |  |
| 2026-11-24T07:16:29.527765+00:00 | retry |  |  | test:separate_scoring:original:A |  | 6991ecae07f50e2fd86f8bd3f4c350f7a1880c1f51bb1ebd76ac82a0b810a04e |  |
| 2026-11-24T07:16:30.286762+00:00 | retry |  |  | test:separate_scoring:original:B |  | e5a1ac2202c53d8795babdf66d456c0e56c0dd54fb088a0212efb6f3ef7eba05 |  |
| 2026-11-24T07:16:35.423454+00:00 | retry |  |  | test:item_checklist:original |  | eb499f19107cbd51ca5d86f049135fc44df7f46286a2dfe3d86424be77059402 |  |
| 2026-11-24T07:16:37.368722+00:00 | retry |  |  | test:item_checklist:original |  | 103debccb1502c964cd0042b8748fede3fe30981812a507ad1676de94525827e |  |
| 2026-11-24T07:16:37.457799+00:00 | retry |  |  | test:separate_scoring:original:B |  | ce2924578b7057e14f7434a2349e3839539ef48f2307a80b09936b58f70859fb |  |
| 2026-11-24T07:16:40.416451+00:00 | retry |  |  | test:item_checklist:original |  | df72737ddd9786bd2cb11520694066dae7e2347131176693c85f2590b7d70946 |  |
| 2026-11-24T07:16:42.504305+00:00 | retry |  |  | test:item_checklist:original |  | e5c68116c9694bdf0c6150503f52624242aa2305c787fabc15add6555d82374a |  |
| 2026-11-24T07:16:45.385388+00:00 | retry |  |  | test:separate_scoring:original:A |  | 7d7d56642301a9a98e8d8ca2d5c5af1f344ce930ea6832c9c2d89c63153cf501 |  |
| 2026-11-24T07:16:51.725639+00:00 | retry |  |  | test:separate_scoring:original:A |  | a06941a6a35a7062c39bad00306993417b0cc793db4e5be8ba71e2d047fc61cb |  |
| 2026-11-24T07:16:52.099308+00:00 | retry |  |  | test:separate_scoring:original:A |  | eabe395838ebad2bffb4889cbb1fb538aba227c6a74e92b98eace202df2a6f07 |  |
| 2026-11-24T07:16:57.209729+00:00 | retry |  |  | test:general_rubric:original |  | 8170b5882e62f2024951f675f74ba6978f34d82d15d9bf19d852046076f9c582 |  |
| 2026-11-24T07:16:58.718481+00:00 | retry |  |  | test:separate_scoring:original:A |  | 49860efbddf5745285b4040f07b9a0af9d326d376b6a44d86b5bf93071c46210 |  |
| 2026-11-24T07:17:02.100013+00:00 | retry |  |  | test:general_rubric:original |  | 2e639b9375d86cc9cddb1ae9368fd656e207fef2f5854e720f8ba7f9666af7bd |  |
| 2026-11-24T07:17:09.008874+00:00 | retry |  |  | test:separate_scoring:original:B |  | 5b07385686edf9cecdf0341211e535e29bf6fe9359672f481a499e39a23f39db |  |
| 2026-11-24T07:17:10.953187+00:00 | retry |  |  | test:separate_scoring:original:A |  | 96615329b174937af8bd843036d1166edd72440ebd1dbe9b0650bc161961a31b |  |
| 2026-11-24T07:17:14.445265+00:00 | retry |  |  | test:separate_scoring:original:B |  | bd4684d4c90d5874901da823758913ba35a6c29d2f23c9937b6d8a8affb83dce |  |
| 2026-11-24T07:17:16.428861+00:00 | retry |  |  | test:free_form:original |  | 88a7987ba545b00b689c5f1cb67818492e7986bc75567fcc812647d650366b49 |  |
| 2026-11-24T07:17:17.610935+00:00 | retry |  |  | test:separate_scoring:original:A |  | f67ed66c4194b4d4a0a961bd01b68ed17084d04103cedbd76fc58307b7f4d06f |  |
| 2026-11-24T07:17:21.559326+00:00 | retry |  |  | test:free_form:original |  | fd553495ce2bc6a2e61aefeefa2f68b70bccf6c9edee587e47937d74d1e9ba42 |  |
| 2026-11-24T07:17:23.399328+00:00 | retry |  |  | test:separate_scoring:original:A |  | d858c8e572144836343ffcaac4c9f298683af11451b66fba003fd60f2b511358 |  |
| 2026-11-24T07:17:26.111574+00:00 | retry |  |  | test:free_form:polished |  | 062fb55bbefdd38e4c7c64b39ae4f79d8f51febf9b2d3781aae7be01fe0ff8e8 |  |
| 2026-11-24T07:17:28.342791+00:00 | retry |  |  | test:general_rubric:original |  | 3279f942a7525f86c9aad576acb54bf459559f216e72456e79d21582ebb246d4 |  |
| 2026-11-24T07:17:30.225799+00:00 | retry |  |  | test:separate_scoring:original:A |  | 260830a62e0b2911d8589cbd06813414b83ae414233a2dd21bd9a75d4e89ce9b |  |
| 2026-11-24T07:17:33.373113+00:00 | retry |  |  | test:free_form:polished |  | 9298d6e60eb1dba10404a29079f2eb8152be72b6ad801de39f60df56b4126f13 |  |
| 2026-11-24T07:17:36.738089+00:00 | retry |  |  | test:general_rubric:original |  | b49a78c5ef9183b08b5cf45e9e8ff7c4f0987e40808b0eeaa2a09aac9fd5ee94 |  |
| 2026-11-24T07:17:41.224557+00:00 | retry |  |  | test:separate_scoring:original:A |  | d3439521c3b7bcea069faa1884c19a3bf73b391657321e6a6a76983bc0db900c |  |
| 2026-11-24T07:17:43.171332+00:00 | retry |  |  | test:separate_scoring:original:B |  | 823ec1ef266c94d9c22703377f1b446209a1254a5840404c5e121e755ff7c433 |  |
| 2026-11-24T07:17:48.929071+00:00 | retry |  |  | test:separate_scoring:original:A |  | 5f5a108d6c4516d1b8aa6af5ea85bbbddf642a09a1180c8d486df9cca5484e5a |  |
| 2026-11-24T07:17:50.989894+00:00 | retry |  |  | test:separate_scoring:original:B |  | 08318096e6bb78844302ebcc027dddc024ba68b330449aa6f68d8878e65701d5 |  |
| 2026-11-24T07:17:53.672757+00:00 | retry |  |  | test:exam_prompt:polished |  | f6be30a0f57330dd282a76d33bbdffab2ae24f68af1de1be1a221c7dd06a79c1 |  |
| 2026-11-24T07:17:57.686604+00:00 | retry |  |  | test:separate_scoring:original:A |  | 1a14d19efeb94645691a8e5660845228ef381d992ec2b781288f029e6e82c600 |  |
| 2026-11-24T07:17:58.588411+00:00 | retry |  |  | test:exam_prompt:polished |  | 1a1eb4de6ceec9188a55dd3c024f4bd5847091f3b09d584332b5b057c61aff38 |  |
| 2026-11-24T07:17:58.821836+00:00 | retry |  |  | test:separate_scoring:original:B |  | 5bdd7e52faf83fde0ab138c141fa02ce66e10dcf52a186ee80454e234e51c61a |  |
| 2026-11-24T07:18:04.109104+00:00 | retry |  |  | test:separate_scoring:original:B |  | c201d4dfb6b92d5f320ec874e02fa71166805a2a767c0e5bb1c66fbce95203ae |  |
| 2026-11-24T07:18:10.509247+00:00 | retry |  |  | test:general_rubric:original |  | 399a1a955c4317118aa09170f6aee5d9bde547f0e473a6906eed749b025e0020 |  |
| 2026-11-24T07:18:14.180044+00:00 | retry |  |  | test:separate_scoring:original:A |  | 561fb2b58dcee01ebaccb1d003137fbeeadd0f1bcb164adf0b97d98390c5ee45 |  |
| 2026-11-24T07:18:14.392733+00:00 | retry |  |  | test:own_requirements:original |  | 68fca36af4e32367e82c0b37f6fd3efff16ae3e51ecb7b4087517eef03d2808e |  |
| 2026-11-24T07:18:15.601610+00:00 | retry |  |  | test:general_rubric:original |  | 86df416890ee45557cf8ec02297f7eb12d733d42c92468633dcafe6e536e869e |  |
| 2026-11-24T07:18:18.311915+00:00 | retry |  |  | test:separate_scoring:original:B |  | 09fe5eb995f9508d02400610e0b851e1e2e424850ec663a42d03f0957cd4d453 |  |
| 2026-11-24T07:18:18.600690+00:00 | retry |  |  | test:separate_scoring:original:B |  | 6f99e74065c1da5d35c1cf29ab53dfe769754ee362dca12a4a8e98fdf8008968 |  |
| 2026-11-24T07:18:26.943245+00:00 | retry |  |  | test:own_requirements:original |  | 0afd08ac2f8bce66d14c07a436d8999125b30a5e7611e27eef6a35a375d29ac6 |  |
| 2026-11-24T07:18:42.032737+00:00 | retry |  |  | test:own_requirements:original |  | 86bf9ec8832ec29a1b9e9608816dff97c81707384471f761746665b4ba764732 |  |
| 2026-11-24T07:18:45.586957+00:00 | retry |  |  | test:separate_scoring:original:A |  | 184c8b9b576a96e70646c279bed42eea7448bfb92e173bf9f08d8a87626e8c2b |  |
| 2026-11-24T07:18:46.997429+00:00 | retry |  |  | test:own_requirements:original |  | e31811e36064c9276d0ffdbaeeed7af906b61904081ad5afc03bbf97083b30a4 |  |
| 2026-11-24T07:18:50.666128+00:00 | retry |  |  | test:separate_scoring:original:A |  | ef6f61db558438ae64d2bddd180a24f5aedaff325eb7ed37b42785bbe1a52da4 |  |
| 2026-11-24T07:18:58.570674+00:00 | retry |  |  | test:separate_scoring:original:A |  | 740180bbb6bf940121400cc665791f13c2d5d0521b2b529b7415731af97056ca |  |
| 2026-11-24T07:19:00.948291+00:00 | retry |  |  | test:item_checklist:polished |  | 425044519953e6f388f93f7ef9bce3b177cf9d5185df4785e5914f43cc9caee2 |  |
| 2026-11-24T07:19:00.949625+00:00 | retry |  |  | test:separate_scoring:original:B |  | 74170290180a57057d86e14db7cb6f73619a7bd73ef3f3a809ba0595ae8e9e6c |  |
| 2026-11-24T07:19:01.989328+00:00 | retry |  |  | test:separate_scoring:original:B |  | 96cf254e327b3686c1d08eae3460eec25b4fdc03de70a5b37b2b6c2d3eee349a |  |
| 2026-11-24T07:19:03.725391+00:00 | retry |  |  | test:general_rubric:original |  | 6b8ca46a3994e56d7ec121b9723246662f2513d56224838aa45d368d302193eb |  |
| 2026-11-24T07:19:06.133231+00:00 | retry |  |  | test:separate_scoring:original:B |  | a875c95e1e10da34e543fa94893cd165f1c45aee850b36367030a7719178c7b9 |  |
| 2026-11-24T07:19:06.184014+00:00 | retry |  |  | test:item_checklist:polished |  | 47ac96d814a496781626d66f97e9b4250d875b14a1537f90b4a0e8a7d7fdad04 |  |
| 2026-11-24T07:19:08.813478+00:00 | retry |  |  | test:general_rubric:original |  | f9a8bd8fbd946c1ec6be76615110201373c5b84a9261303f5de13becf72672d8 |  |
| 2026-11-24T07:19:20.506348+00:00 | retry |  |  | test:own_requirements:original |  | 16b155d4d9f10b0e47777bb49b9bac39941512dba1ffb55b1e109efc28ac46fc |  |
| 2026-11-24T07:19:58.901929+00:00 | retry |  |  | test:free_form:polished |  | 71abb474a7f64423719f0c416eb6b8f49be83863cd7e23f61ec7bf931e49c1cf |  |
| 2026-11-24T07:20:04.132877+00:00 | retry |  |  | test:free_form:polished |  | 4bdb9f861056a76a2e81dbc3fb3f4b700fa19bd43b0202a4d25cab6125fb9d4d |  |
| 2026-11-24T07:20:15.965646+00:00 | retry |  |  | test:item_checklist:polished |  | b9733858a328a0f83fad9e9e5ad36ec9f505c8907b07b700aa9f62672317c82f |  |
| 2026-11-24T07:20:21.110775+00:00 | retry |  |  | test:item_checklist:polished |  | 89e905b5ad2b3981c0ac848b002c1e6236e874790b0e17ff83f499ebc4972cf3 |  |
| 2026-11-24T07:20:25.918309+00:00 | retry |  |  | test:own_requirements:original |  | b284627edbc827c710451c7934f8f0cca16b68b5b56cefbb6297e0811a8fb8fb |  |
| 2026-11-24T07:20:31.671937+00:00 | retry |  |  | test:free_form:original |  | a68eb8511a445f3d136668b9fd4e470ac2632931a2c3ca6a7fce52bf04362697 |  |
| 2026-11-24T07:20:31.808801+00:00 | retry |  |  | test:item_checklist:polished |  | cc9fee99b269d9c2739ef240f59c1e7e9ba05ff0336abcfe4ed4e5fd5a7656a9 |  |
| 2026-11-24T07:20:33.977353+00:00 | retry |  |  | test:free_form:original |  | 7cbce6ee3f9f5d18ece2d4d253fdb31fdd963632deb2606702db14dba62376c8 |  |
| 2026-11-24T07:20:36.017362+00:00 | retry |  |  | test:separate_scoring:original:A |  | 8c9f6dc971d1952b152b040ff0935df2edb513ae23a3cee8b0954680f7b50d64 |  |
| 2026-11-24T07:20:37.368769+00:00 | retry |  |  | test:free_form:original |  | 80f54867edf8b0ece9d57de8a5416602c0e53ebdd0b59f6a4744e8165fc518de |  |
| 2026-11-24T07:20:38.654470+00:00 | retry |  |  | test:item_checklist:polished |  | c920d2832debfc23b733228f58103fe07265b85957ff18252e44fd702df40143 |  |
| 2026-11-24T07:20:40.787237+00:00 | retry |  |  | test:free_form:original |  | 2da6cfbac14202f35eb997635d94bd24bf5bbeb02e137748222293df2baac6de |  |
| 2026-11-24T07:20:42.832016+00:00 | retry |  |  | test:item_checklist:original |  | c6df3a32b37842c613fb906fa099ebede1ed231d2f3535dcf842fbd81d2c62f3 |  |
| 2026-11-24T07:20:43.955131+00:00 | retry |  |  | test:free_form:original |  | 6f81fe1d59beada9af64df021933ce5323fd7e4b19b63043cec01d96130a085f |  |
| 2026-11-24T07:20:44.608420+00:00 | retry |  |  | test:separate_scoring:original:A |  | 5962e4e44b5c3bc1788135683af782f06940f9566ef277fef25d20561aac23a5 |  |
| 2026-11-24T07:20:47.845321+00:00 | retry |  |  | test:item_checklist:original |  | e0710f4abea3831e4f9281e14bea0d63e6010577dd42e18cf13df3c2afc78665 |  |
| 2026-11-24T07:20:51.898822+00:00 | retry |  |  | test:free_form:original |  | 7cd961a7ca45832769670d6d4014f631db82b59a89b1c0d98033ab78ad978e78 |  |
| 2026-11-24T07:20:56.085883+00:00 | retry |  |  | test:separate_scoring:original:B |  | 7cb6a02bbcfec8a40556c6b0d8bc3c562b4ab1a474562ec13b605b07977c7e0f |  |
| 2026-11-24T07:21:05.876029+00:00 | retry |  |  | test:item_checklist:original |  | ab8452c62f11d9c51043d52dd74eb779d8a76a8c1b90a1a894fa466ad96a50b9 |  |
| 2026-11-24T07:21:07.716220+00:00 | retry |  |  | test:general_rubric:original |  | c92c0bf994283199bb509017caee4d6ce8c7627ba5cee2c4366fe821af0bd53a |  |
| 2026-11-24T07:21:09.402432+00:00 | retry |  |  | test:separate_scoring:original:A |  | 8e99cc67a19c375fc7c28f5163275bba43b12b3f46b1d97fe5c6ba920c28d157 |  |
| 2026-11-24T07:21:09.881080+00:00 | retry |  |  | test:exam_prompt:polished |  | d9e801b8ad43888e8517b142d60fca8e55a9cb6fabf4771d481208a319bc50b0 |  |
| 2026-11-24T07:21:19.363425+00:00 | retry |  |  | test:separate_scoring:original:B |  | a47749315b85ad27ff25bd64b22346d918b0fb217200084eb8bb9883dcaed247 |  |
| 2026-11-24T07:21:20.087490+00:00 | retry |  |  | test:item_checklist:original |  | 9e3b5214ac2aa34f434e8facdc41fe78f81e688d9f4f95783be86cae888c3804 |  |
| 2026-11-24T07:21:25.255171+00:00 | retry |  |  | test:separate_scoring:original:B |  | 42b11c03c7c543cd9bbfce4a159fa03339b3f5a6850b20d689fc944448ae930f |  |
| 2026-11-24T07:21:29.416231+00:00 | retry |  |  | test:item_checklist:original |  | 816741b2ccbdfcbe888780f5450237ef86b227d9bcdd8fd6909f9bb00b953aad |  |
| 2026-11-24T07:21:30.650934+00:00 | retry |  |  | test:general_rubric:original |  | 4c375e56111e3947b18a17ce6c85044ffb31495bdccf85bda27511eb6af98678 |  |
| 2026-11-24T07:21:31.408454+00:00 | retry |  |  | test:separate_scoring:original:A |  | 42e6fa84a540504a1f44548362f68e562530a800cbdb6d3ab125561547ec5505 |  |
| 2026-11-24T07:21:32.650930+00:00 | retry |  |  | test:exam_prompt:polished |  | 27b553fa787527aa5ae4cf91e561c8363e8fb15e4b71fae4dd58704042bec414 |  |
| 2026-11-24T07:21:33.931955+00:00 | retry |  |  | test:separate_scoring:original:B |  | 439dad55fce175803f67b0945e6aef2d1d3173369a8eccce52ad5530c1c28858 |  |
| 2026-11-24T07:21:34.735190+00:00 | retry |  |  | test:item_checklist:original |  | dbfd83e7b4188eeb29f6d9263a018958a3a511d3a42706a9811e32f767b9bb7e |  |
| 2026-11-24T07:21:36.665000+00:00 | retry |  |  | test:separate_scoring:original:A |  | 8e9078860e500bebc3693135a76f6f5a96abf887080a8e23d168f905c98404b1 |  |
| 2026-11-24T07:21:41.370811+00:00 | retry |  |  | test:free_form:original |  | c7b350219bf9edf17d8c2390be282c389ead90b2d3f76cff407b31ddea8509ce |  |
| 2026-11-24T07:21:42.423053+00:00 | retry |  |  | test:separate_scoring:original:B |  | 375edc8e431cc8b4fba9c71f5f7144f0564e2b441edb79120b009b6697287578 |  |
| 2026-11-24T07:21:43.234403+00:00 | retry |  |  | test:separate_scoring:original:A |  | 28afe561fe4c88eda434ee79d03dc17a48b67b62c3736e3684566ca31cb15ae6 |  |
| 2026-11-24T07:21:45.104575+00:00 | retry |  |  | test:item_checklist:polished |  | 4100ee2c0193df0284333519074a01e539a2c5f30def0978d4f696293e51c1ac |  |
| 2026-11-24T07:21:46.985716+00:00 | retry |  |  | test:free_form:original |  | 056527743f1ce4cba0338d8d1ef90c572a7fb2272d8f0b06a53ac418e3e80ee6 |  |
| 2026-11-24T07:21:48.932024+00:00 | retry |  |  | test:separate_scoring:original:B |  | 96d23623766f59774200849a6252227c74e6c643c51975bd6c12b9c2e4944189 |  |
| 2026-11-24T07:21:50.876169+00:00 | retry |  |  | test:item_checklist:polished |  | 3c4271de8efb5196179e3490e8e2a63a15aa2eafe868bb228f9f3df93a1b4828 |  |
| 2026-11-24T07:21:53.757253+00:00 | retry |  |  | test:item_checklist:original |  | f5fd6c9df084c9c3aa508771da3634a3b583fa23f42f3f1516293ec9793dbfa9 |  |
| 2026-11-24T07:21:54.679098+00:00 | retry |  |  | test:separate_scoring:original:B |  | a44128688d1e29d266996101d6d756633b2e7526ba15b1600fa36a33183c08f9 |  |
| 2026-11-24T07:21:59.180519+00:00 | retry |  |  | test:item_checklist:original |  | 844438c907a147f609bde82c7a9e32eca4774bde36c2b9af938cdf5d8c1c947d |  |
| 2026-11-24T07:22:01.763016+00:00 | retry |  |  | test:separate_scoring:original:B |  | dbe5f7113a92a7cfa0b96e966bfd630239ba580e8ebcf2804f9adf96fc16f405 |  |
| 2026-11-24T07:22:03.431886+00:00 | retry |  |  | test:item_checklist:original |  | 156a90674e94f186f3ecf59a8341c968437184357264ded36a5d97851b448818 |  |
| 2026-11-24T07:22:05.209766+00:00 | retry |  |  | test:item_checklist:original |  | 646ddcc92b8f7a33779c8177d9a7e962a972e534b6a9aad2c2e8abc33d230020 |  |
| 2026-11-24T07:22:16.694496+00:00 | retry |  |  | test:item_checklist:original |  | 20c3d7ccd35d1f8a57a98fb87e6f05b71fa019d73b8ba7251efeb0b785672d0c |  |
| 2026-11-24T07:22:21.615879+00:00 | retry |  |  | test:separate_scoring:original:B |  | 0036d5692d491d9f50c3d40b67c441cf51e3af3f5045a6927041905c432bbf48 |  |
| 2026-11-24T07:22:30.933638+00:00 | retry |  |  | test:separate_scoring:original:B |  | afed15e1075ea70a9570182008f9cb2d72c3f78123c70c53279c22571942fea4 |  |
| 2026-11-24T07:22:31.078321+00:00 | retry |  |  | test:item_checklist:original |  | 979debf01b0b1d2033a6b9cc546b282c5d4b54c43f14da14f85d54f15297f61c |  |
| 2026-11-24T07:22:32.988372+00:00 | retry |  |  | test:item_checklist:polished |  | a6b9c4f4dd64473601396922cf09696dc4189d60b1ae5d78dcda2fc75105f8ae |  |
| 2026-11-24T07:22:36.970706+00:00 | retry |  |  | test:item_checklist:original |  | fa508bc8c5434c15b56bd2ffda06b23ecce6930934d3305c6c81cafb67a1d75a |  |
| 2026-11-24T07:22:38.780115+00:00 | retry |  |  | test:item_checklist:original |  | 49a665da888f35596562734b7f73e0519a3023a56ff101b6694625862e7451e0 |  |
| 2026-11-24T07:22:40.651655+00:00 | retry |  |  | test:item_checklist:polished |  | 26785f5d98dcd4e263b4a95d875b0275be8d82fe4ba64d39faa4ee22036b5ead |  |
| 2026-11-24T07:22:42.351127+00:00 | retry |  |  | test:free_form:original |  | 88f1cd9058c8a1fdbd263d94336c216f0662cc7244f5878bce3ac9168170e11e |  |
| 2026-11-24T07:22:42.911347+00:00 | retry |  |  | test:item_checklist:original |  | 9927f6ad7253ec8dd816e2198f0b033e09f8bab0f509cbbba7739b6994ea5725 |  |
| 2026-11-24T07:22:44.223586+00:00 | retry |  |  | test:item_checklist:original |  | 722dbb31af13ce633c730de8a7bac9dc4f7a850141eeb089076474896942ed6b |  |
| 2026-11-24T07:22:47.176054+00:00 | retry |  |  | test:free_form:original |  | 41a3ad25a94a41cc7ce55c1967359d4f2b2cd2a8e34bc3045b3d0c6808ce895a |  |
| 2026-11-24T07:22:49.077525+00:00 | retry |  |  | test:item_checklist:original |  | 8a21a15639b96925e1fc35bea38f8f8cc19db0cfc61cd356c9a7a528d494854e |  |
| 2026-11-24T07:22:50.441235+00:00 | retry |  |  | test:separate_scoring:original:B |  | 3b5c09990d8fa3e86cb15cb037e963d9c8a7e6362966d3974f8b8c1d5c84a52c |  |
| 2026-11-24T07:23:06.371196+00:00 | retry |  |  | test:free_form:original |  | cb1fc76467ec99fbe23ac26811b87d0b4aaa1c5e6a87632e9705d88ffc6555f3 |  |
| 2026-11-24T07:23:08.179351+00:00 | retry |  |  | test:separate_scoring:original:A |  | a4eda3b263eae3a3d419d857c2731951daa676ad2dc26a518454873951aa44ab |  |
| 2026-11-24T07:23:08.331132+00:00 | retry |  |  | test:separate_scoring:original:B |  | 8004e7147866c036d2bfc6a7dcf938d4d463300a042957c61cd8d46c5df2b9fd |  |
| 2026-11-24T07:23:08.365786+00:00 | retry |  |  | test:free_form:polished |  | 497f6ba1b63219ad8cd48f67955a39efafebd6107e81af2b46de5922d01928ea |  |
| 2026-11-24T07:23:11.614893+00:00 | retry |  |  | test:free_form:original |  | 6ec502e936e178a651c6615297bf2d7a0a099ab70e436a6c1c7495eea0dde051 |  |
| 2026-11-24T07:23:21.150758+00:00 | retry |  |  | test:free_form:polished |  | 6302a067217d38ac44323fdceddd14c5fa2861e6118cc5c7cc0e7c9f406526d7 |  |
| 2026-11-24T07:23:21.405325+00:00 | retry |  |  | test:separate_scoring:original:A |  | 9507b4807b949d3f436f4f4c8ccb0c088ddd9e8ff56da0ad7562f28b814cbef0 |  |
| 2026-11-24T07:23:21.798123+00:00 | retry |  |  | test:separate_scoring:original:B |  | 7b338373ff0e7cf49066fe60563406ebbad93d702190a01064e5d0e468ebba6a |  |
| 2026-11-24T07:23:22.207073+00:00 | retry |  |  | test:separate_scoring:original:B |  | 0db8d3460902437f733ad88ec2ccfc9bd599a596c008a53d0517300a8f0480c6 |  |
| 2026-11-24T07:23:33.100064+00:00 | retry |  |  | test:separate_scoring:original:A |  | 0a9ee06bc7829b290ea294d14c8f9414e3e94917f6cdcb9ceadfbd6938fd4600 |  |
| 2026-11-24T07:23:37.304528+00:00 | retry |  |  | test:free_form:polished |  | 8141b09bbb1304b4c2acb77d0c82e392690aae76fd3005b1506a41d12210ae59 |  |
| 2026-11-24T07:23:39.496400+00:00 | retry |  |  | test:separate_scoring:original:B |  | 2b48a4a257eee1abb389cb22075202b70102616a6ae82d44ba1b72199f17fd50 |  |
| 2026-11-24T07:23:40.631800+00:00 | retry |  |  | test:separate_scoring:original:A |  | 21c5a41571a5164e71c8a0bd38690a370c677ddab2d2a07dbf7cd562b41954e9 |  |
| 2026-11-24T07:23:50.999403+00:00 | retry |  |  | test:separate_scoring:original:B |  | 85ecf1a4c1a770f4b939a0215fd6fe9af85889737ac4c31cb4f196769e304087 |  |
| 2026-11-24T07:23:54.456987+00:00 | retry |  |  | test:separate_scoring:original:B |  | f848e1b692f4d397cec9f47480ed4b13e9d0729ddfbb9766b68454ebe015b08e |  |
| 2026-11-24T07:23:56.818511+00:00 | retry |  |  | test:separate_scoring:original:B |  | 7ba1926e76bbf24506a1bcf54364c1b7d3ee8898fc937b44446a36fa7c69bf50 |  |
| 2026-11-24T07:24:01.120092+00:00 | retry |  |  | test:separate_scoring:original:B |  | 094253e52bea4a16a4f1273ab935ed8f2830605409d8f52c7f6c39050bff93e8 |  |
| 2026-11-24T07:24:01.146594+00:00 | retry |  |  | test:item_checklist:original |  | 7a8c1031428e06ffdcd24120818a3e38a66904760226eaa1ca66ac533f0e4fc8 |  |
| 2026-11-24T07:24:02.868686+00:00 | retry |  |  | test:item_checklist:original |  | 5a9f4c4f4adf07d99aa5b61bbab2c95391c54a03467da95242c7dbbfb785e0e7 |  |
| 2026-11-24T07:24:07.538992+00:00 | retry |  |  | test:item_checklist:original |  | 65a78f0fe1cb98e9b1bf68fb5b66f90766c9bc16dd3389a1260ba15bff2adce9 |  |
| 2026-11-24T07:24:07.904821+00:00 | retry |  |  | test:item_checklist:original |  | bde7cb0c7f3eac1dafb25497871de3ac4b3e411706200372c87494a846c79bf6 |  |
| 2026-11-24T07:24:14.619227+00:00 | retry |  |  | test:item_checklist:polished |  | 1767acd547bda837ad0e3f4578c698a238962a23e44a2b6b2e297689334eebc7 |  |
| 2026-11-24T07:24:15.213748+00:00 | retry |  |  | test:item_checklist:original |  | ef04c25104f3e160e72837fb0c6ee798da76a96e1020c5afd4abcc5bcef0601b |  |
| 2026-11-24T07:24:16.388932+00:00 | retry |  |  | test:item_checklist:original |  | bd7d8c1118d36adb57ded05256fc9714479741326d1fc73156d349979de24c9e |  |
| 2026-11-24T07:24:21.724498+00:00 | retry |  |  | test:separate_scoring:original:B |  | 9e6046d2f8765d6d2b3f53fb59e2f24c85cf56d26290188eb01004ffab97df38 |  |
| 2026-11-24T07:24:28.891188+00:00 | retry |  |  | test:item_checklist:polished |  | e7ed006c5a409a11e8cc4c3b77a1946a7b2a24d26ef12cd93c293537ed221a71 |  |
| 2026-11-24T07:24:32.027132+00:00 | retry |  |  | test:item_checklist:original |  | c3eec01d09dadfbd3b7ffa79999ed0c736e6c2201f73c0d0e722b2adbbcff2b6 |  |
| 2026-11-24T07:24:35.562203+00:00 | retry |  |  | test:separate_scoring:original:A |  | 26d159d841828eebcb2c1d86feb93e25720d6fbd40e1f785eccc93f594a1e1b0 |  |
| 2026-11-24T07:24:37.594282+00:00 | retry |  |  | test:item_checklist:polished |  | beb841bbd1c8744287ca1ae248fc669aaf266e920757dfb95e0b5317873ca1c3 |  |
| 2026-11-24T07:24:41.604520+00:00 | retry |  |  | test:free_form:original |  | 63ab08c3173029851ab564bb8b8d1fea8355845890c2d19f8cf7c49af778d5ae |  |
| 2026-11-24T07:24:46.106792+00:00 | retry |  |  | test:free_form:polished |  | f4ab5aa65367eddf4b8a8c25c3078812039f37fa30aeb17c96bc519cbb3dcb46 |  |
| 2026-11-24T07:24:47.906609+00:00 | retry |  |  | test:item_checklist:polished |  | 36ff0eaf9ab025c239ad357274a4993d4242335174f4974f1a3a22d25d84abcf |  |
| 2026-11-24T07:24:49.695559+00:00 | retry |  |  | test:separate_scoring:original:A |  | 9282bf569b33715d4f33147d1364e108e63838d41b3a03e437d1ef27e721456f |  |
| 2026-11-24T07:24:51.284933+00:00 | retry |  |  | test:separate_scoring:original:A |  | 03a524b0b779d4f3fcf659c2ba5985660d6e2cbbee7e8eda46924dc910201fc4 |  |
| 2026-11-24T07:24:53.342315+00:00 | retry |  |  | test:free_form:original |  | 1b114f80dc443a33785e82b54d4257791c3ca665a56ac7cfe28b9909923cb936 |  |
| 2026-11-24T07:24:55.326474+00:00 | retry |  |  | test:free_form:polished |  | 7abc916657daea82db785e4640e6fc053ec5f245d5734b310b773172818b1187 |  |
| 2026-11-24T07:24:56.747625+00:00 | retry |  |  | test:general_rubric:original |  | f9e54652729f5c7b4ec87f4533b28f7cdf3e382854a299ccf9af5fa444b5a533 |  |
| 2026-11-24T07:24:57.478197+00:00 | retry |  |  | test:separate_scoring:original:A |  | 15c31e36f452302608e3b12f7eed5494c19e08dbbef449f20566acdcfa2ab945 |  |
| 2026-11-24T07:25:03.272346+00:00 | retry |  |  | test:separate_scoring:original:B |  | d81c463d9fea9fbae08c6726d110a2ab044d4a32f2dead4880a108542a977a5e |  |
| 2026-11-24T07:25:04.864376+00:00 | retry |  |  | test:general_rubric:original |  | e9b62cbc525fb090b3ebb8dccf0da90d2f5999bb4dffc6f41d3f41a6ffc1ab74 |  |
| 2026-11-24T07:25:05.154490+00:00 | retry |  |  | test:free_form:original |  | c8e149fa3ad22adc42093e8c7740e4b4983d58ae5b12cfeca92cff40685897fa |  |
| 2026-11-24T07:25:20.400154+00:00 | retry |  |  | test:separate_scoring:original:B |  | b5d53444b502c75a0b8ed0ef1dd44a9e088fe44463e0bd26ab1fc42211981029 |  |
| 2026-11-24T07:25:23.526297+00:00 | retry |  |  | test:free_form:original |  | 07cbb793e021fabed6a3ef06d1bb38597073192831157642f08ac7a68b408ea0 |  |
| 2026-11-24T07:25:35.127785+00:00 | retry |  |  | test:item_checklist:original |  | dc27b4e56f2e467893fd4b5f4cf134e75d3520f08c53a0ef3439706fe42bc8aa |  |
| 2026-11-24T07:25:40.869720+00:00 | retry |  |  | test:separate_scoring:original:B |  | ce6956a8fc9aa13b50eecd9a621ec0f3f8276caec499196e01fc1d7fdc37bab8 |  |
| 2026-11-24T07:25:42.801854+00:00 | retry |  |  | test:item_checklist:original |  | 49f5b5a61a8844337622506d7be451d517f6c08565f85fa7388079d06490bdcb |  |
| 2026-11-24T07:25:48.081947+00:00 | retry |  |  | test:free_form:original |  | 7dff0dca4828985465b3c31676cb4c8e0aa7183abd787f395f9306a9df6b8292 |  |
| 2026-11-24T07:25:50.206591+00:00 | retry |  |  | test:separate_scoring:original:B |  | bf693a760e7f29b1ef88ce7f6753a9a3e5fb17e4354d4e38c8bbaee8b02452ea |  |
| 2026-11-24T07:25:58.365412+00:00 | retry |  |  | test:free_form:original |  | 8fd8f7843a7dfa24ae8d7ad7da4a782dbc433c0a24c38dd572931f900972eb45 |  |
| 2026-11-24T07:26:03.834585+00:00 | retry |  |  | test:separate_scoring:original:A |  | c86bc6a1caff5a8c12adceb560bf3997c46af733c2e318b734ac2d4f540d5988 |  |
| 2026-11-24T07:26:05.805521+00:00 | retry |  |  | test:general_rubric:original |  | 269c506ad3b8eead8e3569ccdeff632094c43e334d862a2cb8c25535e23bd661 |  |
| 2026-11-24T07:26:07.883504+00:00 | retry |  |  | test:free_form:original |  | eb63e8defe1dce3f8744fa365cee850fed2d5a09f6a7126004510fc0f6aa9b09 |  |
| 2026-11-24T07:26:10.472442+00:00 | retry |  |  | test:item_checklist:original |  | f1bc1f2691ee3487663c8b3c2909faf1d4798f8117d35988de52945c61753b61 |  |
| 2026-11-24T07:26:14.545937+00:00 | retry |  |  | test:general_rubric:original |  | ae2ce75b739ac28a2137662aaf168758af9169273ed8e7e603c243666161d582 |  |
| 2026-11-24T07:26:16.903676+00:00 | retry |  |  | test:free_form:original |  | e4951ef8ee70bb40c583cd025939a971fd1a01f35fc3b4fe20943be276d40082 |  |
| 2026-11-24T07:26:32.574656+00:00 | retry |  |  | test:item_checklist:original |  | 63c5a52cc18df4fd5f7566655090625594bdadd653d15c2203493e241fede1c6 |  |
| 2026-11-24T07:26:33.625365+00:00 | retry |  |  | test:general_rubric:original |  | 293cf4516ef28cdceaea320d2f33b77a91bcf9d14ac79f7fa986313b2fb0b674 |  |
| 2026-11-24T07:26:41.853053+00:00 | retry |  |  | test:free_form:original |  | b7baecacfa01b2aa1b952bc989035c3896db724f3cdbaef551c42fff11091fb1 |  |
| 2026-11-24T07:26:43.967181+00:00 | retry |  |  | test:free_form:original |  | ee5fee792e284e5f3783cc04fadcf83a8f5586c856d7e03bcb1b20690bca482d |  |
| 2026-11-24T07:26:44.223921+00:00 | retry |  |  | test:general_rubric:original |  | 502ea39563216aea036ea5bb88cfd6625c640519d9cf97e70aaae4e6a0916064 |  |
| 2026-11-24T07:26:46.723225+00:00 | retry |  |  | test:free_form:original |  | 174a2cf8d456efbb25bc04fc53ded0ad83418a17fa11249314589842d0bc24e4 |  |
| 2026-11-24T07:26:51.712736+00:00 | retry |  |  | test:free_form:original |  | 8a6ad3893ed40c7c818c5378bfc2572f0c8594a1a58216a3b53656f9ef34f17f |  |
| 2026-11-24T07:26:54.718091+00:00 | retry |  |  | test:general_rubric:original |  | c508ba70c1dc3fc3742d67fa650ac143f142d7a30b8b0ce04dd69e7db38825cc |  |
| 2026-11-24T07:26:59.110703+00:00 | retry |  |  | test:general_rubric:original |  | fdd8e4759f98ae0a10aa933f87e6fe6e8f85fb2ab887bd6f49dc412fc41a1e97 |  |
| 2026-11-24T07:27:01.180195+00:00 | retry |  |  | test:general_rubric:original |  | 97feb38de833542b80875146d8863e1a908fd1efac30499aa6278419d68253a1 |  |
| 2026-11-24T07:27:02.257714+00:00 | retry |  |  | test:separate_scoring:original:A |  | 4c40eaf333d2abd4f61a4f8fdcf39fbe2724789cbe89940764e5f137a2af1778 |  |
| 2026-11-24T07:27:02.358862+00:00 | retry |  |  | test:exam_prompt:polished |  | c7c283f818712156dd6b7b4409507d4ed01f756a7cff223c0b8043f4b1f0e97c |  |
| 2026-11-24T07:27:06.202710+00:00 | retry |  |  | test:item_checklist:original |  | dd30bdd13d2f78ec9c381f0fb9f23a2feed5037016a74c7ade749453165e8aad |  |
| 2026-11-24T07:27:06.771748+00:00 | retry |  |  | test:separate_scoring:original:A |  | 1b808379be039f57d04e43279a999e1b3304adc63119bf3848204336a92eecaa |  |
| 2026-11-24T07:27:07.988410+00:00 | retry |  |  | test:separate_scoring:original:A |  | 4904e5e158139096410a75e3a7ee240b2fb5731be0b6ad866f1fcfd280e172fd |  |
| 2026-11-24T07:27:09.182511+00:00 | retry |  |  | test:exam_prompt:polished |  | 7ce66008f54ed320916fee17b2fb3d47a9c3bbb6915337aad9da811f902d567e |  |
| 2026-11-24T07:27:11.061993+00:00 | retry |  |  | test:item_checklist:original |  | bd227ffd3811b471750519e7376c6a1388af7b61fd840b905ea53cc0cb911dc8 |  |
| 2026-11-24T07:27:11.688180+00:00 | retry |  |  | test:general_rubric:original |  | c01248fe445ad4a9b6090fbbc2559b3f331908f7ccf3d4518dd85270b230a865 |  |
| 2026-11-24T07:27:21.227320+00:00 | retry |  |  | test:separate_scoring:original:A |  | d9d99e5cf2c004a701fab594f26db88102a77835d21bb65e84ba53953e611c3e |  |
| 2026-11-24T07:27:21.837119+00:00 | retry |  |  | test:separate_scoring:original:A |  | c5dc534ccee06b77f91d5913d1ad5d054e0f3b71440475cf2b4e9fa6ed891825 |  |
| 2026-11-24T07:27:30.847396+00:00 | retry |  |  | test:general_rubric:original |  | 51e6141626121eb8cf28904a5006793e4918f7aedcee38105747f91d77e424ed |  |
| 2026-11-24T07:27:33.660141+00:00 | retry |  |  | test:free_form:original |  | b23fa9f866c4d21c5a94e10c50bf2cbd774fcb34cccefda41f2fd0edd3d9f75c |  |
| 2026-11-24T07:27:36.048593+00:00 | retry |  |  | test:general_rubric:original |  | 2e25ec79048067f124e04cbaf2ed2601d8822a69bee22b596f58c00a1979849e |  |
| 2026-11-24T07:27:36.653118+00:00 | retry |  |  | test:item_checklist:original |  | b5b0d269debf23188acc90c992818321ccab70dcc2e4a0144a32fb95668987db |  |
| 2026-11-24T07:27:37.245187+00:00 | retry |  |  | test:separate_scoring:original:B |  | 75289f403e82563ebf7c6604a256cb93b5b77af32c58acb267b0f60d8b8dcf7e |  |
| 2026-11-24T07:27:38.439602+00:00 | retry |  |  | test:separate_scoring:original:B |  | 75e8b82f338d2736cb64025e7f26aac8a9f2405a37a00c6dd5114badb370b6e1 |  |
| 2026-11-24T07:27:38.945738+00:00 | retry |  |  | test:free_form:original |  | ccf9bc6542184798c8ffb86678063ce8c83e84c96a07d953ba064f115c9c15e4 |  |
| 2026-11-24T07:27:41.658691+00:00 | retry |  |  | test:item_checklist:original |  | d7ee4e348c425f64a223d4b5d66093642bcfdd203a97a4d89eea1b6f053209bb |  |
| 2026-11-24T07:27:42.627687+00:00 | retry |  |  | test:separate_scoring:original:B |  | 66748cdc906ef7781f29670ac755428c892ba649aa5c270499f3acc9c036301e |  |
| 2026-11-24T07:27:43.511438+00:00 | retry |  |  | test:separate_scoring:original:B |  | 4c8012084b5306593f377079e37f33093c92a4cb412187ca0df00440d0b7df30 |  |
| 2026-11-24T07:27:56.155763+00:00 | retry |  |  | test:general_rubric:original |  | 22cf72eca3cd6f4d548e96bb4bfcaa04478dc6bfb7b514b078522eae38e01e6a |  |
| 2026-11-24T07:27:57.848717+00:00 | retry |  |  | test:exam_prompt:polished |  | d499021635c0d4eec5228f960ce7c181c9476fb2f41d6e3afbb3cbacf8407093 |  |
| 2026-11-24T07:28:02.650016+00:00 | retry |  |  | test:separate_scoring:original:A |  | 07ee87c2ad2c3d0ffcba37de864f55d47619afc681695be09ea984681a4fe6b3 |  |
| 2026-11-24T07:28:04.908934+00:00 | retry |  |  | test:exam_prompt:polished |  | bfce289b2af4c8d174a858b1e4f82074e6dbbce1d88cfe41302eb706a7cb9d4d |  |
| 2026-11-24T07:28:05.225782+00:00 | retry |  |  | test:general_rubric:original |  | e0164134028bc039c61ed784e824254fbd2a4f6a82756a3d062d011826c028a8 |  |
| 2026-11-24T07:28:07.618458+00:00 | retry |  |  | test:separate_scoring:original:A |  | ce94d0cc76ea1a7627bb68529e9893368749351b2d42282aaff4ac6a296b440b |  |
| 2026-11-24T07:28:08.121698+00:00 | retry |  |  | test:free_form:polished |  | d201e1d4ce812f9987d178fc04a7b1172e02ccbde3d9276e5a18f4a69f5f6591 |  |
| 2026-11-24T07:28:13.289655+00:00 | retry |  |  | test:free_form:polished |  | 67920dd714d5371234ce9902b83ef491f6c4c5117c8f4b57152fda8a392c193a |  |
| 2026-11-24T07:28:35.403431+00:00 | retry |  |  | test:separate_scoring:original:B |  | 035714772bd5ecb5f5f4b19c4a0ac3eba985ab3b8d0c3c12dcca5393c3e6675f |  |
| 2026-11-24T07:28:37.175613+00:00 | retry |  |  | test:general_rubric:original |  | 31c934ba8c4b3fdc2ccee140531a258c0a1df610d1d4553a00575687ddb411e2 |  |
| 2026-11-24T07:28:38.188847+00:00 | retry |  |  | test:separate_scoring:original:B |  | faab24e88e8e310add04d40b696dc97e8009d4df17d0b02341b6bed5a945aca6 |  |
| 2026-11-24T07:28:40.327379+00:00 | retry |  |  | test:separate_scoring:original:B |  | 1726f85a3f69e60209c0ee156ee07d91537857c9fa8bd93ab07fd2adb4504345 |  |
| 2026-11-24T07:28:42.092277+00:00 | retry |  |  | test:general_rubric:original |  | 216e7dd09213a3000c0ba40197163fa625cd4d1b679c6421d6be951fdd64285d |  |
| 2026-11-24T07:28:52.435495+00:00 | retry |  |  | test:item_checklist:polished |  | 7a91f25750c3e07608bbd8a839d868c699ea04cbb2b51d7e9cbee91613509c3b |  |
| 2026-11-24T07:28:59.136935+00:00 | retry |  |  | test:free_form:original |  | 3a8e3cd0493c63cd651c5eed6b367ddfd5d15914e53c979aaf77c567768a1684 |  |
| 2026-11-24T07:29:00.665186+00:00 | retry |  |  | test:free_form:original |  | 7d9f1f376807b887f4a735942a9e0b6759971cf9bbc29d5e3ff31517ef15d9c4 |  |
| 2026-11-24T07:29:01.041009+00:00 | retry |  |  | test:free_form:polished |  | 0172e397630435c40c2e382840033ee0f17018f78be17b62aaf326b1f5914446 |  |
| 2026-11-24T07:29:03.025270+00:00 | retry |  |  | test:general_rubric:original |  | fb7b60c436919d43ab44702d2cd9ee3df228bfdba00201fb2243641761fb5d90 |  |
| 2026-11-24T07:29:03.094208+00:00 | retry |  |  | test:item_checklist:polished |  | ada2df624fd76db30c962af855d7a63b33511ac7f6a10c46941b9cbbe5c802b8 |  |
| 2026-11-24T07:29:05.007646+00:00 | retry |  |  | test:general_rubric:original |  | 6ba9b291f29afa580d47559966a2d01705d9d325c964a503310b4e47ae62ae55 |  |
| 2026-11-24T07:29:06.984446+00:00 | retry |  |  | test:free_form:original |  | 37694c4d6263bd33482a3ff63b1f6a77eb0e2e207527e22d26ed0a9bb25de6ac |  |
| 2026-11-24T07:29:08.941029+00:00 | retry |  |  | test:free_form:original |  | 916e27cae3b1da84e558d36f2fa19b586dfde79180f6b4852dc904b9100d400a |  |
| 2026-11-24T07:29:10.085512+00:00 | retry |  |  | test:free_form:polished |  | 0ccf99591645951a2dfe5892ce7e01c336fb9a43718cd79fcbacb4d941b182fc |  |
| 2026-11-24T07:29:11.080341+00:00 | retry |  |  | test:general_rubric:original |  | 56896538f903bbf22f7d27df8fade39e850d17a46e3beda3825062ec6d0133ed |  |
| 2026-11-24T07:29:11.963318+00:00 | retry |  |  | test:general_rubric:original |  | 890fefa71b32dc030e64cb5d187118629a42e85a0795eb0c65038ed0da4ef634 |  |
| 2026-11-24T07:29:25.188817+00:00 | retry |  |  | test:separate_scoring:original:A |  | 673a9b6246b1d14bc82d4dbb3e4a5080009fad2a19edf74b7e2077da9a6c1710 |  |
| 2026-11-24T07:29:34.875096+00:00 | retry |  |  | test:item_checklist:polished |  | 72643b80069956b8699bf6a0aa22066b5c9d83f35fec028926f0777f9f747acc |  |
| 2026-11-24T07:29:38.681274+00:00 | retry |  |  | test:separate_scoring:original:A |  | 77046a5182124c1be75c14b809252b38096ec105432aab4503a023340fe5aefe |  |
| 2026-11-24T07:29:38.885123+00:00 | retry |  |  | test:general_rubric:original |  | cee86dc75b090c678752cbc60a375e3f053c265031532dd5fba6d9a29bb5394e |  |
| 2026-11-24T07:29:44.537691+00:00 | retry |  |  | test:free_form:original |  | 7e628b5da74dc6295edd2adb08adad9acda55086c19627156716d9d9ddab3c95 |  |
| 2026-11-24T07:29:45.524579+00:00 | retry |  |  | test:item_checklist:polished |  | 7ba12c423ff398366cc9f12e6f8b2be16a4d628086528dc509152c38cda62e04 |  |
| 2026-11-24T07:29:46.508941+00:00 | retry |  |  | test:general_rubric:original |  | 29763553cd4e5dd44191557caf924448c3ab280699e45a4268c273bd2976058e |  |
| 2026-11-24T07:29:49.335749+00:00 | retry |  |  | test:free_form:original |  | 51b0c1d820119d95a30edd1838681b7fb35c94cbb3bc2ec7387f41a0523b5607 |  |
| 2026-11-24T07:29:51.288840+00:00 | retry |  |  | test:separate_scoring:original:B |  | edfeb16f4f8bc032a94b3b4e45709232bcd67e47adb5078b190b427282445b32 |  |
| 2026-11-24T07:29:59.749521+00:00 | retry |  |  | test:exam_prompt:polished |  | 60ec8904213c02eff4c79873f744acb592b851eaf64c209bc6ca561877ad9754 |  |
| 2026-11-24T07:30:01.223972+00:00 | retry |  |  | test:separate_scoring:original:B |  | c716d19c8e9a0d549f9236de7f678462108b1635df0aa631bcc3c986fe8355d4 |  |
| 2026-11-24T07:30:02.165712+00:00 | retry |  |  | test:general_rubric:original |  | 36a9d89ca33b47b335983cbb964485995311a3f34cec428f90ead042204d92d4 |  |
| 2026-11-24T07:30:02.997495+00:00 | retry |  |  | test:general_rubric:original |  | 33b0998a507f3e2830ef9a91e69b0b66d1693a63a95d79ae3f18b13e2de192d2 |  |
| 2026-11-24T07:30:04.202167+00:00 | retry |  |  | test:general_rubric:original |  | 9cca1147634fe46cdb1cc3f92b7d81688db74eb714a09333794befe4c2c0da7e |  |
| 2026-11-24T07:30:04.841678+00:00 | retry |  |  | test:item_checklist:original |  | 2763242ac824115fcfd7a39d46005092cf1509f080977cf883b0be261dd700f9 |  |
| 2026-11-24T07:30:08.278616+00:00 | retry |  |  | test:general_rubric:original |  | 3b4dd85d1e767d321aa04c46f27b548b2dd9e60d99738cee1e894abcf070da82 |  |
| 2026-11-24T07:30:09.169090+00:00 | retry |  |  | test:general_rubric:original |  | 112bc4ea28a150b0e3ef7365f32ad7559b8c097a80bab64075c778ec0f9c768d |  |
| 2026-11-24T07:30:11.136066+00:00 | retry |  |  | test:item_checklist:original |  | c7fc956bafb417e7e3ed5efea22c1d45d17809f2604802b4b3b228e69b8fef2a |  |
| 2026-11-24T07:30:12.407306+00:00 | retry |  |  | test:free_form:original |  | 06106288f4ffde84ec7fe2e374c13d079805c885912ffb3733c6993e3c5632ea |  |
| 2026-11-24T07:30:34.006196+00:00 | retry |  |  | test:exam_prompt:polished |  | 8321b4200b29a1394745bf480554f188e07f54e80f64b14e8b5e1b616f3bef03 |  |
| 2026-11-24T07:30:35.166996+00:00 | retry |  |  | test:free_form:original |  | a1c9d05f2d811ae9456c600e3776b59040f94f4f446d21e9646e192abff773c6 |  |
| 2026-11-24T07:30:38.758942+00:00 | retry |  |  | test:item_checklist:original |  | 7cd02da0b178cf922dc04a25e0479d6c5b5da26ea3ecef3dd69de0759c732fa6 |  |
| 2026-11-24T07:30:41.029547+00:00 | retry |  |  | test:free_form:polished |  | 36ea1538894bfd82f10963e37b5810acfa4275fd7a7f211fda20f8d2316e8020 |  |
| 2026-11-24T07:30:42.743946+00:00 | retry |  |  | test:free_form:original |  | 40fc82be8767e0c162d4ca219b54328781c6d1fa44dca730f72d84f94b2a00fc |  |
| 2026-11-24T07:30:43.364742+00:00 | retry |  |  | test:exam_prompt:polished |  | 757449d44cdeb81ab264001d6a50eb41e13c1edb0a3974285254f5e71465fc0b |  |
| 2026-11-24T07:30:47.337410+00:00 | retry |  |  | test:item_checklist:original |  | be143a2f259657ab3bbcb4faf80e18a82721eb6b384695f76b3a08c9035584c5 |  |
| 2026-11-24T07:30:48.629069+00:00 | retry |  |  | test:free_form:polished |  | 0d0d65996b29a39447da2f326099adc7f9bd62aa14b5a9d8ec494cfdc8d6877a |  |
| 2026-11-24T07:30:49.088170+00:00 | retry |  |  | test:free_form:original |  | ff3e49b7f340c0a4522e5eb9c35de734c1984753152376a10ba2c7bb5f7d8c61 |  |
| 2026-11-24T07:30:50.455758+00:00 | retry |  |  | test:free_form:original |  | 954346e039eaeefea81d3c0ab38def48a21f347888fb7e83fed001c084dc8eef |  |
| 2026-11-24T07:30:51.077139+00:00 | retry |  |  | test:exam_prompt:polished |  | 5fdd96b30b75fdb284172c4a4200b20ba10aae21fb9f83a4a140254f1707602e |  |
| 2026-11-24T07:30:52.508886+00:00 | retry |  |  | test:general_rubric:original |  | ff54bfe41954af3b72eda5faf0a5d9161a7928a2d2aa29dfa0d42fa61f11bb7c |  |
| 2026-11-24T07:30:54.060361+00:00 | retry |  |  | test:free_form:original |  | df12e1ad81fb1d5734f4090cb8099f3de38422d53dc4eba80063ff325d696865 |  |
| 2026-11-24T07:30:57.807902+00:00 | retry |  |  | test:general_rubric:original |  | 1df8b3bc2deb03ed9846088e7b754068b59d9d4c321c65ed52f1d833e0da5fb8 |  |
| 2026-11-24T07:30:58.539333+00:00 | retry |  |  | test:own_requirements:original |  | c57c7d394b96b6302f7a74eede649343e7ea1a85b71029db6b8bb6dc3c387d0c |  |
| 2026-11-24T07:31:03.853969+00:00 | retry |  |  | test:own_requirements:original |  | b3f9484f4eb6b79f7b6b68d854b6eae5111aece393446ce9bc7d4cfbf61a0118 |  |
| 2026-11-24T07:31:06.038493+00:00 | retry |  |  | test:free_form:original |  | f4eadb0e236b714b86a296d3e135ae4ab11e6b0a100a27ef82a1922661ec61da |  |
| 2026-11-24T07:31:21.971899+00:00 | retry |  |  | test:item_checklist:polished |  | b247bd7c264a41742fe6a2ac06c573e6fe08fdf821759ee7eead408cbc019a47 |  |
| 2026-11-24T07:31:23.973428+00:00 | retry |  |  | test:exam_prompt:polished |  | 6140fb28e4875ec6400a98e287b4f6eacbb4ac50b0670679da1c30b97d09b3e6 |  |
| 2026-11-24T07:31:35.601255+00:00 | retry |  |  | test:free_form:original |  | 5166e79a7327c05e12cda2af842bd4e1d87cf13190c265dfcba44f07ad0c0c8f |  |
| 2026-11-24T07:31:37.848995+00:00 | retry |  |  | test:item_checklist:polished |  | ce2140af0e45fb0461589302e1ccaf51c2f4c3dd5670e3493a594279a8a14a9d |  |
| 2026-11-24T07:31:39.749427+00:00 | retry |  |  | test:exam_prompt:polished |  | 1da3e8f3e6cf3fd86c42fc2b81fbcbca68e2bd7579202c39b8c65c99597286f0 |  |
| 2026-11-24T07:31:39.891669+00:00 | retry |  |  | test:free_form:original |  | 03f2c9c281931487bb65a4076fd3deb3b933573ca8e39546d52c5c9c6d79a540 |  |
| 2026-11-24T07:31:47.320608+00:00 | retry |  |  | test:free_form:original |  | 7cbbbcb7dc14f13980e80b5b891e987ae136219b9910b5a1bff363555da97507 |  |
| 2026-11-24T07:31:52.416165+00:00 | retry |  |  | test:item_checklist:original |  | a137fd061b6779994239f9dfa994f6630f157426618657de6318dd2d9c1bb895 |  |
| 2026-11-24T07:31:55.018703+00:00 | retry |  |  | test:item_checklist:polished |  | 0ef2862641ca1a2baa85c50bd15e0a7923587523e0724ccc60daa4990ebb70dc |  |
| 2026-11-24T07:31:56.701707+00:00 | retry |  |  | test:free_form:original |  | 2a2010f4f8e1828e5013043949654127b7b471c7936a6c4b473dbcf85a3dceac |  |
| 2026-11-24T07:31:56.917549+00:00 | retry |  |  | test:free_form:original |  | 7f8879953761b1ac75353d2ed58ec5021123cadf680dd6641cc3ef64808e3b04 |  |
| 2026-11-24T07:31:58.551916+00:00 | retry |  |  | test:item_checklist:original |  | 5999bf3370c99d26febd6b7d2830747f9a3e8fdf4ac5cfa9f7987e341db7ba15 |  |
| 2026-11-24T07:32:00.504395+00:00 | retry |  |  | test:item_checklist:original |  | ae071d188931c1c7fc92fb91ac79f70991e9de8ee540f9d6c374bbc284f0b16d |  |
| 2026-11-24T07:32:00.812154+00:00 | retry |  |  | test:item_checklist:polished |  | b2babf63ebeaf8b324fea0f73058bc33881bdde1a334f07f46d4f02eee0c9d94 |  |
| 2026-11-24T07:32:02.622027+00:00 | retry |  |  | test:free_form:original |  | 2ccd2bea6ab008a3b8165b808517efb1c57f2c1fa55f2d035d9bcc7e29822321 |  |
| 2026-11-24T07:32:02.704956+00:00 | retry |  |  | test:free_form:original |  | 3beee400456b3bd33942f64d969f41f6a0433d77f9f596c50818bc96a7e69fc3 |  |
| 2026-11-24T07:32:04.559783+00:00 | retry |  |  | test:item_checklist:original |  | 501558e805a530c505fe89a944fb7268c3896e5f72e860190f41b71564ffef2a |  |
| 2026-11-24T07:32:09.253361+00:00 | retry |  |  | test:free_form:polished |  | c6cb4564073d186266094193f3cc15965f59747c3fce063cb53872740da3c66d |  |
| 2026-11-24T07:32:35.545504+00:00 | retry |  |  | test:free_form:polished |  | 60c39d0012a123c963a1f571ffc4c1217a0a3f4a9c1459a1d852c5b5f03c5ab6 |  |
| 2026-11-24T07:32:38.998758+00:00 | retry |  |  | test:exam_prompt:polished |  | dbac5eb37d5e5948a674ea144fb0acef742a63fb1a68022ffcad29bed0c7a67b |  |
| 2026-11-24T07:32:42.123263+00:00 | retry |  |  | test:free_form:original |  | b7e30958c21b0f928c4692625d87db32e88085e9ebe36babfd8faea9cc394ec5 |  |
| 2026-11-24T07:32:44.807268+00:00 | retry |  |  | test:free_form:original |  | 6bf73b73dabeda0c51a64af420460e92e49260b736c78a5389701745dbbd5843 |  |
| 2026-11-24T07:32:50.077945+00:00 | retry |  |  | test:exam_prompt:polished |  | 6e24d12a87d099d16259c76d051feafbd82b6a6ff3aaeb3f7587b95f218bae08 |  |
| 2026-11-24T07:32:52.604140+00:00 | retry |  |  | test:free_form:original |  | 934b7ff8a1db4ed6635107cbe7b4cd5f69bd85224100d55e00b85b3ed926a063 |  |
| 2026-11-24T07:32:54.450334+00:00 | retry |  |  | test:item_checklist:polished |  | d973882beeb59200295147b949a9d3906cce3cb1a3c112b2f7d1aa0b0aa9afa9 |  |
| 2026-11-24T07:32:55.609872+00:00 | retry |  |  | test:free_form:original |  | 12fed52f1498b24071b2ebc4a997dbab86117dd6fdfcd3901ef7a6b0559ca675 |  |
| 2026-11-24T07:33:14.803931+00:00 | retry |  |  | test:item_checklist:polished |  | 46027976e3b4d66ef918ea218f153240d2751a945c99094e21d95b0a280b6d7d |  |
| 2026-11-24T07:33:16.686256+00:00 | retry |  |  | test:exam_prompt:polished |  | d1014baef59b6a84e27334b182569cba42564e5dccef9ecc8c3fdc70c9160ed6 |  |
| 2026-11-24T07:33:26.675174+00:00 | retry |  |  | test:free_form:polished |  | d262ca11cbe5181cf795e2d480455d0f0d7a5239ba10a1661ff6caa5f65b9359 |  |
| 2026-11-24T07:33:36.681025+00:00 | retry |  |  | test:general_rubric:original |  | 1519847dc1bc114ea8734a7d87901a5bfeeb81a631c32c73584ecae682342115 |  |
| 2026-11-24T07:33:39.662182+00:00 | retry |  |  | test:exam_prompt:polished |  | 02041c1eebbe345a7fcbc08c4ee52c18340131ef85dbdb74f6e22f0c7dea367c |  |
| 2026-11-24T07:33:50.071918+00:00 | retry |  |  | test:free_form:original |  | 90b9fa35421ec4c88734520309ff9e39485e03e59bc8ca6d96a195ca1e10595d |  |
| 2026-11-24T07:33:50.735323+00:00 | retry |  |  | test:general_rubric:original |  | ecf046dbd175d13e5cf29a029681ad8b2e3a1ddbf23a13682f91d1ca3aed44b0 |  |
| 2026-11-24T07:33:54.502350+00:00 | retry |  |  | test:item_checklist:original |  | ee66e5283db352e69b3cf558f8d356571a62cde72c81a9229f8ce47d25e0ae4b |  |
| 2026-11-24T07:34:00.863711+00:00 | retry |  |  | test:general_rubric:original |  | 3da7c5b389ae7ec99dd6038bfb27c123fd2d65c803096fd9b64908086dae63f3 |  |
| 2026-11-24T07:34:01.884884+00:00 | retry |  |  | test:item_checklist:original |  | d23ceb7319036cf1d32c9d1ef7bce7541e0b9ae522f1a3595ed7ffa46f42f600 |  |
| 2026-11-24T07:34:02.654753+00:00 | retry |  |  | test:free_form:original |  | 7dfd77892dbdd9300b673bfb2bc61e447cc9aff02d1d23c2b3eed4abb0fa2c11 |  |
| 2026-11-24T07:34:04.767730+00:00 | retry |  |  | test:item_checklist:original |  | 0b13135a479c7cc3f7d2987b1de0f83f060dd4475c20d0f5ecccafa166ab39e0 |  |
| 2026-11-24T07:34:05.794802+00:00 | retry |  |  | test:item_checklist:original |  | 73bf55dfb38a695cfd7477aafc8a2b7edfd8bf7797725f39c6bca5391f1a4fce |  |
| 2026-11-24T07:34:07.770430+00:00 | retry |  |  | test:general_rubric:original |  | e6c9b4a6668b73df45dcb6d36995752be59087d7fd4ee30c00fd44a5cf6181a7 |  |
| 2026-11-24T07:34:10.583159+00:00 | retry |  |  | test:item_checklist:original |  | 25933b30c1c996d0f1f09148b715bc983be1b2218b59a247879b6e9afbb61149 |  |
| 2026-11-24T07:34:14.335142+00:00 | retry |  |  | test:separate_scoring:original:A |  | 29f03062a68c991a75d1aef2b0359a7201711b9d3358764a16806c5823885bde |  |
| 2026-11-24T07:34:14.538115+00:00 | retry |  |  | test:item_checklist:original |  | fd099d5e0855299c4a59ef07cd6aedae8c9df67d1903c8dfc6a92a662c33cdf0 |  |
| 2026-11-24T07:34:30.896643+00:00 | retry |  |  | test:separate_scoring:original:A |  | 8a9b8d62872c33fe009ad544915b2cef252e9c47c4352497369388ae06e4087e |  |
| 2026-11-24T07:34:44.243037+00:00 | retry |  |  | test:separate_scoring:original:A |  | f24ce3e2529260364c6b8d79836fb58875b0d83f614b059ea9935be4fe97284d |  |
| 2026-11-24T07:34:51.970037+00:00 | retry |  |  | test:separate_scoring:original:B |  | 3c756bb5a908e45e36712936bb2d85d7acec7d23b7256b887f6af51f1967713b |  |
| 2026-11-24T07:34:53.916118+00:00 | retry |  |  | test:item_checklist:polished |  | 3e419c7e6a760be19c031f29769baa76b812a75e371671d88f8c595a98ddeeeb |  |
| 2026-11-24T07:34:55.353090+00:00 | retry |  |  | test:separate_scoring:original:A |  | 824ce72e8a80cac4668cac2e9c9f3b6f7fc9c7368d412aacdb065c355a33240d |  |
| 2026-11-24T07:34:55.823713+00:00 | retry |  |  | test:free_form:original |  | 8780c1d4dfd68d417540f74e891b2e0448c57123847ed511f74bd95fec2c64c3 |  |
| 2026-11-24T07:34:56.035417+00:00 | retry |  |  | test:separate_scoring:original:A |  | f736f57bdc367004efa558ae257733a09a989d0faa0b1151f878e69ac0ebf5af |  |
| 2026-11-24T07:34:57.764440+00:00 | retry |  |  | test:separate_scoring:original:A |  | ed01008390d7445a98b3fab430fe7aefdfc0e78746bc9629ab575c36cded81a4 |  |
| 2026-11-24T07:34:59.848194+00:00 | retry |  |  | test:separate_scoring:original:B |  | 81774ad90ace928cb6e4c4372b708b3120555332908c8dae660dd13b5137eaee |  |
| 2026-11-24T07:35:01.764602+00:00 | retry |  |  | test:item_checklist:polished |  | 3fca066cc7cf51daa815b6a9b3533f91745f83a9b87746c1afddfbffaa7dc2cc |  |
| 2026-11-24T07:35:02.786636+00:00 | retry |  |  | test:free_form:original |  | b3a68fb26e29bd0603355d0e13829be48173ff7baeffd569eeaff8d7c1924bba |  |
| 2026-11-24T07:35:05.119396+00:00 | retry |  |  | test:separate_scoring:original:A |  | 0471958ce8c99a518a1910f68640a4376a680a0826002da02614fdb51c87185e |  |
| 2026-11-24T07:35:09.060478+00:00 | retry |  |  | test:separate_scoring:original:B |  | 28380b21f1757ce03bc2a6c6687fd316429d5ce9271f13efe4d8d1cc72e8d367 |  |
| 2026-11-24T07:35:15.379804+00:00 | retry |  |  | test:separate_scoring:original:B |  | f7fd42dd9a6dc0350bb0b1b8bed1c443bdf73ea0a088d81ebaff811583f9abbb |  |
| 2026-11-24T07:35:25.850945+00:00 | retry |  |  | test:separate_scoring:original:B |  | 3435f84ea828bd25a79f3daea585c411249103a487ca25e707b0272b424ffd46 |  |
| 2026-11-24T07:35:32.279641+00:00 | retry |  |  | test:item_checklist:original |  | 48189ac62231fca394629895cb6cf46554d0989f04f9cebdb9f44809f393921f |  |
| 2026-11-24T07:35:36.044500+00:00 | retry |  |  | test:free_form:original |  | afa8ee168291e155fdc2e6cc2cd9f9f5f4c6df285b476e2a97124d8c77018507 |  |
| 2026-11-24T07:35:36.414516+00:00 | retry |  |  | test:separate_scoring:original:A |  | 934a3885ce251326d3823e7cf15c5e678869bc1ece7625d682d1f3e06ead6a56 |  |
| 2026-11-24T07:35:38.667861+00:00 | retry |  |  | test:separate_scoring:original:B |  | f8f99dfc9840271e6a3cca5b846834174487192d72be24c582e7eff7eeea2bce |  |
| 2026-11-24T07:35:42.590537+00:00 | retry |  |  | test:free_form:polished |  | b6916c1ddb448e7f3dacb6ef3548ab1f2370f2b933d38b11e61c1cec38e72b49 |  |
| 2026-11-24T07:35:44.154183+00:00 | retry |  |  | test:free_form:original |  | e45b1b34248e83e2828f3138511f27a2ecceaa8640ca8cf5900b5d3998b71327 |  |
| 2026-11-24T07:35:45.973998+00:00 | retry |  |  | test:separate_scoring:original:A |  | 6f5855b8b98ab598d8fbc06ba182e06480720245c41abf7597b41d86100e34ae |  |
| 2026-11-24T07:35:49.597225+00:00 | retry |  |  | test:free_form:polished |  | ce7893a65680cc692931ba6034a1735e4283b2c625131a63d3591e7a832eddb1 |  |
| 2026-11-24T07:35:51.506031+00:00 | retry |  |  | test:separate_scoring:original:A |  | a5b016b533503e4cdd8561be69fd4b27ee9501229ff0368e12ca38b5cb3ae063 |  |
| 2026-11-24T07:35:55.037501+00:00 | retry |  |  | test:general_rubric:original |  | 370469061e418c0c4ad7d5e3ed253a83248e0084ff5b5971d3c8501801e6b498 |  |
| 2026-11-24T07:35:57.018514+00:00 | retry |  |  | test:exam_prompt:polished |  | 39e011fa1ea7b31ca190cfab81cea78e1b540825d716b52c504d8842a5ebcfd7 |  |
| 2026-11-24T07:36:02.484791+00:00 | retry |  |  | test:separate_scoring:original:B |  | 73177ee9a58832bb40a7a263285b1caeb336c04da4ba3ce3d42de089f2447a59 |  |
| 2026-11-24T07:36:04.018776+00:00 | retry |  |  | test:exam_prompt:polished |  | c20e33ded1e0b24a783c0cc3a58c0bb682a3ee05a8088eff3b36a30f22e3172a |  |
| 2026-11-24T07:36:04.464172+00:00 | retry |  |  | test:general_rubric:original |  | d5104c5ffdba0202a60b0f930a58a89c62497dae69b5579a9996b44d8691069c |  |
| 2026-11-24T07:36:07.518624+00:00 | retry |  |  | test:separate_scoring:original:B |  | 3753eb5c8def10a5bea5a97c94b00dc9ac060e8b3a1e5d1f6ff610ab20b7da69 |  |
| 2026-11-24T07:36:11.830569+00:00 | retry |  |  | test:free_form:original |  | 281e638bad083f295e2b25ce600392e1b7725c3b77fea01216a14377a8ca942f |  |
| 2026-11-24T07:36:12.411531+00:00 | retry |  |  | test:exam_prompt:polished |  | c35f98dc067ec4eb0c18677ab6088b068034991d5442e6c3d3edad80b1e8c5f6 |  |
| 2026-11-24T07:36:16.732904+00:00 | retry |  |  | test:free_form:original |  | 6991a86c2d0a40e81766df1065a409833f8cae4bb033a697d04607d11ac0de59 |  |
| 2026-11-24T07:36:17.441092+00:00 | retry |  |  | test:separate_scoring:original:B |  | ac78ed9a39ed51f985534181b9967b4005112917318ed920dc27665f6a99ed86 |  |
| 2026-11-24T07:36:34.799224+00:00 | retry |  |  | test:free_form:original |  | 2310e08dcaa6983cdc85f6619987f0c268b7c2cf984a26d81ea95279fedd6dbc |  |
| 2026-11-24T07:36:36.644901+00:00 | retry |  |  | test:general_rubric:original |  | b77d3627c914439b0f20b6847775af76db0a9ad0b7e29292047da33cd7e136d5 |  |
| 2026-11-24T07:36:43.113660+00:00 | retry |  |  | test:separate_scoring:original:A |  | 400aa717d1b577d7945a6d433ca23005e0cea2e0035b7b5d2d9f99049b775400 |  |
| 2026-11-24T07:36:44.676983+00:00 | retry |  |  | test:free_form:original |  | 55d3f0a396c8e0a17c68ad65a7769663aeef90c713ce848f0caa54c91a673507 |  |
| 2026-11-24T07:36:44.978955+00:00 | retry |  |  | test:separate_scoring:original:A |  | a7a38b4fd2dcf562047043309d0eae521ac840cd795d734afe57eea660d6d818 |  |
| 2026-11-24T07:36:46.696960+00:00 | retry |  |  | test:general_rubric:original |  | 18e5af7a0ddc3b994cd45d68de8f4fdcff71b08effda16c8e82e1f9d09ef6637 |  |
| 2026-11-24T07:36:48.449869+00:00 | retry |  |  | test:separate_scoring:original:A |  | 24498c06cfa25ca11020d9cc1a986333b28f3154f8dd2843637512ab41e8885f |  |
| 2026-11-24T07:36:50.289171+00:00 | retry |  |  | test:free_form:original |  | 91f0b98e0d72a1da71bbb32fd6fb42ea98fe39f20daab2539315920aff999a8e |  |
| 2026-11-24T07:36:51.988263+00:00 | retry |  |  | test:separate_scoring:original:A |  | c6296e0e4b5bd9040c594e9e24faa55984bf9a86efc377a8f1598cf31e1baaed |  |
| 2026-11-24T07:36:53.166714+00:00 | retry |  |  | test:separate_scoring:original:A |  | 66b8da61359210e07c05b61e1eace5ef828ee8a4799dc1c2adf88ff15c70e08f |  |
| 2026-11-24T07:36:56.696818+00:00 | retry |  |  | test:item_checklist:polished |  | 587233d93c979bd3870e56faacc2a299b9034998a76f88025c628ed524da6ba9 |  |
| 2026-11-24T07:36:58.283490+00:00 | retry |  |  | test:separate_scoring:original:A |  | ecc5011f2f52d87786f77a25cc184383eed108a5787079c1fbd59c4459d452db |  |
| 2026-11-24T07:37:00.068809+00:00 | retry |  |  | test:separate_scoring:original:B |  | 1ab593400e0ff98f278131471c36e9d416f78fe4cb3f7cd47e3768f07ff58f88 |  |
| 2026-11-24T07:37:00.115284+00:00 | retry |  |  | test:separate_scoring:original:B |  | 3590b146d51098e676425a2d96a0e18ac0b586fe6ac5307b5569ba562f08ec66 |  |
| 2026-11-24T07:37:01.798798+00:00 | retry |  |  | test:free_form:original |  | 08b9f2ff24cbeeeeba12605a27126cf66c37cfca2f9589b16c34ffefbd8130eb |  |
| 2026-11-24T07:37:02.800195+00:00 | retry |  |  | test:item_checklist:polished |  | f27d998ed43bddc3236520a5e24814d43de9c18b436c6e2cebd4ebfebacfef63 |  |
| 2026-11-24T07:37:03.586220+00:00 | retry |  |  | test:separate_scoring:original:B |  | 84342a3c0c80b360b8698e4db39e8df4b37e2db8b82ebf0937607ac9aea73742 |  |
| 2026-11-24T07:37:04.866621+00:00 | retry |  |  | test:separate_scoring:original:B |  | 84f253803ced26c72b6e37597dd1fc2200d21bcd738e7058d5a99e1bf55c12dd |  |
| 2026-11-24T07:37:06.858476+00:00 | retry |  |  | test:free_form:original |  | 086499d661391f4886e1d3ea848a432509b22c3d713d97d1f03120d6a6b69ba7 |  |
| 2026-11-24T07:37:08.182192+00:00 | retry |  |  | test:separate_scoring:original:B |  | eb9be470e263c014f5fadc53c89fa6a9d0c01636282c0988a3ce37c351881374 |  |
| 2026-11-24T07:37:08.611833+00:00 | retry |  |  | test:separate_scoring:original:B |  | 3a01263c01cb9d3cd465988a28a1050db1d9d7154ad60a6783b2a0fded29d396 |  |
| 2026-11-24T07:37:08.682774+00:00 | retry |  |  | test:separate_scoring:original:A |  | a530daed9f12660df937fbbe6586bd6da72c33912b3e3c6a09c4f41f2e826264 |  |
| 2026-11-24T07:37:14.929546+00:00 | retry |  |  | test:general_rubric:original |  | f01d33c6f2eea32179cf993eeae568b834b41993a490dabca5a2e4adc11299f1 |  |
| 2026-11-24T07:37:24.577536+00:00 | retry |  |  | test:own_requirements:original |  | 4009b19ff597b71fae899f141a41fdad595ac91c27b2ac70350cea20593b60bd |  |
| 2026-11-24T07:37:34.146936+00:00 | retry |  |  | test:item_checklist:original |  | 61956f289b0ee1a2b3464e008dd08622a2f5e27e74d9b85fd774a83af7d48b8f |  |
| 2026-11-24T07:37:35.941874+00:00 | retry |  |  | test:separate_scoring:original:B |  | 1d45305c22749b8b14e04f62d7105641618f7cf5d9ac06196f617444a238dc4a |  |
| 2026-11-24T07:37:36.729950+00:00 | retry |  |  | test:general_rubric:original |  | d6d330e15d68beb162631f5c9e648b50e9dd9428618bf89f1815a34be66330f8 |  |
| 2026-11-24T07:37:38.492221+00:00 | retry |  |  | test:own_requirements:original |  | 7794b3b50ae525460dca7a778497ec0e5ae1be473ffa471709ecddecc919dd02 |  |
| 2026-11-24T07:37:42.299229+00:00 | retry |  |  | test:item_checklist:original |  | 14b1d0d88c7e7bc6e2c056b6abc9cc961d6bd2b6bf9b5364460f9395ebced808 |  |
| 2026-11-24T07:37:48.923117+00:00 | retry |  |  | test:item_checklist:original |  | f4ca7dcdb58a1e0d1fde3ba6d17f3768443df3b4ca1c7b6acf38efe3bcbdf708 |  |
| 2026-11-24T07:37:52.931180+00:00 | retry |  |  | test:own_requirements:original |  | 1c74d3dcf598a7a481dca66f023e107867c40213bfab1485be8b7051fd310327 |  |
| 2026-11-24T07:37:54.855060+00:00 | retry |  |  | test:free_form:original |  | db62e6cc3fcf27ec01d6bf50d716e628d90a91a453016a05d7a332e0bb034a4f |  |
| 2026-11-24T07:37:55.071806+00:00 | retry |  |  | test:item_checklist:original |  | ecd5a78f8245ebedd865be9bd64191ccfca54d0efaf20a467303f07a2d8e2b4e |  |
| 2026-11-24T07:37:58.070965+00:00 | retry |  |  | test:own_requirements:original |  | 5e82ded73f3529a34931968c9bad6e067c93e22cda0fe84ff529a53e711d61b3 |  |
| 2026-11-24T07:37:58.732345+00:00 | retry |  |  | test:separate_scoring:original:A |  | 14258d5b763bd26bf1764e7cc003f26c68d1788f0c3bd734366609bbced80ca9 |  |
| 2026-11-24T07:38:00.326211+00:00 | retry |  |  | test:free_form:original |  | 86c692ca1becf44cfb4f383d0c7ad04c9f506ecf0f2ff9917347fb5c52477765 |  |
| 2026-11-24T07:38:05.765877+00:00 | retry |  |  | test:item_checklist:original |  | c88566ac58dd73cfdaf89382b8a2ce0ca7969a09ac5c1d013acaee7bc20c49dc |  |
| 2026-11-24T07:38:09.266119+00:00 | retry |  |  | test:separate_scoring:original:B |  | 33c5c048d88d0c9b8d6e5b2010902ef7737183434b6cafdf0ef370238071c74e |  |
| 2026-11-24T07:38:09.407387+00:00 | retry |  |  | test:general_rubric:original |  | 3be8758c18982a11c0381d757b0f9e33f51912698426bb18f7e1e803766cb294 |  |
| 2026-11-24T07:38:12.000169+00:00 | retry |  |  | test:item_checklist:original |  | 905e79d23445634f858e79bfe50110e81b8c0e50f087734d8f56e27d5bac87a0 |  |
| 2026-11-24T07:38:13.843050+00:00 | retry |  |  | test:free_form:polished |  | 754b9b117663377bf41b4d5dbe047f9d84f66edb57c785a01e08a899494bf8cf |  |
| 2026-11-24T07:38:14.618713+00:00 | retry |  |  | test:item_checklist:original |  | aaa24b245ec2676a1e6d787cdbaaff26f00f68b12a8605224b19816d4f69489f |  |
| 2026-11-24T07:38:15.647580+00:00 | retry |  |  | test:general_rubric:original |  | 580d0a3047229a570f28f310c97ed49d49b48b9fb6a98b9186b2842e29421af4 |  |
| 2026-11-24T07:38:26.880257+00:00 | retry |  |  | test:free_form:polished |  | f19244e89b2925b5800e3df2c97bd3010409223ca6398827315c33d6fa93bea3 |  |
| 2026-11-24T07:38:55.930533+00:00 | retry |  |  | test:separate_scoring:original:B |  | fb721c24c9b585307434591f8b54937d2e6fc038ead604968a2d7c6bc5260a71 |  |
| 2026-11-24T07:38:58.246635+00:00 | retry |  |  | test:item_checklist:original |  | 26514570e4bc1b0415c55076c028c04910736664531280021dd1cc78d1ffe3e5 |  |
| 2026-11-24T07:38:59.378544+00:00 | retry |  |  | test:free_form:original |  | 63fe58fea28d549500f8d7dff09be8861af052352def323be48ef0fa288d0239 |  |
| 2026-11-24T07:39:01.149685+00:00 | retry |  |  | test:general_rubric:original |  | a252acba64d32cc0fbf1a7b1f449b66df0e20f18bbb1f0f829dedd9263b6e9a9 |  |
| 2026-11-24T07:39:03.044420+00:00 | retry |  |  | test:item_checklist:original |  | ccf717405f95d5fa8a32f13e803e757e5465ee5411ce3136c93ef8a331ac4626 |  |
| 2026-11-24T07:39:04.923842+00:00 | retry |  |  | test:free_form:original |  | 0ec74b0bdbe5cf6929d44004285f14e085338b72653924c255961e3fbf284eca |  |
| 2026-11-24T07:39:06.956351+00:00 | retry |  |  | test:general_rubric:original |  | 1ab23f3242e83f8bb43ef2a75d2d831eb52407ac17c2c737a9bd8728d8d085b3 |  |
| 2026-11-24T07:39:09.131748+00:00 | retry |  |  | test:item_checklist:original |  | 7c6bbb32f9cf0cda8ffebf1125b513d60e0a28bc8c06bec2818c5d8fe3573290 |  |
| 2026-11-24T07:39:38.386640+00:00 | retry |  |  | test:item_checklist:original |  | 676c94f3e4791507ee88c836eb0075d0bfbea48e9868ff62ab09ee22dce05d87 |  |
| 2026-11-24T07:39:40.114308+00:00 | retry |  |  | test:general_rubric:original |  | ea741bc8d41421f11b578c1c00e42dab6ba519f7fc0e39baa4843d6629358fa1 |  |
| 2026-11-24T07:39:46.486332+00:00 | retry |  |  | test:item_checklist:original |  | 2b016c910b79569cc03f99e57b7cb2b5d0d70cad300c62fd33df339a3da88689 |  |
| 2026-11-24T07:39:56.957870+00:00 | retry |  |  | test:general_rubric:original |  | d45ab939784c881fef70e64fe83f4bbf1a6fb8438f4f028569b1f8939b25cc6d |  |
| 2026-11-24T07:39:59.997289+00:00 | retry |  |  | test:general_rubric:original |  | f8c9dfd11ac61885d9fde82e8920a2d208dc1437cab92e5b5596c13cc5e010a6 |  |
| 2026-11-24T07:40:03.519821+00:00 | retry |  |  | test:free_form:original |  | 4b0043e9306b2c04727074fd943ce22a8c91eb4d4cdbaba7f970c7a970897e5a |  |
| 2026-11-24T07:40:14.929197+00:00 | retry |  |  | test:free_form:original |  | 6221c03af978adc13c0141a66f69078dc68508994d8a6ac32f7429dbb23bebaf |  |
| 2026-11-24T07:40:16.934447+00:00 | retry |  |  | test:general_rubric:original |  | d6363e605ccc29b9f7bcf2ef726f1993d8556b1ec2f3867634973c418c00c56c |  |
| 2026-11-24T07:40:18.846362+00:00 | retry |  |  | test:free_form:original |  | 47096b3cc3811a9a7e83a8a68e57ad8bd00397d0d14c938f6bef2c1ee2e0c9bc |  |
| 2026-11-24T07:40:20.836145+00:00 | retry |  |  | test:free_form:original |  | 123debb3d2e7d226ade45344ccb476858d31620bbba99a729ec42f0121faab27 |  |
| 2026-11-24T07:40:34.044559+00:00 | retry |  |  | test:own_requirements:original |  | 43c335d6f8ef480c7453e69a15c09edf8489f50edf7414f1aaac2b1668189263 |  |
| 2026-11-24T07:40:35.850094+00:00 | retry |  |  | test:free_form:original |  | fc2a01f609fea3b1c1c2f3e5bf18cf226594659b0b271fdb3a96fa12a3ab81c5 |  |
| 2026-11-24T07:40:37.793917+00:00 | retry |  |  | test:free_form:original |  | a49569d98d416ca779ba504a81bb958705c93b0c43fd83df32ff02447c64e61b |  |
| 2026-11-24T07:40:41.816372+00:00 | retry |  |  | test:general_rubric:original |  | 958815daa2290a69853565edabb80540de819cc5683a5d38c4aebe1ee1049f64 |  |
| 2026-11-24T07:40:44.080406+00:00 | retry |  |  | test:exam_prompt:polished |  | fe2ebb2b121a9c1a20700243177540c2e9f34348b1ebb99c9c0674d95e17206d |  |
| 2026-11-24T07:40:44.353819+00:00 | retry |  |  | test:own_requirements:original |  | 8a886607a6366c73d046b13ae62066fc91ab4c8c99e820fe7997bf48c40c0f53 |  |
| 2026-11-24T07:40:48.205647+00:00 | retry |  |  | test:exam_prompt:polished |  | 311dd69ae06601a67c8037e77dafa095cbbc765af7c58e2ab34a31a06e0a1398 |  |
| 2026-11-24T07:40:50.113894+00:00 | retry |  |  | test:general_rubric:original |  | 3dd48fd20f83095626cfac3734dfa54ec5fa6bf1afeeea03cf7f1cfd1093df64 |  |
| 2026-11-24T07:40:50.339411+00:00 | retry |  |  | test:exam_prompt:polished |  | 2e6efced8a868256509a4219658c496bcd10ef32318ee98c105eb4a5cb95cd31 |  |
| 2026-11-24T07:40:52.114914+00:00 | retry |  |  | test:item_checklist:polished |  | 6aba1f58a6157fcdf05a17fa8dff0e45b1947d69a40f4aff3d9a1d03d1a37634 |  |
| 2026-11-24T07:40:55.721499+00:00 | retry |  |  | test:exam_prompt:polished |  | 1d3cf8d1dd1ba6ee6c77108e4858c3ed15a71b4ea89e0af93f54cd505e166aac |  |
| 2026-11-24T07:40:56.374743+00:00 | retry |  |  | test:item_checklist:polished |  | 838e2c440ee99c70c8087ce62017e6187834bbc5ffc1fcf0d49e905ab53026ca |  |
| 2026-11-24T07:40:58.166735+00:00 | retry |  |  | test:item_checklist:polished |  | ca4865f48af76e3f3326775b48dd34508f95755e64cfe2bce542e9d07b7ccce0 |  |
| 2026-11-24T07:41:02.341228+00:00 | retry |  |  | test:item_checklist:polished |  | ca5a540b31e021f2f450c2d3064a91744cd7d89022ab4003028282d79be1d453 |  |
| 2026-11-24T07:41:10.665627+00:00 | retry |  |  | test:free_form:polished |  | 0735ed3cff3faf5f9e58d81364b05f95fb5b4d0ed8fbdbfd1653acc7292e8695 |  |
| 2026-11-24T07:41:11.149294+00:00 | retry |  |  | test:separate_scoring:original:A |  | 422117031f7c2be0c87cde71182750a73a63e0c57593e42749d369dc3daa11a2 |  |
| 2026-11-24T07:41:11.312821+00:00 | retry |  |  | test:general_rubric:original |  | 6a1f2e3888f8bbdd1d0864062529957c90ea274f90da4a2894ea2cd26940d63c |  |
| 2026-11-24T07:41:13.351711+00:00 | retry |  |  | test:general_rubric:original |  | d5157a6647f25e36d183000e0eba1bcbc421daaa1955e57e49273bfa9eae2864 |  |
| 2026-11-24T07:41:23.709338+00:00 | retry |  |  | test:free_form:polished |  | b952da1f283ebb819b4607ebb651880021b3d0d4d138a11f9f57ae94f830eaae |  |
| 2026-11-24T07:41:33.483876+00:00 | retry |  |  | test:item_checklist:polished |  | a73260c4fa5294a7026b72be296321be8ad163bf4603e743452c858aa15208e3 |  |
| 2026-11-24T07:41:34.858383+00:00 | retry |  |  | test:separate_scoring:original:A |  | 176136bbd4f9e35868bd6e9017f4da37090eddfb2f608922fcf7455f8498495c |  |
| 2026-11-24T07:41:35.743771+00:00 | retry |  |  | test:free_form:polished |  | 5644406c6962cc1cff175fe78e4286805fdb66687cae00000a6d8cd22d3667d3 |  |
| 2026-11-24T07:41:36.847101+00:00 | retry |  |  | test:general_rubric:original |  | 2bddc16f248c4bab498d5d527ecf2a23f5aab954fe2c7ec9e737d51f2763a19b |  |
| 2026-11-24T07:41:38.643677+00:00 | retry |  |  | test:free_form:polished |  | 758b3d34647efd3820088c26f390d4a7089d4bc616b55bb2487df9643e4585fa |  |
| 2026-11-24T07:41:41.955821+00:00 | retry |  |  | test:item_checklist:polished |  | 8d8aa222740886642b5251722f9485d3d4be09e48d370da89e39c9429c8e5d28 |  |
| 2026-11-24T07:41:46.785537+00:00 | retry |  |  | test:separate_scoring:original:B |  | c285449598c5b6a9183b475b30c31a0b5f30670c7daf91904b8a174965beddf1 |  |
| 2026-11-24T07:41:49.111551+00:00 | retry |  |  | test:item_checklist:original |  | d3e3e2bea1fd8e05166ae9613b2aed6bcab78196da2635a038ab30abb16f4a0c |  |
| 2026-11-24T07:41:56.912159+00:00 | retry |  |  | test:own_requirements:original |  | 2afa6c34ac60f3add0affc4973d615afa441811cd9a45c37c9a6e42f69c244c7 |  |
| 2026-11-24T07:41:57.153224+00:00 | retry |  |  | test:separate_scoring:original:B |  | 5c61470d667e76ddb4a3a779863e12b78947d2976e28f52b08cbabcdf1a62481 |  |
| 2026-11-24T07:41:59.293042+00:00 | retry |  |  | test:item_checklist:original |  | 52e46d44f5349e9f9ab324f2a5aac115d62f17278bc572db1578ae550d920bf1 |  |
| 2026-11-24T07:42:00.983074+00:00 | retry |  |  | test:item_checklist:original |  | e82430c4274d650db8d28b1654a3e7135eedb804a53715335ab2fc40f14c0335 |  |
| 2026-11-24T07:42:02.706793+00:00 | retry |  |  | test:free_form:polished |  | dc7b03fd930c86f332c257bf1547d0dd6d37a81ecb669dfb58cc62331ab5b282 |  |
| 2026-11-24T07:42:04.578370+00:00 | retry |  |  | test:item_checklist:original |  | c448d715fb3ffe5702a785f00c31dc451a476168b721d19dc3c50b21494cfbd7 |  |
| 2026-11-24T07:42:05.460601+00:00 | retry |  |  | test:free_form:original |  | 1b8eab33e1eaab0235b9087ee283e14671244b5450a08e68a7666e851eb020c8 |  |
| 2026-11-24T07:42:07.415480+00:00 | retry |  |  | test:own_requirements:original |  | fb0b0fbfee96341bf2076bdc735e678316366ce66176812a3b11c4389fb118a3 |  |
| 2026-11-24T07:42:08.521622+00:00 | retry |  |  | test:item_checklist:original |  | f63da2aededb555f1651498ea31081700c6dfe9f154db26fca999ee00de6127d |  |
| 2026-11-24T07:42:10.610098+00:00 | retry |  |  | test:free_form:polished |  | 1b21d772acfb1ca7092b1391e5ea2591964a73ee0005c4e32db88381ee81a24f |  |
| 2026-11-24T07:42:12.315966+00:00 | retry |  |  | test:exam_prompt:polished |  | d439156868a105b61798d09455aa239df166c606c7597ae178074e19395bae0d |  |
| 2026-11-24T07:42:12.519498+00:00 | retry |  |  | test:item_checklist:original |  | b8fe28b04f848c6f07f4733d6f3367533ebe297ba0b8e76923147575641f00be |  |
| 2026-11-24T07:42:22.155274+00:00 | retry |  |  | test:free_form:original |  | 926ddd72ca2d0d0b9b97739c797a11019d2299bdf3ec3babb0ffdaee0a8707e8 |  |
| 2026-11-24T07:42:22.318355+00:00 | retry |  |  | test:general_rubric:original |  | 526ee35fddb80d1463de762411bf97983f5a58a107a8138bfb4ca482a46de8c9 |  |
| 2026-11-24T07:42:35.184772+00:00 | retry |  |  | test:exam_prompt:polished |  | 9a21d9676002efb0ea1458548497d50b797adb26f5486429a8946195a5017188 |  |
| 2026-11-24T07:42:37.306294+00:00 | retry |  |  | test:general_rubric:original |  | 45038e2849adabb806ce5b5eca630289d47a333a970f0c24b4e4b6ea35f59dca |  |
| 2026-11-24T07:42:39.250742+00:00 | retry |  |  | test:item_checklist:original |  | eaf01b6ebe3b6e3f3ef64d94339cbc23d10dcb56673008a6234ee0fedf91233a |  |
| 2026-11-24T07:42:44.584126+00:00 | retry |  |  | test:item_checklist:original |  | 00df6da1fee3e0f1e34e70c03b1f33470e1f4f35ae5edb820f7dbe2637d10c44 |  |
| 2026-11-24T07:42:46.352489+00:00 | retry |  |  | test:item_checklist:original |  | bce4b1ef9c00dbb3ce6c3721c48d7e43482cd1ecff97e997cebd376d1d8d441e |  |
| 2026-11-24T07:42:48.013606+00:00 | retry |  |  | test:free_form:original |  | 8eeab0d19651269ed7af4b45b1aad02401621d49d1951aee6e519fad03d19faa |  |
| 2026-11-24T07:42:48.226014+00:00 | retry |  |  | test:free_form:original |  | 72456ca0c7ada3911d8d1ef8c46cc03daae68b8f611fc6b6cb240e95ac872a67 |  |
| 2026-11-24T07:42:49.794177+00:00 | retry |  |  | test:free_form:polished |  | 88a009319f8a3bb5865d447d61e9c488398361f5aba6bf3e90af05446880c00e |  |
| 2026-11-24T07:42:49.941199+00:00 | retry |  |  | test:item_checklist:original |  | 9266aa693a484f321c1f2aad9df15d44abf1d208a8d74fb66aad0b7e6990ebc8 |  |
| 2026-11-24T07:42:51.878081+00:00 | retry |  |  | test:item_checklist:original |  | 908674ab082a4960a6f6a1ba376ba5235a3d03d1414364399199dfa1b048c361 |  |
| 2026-11-24T07:42:53.258027+00:00 | retry |  |  | test:free_form:original |  | bc92337121e55842625f32aff678ac73f29bc14f0a4d270891fce31107d7265f |  |
| 2026-11-24T07:42:55.400087+00:00 | retry |  |  | test:free_form:polished |  | ede5f6021f465c7102de2a9c758c113d0d3d03d1f9e726954b4555fc7ec951cf |  |
| 2026-11-24T07:42:56.093328+00:00 | retry |  |  | test:general_rubric:original |  | 556fee27aa7c1b691b793c25f11bfe5bb109bc1009af6b19dc3b6347b3a4dca5 |  |
| 2026-11-24T07:42:57.214127+00:00 | retry |  |  | test:item_checklist:original |  | 65db5502ff1598eab2400aa7531d412c92e93da6128f3eb6fe8ad6fce574f45a |  |
| 2026-11-24T07:43:00.681609+00:00 | retry |  |  | test:separate_scoring:original:A |  | 929224b974d0a0704a17e3153d8b29b246e5b810c0add9515230a14dd2c380ad |  |
| 2026-11-24T07:43:02.386388+00:00 | retry |  |  | test:free_form:original |  | a8a51542c9dfdf8fc9a948388ed55c3e94041d98cb48a3536f9fcb82fac74c26 |  |
| 2026-11-24T07:43:03.063134+00:00 | retry |  |  | test:general_rubric:original |  | f5ac089a5cccebaaa6d71b197f195a69e64939933135a6d879e9c071ae887593 |  |
| 2026-11-24T07:43:04.969166+00:00 | retry |  |  | test:general_rubric:original |  | 8739366142bb65fc4f995250e4024cec54a905eec6cd3f70fd05455cd7452f5b |  |
| 2026-11-24T07:43:08.362201+00:00 | retry |  |  | test:separate_scoring:original:A |  | 421d903f4b09f3fae66e89b64d721321be779a334dc42236e3c2b3ba59210248 |  |
| 2026-11-24T07:43:08.707458+00:00 | retry |  |  | test:free_form:original |  | 2937095aead63f9b67b02bbcf78606068acf40cc5d1ea4cbb436bd513e429fc8 |  |
| 2026-11-24T07:43:18.301560+00:00 | retry |  |  | test:separate_scoring:original:A |  | df29cc3df673bdd5022edfee9053e811a11edad21f491af3e1ea5aa514e30150 |  |
| 2026-11-24T07:43:28.107441+00:00 | retry |  |  | test:general_rubric:original |  | 1b64fc97ea1880195b76c035700055dd90bc7b81efa864546dffe433800a5678 |  |
| 2026-11-24T07:43:39.781808+00:00 | retry |  |  | test:separate_scoring:original:A |  | 2827af34b53f5b3c3b13e5800f8edf9cb791667332613a9b3b87e3fc6f1366ac |  |
| 2026-11-24T07:43:41.710000+00:00 | retry |  |  | test:item_checklist:original |  | f7548ebd79de6052369919dca269ef45687a512401729746362d1fa35f16ea61 |  |
| 2026-11-24T07:43:59.961394+00:00 | retry |  |  | test:item_checklist:original |  | 753bf6f13e55a455252e24b1bc10b849c459ec4d85bef80154e57b66af370c78 |  |
| 2026-11-24T07:44:03.465637+00:00 | retry |  |  | test:separate_scoring:original:B |  | 8e95459f8c4238487d5067b8a80d6806da02e88c0c2b7ea624b937259aa18a0d |  |
| 2026-11-24T07:44:05.267611+00:00 | retry |  |  | test:free_form:original |  | cec087e7fd1ac1f1241122f7461e065469c2f5c747c1dc62e7dbce9e479e1eba |  |
| 2026-11-24T07:44:11.503242+00:00 | retry |  |  | test:exam_prompt:polished |  | 36749df46783d2936e364525c37a5b17f05642528ceb0802edeb1947c4aba2c7 |  |
| 2026-11-24T07:44:15.190442+00:00 | retry |  |  | test:separate_scoring:original:B |  | 2aedcce0e636e9f8d1848bbe3f7c07fca1152b19325f09f34cf89ba88e5f3b65 |  |
| 2026-11-24T07:44:15.933482+00:00 | retry |  |  | test:free_form:original |  | 6d90b75ad022576d7de2737c427664b9c5292762cea812c0a539f47d66d2272f |  |
| 2026-11-24T07:44:22.456400+00:00 | retry |  |  | test:exam_prompt:polished |  | cb3672e694c4698a32981623fca75f7181b09f2aa1429928d2a5d2e97405fcfc |  |
| 2026-11-24T07:44:33.182343+00:00 | retry |  |  | test:exam_prompt:polished |  | b8d89cc1e957d0378ba544600f450dc01be45afad1798c40ca3f7251d083a675 |  |
| 2026-11-24T07:44:35.382430+00:00 | retry |  |  | test:separate_scoring:original:A |  | 429406520730d3148725abab504b3b8f9f08037b54381645a917bdf89e8af844 |  |
| 2026-11-24T07:44:39.396140+00:00 | retry |  |  | test:item_checklist:original |  | 1022daa49f48da963c40d41eab46c0f0f33d04c6e7ccf0e77615c3d98c2c1485 |  |
| 2026-11-24T07:44:41.170613+00:00 | retry |  |  | test:item_checklist:polished |  | b189d57c61ad239153a1645035c902712a0760383dd8d6b1028f2b06ff42a932 |  |
| 2026-11-24T07:44:43.061580+00:00 | retry |  |  | test:exam_prompt:polished |  | 07a6e69d750d2e426dc4dae16b8ed1ed3061ce748534580a425f3370a9992404 |  |
| 2026-11-24T07:44:45.121404+00:00 | retry |  |  | test:separate_scoring:original:A |  | 0d2e36b1e49741b7a813ff3370810ff73726563bd065d82bb3656ba88c7f5ea5 |  |
| 2026-11-24T07:44:51.280588+00:00 | retry |  |  | test:item_checklist:original |  | 99b526befcc07524ca4a15e6755523b1a9051aab6c579e1c253d042d6a74e710 |  |
| 2026-11-24T07:44:52.821895+00:00 | retry |  |  | test:item_checklist:polished |  | d6d4d1c1ea1aefab849ab3b27fdb11f89e947b28c5be2025f58605f7549112c0 |  |
| 2026-11-24T07:45:02.525237+00:00 | retry |  |  | test:separate_scoring:original:B |  | ac5edc8fc4708f61f6556e69ef6b5670ad71933ed88b21c963d97f7663b8fb96 |  |
| 2026-11-24T07:45:08.733096+00:00 | retry |  |  | test:own_requirements:original |  | 4d6b8ea05e017d716084c767fc91306117358a6721bd50b485d473d95b212294 |  |
| 2026-11-24T07:45:14.702512+00:00 | retry |  |  | test:separate_scoring:original:B |  | 171092473bff13ce5462573029b4d929ee71598282111af6a7ae88ceebc72b90 |  |
| 2026-11-24T07:45:15.655429+00:00 | retry |  |  | test:separate_scoring:original:A |  | 6e24b1bd3090cfb833c80c2cfb9bcb39808b0e1e94e4a658cec72948ee645efd |  |
| 2026-11-24T07:45:25.440231+00:00 | retry |  |  | test:own_requirements:original |  | 6247a1d7811e6ba640fe8aefdd2fd707235c1e03ed374f626ff9c808aa37e4db |  |
| 2026-11-24T07:45:35.355277+00:00 | retry |  |  | test:own_requirements:original |  | cde65750399893ea9c472b65198a113ba00c8d454c152b6d0f8f50f0788edf67 |  |
| 2026-11-24T07:45:40.261397+00:00 | retry |  |  | test:separate_scoring:original:A |  | 6e4fff386e623a16148b0dbbb9e40398a7ac42cd3d1ff3a51f42049890e663ba |  |
| 2026-11-24T07:45:42.514554+00:00 | retry |  |  | test:item_checklist:original |  | 51dfdb9bdcdfd3f7cb298f4d17df6581b6d4949e21b878a94fe51470aab11320 |  |
| 2026-11-24T07:45:44.097013+00:00 | retry |  |  | test:free_form:polished |  | 70d95c93eb1f6ca81c0649c8e5ec563bd10d7067278f0513847469256377d7a0 |  |
| 2026-11-24T07:45:47.788042+00:00 | retry |  |  | test:general_rubric:original |  | f1c5354a1dc83e15e8f807745616374f57cbcc349d8d47fa4e45382339721a17 |  |
| 2026-11-24T07:45:48.428234+00:00 | retry |  |  | test:item_checklist:original |  | fd3e2546c593f0b499d26fb5fc069317baa8688bb03ff3375fb9dbc18d0f59c5 |  |
| 2026-11-24T07:45:49.569537+00:00 | retry |  |  | test:own_requirements:original |  | 73541c2e8ccdb65a8520152f9271ac8e8316a2af1dc03026c94bb3f676fc1477 |  |
| 2026-11-24T07:45:52.018352+00:00 | retry |  |  | test:general_rubric:original |  | 04cc4d90d8bda57d867b77b2c798cbbeed7348b4fc04046630f2c19474c4cb66 |  |
| 2026-11-24T07:45:52.400762+00:00 | retry |  |  | test:exam_prompt:polished |  | cfdce99d6731060fcfcd9fcca07e85db92a2cae146ce32298bfe261b25c1ae34 |  |
| 2026-11-24T07:45:53.922798+00:00 | retry |  |  | test:free_form:polished |  | 43c59a4fa0c3e94d83c82fcb2bcc065f6ba2b5610236c4c01629d266d309a6f9 |  |
| 2026-11-24T07:45:54.251550+00:00 | retry |  |  | test:separate_scoring:original:B |  | 8933dfdd8b44d91c12b6b47a7bee39a89f6e2fb8b3a71ef6c6a6e4da855b4776 |  |
| 2026-11-24T07:45:56.053001+00:00 | retry |  |  | test:general_rubric:original |  | 6cb55d8321c8789ed6bfafb7c4f8043646021ebf5d25bf0658c822c5c1c543ee |  |
| 2026-11-24T07:45:58.043907+00:00 | retry |  |  | test:general_rubric:original |  | a404a49a5132ee539f550e4419b62daafe7c94a155fe17ec0f981e293a85d915 |  |
| 2026-11-24T07:45:58.791422+00:00 | retry |  |  | test:exam_prompt:polished |  | 18800832778d422db97736d47565e8d0fa224a4e4005dfb155d8ca9479de59ba |  |
| 2026-11-24T07:46:00.600225+00:00 | retry |  |  | test:separate_scoring:original:B |  | 88797752ac0a4ee155391ca47c2324a3349ec8df187f2209ed28bb94a03604c5 |  |
| 2026-11-24T07:46:01.718138+00:00 | retry |  |  | test:separate_scoring:original:A |  | 84b41c7019caaaeefb490884da0687ae7f43c0d23bc264cf5e481438cb533712 |  |
| 2026-11-24T07:46:06.534404+00:00 | retry |  |  | test:exam_prompt:polished |  | 6bd782c41cb4858f2ca3f560a2100b9c69d617fc38ef89b8b5aedaf298c43817 |  |
| 2026-11-24T07:46:08.561904+00:00 | retry |  |  | test:separate_scoring:original:A |  | 0b4bd39f78b1c3b6ff0b282d08bdfaec8a5a5322233b4ce29b20174afe7b5822 |  |
| 2026-11-24T07:46:11.658789+00:00 | retry |  |  | test:exam_prompt:polished |  | 18f5e9baac1a8dc4247c1209647c4102893fb67a85600ebeeaa929ca809878e3 |  |
| 2026-11-24T07:46:16.854095+00:00 | retry |  |  | test:separate_scoring:original:B |  | 7bc203cf634b7631e3804b6ed4e644263055db135a7f69956845cc9dc9f512d9 |  |
| 2026-11-24T07:46:25.578772+00:00 | retry |  |  | test:item_checklist:original |  | 6f3f3b5097676ddf0d0cd6d100521eaf8a3bf96141ea9e9d57601a069e9f8969 |  |
| 2026-11-24T07:46:38.570746+00:00 | retry |  |  | test:general_rubric:original |  | 83768d4e913a8f9bb2a14ed3be4275e1ccf47b36cdaec8d71cd13cb5fd6b479a |  |
| 2026-11-24T07:46:44.879687+00:00 | retry |  |  | test:item_checklist:original |  | 8638c85689d7f9a9034dd84f46b95c4d5512366960c61bb329963d2f8103c9ec |  |
| 2026-11-24T07:46:46.539991+00:00 | retry |  |  | test:item_checklist:original |  | 7c08dcb6a0cabeb5cbce258f9ac2ef6aa24e4703c89a8b530a96bf436de60c0d |  |
| 2026-11-24T07:46:47.537297+00:00 | retry |  |  | test:separate_scoring:original:B |  | de9416a750c8097e4b2fdff17e8f2e300f11e7a081606789d98867a6800818c4 |  |
| 2026-11-24T07:46:49.743552+00:00 | retry |  |  | test:general_rubric:original |  | a272a23d589feadee6d8c09b1744a10f6c44f465cbcdfee74bb92d323ee32448 |  |
| 2026-11-24T07:46:51.534996+00:00 | retry |  |  | test:free_form:polished |  | 704286bf7049061d34fbd333a62ddd0e418f0273522b375927bacd08f716134e |  |
| 2026-11-24T07:46:52.289029+00:00 | retry |  |  | test:item_checklist:original |  | eb182b54b42f70a0a692e1a3ee9844a9020ff9d889f5dc3c537648ca93b21462 |  |
| 2026-11-24T07:46:53.362846+00:00 | retry |  |  | test:separate_scoring:original:B |  | 28864cdedcdb1e25bd983376f9e287e1d7639456ee06389bc5beb738fde45d43 |  |
| 2026-11-24T07:46:59.281229+00:00 | retry |  |  | test:free_form:polished |  | cdab8bb877929cfe4f288f256a6be2804d603351f9561b529e320d2e69ac5634 |  |
| 2026-11-24T07:47:05.829920+00:00 | retry |  |  | test:separate_scoring:original:A |  | 4f7f1fb5d8d12fcd625be4131a72e3b0c22233d3d113c03b2e55115a2d0e08f3 |  |
| 2026-11-24T07:47:07.876770+00:00 | retry |  |  | test:general_rubric:original |  | ac7158bfca5684bcf00be53d7ae981e90dad2ec6dd3d35ba1c97c106c17ff724 |  |
| 2026-11-24T07:47:09.949442+00:00 | retry |  |  | test:item_checklist:original |  | bea6090c5039d05fd049b32297e6b7d38bc8a703f811d9c281e12b53b7bb5067 |  |
| 2026-11-24T07:47:12.055069+00:00 | retry |  |  | test:own_requirements:original |  | f1dc1d452dedb997a60e98cb3431a43b17a9e3748eb2b190e14e0494c147b6bb |  |
| 2026-11-24T07:47:14.732494+00:00 | retry |  |  | test:separate_scoring:original:A |  | a3e80901fd4bf547546d9df2612e39bfb0f46762a3b09e7fea10d1d75672356f |  |
| 2026-11-24T07:47:16.950314+00:00 | retry |  |  | test:general_rubric:original |  | fc3e17781c81d50cc587326e3cac12d4450d4f1144e62aabb3c42aeaba816655 |  |
| 2026-11-24T07:47:30.080579+00:00 | retry |  |  | test:general_rubric:original |  | 329f28c997555edb79f5b11a2c3becb03711704e9a3c5fa1a9c66a2aec6f5d92 |  |
| 2026-11-24T07:47:35.820105+00:00 | retry |  |  | test:item_checklist:original |  | 8ac0b989b8735e61f0c44390489d382bd426720354c17eaf5a3c003d179c1544 |  |
| 2026-11-24T07:47:38.038506+00:00 | retry |  |  | test:item_checklist:original |  | c1a23f20904ca59545a620dd7588ca93f5d604865b0c04248fc20656983a9021 |  |
| 2026-11-24T07:47:38.805702+00:00 | retry |  |  | test:own_requirements:original |  | 5a1d8a9e50eea67c3407275063bdbd3284e40fea4493c3b8c0aab5db53a344d3 |  |
| 2026-11-24T07:47:41.755516+00:00 | retry |  |  | test:separate_scoring:original:B |  | 40e775a3ee2fc3ff864bb9a38334836e83bb505d63681fc0022e35ec0c04d26c |  |
| 2026-11-24T07:47:42.274182+00:00 | retry |  |  | test:general_rubric:original |  | b057ce338904e9f0b20b690688010648e09fb988277e39f5e5007ecac9ba8dc7 |  |
| 2026-11-24T07:47:43.608885+00:00 | retry |  |  | test:item_checklist:original |  | dd3d294289cccdb493f03b5a19ea241c0b597b24d8401624641a7b19e27ec6f4 |  |
| 2026-11-24T07:47:45.319198+00:00 | retry |  |  | test:item_checklist:original |  | 1e9364f33edd4c212054d47376a27e2f96893997a449beed01934c126cb08a92 |  |
| 2026-11-24T07:47:48.817732+00:00 | retry |  |  | test:separate_scoring:original:B |  | b001b70762df03d118ccaec73b79e4006ec129b4d07ebef8982dee4729250759 |  |
| 2026-11-24T07:47:50.738647+00:00 | retry |  |  | test:separate_scoring:original:A |  | 5302f82e7d7f3ef5097af0037e320dc8d2be98d047092cddd5975d5ceb08eefd |  |
| 2026-11-24T07:47:53.149419+00:00 | retry |  |  | test:item_checklist:original |  | d4c94d1fee77f171b05dc1d13531cd03e1cb097c02e1bf0897484b0c3f355e01 |  |
| 2026-11-24T07:47:55.103692+00:00 | retry |  |  | test:free_form:original |  | 3f58c93872ae52f26558cb244883222a5acd03a942637e295b69c35982f009d7 |  |
| 2026-11-24T07:47:59.225198+00:00 | retry |  |  | test:item_checklist:polished |  | 81d84e134a5e1fee6a52ae6865ab0167accf7201b70492059af54b69597052d2 |  |
| 2026-11-24T07:48:02.342773+00:00 | retry |  |  | test:separate_scoring:original:A |  | 2e3bc985ac7376e4371a3911bd0c5a72896dbdc5a6a692381fa89846db1ae786 |  |
| 2026-11-24T07:48:03.121937+00:00 | retry |  |  | test:free_form:original |  | b83631b3a1ac98e8b12a0632b0cccc2686ea221d934f49be7f71210fe4ef984e |  |
| 2026-11-24T07:48:05.414009+00:00 | retry |  |  | test:general_rubric:original |  | 7395327b0d0a22f79d4ed0eeb3088e1cd1bed79ef18f022e5e5fa21de2d25726 |  |
| 2026-11-24T07:48:07.517195+00:00 | retry |  |  | test:item_checklist:polished |  | 9170691a558ccb3c549ce77d2c8c506e0f55c95bd824e9b75ae08a19b8189355 |  |
| 2026-11-24T07:48:09.499783+00:00 | retry |  |  | test:free_form:polished |  | 43a1a8a185894e3a48ee59796b2282539ef1aae81c36b135f569f8f2f2755882 |  |
| 2026-11-24T07:48:14.857895+00:00 | retry |  |  | test:separate_scoring:original:B |  | c4b83a44e6b4d49d806151c30c65689456ea979de9f732d76233b77cf6c80149 |  |
| 2026-11-24T07:48:25.574021+00:00 | retry |  |  | test:general_rubric:original |  | 9b799b4920b344ffc490f42bbc632c50997aa3ab306ba9662437e8cc7a823404 |  |
| 2026-11-24T07:48:34.876110+00:00 | retry |  |  | test:free_form:polished |  | c11ed382d17cc2b7d0d43ecea9f1cecbaf6f9a27a960ce6f00f2af064ea7d72f |  |
| 2026-11-24T07:48:35.359094+00:00 | retry |  |  | test:free_form:original |  | 2b5cbb5e8d4e6a4fdf42e5f726e02bfc7fdb4b25b3ad5db64c666c8d5eefe4ce |  |
| 2026-11-24T07:48:36.702882+00:00 | retry |  |  | test:separate_scoring:original:A |  | 87bda4ca982137c7b9f7f0e9ccb98f8d2391338e9ffdb9da461e08d0152b93e7 |  |
| 2026-11-24T07:48:38.774453+00:00 | retry |  |  | test:separate_scoring:original:B |  | 9bb210cf87c96e3b02cb626134fe2ea516127ee9e3ba94d278c9bafbe5532728 |  |
| 2026-11-24T07:48:39.491858+00:00 | retry |  |  | test:separate_scoring:original:A |  | 05268c14b0523e761e23c4f9a6eb3d46184f1b8e4cdb157e3907b7ab95f65742 |  |
| 2026-11-24T07:48:41.427369+00:00 | retry |  |  | test:free_form:original |  | 015543b6c4cb6e5fd4d5b5921dc9e6d49f52422bdd48fb62605d88108cbd2a4c |  |
| 2026-11-24T07:48:43.305838+00:00 | retry |  |  | test:separate_scoring:original:A |  | ec83fbde9d190209d791b943ad00097482c24459003833d5d170d78c8fc05a1e |  |
| 2026-11-24T07:48:46.432942+00:00 | retry |  |  | test:separate_scoring:original:A |  | cf0c8ebc3faab3284e348edaebb6ff4be17f8ef474df5a1509bec40fbc4cdf93 |  |
| 2026-11-24T07:48:55.411742+00:00 | retry |  |  | test:free_form:original |  | 6649e291b3f3e0273b1278d8403bf6cb462e995d0a61f8787ed7529f66320cdb |  |
| 2026-11-24T07:48:57.199543+00:00 | retry |  |  | test:separate_scoring:original:B |  | 2f25d6086df5064a0811bfdcae9303b2ee60a4feedfda4cd2f69c13ed4a3a7a6 |  |
| 2026-11-24T07:48:57.405612+00:00 | retry |  |  | test:free_form:original |  | 6aac558ba93d5158c5b5ddde4429c911f12d444bf8a6b9b30e3306d2c7a26e24 |  |
| 2026-11-24T07:48:59.636093+00:00 | retry |  |  | test:separate_scoring:original:B |  | f1d3f895b36834d3b459aaa9ca43f5a31512bc66d91307eeb652a12ca5c685b3 |  |
| 2026-11-24T07:49:01.700680+00:00 | retry |  |  | test:free_form:original |  | e813255cbaa97576770a7aff3a375e377f0435bc6253c834cf60859f1bc799e2 |  |
| 2026-11-24T07:49:03.471174+00:00 | retry |  |  | test:exam_prompt:polished |  | aa476165fd2c4b957ea275ebb4b94554efcb5ff10661e5495d914f0a1f57411b |  |
| 2026-11-24T07:49:03.495218+00:00 | retry |  |  | test:free_form:original |  | 76f7c3590bd17c4fb96fb471f1e6967f58d96356c462bf5f8bf15fb06b737b11 |  |
| 2026-11-24T07:49:04.240941+00:00 | retry |  |  | test:free_form:original |  | a200b70abf8c7f4a6477415f3d12be0a7a685eed1a7f128c8f143bf8b305681c |  |
| 2026-11-24T07:49:04.565999+00:00 | retry |  |  | test:item_checklist:polished |  | 3d56a4e91ba78aeba48ba2b6d7e707a574c6ca932e7ec46465bdc24e43d10f9e |  |
| 2026-11-24T07:49:05.596232+00:00 | retry |  |  | test:separate_scoring:original:B |  | c9bded635da824c92ffdf4158528600ad93f12ed314b92f1bd2f941a213ee882 |  |
| 2026-11-24T07:49:07.380514+00:00 | retry |  |  | test:separate_scoring:original:B |  | 45ef3590c95c7e39a946c596ecb7ff025c6cfd400f1f60f7843f307bfeb0923e |  |
| 2026-11-24T07:49:08.991564+00:00 | retry |  |  | test:exam_prompt:polished |  | fe3dfb6172267241f19296cf3c1abd1dca5d3fc9fcc7a59092000c540382dfc8 |  |
| 2026-11-24T07:49:11.716141+00:00 | retry |  |  | test:separate_scoring:original:A |  | a3bc6cd048f4328590d706a07947fd44fa10ed5c585848b5b920def418e1e352 |  |
| 2026-11-24T07:49:15.953814+00:00 | retry |  |  | test:item_checklist:polished |  | 755ec3109681de62e247cdbd4460959bc339e526fd4269001514e4c3a47c8411 |  |
| 2026-11-24T07:49:17.879311+00:00 | retry |  |  | test:free_form:original |  | 7213d3838530115437b98179d60a32f69fb23c8143e26e1f38f6a400cadcca7f |  |
| 2026-11-24T07:49:19.745032+00:00 | retry |  |  | test:separate_scoring:original:A |  | 3a444ca17b80eb9953f496b3d1df1973b8040ca00522631695f8477cca98dd00 |  |
| 2026-11-24T07:49:24.047563+00:00 | retry |  |  | test:exam_prompt:polished |  | 85639663f36bb3e8ab60dbcee089c9656b972dab2305b68bec1f9f692c289159 |  |
| 2026-11-24T07:49:24.179666+00:00 | retry |  |  | test:item_checklist:original |  | 6a933ff0bdf23920e0d8fee24262aeefa52ba35b545d41daf0545768b6414fcf |  |
| 2026-11-24T07:49:25.982710+00:00 | retry |  |  | test:free_form:original |  | cf4c1953c1933c4af2df13e57f4a4b3b5dbec34058ba65be4ce00b6f86261c8f |  |
| 2026-11-24T07:49:26.044734+00:00 | retry |  |  | test:item_checklist:polished |  | d0ef59ee0cdcf20bb27b22f6c10debaf56b3b864905c0b98af877929d1d63fda |  |
| 2026-11-24T07:49:33.380023+00:00 | retry |  |  | test:exam_prompt:polished |  | 317417aea1919a8c6fb63503512866114d3e0ab600a91aaa8503c01842319d61 |  |
| 2026-11-24T07:49:34.523312+00:00 | retry |  |  | test:item_checklist:original |  | 9b7b05a6d6cba0bd46d10dc92984e2c1663f2256bc19c01ace4af8e6c3a72657 |  |
| 2026-11-24T07:49:42.216364+00:00 | retry |  |  | test:separate_scoring:original:B |  | 3a61317d5ba142160efa1419aea132c6b6b335554542a719c53d8fda5e893e15 |  |
| 2026-11-24T07:49:46.130020+00:00 | retry |  |  | test:free_form:original |  | 32d2488c07a34d640de36101e2fe09351f75be618b40bfa4dc0ca2e36fc9d403 |  |
| 2026-11-24T07:49:52.980859+00:00 | retry |  |  | test:item_checklist:original |  | e8c0208914041ca5235f7a9cc07e1699e826974d2311f7fc89fa914cc2b92210 |  |
| 2026-11-24T07:49:54.795520+00:00 | retry |  |  | test:free_form:polished |  | 73a77a186430a02b46b5b0dafe1898a61af118ba60438141264244f6b1cdfd2b |  |
| 2026-11-24T07:49:56.969939+00:00 | retry |  |  | test:free_form:original |  | 0e82654c255361f617ed8e022f5e25e6d74d7cdb07ed5cb4028fb122f2f5a174 |  |
| 2026-11-24T07:49:59.417058+00:00 | retry |  |  | test:separate_scoring:original:B |  | dcc0433dc44524f55576ea2739da0b4ed5e0407513d33b5111404e95714ae215 |  |
| 2026-11-24T07:50:01.204325+00:00 | retry |  |  | test:item_checklist:original |  | 8db9d9603912a1dba5e370a7135f65dfff3d6368d0c48e9cf91ececd0745af4b |  |
| 2026-11-24T07:50:03.057026+00:00 | retry |  |  | test:free_form:polished |  | 1a8fc9b2664c8dc697c7c76d2f2d4f57781161debc97097d5f738841a995412b |  |
| 2026-11-24T07:50:10.824195+00:00 | retry |  |  | test:own_requirements:original |  | e5b09e07dcac6145fb4d182e3fbf7272fc9b189d15a100a92462b8150857ed8b |  |
| 2026-11-24T07:50:15.084190+00:00 | retry |  |  | test:item_checklist:polished |  | 46a571fcef63d44b26869151eb6e1809509f2ed610f7ba44808fc3cded2174b3 |  |
| 2026-11-24T07:50:16.968281+00:00 | retry |  |  | test:free_form:original |  | 4bdbce678a6b3cd6c7cec30dcd879c20937f1b1982d143d460908a8817ba5aa9 |  |
| 2026-11-24T07:50:18.252855+00:00 | retry |  |  | test:separate_scoring:original:B |  | 5f2f34a1a414a7a64d29d7636c24600d15ecf7b6384d10cdad2653516af52be1 |  |
| 2026-11-24T07:50:18.995938+00:00 | retry |  |  | test:own_requirements:original |  | dc5eacd147e4139259f22eb8a6dd1e52e62c73e77e51de3dd199b91d92310b7b |  |
| 2026-11-24T07:50:19.775849+00:00 | retry |  |  | test:separate_scoring:original:A |  | 7d140e45ff3409573eec7596d9461dcec7df228021aa810ec42415c2f322a1b8 |  |
| 2026-11-24T07:50:20.859857+00:00 | retry |  |  | test:item_checklist:polished |  | 1cbb40d33609ef040f94fa4f2ee250581ddfef1d4ca6c8f74c378508c3d27b80 |  |
| 2026-11-24T07:50:21.802072+00:00 | retry |  |  | test:free_form:original |  | f3eb2fde44304b72e439f241e63fa1ccf7de8a2370444efff7792bf3f9c73ab3 |  |
| 2026-11-24T07:50:24.608357+00:00 | retry |  |  | test:separate_scoring:original:A |  | 20f00edfc066a15e28eb07e1b6703f932ffa41ab832444666ac4be13a4d11252 |  |
| 2026-11-24T07:50:25.406456+00:00 | retry |  |  | test:separate_scoring:original:A |  | 7ff0cbdd175db085607bb734bd30fc6426daf34d556f92dab7f5d3c1b6f21fb6 |  |
| 2026-11-24T07:50:36.312372+00:00 | retry |  |  | test:free_form:polished |  | eb4ef57e2e1ec81a81a376ef64d8eeb2c8d5036dccd85d9edfb513a0665cbdbf |  |
| 2026-11-24T07:50:37.173225+00:00 | retry |  |  | test:separate_scoring:original:A |  | cc774e5d1d5122f6c949f7464f29b4429cf94539314ab95308ae2993585e0731 |  |
| 2026-11-24T07:50:39.374086+00:00 | retry |  |  | test:item_checklist:polished |  | 1545af8ccf54900d5c07b5b8a185918b1f71a3e276435ad2eaeb4122fe9014fa |  |
| 2026-11-24T07:50:45.346407+00:00 | retry |  |  | test:separate_scoring:original:B |  | d120f203be250551c2249916de28ceec48b73834d724b59d84a0aeffab7908a1 |  |
| 2026-11-24T07:50:47.219034+00:00 | retry |  |  | test:item_checklist:polished |  | f7ce79f8bf323d16f9adf41876a7df1f24b71549850a4e40e8e035589794ee63 |  |
| 2026-11-24T07:50:51.013480+00:00 | retry |  |  | test:separate_scoring:original:B |  | 37df67217159366d89539e72369c8af2c3a74126173cbb0672089a711012f7a8 |  |
| 2026-11-24T07:50:54.281010+00:00 | retry |  |  | test:separate_scoring:original:B |  | 5364b04c27a187841250a0b1059051eb1a20aa6899003f0b13c818edc2e8aa59 |  |
| 2026-11-24T07:51:02.005396+00:00 | retry |  |  | test:separate_scoring:original:B |  | bcfb4c569ee6be113935b5bea7ebab1415fcab01c06590803b1e8badef5eebda |  |
| 2026-11-24T07:51:07.549975+00:00 | retry |  |  | test:exam_prompt:polished |  | 035ad12c0eef3c766687b2b852e8745e410821bfcddc627b050f1a4acf854456 |  |
| 2026-11-24T07:51:14.485509+00:00 | retry |  |  | test:own_requirements:original |  | 219e815bbc732ea6b63d4dbe701bc376516f43e4b138c549797b37877c344280 |  |
| 2026-11-24T07:51:18.503074+00:00 | retry |  |  | test:own_requirements:original |  | 93bcb793fb672503d04779285f400a9bc371723046258c22c3e816c261743aa7 |  |
| 2026-11-24T07:51:19.352990+00:00 | retry |  |  | test:free_form:original |  | e52bd9d8c3be8cf1632cce01bdfbb435d4d6184e96bd66b99d4f960e5a151abc |  |
| 2026-11-24T07:51:21.289459+00:00 | retry |  |  | test:exam_prompt:polished |  | 31eb14bc1c4ff367ed39d5007ca151a2ff0ea77a328aad2e3ebc17dd6c6de8cc |  |
| 2026-11-24T07:51:22.881567+00:00 | retry |  |  | test:general_rubric:original |  | 28ebeeef808d8e81c3707d03bbd60a1eb9e27e3c0c261dc02a2235817b078b73 |  |
| 2026-11-24T07:51:23.082375+00:00 | retry |  |  | test:own_requirements:original |  | 8d4a9b091baedd832af9100863fadb33bb3565107bf6f134d12d9ccafd8b49ab |  |
| 2026-11-24T07:51:24.894470+00:00 | retry |  |  | test:free_form:original |  | 6a635afffdbd08798d90ffe907a37958c45b51027786b808a49f002186a5573f |  |
| 2026-11-24T07:51:24.898972+00:00 | retry |  |  | test:own_requirements:original |  | e1ef71686d72cdcaa0198d93c52fdd30234d06a356910d8fbc86026e47cf6ee3 |  |
| 2026-11-24T07:51:27.670262+00:00 | retry |  |  | test:general_rubric:original |  | 0e9f69dc8ab6b31ef4b1c17344496434df453f0e0e1bafc1bf840fb5299089cf |  |
| 2026-11-24T07:51:27.902655+00:00 | retry |  |  | test:separate_scoring:original:A |  | a2688d65899d26ea3fad90916b15904af5a1edf47b1bb406b1c65e593a41a07a |  |
| 2026-11-24T07:51:34.950569+00:00 | retry |  |  | test:separate_scoring:original:A |  | fded798addf75c28facb03b314cebcd56fe91d0196f7693ecd1408539a1ea4a6 |  |
| 2026-11-24T07:51:41.276846+00:00 | retry |  |  | test:free_form:original |  | 949fc8ec13c4d97ee123b4c7d3b1dab3389d0d8def9502183f81ae682cd9c04d |  |
| 2026-11-24T07:51:42.993256+00:00 | retry |  |  | test:separate_scoring:original:A |  | 548ad0902af862179ce7313abc6f06e0b937992cc8fd2088390f42c62b1709b4 |  |
| 2026-11-24T07:51:43.130864+00:00 | retry |  |  | test:separate_scoring:original:A |  | 643de1868c4d780c5c3b48ced98be084086b4742305cb9dbc1ba9818db7482e9 |  |
| 2026-11-24T07:51:44.986730+00:00 | retry |  |  | test:free_form:original |  | dfe4b9f2d6ae21813884c9659fdb96428dbb68d5350438bed61bc7b73943a861 |  |
| 2026-11-24T07:51:47.234263+00:00 | retry |  |  | test:free_form:original |  | d4f093e36c192a21b0154041541aac6ee03d42c5cd85369ae2f2558effd90e6b |  |
| 2026-11-24T07:51:49.262295+00:00 | retry |  |  | test:separate_scoring:original:A |  | d6ec511cff7ae63bb9c02416719b4e71e1b64c1df3174fe5390239c69bf902de |  |
| 2026-11-24T07:51:50.394252+00:00 | retry |  |  | test:free_form:original |  | 865f1f512631d220e2cd465d8d355b01804e8f14d7081efd983ccaf13e0bd198 |  |
| 2026-11-24T07:51:53.444132+00:00 | retry |  |  | test:separate_scoring:original:B |  | b3548eb3d746b11d449f035c10c61ffe08750c2256137bd5eb5d740a2137ee77 |  |
| 2026-11-24T07:51:53.525453+00:00 | retry |  |  | test:free_form:original |  | b473ea638e35cc39fb250a48d8c3ac1e5588aa1559da148592c3f34624639e53 |  |
| 2026-11-24T07:51:53.542004+00:00 | retry |  |  | test:separate_scoring:original:B |  | dc9fbe43b57eeb0b3e9785573a2518703d2ba8a70f787879abd50210b7d0b59e |  |
| 2026-11-24T07:51:57.583302+00:00 | retry |  |  | test:free_form:original |  | 557ff026090236ba54d1a49e6f02c2e041f98adae979fc36caabe8c549f95912 |  |
| 2026-11-24T07:51:59.677694+00:00 | retry |  |  | test:separate_scoring:original:B |  | bead17485f9a02e2bcd332c917dc965be354f76b1fafc8f7eed80072192fa761 |  |
| 2026-11-24T07:52:01.480214+00:00 | retry |  |  | test:free_form:original |  | caeb5e398bd19d04dabe62c516fdb727b176addc13b40869aeb046c847d77869 |  |
| 2026-11-24T07:52:01.559587+00:00 | retry |  |  | test:separate_scoring:original:B |  | a6a78d8bab3f741373ef08bbbd3acba131aa91cec7474b2b1df5402ecba67dae |  |
| 2026-11-24T07:52:05.728743+00:00 | retry |  |  | test:separate_scoring:original:A |  | 8c87c62bc4119384c9e4235e31951c3fe2c953b4245f8a0f4f76e435e674c236 |  |
| 2026-11-24T07:52:12.322541+00:00 | retry |  |  | test:separate_scoring:original:B |  | 2ee751a4830b4b89b8a53db4c8b69c2fe9cd1f24940a0396a80dee6dbec2294a |  |
| 2026-11-24T07:52:13.208684+00:00 | retry |  |  | test:free_form:original |  | 779bd78501b212ef7cdb4c74e928a890f1ffc5c73243af0d0250522c4d8756a6 |  |
| 2026-11-24T07:52:16.920697+00:00 | retry |  |  | test:separate_scoring:original:A |  | 936bce2ffb7cddab52d44558ead552fee0b1f1d58e4d70f75e6495dadf828fd2 |  |
| 2026-11-24T07:52:20.308274+00:00 | retry |  |  | test:general_rubric:original |  | 50b44789bea1f7fd280c293e0db5fb3b33bb32f8b5a68c334f8734b09e564fe2 |  |
| 2026-11-24T07:52:24.713049+00:00 | retry |  |  | test:separate_scoring:original:A |  | c0b14b67b3b00a58c7f8b92272a4ae98be0d6e49fea636dfcf1fe1b7b6f6701c |  |
| 2026-11-24T07:52:24.826373+00:00 | retry |  |  | test:general_rubric:original |  | f49121f6bc9eb2733d34233a29a49349880b5fb43ea7a70545b9ed87da0cb940 |  |
| 2026-11-24T07:52:28.895554+00:00 | retry |  |  | test:free_form:original |  | 63342f0acd534e3454e8fa79a209156e6dc52f982e5559d0d46fdb095cd9be0f |  |
| 2026-11-24T07:52:30.844131+00:00 | retry |  |  | test:general_rubric:original |  | 1307f387559d3a93d907157af22b649d7e1e26d477b6d29bb0695fe148d3d40e |  |
| 2026-11-24T07:52:32.143530+00:00 | retry |  |  | test:separate_scoring:original:A |  | b57e792df62f5b74ae0893be575a32b3a8074fcafcc44912b1b9fecac675b428 |  |
| 2026-11-24T07:52:32.707066+00:00 | retry |  |  | test:separate_scoring:original:A |  | 20aa71d9a377b7e752ffe736f6f5fa486aa962a00b4214f058f59d07394bda7c |  |
| 2026-11-24T07:52:34.185485+00:00 | retry |  |  | test:general_rubric:original |  | d4effb28487b537a18364049844602d26d843ff1cb6f29f94043372af1e085e2 |  |
| 2026-11-24T07:52:34.617250+00:00 | retry |  |  | test:free_form:original |  | 249466908e189e829c1353d7fc828ad0baeba8787d920b3e71a8abd94a8ff716 |  |
| 2026-11-24T07:52:47.080824+00:00 | retry |  |  | test:separate_scoring:original:B |  | f6fd44b3f6aa86cc8e5da4809585fd5aaa77c5946c0dd86ebba13c78de2ad896 |  |
| 2026-11-24T07:52:47.103380+00:00 | retry |  |  | test:separate_scoring:original:B |  | 626b8184efeacdc45e9385d68060ed860445c9ba1641f9ae2846680993b2bf88 |  |
| 2026-11-24T07:52:57.684265+00:00 | retry |  |  | test:separate_scoring:original:B |  | d9f8ad6eb7b30274dcbd8c8a5d22e7a80b352d3878ac8c0bcc8323a8f9050de3 |  |
| 2026-11-24T07:52:58.422085+00:00 | retry |  |  | test:general_rubric:original |  | d580cb186f3a33ed39289ce17a76c7312c6a8f0ada2f21aa4c2fd7c7b75a33d5 |  |
| 2026-11-24T07:53:00.348984+00:00 | retry |  |  | test:separate_scoring:original:B |  | 62aa6bf286221f18fa7fea723ed92f4b3b5ec7da7214e891c2907ab0da97079b |  |
| 2026-11-24T07:53:02.293264+00:00 | retry |  |  | test:free_form:polished |  | 7527c217a1cc5c25b6dea0fb293b6fc072885856b8194fd5522d9c1a389c558f |  |
| 2026-11-24T07:53:04.125471+00:00 | retry |  |  | test:general_rubric:original |  | 817849f26ade4ece03fe0b7defe707f5a84f5fff1114c8a5f4d9c29c14e1f44f |  |
| 2026-11-24T07:53:08.334879+00:00 | retry |  |  | test:free_form:polished |  | 4edb6f34d12883188beb713b2d63a4b775394f1b39ad9d8e90fcb3a5faff2511 |  |
| 2026-11-24T07:53:08.349734+00:00 | retry |  |  | test:general_rubric:original |  | 663a9e630df7bbdf734e004339cd09fdd40ff6b9b32e6749df5f2a37fcad2ef8 |  |
| 2026-11-24T07:53:12.200117+00:00 | retry |  |  | test:item_checklist:original |  | 8026f69f9edde537a5aaa1bfc3db6f904c0250d6e744412aac0cea41fd526093 |  |
| 2026-11-24T07:53:14.156346+00:00 | retry |  |  | test:general_rubric:original |  | 22a3e49dff8b1e021fc63b3a5a7462ef17730c1faa7618ad7ae3170451e9d537 |  |
| 2026-11-24T07:53:18.624749+00:00 | retry |  |  | test:general_rubric:original |  | 59f8470ae36790569fc46b31408a316323865a8b471ad6e49d73bd9ab2fcd393 |  |
| 2026-11-24T07:53:19.011184+00:00 | retry |  |  | test:item_checklist:original |  | 537504151412adafb0e2701a480fdd4feb16a21035ea1c8cdb1090cce39b3f2c |  |
| 2026-11-24T07:53:24.018369+00:00 | retry |  |  | test:separate_scoring:original:A |  | 912a9e6c89b51ea72c37c03724cbc42200e5509a6e55244de275a10729f51ed9 |  |
| 2026-11-24T07:53:24.130821+00:00 | retry |  |  | test:general_rubric:original |  | c53bd654495fd4645d1fa517c6b2bf20c815837d63947da7fec646d831f94071 |  |
| 2026-11-24T07:53:24.317324+00:00 | retry |  |  | test:item_checklist:original |  | ebc70ab3a12f345951021ce29e4ad6bdbe45880a6494cb140c7779c5082969e5 |  |
| 2026-11-24T07:53:29.085683+00:00 | retry |  |  | test:general_rubric:original |  | 9019a65b3707bd1b787f961938e95aebd56000f6ef66cff93e8afe0f841d8280 |  |
| 2026-11-24T07:53:30.853806+00:00 | retry |  |  | test:item_checklist:original |  | 0835a63143b64a099cebc2edb6ab54830313b98d3792c3c7e89c9db78276cb45 |  |
| 2026-11-24T07:53:34.987906+00:00 | retry |  |  | test:exam_prompt:polished |  | 61855acf3016b3f7d45bfce7cee5f15d1d587fbb76b62f5dd4c11942c2afde73 |  |
| 2026-11-24T07:53:39.267298+00:00 | retry |  |  | test:free_form:original |  | 1f673082a33793bb78b19680c4391d2aa57d6409e2114cb82908ff240c84b93f |  |
| 2026-11-24T07:53:40.672141+00:00 | retry |  |  | test:item_checklist:polished |  | 933e5bf3ad68710ca0d1948fb6b11eaeae1e088a23f474c456df3a1f022d81b0 |  |
| 2026-11-24T07:53:40.963178+00:00 | retry |  |  | test:item_checklist:original |  | 269c347d359dc46bb3be17456086e6990a55331bd8c06197cd3a746f182c987c |  |
| 2026-11-24T07:53:42.810708+00:00 | retry |  |  | test:exam_prompt:polished |  | 21ee7f1f88dc19bf9bdcce58dd20601824b140943bf218204a4e3d2c501166ae |  |
| 2026-11-24T07:53:42.914906+00:00 | retry |  |  | test:general_rubric:original |  | 8a4fc2471cbc346090d231d394a182b0ba7b948cf40a01126fa03d42001bfa10 |  |
| 2026-11-24T07:54:00.856839+00:00 | retry |  |  | test:separate_scoring:original:A |  | 76256ef13ebb2c71b3fbd928e8ef38daa91dbfaccf23e8d36cb3774b9b48aaf6 |  |
| 2026-11-24T07:54:16.529526+00:00 | retry |  |  | test:free_form:original |  | cb21652b530b1cb7730bf048a8b1dbc3a703b93791e95ace3f4fbb93ada727a5 |  |
| 2026-11-24T07:54:17.022913+00:00 | retry |  |  | test:item_checklist:original |  | aa1307112759e68194f32c2024c6ebd74274a1ef31c6f3e705cd907ccd6ad3a7 |  |
| 2026-11-24T07:54:22.107772+00:00 | retry |  |  | test:free_form:original |  | 6fba8f758292c3b9845a0cd20700078977e85faecb550d7416347e4b1fc73055 |  |
| 2026-11-24T07:54:35.937799+00:00 | retry |  |  | test:general_rubric:original |  | ef98d67d5584652c061c4bf57540d434401a941adc9cb3b2880134b108c5abf1 |  |
| 2026-11-24T07:54:38.007544+00:00 | retry |  |  | test:separate_scoring:original:B |  | 261392d6a5b080630f3da2d4518763fb83b232068bc780fa9a6373becd96513a |  |
| 2026-11-24T07:54:48.257423+00:00 | retry |  |  | test:free_form:polished |  | e7d84b0dde901e156491b09b634ccfad6f629686330bf6b7ff9e7ec893e1486e |  |
| 2026-11-24T07:54:50.158101+00:00 | retry |  |  | test:item_checklist:original |  | 29e4e9d05889f5e53e3f0716b58de89c12244c9a5c03e0bda9a422466f99c0fd |  |
| 2026-11-24T07:54:52.002723+00:00 | retry |  |  | test:item_checklist:original |  | 435555afd5a48e4973872604211287f2374361e412fecdda44bad5221664238f |  |
| 2026-11-24T07:54:58.432875+00:00 | retry |  |  | test:free_form:polished |  | cb8a93b1ac11f1f003f39d71067574d7888e256499d7e4c0f1f0d061f84fafec |  |
| 2026-11-24T07:54:58.949021+00:00 | retry |  |  | test:item_checklist:original |  | ce1dda9c7f1f3e8b3ddb7fb91bf05918955372b45bc3fa9442d115c4c1b8aedd |  |
| 2026-11-24T07:55:00.384577+00:00 | retry |  |  | test:item_checklist:original |  | e9bf201d0869d86c38b7b399c8ad1d3dff7d04f229af662a10ed10c60175dfcc |  |
| 2026-11-24T07:55:00.887540+00:00 | retry |  |  | test:item_checklist:original |  | 0c9e4ad15a0e5689b20fd8a4990e375de1725aaa14e52fa8cd212c214eb2a01c |  |
| 2026-11-24T07:55:02.298786+00:00 | retry |  |  | test:exam_prompt:polished |  | eb9d3a406dc21e96525157b8ce1b4c9c2db4bc621c89edc0357d19bddcf39a83 |  |
| 2026-11-24T07:55:05.861156+00:00 | retry |  |  | test:item_checklist:original |  | a277dab65731ef03e0bbcd49f644807cc85cd7011cc9d48d40fbd420e6765ccc |  |
| 2026-11-24T07:55:10.671078+00:00 | retry |  |  | test:exam_prompt:polished |  | f5119cf0d5ecfa84a48254c22e81c19295a26425efc81a54e07fc6770c370a7c |  |
| 2026-11-24T07:55:17.041607+00:00 | retry |  |  | test:separate_scoring:original:B |  | 34586da6806f26c6582059f226dc193b9fc031e14545201189f01c004a5fb8e2 |  |
| 2026-11-24T07:55:27.852761+00:00 | retry |  |  | test:general_rubric:original |  | 495c12ff6cf7dd0342ba8cbc31055ece43cbfcca3083b67620d54d8c4ad572d2 |  |
| 2026-11-24T07:55:32.577984+00:00 | retry |  |  | test:general_rubric:original |  | b98c903cb236da8de90dce274c3cff4faa33820decd8ec6ff7e2e12b9fa30e46 |  |
| 2026-11-24T07:55:38.439678+00:00 | retry |  |  | test:general_rubric:original |  | 55437b181db758ba1ccdf69d42ddde60070a7b3fa5db61ae7aea3f68ebbad5fe |  |
| 2026-11-24T07:55:38.510187+00:00 | retry |  |  | test:separate_scoring:original:A |  | 616fe4f84074381cc7bc989091e4e9f83cac8b6fcbb85cfec03a6cae0ba3a651 |  |
| 2026-11-24T07:55:43.572275+00:00 | retry |  |  | test:separate_scoring:original:A |  | 07a39c8d9bfd7216f11646afc8976d52afc23904c8ed1c54fc43aef09eb51c60 |  |
| 2026-11-24T07:55:46.604559+00:00 | retry |  |  | test:item_checklist:original |  | 7d653773be1139a18f1def3066cb7b3932a1215daf2415f12299df8807eb0f3c |  |
| 2026-11-24T07:55:59.806145+00:00 | retry |  |  | test:item_checklist:original |  | 0629f36ad0a3bbd4c51c16ffa88cafa56a724b63779e2767f8f25c3b4f32b71c |  |
| 2026-11-24T07:56:01.180592+00:00 | retry |  |  | test:general_rubric:original |  | 445110cb1b31156cb8e5f1367b929a0723eb3b0a034bef79aa16f93dc9d6f707 |  |
| 2026-11-24T07:56:01.911272+00:00 | retry |  |  | test:item_checklist:original |  | 466fdda7b10ae463be0eef183a3087e08d7a1155b33f3fd0f3b3baa730a9eaee |  |
| 2026-11-24T07:56:04.378269+00:00 | retry |  |  | test:item_checklist:original |  | 984c1c8259ef263a13d5c1515061ad8f397b72dd3e824b9470f8bbea5be093c8 |  |
| 2026-11-24T07:56:04.469220+00:00 | retry |  |  | test:separate_scoring:original:B |  | 1ede071ef1264b8afa10e0827c8fd5559f54234846cb35c36396bcd9f94de8f4 |  |
| 2026-11-24T07:56:06.600765+00:00 | retry |  |  | test:free_form:polished |  | 5399c3eae9c3a6ea1c321aee15a8f3a72765a2ea8869d2f3af63daa271b9c508 |  |
| 2026-11-24T07:56:07.412214+00:00 | retry |  |  | test:item_checklist:original |  | 658f28183b12a0f62493cc773aef3259ece2e79d472579f1c782afbf9d4073ff |  |
| 2026-11-24T07:56:09.158623+00:00 | retry |  |  | test:item_checklist:original |  | 14969a4f4cae5152d65a1a8a3fa3ad50659c00be2262b38d8bc1bca398629d4b |  |
| 2026-11-24T07:56:11.221543+00:00 | retry |  |  | test:separate_scoring:original:B |  | cf6790ed0061bd85d3f48b367167b8cba3342a0c1eb28a227308f2356c4cbbdb |  |
| 2026-11-24T07:56:13.382908+00:00 | retry |  |  | test:free_form:polished |  | 620f81795b46f7936e12f51d18d8dd9194c29885f470371864fc91e4e00eff57 |  |
| 2026-11-24T07:56:14.419962+00:00 | retry |  |  | test:item_checklist:polished |  | 2ebc0a4251857a97bf7dcfc340867a34a636dd37617ece6befe5d512c5107abf |  |
| 2026-11-24T07:56:17.766277+00:00 | retry |  |  | test:free_form:original |  | fe3cddca3de92f5df81b063c25bcf714b2c53e1dc41eea5ea5e315f4bf0e3c79 |  |
| 2026-11-24T07:56:21.339081+00:00 | retry |  |  | test:item_checklist:original |  | 7348dac2ff7b56f1617b8c7115d25184e2651b36366051e400c9402b763014ee |  |
| 2026-11-24T07:56:23.319171+00:00 | retry |  |  | test:item_checklist:polished |  | 375e86ebd5a2e685e378f2ac98fe906bc7205a9465130970d81afec46ed8d7a7 |  |
| 2026-11-24T07:56:26.402485+00:00 | retry |  |  | test:separate_scoring:original:A |  | 88659756ddfec46591704bafaef1b0f75a60256d2541a9f7c56e03afd18e226b |  |
| 2026-11-24T07:56:27.197503+00:00 | retry |  |  | test:own_requirements:original |  | 2ef1b25589b3d05102792e3ae77586be6504686ee290d2ec168b30a01b7a49e6 |  |
| 2026-11-24T07:56:28.569420+00:00 | retry |  |  | test:free_form:original |  | 513559cfd44ea6fdadee8821f3c50229b72ff33d11911c82d8dfb5948b4ca76e |  |
| 2026-11-24T07:56:29.444545+00:00 | retry |  |  | test:item_checklist:original |  | ef50a87d795e156d7b19e9622eb126d40d68d3512dad5459d73324c1b04eec66 |  |
| 2026-11-24T07:56:31.448053+00:00 | retry |  |  | test:separate_scoring:original:A |  | 471c762180baf5b22d680e26c845aace446102ee307bebd5eea3cd2273ca6fd4 |  |
| 2026-11-24T07:56:33.621057+00:00 | retry |  |  | test:own_requirements:original |  | 312f0a524749c02d2b39ad82dcb04206f25be69218bfee9ebca3009d58f2f85a |  |
| 2026-11-24T07:56:41.413003+00:00 | retry |  |  | test:separate_scoring:original:B |  | 709d151b2d5ef28934c1141e0bbb7f6f653cec3b168730ea41eae3dd58c7d0e5 |  |
| 2026-11-24T07:56:43.790740+00:00 | retry |  |  | test:exam_prompt:polished |  | e25c68db9eec28edc49aff35679deb63b41cbf5547695a34dff67f22e80c22e9 |  |
| 2026-11-24T07:56:45.214815+00:00 | retry |  |  | test:general_rubric:original |  | 3dad37470c0785ee85ba5ed78310255c22f254352405100fc6ac5da1f57e2486 |  |
| 2026-11-24T07:56:46.507319+00:00 | retry |  |  | test:separate_scoring:original:B |  | 8876c0f108fd4840d03b8dfdf89a0ba35081eb9c7b98ea259f425344d2035f01 |  |
| 2026-11-24T07:56:49.388698+00:00 | retry |  |  | test:exam_prompt:polished |  | 7ed613772c0c7f2fe23b6ec8265bdddf8781b800aa5cd3c1a3723231a381a8dc |  |
| 2026-11-24T07:56:49.558991+00:00 | retry |  |  | test:separate_scoring:original:A |  | f3bfd315037fc4a82bbcfbfb2994d006e198dab25940dac0e7a79f403c0f968c |  |
| 2026-11-24T07:56:54.670779+00:00 | retry |  |  | test:separate_scoring:original:A |  | 80796b72b75057e6618e086af03d54a885222215056693c92d3cb05d4c507af6 |  |
| 2026-11-24T07:56:56.109777+00:00 | retry |  |  | test:general_rubric:original |  | 41b23c35eb8e9558c347b10bfcef6e208b3b64381376f7ae95acccdd4c97b8ab |  |
| 2026-11-24T07:57:03.371251+00:00 | retry |  |  | test:free_form:original |  | dff258367c6120325030404a616b847d97b5d19f5337b31d712fd55f87d3b675 |  |
| 2026-11-24T07:57:07.606186+00:00 | retry |  |  | test:separate_scoring:original:B |  | ecbb0f9c0cc72c2dd88662b56f0ed5ae291515eb7f96bf509c21e38fab7a5b62 |  |
| 2026-11-24T07:57:10.001224+00:00 | retry |  |  | test:free_form:original |  | 9f4074fedc56826337229140df7f0eb54c96c5de5e4e5bfe9330c6063691ce2d |  |
| 2026-11-24T07:57:12.071499+00:00 | retry |  |  | test:general_rubric:original |  | 875508d66400c12e38f1d96a8c0a953797fddcc26a1f4636414dcb2e80867ace |  |
| 2026-11-24T07:57:13.901956+00:00 | retry |  |  | test:separate_scoring:original:B |  | 07a9d7be6837284a1abd89d65d25ab183bb9354c644d3f794f560341dce80d9a |  |
| 2026-11-24T07:57:17.119811+00:00 | retry |  |  | test:general_rubric:original |  | f3089963fe65f00f7bd8611507a17dcadc0f79d4bc876efa5567d75e9e1d544e |  |
| 2026-11-24T07:57:31.740182+00:00 | retry |  |  | test:separate_scoring:original:A |  | 240db6b0278c93dca4f718d90b5c005a6f758d925163a0ca8a0cfaf5baf8fea3 |  |
| 2026-11-24T07:57:37.287294+00:00 | retry |  |  | test:free_form:polished |  | d564926f09d19639d97d27b5a6f7626c3a892b2a85295ac1330401c2a54d6848 |  |
| 2026-11-24T07:57:48.959292+00:00 | retry |  |  | test:free_form:polished |  | 06eb5684a1fc287e7ffc8df5ec018a5dc86ed38af958e5a2a45ce584f242888f |  |
| 2026-11-24T07:57:49.512662+00:00 | retry |  |  | test:separate_scoring:original:A |  | c2bf3c31423d1d7b14fab27f1391dbe915c6e241cd2cd1a79138f921f0360d84 |  |
| 2026-11-24T07:57:50.109918+00:00 | retry |  |  | test:separate_scoring:original:B |  | 3e012d13bbbebb79e800cd96caa92f408ace247ee61f211940bdfb3f8bc826d9 |  |
| 2026-11-24T07:57:54.561475+00:00 | retry |  |  | test:separate_scoring:original:A |  | afe546bbf2135c277eeb0d2b3c0bb19d51f2e1534394643f74a99e4ddaed7f00 |  |
| 2026-11-24T07:57:58.898169+00:00 | retry |  |  | test:general_rubric:original |  | dc50def23d1f0c46ba228d46b9b5b99b25d81ff387ee550d6d6a1d98dd7bdc6d |  |
| 2026-11-24T07:58:03.786262+00:00 | retry |  |  | test:general_rubric:original |  | 5f13f5d413476f3a22c09756c4f2abe113a5e65273652a7ea8ec46fd21ecbdbd |  |
| 2026-11-24T07:58:04.700732+00:00 | retry |  |  | test:item_checklist:original |  | ccfc398e653f51d4ecbc5cc06cbc5d6fa4723b1e8534e5871009acf18991f842 |  |
| 2026-11-24T07:58:05.307894+00:00 | retry |  |  | test:separate_scoring:original:B |  | a87583d06c6ec1fd35cb43bd675a13a3fa509d8056e8e94bbd992f80b9f0ab79 |  |
| 2026-11-24T07:58:10.445837+00:00 | retry |  |  | test:separate_scoring:original:B |  | ae5e7f888939efb82f2d257643bc4edec41f49bcc3513ffdb197692f336a13ce |  |
| 2026-11-24T07:58:30.541872+00:00 | retry |  |  | test:own_requirements:original |  | 086747e301f3766b0079441cf72a06445e64daa3b93fd9785eec6c9e9afe131c |  |
| 2026-11-24T07:58:40.391308+00:00 | retry |  |  | test:separate_scoring:original:A |  | 1f52d25a647c4e3ba3eb3b07cafa288a5f7d3ab2419c313d11b82629d46148ca |  |
| 2026-11-24T07:58:44.585492+00:00 | retry |  |  | test:free_form:original |  | d53206cdfdd24cf8a617efa0e9952da0b2f014b33bece831ddd5046c07c35791 |  |
| 2026-11-24T07:58:48.250563+00:00 | retry |  |  | test:separate_scoring:original:A |  | bb88fabb82ff29763694f257c43a4b1d05088abaf2618006321047dcccfa2446 |  |
| 2026-11-24T07:58:49.386648+00:00 | retry |  |  | test:free_form:original |  | 84bb7f11391d23c6451be844f10d198c60f6d3eba218c4a75b49d841cf1bb2f0 |  |
| 2026-11-24T07:58:53.167066+00:00 | retry |  |  | test:separate_scoring:original:A |  | 7c20930115b509229595d5a4e60f4e8a70fec599b84f2fd64e6cfd7c47a7ebc8 |  |
| 2026-11-24T07:58:55.199308+00:00 | retry |  |  | test:general_rubric:original |  | fbbc85b5f8adfc6fd0f5e2b145a84776a2943045c1bf514c133e579e58025f5a |  |
| 2026-11-24T07:58:56.918310+00:00 | retry |  |  | test:separate_scoring:original:A |  | 663d00b220cdb1054d2ccf90cee5ad7a5d5daf6c96f7c306d0107007ddac07fc |  |
| 2026-11-24T07:58:59.320554+00:00 | retry |  |  | test:item_checklist:original |  | 21cfe46d2908e6fad7f30e7ccfcf507d9c2f9bc860ec6a301694b035244c1311 |  |
| 2026-11-24T07:59:00.055991+00:00 | retry |  |  | test:general_rubric:original |  | ce361942403596020f2b011e28382eac763b8ffe1e513a9ae52ffecb8741345f |  |
| 2026-11-24T07:59:00.431230+00:00 | retry |  |  | test:separate_scoring:original:A |  | dae50089d7a45c3d6af883c0f50dbc650754c9388ad9b7e1361e2de9d48cbb99 |  |
| 2026-11-24T07:59:02.105428+00:00 | retry |  |  | test:separate_scoring:original:A |  | c3926490387eceaaea38e11bdded27dd8060a8ac38fb9ad5c79b35bc6dcb8725 |  |
| 2026-11-24T07:59:03.711342+00:00 | retry |  |  | test:separate_scoring:original:B |  | 07c058caaa673a502e62a5370c7149e6dd099550953a3664e60c9c638b2c01ef |  |
| 2026-11-24T07:59:04.077247+00:00 | retry |  |  | test:item_checklist:original |  | a238b568e8b3ffa666e2c98311788a2628b5ef0517bc30e0bf70e1e0f72550c3 |  |
| 2026-11-24T07:59:07.064254+00:00 | retry |  |  | test:separate_scoring:original:B |  | cc55e68a7241f8c8832104c0dbb0715a2a0a260d6cc1e2e59a7b82a6129972be |  |
| 2026-11-24T07:59:08.730084+00:00 | retry |  |  | test:separate_scoring:original:B |  | 7a238c231e0dff9d33a5bbefb8a200e11a597563858f1d54fc0afcf6bf1e194f |  |
| 2026-11-24T07:59:12.564148+00:00 | retry |  |  | test:separate_scoring:original:B |  | 42a077bcab0693955ad7514f87ff184ff104ed2888e318470e96c731f9eee639 |  |
| 2026-11-24T07:59:20.722596+00:00 | retry |  |  | test:separate_scoring:original:B |  | 4095520237b06554aa850b7ec8104176d7fd1803ec91114042cddf2cd68260ec |  |
| 2026-11-24T07:59:57.176561+00:00 | retry |  |  | test:separate_scoring:original:A |  | 8e1b9459831b6a64d27ae1c4f31f8524dc9b8d46dbe4412703adc9602720efcc |  |
| 2026-11-24T08:00:10.549899+00:00 | retry |  |  | test:item_checklist:original |  | 329514f2847aa44429871a59f7db89416d02f9a763a47534a35944ac29e33dbb |  |
| 2026-11-24T08:00:15.550992+00:00 | retry |  |  | test:item_checklist:original |  | 1698e1e98bd5dc35c785c79d0befea6621d1b08ec0d4abb30b8ada8347dd386d |  |
| 2026-11-24T08:00:15.867290+00:00 | retry |  |  | test:free_form:polished |  | 6e6d8548a06685f52100be1b170e7b4b99ad87bd741827e1c4954587647a4a3d |  |
| 2026-11-24T08:00:21.544043+00:00 | retry |  |  | test:free_form:polished |  | b8432bffe19ac8dd135efdca82c6c4f18ace7140a8b252b69513013e534eb58d |  |
| 2026-11-24T08:00:25.414901+00:00 | retry |  |  | test:free_form:polished |  | ef02e7a14026716056ed9b3f66ea7763317e01b89eacdd1429ad85e878da387e |  |
| 2026-11-24T08:00:30.264275+00:00 | retry |  |  | test:free_form:polished |  | edd07ed0f0882c5a16dfbef55e740e7fc299faf672b9307e79d9d1424ade58e1 |  |
| 2026-11-24T08:00:31.582184+00:00 | retry |  |  | test:general_rubric:original |  | 9f3ed9cb09ff93a50041b40fddb38c1c031515ef7036c6a2b71579cda86add69 |  |
| 2026-11-24T08:00:36.607645+00:00 | retry |  |  | test:general_rubric:original |  | f37c4f49863a9917014f6544ffd641856737eb00dc92500c9f8e7f8677d2e7bc |  |
| 2026-11-24T08:00:51.180817+00:00 | retry |  |  | test:exam_prompt:polished |  | a6b2b35b7fcdd2a90740fbbef79f0728ebfa423c82465e0ef6eef3e38e235a89 |  |
| 2026-11-24T08:00:58.544512+00:00 | retry |  |  | test:separate_scoring:original:A |  | 8527311f07d1e0a016b8c7ef29131a175adc06817f956ee3efbb8a9ce6a25e26 |  |
| 2026-11-24T08:00:59.545230+00:00 | retry |  |  | test:item_checklist:original |  | 79fd7d18cf916575e18354c10500c9ca9dd39e197150784df7bc74fefa44d20d |  |
| 2026-11-24T08:01:00.518867+00:00 | retry |  |  | test:general_rubric:original |  | 947205e339e753136f8d77cd78ce7faae9a4673824c598ef0222977d8497585c |  |
| 2026-11-24T08:01:01.720839+00:00 | retry |  |  | test:exam_prompt:polished |  | 766f447fd92db7443272f722074ea8540efa0e3b796c9edaffd25d98ce95d6b7 |  |
| 2026-11-24T08:01:03.430119+00:00 | retry |  |  | test:separate_scoring:original:A |  | 6448a8f679f386c4223fd2dc2a1f5ea0805dfd956b65853c2d35c2459161770c |  |
| 2026-11-24T08:01:05.519236+00:00 | retry |  |  | test:item_checklist:original |  | b056246e1ac28fba8ba42cc2f585b3ae7d1b963c62ac37c465cb84bd4e4f934f |  |
| 2026-11-24T08:01:07.575418+00:00 | retry |  |  | test:general_rubric:original |  | 2d05f3f7c788009912dc8a32e29d40195f33aa728ff5297eb1338921a44fa775 |  |
| 2026-11-24T08:01:13.181922+00:00 | retry |  |  | test:separate_scoring:original:B |  | 8b6376975cb4ae6f1ace0df78cdc2d5075e1f06dc88b0fd4320ade1233c5644d |  |
| 2026-11-24T08:01:15.068681+00:00 | retry |  |  | test:separate_scoring:original:A |  | d0b85d68564d41c16e494c02c4c9cc0845c612c8ec884570a7d4adf26abf2a44 |  |
| 2026-11-24T08:01:16.842928+00:00 | retry |  |  | test:free_form:original |  | 95fc278c23936c3409aba737baa250a2ba5e136e3cdc29f3e4a6031c48f1b369 |  |
| 2026-11-24T08:01:18.859697+00:00 | retry |  |  | test:free_form:polished |  | d10c1fee46b84cf0c611819f7ed830e65412d06584738a53253795842396d1d3 |  |
| 2026-11-24T08:01:20.727870+00:00 | retry |  |  | test:separate_scoring:original:B |  | bdf214232025d6b44248e6bd8e0c92186190c749fee5b38b419efa9ae0d00dae |  |
| 2026-11-24T08:01:20.965386+00:00 | retry |  |  | test:exam_prompt:polished |  | e4b00fac7478478d22b294750f3c362467141cad35d683484dd9838c0287b134 |  |
| 2026-11-24T08:01:22.586368+00:00 | retry |  |  | test:separate_scoring:original:A |  | f4ac36c976c35c3677a17a5985ab24abff026d4c8255ec0fc34a6eb57e4466ca |  |
| 2026-11-24T08:01:22.658884+00:00 | retry |  |  | test:free_form:original |  | 48ba530b584dd4bd3a94e6a6bfe5364518e75d3a421e3a63d31f757b6b6665b1 |  |
| 2026-11-24T08:01:24.344854+00:00 | retry |  |  | test:separate_scoring:original:A |  | 0dc1f2664c8ca920ab1bfdeda16738875cfd5521ebe653e027c83b50eea7c63b |  |
| 2026-11-24T08:01:24.638460+00:00 | retry |  |  | test:free_form:polished |  | db949c410d6b6c49a9550ea6d8f6bce7b21fd9e72fe0fbe0b2b9cbc0e7884b59 |  |
| 2026-11-24T08:01:26.147033+00:00 | retry |  |  | test:exam_prompt:polished |  | 6512531dbc4428b6de1777014df93393441ccd1977f109efb47018646166a405 |  |
| 2026-11-24T08:01:29.161766+00:00 | retry |  |  | test:separate_scoring:original:A |  | 10e985831132a25c36c06dd4c43c8125d7c887c46eedbe15d385b2fb922b3d61 |  |
| 2026-11-24T08:01:33.244027+00:00 | retry |  |  | test:free_form:original |  | 38c52fcc3efddeca9cbab2486449acd59167294e6ac04c4e6ec1eda22174f5c1 |  |
| 2026-11-24T08:01:37.629340+00:00 | retry |  |  | test:separate_scoring:original:B |  | c86f86c54a38d914f28020c807efbb03fa059da392a9806c5180f9b21c377ffa |  |
| 2026-11-24T08:01:39.915292+00:00 | retry |  |  | test:separate_scoring:original:A |  | 463249eb48312a8cce070bd1c34d92ac387df2a34ac26d81aaf1e01e0ee44b30 |  |
| 2026-11-24T08:01:41.409220+00:00 | retry |  |  | test:free_form:original |  | c4282fae991b4c85aa8587dbf16f85773425e956ef0df8429dbbc3b96d189530 |  |
| 2026-11-24T08:01:43.525909+00:00 | retry |  |  | test:separate_scoring:original:B |  | a5323ed94c02617cf6328353728aabb6a8ac1560f9deee17d9725736713650ef |  |
| 2026-11-24T08:01:46.086776+00:00 | retry |  |  | test:general_rubric:original |  | 05d702a9976adacbb7bdea4a8e98ca125211d1d509e92f85fe875302c5d85aaf |  |
| 2026-11-24T08:01:48.185993+00:00 | retry |  |  | test:separate_scoring:original:A |  | 96d0e2fd2af969fffcb78458c28402cd7c68e0af50dcb88631034a670b826fac |  |
| 2026-11-24T08:01:50.293187+00:00 | retry |  |  | test:separate_scoring:original:B |  | 9f0b6f45f376f6edc36aea4e8efe017b02805614cdaba8ae088f4a1575ff5939 |  |
| 2026-11-24T08:01:50.787097+00:00 | retry |  |  | test:separate_scoring:original:B |  | 6553eae4b9b3bb955036d609816ae8b3616807db58869bd8e56797bc46bf16db |  |
| 2026-11-24T08:01:52.672709+00:00 | retry |  |  | test:general_rubric:original |  | 999e85c05f03fb3a40477a8e704ba7f0aed65a0733d0f13fd1becaedf014d58a |  |
| 2026-11-24T08:01:54.267398+00:00 | retry |  |  | test:item_checklist:original |  | 191c7094b9c48322fe9973659ad15bdb9233ab179c52cb506008c250011c7676 |  |
| 2026-11-24T08:01:58.574369+00:00 | retry |  |  | test:separate_scoring:original:B |  | 0051dd1ef87cc542aa515320cf155e00ba70e1884a3c71707af2a7e2ab33350b |  |
| 2026-11-24T08:02:02.360844+00:00 | retry |  |  | test:separate_scoring:original:A |  | bb7ed8ee05e030b72c6511ac1b92af07b2c528a539d60704f4dc246dcdb38fd2 |  |
| 2026-11-24T08:02:14.031404+00:00 | retry |  |  | test:free_form:original |  | becd511bff2e98580773679566b4623e709a9a187affec4406af9ce46d3800ee |  |
| 2026-11-24T08:02:14.352675+00:00 | retry |  |  | test:separate_scoring:original:A |  | 3d672a01bf23f0614c0b89b37284afb14a587c9e072f1cc4515d3eee67c7e81e |  |
| 2026-11-24T08:02:16.281926+00:00 | retry |  |  | test:separate_scoring:original:B |  | 6df5b2560f49235e10aa601ffde0b38b8dc95f86bbbdf824b9bcc6df2aa28bc3 |  |
| 2026-11-24T08:02:16.310785+00:00 | retry |  |  | test:separate_scoring:original:A |  | 2b640d9821f25bcbac4d651da61a1e41bba00e11fb062d8c0533f7c9e6ae4cbb |  |
| 2026-11-24T08:02:18.302873+00:00 | retry |  |  | test:item_checklist:original |  | 46610cdf03c2aec6a61a9771b548db2ffef191da75034a58e02e57ce61444ecd |  |
| 2026-11-24T08:02:20.257609+00:00 | retry |  |  | test:free_form:original |  | a8baae562280e7c9f1326fddcd8961f7f54aa40e71a63171925ef563942bda83 |  |
| 2026-11-24T08:02:22.298161+00:00 | retry |  |  | test:separate_scoring:original:A |  | 184fb900bc8dfcc3670ef5320beb74f9ada1b7555b6b291734a63078c8cb6127 |  |
| 2026-11-24T08:02:26.753866+00:00 | retry |  |  | test:separate_scoring:original:B |  | de645184e5f71ea6d3ee3305e20716cc4418d86a496f1d50931925bfd8f570bb |  |
| 2026-11-24T08:02:28.643235+00:00 | retry |  |  | test:separate_scoring:original:A |  | 2491ae7e80f0e8f6caeb2f091e53aeba28ee24b6de767b75f246f7516d3a175b |  |
| 2026-11-24T08:02:28.994290+00:00 | retry |  |  | test:separate_scoring:original:B |  | 371a7472f85a10ba8f441d07ab9f152555a2f63e5edde599c78123ccd3e8cf06 |  |
| 2026-11-24T08:02:32.858789+00:00 | retry |  |  | test:general_rubric:original |  | 3079a3f5d6aed61df0d7a758898472acddf522c9deafb579bdccfdaca0414aa3 |  |
| 2026-11-24T08:02:35.311147+00:00 | retry |  |  | test:separate_scoring:original:B |  | 6b4ba5f67f30854a0d98d48dfb41cb023bfcf29e3efa2c372ace9dadb0faddb0 |  |
| 2026-11-24T08:02:37.048970+00:00 | retry |  |  | test:separate_scoring:original:B |  | 39867abe2f5df8a4f88a4b88c2e284dbfd8330c15edd6aae9d3267dbcf5c3d24 |  |
| 2026-11-24T08:02:39.140756+00:00 | retry |  |  | test:free_form:original |  | 5af770e915e49a30e33c5df1df090f2d1599b9a58e42d2225e8284e094aa3cb3 |  |
| 2026-11-24T08:02:41.423470+00:00 | retry |  |  | test:separate_scoring:original:A |  | c89b370668f225ef6eeda6028cabf4a81178e6631992cc0aba8104b379c6a98b |  |
| 2026-11-24T08:02:41.976875+00:00 | retry |  |  | test:general_rubric:original |  | 170cfff22842d147ace42e7cc04370494b76968195712e8794e27cbc78cffc4a |  |
| 2026-11-24T08:02:43.257037+00:00 | retry |  |  | test:separate_scoring:original:B |  | 6fad6c5518889dbd5c6d2bf612aeaf0bdf262dbd66b0dedf5e2e4893ed5e6553 |  |
| 2026-11-24T08:02:45.256146+00:00 | retry |  |  | test:exam_prompt:polished |  | 364155f2049ab3dfe7aaaa2979aafe174e97b3180cd8cb18c69c33063943db30 |  |
| 2026-11-24T08:02:46.142666+00:00 | retry |  |  | test:free_form:original |  | 3cf95a3181e9fae6130f283a5a13b3e00b5ba5f8f260e35ab4c4aeb4e3881be2 |  |
| 2026-11-24T08:02:47.480705+00:00 | retry |  |  | test:exam_prompt:polished |  | a3cf1e700845226abfb9ee756d47ab2eec96a4c29efb6812610144b35711d33e |  |
| 2026-11-24T08:02:51.407716+00:00 | retry |  |  | test:exam_prompt:polished |  | c9d5fab25dfa51c1473f66d50675a08a3e04a0ddd7694bae02fa725272fa3569 |  |
| 2026-11-24T08:02:53.534822+00:00 | retry |  |  | test:separate_scoring:original:B |  | 607ebc4d97bf649ffd971adc1694245bade378467580a989d58ff49b831a3699 |  |
| 2026-11-24T08:02:55.431156+00:00 | retry |  |  | test:exam_prompt:polished |  | ad18bbfef11ea9e35f55fb4217ec706d6a6346bf676f71f2181de220737480ec |  |
| 2026-11-24T08:03:05.582135+00:00 | retry |  |  | test:item_checklist:polished |  | e6c4890d95be0e11f1c25d1f24c181374d1dbbff8d088ea076e94b3fa455a3b0 |  |
| 2026-11-24T08:03:07.496013+00:00 | retry |  |  | test:separate_scoring:original:B |  | 60e935ed407328cd1dfe65290d1f501fd61feb3280afc47abb06025ddd1e67bd |  |
| 2026-11-24T08:03:11.860610+00:00 | retry |  |  | test:item_checklist:polished |  | 7cf4a97adb1db435f7590ba60acc0c700853c125fa74c9551afe35617a79f551 |  |
| 2026-11-24T08:03:13.479462+00:00 | retry |  |  | test:free_form:polished |  | af4bb7aaf281ad15130ccde5873f732f00fe0b5beaad541e3fa6609fad214e26 |  |
| 2026-11-24T08:03:13.545235+00:00 | retry |  |  | test:free_form:original |  | 430dd9394d50547d1c9ee72c8765baeba273b058f9a3124734a1a6960b498a0d |  |
| 2026-11-24T08:03:18.431717+00:00 | retry |  |  | test:free_form:original |  | 49d0e402eaf07d204681d7af00137da314a04c71e774a3d1abedb94f23b5132c |  |
| 2026-11-24T08:03:27.184773+00:00 | retry |  |  | test:separate_scoring:original:B |  | 5ff15f5fc13af43377eb0cc14bbf9c1a5bb5fd1eb8d9acb0d44d232887b987c0 |  |
| 2026-11-24T08:03:28.087517+00:00 | retry |  |  | test:general_rubric:original |  | 28616e68465ebc6e9216eb529f130d9aa29ab2b67323d4b5b14d6ccc2a28f4d2 |  |
| 2026-11-24T08:03:29.626468+00:00 | retry |  |  | test:free_form:polished |  | d9f0a82e22ab24169a09a9a709f64ed8be8fa2b6301a44a74648b6cab6522b53 |  |
| 2026-11-24T08:03:35.922226+00:00 | retry |  |  | test:general_rubric:original |  | 5ab2283da05c26018dcd8f3df2e1e6cb4d83ced4a2bb12eeaae41258feba08ce |  |
| 2026-11-24T08:03:38.070043+00:00 | retry |  |  | test:separate_scoring:original:B |  | 9e25b45df619b5db2249812169156faa21a85cfa5460069e952063ac9f4b8f43 |  |
| 2026-11-24T08:03:38.181093+00:00 | retry |  |  | test:free_form:polished |  | 867696d7d6a71795b913074ad0fe1c66e97ec630d58c929d63bc97944dd06b49 |  |
| 2026-11-24T08:03:39.915426+00:00 | retry |  |  | test:exam_prompt:polished |  | 81044651e263f6950bcbb5f9a2bd909a2c4aedcd812a33c888a700d0a28b968a |  |
| 2026-11-24T08:03:43.044634+00:00 | retry |  |  | test:exam_prompt:polished |  | 2f3f2208ab0a646583f56d9230784b9b9f975f12c7e80edd684019c6ad455210 |  |
| 2026-11-24T08:04:33.424799+00:00 | retry |  |  | test:exam_prompt:polished |  | 3a368262a9363f39fff87ad77826f874c9b09c9247b5cc95898a49aa02c7c8b0 |  |
| 2026-11-24T08:04:35.728835+00:00 | retry |  |  | test:separate_scoring:original:A |  | cb5f38c765ede4ddc6e7ca5188cca533503c2be2bea0dfc7096229eb30d0a377 |  |
| 2026-11-24T08:04:37.939778+00:00 | retry |  |  | test:own_requirements:original |  | a51b2c1a3cf57488edcb2d4cee6d8ecde3fecc192059e7005a080075e069e802 |  |
| 2026-11-24T08:04:39.960242+00:00 | retry |  |  | test:free_form:polished |  | 688afecb045e574b8c05bdb4c294bfad35228703bc416b7f210243787cbf6dc8 |  |
| 2026-11-24T08:04:42.047514+00:00 | retry |  |  | test:exam_prompt:polished |  | b0ee1ce9ab362b23f580f681a5f7e3b5c9f59435a4b2528cc179055a21cf58a4 |  |
| 2026-11-24T08:04:44.926413+00:00 | retry |  |  | test:exam_prompt:polished |  | e06eb0237661810be5ffbcc001aaf0d12d9de25420bbaa70080ac29c0a81fe49 |  |
| 2026-11-24T08:04:48.990587+00:00 | retry |  |  | test:separate_scoring:original:A |  | 970121e6d1b7de8e1b9502b7e8060384fd57353d7b8ec6fb1c7046a7f4f82176 |  |
| 2026-11-24T08:04:50.775807+00:00 | retry |  |  | test:free_form:polished |  | dc03eb6c1e97d32123a7fae8b185d4b092cf3d37ab9a26ce3ad5ddd5bb8322a6 |  |
| 2026-11-24T08:04:52.141431+00:00 | retry |  |  | test:own_requirements:original |  | 2c0b8eed0a51b0163ee761b8f7f28a8257df2545746ce4ad200e179bb6e871da |  |
| 2026-11-24T08:04:52.818598+00:00 | retry |  |  | test:free_form:polished |  | c0ab21e66aaa833028c9e3734e7ec47e4527569f3c22ea25da203ad0aea3de10 |  |
| 2026-11-24T08:04:54.546494+00:00 | retry |  |  | test:exam_prompt:polished |  | 484102bfe5e58bd92571e61bbde1e3dde325f17a8b850c330856d970187404bc |  |
| 2026-11-24T08:04:56.621755+00:00 | retry |  |  | test:general_rubric:original |  | a3c6c103254ffd0c262c4bcc9a77f7ca4349acdc2a5afcefa60a8fa2ee0015b8 |  |
| 2026-11-24T08:04:59.153043+00:00 | retry |  |  | test:free_form:polished |  | 29718f621c03cecca604807b910460a5b60889511588036dbf2353c7cfcf6c3c |  |
| 2026-11-24T08:05:03.758909+00:00 | retry |  |  | test:item_checklist:original |  | 03987d6b070b027db9d061d38b2fd83fb8cdc36dfba264efc51c112bb9e681ca |  |
| 2026-11-24T08:05:05.711031+00:00 | retry |  |  | test:general_rubric:original |  | 92fa07d2e7118e8f3c4fc2361d802035cf67533cf249c55224095fae4fc8e7a7 |  |
| 2026-11-24T08:05:08.012574+00:00 | retry |  |  | test:separate_scoring:original:B |  | 69c8962c65b4cce6b04244c407c4ae4f2212c188c90bd9aa56233c7d386b5ec1 |  |
| 2026-11-24T08:05:12.380949+00:00 | retry |  |  | test:free_form:original |  | b9a974103c6df8ce1036fbec936fd704a7b00e327c4424829989ff344e4ad778 |  |
| 2026-11-24T08:05:14.237160+00:00 | retry |  |  | test:item_checklist:original |  | 790a4bddad1e77523a0fa0bcffff166cde0a47f4fc59c31eb4a7acc2dfd790fb |  |
| 2026-11-24T08:05:17.008125+00:00 | retry |  |  | test:separate_scoring:original:B |  | cdcdf4d670b83a91a3808653f7e1ce0fca40bd3c34deef5b22220481319a816e |  |
| 2026-11-24T08:05:18.889005+00:00 | retry |  |  | test:free_form:original |  | e28fed5aad872ba7d1fd9bc85391ed8f11172ac1cdb6b0494f181562722f7bc8 |  |
| 2026-11-24T08:05:21.219315+00:00 | retry |  |  | test:separate_scoring:original:A |  | 4583d4b30a5e0960635c0b0b209fa2d80d13e9e40535e0c3ebce71eb9b9e75a3 |  |
| 2026-11-24T08:05:23.296677+00:00 | retry |  |  | test:general_rubric:original |  | b5e77a307e7e2983f0b8aaab8ed6593538c6e62bd537d106253512625e8039b0 |  |
| 2026-11-24T08:05:24.450180+00:00 | retry |  |  | test:separate_scoring:original:A |  | 402a05d93b45d262d094ce536a75d5996bf2e9b8ea8c0ade64cb1b3d7bc7328b |  |
| 2026-11-24T08:05:26.519574+00:00 | retry |  |  | test:separate_scoring:original:A |  | 649a2d154858a464ca7aa630a4230b0250478549df43c65977b3ccca94cc9f71 |  |
| 2026-11-24T08:05:31.171064+00:00 | retry |  |  | test:item_checklist:original |  | 7a960518fc701c24b8ba730d8f4574d341cc9c2d4b1b3e4575123a01cee79569 |  |
| 2026-11-24T08:05:33.090454+00:00 | retry |  |  | test:general_rubric:original |  | 2dd4cddbcb9fe00e0a7ac8b18eca759b312baa2d8883ea61c00282a1232efcff |  |
| 2026-11-24T08:05:33.618646+00:00 | retry |  |  | test:separate_scoring:original:A |  | 05b4b596203ae7de94c7bc7deb17e0830e1ee6d62a83fcc7e27e986b0e2c0329 |  |
| 2026-11-24T08:05:34.733093+00:00 | retry |  |  | test:free_form:original |  | f648f01ea0d8d0e5ed0d03659f18f48f243f67ddc752cd247c5a3c0ea58acae4 |  |
| 2026-11-24T08:05:35.486988+00:00 | retry |  |  | test:free_form:polished |  | 74cb9104179087995b0d66c7a4e63aeccb33a25a8155c3fb3f88d49edc8c67a3 |  |
| 2026-11-24T08:05:37.485822+00:00 | retry |  |  | test:item_checklist:original |  | 199bbae310d1b9816b25754a99faee567a124ddc9ab7b578baca8957a54800e8 |  |
| 2026-11-24T08:05:39.195809+00:00 | retry |  |  | test:separate_scoring:original:B |  | ce8fde7b3203145f6df0e31bf1aa7a2107ab3ca74a4f488f9a61e736fcf8c64c |  |
| 2026-11-24T08:05:39.666587+00:00 | retry |  |  | test:free_form:original |  | 5669159c59eb1ce7ef03790afbf1a1b1361870bcddb8b53916e376d36b4fa9ac |  |
| 2026-11-24T08:05:41.102034+00:00 | retry |  |  | test:free_form:polished |  | d809c2dd550feb56cc1bcd0aec3d309885d0d2bbf8851396d5eccd65943f39de |  |
| 2026-11-24T08:05:45.040809+00:00 | retry |  |  | test:separate_scoring:original:B |  | 18a1d4d995a21cacf84267b23413bc1b148b210c2884c8ff363628b7ec2f968a |  |
| 2026-11-24T08:05:46.926639+00:00 | retry |  |  | test:separate_scoring:original:B |  | c009d9e19823f5aa308427db34898af95d57c751f5d2ddeadf6b647e27b9f22d |  |
| 2026-11-24T08:05:56.249545+00:00 | retry |  |  | test:item_checklist:original |  | dc61adf9eba9a234e35cf5b352b3fdf2021d5b5568a74bdc4d7f659941844029 |  |
| 2026-11-24T08:05:58.244844+00:00 | retry |  |  | test:own_requirements:original |  | f8ab72322a87f55225ca1ab6d0b7fafc5a968054a62d1af73658fa566b50de85 |  |
| 2026-11-24T08:06:07.269915+00:00 | retry |  |  | test:free_form:original |  | 78170550551a1714dc78dce53d5daf36d0cb17e297753ec15e9355ee470e4044 |  |
| 2026-11-24T08:06:09.315396+00:00 | retry |  |  | test:separate_scoring:original:B |  | babbccd33fc0a11e92229fef18df2fd1f02357a6b8d9a526a64d21422c0dbeba |  |
| 2026-11-24T08:06:15.676021+00:00 | retry |  |  | test:item_checklist:polished |  | c5c4d24a8c69e94e59b98b50c8f0156a7a6d3fc67fae4d5ee3ee8bf95573397f |  |
| 2026-11-24T08:06:17.830941+00:00 | retry |  |  | test:own_requirements:original |  | 79341facda8c185940883161fa91fa726189e75d2da27b1667ffd6762410f924 |  |
| 2026-11-24T08:06:19.729646+00:00 | retry |  |  | test:free_form:original |  | 24470c40765619a0473d1538fb47da90be405d4cf46c825463aab0b5576831a6 |  |
| 2026-11-24T08:06:21.630867+00:00 | retry |  |  | test:exam_prompt:polished |  | 18781cd809ff199349343b0b53d8a11ba034466822b79c04101b5b94db7770ed |  |
| 2026-11-24T08:06:23.601793+00:00 | retry |  |  | test:item_checklist:original |  | 3938d16eb0ca1ad05502babe7e8d3308406757bd79eaddc3dd4fb3a8a0e2c78a |  |
| 2026-11-24T08:06:25.545018+00:00 | retry |  |  | test:item_checklist:polished |  | ac9e83ac2cbca3d37e5fc80abaae7b2dd9a016373d65510dcba3d531a56e93d9 |  |
| 2026-11-24T08:06:29.611400+00:00 | retry |  |  | test:general_rubric:original |  | c2eb6461ecb120b16f7447e42f6d3d53ed8b8632db771915054533646a861051 |  |
| 2026-11-24T08:06:31.394787+00:00 | retry |  |  | test:item_checklist:original |  | 703d7c5ef858b71144a744e6623db4040eb3d12e11097b9f4de51bd05cfa0e38 |  |
| 2026-11-24T08:06:37.564968+00:00 | retry |  |  | test:exam_prompt:polished |  | cff0f423ed965ebaed1ba504284a92c7eea46736219cb33da36858c89203263c |  |
| 2026-11-24T08:06:41.436076+00:00 | retry |  |  | test:general_rubric:original |  | 2024582a0938c9b8165762ee1d6e80c9bbae824d95dce250c231fe5959cf20ae |  |
| 2026-11-24T08:06:45.227931+00:00 | retry |  |  | test:item_checklist:original |  | 59f3789000c24c23fac714c91eda67147340c31050800f3f8d38fa2397210062 |  |
| 2026-11-24T08:06:48.571963+00:00 | retry |  |  | test:general_rubric:original |  | 537354d14abbb4465ba7944c9386be96dc1d0466d0a533e87bb3ebabc873225b |  |
| 2026-11-24T08:06:52.883617+00:00 | retry |  |  | test:free_form:original |  | ebb17d0d85e0fe52e6a49cbce72289dc1ce3311b82ae120587149fc44efeb80b |  |
| 2026-11-24T08:06:54.802839+00:00 | retry |  |  | test:general_rubric:original |  | 2ef39ec210fe90c00e9c845b7526bc6a21a69341c4f3e57e1b542ddef32c64be |  |
| 2026-11-24T08:06:55.941244+00:00 | retry |  |  | test:item_checklist:original |  | e2471c17441645591a5b8fdc4a6221b2b23302cc3eaa106a4ec6050b7c8f1c8a |  |
| 2026-11-24T08:06:56.817076+00:00 | retry |  |  | test:general_rubric:original |  | 2f5b9bacd7ee3e1caf07fd1283d8fbff46d5dc7f721cdc2f31a5e1f843dc9c09 |  |
| 2026-11-24T08:06:58.618655+00:00 | retry |  |  | test:general_rubric:original |  | c0f556460e2074752b9ad83177051d5e5b2fc1622e468ce39590ed2903d94e6a |  |
| 2026-11-24T08:07:00.694637+00:00 | retry |  |  | test:item_checklist:original |  | 9c445c160326578836a3fedd95d768b978b8a792b045aab2bb72f613188eb0b1 |  |
| 2026-11-24T08:07:02.697883+00:00 | retry |  |  | test:free_form:original |  | 9655213bbdfa7009054db7d78f6009d1aa91e89d6bc993a4c2528305f7ed5be3 |  |
| 2026-11-24T08:07:11.936893+00:00 | retry |  |  | test:item_checklist:original |  | 4adf9073ba3d8ce12497c8923129a7377e116ac36b0954e1f6d6b99fc51ebd84 |  |
| 2026-11-24T08:07:14.711953+00:00 | retry |  |  | test:free_form:original |  | 257f3d696e541b2c07972ff96698a4b1152d8f9cd21841c0b02e4a0ccf830e5a |  |
| 2026-11-24T08:07:17.518900+00:00 | retry |  |  | test:item_checklist:original |  | e5157dd8129e74f4ee8f2d52c4ccf45a5ced253fd663655d2f0b0797807ad8f7 |  |
| 2026-11-24T08:07:19.459205+00:00 | retry |  |  | test:separate_scoring:original:A |  | 76ff6c073c304b58b520d3daea92f7217e12c6b9b026ac105858592d0bd75eae |  |
| 2026-11-24T08:07:23.249021+00:00 | retry |  |  | test:free_form:original |  | eef639dd882d62f7523dfc0c41ddfb8c3092e19e3b104f084e6c24551e019f40 |  |
| 2026-11-24T08:07:25.191864+00:00 | retry |  |  | test:item_checklist:original |  | da7e1e17ecb158c403298f1291a66f14e53c439f7e25fb8dd3524f87ede4c60b |  |
| 2026-11-24T08:07:27.264319+00:00 | retry |  |  | test:free_form:polished |  | e4e58ad099000ccc67ddd310b6d68d871ac2b8925de2e90f15efbc0466ce2660 |  |
| 2026-11-24T08:07:29.292677+00:00 | retry |  |  | test:separate_scoring:original:A |  | b5ca5965f33017df1881064b71904db20bab2a3995ca8204e3f00e6d1af671e5 |  |
| 2026-11-24T08:07:31.112719+00:00 | retry |  |  | test:separate_scoring:original:A |  | 21908aa81cbd5acaeb6e18eecbfdf457327cb424fce0aaf3770776b8e4cbcc2d |  |
| 2026-11-24T08:07:35.311759+00:00 | retry |  |  | test:free_form:polished |  | e5f6077a623043c09c988a60f93aae6d7aff2324d89fccce24faba32a8ed54ad |  |
| 2026-11-24T08:07:37.291841+00:00 | retry |  |  | test:separate_scoring:original:A |  | d9d392d5230f029df70fa5d810f5f61b37c265405d9a24b83238155987e96a65 |  |
| 2026-11-24T08:07:39.102166+00:00 | retry |  |  | test:separate_scoring:original:A |  | 20690fb21420bd8ca297fa541071ec9c394be0c841bef989a82e9a5b64b5ef39 |  |
| 2026-11-24T08:07:41.213945+00:00 | retry |  |  | test:free_form:original |  | b4d9b1ae530c69ee96698fbddfa1b592ea88d3d4411d36e05cd2244634283c45 |  |
| 2026-11-24T08:07:43.021352+00:00 | retry |  |  | test:separate_scoring:original:A |  | 9993c0399f30437cde29572e4d2a04ceae84dc1b502cab078071e5e727685c0e |  |
| 2026-11-24T08:07:44.637878+00:00 | retry |  |  | test:separate_scoring:original:B |  | b7095c56a5ddbbdb6588997ab5312a048a20c88be9a1cf242b8cf776b45542c8 |  |
| 2026-11-24T08:07:49.266441+00:00 | retry |  |  | test:separate_scoring:original:A |  | 59e5bfc0b35161fe940a7499478b987af8617adbe062d5c1be23e5706cdca9c7 |  |
| 2026-11-24T08:07:53.794663+00:00 | retry |  |  | test:separate_scoring:original:B |  | 8f55b538dc1edbfefd07de945f876bab5e66f30f7a9cdc8fb678ef3540cdbef9 |  |
| 2026-11-24T08:07:55.933646+00:00 | retry |  |  | test:separate_scoring:original:B |  | 9483c862c2118b2715a9e60ccff04729630735bfb64555287d9da0231a5a8843 |  |
| 2026-11-24T08:07:57.941222+00:00 | retry |  |  | test:separate_scoring:original:A |  | 3be5cdcbedc6a6c90ebb4b37938c0ddb487b230df3f7cc90b62c7effc8ce8a99 |  |
| 2026-11-24T08:07:59.937071+00:00 | retry |  |  | test:free_form:original |  | 32277de96c8ccb7bb1c61cf76790fe9bafc1d4a495b53909c65070f6639255f1 |  |
| 2026-11-24T08:08:03.730399+00:00 | retry |  |  | test:exam_prompt:polished |  | bc8ec6dcbb7e3992a3df3a939c0a4b4c99e7964472998b49f97c80df8cc5f169 |  |
| 2026-11-24T08:08:03.889517+00:00 | retry |  |  | test:separate_scoring:original:B |  | 6f4b482bb138ce8e5375f74755c27af846e78503ad7ac3c1656d62732f16c09c |  |
| 2026-11-24T08:08:05.819532+00:00 | retry |  |  | test:separate_scoring:original:B |  | d832f5b22111fccdd7d0813e2123b5da61f7d81e4e20fbe1fe9f2ce7c8b5420b |  |
| 2026-11-24T08:08:09.664981+00:00 | retry |  |  | test:separate_scoring:original:B |  | 26dc6bfbc2db497c1fd6f51cc0f16efd23461ebdd81606eb3cf15f765bd2108f |  |
| 2026-11-24T08:08:11.681733+00:00 | retry |  |  | test:exam_prompt:polished |  | 7f2050eee4e879bd9becd045e0a1327534f6401fee8c9467b7076fae36519924 |  |
| 2026-11-24T08:08:14.487441+00:00 | retry |  |  | test:separate_scoring:original:B |  | b0be27e69df63fd5b1983059a92ad58df416f2bcb4c0309783f177c197984be3 |  |
| 2026-11-24T08:08:15.593822+00:00 | retry |  |  | test:general_rubric:original |  | 39789326e78ca4673eeef1ce7c692d29c50479f3a87592d529977d132368fb38 |  |
| 2026-11-24T08:08:16.271136+00:00 | retry |  |  | test:free_form:original |  | 18a17995a8469138f2f4eab18de5fc744b0339aa741caf3410f42c67bf40523e |  |
| 2026-11-24T08:08:17.814054+00:00 | retry |  |  | test:separate_scoring:original:B |  | 154c182df277b0a282447046805fe3045b89cf606c9b983c839d3441025628a8 |  |
| 2026-11-24T08:08:19.708996+00:00 | retry |  |  | test:free_form:polished |  | 2bb0e7aa59da0d47506a33d2ded2552321f47c18c0f8c6b30e8c2d81c8c9cd2a |  |
| 2026-11-24T08:08:22.275155+00:00 | retry |  |  | test:general_rubric:original |  | 85155bd277e4bd8504cbd85aa0b1b81cd2cdb622996e5222909bc29e3910d10f |  |
| 2026-11-24T08:08:24.047778+00:00 | retry |  |  | test:general_rubric:original |  | 16b75136b7321ad31c53507fd4f4fae8c6ecbafec80fe2f58751b1c4b096b25d |  |
| 2026-11-24T08:08:24.263389+00:00 | retry |  |  | test:free_form:original |  | 8047318eac4c5f3c2811536c2671d920cf9bf7f5413daeb784310be5fb471e2c |  |
| 2026-11-24T08:08:26.178556+00:00 | retry |  |  | test:free_form:polished |  | c9c7dbba1bc209247fd3729fab67ddffee6df160e14df7b6b50e9a0a477d6ba2 |  |
| 2026-11-24T08:08:27.678127+00:00 | retry |  |  | test:exam_prompt:polished |  | dd5135aba6b9f6d35a8d880977ab6b9d2390e5bf919fd8d6ed3854b040ead2e4 |  |
| 2026-11-24T08:08:29.480159+00:00 | retry |  |  | test:general_rubric:original |  | 859ac3790d399fd333b1da1e351acbe1029a4a87e6e41d358913fac2db901b65 |  |
| 2026-11-24T08:08:35.578484+00:00 | retry |  |  | test:item_checklist:polished |  | 23bd60c7cd4a937935020abcdbdcfae5d957ac8820d57eefff8907641e9e7c8e |  |
| 2026-11-24T08:08:40.966536+00:00 | retry |  |  | test:free_form:polished |  | d6d714113a6091d949e30ad0aba071831c834ca685023cb467696722f306f576 |  |
| 2026-11-24T08:08:42.996127+00:00 | retry |  |  | test:exam_prompt:polished |  | 67fc4d994c7652e2891df89824b4c10251b6b4199dbfc2f99396909213e57cda |  |
| 2026-11-24T08:08:46.954288+00:00 | retry |  |  | test:free_form:original |  | dfc5518a31299974567ad1cc4e4c787b7f1b0d7cc471ba40715e432132d55034 |  |
| 2026-11-24T08:08:49.757085+00:00 | retry |  |  | test:free_form:polished |  | 29ee96807f286a9ca5c42051a36b09670eb8323b79a3d5d27ad6ca808111b745 |  |
| 2026-11-24T08:08:51.822346+00:00 | retry |  |  | test:item_checklist:polished |  | 7ae082e2d2b16473728431dd9cd4ea6e9ebe749ba0fd923f49c9892d5c44a7d9 |  |
| 2026-11-24T08:08:53.601825+00:00 | retry |  |  | test:exam_prompt:polished |  | 0885e285446a71947cd6ec05795ce74698e2741ccb8391b51ed3f59cad75d8b6 |  |
| 2026-11-24T08:08:57.481331+00:00 | retry |  |  | test:free_form:original |  | 490a37ef385ff75755e2f57366abb58cc16874dc8883d9faa80ed6540087ab9a |  |
| 2026-11-24T08:09:02.066100+00:00 | retry |  |  | test:exam_prompt:polished |  | bc1319da7c17d770f3c7755854c636b0019329e7ec353e0545f5f5fb66b62897 |  |
| 2026-11-24T08:09:03.000968+00:00 | retry |  |  | test:free_form:polished |  | dd671a35eacb99856840a0f94b49e45611a3bba773ea32cfd77b405088bab27c |  |
| 2026-11-24T08:09:07.925368+00:00 | retry |  |  | test:free_form:original |  | 3931546c8f0db9e7989e2a26905dcf7143d5abd6da6c75e9aabbc891e1cb1dcc |  |
| 2026-11-24T08:09:22.608962+00:00 | retry |  |  | test:free_form:polished |  | e63ab1ddf286b7415f5913b1bff343c4d0a2c4eee5b68f2eb119bb938afbb6f1 |  |
| 2026-11-24T08:09:24.509577+00:00 | retry |  |  | test:free_form:original |  | 525d0408a1848721a6364dac45143527fbdac0a74302b82ef02abf1d696654b6 |  |
| 2026-11-24T08:09:32.715973+00:00 | retry |  |  | test:exam_prompt:polished |  | fa578bcaca83e5b2befccf2144eb273c72bd377f9ec21bbcd527c2075b128db3 |  |
| 2026-11-24T08:09:40.507540+00:00 | retry |  |  | test:item_checklist:polished |  | 4662aa4c427c60dd6d09263727d14b89424b42b0abbec34dcb1e691399da5f95 |  |
| 2026-11-24T08:09:40.571263+00:00 | retry |  |  | test:general_rubric:original |  | 18b7b41f7998b245be8f55aea85cd9b92802224cfcd633aef37e09dab9ca4e5d |  |
| 2026-11-24T08:09:42.570057+00:00 | retry |  |  | test:exam_prompt:polished |  | be4a24af46cbdbc9bb4b52ac382fff63d1f8fd26b82cbaf717ef746cc3ac4b78 |  |
| 2026-11-24T08:09:47.728246+00:00 | retry |  |  | test:own_requirements:original |  | 0fff29ce6c13d9e4d9dca517f365b66cb6e3d62841e64777ebe08eb670d2d735 |  |
| 2026-11-24T08:09:50.119794+00:00 | retry |  |  | test:item_checklist:polished |  | 9c85a1ca9035d4e085b3d9d2e3233409e1f4f9a76a68a1d097f7fbcf2a0d0cc6 |  |
| 2026-11-24T08:09:52.190138+00:00 | retry |  |  | test:general_rubric:original |  | 892681c55e325a229c9de4b1bf228582a2ffbfe5e429c8141780b0e4ccc10c48 |  |
| 2026-11-24T08:09:54.460800+00:00 | retry |  |  | test:general_rubric:original |  | b9d1d91c23404081a681f64631ad0c76165d50e743f55dbc0a9b2308e1c3ead1 |  |
| 2026-11-24T08:09:58.651666+00:00 | retry |  |  | test:own_requirements:original |  | 721b8579f609abbc5cc33ad40465cd5385f07e5d610aa09343cb4f3093f07c38 |  |
| 2026-11-24T08:10:03.028381+00:00 | retry |  |  | test:general_rubric:original |  | 1408064b412a5d35f44a59b2cf6c987394e8dd642c9c68329ee8b795ba07ea90 |  |
| 2026-11-24T08:10:07.334120+00:00 | retry |  |  | test:item_checklist:polished |  | bf62042331d057cd99857a30d21f1c504def59beb3e91316e7e57233c470515d |  |
| 2026-11-24T08:10:17.797632+00:00 | retry |  |  | test:free_form:original |  | 539dda42b43f6f0a8343402063342dccd8d8e69b9dbb7254e04f76d6e92a0644 |  |
| 2026-11-24T08:10:18.462509+00:00 | retry |  |  | test:item_checklist:polished |  | e083dd24b631f4bac18663d2b1f5ef369cb6558f27db2476f53d8cd928a29018 |  |
| 2026-11-24T08:10:20.022475+00:00 | retry |  |  | test:separate_scoring:original:A |  | 805e407cc6b897bbb46c320a9f59e7cbbd25a99c2adeac0ba40533003471176b |  |
| 2026-11-24T08:10:26.535665+00:00 | retry |  |  | test:item_checklist:original |  | 511d32b1a8d3f10c28c3f1103bb0f01c8390b4e77b52459a27862d01e988b876 |  |
| 2026-11-24T08:10:28.482521+00:00 | retry |  |  | test:separate_scoring:original:A |  | 1f65db0430580e4711ba54585be9ca0e6240395c124e93e12f78f14529fcdc29 |  |
| 2026-11-24T08:10:30.762600+00:00 | retry |  |  | test:free_form:original |  | d7dfd5feb8630b7a624f599af0c1abfe7a3a26ee13d1abc9d7ee818bd3cf3a0e |  |
| 2026-11-24T08:10:32.784024+00:00 | retry |  |  | test:separate_scoring:original:A |  | 223d6de3f6b13942c25a74aa700e60bec1d458efc084717a9bb7530c84883968 |  |
| 2026-11-24T08:10:34.693918+00:00 | retry |  |  | test:free_form:original |  | f7b83ef160232fafb89746a49370141c1fec6178150c5897f48f25807be92f2f |  |
| 2026-11-24T08:10:36.663380+00:00 | retry |  |  | test:item_checklist:original |  | d9a651da061b0c67a75826a7f73197fc510ec02b0d4ee7f9c0cd6408f0def967 |  |
| 2026-11-24T08:10:41.178113+00:00 | retry |  |  | test:separate_scoring:original:B |  | 90002c9fbeb95e0077e9b8b0e40a3356725c06438d4fbf2e33451ee9152e9884 |  |
| 2026-11-24T08:10:43.229851+00:00 | retry |  |  | test:free_form:original |  | 0ac88eeec5c16037c321abb56c8cd078a7767c4e4f9ad83a851dd4b1f392ffb1 |  |
| 2026-11-24T08:10:49.323831+00:00 | retry |  |  | test:free_form:original |  | 2d73c4572a176d23e75b983f85a6773e390c79df3971df64cf2df8a22e0e28d9 |  |
| 2026-11-24T08:10:51.689768+00:00 | retry |  |  | test:general_rubric:original |  | f5515371c18a091763d3dab0c63b953a402685d0d302f4255afe95ace6aa153a |  |
| 2026-11-24T08:10:53.569102+00:00 | retry |  |  | test:separate_scoring:original:A |  | 64370a94b6e22cee41e52881f0bd5343f53a4730503ff7f8acc360583257741a |  |
| 2026-11-24T08:10:57.195396+00:00 | retry |  |  | test:separate_scoring:original:B |  | c958a9d680acd59ca93d9961999d0d52001b7885c80c2476bdc5bbd4b5de6bce |  |
| 2026-11-24T08:10:58.648809+00:00 | retry |  |  | test:free_form:original |  | 26eb3e2581574fcdda03ae301fe56e30b3eb5f425bc2c9793fd2eef4298644ab |  |
| 2026-11-24T08:10:59.034413+00:00 | retry |  |  | test:general_rubric:original |  | 46bf4f6fc0a83aeea54849e3367b22680e061bb5687c8078005dc946697d989b |  |
| 2026-11-24T08:11:00.864865+00:00 | retry |  |  | test:separate_scoring:original:A |  | e0f7e7415dfbb1f9a208ac892c146138798fd9ab1018421e5e08268a06c30a96 |  |
| 2026-11-24T08:11:01.077401+00:00 | retry |  |  | test:separate_scoring:original:A |  | 56e5c3471bc6f0a9aba79b6e998e9b9aec43937ede8a7aa03413c4808a8f6fd2 |  |
| 2026-11-24T08:11:04.296405+00:00 | sol_rate_limit_audit |  |  |  |  |  | Raw CLI error events show sustained generic429s and intermittent successes. Terse inherited retry logs omit list-event detail; all raw events were cached. Maximum3 attempts and scoring unchanged. No explicit usage/quota message. Luna audit had0 nonzero exits; no model substitution or post-hoc replacement of exhausted errors. |
| 2026-11-24T08:11:05.938525+00:00 | retry |  |  | test:separate_scoring:original:A |  | d312858e14500da3dd3ba174f86c5bdae16f9edc33263648b38c592d6857115c |  |
| 2026-11-24T08:11:12.779697+00:00 | retry |  |  | test:separate_scoring:original:B |  | e2ca069375ffd05fb6447be5e9da1f1bb94811ee404a127d50bcafbcd4d187e1 |  |
| 2026-11-24T08:11:16.124798+00:00 | retry |  |  | test:separate_scoring:original:B |  | 57d8b9b4a3e949ae7bef6c3b459c5697bbdc1268f60bad01696d106bd334182e |  |
| 2026-11-24T08:11:17.536952+00:00 | retry |  |  | test:separate_scoring:original:B |  | 631207560e1839d5c0ed824502977f6912e1f04f8f83f825a49a4cc1fad214e9 |  |
| 2026-11-24T08:11:21.162783+00:00 | retry |  |  | test:separate_scoring:original:B |  | 8b6d9ba0e4970d42819f847c56f5f7a83143c0b245e0f0f6d4ad2cdc6ba6167c |  |
| 2026-11-24T08:11:26.785227+00:00 | retry |  |  | test:general_rubric:original |  | 9b1a7afd5087cbba7e123a5ea832d8cb0941de8ee7954991932d349874651c85 |  |
| 2026-11-24T08:11:29.406690+00:00 | retry |  |  | test:separate_scoring:original:B |  | 281ae26edc4014c7fa3ab79ac7b2c9f7767c34d92e842c68ce7ac1cbc8e70f4f |  |
| 2026-11-24T08:11:37.671748+00:00 | retry |  |  | test:own_requirements:original |  | c36b53b0b9f0ecb92143a37ff5b7e2437eaf9f92cac7395c970a631899b6755a |  |
| 2026-11-24T08:11:44.080594+00:00 | retry |  |  | test:general_rubric:original |  | 0fa75bdf49936f74e7c2df4663279873b42ae1e41fa3325dc84e2613ffe19e04 |  |
| 2026-11-24T08:11:46.920239+00:00 | retry |  |  | test:item_checklist:original |  | 5c6a3f66428068bf0e05d49dffdfe9418e5a20ade22ecaa73661dccf87f362a5 |  |
| 2026-11-24T08:11:49.213662+00:00 | retry |  |  | test:general_rubric:original |  | 530376cd93f717e60a263c6cc337ae181821d971b491f4e4cf96bfec0cbe38c7 |  |
| 2026-11-24T08:11:52.059154+00:00 | retry |  |  | test:item_checklist:original |  | cd27a7a7307be1a91af964b0a36d91290800c403651b2152d06d87b158b1f4a8 |  |
| 2026-11-24T08:12:06.193176+00:00 | retry |  |  | test:separate_scoring:original:A |  | 01e324dbd4a77ca2cf62d30abc5e763a97269b5a4637f6acd70c0831c7630b5b |  |
| 2026-11-24T08:12:39.423028+00:00 | retry |  |  | test:item_checklist:original |  | 38cffa719833fafb55db2865188a06ed496e353472f1a82766801f055b521156 |  |
| 2026-11-24T08:12:42.837038+00:00 | retry |  |  | test:separate_scoring:original:B |  | 3ad5807cceb1fca38a075fbcc2578cc368d373c4620b399d1e01e1270d7fe962 |  |
| 2026-11-24T08:12:44.862206+00:00 | retry |  |  | test:item_checklist:original |  | 557c5a7ef9d34adaefbdcc0fd63abff4a0780430374051a64b71262d54e0187e |  |
| 2026-11-24T08:12:51.705393+00:00 | retry |  |  | test:item_checklist:original |  | 3a5af760ffe41eee0c804b46cacc9785df187108ea6a6de282a3cfc47c3c4cf2 |  |
| 2026-11-24T08:12:51.794707+00:00 | retry |  |  | test:own_requirements:original |  | ce0ba517e12101c39c56d66286e3d5e1b1534f00265c8b418bf6e5b857cc56b0 |  |
| 2026-11-24T08:12:54.981222+00:00 | retry |  |  | test:general_rubric:original |  | 6c56021b2dc40c604e971296fb91514f39811e241dbffa996c22c3e0a1cf29a2 |  |
| 2026-11-24T08:12:56.800726+00:00 | retry |  |  | test:item_checklist:original |  | c28e534eb85c9a1055152dd9798bcd4df4997aaf34f03966e65f018ef01fe469 |  |
| 2026-11-24T08:12:59.762933+00:00 | retry |  |  | test:item_checklist:original |  | 9bc5ebae4a39ff6b79831689cd0e2e191aacfaff9bfd39e35cf4fb39230261e7 |  |
| 2026-11-24T08:12:59.883895+00:00 | retry |  |  | test:general_rubric:original |  | 0a435c50d4b639306e548d529a899c565cd1b482097f60a4456d79ffeb2868e6 |  |
| 2026-11-24T08:13:04.851690+00:00 | retry |  |  | test:item_checklist:original |  | 60d75c4f975b34e299cc15b38effc09d73e4ee046d404ab97903ae7d11375a08 |  |
| 2026-11-24T08:13:06.771930+00:00 | retry |  |  | test:free_form:polished |  | c0afb9c523a7c4ed50f9618479d018654b9517f83ef988c989e15959c9dbfd61 |  |
| 2026-11-24T08:13:07.043644+00:00 | retry |  |  | test:free_form:polished |  | c7c7841c25e493590b345d990acd2f554fe2644cb8375c128435ebc02ff541e8 |  |
| 2026-11-24T08:13:12.198825+00:00 | retry |  |  | test:free_form:polished |  | 1c2bf15683a960679631f27a2f1c2f0fb10c489c819cccf88cb2b5a0c0dd1c26 |  |
| 2026-11-24T08:13:14.578755+00:00 | retry |  |  | test:free_form:polished |  | e45505fec735e0c58aa3d2c44982b87f134f8fe265fc93c6c31b3882a690068e |  |
| 2026-11-24T08:13:17.055137+00:00 | retry |  |  | test:own_requirements:original |  | 594299f773ff72621a975770ae7697a6f79d4ff319513470b43826463a5c4d83 |  |
| 2026-11-24T08:13:23.502798+00:00 | retry |  |  | test:own_requirements:original |  | 1ce670b5e8b213df5a0ef76cf9010dce9e154cbfbcc0d5b1a7efa3d99177dea5 |  |
| 2026-11-24T08:13:33.014137+00:00 | retry |  |  | test:item_checklist:polished |  | bcfbf14157c5ce7e904b00d999465a864783d6ef2734d9762aa02b6ed8d72688 |  |
| 2026-11-24T08:13:33.435754+00:00 | retry |  |  | test:free_form:polished |  | 468f1270479d2618d8b915db136c2945505533179eb4f2ac78c175e4f71d738f |  |
| 2026-11-24T08:13:37.338150+00:00 | retry |  |  | test:separate_scoring:original:A |  | d251c48f49ceb9b9228ba2ee9bf5417c705b35aa99b1b1f468f7dea3df16f769 |  |
| 2026-11-24T08:13:39.673507+00:00 | retry |  |  | test:item_checklist:polished |  | bfcd8d5c56aeb6ca6dc16c9825c2af6f824b5d7f60be798feb10286d87dc82ad |  |
| 2026-11-24T08:13:39.846768+00:00 | retry |  |  | test:item_checklist:original |  | 95efecab8c9b02ba7b9d664ea01853f28c73a520adc027a87827d55472c57bd1 |  |
| 2026-11-24T08:13:41.578412+00:00 | retry |  |  | test:free_form:polished |  | 20bbb980bdc004d6c4fd1ef68ae29aec785ba6bb8d9ea5b6ee84b039008ca833 |  |
| 2026-11-24T08:13:43.601706+00:00 | retry |  |  | test:separate_scoring:original:A |  | 1bd7fd1e3d91dc6bd668fd9f82a5288a333a76372aa086a318c1b32abd021fc3 |  |
| 2026-11-24T08:13:45.676029+00:00 | retry |  |  | test:item_checklist:original |  | d41cdb24c1b296888f808abf0dad6e4d9df699ff3bc1e31e39c2122975bf748b |  |
| 2026-11-24T08:13:46.058339+00:00 | retry |  |  | test:item_checklist:original |  | 3caa546f6d5bce45a57abad163af3ce2bac73c77297458b972764fe738bb3452 |  |
| 2026-11-24T08:14:48.232487+00:00 | retry |  |  | test:item_checklist:polished |  | c2524d877a8f87441e2ec96bc59429717b8ce6b1476e57902940d19416905237 |  |
| 2026-11-24T08:14:52.617547+00:00 | retry |  |  | test:free_form:original |  | f2ee2f94c870b7c7e054c3a26bbda875950a7ebb56a5cc1e5a405becd0dc73d2 |  |
| 2026-11-24T08:15:00.496779+00:00 | retry |  |  | test:free_form:original |  | 4843651f84152cd5b692854e87a29c88e5fb7ae18dde800c8b2c6bdd5b7bd709 |  |
| 2026-11-24T08:15:02.314329+00:00 | retry |  |  | test:free_form:original |  | 299ebf86c70b3fea2ca3fadcb4150c3a8719f6e3e2feeac8a9727a230421b293 |  |
| 2026-11-24T08:15:03.529960+00:00 | retry |  |  | test:item_checklist:polished |  | 7b6510dadadea9ba342e0dada9e00f74c454ea014d382e6ee38f0b4c526b8ec9 |  |
| 2026-11-24T08:15:05.847959+00:00 | retry |  |  | test:item_checklist:polished |  | 1a658f4d5687c7f8780fcb9187d4290502b859c1ea2deb24f524e005c25b7ab3 |  |
| 2026-11-24T08:15:08.079506+00:00 | retry |  |  | test:free_form:original |  | 7bffa00628a78532991a012307a2da31e0aa5bb9e1941ada329aa3c7c345832d |  |
| 2026-11-24T08:15:12.115311+00:00 | retry |  |  | test:item_checklist:polished |  | 4289b49d0b37017f65755387c6728727d4641383e574bbf5a8b7722f44bf170e |  |
| 2026-11-24T08:15:15.980909+00:00 | retry |  |  | test:free_form:polished |  | 21d85bf30ee0159a02a8f26469cfca965a4bdb3059bf7542cc60fcd8a85edc19 |  |
| 2026-11-24T08:15:23.709535+00:00 | retry |  |  | test:free_form:original |  | 0e7f6248bf1930d8e54cdd176242dbb32596aa3b5fece553afab585888add213 |  |
| 2026-11-24T08:15:26.867095+00:00 | retry |  |  | test:free_form:polished |  | 869fdae2e2c8f83b0a86e7e1b375af2906b867d15678ab74e0283f8959a20cc1 |  |
| 2026-11-24T08:15:29.051714+00:00 | retry |  |  | test:separate_scoring:original:A |  | 5a28093d20cb4291e88a00de29a10fcd2fceea8e9aab74ec6ea1edb0253e1879 |  |
| 2026-11-24T08:15:29.590713+00:00 | retry |  |  | test:exam_prompt:polished |  | 3cabcf98136f5478d061cf1ed4d2484e3f0e4071fdcff7fa6f915ca7f8fbf9cb |  |
| 2026-11-24T08:15:39.735121+00:00 | retry |  |  | test:general_rubric:original |  | 0e97a3910a8cc69ee2f56ac19053c783e826dbdffd9e1c1baa9ad79481b517af |  |
| 2026-11-24T08:15:41.718201+00:00 | retry |  |  | test:free_form:original |  | ae11086ce9ae9baf6fd554b7dbf85852ddc4ffddb52a70668daa5c3f7289cf77 |  |
| 2026-11-24T08:15:44.034044+00:00 | retry |  |  | test:free_form:polished |  | 270cfe9e55171e9e164e1aa2852f102875dd161833a9d0c3e18233f127931639 |  |
| 2026-11-24T08:15:46.031424+00:00 | retry |  |  | test:exam_prompt:polished |  | 333b522c09dae7010e0b6181a668a24864a7a01e52d5f38a91cea8e9c436d304 |  |
| 2026-11-24T08:15:48.063169+00:00 | retry |  |  | test:general_rubric:original |  | f1e540694bf2d437c3b127d1e7b88c3e44f500ce82c6a2fe1a76ac19461dcc38 |  |
| 2026-11-24T08:15:50.316286+00:00 | retry |  |  | test:separate_scoring:original:A |  | c7b4934147ec999d0c396fe51aa7bd99ecc6e986dc7f04150ebe6f39d467bd54 |  |
| 2026-11-24T08:15:54.313205+00:00 | retry |  |  | test:free_form:original |  | 283fc201f0de949b2f95489c9d7db29d5e9464154f1072975e939c9461fab4d4 |  |
| 2026-11-24T08:15:59.740502+00:00 | retry |  |  | test:free_form:original |  | c4517b7257ba079ebd8828f873dab35947dbb94045a75b73f775798376dfc64b |  |
| 2026-11-24T08:16:08.535711+00:00 | retry |  |  | test:free_form:original |  | 64d8a17f557bdd694e4d8a37fd2ae7b8279b8e3e8d36a2ebadf96b12f9e0f1fe |  |
| 2026-11-24T08:16:09.751279+00:00 | retry |  |  | test:separate_scoring:original:A |  | e8352005bf9917cc32fd08bc1778d381917754701b687bebda48982b335a9718 |  |
| 2026-11-24T08:16:10.504662+00:00 | retry |  |  | test:general_rubric:original |  | 023866f368849514dde254ae8e68c3697b86f4ad08ebe04094063fc4cbaea65a |  |
| 2026-11-24T08:16:11.738915+00:00 | retry |  |  | test:separate_scoring:original:B |  | ffde354c0b5092a31e088cf95c335f7c1f18137f4560ebd5b6d231b7de553c0a |  |
| 2026-11-24T08:16:12.465074+00:00 | retry |  |  | test:free_form:original |  | ff5d99a60471ad5787b35e6f27c4d8466b7682d7d6fcdcebd336f54a5ca61716 |  |
| 2026-11-24T08:16:14.646798+00:00 | retry |  |  | test:separate_scoring:original:A |  | 715759f60dd05e77b8707202c0d35d4309e1a87f5d0f5d1cc3df52f2fc92f01b |  |
| 2026-11-24T08:16:14.662891+00:00 | retry |  |  | test:separate_scoring:original:A |  | 57d9d919efc12b082efb4dc95bb373aba6d23c63877eb6a2bfa3fa9bdbff894f |  |
| 2026-11-24T08:16:16.966703+00:00 | retry |  |  | test:general_rubric:original |  | 79d5b872b17beecef7ce32897a7f0016c0d0cdaf7fac037c943d54e35de582aa |  |
| 2026-11-24T08:16:18.706140+00:00 | retry |  |  | test:free_form:original |  | 0868200ec3cb8cdd6af9ab8345fee199cf4380cb3c76698121769cc7b8963ff8 |  |
| 2026-11-24T08:16:18.742262+00:00 | retry |  |  | test:separate_scoring:original:B |  | 67908490944a7ed9b1bcff3522459771205e92995db7c3ab07ffa74b3d68b2b9 |  |
| 2026-11-24T08:16:20.729120+00:00 | retry |  |  | test:separate_scoring:original:A |  | 78df885ca7dea59b90a130393f9c0419d3695e20a542edaf6374466c9844d5e2 |  |
| 2026-11-24T08:16:24.539897+00:00 | retry |  |  | test:separate_scoring:original:B |  | f2d9b31bec24a201334f1392e5a6173a1fbdb917294bd3de31b00ff2e66479e8 |  |
| 2026-11-24T08:16:32.557313+00:00 | retry |  |  | test:separate_scoring:original:B |  | 33b0ac91143087afb87bbdf8e616849a4f130dffca66b7cde7303bb54a9f6e5a |  |
| 2026-11-24T08:16:34.126532+00:00 | retry |  |  | test:separate_scoring:original:B |  | ed27ae986bddf9e2d2c21650993f5011aae8f92604d8b9297f666ab3bdafd6c6 |  |
| 2026-11-24T08:16:34.492304+00:00 | retry |  |  | test:item_checklist:original |  | d36121c3c4b9483014eb3f89fa1a492dc232ab1d53b620579a21d781fa9bc815 |  |
| 2026-11-24T08:16:40.090388+00:00 | retry |  |  | test:separate_scoring:original:B |  | 2b9d50159155e7a8658ab0efe9a62c8013a8a6ff8e1600610244de4c592bdaf3 |  |
| 2026-11-24T08:16:40.767231+00:00 | retry |  |  | test:separate_scoring:original:A |  | 22044adbb623ba7e7329d65448ec85c1e7af52fd6acd10b755eb9a664d0d8578 |  |
| 2026-11-24T08:16:43.003523+00:00 | retry |  |  | test:item_checklist:original |  | 885e542bfc047209689fba4200839fbcd8aa0f366ea0c649c54f1f63f2657f6f |  |
| 2026-11-24T08:16:44.916122+00:00 | retry |  |  | test:separate_scoring:original:B |  | 5cc15366402524fc8eaab9a6b794817b4fa779ea099434ca9099364f9461083f |  |
| 2026-11-24T08:16:48.641916+00:00 | retry |  |  | test:separate_scoring:original:A |  | fbaf421b4fc0ca44bb4ec375c7e6d969441ed4c7cd5ac213001e2c235a10fd06 |  |
| 2026-11-24T08:16:59.099226+00:00 | retry |  |  | test:separate_scoring:original:B |  | a847ea8508d42bd93d83e72b7ff91e68e62f61191a6364b6b2fdd7c0af64e30e |  |
| 2026-11-24T08:17:06.284624+00:00 | retry |  |  | test:general_rubric:original |  | 9a6e8b51b971f81d8af250100912984b1a4741faf50d162f081bd74e3f1077b6 |  |
| 2026-11-24T08:17:08.231157+00:00 | retry |  |  | test:separate_scoring:original:B |  | 3c45a622c5ccc6c285a936d51af3e2085e2f5458454c95e7662e03737009c2c0 |  |
| 2026-11-24T08:17:11.253991+00:00 | retry |  |  | test:separate_scoring:original:A |  | aa6f494d0836ac237b57eb25e9b6b37133d03ce2a3aa5e2fab11ae430badd5c3 |  |
| 2026-11-24T08:17:20.609275+00:00 | retry |  |  | test:general_rubric:original |  | 288e85e5ee47254dd339392d39eaba1789eb19c79b99867d5bf2ab62a9d9cfcc |  |
| 2026-11-24T08:17:22.529658+00:00 | retry |  |  | test:separate_scoring:original:A |  | dea8f913f7d58c2bc2703bb07f9d7cbf843640685c832e495e9d05672a1af214 |  |
| 2026-11-24T08:17:28.488224+00:00 | retry |  |  | test:item_checklist:polished |  | 2110b5713d98a66751757f38f8e167f478f58b4808b2fd2dff561c438e1fbfed |  |
| 2026-11-24T08:17:30.786843+00:00 | retry |  |  | test:free_form:polished |  | c64fc6c48d1b8b4a01f96968e102309e467e1337ba76287bb95bb9636baed9a4 |  |
| 2026-11-24T08:17:35.037366+00:00 | retry |  |  | test:separate_scoring:original:A |  | af235567a79bcb86a5229c80af9b4a4be032a8ce162f80bdb7b5cbcb0b12f840 |  |
| 2026-11-24T08:17:36.832918+00:00 | retry |  |  | test:general_rubric:original |  | f2790063d21510edbc8eda5d071fdc7dd2949d7444bb4d6b0d1fe523aac63a96 |  |
| 2026-11-24T08:17:37.799652+00:00 | retry |  |  | test:item_checklist:polished |  | 7214364f1c1158b56ec6a94efffb6a65e688b2bc7056b9bab865a4a123dd21d5 |  |
| 2026-11-24T08:17:38.664153+00:00 | retry |  |  | test:separate_scoring:original:B |  | 4389735a4dd7d773aa996aaf83341456209387b4e948723beadc00e2ded1c80b |  |
| 2026-11-24T08:17:39.654898+00:00 | retry |  |  | test:free_form:polished |  | a12432f945dead80ed73f954ce0687c675c36bf3a7cec3acf5bf61b80a83d951 |  |
| 2026-11-24T08:17:40.689993+00:00 | retry |  |  | test:separate_scoring:original:A |  | f4ebf5b25da905284c4c4a67a65128171b6d7091bef814091f66e389c721af99 |  |
| 2026-11-24T08:17:42.100125+00:00 | retry |  |  | test:general_rubric:original |  | 18b25e3e3f2fb3f1da7e7339a87e64662fbbe20b3f7be918662f6dbd912ded95 |  |
| 2026-11-24T08:17:43.560911+00:00 | retry |  |  | test:separate_scoring:original:B |  | 6d1ce574e908c5f29dd407518d46865bbd162ba56b8b4d665c5a727ee956fe7d |  |
| 2026-11-24T08:17:47.762254+00:00 | retry |  |  | test:separate_scoring:original:B |  | d6631688a9a0bb8f74f428eace71f45bff32d13af0d125e709d86e41f197aaa6 |  |
| 2026-11-24T08:17:50.983568+00:00 | retry |  |  | test:separate_scoring:original:B |  | e8822366f34a208296b73d140d829a1122614084850f308bbeb326666d20a6cc |  |
| 2026-11-24T08:17:57.999265+00:00 | retry |  |  | test:exam_prompt:polished |  | acc4d181b9366ed47d8a3473268f0547b69ea62cbae4a3151479d2b6927e8e04 |  |
| 2026-11-24T08:17:59.987994+00:00 | retry |  |  | test:separate_scoring:original:B |  | 2ba9c12dcddb15c7b8a348f43358d03885e085afa182e9b868a66b6be98c9dea |  |
| 2026-11-24T08:18:03.994021+00:00 | retry |  |  | test:separate_scoring:original:A |  | b9864f883b9e39f51a32dfb3e80a31c537b1d924560c5a176a5f789deb048b81 |  |
| 2026-11-24T08:18:05.962246+00:00 | retry |  |  | test:exam_prompt:polished |  | 560cd343a705cc18e3b7cbe7df6a0d1796f6dd040afb1f7ad3fe05a676be70eb |  |
| 2026-11-24T08:18:07.037751+00:00 | retry |  |  | test:item_checklist:original |  | a216a7e175c096cbe7df7f556052e9a1453b2166449a610599c7719ccb8d3cd1 |  |
| 2026-11-24T08:18:07.984003+00:00 | retry |  |  | test:item_checklist:original |  | 9102332c3a9c022f98f069d623edfe4b2ea137a69abfab1cd185bfa3cb0cc271 |  |
| 2026-11-24T08:18:09.908129+00:00 | retry |  |  | test:separate_scoring:original:A |  | 16f415a9a6edd54cfee27bfe496a3fcb184914341249a43b036405c1df2f8433 |  |
| 2026-11-24T08:18:10.734782+00:00 | retry |  |  | test:free_form:polished |  | fdc8d36af73b363ab61dbf796eb0848378485e5bd62d2c3d336c6f28b073054a |  |
| 2026-11-24T08:18:11.916297+00:00 | retry |  |  | test:item_checklist:original |  | 9851acb9eac0dc77fd9582ce15b5f1e668cca79dc2a20c20df66d6cec4aace5a |  |
| 2026-11-24T08:18:12.894640+00:00 | retry |  |  | test:item_checklist:original |  | 8cbf48e627adeb646b9826e97bd05167609e492184830172fdbb4b59379b8903 |  |
| 2026-11-24T08:18:17.109977+00:00 | retry |  |  | test:free_form:polished |  | 351e9cd736f50f79be2afb07eaf2dc791d8f922fda88345d86ec44aef8ae0115 |  |
| 2026-11-24T08:18:21.351092+00:00 | retry |  |  | test:separate_scoring:original:B |  | fea19839f75bb1f874d8022a25008766608de59c5d187b1869c4b1ff9fb4d1af |  |
| 2026-11-24T08:18:26.770088+00:00 | retry |  |  | test:separate_scoring:original:B |  | 1c6a98451227a2c89c61412f7c1bfe6476dd41b072577487faca87a3fae3f990 |  |
| 2026-11-24T08:18:48.546533+00:00 | retry |  |  | test:item_checklist:original |  | 6846dcce49cc7766b3c79cb5d0a3f8924392bb08ac7d12fbc528ab50e2b6389c |  |
| 2026-11-24T08:18:50.947563+00:00 | retry |  |  | test:free_form:polished |  | 452ab1b1f242c8489fe73360630f6791a4f99b8c9fa5b7905ad0d8ca2aa875e7 |  |
| 2026-11-24T08:18:55.308152+00:00 | retry |  |  | test:item_checklist:original |  | 60e385c70f55b897e225d6a8d2f416dc8786ade4e83fff41d36ac698fa555446 |  |
| 2026-11-24T08:18:58.040257+00:00 | retry |  |  | test:general_rubric:original |  | 9475ef57d387f1393e889b632ea89fb6dd07e95eb988e95fcdb60973f5d1d6d7 |  |
| 2026-11-24T08:19:00.367493+00:00 | retry |  |  | test:item_checklist:original |  | a5ff00f48d58f6f44363b1bbe8d359494b30c9f589a17ce8b73a57577b0a7d70 |  |
| 2026-11-24T08:19:02.934248+00:00 | retry |  |  | test:general_rubric:original |  | e19b6eab5796fd3f6a3d993bdec61f01022f50c237aee837655791e14f3b8441 |  |
| 2026-11-24T08:19:09.422949+00:00 | retry |  |  | test:separate_scoring:original:A |  | 0c4a03a3724fd5d595e6905bdfa802111fb88e025a80796cb15f0694dc196670 |  |
| 2026-11-24T08:19:12.786677+00:00 | retry |  |  | test:exam_prompt:polished |  | 38e6a4ca4627dcddfe02ccc05043a1b48b062d11b0d6d30b829e40dff32b394d |  |
| 2026-11-24T08:19:14.754884+00:00 | retry |  |  | test:separate_scoring:original:A |  | e8d94d36c1126dc99fd66a3e74e926c0c07d9aaf7313f4a92f631af22a88b92e |  |
| 2026-11-24T08:19:17.673487+00:00 | retry |  |  | test:exam_prompt:polished |  | 6fae26ea42bb3c46d885623b3ed460f5b5a3f6bf10dedefd19438ab8a90a27be |  |
| 2026-11-24T08:19:21.852996+00:00 | retry |  |  | test:separate_scoring:original:A |  | 00e6a74ec18f98250db52c148023ad148c8b432424db0b60b54103ff5ab1c1c0 |  |
| 2026-11-24T08:19:24.586706+00:00 | retry |  |  | test:separate_scoring:original:B |  | a8743f53d7daef169812c831c6ba0d52d7d8976f2c2eeed1f87956476e645c9e |  |
| 2026-11-24T08:19:24.805182+00:00 | retry |  |  | test:item_checklist:original |  | 92f9ad6e82cb1c366e828f3c86faf10087322cab3108bfcbc2e9f841cc231736 |  |
| 2026-11-24T08:19:26.553020+00:00 | retry |  |  | test:separate_scoring:original:A |  | c9e34641b2647a46e0b439d90944f043132eab9b5d1fb445316b5236a621f4af |  |
| 2026-11-24T08:19:28.441791+00:00 | retry |  |  | test:item_checklist:polished |  | af4520d6edda93ffb8cf3f43d6b957a68f3bbc5a19f66294e1f4264d3f1f2510 |  |
| 2026-11-24T08:19:29.393140+00:00 | retry |  |  | test:separate_scoring:original:B |  | cb454cde28095e405d4c583297819fb00913c2791d6c73afa0ece114f238c3ad |  |
| 2026-11-24T08:19:30.529949+00:00 | retry |  |  | test:item_checklist:original |  | 0eea83ef6bda32d894d0c868fb475dab7582369f661196cccf60c2e57c2a12fa |  |
| 2026-11-24T08:19:31.684893+00:00 | retry |  |  | test:general_rubric:original |  | 79419d71def18174573db27147435e2b0880d3f7992d2bafbb36ae224b8cf8ba |  |
| 2026-11-24T08:19:33.195107+00:00 | retry |  |  | test:item_checklist:polished |  | febd42d814e6c851f7802e8d05b10c2821da7ac69ceadad387b2a206bb1d77f9 |  |
| 2026-11-24T08:19:36.390414+00:00 | retry |  |  | test:separate_scoring:original:B |  | ef4ea7bc3c1345b6db791612b073b6ce0bdda1ef0a4e24439387d7d2c6361da9 |  |
| 2026-11-24T08:19:36.464160+00:00 | retry |  |  | test:general_rubric:original |  | a49f04319fd2de62f87aaa037195a53d10ec13d46e4a39073c08013c3f3b787d |  |
| 2026-11-24T08:19:40.978694+00:00 | retry |  |  | test:free_form:original |  | 573e70f6065de0abd2ce57a5194564c1aa7657e22783368df339afbe923f63fa |  |
| 2026-11-24T08:19:42.251269+00:00 | retry |  |  | test:item_checklist:original |  | dfb6a31423ab4d23c67b7df5d8b81490638cc62d76a6d032a05bc8547471bb26 |  |
| 2026-11-24T08:19:43.158923+00:00 | retry |  |  | test:separate_scoring:original:B |  | 7044732f13f19da68a2518167dfbfbced26b8e2afa04f7aa47cab17352991dc0 |  |
| 2026-11-24T08:19:43.542014+00:00 | retry |  |  | test:free_form:original |  | f9bdca1497b4ec11d1619ce8c80505fb549119a2f11cd7bb8663cf32c003093d |  |
| 2026-11-24T08:19:44.975980+00:00 | retry |  |  | test:general_rubric:original |  | f4aed187480c67ec68fe3935290ff59ce07c2681aaa75c8827e51bd5c84187b7 |  |
| 2026-11-24T08:19:46.842732+00:00 | retry |  |  | test:free_form:original |  | d1c39b1f2fbf9afbc1504a00b06cac5db4853eb1c8f9046bf5364ca45a365e53 |  |
| 2026-11-24T08:19:47.515670+00:00 | retry |  |  | test:general_rubric:original |  | b05e1289052396eebd59846089affb74675876d2edf1338d6758592efa9ced90 |  |
| 2026-11-24T08:19:48.850365+00:00 | retry |  |  | test:free_form:original |  | 10895f28db13bbd0707cacc8e1dac0263cee7e49d794e0460531ef74cabf8813 |  |
| 2026-11-24T08:19:49.719104+00:00 | retry |  |  | test:general_rubric:original |  | 806fa13c2df1525ce39e32a2b9b94e87e095fefcb449e2daa8050ff20a02e982 |  |
| 2026-11-24T08:19:52.830014+00:00 | retry |  |  | test:general_rubric:original |  | 8e78582b21d553226ce4bcfd13988a22c81dba25466e0bdc183e4b11a4e6b33a |  |
| 2026-11-24T08:19:54.114329+00:00 | retry |  |  | test:item_checklist:original |  | 8b0bea0a3cb1b3710ef0e75a7cb9df92d51730a66a21390c9f70ffd6e054b055 |  |
| 2026-11-24T08:20:01.349829+00:00 | retry |  |  | test:item_checklist:original |  | aee780653c70a569924d5c3bf445ac5f569e43e7adf8357df58f076c00872ba5 |  |
| 2026-11-24T08:20:05.659400+00:00 | retry |  |  | test:general_rubric:original |  | 9149a46f77d03bc0c643aeb4c636f5cbb61dbf704b2283cce140ca7fe8b46d6f |  |
| 2026-11-24T08:20:08.327172+00:00 | retry |  |  | test:free_form:polished |  | 5df87f8e4807097ad6f058af6f971d3a54a0088f561b458c3a0d1affd3bac107 |  |
| 2026-11-24T08:20:13.196008+00:00 | retry |  |  | test:general_rubric:original |  | 311aa09993598baf1763042dfc64fbef707121141a9d59e2ab44f57b47068d6f |  |
| 2026-11-24T08:20:15.438247+00:00 | retry |  |  | test:item_checklist:polished |  | db18fc0ad513d9d28625cca3109121b96b77feadb330ced2814a0b276b217506 |  |
| 2026-11-24T08:20:17.368151+00:00 | retry |  |  | test:free_form:polished |  | 120dbe7618b1f56a675f688b7c944d6acc3e5cf5cefc34dd9725e286d694fd9e |  |
| 2026-11-24T08:20:20.415318+00:00 | retry |  |  | test:item_checklist:polished |  | ff78e29578c8bad8b31b6b95db8365457c809b7744276691ba49402ac817ac95 |  |
| 2026-11-24T08:20:24.865316+00:00 | retry |  |  | test:item_checklist:polished |  | 363043fa87a1934708fd8b6c4c3f126035a9b9dba3c3cb3020ccc619eeaa1f7f |  |
| 2026-11-24T08:20:27.682807+00:00 | retry |  |  | test:free_form:original |  | d032ce53976797a3db1b7ec75142deea322ecfc31119cd3e6271dfbb2c40cce4 |  |
| 2026-11-24T08:20:27.984007+00:00 | retry |  |  | test:separate_scoring:original:B |  | aa767e6e76fd70a5da079d508bce75bca716cc2ff1be59f41046f22834e6a78d |  |
| 2026-11-24T08:20:33.158415+00:00 | retry |  |  | test:free_form:original |  | 01164b754b8968a418f1fffaae200c4bdb8ce636f58a14b3c45ce0fbed67cead |  |
| 2026-11-24T08:20:39.211721+00:00 | retry |  |  | test:general_rubric:original |  | 917007672b2a919d61fe1ad91acda74d178b581c424ef8625d2746986b1622a8 |  |
| 2026-11-24T08:20:43.241976+00:00 | retry |  |  | test:free_form:original |  | f015ee54681abc2017bdf12ecf556b226555b9493a99090f40f05f85a07cbd36 |  |
| 2026-11-24T08:20:49.646988+00:00 | retry |  |  | test:free_form:original |  | aea590f1668d3e9b11bd7f08b3277d85a551bc7aba8cb4d08a26c0271d2a2c43 |  |
| 2026-11-24T08:20:49.711149+00:00 | retry |  |  | test:separate_scoring:original:A |  | ee105f0c240d63b4778ee0c598b933a725eae3dafccbbc72c28dd884aa67e805 |  |
| 2026-11-24T08:20:52.988546+00:00 | retry |  |  | test:free_form:original |  | 6c687cad2f3bc04f65d9d32669ae494837b5574bf93afb3b84d9b7dcbb2aba38 |  |
| 2026-11-24T08:20:53.641461+00:00 | retry |  |  | test:item_checklist:polished |  | 3b44564b20bfe35753e221a192315ce75ceee1ab66c4514ad2d958a2a7d241d3 |  |
| 2026-11-24T08:20:59.893201+00:00 | retry |  |  | test:item_checklist:polished |  | 9bae70de3c6adf9d84ee2851a9ba0d74f89173b7ae581109721a564fd615aa83 |  |
| 2026-11-24T08:21:37.408193+00:00 | retry |  |  | test:separate_scoring:original:B |  | 1b7e3188a1c8474ae8c150a7f6d939832e684197df8cdf02783aa80dcaa493fe |  |
| 2026-11-24T08:21:38.070546+00:00 | retry |  |  | test:general_rubric:original |  | d78e364cd46e2cca9b3d9ed50b29ee7bd950d02f5b182ad7714f9a88b27e97a0 |  |
| 2026-11-24T08:21:39.432636+00:00 | retry |  |  | test:free_form:original |  | bccc5ffea5ce56c615fcdd142ad90050c6925b891c9d4eef882ac275c4416209 |  |
| 2026-11-24T08:21:49.434804+00:00 | retry |  |  | test:item_checklist:original |  | 7f4314cc921153f6636eba1ed21b99b8dd9be68945ffd61bb0fc8770cb61e55c |  |
| 2026-11-24T08:21:52.869399+00:00 | retry |  |  | test:separate_scoring:original:A |  | 8de67e5db1307f76b866c900b619fb363ae01a0a5fdb18e40ece54ba8b9c05ac |  |
| 2026-11-24T08:21:54.617032+00:00 | retry |  |  | test:item_checklist:original |  | f86574d3f9c2fb71e88e431d22e69b13c933c26eb8cfb44c54c2941f9bcb6139 |  |
| 2026-11-24T08:21:58.274735+00:00 | retry |  |  | test:separate_scoring:original:A |  | a196f084b26f4d5d4b145e089224e85b81002f8d50eee04153c5e6e356634329 |  |
| 2026-11-24T08:21:59.693128+00:00 | retry |  |  | test:item_checklist:polished |  | 52c943a246ce644529f966f6b742215809637ad64decf2324cde88511644ffe7 |  |
| 2026-11-24T08:22:04.942251+00:00 | retry |  |  | test:separate_scoring:original:A |  | a40e689da93ac234bcf6a28ff5e285f26d2de9f732ae2d072cb5df33eca693bd |  |
| 2026-11-24T08:22:06.301269+00:00 | retry |  |  | test:separate_scoring:original:B |  | a8a9325f8cd8d56975f00346424477de43b9a457d0eb6e5aef0657461eb1ab86 |  |
| 2026-11-24T08:22:08.230446+00:00 | retry |  |  | test:separate_scoring:original:B |  | 0a2d934a1e058f3f054d12c5ab0054c759c33cb89ed2b79ee341241397955b6d |  |
| 2026-11-24T08:22:09.908806+00:00 | retry |  |  | test:separate_scoring:original:A |  | 71339a2df39b34fc71037950e71196fde3fba90e535993292f9f9af99088d76d |  |
| 2026-11-24T08:22:13.817806+00:00 | retry |  |  | test:separate_scoring:original:B |  | df67991c8889af0cdd2459388781d060b12f97a36450c65d2c085f97959b29e1 |  |
| 2026-11-24T08:22:27.067565+00:00 | retry |  |  | test:separate_scoring:original:B |  | 12934efd9bb77d627e07b75b1a88763a69b8e71709f07425064eac87be78a702 |  |
| 2026-11-24T08:22:32.148631+00:00 | retry |  |  | test:separate_scoring:original:B |  | 45366785dd72164d3fe04b35797ca4a6fea83e7a425ab70c0f9724b13fa08d08 |  |
| 2026-11-24T08:23:18.716314+00:00 | retry |  |  | test:separate_scoring:original:A |  | 1ec48e48043c4cde4e6f37985433c25cc55c50eb93a7d011d6e74c9e238192f8 |  |
| 2026-11-24T08:23:23.998936+00:00 | retry |  |  | test:separate_scoring:original:A |  | 56e753e57d06c6cd14ce47222734d4258c8ca403391a5c70ec6967cd4ad48c8c |  |
| 2026-11-24T08:23:31.466055+00:00 | retry |  |  | test:separate_scoring:original:A |  | cd43686ffcc0480fa74f05f88213b3e23620bbf6d7e4142bad8be1b3e5914d4b |  |
| 2026-11-24T08:23:35.818462+00:00 | retry |  |  | test:separate_scoring:original:B |  | ea7a4db7d1200282b74e97ed4baa2f517e5bdaaa4a3814584bc85a712251e7ed |  |
| 2026-11-24T08:23:37.843087+00:00 | retry |  |  | test:separate_scoring:original:A |  | 48756b3cdc2c60bf13f67176a5fbd11263ce353b04f49d2b49e5140fb5a50c63 |  |
| 2026-11-24T08:23:37.895413+00:00 | retry |  |  | test:separate_scoring:original:A |  | 4746b97c455139859b36699ee80ca5da784c9fd9c5f8f61cb919e01a6d0c98ab |  |
| 2026-11-24T08:23:40.851196+00:00 | retry |  |  | test:separate_scoring:original:B |  | 316597f6de26d575f7bf29b957f5a8839e6b0552d7f58caae0cfdb338efdf258 |  |
| 2026-11-24T08:23:42.684959+00:00 | retry |  |  | test:separate_scoring:original:A |  | cf212e61d871653445c6fde86ecf0f1de611b5d9d6e73b24f6d77e37802151bc |  |
| 2026-11-24T08:23:45.450192+00:00 | retry |  |  | test:exam_prompt:polished |  | 6d8aa369f12bef787a559349cbc11459ba02cbba03bf2a4ff08e57f440d78edf |  |
| 2026-11-24T08:23:47.832680+00:00 | retry |  |  | test:free_form:polished |  | 557b1261d1076fecd5ebd7f8580c4b6e2dbf58093596319a4b9ec8bf5be5007c |  |
| 2026-11-24T08:23:48.643635+00:00 | retry |  |  | test:general_rubric:original |  | 00335caa305bf0bcbc8e59d58852bd6487a8f206adb9d21d40f7e3c885cf0305 |  |
| 2026-11-24T08:23:49.700715+00:00 | retry |  |  | test:separate_scoring:original:B |  | 05d64361aecc40ad5497c6600e34b2d545554bf7e37428bdd9d2e661222ca6c9 |  |
| 2026-11-24T08:23:59.169553+00:00 | retry |  |  | test:own_requirements:original |  | 3ff5b2c2605afb5a64dca21ec97a89e64d1ccdd0ee9332f86d45886b96e46cce |  |
| 2026-11-24T08:24:21.002824+00:00 | retry |  |  | test:item_checklist:original |  | 4cb04497a5c1efc27777e7f05a99c568d56815d556a381385060ef32753fa833 |  |
| 2026-11-24T08:24:22.970591+00:00 | retry |  |  | test:free_form:polished |  | f5bf5c5229070509f45e7a0724005f100a2e030fa97a4f046a5e7b28ada2d843 |  |
| 2026-11-24T08:24:24.687004+00:00 | retry |  |  | test:general_rubric:original |  | 41dcc66010f9c88ecfc133f6a6133d53f01010eb9cf153fe934150fb21658203 |  |
| 2026-11-24T08:24:25.450889+00:00 | retry |  |  | test:separate_scoring:original:B |  | 6648b7c8eada9164424c91145ea5f51ac62d3e6e47ad67519ad7f4656a16308a |  |
| 2026-11-24T08:24:27.203947+00:00 | retry |  |  | test:item_checklist:original |  | d82b1eaa3af55d32dcaae58e63a7ed6eb8c2178ea4c611c1ec5182a032249d6f |  |
| 2026-11-24T08:24:32.624563+00:00 | retry |  |  | test:own_requirements:original |  | 5dcebb02ef16637dca9cd00cc267620608d40bb004b46edbd616b30bb16a8018 |  |
| 2026-11-24T08:24:38.254175+00:00 | retry |  |  | test:separate_scoring:original:B |  | 490302e8afbf82784e1fd663f57a04fe7d92cdea336db9eaf9092c6264753157 |  |
| 2026-11-24T08:24:45.109585+00:00 | retry |  |  | test:free_form:original |  | d963108f40f9dc0f73f3fb08ac4862e74de3712bae8bbeb4c4681a42a8ac1e6d |  |
| 2026-11-24T08:24:47.555442+00:00 | retry |  |  | test:separate_scoring:original:A |  | bf94af03f9ed4e04a7ab6973b69bf2c69ea62f6f333729f3451d2da8ec6fd639 |  |
| 2026-11-24T08:24:49.361132+00:00 | retry |  |  | test:item_checklist:original |  | c9d635457dcb157fef307498ddfff7db5349cdac99a3e29f64abaae8b646ea34 |  |
| 2026-11-24T08:24:51.613720+00:00 | retry |  |  | test:general_rubric:original |  | ca36cb25c7c62930acf9f4c0affdcb0a263f9a7d4f632d74de0251fbfc5952ca |  |
| 2026-11-24T08:24:53.463039+00:00 | retry |  |  | test:separate_scoring:original:A |  | 215754fdc68c2ade80aa02172081b830db2fff798f98760cc04591c4368f220e |  |
| 2026-11-24T08:24:55.598295+00:00 | retry |  |  | test:separate_scoring:original:A |  | b2e2c09fbd274b64583e051f57453243dd0f029bf7efc17690fcb56ddd8261d7 |  |
| 2026-11-24T08:24:58.054390+00:00 | retry |  |  | test:free_form:original |  | ab18d7da5babf712da86ff31c5a09e81123cf09f396595dd6e46872650005bfc |  |
| 2026-11-24T08:24:58.129579+00:00 | retry |  |  | test:item_checklist:original |  | 6ae380850db2a5362d8ac66efd1f737a352cb06075be8dbb053ab4f712c83c45 |  |
| 2026-11-24T08:25:00.095208+00:00 | retry |  |  | test:general_rubric:original |  | 5eac4c807fa2ad67a6164edaf361035c06123befded029d494cfea36e92f097c |  |
| 2026-11-24T08:25:00.276625+00:00 | retry |  |  | test:free_form:original |  | 227a90e80de0b3557c99d8b45c8d144f7ade84838fd423eb1b77b8c7894afe17 |  |
| 2026-11-24T08:25:01.743562+00:00 | retry |  |  | test:separate_scoring:original:A |  | 2fb230512d5de5e7f29c740505eaf01f38621bc59c23b3b9d7ab8fa7a9471697 |  |
| 2026-11-24T08:25:05.348088+00:00 | retry |  |  | test:free_form:original |  | c7a504c09c6fa12af34ac9c9a4f6407a706dbddcd36ce1976b634d7d387945ef |  |
| 2026-11-24T08:25:05.603938+00:00 | retry |  |  | test:separate_scoring:original:B |  | b48cb1d9932009fbeb01c28265009ef30819167eb5c8e159588dfa0b56247f71 |  |
| 2026-11-24T08:25:09.612736+00:00 | retry |  |  | test:item_checklist:original |  | bf256e0e89eae4ecf6d0e2c4783c520b5cca88d3c61d634faa10185c441ec512 |  |
| 2026-11-24T08:25:13.786251+00:00 | retry |  |  | test:item_checklist:original |  | 2ab61eaf246b8cdf57988827b96f198ba7c3cdd03f0b2c40a91299a396d074da |  |
| 2026-11-24T08:25:15.938699+00:00 | retry |  |  | test:separate_scoring:original:B |  | c09dc45a70b5e397a311b799b01b1339f7ef2de42525bf9ee612924893d35872 |  |
| 2026-11-24T08:25:17.632266+00:00 | retry |  |  | test:item_checklist:original |  | 62c128dc65e65d1df255e76a5ef4238208622009e8fd9b56f81cad096c57feeb |  |
| 2026-11-24T08:25:19.500689+00:00 | retry |  |  | test:separate_scoring:original:A |  | c5db5de99cfbe3b8bfaec55002c97e730bb9fbd3060ab948e22dce71df8e0487 |  |
| 2026-11-24T08:25:21.306933+00:00 | retry |  |  | test:separate_scoring:original:B |  | bad6f213cbadb569d38c3e7b2a5c8481b1c35b348fb26578e1d9bc83e0310fce |  |
| 2026-11-24T08:25:23.212666+00:00 | retry |  |  | test:separate_scoring:original:B |  | 9f095c3c14a86767c31f5230c65e448fc4a01f049915df12bd09b43228ef7223 |  |
| 2026-11-24T08:25:25.221147+00:00 | retry |  |  | test:item_checklist:original |  | 7f5b130f52effee142c8fbd4defc19c7104e21e4125bbf87999f5e424835fffe |  |
| 2026-11-24T08:25:26.466045+00:00 | retry |  |  | test:separate_scoring:original:A |  | f08ea3a737296040ce4c761f56aaa3e1829f7020f92d3b158e4070db6dc84dcf |  |
| 2026-11-24T08:25:31.258442+00:00 | retry |  |  | test:separate_scoring:original:A |  | 95f50ab3e3ab6366d7331a624a44a8e50ad954d7451faa62b376f20c6ca19745 |  |
| 2026-11-24T08:25:36.101002+00:00 | retry |  |  | test:separate_scoring:original:A |  | 6121d94f9934d8745fa7355e73e9b3a96ff712a3d37bd9d98fd25dbf5fb4c050 |  |
| 2026-11-24T08:25:36.245940+00:00 | retry |  |  | test:separate_scoring:original:B |  | 85fe67d29fb33232392e596f1cbd2ff8632e79eea7e46e7fe73eba8a6b3cd49b |  |
| 2026-11-24T08:25:37.988522+00:00 | retry |  |  | test:general_rubric:original |  | 0cf601adbb3bf3ebdf118100d94e08cf89f42fb464de00c7eea8ebafdc492329 |  |
| 2026-11-24T08:25:41.805828+00:00 | retry |  |  | test:separate_scoring:original:B |  | 5821c473d9d87f327183760937c81e9cfa40f7590a2b1d560c04ce1b57969378 |  |
| 2026-11-24T08:25:43.061543+00:00 | retry |  |  | test:general_rubric:original |  | 2b261d7f4dd1188c30ffd7d09d11f76dac1253df838510727b9a1518f23646e9 |  |
| 2026-11-24T08:25:46.816973+00:00 | retry |  |  | test:separate_scoring:original:B |  | 23b52c6f814884366f2fa650fbb9c2f905cf84ab10acf14459bc3f3b3a19df2e |  |
| 2026-11-24T08:25:53.823815+00:00 | retry |  |  | test:separate_scoring:original:B |  | 098b6f6a113c788d9573b8ce341092afa2c0ec58a67e1e08d215a55f15fe5dac |  |
| 2026-11-24T08:25:55.694129+00:00 | retry |  |  | test:general_rubric:original |  | a0cdd2cd8039b8a1651fe376a34d09a8a8ad9c65b1f3042ad5b8382c42b6f500 |  |
| 2026-11-24T08:25:58.978481+00:00 | retry |  |  | test:separate_scoring:original:A |  | aaf3584741f7a910fb02b8327111da1e0a0dd02809fc6ec66f1ce59034a9481d |  |
| 2026-11-24T08:26:07.334387+00:00 | retry |  |  | test:general_rubric:original |  | f19f300a26ba5c55491a46a1c3069ac1345edcc189aeb8e44fa49308e75dd8a8 |  |
| 2026-11-24T08:26:11.859182+00:00 | retry |  |  | test:item_checklist:original |  | ca8a67718a63e19be0604fbd219008727f9fc0309bc59a6187ae315108b09b33 |  |
| 2026-11-24T08:26:14.688116+00:00 | retry |  |  | test:general_rubric:original |  | 527d09fba30116c8f7433a0b5e57f6bfcbab7a1ca86b9df80fb3190b68e7787e |  |
| 2026-11-24T08:26:18.320824+00:00 | retry |  |  | test:item_checklist:original |  | 9f483ec8599a2478bbed296a5bf314902ddefa5f83e88759ef75595868358344 |  |
| 2026-11-24T08:26:20.306930+00:00 | retry |  |  | test:general_rubric:original |  | 5f35e3377a7dd5e8c1306056e49e596599fb7c650f6deb28ff910b1021725d53 |  |
| 2026-11-24T08:26:28.145793+00:00 | retry |  |  | test:separate_scoring:original:A |  | c305222ca4f29c0bff1119660e82dcab18ab25612cd5bf39fe990df6a6344144 |  |
| 2026-11-24T08:26:28.353334+00:00 | retry |  |  | test:free_form:polished |  | ed0ba2ca30fdf963abcf2988e1fd85910bdbd6abf4d561d15c9f37d8e80b1e1f |  |
| 2026-11-24T08:26:31.816006+00:00 | retry |  |  | test:item_checklist:original |  | 0fc55703098a46a5a3f41c849ae71e1a8511d237fbd76befe556f5f2492cbc93 |  |
| 2026-11-24T08:26:32.403034+00:00 | retry |  |  | test:item_checklist:original |  | fd12cd69bb750a09f9430f23b60d32917416a551dd9ea0095a38f53bcd81c311 |  |
| 2026-11-24T08:26:32.560098+00:00 | retry |  |  | test:general_rubric:original |  | 00bb0243dccb0db99dd0fbdfefcb0d5c3bd598ae84ace2595d8e13630b8a8f59 |  |
| 2026-11-24T08:26:34.523234+00:00 | retry |  |  | test:free_form:polished |  | aab9c3c58bdbe78e3a7b073d6d51c7f70bd3d8224d8307bd095e987906ae5bb3 |  |
| 2026-11-24T08:26:37.284952+00:00 | retry |  |  | test:item_checklist:original |  | 5f379006eb46d360763cc20353dea5578aa5a558532d027dc8eca310ab4a5a92 |  |
| 2026-11-24T08:26:39.317463+00:00 | retry |  |  | test:general_rubric:original |  | afd201f5c7ecbe591c1622c1f5f72e986c5fa49584c7b1a29bf11cf483999ec4 |  |
| 2026-11-24T08:26:43.222848+00:00 | retry |  |  | test:separate_scoring:original:A |  | 0d656d1d852d352bf045c91a246e9b4d6cd0cf01b3e9e1c159147d0ed5f128ab |  |
| 2026-11-24T08:26:47.793603+00:00 | retry |  |  | test:free_form:polished |  | f06067d77de085c262a0d02b24a1d0f7677a1ec18a671dc9ba4bb4e75f9b7f32 |  |
| 2026-11-24T08:26:49.735738+00:00 | retry |  |  | test:separate_scoring:original:A |  | 788fb6c3076bb7945668ca74e0a3e32fbb75b30bfa403b13d7d8150a0a39905e |  |
| 2026-11-24T08:26:59.330389+00:00 | retry |  |  | test:separate_scoring:original:A |  | f54f4535491b7521673549430842fc44b71c9d39ac1003324a436d74134d0d56 |  |
| 2026-11-24T08:27:01.201954+00:00 | retry |  |  | test:free_form:polished |  | a1c4733da41f7f3c803fc96fa28afe8a7b3fea45d43f1f247080450212f1a27b |  |
| 2026-11-24T08:27:09.529403+00:00 | retry |  |  | test:separate_scoring:original:B |  | 1f72e7d93e380ec2e31b79c9a0736faf0bf893cc5ecb739a4a73d610e453e386 |  |
| 2026-11-24T08:27:11.338719+00:00 | retry |  |  | test:separate_scoring:original:A |  | 8a2ecc5699a9d1e527dcfce5905d854232a634ea403c3a515162d82920cc3abe |  |
| 2026-11-24T08:27:12.640198+00:00 | retry |  |  | test:item_checklist:original |  | 75c2c576ce89a93e9a7ce65407a4600d4ba34869368e4e58e5e9e8da18f121d5 |  |
| 2026-11-24T08:27:13.450307+00:00 | retry |  |  | test:separate_scoring:original:B |  | e839c326613e410111b5f7b4f6c2d5838fb1c87cd2b1008b7d5408ead4d3a476 |  |
| 2026-11-24T08:27:14.923959+00:00 | retry |  |  | test:separate_scoring:original:B |  | d32f35a2ffcf76ac518412e3f896a217959b477c4d0d3dd12049259920a38418 |  |
| 2026-11-24T08:27:33.891891+00:00 | retry |  |  | test:exam_prompt:polished |  | 9b585445429ec47fe2b52f082c90b78f9cac5db6532dea4b490526222401d53e |  |
| 2026-11-24T08:27:36.046269+00:00 | retry |  |  | test:item_checklist:original |  | 3cbc33be62178abad7f378f8fb3e6e24c190465b12e49204d1435e4a3941c114 |  |
| 2026-11-24T08:27:38.272481+00:00 | retry |  |  | test:general_rubric:original |  | 63f8f714797eab85f1af613d1ff1563f752ae5f715c9528701bbb0d1fc33c8fc |  |
| 2026-11-24T08:27:39.169795+00:00 | retry |  |  | test:exam_prompt:polished |  | 69bfa8fe43320220a1731b5b661427255a118bb348f428128aad66f92a3d9841 |  |
| 2026-11-24T08:27:58.234520+00:00 | retry |  |  | test:separate_scoring:original:B |  | 654726bb1885f89aeb36ed904b698c8c18120418ed7104e3dff1bbbf45145d02 |  |
| 2026-11-24T08:28:39.863115+00:00 | retry |  |  | test:general_rubric:original |  | 56d4d25cd861fb119dfece82ea48f68b7087af906939463604bdad852ecc2809 |  |
| 2026-11-24T08:28:44.968695+00:00 | retry |  |  | test:item_checklist:original |  | 50f2ab566852c180fe2feb387731ed1467cb1cb13cc5732f7c9530ded50616fa |  |
| 2026-11-24T08:28:49.936271+00:00 | retry |  |  | test:free_form:original |  | 69b9aaf9ad2d76b275eacd9bf85aef1a67691728249843861267d298fe7199d4 |  |
| 2026-11-24T08:28:52.184273+00:00 | retry |  |  | test:free_form:original |  | 703b1dea7633aac3fea4695312af7851ed056a03528659d0d475f91add89d6ad |  |
| 2026-11-24T08:28:57.984706+00:00 | retry |  |  | test:separate_scoring:original:A |  | 0aa61f743d6e7e3fdd2c45c192594ab7ec5dcce8d9bc08c34abe60a6b42cd5ad |  |
| 2026-11-24T08:29:00.268320+00:00 | retry |  |  | test:free_form:original |  | c2bf39774dcfc82299d5ac4231cbc61aa1064dd4d8eca59c1fd0832a7de4c97c |  |
| 2026-11-24T08:29:01.637384+00:00 | retry |  |  | test:separate_scoring:original:B |  | 2a514f157679cd4a7a77b99b6b25bf944a1c70b834bb65f52de3a65255d8382c |  |
| 2026-11-24T08:29:05.379663+00:00 | retry |  |  | test:free_form:original |  | eecc39a8826ee2f515ff55925019753148289c42c740a2c8b9fe13e397c8bf38 |  |
| 2026-11-24T08:29:07.280894+00:00 | retry |  |  | test:free_form:original |  | 80d852ca0307e16e43729302942033321694ab16e8770bd691c712119b66c23a |  |
| 2026-11-24T08:29:09.249446+00:00 | retry |  |  | test:separate_scoring:original:A |  | c9da180bf6a235701bafa7f8f1ab6b11e5635223b236d7b9fd0f78c213a8504a |  |
| 2026-11-24T08:29:13.148351+00:00 | retry |  |  | test:free_form:original |  | 10d833696bd0338a6f0e0e888d2dadee903491913cc5d04019ff4964a2833975 |  |
| 2026-11-24T08:29:15.100769+00:00 | retry |  |  | test:separate_scoring:original:A |  | 2a295d535ddbfb3730305270bfc8a2bf67326ed8a907e2e37d97446bbd2cc36e |  |
| 2026-11-24T08:29:18.985869+00:00 | retry |  |  | test:item_checklist:original |  | 2e714c97c7c03d39ede5bf5f71e5b2cefa6bf31b86b9a6f86cd5ad463d5cb484 |  |
| 2026-11-24T08:29:19.469916+00:00 | retry |  |  | test:free_form:original |  | 0b19f3982201366161a9cad1f9e640d394913b9c64034090a73d1ccad6142664 |  |
| 2026-11-24T08:29:20.971006+00:00 | retry |  |  | test:exam_prompt:polished |  | 34197747b2342084433c98628622ad12b0f0f47e1e0d9e143941a442cf43e712 |  |
| 2026-11-24T08:29:22.877913+00:00 | retry |  |  | test:separate_scoring:original:A |  | 230162e861c2fb8d655fdd484943827186d8a98c7bd24446475433c05f2c559e |  |
| 2026-11-24T08:29:24.758705+00:00 | retry |  |  | test:separate_scoring:original:B |  | f884e87c65ceb4e273b738445b98294c4ba1ec5970190c630df6337c2d947ce7 |  |
| 2026-11-24T08:29:25.608096+00:00 | retry |  |  | test:item_checklist:original |  | 8f190a34c0fb0685192281751b6e42c79b405ed230c14858282644e730c728e8 |  |
| 2026-11-24T08:29:26.823514+00:00 | retry |  |  | test:free_form:original |  | ed5d583cde7501d067fa7c3ac43aa499438c4d86d97d1cf1240da04c5985dce0 |  |
| 2026-11-24T08:29:27.460379+00:00 | retry |  |  | test:exam_prompt:polished |  | 78e650c56eaa82ca8039bec8563811d67069e13f4f78315b35ed4fca5dc6af4a |  |
| 2026-11-24T08:29:29.972614+00:00 | retry |  |  | test:separate_scoring:original:B |  | 0e9455e97ccc56266346f550e7882a4d95ed36c5556d2fbc642434ce552e9feb |  |
| 2026-11-24T08:29:33.434079+00:00 | retry |  |  | test:separate_scoring:original:B |  | 5696c67fe65d2c42ee9c91247193fa68294be1035c472b78752865b8bb0eb798 |  |
| 2026-11-24T08:29:35.599281+00:00 | retry |  |  | test:separate_scoring:original:B |  | 9b64048511295dad7e96fbeb3643e99b0d7626833920e44eacec40214a4f9a42 |  |
| 2026-11-24T08:29:37.449673+00:00 | retry |  |  | test:item_checklist:original |  | 65fd79f0656424302a99e81fffa6308a6beb740f0776e4c85844c7169a7fe749 |  |
| 2026-11-24T08:29:37.523481+00:00 | retry |  |  | test:free_form:original |  | 759ac35cbca365a553fb043b6f46296a2cf579a57829ad70780c2976aeb7d86d |  |
| 2026-11-24T08:29:39.329117+00:00 | retry |  |  | test:free_form:original |  | 5016b80c977166ebfbe11b3ece17e61d3c5af991cd9665dd5b6a17dcbb4d21da |  |
| 2026-11-24T08:29:39.739395+00:00 | retry |  |  | test:separate_scoring:original:B |  | 1b00a15ed1a2516100ec585fbf5bed3523a114b96b0bda46352c1e6908495362 |  |
| 2026-11-24T08:29:41.125835+00:00 | retry |  |  | test:separate_scoring:original:B |  | dd9e058d08d720af21d5da02692650116944f79e9fbc7a96ad935069f3f6794d |  |
| 2026-11-24T08:29:42.417388+00:00 | retry |  |  | test:item_checklist:original |  | e68723236a00e1b59cc743317410a10e88087c26067d1799d4a5a7b4c03f0875 |  |
| 2026-11-24T08:29:43.071531+00:00 | retry |  |  | test:free_form:original |  | f129d3cedca40a655f954899f9e0ab5015fbf57764fb94cfc4578c4eb344d4c4 |  |
| 2026-11-24T08:29:44.954698+00:00 | retry |  |  | test:free_form:original |  | 8ab4de87b632c0614a8d591fa8233e10cf54b5e49901f10bde75b50c9ef8129e |  |
| 2026-11-24T08:29:47.581290+00:00 | retry |  |  | test:general_rubric:original |  | db229e6d03d73968e758dac949a8e89b10450d7f2011b2fd3886b24e788154d5 |  |
| 2026-11-24T08:29:48.410656+00:00 | retry |  |  | test:item_checklist:original |  | b56bc65cad25ce6e8007a484d7e7a0f84e07da77fc60bd37e8e7873ca8935a65 |  |
| 2026-11-24T08:29:52.004474+00:00 | retry |  |  | test:general_rubric:original |  | 1590e3741c29aff911ac7bd95e81dac5fe07589cafc5327760716d8a2f974449 |  |
| 2026-11-24T08:29:53.304000+00:00 | retry |  |  | test:own_requirements:original |  | bdb9774715bb72b9a25999f7029da998502ff657f040e186f004383fea0dbde6 |  |
| 2026-11-24T08:29:53.748466+00:00 | retry |  |  | test:general_rubric:original |  | 5a6d2e271ba4042b1c224c097fe43857263e88e1383695d6933d41d549b913d6 |  |
| 2026-11-24T08:29:55.820069+00:00 | retry |  |  | test:item_checklist:original |  | 76b269ba9647f929cbbcecafd9c88173e65a1033f869efe1fadbb0398a6d4715 |  |
| 2026-11-24T08:29:57.839609+00:00 | retry |  |  | test:general_rubric:original |  | bcc5c51706023221543a2b63e2ee5aa9ea299e913a3c0a8d3f42086b2c9dec7c |  |
| 2026-11-24T08:29:59.914207+00:00 | retry |  |  | test:own_requirements:original |  | e318b860479e7894f10badd61da66e84be412de1924f3e0d2925d3666f3490bb |  |
| 2026-11-24T08:30:08.005407+00:00 | retry |  |  | test:item_checklist:polished |  | afc9cbed8a8e5409c255663a21d3fec0e791105a4f7f508cb001de640ba4bb16 |  |
| 2026-11-24T08:30:11.458949+00:00 | retry |  |  | test:general_rubric:original |  | 1d968fc85cfb0d84cce023e50f8b20c4d4e688d2062cfe658137a6245545812e |  |
| 2026-11-24T08:30:15.674782+00:00 | retry |  |  | test:general_rubric:original |  | 7465cf3c6bf60612e0550605c04cf90f213e5ce4294a8eba9a34e28b3142e0db |  |
| 2026-11-24T08:30:17.179020+00:00 | retry |  |  | test:item_checklist:polished |  | db892347bf0dfaa1de3d705fc2d998d03315c2542ab27fa492cd704a920e6e3a |  |
| 2026-11-24T08:30:20.616050+00:00 | retry |  |  | test:separate_scoring:original:A |  | 6162ca259da55558b881bf3045943c80c619ef95e65e48edf6197ba3fd74ab5c |  |
| 2026-11-24T08:30:26.499515+00:00 | retry |  |  | test:item_checklist:polished |  | b07aec2a7f64075de2f7c715bbfdcf006cc8e131e2b513abaa403aa7081125f5 |  |
| 2026-11-24T08:30:28.677638+00:00 | retry |  |  | test:item_checklist:original |  | ff62ac6a0011503bb2fb4420c575da29a2f068a43d1748c42be849f8870e2eb0 |  |
| 2026-11-24T08:30:30.653097+00:00 | retry |  |  | test:general_rubric:original |  | c8d87205f74d52426fcf219e513a177541f54b003d065acc9b51cc8b546cdc39 |  |
| 2026-11-24T08:30:32.394769+00:00 | retry |  |  | test:item_checklist:polished |  | 1f818589efff0210f7714a72f70e45f631f0d29dba79ca5ed4105c7684112de4 |  |
| 2026-11-24T08:30:34.489666+00:00 | retry |  |  | test:item_checklist:original |  | a7f27b3882877e286cc4e90a9753b99a22f817b2a7d5787314613d94976b4920 |  |
| 2026-11-24T08:30:36.345987+00:00 | retry |  |  | test:general_rubric:original |  | 9f0a9fa2b96d9f54e8c66736e5a9181dcc212766a758cf4aa5d971c91dbd4b0c |  |
| 2026-11-24T08:30:41.495103+00:00 | retry |  |  | test:general_rubric:original |  | 4e49facefbf01f0bb75aadec41a22e81b3ca3edfc4f789c9a4d37909a332fcba |  |
| 2026-11-24T08:30:43.340114+00:00 | retry |  |  | test:separate_scoring:original:A |  | 45304e3ca0b12b194212e924f40fe21e275b21b421cc62a419cd4b7b31b649e4 |  |
| 2026-11-24T08:30:55.633902+00:00 | retry |  |  | test:separate_scoring:original:A |  | cde2df1a28ce88d396318da8ff5da7fd7f3120179009f6cda942d53de8c3a945 |  |
| 2026-11-24T08:30:59.292293+00:00 | retry |  |  | test:free_form:polished |  | 0f7160d31ee0ab3c0e1901860dd1d48e0765fdaa77ab47d4a88ac4f26f122206 |  |
| 2026-11-24T08:31:01.506549+00:00 | retry |  |  | test:separate_scoring:original:A |  | 639965aa81e9696a3d43571d5453c84dd7fa9ba85ec388cde4d4d2eee5f61268 |  |
| 2026-11-24T08:31:02.718196+00:00 | retry |  |  | test:exam_prompt:polished |  | e07ccee2a99a9d7b4a9a7ae373f59bb074bb22ed400ae352f8a1ce112de767df |  |
| 2026-11-24T08:31:03.111897+00:00 | retry |  |  | test:item_checklist:original |  | f6787afa98f3731fd97e891e5e81fb11c3f050676998901d9359effc7a894b3e |  |
| 2026-11-24T08:31:04.191145+00:00 | retry |  |  | test:free_form:original |  | 1ae758b5aacfa24b4a2616141a391157814870e57557f2376cab7479d43cc019 |  |
| 2026-11-24T08:31:05.409978+00:00 | retry |  |  | test:free_form:polished |  | f309a3159d7f0ffe90d6f5888d0c5c6742ea1be0fc32af2776e69b14e11347f5 |  |
| 2026-11-24T08:31:07.806093+00:00 | retry |  |  | test:item_checklist:original |  | 5b30af0210af80dda4994af633b594b748a0da43c13bff8e140d8f976628a553 |  |
| 2026-11-24T08:31:18.245691+00:00 | retry |  |  | test:separate_scoring:original:B |  | c7a4b893438c59df1bd905862a761a67b867840165721241665efe8e7221d619 |  |
| 2026-11-24T08:31:22.316044+00:00 | retry |  |  | test:general_rubric:original |  | 7edb0fb5abee3f3d357f8095f2846976460d6b8da8005ba94c4ab1179b51dd19 |  |
| 2026-11-24T08:31:27.689302+00:00 | retry |  |  | test:separate_scoring:original:A |  | 8681043cefb08eb895cb7b5b84624380a473e8fd084ca08732e2e5c5e03923ce |  |
| 2026-11-24T08:31:27.942102+00:00 | retry |  |  | test:separate_scoring:original:A |  | 6696d590c5b568c55d0bc64a0e4bd0022c800386ffac0181bd8cab1f962c5bc1 |  |
| 2026-11-24T08:31:29.495905+00:00 | retry |  |  | test:separate_scoring:original:B |  | 8b67b76361aaadd1d568df4d165457e54d4d8f3443e9048f8a0242df630ff5c5 |  |
| 2026-11-24T08:31:29.669340+00:00 | retry |  |  | test:general_rubric:original |  | f7b7411757eb61b9a62d9c2f55baec93dc67f6a04ac99571b6806de8c494cee3 |  |
| 2026-11-24T08:31:35.307334+00:00 | retry |  |  | test:item_checklist:polished |  | f99e62d1e3f52f714b8f9ccba366c7dfebdffba670553b551fa96f88f16e418e |  |
| 2026-11-24T08:31:36.953802+00:00 | retry |  |  | test:separate_scoring:original:A |  | 786ef0488b9d3777478dcbd43b5a7fc888b98d4675090af5ad1eb4caeb64a5b3 |  |
| 2026-11-24T08:31:37.391888+00:00 | retry |  |  | test:separate_scoring:original:A |  | 85a7a28d391fc544d26810b2351ca4abb4bdca8d9947ef22a7f699ccc995f61f |  |
| 2026-11-24T08:31:38.820148+00:00 | retry |  |  | test:free_form:polished |  | 121fc0e82711f9279d5546e53b1b6125a55033a2e2fb6bb3d8f5b879c620f500 |  |
| 2026-11-24T08:31:41.244548+00:00 | retry |  |  | test:general_rubric:original |  | 1329749dfb6da42a4f2274d30e869119564a6c90cacf18035cffa5f998900a03 |  |
| 2026-11-24T08:31:43.009609+00:00 | retry |  |  | test:item_checklist:polished |  | 046b17d28cd5f27e2aeb40829d6292c61c99237848e6475600214de7e416d1c0 |  |
| 2026-11-24T08:31:43.215412+00:00 | retry |  |  | test:item_checklist:original |  | 22e0f81c575b435e615834d33e30f96c49af955104ca0255b0ccaed641b027e1 |  |
| 2026-11-24T08:31:44.942868+00:00 | retry |  |  | test:exam_prompt:polished |  | c6e379e81656b74b9edf89cb387ca8d16899191cdeda2eb14b72a50eb838cac8 |  |
| 2026-11-24T08:31:45.014494+00:00 | retry |  |  | test:free_form:polished |  | 74fe379dea1e6e0499894202b35b29d15c45b7de92aca3692356111eb3f38d7f |  |
| 2026-11-24T08:31:48.843745+00:00 | retry |  |  | test:separate_scoring:original:B |  | 9e843c92a7886e19a4ec30cd357e9767441c3fe35e4cae34623c70ed3aa23c34 |  |
| 2026-11-24T08:31:49.180745+00:00 | retry |  |  | test:separate_scoring:original:B |  | 2025feea4bee7b28383340b26a0ea1d3c0d5e5febbb5d7643bbf82ed5a5af6c8 |  |
| 2026-11-24T08:31:50.696030+00:00 | retry |  |  | test:general_rubric:original |  | 83aae5b251f6850c0a516a145552b656b5123439fefd57243b495ed5a388a77d |  |
| 2026-11-24T08:31:51.268549+00:00 | retry |  |  | test:item_checklist:original |  | f063d804776f2c3e244d60a6b9704d8e9b06b88da9e10c61f8a9fc76d18b4a7b |  |
| 2026-11-24T08:31:52.689358+00:00 | retry |  |  | test:exam_prompt:polished |  | bab4abe6a73be58a9e5d3f07f3935f6f5af8b23242d703cfc0f357fde1a5bfd6 |  |
| 2026-11-24T08:31:55.028241+00:00 | retry |  |  | test:separate_scoring:original:B |  | 012e61fe89bd410b20b22b92ded1de4d01630ad2d736f5d64ea2c10f89d2924e |  |
| 2026-11-24T08:31:56.914380+00:00 | retry |  |  | test:free_form:polished |  | 92d72c87ea501fa45c19b9b6aa852b726d476ef548fa6e22999bf45da5718542 |  |
| 2026-11-24T08:31:59.003388+00:00 | retry |  |  | test:separate_scoring:original:B |  | f05778ab42afec9f689940a9a309400ee67c4f20143c28750dad0de31d1f5c82 |  |
| 2026-11-24T08:32:03.718232+00:00 | retry |  |  | test:free_form:polished |  | 6bc875f4d357592df059caff946ec19702f8a49a3aecd3d544520344fa064b90 |  |
| 2026-11-24T08:32:08.169263+00:00 | retry |  |  | test:exam_prompt:polished |  | 5282f8eaee0b8c8fb86415c5db9d7aea35630a13f2b9f3c8f3c9820eb103a2fd |  |
| 2026-11-24T08:32:10.045163+00:00 | retry |  |  | test:separate_scoring:original:A |  | 34c5c30e500dcba13386e41a9ed9255912085dbccb4808be49f78ef57c231b4b |  |
| 2026-11-24T08:32:10.187746+00:00 | retry |  |  | test:item_checklist:original |  | ed4e3d0b39ecfbf664b5d75a921e513348db5691d70e4aa826055aa29fe2db1a |  |
| 2026-11-24T08:32:12.101114+00:00 | retry |  |  | test:item_checklist:polished |  | b39be88443b608628fa508aff5b5f940ad56fd70ce4470aad7b14b157ef1b171 |  |
| 2026-11-24T08:32:14.158474+00:00 | retry |  |  | test:separate_scoring:original:A |  | ebbd73dca3b0e31199168e684928d820f4182dd9f50269ee94b5bccb29bde27b |  |
| 2026-11-24T08:32:16.197900+00:00 | retry |  |  | test:exam_prompt:polished |  | f89e32f4b2ee6568fcb2bd3b3d1e9cdd7b93a854a7a0924cd6ca837ad3dc8a5e |  |
| 2026-11-24T08:32:16.400423+00:00 | retry |  |  | test:separate_scoring:original:A |  | 9c8361a4335984c2b799449af4823d810de834b47abab4c5cf7fad2118b484f1 |  |
| 2026-11-24T08:32:18.353870+00:00 | retry |  |  | test:general_rubric:original |  | e5d579511f03d242a26271082cd09e2d54e848dae9183f4ddf9d9524edeb3662 |  |
| 2026-11-24T08:32:18.374122+00:00 | retry |  |  | test:item_checklist:original |  | 6347b300b40774411cdd7da5a2ebf0133671c9da41859e432ad44a8a3485e1c9 |  |
| 2026-11-24T08:32:20.179174+00:00 | retry |  |  | test:item_checklist:polished |  | 235827bce15b58fc84a31cfb61bdd9649c4d1357c2875c2a0f308565f5f7bd11 |  |
| 2026-11-24T08:32:20.456075+00:00 | retry |  |  | test:item_checklist:polished |  | 66727a712d81c2320fcd8b1162753a0dc2db9196c0158945379020d15434882b |  |
| 2026-11-24T08:32:21.853966+00:00 | retry |  |  | test:separate_scoring:original:A |  | 54bd78a22441895659b6d8df7c2d1c2a02a37206dc587d08315a70c4de9eaafe |  |
| 2026-11-24T08:32:23.428957+00:00 | retry |  |  | test:general_rubric:original |  | e14fb0f9ec244d97440f228cc9743951e7c4c8cd2db5ff3e44466354b1380c8f |  |
| 2026-11-24T08:32:26.458977+00:00 | retry |  |  | test:item_checklist:polished |  | 44eb67b3fca695a443cda9a8575f8fc847ec56921f74a7789a28def68dd9468b |  |
| 2026-11-24T08:32:27.975518+00:00 | retry |  |  | test:separate_scoring:original:A |  | 0da9163239e673877f5d3e0f9952b6cbf11fb05d752461039db444c30779c987 |  |
| 2026-11-24T08:32:30.006342+00:00 | retry |  |  | test:separate_scoring:original:B |  | 37c228a1171921ea7cfb13374cddf0ea40521759ba55214bc63b9a122cfd06ff |  |
| 2026-11-24T08:32:30.841580+00:00 | retry |  |  | test:free_form:original |  | 5bfe148ff95f90231af1962ba5cdb5b7f09db8e9309a71340913e034b9c41647 |  |
| 2026-11-24T08:32:34.699664+00:00 | retry |  |  | test:separate_scoring:original:B |  | 28a34600c15901522a4201ab064d59888fc23cdff9da2ac1d6047f5d7f037a25 |  |
| 2026-11-24T08:32:39.387370+00:00 | retry |  |  | test:item_checklist:polished |  | 60214606ef4730ca5569e79de6ac4d652bf4363def5025d664b0f046224ebd68 |  |
| 2026-11-24T08:33:37.609258+00:00 | retry |  |  | test:item_checklist:polished |  | bcfcf18a013b205b3304763c83044dad69e9f552830d8a2f4a09526870868edd |  |
| 2026-11-24T08:33:41.689696+00:00 | retry |  |  | test:exam_prompt:polished |  | bc3f9fc0f8cb635d7f20f42fc213e167168bd69c201d192a439fc272773b2b8b |  |
| 2026-11-24T08:33:52.736300+00:00 | retry |  |  | test:separate_scoring:original:A |  | f5ae0181e01e9f61ccbb8adcec359b1505623e2b8a423eeabc2586bb7189e4a6 |  |
| 2026-11-24T08:33:56.596377+00:00 | retry |  |  | test:item_checklist:original |  | e662130c0a42cbf6bc731907986f37986f232a9c941dd201f73a0da1a3b157b9 |  |
| 2026-11-24T08:34:05.508699+00:00 | retry |  |  | test:free_form:original |  | 79039d3c187040a652d7f4fd6d2c4dbb78133739d133f038f8f1315c7b9e8716 |  |
| 2026-11-24T08:34:07.296925+00:00 | retry |  |  | test:separate_scoring:original:A |  | 87a105bc257aeb9bf209789a38f740a5280bcbb2e282b0f6fc96c76522974852 |  |
| 2026-11-24T08:34:09.113714+00:00 | retry |  |  | test:exam_prompt:polished |  | 98b52c93322dd45673f76ca6cbcf6c62457c7bbb9ef30b7bfdd65eb5d9f9e2c6 |  |
| 2026-11-24T08:34:12.550776+00:00 | retry |  |  | test:item_checklist:original |  | 57f4e4a60650ea763f969a8112fdbeb96a872823d492f25560e426a1d3b86748 |  |
| 2026-11-24T08:34:12.570403+00:00 | retry |  |  | test:separate_scoring:original:A |  | 0789ebb86c7ff294bba8dc1a8de971fb41e22d5536826c069a73e2e98206268d |  |
| 2026-11-24T08:34:14.350054+00:00 | retry |  |  | test:separate_scoring:original:A |  | 345876f738a84a9086d6b447dca3bd13ee8e1750aa81b2aa63b61e0ab6a9e4e5 |  |
| 2026-11-24T08:34:18.391478+00:00 | retry |  |  | test:general_rubric:original |  | 8079b84f6e259361cba566a33508ca79f4e8431bb888810f5efcc0d924aed2bc |  |
| 2026-11-24T08:34:20.846313+00:00 | retry |  |  | test:free_form:original |  | db451dd95950c9ee557ae4fe8fa368688a9d9d398f16bf47d1857e0a3dee0907 |  |
| 2026-11-24T08:34:25.070118+00:00 | retry |  |  | test:item_checklist:original |  | f6a07fba459e60c0fd98b4eb8dbc07cf744ad92738fb6115db4fc2bf9d101cc8 |  |
| 2026-11-24T08:34:30.908355+00:00 | retry |  |  | test:general_rubric:original |  | dadab8fcdaf72ebe916b382b3e7fe8c1a1d0b86879f0ee6a80fce3dde4d9080b |  |
| 2026-11-24T08:34:33.200566+00:00 | retry |  |  | test:free_form:original |  | 5d463088f1b8231f3a5c76a59692eccc9aaebd3d9294603032f8b15f6bed796a |  |
| 2026-11-24T08:34:35.170141+00:00 | retry |  |  | test:item_checklist:original |  | d15f0299d3f3d17bb57df219d3376ced46cc37e10e9f079f0090c3d24e62e3fd |  |
| 2026-11-24T08:34:36.058772+00:00 | retry |  |  | test:separate_scoring:original:B |  | 1db26b6cfc4c890ab22a28aa26b9ae33447fc6205b1851bddf108c09a0520f3f |  |
| 2026-11-24T08:34:38.027336+00:00 | retry |  |  | test:separate_scoring:original:B |  | 27d31acd6dfd1430ec8e061daea7d6047d0425f72bbcfcc757314908d5c02460 |  |
| 2026-11-24T08:34:45.223272+00:00 | retry |  |  | test:own_requirements:original |  | cc6af31c3dfbf7007d5a006617d85e88f6379655c206b272ce0588a9faff3d0c |  |
| 2026-11-24T08:34:50.210783+00:00 | retry |  |  | test:separate_scoring:original:B |  | 1baf47006dc0a00a942d56c27bb37c73b1005948f275f1d373f15241747d95d4 |  |
| 2026-11-24T08:34:51.591268+00:00 | retry |  |  | test:item_checklist:original |  | 6ab629c95f741016be713026a1c8e36139888f22659619fa66eac9b63960ee46 |  |
| 2026-11-24T08:34:52.047768+00:00 | retry |  |  | test:separate_scoring:original:B |  | 048c035b52ef790d4e029d254244dffac7680936292559452fa71332c2451064 |  |
| 2026-11-24T08:34:53.944401+00:00 | retry |  |  | test:own_requirements:original |  | a001d60306eb15b414d23e648e4b3cbdca7d34853f3cfa2c22be5288a62d8153 |  |
| 2026-11-24T08:34:55.244353+00:00 | retry |  |  | test:free_form:original |  | 5cf34f090f49bc9c5af85b2a10a33a2b29c83ac06795a540d61e524a97f7bd9f |  |
| 2026-11-24T08:34:56.021253+00:00 | retry |  |  | test:free_form:original |  | 0eb01c415c351bf813d04d73756049e4a8cb85f948c36f54ed1f749887f2c6e1 |  |
| 2026-11-24T08:34:57.871568+00:00 | retry |  |  | test:item_checklist:original |  | 97a76ae4f9a82359a17d419df001974a19b23b3094e796d806d7de98972e980e |  |
| 2026-11-24T08:35:00.056721+00:00 | retry |  |  | test:separate_scoring:original:A |  | 2df4e4a445c69693e806d55348c9cc66459caf4bc3a350b8c991df3aee22d37a |  |
| 2026-11-24T08:35:03.803097+00:00 | retry |  |  | test:free_form:original |  | 1ec2f280a114d8da878f2d4729803ebfa64fab4cdae8f91f2e4b88aebeeb631d |  |
| 2026-11-24T08:35:04.042505+00:00 | retry |  |  | test:free_form:original |  | 4c5db3667b98ad04c01da46855a20610ee30b909b56906e7ddc2128ef99cb193 |  |
| 2026-11-24T08:35:06.548061+00:00 | retry |  |  | test:free_form:original |  | 920bb485b3ee12235f076342dd91ee6673f87e1ffb8c5a8c0f137eafdbb677ea |  |
| 2026-11-24T08:35:08.668116+00:00 | retry |  |  | test:separate_scoring:original:A |  | 5d9e01e85072f1196dd36ae2746f9b1648928aa741ebd078c65cd686db506631 |  |
| 2026-11-24T08:35:12.739976+00:00 | retry |  |  | test:item_checklist:original |  | 560402ce31a91bc6420738b32e6d78ae74216dce5322f5bf851ea521bb5c17ec |  |
| 2026-11-24T08:35:13.063681+00:00 | retry |  |  | test:free_form:original |  | b69161f5a709b3e73d0e1ce04f9d052f62f15154fba624d0c25b1f0adfaeb2a0 |  |
| 2026-11-24T08:35:19.320660+00:00 | retry |  |  | test:separate_scoring:original:B |  | ab6b325c2a0ae84199a518512e408f440d3225a4c630299e022d7d56cfa651cf |  |
| 2026-11-24T08:35:21.773074+00:00 | retry |  |  | test:item_checklist:original |  | b727e8be74e66fc53672687a1a2ce4f5d518b9ab9c1184b520611e6e7907c37e |  |
| 2026-11-24T08:35:30.138147+00:00 | retry |  |  | test:own_requirements:original |  | d25c7aa1bda3bf76b7cedf4f93024bf28fb610e5d8a032962d0beb9d456a0530 |  |
| 2026-11-24T08:35:30.556054+00:00 | retry |  |  | test:separate_scoring:original:B |  | 1763bac52351a74f7af84c5c24ba27748306eb61004ea759a5674543dacdea06 |  |
| 2026-11-24T08:35:30.639095+00:00 | retry |  |  | test:item_checklist:original |  | fbee04e0ac096812f0e2d4e1fc2ca724bdf01668836de9d64be9e3efc18e59e4 |  |
| 2026-11-24T08:35:34.701486+00:00 | retry |  |  | test:free_form:original |  | 72b59b1a140eceee18e5b5902e2896b746995212b7ba17cffdb09fb76fe943b8 |  |
| 2026-11-24T08:35:37.067621+00:00 | retry |  |  | test:item_checklist:original |  | 8e6990a520bb9d9eb209e48d6b10ff21022eb8a9fca289123a439d4600c1c5f1 |  |
| 2026-11-24T08:35:40.900935+00:00 | retry |  |  | test:item_checklist:original |  | d7f0f1053e7f40aa15f0c35b8135a998c416a7047cfbd6282d8bdfd339d3d6cb |  |
| 2026-11-24T08:35:41.193089+00:00 | retry |  |  | test:free_form:original |  | 96d108b0f5437ecdd3fd99cff6ef20477eabbc8a16fd112ec6dd233328f305ed |  |
| 2026-11-24T08:35:48.438667+00:00 | retry |  |  | test:item_checklist:original |  | 04cfde6009e9001a103da8268cd97a57db177fa07b3c4b58d79232a875b9b3d3 |  |
| 2026-11-24T08:35:49.017748+00:00 | retry |  |  | test:separate_scoring:original:A |  | 5ccb0e79522ce91905e9bba9e88bfd426b8518ddeca73b8799b5c157f7abae45 |  |
| 2026-11-24T08:35:52.877279+00:00 | retry |  |  | test:item_checklist:polished |  | efc40fd987261f99a29ade4f98fddcb938e27b697c03456c85d4b2da5e23d632 |  |
| 2026-11-24T08:35:53.656393+00:00 | retry |  |  | test:separate_scoring:original:A |  | 7781dbbc9e34a7b3d3030bfdad4b69996f45d861bf30bf84a1945a82374987e3 |  |
| 2026-11-24T08:35:59.129632+00:00 | retry |  |  | test:separate_scoring:original:A |  | 9bb288034d269f7f8a29e19f55d9a50aa0c125b878fa31db0421dc25817b6c94 |  |
| 2026-11-24T08:36:01.337956+00:00 | retry |  |  | test:separate_scoring:original:A |  | d3fdc7064842a35e1eaca3cf98a93a93e4440c9116266e1d1ad100530063b8a5 |  |
| 2026-11-24T08:36:04.271091+00:00 | retry |  |  | test:item_checklist:polished |  | 2e641f822b6c4882ad2a1e1482131d5deeb818f40233051471a7d0894f068824 |  |
| 2026-11-24T08:36:06.202917+00:00 | retry |  |  | test:own_requirements:original |  | 4a0a015ce1c1d1b924d554b68a924c9f06caa4c8a0996578d5cc1781f95a7e9c |  |
| 2026-11-24T08:36:06.957766+00:00 | retry |  |  | test:separate_scoring:original:A |  | 8d6d3fc6d65fc7082f6725c448d2aeafb4f45aae434e7db840366b50c9bc28ec |  |
| 2026-11-24T08:36:07.702680+00:00 | retry |  |  | test:separate_scoring:original:A |  | bc7ef89d1b0176a5ccffa68e81f4fd070c45168f6be15238ec46da2fb10a96d1 |  |
| 2026-11-24T08:36:11.990922+00:00 | retry |  |  | test:separate_scoring:original:B |  | d9a64be59b8f358055e99b4198fd9415816f73802d040b6c7a362993e6e49c12 |  |
| 2026-11-24T08:36:19.496133+00:00 | retry |  |  | test:separate_scoring:original:A |  | 785cf158ad9762a10ede29c74b1edc635111788a6129c8365e9a8c538df7f98e |  |
| 2026-11-24T08:36:20.317583+00:00 | retry |  |  | test:separate_scoring:original:B |  | c5b48a8aa051058fd54e58e11c73f1a7378e2e05614408b8c0a9d1e49fa57ff1 |  |
| 2026-11-24T08:36:25.759554+00:00 | retry |  |  | test:separate_scoring:original:A |  | 8e82278b5734875c8b0b7b66d2b32ae758ab0c092627c285fd5b374756dbba0d |  |
| 2026-11-24T08:36:25.893352+00:00 | retry |  |  | test:item_checklist:original |  | 563a7e616303b45ca265051925852db1c119ffb5f6f01a9a787715ad525f30fe |  |
| 2026-11-24T08:36:27.862849+00:00 | retry |  |  | test:separate_scoring:original:B |  | 68f0c6700574a6a419ae1e30817f0393e893c0355991e92c632487c2f62c2ae5 |  |
| 2026-11-24T08:36:34.274006+00:00 | retry |  |  | test:separate_scoring:original:B |  | 3d0448e2baf5c302af295a3dd2a746dcb5c06cfa7e8f57d0de77d7574bac434a |  |
| 2026-11-24T08:36:36.942523+00:00 | retry |  |  | test:exam_prompt:polished |  | 6cf8feaaa12d55181df3e9f10e2ee7b2084e846fd4e4f1414a60dbc3db97e957 |  |
| 2026-11-24T08:36:38.919119+00:00 | retry |  |  | test:separate_scoring:original:B |  | e0f0f2b2fd5fa549be68e8dc29b3657c9041d94da2e6bdf64e82a25aa3d7505a |  |
| 2026-11-24T08:36:41.026470+00:00 | retry |  |  | test:item_checklist:original |  | ffb24e7de2c89cb0ffe35ee94fa4c00f826ed55f7e566b9f6d779c07ece6dc90 |  |
| 2026-11-24T08:36:43.103093+00:00 | retry |  |  | test:separate_scoring:original:B |  | 8ef1f09c0999d4076d196791e5d1d91ae7835e27c6f0f49f7032e0940d7ebdc7 |  |
| 2026-11-24T08:36:45.177296+00:00 | retry |  |  | test:exam_prompt:polished |  | a8c72fe4b79dd92e0653330f5b12c80b5347e9793a9888f3a08ff03ccd507d1f |  |
| 2026-11-24T08:36:50.928195+00:00 | retry |  |  | test:own_requirements:original |  | 87246361e0886bca60b3ffbba37c7765bb40245d54a961a3901eea5802124d6c |  |
| 2026-11-24T08:36:52.750590+00:00 | retry |  |  | test:general_rubric:original |  | 7d968507c295c1eaad27d68dae29b383be6a840bee4d0deb6953bf2a0bf25f5a |  |
| 2026-11-24T08:36:52.758057+00:00 | retry |  |  | test:general_rubric:original |  | e2fb1e0b659a2e3993c5f0fa7e09663f04fb715825e2cb0bf67ee52150f2d5fd |  |
| 2026-11-24T08:36:55.020064+00:00 | retry |  |  | test:general_rubric:original |  | 8d611f422699f67bffe019344a60ec7e9af5faff8a62053426e0de8534c9bdfb |  |
| 2026-11-24T08:36:57.119955+00:00 | retry |  |  | test:own_requirements:original |  | f6c6404443e422112b447a28aedcc716251b842da4c876386df30d5edd5eab5e |  |
| 2026-11-24T08:37:00.787374+00:00 | retry |  |  | test:general_rubric:original |  | af6f24f23438de3e0bedd144bc871a67dd4f82d5050a8836398c206db230cc7a |  |
| 2026-11-24T08:37:03.086663+00:00 | retry |  |  | test:general_rubric:original |  | 11f6f6326d57312d1244a8a2e72dc9a4b6a20914701106af738ddd3975fca505 |  |
| 2026-11-24T08:37:05.077944+00:00 | retry |  |  | test:general_rubric:original |  | cb2221e033e0b5dcc990af6f07e9f2ef5f57cd4d1383422740fc4aa03e2c23ae |  |
| 2026-11-24T08:37:07.033975+00:00 | retry |  |  | test:item_checklist:original |  | 74c3f4a80d114e9d6a706b6ec79221c19abc93f4a7384899c0b7e6184ff12e64 |  |
| 2026-11-24T08:37:21.609176+00:00 | retry |  |  | test:item_checklist:original |  | 7a93714e4d90c4830fbd6df8f52328f2db3b0d1d5a5491508521869c5b1348f7 |  |
| 2026-11-24T08:37:23.065601+00:00 | retry |  |  | test:item_checklist:original |  | 5cbf69fa74fc2217c0fd53985245a1bfa006578f04f32b92882591cd535963bf |  |
| 2026-11-24T08:37:28.282286+00:00 | retry |  |  | test:item_checklist:original |  | 81f7a29ae49de3a8afb10fe52d26088f5d1dc4160d5b1773e0dbfb954b356d4d |  |
| 2026-11-24T08:37:32.050936+00:00 | retry |  |  | test:exam_prompt:polished |  | 439387210758ad875597b6dcb3bc83b0dd92cdfcec094d7436552d6f300d7e42 |  |
| 2026-11-24T08:37:35.625834+00:00 | retry |  |  | test:item_checklist:polished |  | 93abab25aaf02887a9178f15db4f4768b3cc5228522ef4270bcf19b70b75feb1 |  |
| 2026-11-24T08:37:38.983190+00:00 | retry |  |  | test:exam_prompt:polished |  | 1566ce56f033717d59edd16fd45c29254528968ecfecaf9a888e96d71d6a33a6 |  |
| 2026-11-24T08:37:39.216562+00:00 | retry |  |  | test:item_checklist:polished |  | f37b563e140e2b1209010b621b8afea2e0285d9a255e46f311bdf1bc3e0b39bd |  |
| 2026-11-24T08:38:42.637020+00:00 | retry |  |  | test:general_rubric:original |  | 5c9c9bcef8b7e96ccb3484df2617be68fc627b4a2dc567ae8e33bd32e7e4d7a0 |  |
| 2026-11-24T08:38:44.609320+00:00 | retry |  |  | test:item_checklist:original |  | aaae33c86719bda18c82b2e15830e58052b6dbe75803ce9fc822502850d06869 |  |
| 2026-11-24T08:38:52.667176+00:00 | retry |  |  | test:free_form:original |  | b6ca99966601276aa6d2abf792102d24a6ccd7695a5b33947d4fcb550cfbd060 |  |
| 2026-11-24T08:38:54.469680+00:00 | retry |  |  | test:exam_prompt:polished |  | f992f456aaf610c639e3ef5eb6a21e160f7751090a6fe376dcfe65b5e56d6bd2 |  |
| 2026-11-24T08:38:57.613353+00:00 | retry |  |  | test:general_rubric:original |  | f45ace74e71fbc2f1c4e34c1289e22dc5dc5d6c8068b50be23ba0e36d8213c28 |  |
| 2026-11-24T08:38:59.816442+00:00 | retry |  |  | test:item_checklist:original |  | a4bf20f3620680b8121dfaa2acfcf8825e2416414c2809cec88a36eaab6b7e85 |  |
| 2026-11-24T08:39:01.610956+00:00 | retry |  |  | test:exam_prompt:polished |  | 14c3991aeeab6b10902da18ee6a3faefedfca85c11a046ab8804d9cb5fd28528 |  |
| 2026-11-24T08:39:03.643720+00:00 | retry |  |  | test:free_form:original |  | 5f5a2b6c99aedb9979a51aeab7c5d7f68864cdc419114ddc1213a8a48e25e8f4 |  |
| 2026-11-24T08:39:04.250158+00:00 | retry |  |  | test:exam_prompt:polished |  | 4aff101f83bbbeb8d1f42e41f6090c20d795f286e111e839a300fce3baa29680 |  |
| 2026-11-24T08:39:08.421605+00:00 | retry |  |  | test:exam_prompt:polished |  | f404b1e241ee395cbc4e0f4115da3036dbe316264fe0b34cea3836841dea65e2 |  |
| 2026-11-24T08:39:18.302979+00:00 | retry |  |  | test:separate_scoring:original:A |  | 1f219f1cf2582a1d271d1a4c6cbbfcb2ee1faeefb57ac1b78567f2cdf65084d1 |  |
| 2026-11-24T08:39:20.381242+00:00 | retry |  |  | test:item_checklist:polished |  | 2f89e981136d61e545f492404f9eface12700a3cc15a7ef58ef8dcdbe7aedc44 |  |
| 2026-11-24T08:39:21.888791+00:00 | retry |  |  | test:item_checklist:original |  | 64007b19b2d5c8212c173ba1e4d0efb567953fdc6fa03c2a8ca3be3c88cd1887 |  |
| 2026-11-24T08:39:26.146224+00:00 | retry |  |  | test:item_checklist:original |  | 6dc0b531614131a42a9bc7da49e3c7e9c31dfa8bc0e660ebe52a61170ed13f51 |  |
| 2026-11-24T08:39:28.040977+00:00 | retry |  |  | test:separate_scoring:original:A |  | 77de6a10480ac0759e18ca1340f44eb5ffca3d32427ef585ccf448b5bc4f1ad9 |  |
| 2026-11-24T08:39:29.925433+00:00 | retry |  |  | test:item_checklist:polished |  | a67444b99a97f40012f65c17a099084f6f8be0ad760c9ae763b69bca1df7ae00 |  |
| 2026-11-24T08:39:32.275212+00:00 | retry |  |  | test:separate_scoring:original:A |  | 0eaae3396f4fc81f7f408e767718b30c94513036c8a9f3af25241983b70694b9 |  |
| 2026-11-24T08:39:34.413719+00:00 | retry |  |  | test:free_form:polished |  | 9e192cbc396a59b15baef8a9003fc65c3cedf322e35af85da4809ec27de93df3 |  |
| 2026-11-24T08:39:36.541549+00:00 | retry |  |  | test:item_checklist:original |  | 2c7db2f37900f9d55fb1092da7ee22341b8a7bdaf49e4b6de98185d48eeb3c6a |  |
| 2026-11-24T08:39:40.151224+00:00 | retry |  |  | test:separate_scoring:original:A |  | 8edadb4f9917f95008e5217bd6abf1647827d982c08c88531c5980db8893a185 |  |
| 2026-11-24T08:39:43.406593+00:00 | retry |  |  | test:general_rubric:original |  | ce6248c52ed235a7723bf80d1c61f1ed7acd90326609d222fab174aeff96af2c |  |
| 2026-11-24T08:39:46.716328+00:00 | retry |  |  | test:free_form:polished |  | 708f5900ddabf9d44a08b3f299e000c02d9431a755230d9315496ae282a8d738 |  |
| 2026-11-24T08:39:51.181687+00:00 | retry |  |  | test:free_form:polished |  | fc9525fab79de0000b8004dbba17abc294d5d7feebd9d884ec23a10f76780cce |  |
| 2026-11-24T08:39:55.239059+00:00 | retry |  |  | test:general_rubric:original |  | a757f389f0e7eafd15c93aaa5dfd34e3589c6ce2689fcfda038e2ae04f3538a5 |  |
| 2026-11-24T08:39:55.731951+00:00 | retry |  |  | test:separate_scoring:original:B |  | f31fc0671fa966ed6d8e2de6c147e499d1d8e3f971ed0954e442b22ee6277bd7 |  |
| 2026-11-24T08:39:57.175265+00:00 | retry |  |  | test:separate_scoring:original:B |  | 3bd15b8d8b980a42a4d7cc25dd0ef8aa5cb0481729a8b0f8464f28d1dd1eee0d |  |
| 2026-11-24T08:39:59.208780+00:00 | retry |  |  | test:item_checklist:original |  | d98590f45e68c0d7f43db34958c158da15a366153f58a5ce6cca712fde85cc0d |  |
| 2026-11-24T08:40:01.389374+00:00 | retry |  |  | test:free_form:polished |  | 2769351e23ae2c1d3af341c2d266e11ef0c53e5d1d0674a4beb8baee911dc3c6 |  |
| 2026-11-24T08:40:03.551080+00:00 | retry |  |  | test:general_rubric:original |  | 04ec0e0cd192a1216338c803c42b4604cb13509d64d9ba73c838523101a8b922 |  |
| 2026-11-24T08:40:03.783891+00:00 | retry |  |  | test:free_form:original |  | 1ef6f61a1b212789a4e5ce16d7a9b1979a4541cb52c7cf903700f038bb01d0cd |  |
| 2026-11-24T08:40:05.655465+00:00 | retry |  |  | test:separate_scoring:original:B |  | 769e78948a5bcd687edad3dbf9bc834e4a599cfd528402a03de12ba356134851 |  |
| 2026-11-24T08:40:07.713111+00:00 | retry |  |  | test:separate_scoring:original:B |  | 976a870cf1778d31aec5c1b1e6d0dddabf2a5af7dddb3d1e522652e2995b7189 |  |
| 2026-11-24T08:40:07.732883+00:00 | retry |  |  | test:item_checklist:polished |  | 0275da753e5290f807c732ead9a85f733eb751a67218b9382b36a4989caf5b17 |  |
| 2026-11-24T08:40:09.681457+00:00 | retry |  |  | test:item_checklist:original |  | db2dbcbee32303b30cd24e4403724ac86884a7e621df2fc0754d01f512f17c88 |  |
| 2026-11-24T08:40:09.916048+00:00 | retry |  |  | test:general_rubric:original |  | 82c707ccea4fc676640f868c52f1bb391a5b81f89e8a1430d1dc23adf982f8f1 |  |
| 2026-11-24T08:40:11.608849+00:00 | retry |  |  | test:free_form:original |  | c9f85b4ffcc29cf7edfddf57205119c66f4a62461059004c2957e2d35c7f66ad |  |
| 2026-11-24T08:40:13.448433+00:00 | retry |  |  | test:item_checklist:polished |  | b76c7853da6e2d20d7f1c27ada5e1260aed6824ea9335a589733d084e907cab0 |  |
| 2026-11-24T08:40:13.694436+00:00 | retry |  |  | test:item_checklist:polished |  | f71f18c07c55debde628591359a0eded9291a17ba2b4081589d24a8066d6387d |  |
| 2026-11-24T08:40:22.563459+00:00 | retry |  |  | test:general_rubric:original |  | e2458d224981b775a0140a0a6ac7a1e0c4d4909eec260bf875e1b81ed196f19a |  |
| 2026-11-24T08:40:22.940631+00:00 | retry |  |  | test:separate_scoring:original:A |  | bf1daaac6601cd29614ff7883db3682fd8a560ee375d94ac970781df1562a356 |  |
| 2026-11-24T08:40:27.317456+00:00 | retry |  |  | test:item_checklist:polished |  | 5d0978ab8a8ddd05adb482188589aac37217ad33d9fb3f41ef13730009d44dd4 |  |
| 2026-11-24T08:40:31.503495+00:00 | retry |  |  | test:general_rubric:original |  | c2ff72b9d917fa105e27d7b185c2038fb7f2bc728a3e6345287e120e0e7f21fc |  |
| 2026-11-24T08:40:32.834178+00:00 | retry |  |  | test:separate_scoring:original:A |  | eb9c4afc307d7bac34fe8bdd454a7055ef27d795bfb8b1dfec4a7085a23ecd7e |  |
| 2026-11-24T08:40:33.728049+00:00 | retry |  |  | test:free_form:original |  | c2977082a06c0e682acd84789539bebd439d5dff9b623a4162de82cb08038490 |  |
| 2026-11-24T08:40:43.683947+00:00 | retry |  |  | test:general_rubric:original |  | 05db7b9d614c6196b93edfd0d628ed111ac8de6aae84a65d43444e2dee3050d8 |  |
| 2026-11-24T08:40:46.179196+00:00 | retry |  |  | test:free_form:original |  | 61943e421eaedab5d71e4c9826ea359228e40a98447bba44b838eed187c0dca7 |  |
| 2026-11-24T08:40:49.197794+00:00 | retry |  |  | test:separate_scoring:original:A |  | eed012e2c12b72e0517252a894c9f322927118e83896031157a6043f6a006301 |  |
| 2026-11-24T08:40:51.462013+00:00 | retry |  |  | test:separate_scoring:original:A |  | d06f314a215ae1a123c69b13c464ddb63785fa79fbba47345fa84bf954669370 |  |
| 2026-11-24T08:40:52.419918+00:00 | retry |  |  | test:general_rubric:original |  | c5887dd140d1eec91bcfe0951670042b8b6f18285d5e706882b1e43d7652a42e |  |
| 2026-11-24T08:41:01.556253+00:00 | retry |  |  | test:free_form:polished |  | 04dfb67b897fc465b34bfabd1cea3c514890c2f2a597258a313eb38035348cab |  |
| 2026-11-24T08:41:03.350327+00:00 | retry |  |  | test:separate_scoring:original:A |  | 04d4a242018d6fd9b9854726223b7b87946d6cc97f738947d5a4547a3dc3a6f7 |  |
| 2026-11-24T08:41:07.861267+00:00 | retry |  |  | test:separate_scoring:original:B |  | 1d0d46484f7d9e2238d89408fb41b39066a25b1c802fa35dd3f20e8c055608f8 |  |
| 2026-11-24T08:41:08.224977+00:00 | retry |  |  | test:item_checklist:original |  | b08c3ce401f3934a505994e370ffe962f1282a783836059c4480ed037080a900 |  |
| 2026-11-24T08:41:10.089222+00:00 | retry |  |  | test:free_form:polished |  | e64ffe918ed62cca69e99e4a4696f548ea10bedead7db128039ce3b430035d3f |  |
| 2026-11-24T08:41:11.243764+00:00 | retry |  |  | test:separate_scoring:original:B |  | 80dbf78e23b2b01f716b32d8975ed08dde912896d5b7e4e86591273e7ff93f44 |  |
| 2026-11-24T08:41:12.222840+00:00 | retry |  |  | test:separate_scoring:original:A |  | 3f9d1a97bfcd6ea417c1a592fa00be101a82e7343efb088b9bcd1e2610af0abf |  |
| 2026-11-24T08:41:14.172637+00:00 | retry |  |  | test:separate_scoring:original:B |  | 192c7e5ece0db3613e86e77c3a9312c038194fa210cd06a925bdc4ec8ef27eb7 |  |
| 2026-11-24T08:41:15.806102+00:00 | retry |  |  | test:general_rubric:original |  | 7c5215edaa1802ee3f85ae98c9754db1dc056b7af7c680f70144851d95cc9f61 |  |
| 2026-11-24T08:41:16.009710+00:00 | retry |  |  | test:exam_prompt:polished |  | 56bfeaecfe4f59b19bfa60b8f79f56fde2fccf8b2127c6b4c0b0e0b59bded457 |  |
| 2026-11-24T08:41:17.871316+00:00 | retry |  |  | test:item_checklist:original |  | 1f454919777fe2e6a6300876386c52712a76093734da76f1547211e608ed89f2 |  |
| 2026-11-24T08:41:18.484651+00:00 | retry |  |  | test:separate_scoring:original:B |  | b51ceda00a2db4f07bcc83ed044e511bb404f492def3309032ef2d9146233df0 |  |
| 2026-11-24T08:41:22.410689+00:00 | retry |  |  | test:general_rubric:original |  | 18781eaa4e8ed8e2a87d0ef0e38cac8589dcc27288253927c1cce3c3abb154d7 |  |
| 2026-11-24T08:41:22.526449+00:00 | retry |  |  | test:separate_scoring:original:B |  | 2bdc7b7731664796e68eccb363709286e984d9f733173f40271ec4395f952a0a |  |
| 2026-11-24T08:41:26.577026+00:00 | retry |  |  | test:exam_prompt:polished |  | f6be9e63a4f5b9e40a652dc68e6d67d01e1c35ecb9573e409fa63a1680651e71 |  |
| 2026-11-24T08:41:52.811173+00:00 | retry |  |  | test:separate_scoring:original:A |  | 43c68cf97271d2b8e455f91b1fe9103d2f49e68a598833be337fe7dd112c3cdf |  |
| 2026-11-24T08:41:59.818454+00:00 | retry |  |  | test:separate_scoring:original:B |  | 59154b2f7987d4ef6f76f0c027255594bf8a1955c0c90de4afe3909f382b6d8d |  |
| 2026-11-24T08:42:12.353587+00:00 | retry |  |  | test:separate_scoring:original:A |  | 295ad90bc34c0f56d3d4556b35b7a2342dc5dee12e66a59b0937fba9e871c587 |  |
| 2026-11-24T08:42:14.784454+00:00 | retry |  |  | test:item_checklist:polished |  | dc28aed090ae086da4f400c922b56e364688481b8acc3149da8de6563e78cc6a |  |
| 2026-11-24T08:42:36.008316+00:00 | retry |  |  | test:separate_scoring:original:B |  | f55e0903176dfbb6bb965efa26a7b6961a834ecf392125dd02728bb9f190ada3 |  |
| 2026-11-24T08:42:37.844965+00:00 | retry |  |  | test:separate_scoring:original:A |  | bde9625d474c1743caeee3f61472e6a4d4a666a72d76a126d1f7a44e881d8b4c |  |
| 2026-11-24T08:42:39.878435+00:00 | retry |  |  | test:free_form:original |  | 82105d105c5f7befd0813e5025d16776a9a63d26930604646b710871081ff391 |  |
| 2026-11-24T08:42:48.843598+00:00 | retry |  |  | test:item_checklist:polished |  | 02c40375ce944f1c89b435c0fe2f0fcc59d50c143fa41b2b4dec31cd1b4a4fcd |  |
| 2026-11-24T08:42:50.300733+00:00 | retry |  |  | test:free_form:original |  | 70ee276ff4c051e94fe0ada9710099b0590f92417dc55a686af4d3d6523f9591 |  |
| 2026-11-24T08:42:55.147404+00:00 | retry |  |  | test:free_form:original |  | 7b4637cb5fb90140a1efe3a445cbd7d7f7f1100c780fdb64509c907b619ec026 |  |
| 2026-11-24T08:42:59.898008+00:00 | retry |  |  | test:separate_scoring:original:B |  | 8ed22b7e71640e89d588df40d2f28d6888deaf64fc84b4d45f16ca54dca653c5 |  |
| 2026-11-24T08:43:02.361648+00:00 | retry |  |  | test:free_form:original |  | 1f94b4dddc373e6bf1ff197e761b83206f187438a676feb1977113d94b894eed |  |
| 2026-11-24T08:43:03.989364+00:00 | retry |  |  | test:item_checklist:original |  | 5baecd171d166c828ee8facdcd9ee0ae6e6e6050911390addd6aeeee2a1a3b88 |  |
| 2026-11-24T08:43:04.644706+00:00 | retry |  |  | test:general_rubric:original |  | 47d431017d2ae6087a6d843ec467d00d09d4cfa32e6bcd1ec6921ab2fd701e6a |  |
| 2026-11-24T08:43:06.879935+00:00 | retry |  |  | test:separate_scoring:original:B |  | 28fccb7adc42a789fdf082c389c2988bc3f039faab250f44d7ef28713f388589 |  |
| 2026-11-24T08:43:08.264467+00:00 | retry |  |  | test:free_form:original |  | 17f46856ce8e5648e57c06df7e23d1a8e3d1a510c10427f78a6ea7f4e1ed30c7 |  |
| 2026-11-24T08:43:08.764054+00:00 | retry |  |  | test:separate_scoring:original:A |  | 323cb3ac8e4047df7160eae0e80bd60b0c7282466e40e15d20b34848caba962e |  |
| 2026-11-24T08:43:10.318087+00:00 | retry |  |  | test:item_checklist:original |  | 4b4e1fa46a3ab886739f82df789f23734aa4beafd29f83e841e99bec3f1a21fe |  |
| 2026-11-24T08:43:10.693847+00:00 | retry |  |  | test:general_rubric:original |  | de9fe96598602a011d43347adfa4dd43183471354a8eb0ba81d39a440440b226 |  |
| 2026-11-24T08:43:13.502779+00:00 | retry |  |  | test:free_form:original |  | 11d56c297f703d274ab1b5a7326982631faa271355136fb3d4d44a345b499db6 |  |
| 2026-11-24T08:43:13.879254+00:00 | retry |  |  | test:free_form:original |  | 2c40633786359f860818a2caad7ae0c613571638f5a27a95f85783cf10067d8d |  |
| 2026-11-24T08:43:14.477721+00:00 | retry |  |  | test:free_form:original |  | 249db814283b1c464b6d8763551303e298b9423e3bd25be8b5c75a8b9a57da9f |  |
| 2026-11-24T08:43:15.645246+00:00 | retry |  |  | test:separate_scoring:original:A |  | 6fe7426e260084b2176069119afc791a91ca34198e338672f0e63123ba7cb292 |  |
| 2026-11-24T08:43:18.824220+00:00 | retry |  |  | test:item_checklist:original |  | 9a212d72d80b8f5bdf634b613780cb376a2e23822f1ec6a4824180e5c420ce87 |  |
| 2026-11-24T08:43:20.912872+00:00 | retry |  |  | test:free_form:original |  | eee6999b9e2b012a361619a73df0c1de156dd6eab48b8abe95a5fd3366b7b262 |  |
| 2026-11-24T08:43:30.448149+00:00 | retry |  |  | test:general_rubric:original |  | 1c1fc948c0247721377d198db868ba159971de9743ddbf4077c2b36487ce6f05 |  |
| 2026-11-24T08:44:25.504955+00:00 | retry |  |  | test:free_form:original |  | 6a9f3494ccd7cf2beef5a6b14671062cda81a25fa04983e26c99517c4222245b |  |
| 2026-11-24T08:44:27.504820+00:00 | retry |  |  | test:general_rubric:original |  | 631ae85787cf6b895cd67c6be15a385cb757137fdbc0d0b9e96dbb5fb907fdb6 |  |
| 2026-11-24T08:44:29.890584+00:00 | retry |  |  | test:item_checklist:original |  | 5a028f6072bd96a81963ab65f3374648b29434cc9aed91ae95b229a14bd55def |  |
| 2026-11-24T08:44:34.278351+00:00 | retry |  |  | test:item_checklist:original |  | e1988d2eb97132dd5c72d9db955068e02e7db6a79dea9e2c6293ffd3f0da3a76 |  |
| 2026-11-24T08:44:36.121794+00:00 | retry |  |  | test:separate_scoring:original:B |  | 0679417f50729393dc879e57e18ae826a96fa0e73c3bb63fd7e4d600e6dbe209 |  |
| 2026-11-24T08:44:38.989616+00:00 | retry |  |  | test:free_form:original |  | b92a22022c204e3d5e56b2598241d28968a198549ae40ffe0d215f2bb6b8cd06 |  |
| 2026-11-24T08:44:43.352528+00:00 | retry |  |  | test:free_form:original |  | 9509ed776fac8a6529221a1d0f41efc92ac81610ed45fd1d7f298860daba0370 |  |
| 2026-11-24T08:44:45.442590+00:00 | retry |  |  | test:item_checklist:original |  | 5c2cecf963be128ab7e527f27b040824c93bffb9c08f095b8b3641f92d02818b |  |
| 2026-11-24T08:44:47.366266+00:00 | retry |  |  | test:separate_scoring:original:B |  | 988529f333fd095851d36e67274d31120ddcb61a9276375c8b5eebfc59477535 |  |
| 2026-11-24T08:44:53.960427+00:00 | retry |  |  | test:general_rubric:original |  | 02a3fac9c0c0fbafa0c99156ad5954a99e1733c5be18101c2f61cf09e6cc6283 |  |
| 2026-11-24T08:44:56.385523+00:00 | retry |  |  | test:free_form:original |  | 3b334e03c0e6a5a726ac4cee780744371c400dcf6f5ae80a55b96132b30a967e |  |
| 2026-11-24T08:45:00.504742+00:00 | retry |  |  | test:free_form:original |  | fd6b0f20c2f1d78101176bfc40d6b7083d2c550d33a147c07a258f2c4b783cdd |  |
| 2026-11-24T08:45:02.059793+00:00 | retry |  |  | test:general_rubric:original |  | 52d1df3a9978a2b41c01d6676cda4045efab649f9b00936e6d2b926031563bfe |  |
| 2026-11-24T08:45:06.600458+00:00 | retry |  |  | test:exam_prompt:polished |  | 5674e52076821f04969791cfffeea02c758596ac8aab625a3e4ec00a8799a2cd |  |
| 2026-11-24T08:45:07.903441+00:00 | retry |  |  | test:item_checklist:original |  | 24bfb649eb0322904918650a760b3fce3f822119c12c845267e8d7e28aa52f06 |  |
| 2026-11-24T08:45:08.637150+00:00 | retry |  |  | test:free_form:original |  | cb96217cfccf75d960798bbec628cb8142e0e6a628453072251c10d150131d52 |  |
| 2026-11-24T08:45:12.581295+00:00 | retry |  |  | test:general_rubric:original |  | 0c59391db560b0b8f7f0497d3fb021249d7f1d7830feaff0325373a2cda5d9d2 |  |
| 2026-11-24T08:45:13.017292+00:00 | retry |  |  | test:exam_prompt:polished |  | c6edabd32e5ad8aa29a3e89d846c42d307815c28ef5905fbd57b816ef8b65201 |  |
| 2026-11-24T08:45:28.939527+00:00 | retry |  |  | test:general_rubric:original |  | 891ac1d58ad25815639e580537e313bba6be6ac65d5368604396baeece2cf2bf |  |
| 2026-11-24T08:45:41.688365+00:00 | retry |  |  | test:separate_scoring:original:A |  | 01fd73a161efb981675fa3a3c4b1645a8792539071c6764e35f0e32a7c39f971 |  |
| 2026-11-24T08:46:38.280112+00:00 | retry |  |  | test:free_form:original |  | 10fddbd02530500fdbcaae120851b1acd1640c624d3a773db99c4f2218440242 |  |
| 2026-11-24T08:46:44.616959+00:00 | retry |  |  | test:free_form:original |  | a264ef37c47db1efdac601f60e96306a7757a37cc86d31c579d1392b69d221f8 |  |
| 2026-11-24T08:46:54.487097+00:00 | retry |  |  | test:free_form:original |  | 8bd2ef3c9b33ff760f541c3bab5cc2cd6819083b7caa512118fcd6dbef19fbc8 |  |
| 2026-11-24T08:46:54.755921+00:00 | retry |  |  | test:separate_scoring:original:A |  | 698a35a75d51fb49412d950b89e7b80a8b3fdb94070f565c877f8dd96fcc85d2 |  |
| 2026-11-24T08:46:56.744175+00:00 | retry |  |  | test:item_checklist:polished |  | 8f36a5cc0d1c0680ce7b3de0e3e30f0ec7062a9a587a8833aa147f5491868cb4 |  |
| 2026-11-24T08:46:57.217213+00:00 | retry |  |  | test:general_rubric:original |  | e91448c618a40aabd59f854bd06c0dbf1c72f2cc504559878a2fcfa3fba69b3e |  |
| 2026-11-24T08:46:58.924171+00:00 | retry |  |  | test:free_form:original |  | d9d7def4e5e8ca8b174c743030f3fce159ee9d19cb6baf45c5db1241f010b3b5 |  |
| 2026-11-24T08:46:59.115754+00:00 | retry |  |  | test:free_form:original |  | b9eb67e4cf92f145b04c31a510a6210f3c039320465aa13d4d6ba45cbe9f3af1 |  |
| 2026-11-24T08:47:00.767256+00:00 | retry |  |  | test:free_form:original |  | 98be59819cb2a37d67da4464e1767c055d2f93219e306e5c19b15548cdfd489e |  |
| 2026-11-24T08:47:00.823216+00:00 | retry |  |  | test:exam_prompt:polished |  | d091339ad56bfec77aaa5968720342685388fd239e966399b8ff4abddf3871c7 |  |
| 2026-11-24T08:47:03.131751+00:00 | retry |  |  | test:separate_scoring:original:A |  | cc932a01a8586661215d9e5611f35733fab613c2742eeb2f273be42b3c2674e2 |  |
| 2026-11-24T08:47:03.357504+00:00 | retry |  |  | test:item_checklist:polished |  | be617df0d10f63e28e2874d3178232608f1182adb2ee1400d9d958042199cb1d |  |
| 2026-11-24T08:47:05.347290+00:00 | retry |  |  | test:general_rubric:original |  | d084d76eda513307e2b4c0fbda827b9e43a3aee1faeb137e0d2dae8fe1444f55 |  |
| 2026-11-24T08:47:05.877571+00:00 | retry |  |  | test:exam_prompt:polished |  | 53b633e994549002cbdd3728b40e5768845328aa941c18b2dfd828c6cd9a36c8 |  |
| 2026-11-24T08:47:16.863910+00:00 | retry |  |  | test:separate_scoring:original:B |  | e1f24a526144e9811acb23d567e96ed7bbde25610eb7190b4b37fd56b0ed7f06 |  |
| 2026-11-24T08:47:16.962934+00:00 | retry |  |  | test:free_form:original |  | 4169cf0e989676946f3ad49ad1a2aa8d1e52b1bc16cb0a454ca0399cbe911365 |  |
| 2026-11-24T08:47:23.069204+00:00 | retry |  |  | test:separate_scoring:original:A |  | b21aa15a5bd33cab66d4e3e3e019049a5ef27b9dc0c56b6637d5ca34bf6246d9 |  |
| 2026-11-24T08:47:25.197716+00:00 | retry |  |  | test:separate_scoring:original:B |  | 837df0567bc98d70e599629e27e24582ef557b40b9565ff15b9a97d83e382ffb |  |
| 2026-11-24T08:47:27.554916+00:00 | retry |  |  | test:free_form:original |  | 95ac80fda2c01a0da89a273dcfcb14046f37d0e36e6303b26b86a53dda73430b |  |
| 2026-11-24T08:47:29.215361+00:00 | retry |  |  | test:separate_scoring:original:A |  | a24f633d20e8109eabaef1a98255fb527debb6d35db7887adb6d65710fe57f47 |  |
| 2026-11-24T08:47:29.299051+00:00 | retry |  |  | test:own_requirements:original |  | 5a8f5feb6a15ae794d7f9c2e9e14adbfb36827c4bcc7aae2f710db1ef3933c3e |  |
| 2026-11-24T08:47:31.250775+00:00 | retry |  |  | test:separate_scoring:original:A |  | 804977f7390b569e1c0a82a53d0ffbae8ca709aaa928e5484ee4e39fdf90fb32 |  |
| 2026-11-24T08:47:33.277365+00:00 | retry |  |  | test:exam_prompt:polished |  | 0663257b353452186f4780b069c2d8af6b4f1f2a88ece34bea5a1a25dc92f00a |  |
| 2026-11-24T08:47:37.465983+00:00 | retry |  |  | test:own_requirements:original |  | 7b4332e4eb0e7a778a98e83aa838f13498cadf9ea06f582c224ed654922c9b4a |  |
| 2026-11-24T08:47:39.799782+00:00 | retry |  |  | test:separate_scoring:original:A |  | 0805e746e020419e5c02e429ecaf427e25f2c0be93c21a967aeeae2871816b61 |  |
| 2026-11-24T08:48:16.597512+00:00 | retry |  |  | test:separate_scoring:original:B |  | 36a297623fd802d640d8fc9af2a950894502d896ad6e775c78f9e1d5a5683458 |  |
| 2026-11-24T08:48:22.557482+00:00 | retry |  |  | test:item_checklist:original |  | 2061c5b2207c0a029f468042c8a791a5b89dfd2b53344da499ce9bae8e60e935 |  |
| 2026-11-24T08:48:26.836935+00:00 | retry |  |  | test:separate_scoring:original:B |  | 0b9520d2d46cd43d0e5093dee2bdf1349a025ce222b45913c9a3102a786ad71a |  |
| 2026-11-24T08:48:48.006948+00:00 | retry |  |  | test:item_checklist:original |  | 4f3c47862f1bd9ca1fe320fd164563e7324644e6e319f0c3f972ef4ba34f8189 |  |
| 2026-11-24T08:49:03.339617+00:00 | retry |  |  | test:general_rubric:original |  | 68faa8e9b9d51c22f44ab151a937f21b57044360929d1a55e41c7e5125dbda13 |  |
| 2026-11-24T08:49:06.819230+00:00 | retry |  |  | test:exam_prompt:polished |  | a2c3d2a66bc6a67bfa673fa4c2e388f3e5a1ca2aaff1cedcefcb758df43f6496 |  |
| 2026-11-24T08:49:07.126170+00:00 | retry |  |  | test:separate_scoring:original:A |  | f63bacdb39f5232ff222c1c8267b2e0dd35bdd46a598c9ecf83b5d7ab2542080 |  |
| 2026-11-24T08:49:09.083974+00:00 | retry |  |  | test:item_checklist:original |  | 8917197d70ef053c9fa436371dda95d97ffabbb8be969018df3444d3282906b7 |  |
| 2026-11-24T08:49:15.207228+00:00 | retry |  |  | test:general_rubric:original |  | e927668f27a6cf1847132ba1d2b216a3b3ef1fcd74723364772adc749f890fcc |  |
| 2026-11-24T08:49:17.072442+00:00 | retry |  |  | test:exam_prompt:polished |  | 17ac34c2b12a2ec3d691496f7ea92627cfec506f8c29e8a1d5b6c5840ddb23f3 |  |
| 2026-11-24T08:49:36.456163+00:00 | retry |  |  | test:exam_prompt:polished |  | 9f2004ffb5722025fd58e98e4b75fed38325fe9bcb93293bd03cc1af91c387c7 |  |
| 2026-11-24T08:49:38.829201+00:00 | retry |  |  | test:general_rubric:original |  | 51ed486b14585613694c7e36bf7e8d246fc9c6745757aa563a9df83ea3949b59 |  |
| 2026-11-24T08:49:41.138711+00:00 | retry |  |  | test:item_checklist:original |  | 803cf64bd3f5f49997a496bc38588d9be78bdfc77bec9d299484b040ecc5c753 |  |
| 2026-11-24T08:49:43.233156+00:00 | retry |  |  | test:general_rubric:original |  | bc2ac53c9cd96c530f01ebdefa7e30bb0b93e754f32a8aed6ce906fe80a4a11c |  |
| 2026-11-24T08:49:56.597886+00:00 | retry |  |  | test:item_checklist:original |  | e0fb2c21edcd17e575a83002296a22263d67702b2b2520d5b700d20c681c082f |  |
| 2026-11-24T08:49:58.447089+00:00 | retry |  |  | test:exam_prompt:polished |  | 6b7036cb20b3e9d7279d0b4fd338cf3b02b568cba5e8d593a905609acddbd327 |  |
| 2026-11-24T08:50:00.267857+00:00 | retry |  |  | test:general_rubric:original |  | 8d7f2b17828e0c6c98b5234d96b9ba506747c3f4cef3bcbda8050b0998d84c10 |  |
| 2026-11-24T08:50:04.689473+00:00 | retry |  |  | test:general_rubric:original |  | 18f753f5faa327bb618598fe00526043c99cdc4ba0d2e2f747eac66c2fa2c8a9 |  |
| 2026-11-24T08:50:07.227882+00:00 | retry |  |  | test:general_rubric:original |  | 7a4c28604f104bc7b074a00a9a53dd5690957bfac68c53438712b9d3ff27ae12 |  |
| 2026-11-24T08:50:09.177334+00:00 | retry |  |  | test:item_checklist:original |  | cecd2f2f20a6b077a9eba5cba197d5fd78b545c9bc1152656da638c094574d6f |  |
| 2026-11-24T08:50:11.045810+00:00 | retry |  |  | test:general_rubric:original |  | e643c249953c0ff83de941c781c531acbda4ce14bbdf3640daa8f004c572fb87 |  |
| 2026-11-24T08:50:17.623429+00:00 | retry |  |  | test:general_rubric:original |  | f82aea5cbda1aa41946d927f01128b79af8babbae0b98d91ee4e71d6899d8b6e |  |
| 2026-11-24T08:50:17.684863+00:00 | retry |  |  | test:free_form:original |  | 3ef0fe6e981b1931288ee067f20f5086b6ea1bd77fe37af4a0d3956b48af5caf |  |
| 2026-11-24T08:50:41.674153+00:00 | retry |  |  | test:item_checklist:original |  | dfed5345c8f234df1cbb393be1cacccba3ac5efda82ad2d3ddc5341ff1eba4b3 |  |
| 2026-11-24T08:50:56.926844+00:00 | retry |  |  | test:free_form:original |  | bd5786fdef76f1b6222a980a28c2794e24263598ef5cd4a6e61478afb7188cf1 |  |
| 2026-11-24T08:50:59.616956+00:00 | retry |  |  | test:general_rubric:original |  | 820ad378fb25cbed9131c1b093cd94433684d0c406f579dfd47b6b37ea00a237 |  |
| 2026-11-24T08:51:02.947832+00:00 | retry |  |  | test:free_form:original |  | 810b5f79703ba75ae18c6e02f760ad4d7793ee9eedcbbfd90338212e8b484c19 |  |
| 2026-11-24T08:51:04.639562+00:00 | retry |  |  | test:own_requirements:original |  | b9c62d2722d2fa4580fb62b685c1d5871e6a74395117cce6ee60365e4006eb24 |  |
| 2026-11-24T08:51:06.506278+00:00 | retry |  |  | test:general_rubric:original |  | 84afe7a91952676aa1db20516b40f96022b6896fae57d57eca74682f2d89a2e6 |  |
| 2026-11-24T08:51:08.241906+00:00 | retry |  |  | test:item_checklist:polished |  | 47c3c14e332f0b8ea5f7803da24460effcb2a65c8b3c599890d2d5a577325aa5 |  |
| 2026-11-24T08:51:10.172623+00:00 | retry |  |  | test:free_form:original |  | ca848c71dc47ae1c08d1d7badcb3f4af5d95c4cc96e4dbfde7b270fda0d92975 |  |
| 2026-11-24T08:51:15.801948+00:00 | retry |  |  | test:item_checklist:polished |  | 99e848eedd76adcaadf9a861221328df48cd822182294bd8173bd17bfdadfa03 |  |
| 2026-11-24T08:51:16.005527+00:00 | retry |  |  | test:item_checklist:original |  | e515eab936e5c6043c45ba4ef0af84aad1cd575e403b53f5e51359dd9bfa1543 |  |
| 2026-11-24T08:52:04.735924+00:00 | retry |  |  | test:own_requirements:original |  | b0c8a4f881f5e610456df3b1405fa45dc797a644f2eb974f6aa235007573f6d0 |  |
| 2026-11-24T08:53:01.773084+00:00 | retry |  |  | test:own_requirements:original |  | 4145a8db903eefb4657135e483c6efe312fdc3fe8056652e70c59f6b6d20fb92 |  |
| 2026-11-24T08:53:03.786443+00:00 | retry |  |  | test:general_rubric:original |  | 46915c62a27c5706aa59c5b1a6deadfeb591b13ca4d946239a54f52a62b04c23 |  |
| 2026-11-24T08:53:11.906602+00:00 | retry |  |  | test:general_rubric:original |  | 667950d8d10210624e1f560aed770c2f84544716f10c75b7674913a9f93b9ffc |  |
| 2026-11-24T08:53:14.100949+00:00 | retry |  |  | test:general_rubric:original |  | 67e22039cc2c3e09d90ee3d2f622fd618260eecb71c81c337a3b2ddba9bc366a |  |
| 2026-11-24T08:53:46.465504+00:00 | retry |  |  | test:general_rubric:original |  | a6807f744d0bb310c24ab8bfa6efb3786da3130ca486fbc59f0b5e60a1691dd3 |  |
| 2026-11-24T08:54:01.515652+00:00 | retry |  |  | test:item_checklist:original |  | d410b958893876de8cb0d3df76c1ab2685a36112b27011a44705a2800ff5e518 |  |
| 2026-11-24T08:54:04.250582+00:00 | retry |  |  | test:general_rubric:original |  | 0452b947845eef09209b258ecfd0a35e936c8d6b2ead11043a066a5d1913dc07 |  |
| 2026-11-24T08:54:06.663303+00:00 | retry |  |  | test:free_form:polished |  | 846f5314723855550d10a88791bdebe8e1ae39909dacc62e7e1019cf78b8556b |  |
| 2026-11-24T08:54:09.744140+00:00 | retry |  |  | test:item_checklist:original |  | 16106e4a4cc6c904afc9a5dd546851a053b76e58b641cc78faf2590da3713ec1 |  |
| 2026-11-24T08:54:11.733530+00:00 | retry |  |  | test:general_rubric:original |  | 379b70505758744795315b134ff43c13ae32418c5a13b963f4ffd208cdf93288 |  |
| 2026-11-24T08:54:14.524649+00:00 | retry |  |  | test:free_form:polished |  | 73346c49a3e84ed5dc1fc94b726a671bbca3315dde368f7ef8ee4436fa9d8cce |  |
| 2026-11-24T08:54:18.557937+00:00 | retry |  |  | test:separate_scoring:original:A |  | fdacba4e2c9b14a591c924e536d5624a655160757bcc1ad1afac8d02b8920f99 |  |
| 2026-11-24T08:54:32.679930+00:00 | retry |  |  | test:general_rubric:original |  | 39026b5029ee303b227f8213cba7598f4a72a4eaa00e0b001bed4c68d2735879 |  |
| 2026-11-24T08:54:55.204016+00:00 | retry |  |  | test:separate_scoring:original:A |  | 2965f86c694b76d86f710de0eb0fd829347cba45a1831ad1bba55501b8efea16 |  |
| 2026-11-24T08:55:05.572893+00:00 | retry |  |  | test:free_form:original |  | a06885c87d7689ee42ae192fd6a79559eac074ce889ebfe15e8c193f711571a9 |  |
| 2026-11-24T08:55:20.819452+00:00 | retry |  |  | test:item_checklist:polished |  | 4f39c8fbe986cdbf343ca341ba484f988b704e0eae29daebf640e9b22a7525c4 |  |
| 2026-11-24T08:56:04.780430+00:00 | retry |  |  | test:item_checklist:original |  | 7c2f9b371526939da0dcd80fa425280508bcaf80d85a67f52164c5b858f88a9b |  |
| 2026-11-24T08:56:06.852097+00:00 | retry |  |  | test:free_form:original |  | 2073ffa0e5c7ea9cbdda12df7fd44bf51f8ccab7703f752ba19f1995f6430392 |  |
| 2026-11-24T08:56:09.280796+00:00 | retry |  |  | test:free_form:original |  | f60c14d3badd1546be3b47cad6d0d794399b1c2d4b0dd5a7bd970aaaf41cf193 |  |
| 2026-11-24T08:56:15.102811+00:00 | retry |  |  | test:free_form:original |  | dad2780a4be7f86b0e52367ff4dfa049b093d9b6883e801f9f469d4a68b3bee7 |  |
| 2026-11-24T08:56:17.343910+00:00 | retry |  |  | test:item_checklist:original |  | 927c33449c8b0a9255d5af4b92158297a08a2e7d34f006b23b43247a4b32a4cc |  |
| 2026-11-24T08:57:32.042808+00:00 | retry |  |  | test:exam_prompt:polished |  | 60e1d15f01f7e1de735ba2ea7a6ec26fabf19abcf9c5d6415985ebb5acc97277 |  |
| 2026-11-24T08:57:57.050516+00:00 | retry |  |  | test:separate_scoring:original:A |  | 8f49ffa8277071e0d971a4cf629b4a955b2ced1785a758128be7e41da2be08f7 |  |
| 2026-11-24T08:57:59.016120+00:00 | retry |  |  | test:general_rubric:original |  | 61fd2ab74272ae47683e1ee0321587994f473b504c33b166e2ba15886cd93207 |  |
| 2026-11-24T08:58:00.843378+00:00 | retry |  |  | test:exam_prompt:polished |  | dbf4550b0d6005d1d76adec268c20fc683f939368f5f3046b11785f37da7b5b7 |  |
| 2026-11-24T08:58:01.031117+00:00 | retry |  |  | test:exam_prompt:polished |  | c6591970a4bcc3925fce9adcf56aacbba69e57eeb5358b1b1f23800fa511e769 |  |
| 2026-11-24T08:58:07.126056+00:00 | retry |  |  | test:general_rubric:original |  | 8c3649dc1810cbf7d11027b7a7b799e174aad70a454f302b0061647d7032172f |  |
| 2026-11-24T08:58:09.140231+00:00 | retry |  |  | test:exam_prompt:polished |  | 4f472be84a11e129ec67435182829ba76b07d7630269d46b26d867b16a45680a |  |
| 2026-11-24T08:58:10.652687+00:00 | retry |  |  | test:general_rubric:original |  | 58432ac4100eb7f522a8dc0a7ffbecf2deab8286faf4e6b595cf4efb04e5368a |  |
| 2026-11-24T08:58:11.537661+00:00 | retry |  |  | test:exam_prompt:polished |  | d6ab80af5a9699bef317093dd368a58f054927b029617a2f9143500818a4264c |  |
| 2026-11-24T08:58:12.086774+00:00 | retry |  |  | test:general_rubric:original |  | c00edd5bf92b06e1a42e5fb0b132efa7cdffdc61e26a52cd303cc3c31b5fafa2 |  |
| 2026-11-24T08:58:14.148893+00:00 | retry |  |  | test:separate_scoring:original:A |  | c7e27da28620891ce26c649822a1ddfbf06c35515d260936d76ce0d00b0dde89 |  |
| 2026-11-24T08:58:17.924069+00:00 | retry |  |  | test:general_rubric:original |  | 64d445ba77fac83c45dea6ec7341bacf61fd0650b9ff76a4a029201134166fd3 |  |
| 2026-11-24T08:58:20.206067+00:00 | retry |  |  | test:general_rubric:original |  | 113dbb4a2140a723e4af18b9a6f0649db6d61a9789c2955d049b1ccbdd410539 |  |
| 2026-11-24T08:58:24.134647+00:00 | retry |  |  | test:free_form:original |  | bc19ada178daa0da74af5e25e7db5602b61bf2b0a744d63237978701e4b7059d |  |
| 2026-11-24T08:58:26.735556+00:00 | retry |  |  | test:separate_scoring:original:B |  | 2d5da07be66061344c5fb410864b89eb214f10cdca84cbcf562ae019bdb15fe2 |  |
| 2026-11-24T08:58:26.846836+00:00 | retry |  |  | test:general_rubric:original |  | 1431b481dbfec94dfa9ce08acac47d7e5e7f4f3aacf9954bc954e8fcbf618579 |  |
| 2026-11-24T08:58:54.048962+00:00 | retry |  |  | test:free_form:polished |  | 1d02f9f899761d8eea657ec6913626ec5bacfd95ce1f48f2b54dc43463a8cc34 |  |
| 2026-11-24T08:59:24.557812+00:00 | retry |  |  | test:exam_prompt:polished |  | a96c9418ebe1a0c9ba3953c294bf586ccbfbb74570a0fe48746760cdaaedab9d |  |
| 2026-11-24T09:00:00.561115+00:00 | retry |  |  | test:free_form:polished |  | ed2f548532e7a23a414a41f0e6829a677945e0bc48af550f7626e49cda52bc7a |  |
| 2026-11-24T09:00:19.705106+00:00 | retry |  |  | test:exam_prompt:polished |  | 6831f590510537eb59aa73dba4fefac5ec4de3b4f3b675338cca7e6a6a4c53e7 |  |
| 2026-11-24T09:00:21.846165+00:00 | retry |  |  | test:item_checklist:original |  | 49f20e63bcb3678c39859589618e39fa19abd4b56830808c7dfe6deea6997050 |  |
| 2026-11-24T09:00:24.099343+00:00 | retry |  |  | test:general_rubric:original |  | 049e071d4d59c614215771414ee3102e2749d4e566c88af63a9a29ee072cdd61 |  |
| 2026-11-24T09:00:25.954905+00:00 | retry |  |  | test:item_checklist:polished |  | b8b225bec4698e47c1a19bcc4a7a0a7d11a8a6649d67eb6d44166132dbd36821 |  |
| 2026-11-24T09:00:27.846202+00:00 | retry |  |  | test:item_checklist:original |  | 613c854676f7dfbbf882a36f8b6cd07194842b410dedbbe5a7aed1b00405fb21 |  |
| 2026-11-24T09:01:10.822467+00:00 | retry |  |  | test:separate_scoring:original:A |  | e65e967b2f5aeb2a2f2e7dec20a8b977f5663aa68f2c060d5f0159538d22481d |  |
| 2026-11-24T09:01:13.167996+00:00 | retry |  |  | test:own_requirements:original |  | bf9ac0d473127af9ea984fccc42ab0cf9892145463c60408d744f265e14b51c6 |  |
| 2026-11-24T09:01:16.153331+00:00 | retry |  |  | test:separate_scoring:original:A |  | 9140aa998d555bc9e4b30b049d84bb7c27f18d8bb9e7e0be120894af875359ab |  |
| 2026-11-24T09:01:18.071372+00:00 | retry |  |  | test:separate_scoring:original:A |  | 6e1b3802e70d7dffd7e754cdcfa29e4481de90316b0823449e0d7c7876656bae |  |
| 2026-11-24T09:01:19.734574+00:00 | retry |  |  | test:separate_scoring:original:A |  | 302bb7bbeee04c5e8b7c3fa787a0ccff1ac9670ec84897a73fd913a10581a793 |  |
| 2026-11-24T09:01:20.046287+00:00 | retry |  |  | test:own_requirements:original |  | c124d0ada0e858b526812ec99c0da8531e8b772033e9d74a9948267ec1902566 |  |
| 2026-11-24T09:01:22.756876+00:00 | retry |  |  | test:item_checklist:original |  | 90f77e8da066862e11b20442ad92859852da476be4278e9ff802430abd565dcd |  |
| 2026-11-24T09:01:23.312368+00:00 | retry |  |  | test:separate_scoring:original:A |  | 4aa584b9e0f83f7e44be9dd5df24f2eeb27999636f295c038ab871cd1a500d17 |  |
| 2026-11-24T09:01:27.576435+00:00 | retry |  |  | test:separate_scoring:original:B |  | 4c22eb036a1ed4a204d0af1da538ff5e543c52e867a64c706987365cfceb23fb |  |
| 2026-11-24T09:01:29.417432+00:00 | retry |  |  | test:item_checklist:original |  | 5f0a9cba612769fb0561533f1d44c8e27355dfeee873df83a2ec1701973f4981 |  |
| 2026-11-24T09:02:08.484450+00:00 | retry |  |  | test:separate_scoring:original:B |  | dfdabd197445ef56443a78d2d7be8bf7844ae95e8a44674fc8e00acb14cda50c |  |
| 2026-11-24T09:04:34.093088+00:00 | retry |  |  | test:item_checklist:polished |  | d0d857641344a4e92fb121fa4bd93811c8afcaa8232891b227ad7b99e106bbac |  |
| 2026-11-24T09:04:36.238673+00:00 | retry |  |  | test:free_form:polished |  | c818874f821e227c66cc844472b03e2bcd55cef9419d20bc3a3adeb3c4f50815 |  |
| 2026-11-24T09:05:01.612388+00:00 | retry |  |  | test:general_rubric:original |  | d3e0ce563cca79de0bfaf21dca84e2dde9f4649c93147a5d184e623173c3b9be |  |
| 2026-11-24T09:06:08.950910+00:00 | retry |  |  | test:free_form:polished |  | a2d0b35ba57f5ba31ac55846f9ffbe41731ce183712af1185890967aedae3551 |  |
| 2026-11-24T09:06:10.928774+00:00 | retry |  |  | test:separate_scoring:original:A |  | e7160911df22f134d0fa325ff0602c7ed6c65a534869de1bc20ae7e1f37a7c0e |  |
| 2026-11-24T09:06:14.070516+00:00 | retry |  |  | test:general_rubric:original |  | 68b6e72a69aeb39fc4a75d166e93bec4214838390ec59e57878efef02e8252fd |  |
| 2026-11-24T09:06:15.417753+00:00 | retry |  |  | test:general_rubric:original |  | 71b7eb15f602b32ef4d055aaf05385e8371cd7df3b7c4c018060ace8b4abb559 |  |
| 2026-11-24T09:06:16.190550+00:00 | retry |  |  | test:free_form:original |  | 4bec5f77f72a30f1f9ad8c426a612ec0f9c61da6e4fa0152f97ff69304eb8a84 |  |
| 2026-11-24T09:06:17.429612+00:00 | retry |  |  | test:free_form:polished |  | 28e2fac940a2a1a84ac215ac43ce11a39b38f911b51b164db22b901bc974c7f0 |  |
| 2026-11-24T09:06:18.287280+00:00 | retry |  |  | test:item_checklist:original |  | 1b5931425848b0cb15e316bd40ee9a7666d5929b85e51eb668166c9ad4bd0375 |  |
| 2026-11-24T09:06:19.726526+00:00 | retry |  |  | test:general_rubric:original |  | 2eea561a23efa39dfa7a56557f65c0c3e9d0d653715872a03b8d17e132284f49 |  |
| 2026-11-24T09:06:20.360528+00:00 | retry |  |  | test:general_rubric:original |  | 1f5a6208a84725ff57a5815891d59a567eae7ae8bf99517924674badef4862a2 |  |
| 2026-11-24T09:06:21.729954+00:00 | retry |  |  | test:separate_scoring:original:A |  | 42b66f8541af506eea1ba866e3ee16efc0ffbe6a5b20bbcc52b90ad8034447f6 |  |
| 2026-11-24T09:06:23.546436+00:00 | retry |  |  | test:general_rubric:original |  | 8bf5e2ab99e8b24abcc9f4d42f015c3aab6db1e59115dd53250b59d74be76ecb |  |
| 2026-11-24T09:06:23.822268+00:00 | retry |  |  | test:free_form:original |  | 54676f858a797542fb11b09c8454cf932e661bdc309b7e4f063ea205f74e9e7d |  |
| 2026-11-24T09:06:25.547470+00:00 | retry |  |  | test:item_checklist:original |  | 02d752e9011414a710a422985491a43f79007562dca3b8f8fdd08c29e6da6468 |  |
| 2026-11-24T09:06:28.305059+00:00 | retry |  |  | test:own_requirements:original |  | b273cbe49384ed19e4c1ed7923becbbad589648cdcb212b474ad5828a9a722cb |  |
| 2026-11-24T09:06:30.848545+00:00 | retry |  |  | test:exam_prompt:polished |  | af1ebf602a2caa62b9a60a48a44a25de7b45694bf025af3641373a125f85c93a |  |
| 2026-11-24T09:06:32.283892+00:00 | retry |  |  | test:separate_scoring:original:B |  | 96cf89c89139949823aff0526e66875aa92b8138e4aaf4fb84cbeb9c659a8b9e |  |
| 2026-11-24T09:06:38.216241+00:00 | retry |  |  | test:own_requirements:original |  | f56107d02f8c5da5cec961e9a2e5c84a94a9389b59612a5d132538f4350cf2cb |  |
| 2026-11-24T09:10:00.131760+00:00 | retry |  |  | test:general_rubric:original |  | 4e086402f5d34c186f9d541a442ed93b996cf64ff237c53aa3d5d95c8596a4e1 |  |
| 2026-11-24T09:18:20.678828+00:00 | retry |  |  | test:separate_scoring:original:B |  | 5e98b78e012e1b5fb0972aae4ca89f43f877ebea6866ab8e0bda88a82b75456c |  |
| 2026-11-24T09:19:13.680409+00:00 | retry |  |  | test:separate_scoring:original:B |  | 1910de3f1fbd915b70b557b7fc31d641b632374433e154763eda2c86dce3d5ba |  |
| 2026-11-24T09:25:58.146475+00:00 | final_artifacts_verified |  |  |  |  |  |  |


## Spend and timing


```json
{
  "openrouter_actual_usd": 0.40290051,
  "openrouter_conservative_accounted_usd": 0.45891263,
  "new_cli_calls": 5875,
  "cli_estimated_list_usd": 31.168349940000002,
  "unpriced_cli_calls": 2934,
  "imported_baseline_calls": 720,
  "new_calls_this_execution": 0,
  "returned_attempts": 7866,
  "collection_span_seconds": 2131678.746492,
  "serial_call_seconds": 54167.40762279877,
  "execution_wall_seconds": 12.757777600025292,
  "prices": {
    "sol_input_per_million": 2,
    "sol_output_per_million": 10,
    "luna_input_per_million": 0.1,
    "luna_output_per_million": 0.5,
    "cached_input_multiplier": 0.05,
    "claude": "CLI returned total_cost_usd"
  },
  "billing_limit": "OpenRouter USD5 guard uses actual returned cost plus conservative pending/unpriced reservations. CLI estimates are list prices, not subscription billing."
}
```

| origin | model | backend | purpose | calls | openrouter_usd | cli_estimated_list_usd | seconds |
|---|---|---|---|---|---|---|---|
| notebook33 | gpt-6-luna | codex | test:judge:test-code-000:BA | 1 | 0.0 | 0.0012827000000000001 | 4.429713899997296 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-001:BA | 1 | 0.0 | 0.0012392 | 5.72456119999697 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-002:AB | 1 | 0.0 | 0.0012802 | 5.36245400000189 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-003:BA | 1 | 0.0 | 0.0012423 | 3.5205756000068504 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-004:AB | 1 | 0.0 | 0.0012529000000000002 | 3.9367047999985516 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-005:BA | 1 | 0.0 | 0.0012483 | 4.161977600000682 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-006:BA | 1 | 0.0 | 0.0012437000000000001 | 3.4812457999942126 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-007:AB | 1 | 0.0 | 0.0012378 | 4.502156000002287 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-008:AB | 1 | 0.0 | 0.001256 | 4.232369399993331 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-009:AB | 1 | 0.0 | 0.00028704 | 4.537471699994057 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-010:AB | 1 | 0.0 | 0.00027594000000000007 | 6.005582700003288 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-011:AB | 1 | 0.0 | 0.0012453 | 3.6849490000022342 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-012:BA | 1 | 0.0 | 0.0012889000000000002 | 4.794698500001687 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-013:AB | 1 | 0.0 | 0.00025924 | 3.6134196000057273 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-014:BA | 1 | 0.0 | 0.00032814 | 4.443213800012018 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-015:AB | 1 | 0.0 | 0.00025884000000000004 | 4.675425800000085 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-016:BA | 1 | 0.0 | 0.0002649400000000001 | 5.392881400010083 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-017:AB | 1 | 0.0 | 0.0012724000000000001 | 4.973583800005144 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-018:BA | 1 | 0.0 | 0.00027704000000000004 | 5.505033800000092 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-019:BA | 1 | 0.0 | 0.00026094000000000003 | 4.831043500002124 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-020:AB | 1 | 0.0 | 0.00026594000000000005 | 5.34949520000373 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-021:AB | 1 | 0.0 | 0.00028104000000000003 | 8.997345199997653 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-022:AB | 1 | 0.0 | 0.00027664 | 4.767386000006809 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-023:AB | 1 | 0.0 | 0.00025774 | 7.68628809999791 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-024:AB | 1 | 0.0 | 0.00029534000000000006 | 4.834143400003086 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-025:BA | 1 | 0.0 | 0.00025464 | 10.59997559999465 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-026:BA | 1 | 0.0 | 0.00025294 | 5.954508199996781 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-027:BA | 1 | 0.0 | 0.00025684000000000004 | 26.87929320000694 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-028:AB | 1 | 0.0 | 0.00026394000000000005 | 18.773440100005246 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-029:BA | 1 | 0.0 | 0.00027784 | 13.197425499995006 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-030:AB | 1 | 0.0 | 0.00026244000000000007 | 5.361415299994405 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-031:AB | 1 | 0.0 | 0.00025684000000000004 | 5.339413599998807 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-032:AB | 1 | 0.0 | 0.00026414 | 11.175504599988926 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-033:AB | 1 | 0.0 | 0.00028104000000000003 | 6.357254999995348 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-034:AB | 1 | 0.0 | 0.00025894000000000004 | 6.110098699995433 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-035:BA | 1 | 0.0 | 0.00025264 | 5.315311300000758 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-036:AB | 1 | 0.0 | 0.00030184000000000005 | 5.0165281999943545 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-037:AB | 1 | 0.0 | 0.00026394000000000005 | 4.8118531000072835 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-038:BA | 1 | 0.0 | 0.00029524 | 5.535897699999623 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-039:BA | 1 | 0.0 | 0.00026214 | 4.90174489999481 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-040:AB | 1 | 0.0 | 0.00025794000000000007 | 4.661294999998063 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-041:BA | 1 | 0.0 | 0.00027204000000000003 | 5.169921200009412 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-042:AB | 1 | 0.0 | 0.0012592 | 6.204203199988115 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-043:BA | 1 | 0.0 | 0.00025704000000000005 | 5.922709499995108 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-044:BA | 1 | 0.0 | 0.0012731 | 4.678677300005802 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-045:BA | 1 | 0.0 | 0.00027834 | 4.803987100007362 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-046:AB | 1 | 0.0 | 0.00025964 | 20.797416600005818 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-047:AB | 1 | 0.0 | 0.00026104000000000004 | 5.327500300001702 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-048:AB | 1 | 0.0 | 0.00029804 | 5.441435200002161 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-049:AB | 1 | 0.0 | 0.00025404000000000003 | 4.376598000002559 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-050:AB | 1 | 0.0 | 0.00025314 | 4.25495729999966 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-051:BA | 1 | 0.0 | 0.00026114 | 6.843702400001348 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-052:AB | 1 | 0.0 | 0.00026324000000000003 | 5.658009000006132 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-053:AB | 1 | 0.0 | 0.00027024 | 4.3049061999918194 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-054:AB | 1 | 0.0 | 0.00028274 | 5.601024599993252 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-055:BA | 1 | 0.0 | 0.00025704000000000005 | 4.324254699997255 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-056:BA | 1 | 0.0 | 0.00026263999999999997 | 4.293021999998018 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-057:AB | 1 | 0.0 | 0.00027934000000000005 | 11.383785099998931 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-058:AB | 1 | 0.0 | 0.00027454000000000004 | 6.06489499998861 |
| notebook33 | gpt-6-luna | codex | test:judge:test-code-059:BA | 1 | 0.0 | 0.00025944000000000005 | 4.904153199997381 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-000:BA | 1 | 0.0 | 0.0005235400000000001 | 4.524902499993914 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-001:BA | 1 | 0.0 | 0.00052404 | 5.129212200001348 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-002:AB | 1 | 0.0 | 0.0005239400000000001 | 4.000744899996789 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-003:BA | 1 | 0.0 | 0.00052434 | 4.558997600004659 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-004:BA | 1 | 0.0 | 0.0005235400000000001 | 5.376622399999178 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-005:BA | 1 | 0.0 | 0.00052824 | 4.312336900009541 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-006:BA | 1 | 0.0 | 0.00052254 | 4.289268199994694 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-007:AB | 1 | 0.0 | 0.0005139400000000001 | 6.46196559999953 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-008:AB | 1 | 0.0 | 0.00052174 | 5.62816350000503 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-009:BA | 1 | 0.0 | 0.00052424 | 6.932357300000149 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-010:BA | 1 | 0.0 | 0.00051174 | 4.417331100004958 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-011:AB | 1 | 0.0 | 0.00052474 | 5.125419900010456 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-012:AB | 1 | 0.0 | 0.0005210400000000001 | 6.082458499993663 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-013:BA | 1 | 0.0 | 0.0005159400000000001 | 4.623653700007708 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-014:BA | 1 | 0.0 | 0.0005174400000000001 | 6.210195100007695 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-015:AB | 1 | 0.0 | 0.00052324 | 4.561799300005077 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-016:AB | 1 | 0.0 | 0.00052254 | 5.353316300010192 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-017:AB | 1 | 0.0 | 0.00052124 | 4.638673999987077 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-018:BA | 1 | 0.0 | 0.00051324 | 4.880930900006206 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-019:AB | 1 | 0.0 | 0.00052154 | 4.4186580000096 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-020:BA | 1 | 0.0 | 0.0005190400000000001 | 4.717162799992366 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-021:AB | 1 | 0.0 | 0.00052224 | 4.587612200004514 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-022:BA | 1 | 0.0 | 0.00051574 | 4.119478900000104 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-023:BA | 1 | 0.0 | 0.00052324 | 7.201123300008476 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-024:AB | 1 | 0.0 | 0.0005235400000000001 | 5.596568300010404 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-025:BA | 1 | 0.0 | 0.00052124 | 8.045689899998251 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-026:AB | 1 | 0.0 | 0.0015132000000000001 | 4.331364199999371 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-027:BA | 1 | 0.0 | 0.00051924 | 5.362614500001655 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-028:AB | 1 | 0.0 | 0.00052174 | 6.790701499994611 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-029:AB | 1 | 0.0 | 0.0005185400000000001 | 4.501883099990664 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-030:BA | 1 | 0.0 | 0.00052114 | 7.046087599999737 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-031:BA | 1 | 0.0 | 0.0005210400000000001 | 4.710905300002196 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-032:AB | 1 | 0.0 | 0.00052654 | 6.1752691000001505 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-033:AB | 1 | 0.0 | 0.00052434 | 4.753497300000163 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-034:AB | 1 | 0.0 | 0.00052344 | 4.895235300005879 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-035:BA | 1 | 0.0 | 0.0005230400000000001 | 4.799849900009576 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-036:BA | 1 | 0.0 | 0.0005295400000000001 | 4.347542599993176 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-037:AB | 1 | 0.0 | 0.00052274 | 4.167341200009105 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-038:AB | 1 | 0.0 | 0.0005134400000000001 | 4.928254099999322 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-039:AB | 1 | 0.0 | 0.0005230400000000001 | 5.171951799988165 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-040:AB | 1 | 0.0 | 0.00052514 | 4.902070900003309 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-041:AB | 1 | 0.0 | 0.00051924 | 5.7373299000028055 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-042:BA | 1 | 0.0 | 0.00052574 | 4.86215300000913 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-043:BA | 1 | 0.0 | 0.00052134 | 4.388516500010155 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-044:AB | 1 | 0.0 | 0.00052404 | 4.062005300002056 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-045:AB | 1 | 0.0 | 0.00051604 | 4.559895299986238 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-046:AB | 1 | 0.0 | 0.0005214400000000001 | 7.616088800001307 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-047:BA | 1 | 0.0 | 0.00051264 | 4.21349840000039 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-048:AB | 1 | 0.0 | 0.00052124 | 9.440440000005765 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-049:AB | 1 | 0.0 | 0.00051524 | 5.774062199998298 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-050:BA | 1 | 0.0 | 0.0005224400000000001 | 4.86814819999563 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-051:AB | 1 | 0.0 | 0.00051174 | 5.591333200005465 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-052:AB | 1 | 0.0 | 0.00052344 | 4.5783139999985 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-053:AB | 1 | 0.0 | 0.00051774 | 4.713475500000641 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-054:BA | 1 | 0.0 | 0.00051774 | 4.432025000001886 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-055:AB | 1 | 0.0 | 0.0015114 | 11.2873821999965 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-056:BA | 1 | 0.0 | 0.0005239400000000001 | 4.936534499996924 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-057:AB | 1 | 0.0 | 0.00052564 | 4.591013899989775 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-058:AB | 1 | 0.0 | 0.0005115400000000001 | 4.058408299999428 |
| notebook33 | gpt-6-luna | codex | test:judge:test-grounded-059:BA | 1 | 0.0 | 0.0005210400000000001 | 6.975668300001416 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-000:BA | 1 | 0.0 | 0.00036214 | 4.3597913999983575 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-001:BA | 1 | 0.0 | 0.00035494000000000004 | 4.7264490999950795 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-002:BA | 1 | 0.0 | 0.00036794000000000003 | 5.0839515999978175 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-003:BA | 1 | 0.0 | 0.00036063999999999996 | 3.501834999988205 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-004:BA | 1 | 0.0 | 0.00036274 | 4.272144500006107 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-005:BA | 1 | 0.0 | 0.00036224 | 4.220082800005912 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-006:BA | 1 | 0.0 | 0.00035774 | 5.340224600004149 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-007:AB | 1 | 0.0 | 0.00036534 | 4.7577453999983845 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-008:AB | 1 | 0.0 | 0.00035753999999999994 | 3.0553599999984726 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-009:BA | 1 | 0.0 | 0.00035684000000000003 | 4.782563000000664 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-010:BA | 1 | 0.0 | 0.00036224 | 4.892650399997365 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-011:AB | 1 | 0.0 | 0.00036784000000000003 | 3.9574193000007654 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-012:AB | 1 | 0.0 | 0.00036914 | 4.804382499991334 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-013:AB | 1 | 0.0 | 0.0013449 | 4.729928900007508 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-014:BA | 1 | 0.0 | 0.00036224 | 6.216885000001639 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-015:AB | 1 | 0.0 | 0.00035774 | 9.194664800001192 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-016:AB | 1 | 0.0 | 0.00036763999999999997 | 4.397420399996918 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-017:AB | 1 | 0.0 | 0.00036244000000000006 | 4.113159200001974 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-018:BA | 1 | 0.0 | 0.00036324 | 5.00938980000501 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-019:BA | 1 | 0.0 | 0.00036053999999999996 | 5.642758599991794 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-020:BA | 1 | 0.0 | 0.00036484 | 4.735211899998831 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-021:AB | 1 | 0.0 | 0.00037134 | 9.532855400000699 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-022:BA | 1 | 0.0 | 0.00035444000000000003 | 6.026478300002054 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-023:BA | 1 | 0.0 | 0.00036374 | 4.53180369999609 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-024:BA | 1 | 0.0 | 0.00036124000000000003 | 3.910572599997977 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-025:BA | 1 | 0.0 | 0.0013442 | 4.023715700008324 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-026:BA | 1 | 0.0 | 0.00035803999999999995 | 4.664123399998061 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-027:BA | 1 | 0.0 | 0.00036144000000000004 | 18.673601899994537 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-028:BA | 1 | 0.0 | 0.00036354 | 4.444693099998403 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-029:AB | 1 | 0.0 | 0.0013426000000000002 | 4.4349474999908125 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-030:BA | 1 | 0.0 | 0.00036003999999999995 | 5.844959199996083 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-031:BA | 1 | 0.0 | 0.00035954 | 6.390082300000358 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-032:AB | 1 | 0.0 | 0.00037084000000000005 | 8.18046050000703 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-033:BA | 1 | 0.0 | 0.00035624 | 4.341998200005037 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-034:AB | 1 | 0.0 | 0.00035994000000000005 | 4.0575268999964464 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-035:BA | 1 | 0.0 | 0.00035784000000000006 | 11.973433199993451 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-036:BA | 1 | 0.0 | 0.00037344000000000006 | 5.360898500002804 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-037:BA | 1 | 0.0 | 0.00036644000000000005 | 7.681388299999526 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-038:BA | 1 | 0.0 | 0.00035403999999999996 | 4.628010000000359 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-039:BA | 1 | 0.0 | 0.00036034 | 3.9738407999975607 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-040:BA | 1 | 0.0 | 0.00036184000000000005 | 4.251727300012135 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-041:BA | 1 | 0.0 | 0.00035984000000000005 | 5.597320300003048 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-042:BA | 1 | 0.0 | 0.00035594000000000006 | 4.887073499994585 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-043:AB | 1 | 0.0 | 0.0003674400000000001 | 8.732647400000133 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-044:BA | 1 | 0.0 | 0.00036444000000000005 | 4.339412100001937 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-045:AB | 1 | 0.0 | 0.00035424 | 3.740625499995076 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-046:BA | 1 | 0.0 | 0.00036103999999999997 | 5.461266499987687 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-047:BA | 1 | 0.0 | 0.00036374 | 4.486912399996072 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-048:AB | 1 | 0.0 | 0.00036534 | 4.832884300005389 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-049:AB | 1 | 0.0 | 0.0013512 | 4.154909399992903 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-050:BA | 1 | 0.0 | 0.00036124000000000003 | 5.905499900007271 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-051:AB | 1 | 0.0 | 0.0013588000000000003 | 4.966125099992496 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-052:BA | 1 | 0.0 | 0.00036024 | 6.446121200002381 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-053:AB | 1 | 0.0 | 0.0003699400000000001 | 5.428504100011196 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-054:AB | 1 | 0.0 | 0.00036444000000000005 | 4.5254991999972844 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-055:AB | 1 | 0.0 | 0.00035494000000000004 | 4.5002574999962235 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-056:BA | 1 | 0.0 | 0.00036853999999999994 | 4.4702901000127895 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-057:BA | 1 | 0.0 | 0.00035474000000000004 | 6.271503099997062 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-058:BA | 1 | 0.0 | 0.00035744000000000005 | 5.127875100006349 |
| notebook33 | gpt-6-luna | codex | test:judge:test-instructions-059:AB | 1 | 0.0 | 0.00035444000000000003 | 5.398766900005285 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-000:AB | 1 | 0.0 | 0.00037254 | 4.2822180000075605 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-001:AB | 1 | 0.0 | 0.00034044000000000007 | 5.59489969999413 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-002:BA | 1 | 0.0 | 0.00034184000000000005 | 4.5948434000019915 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-003:AB | 1 | 0.0 | 0.00033434000000000003 | 4.373461700000917 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-004:AB | 1 | 0.0 | 0.00032504 | 4.978667400006088 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-005:BA | 1 | 0.0 | 0.00033144000000000007 | 5.256335199999739 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-006:BA | 1 | 0.0 | 0.00037524 | 4.471802200001548 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-007:AB | 1 | 0.0 | 0.00033364 | 4.52891290000116 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-008:BA | 1 | 0.0 | 0.00033334000000000006 | 7.4116548000019975 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-009:AB | 1 | 0.0 | 0.00033184 | 3.7964934000046924 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-010:BA | 1 | 0.0 | 0.00031874000000000003 | 4.286661799997091 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-011:AB | 1 | 0.0 | 0.00033744000000000005 | 7.340038900001673 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-012:BA | 1 | 0.0 | 0.00037254 | 4.944533599991701 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-013:BA | 1 | 0.0 | 0.0013216 | 3.9132837999932235 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-014:BA | 1 | 0.0 | 0.00033694000000000004 | 5.600448600001982 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-015:AB | 1 | 0.0 | 0.00034774000000000003 | 4.961675999991712 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-016:AB | 1 | 0.0 | 0.00032713999999999996 | 4.261156300010043 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-017:AB | 1 | 0.0 | 0.00033504000000000004 | 9.516501200007042 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-018:BA | 1 | 0.0 | 0.0013632 | 4.8393639999994775 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-019:AB | 1 | 0.0 | 0.00032834000000000004 | 5.053094999995665 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-020:AB | 1 | 0.0 | 0.0013277 | 4.911352100010845 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-021:BA | 1 | 0.0 | 0.00033163999999999996 | 4.171637299994472 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-022:AB | 1 | 0.0 | 0.00032174 | 4.55129949998809 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-023:BA | 1 | 0.0 | 0.00033204 | 4.916785299996263 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-024:AB | 1 | 0.0 | 0.00035834 | 13.281961999993655 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-025:AB | 1 | 0.0 | 0.00033424 | 5.70234440000786 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-026:BA | 1 | 0.0 | 0.00032464 | 4.533334300009301 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-027:AB | 1 | 0.0 | 0.00033464 | 4.443365400002222 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-028:AB | 1 | 0.0 | 0.00032934 | 3.629356599994935 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-029:BA | 1 | 0.0 | 0.00032864 | 5.460547800001223 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-030:AB | 1 | 0.0 | 0.00037403999999999996 | 3.842344700009562 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-031:AB | 1 | 0.0 | 0.00033744000000000005 | 5.72473830000672 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-032:AB | 1 | 0.0 | 0.00033494000000000004 | 6.449382200007676 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-033:BA | 1 | 0.0 | 0.00034804000000000004 | 5.460324699990451 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-034:BA | 1 | 0.0 | 0.00032204 | 4.3444951999990735 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-035:BA | 1 | 0.0 | 0.00032884000000000006 | 3.9571899000002304 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-036:BA | 1 | 0.0 | 0.00036804 | 4.069582800002536 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-037:BA | 1 | 0.0 | 0.00033434000000000003 | 5.760383100001491 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-038:AB | 1 | 0.0 | 0.00032684 | 5.180660899990471 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-039:AB | 1 | 0.0 | 0.00033154 | 10.6933704999974 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-040:AB | 1 | 0.0 | 0.00032864 | 4.852261000007275 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-041:BA | 1 | 0.0 | 0.00033304 | 3.7524327999999514 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-042:AB | 1 | 0.0 | 0.00035564 | 4.5328801999858115 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-043:AB | 1 | 0.0 | 0.0003384400000000001 | 6.06800280000607 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-044:AB | 1 | 0.0 | 0.0013265 | 4.318794699996943 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-045:BA | 1 | 0.0 | 0.00034304 | 4.635640399996191 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-046:AB | 1 | 0.0 | 0.00032754 | 4.248982999997679 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-047:AB | 1 | 0.0 | 0.00032934 | 4.669823300006101 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-048:AB | 1 | 0.0 | 0.00036414 | 4.4454217000020435 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-049:AB | 1 | 0.0 | 0.0013173000000000002 | 4.163008100003935 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-050:AB | 1 | 0.0 | 0.00032674 | 6.274850100002368 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-051:AB | 1 | 0.0 | 0.00033224000000000003 | 4.775362699991092 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-052:BA | 1 | 0.0 | 0.00032204 | 4.254720700002508 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-053:AB | 1 | 0.0 | 0.00034044000000000007 | 4.776507999995374 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-054:BA | 1 | 0.0 | 0.00037114 | 4.122166600005585 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-055:AB | 1 | 0.0 | 0.0013117 | 3.9042198000097414 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-056:BA | 1 | 0.0 | 0.00032664 | 5.072222299990244 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-057:AB | 1 | 0.0 | 0.0013177 | 5.627628199988976 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-058:BA | 1 | 0.0 | 0.00034104000000000003 | 9.710801699999138 |
| notebook33 | gpt-6-luna | codex | test:judge:test-worked-059:BA | 1 | 0.0 | 0.00033254000000000004 | 4.270016099995701 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-000:BA | 1 | 0.0 | 0.027344 | 6.146306599999662 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-001:BA | 1 | 0.0 | 0.026572 | 7.483348099995055 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-002:AB | 1 | 0.0 | 0.029026 | 15.096915599991917 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-003:BA | 1 | 0.0 | 0.026276 | 7.494158100002096 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-004:AB | 1 | 0.0 | 0.026282 | 4.723769200005336 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-005:BA | 1 | 0.0 | 0.026776 | 7.880277699994622 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-006:BA | 1 | 0.0 | 0.026606 | 6.257136400003219 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-007:AB | 1 | 0.0 | 0.026394 | 6.364453599991975 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-008:AB | 1 | 0.0 | 0.026282 | 5.324683099999675 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-009:AB | 1 | 0.0 | 0.0060328000000000005 | 6.932141400000546 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-010:AB | 1 | 0.0 | 0.006902800000000001 | 14.296369000003324 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-011:AB | 1 | 0.0 | 0.026204 | 7.487722800011397 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-012:BA | 1 | 0.0 | 0.0064368 | 8.221061700009159 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-013:AB | 1 | 0.0 | 0.02647 | 5.913257100008195 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-014:BA | 1 | 0.0 | 0.028114 | 8.547776499995962 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-015:AB | 1 | 0.0 | 0.0056708 | 6.8694317000044975 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-016:BA | 1 | 0.0 | 0.0053568 | 5.321797899989178 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-017:AB | 1 | 0.0 | 0.0060968 | 7.146412100002635 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-018:BA | 1 | 0.0 | 0.0077528 | 20.16911849999451 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-019:BA | 1 | 0.0 | 0.02623 | 5.337588300011703 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-020:AB | 1 | 0.0 | 0.0055908 | 8.139474299998255 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-021:AB | 1 | 0.0 | 0.0062588 | 12.743273800006136 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-022:AB | 1 | 0.0 | 0.028022 | 12.723789800002123 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-023:AB | 1 | 0.0 | 0.0053688 | 14.20377500000177 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-024:AB | 1 | 0.0 | 0.0064188000000000005 | 6.80703419999918 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-025:BA | 1 | 0.0 | 0.005680800000000001 | 12.615832700001192 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-026:BA | 1 | 0.0 | 0.005216800000000001 | 6.9621738999994704 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-027:BA | 1 | 0.0 | 0.0057508 | 9.836745799999335 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-028:AB | 1 | 0.0 | 0.026622 | 29.047904200007906 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-029:BA | 1 | 0.0 | 0.028614 | 19.10420200000226 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-030:AB | 1 | 0.0 | 0.0054568 | 6.538070399998105 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-031:AB | 1 | 0.0 | 0.0053248 | 7.205064000008861 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-032:AB | 1 | 0.0 | 0.0057028 | 16.102493799990043 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-033:AB | 1 | 0.0 | 0.006098800000000001 | 8.486378200002946 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-034:AB | 1 | 0.0 | 0.02684 | 9.813034699996933 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-035:BA | 1 | 0.0 | 0.0052148 | 5.955850000013015 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-036:AB | 1 | 0.0 | 0.0067888 | 9.340096800005995 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-037:AB | 1 | 0.0 | 0.0056408000000000005 | 7.423617099993862 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-038:BA | 1 | 0.0 | 0.0074588 | 15.259679399998276 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-039:BA | 1 | 0.0 | 0.0056408000000000005 | 11.309934499993687 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-040:AB | 1 | 0.0 | 0.026248 | 5.49023809999926 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-041:BA | 1 | 0.0 | 0.02894 | 18.3428952999966 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-042:AB | 1 | 0.0 | 0.0066668000000000005 | 11.330368399998406 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-043:BA | 1 | 0.0 | 0.0053128 | 6.297510799995507 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-044:BA | 1 | 0.0 | 0.0062608 | 9.437426599994069 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-045:BA | 1 | 0.0 | 0.026806 | 6.8392592999880435 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-046:AB | 1 | 0.0 | 0.026464 | 33.05929240000842 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-047:AB | 1 | 0.0 | 0.0055248 | 8.903527200003737 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-048:AB | 1 | 0.0 | 0.0064968000000000005 | 8.750614999997197 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-049:AB | 1 | 0.0 | 0.0056388 | 7.594795699988026 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-050:AB | 1 | 0.0 | 0.0051468 | 5.570915400006925 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-051:BA | 1 | 0.0 | 0.0053448 | 9.828022999994573 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-052:AB | 1 | 0.0 | 0.005386800000000001 | 6.828608499999973 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-053:AB | 1 | 0.0 | 0.0071068 | 14.328867399992305 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-054:AB | 1 | 0.0 | 0.0062228000000000006 | 11.562573599992902 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-055:BA | 1 | 0.0 | 0.0055348 | 6.7663324999884935 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-056:BA | 1 | 0.0 | 0.026568 | 7.664827900007367 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-057:AB | 1 | 0.0 | 0.0061068 | 13.021225100004813 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-058:AB | 1 | 0.0 | 0.0061168 | 7.847317099993234 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-code-059:BA | 1 | 0.0 | 0.0054088 | 7.249920399990515 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-000:BA | 1 | 0.0 | 0.010548799999999999 | 6.209606799995527 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-001:BA | 1 | 0.0 | 0.0106628 | 6.657372800007579 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-002:AB | 1 | 0.0 | 0.0108028 | 6.211586999997962 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-003:BA | 1 | 0.0 | 0.0107888 | 7.316087899991544 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-004:BA | 1 | 0.0 | 0.031458 | 5.09079990000464 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-005:BA | 1 | 0.0 | 0.0105788 | 7.050541499993415 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-006:BA | 1 | 0.0 | 0.010730799999999999 | 6.932231200000388 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-007:AB | 1 | 0.0 | 0.0105528 | 6.776552900002571 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-008:AB | 1 | 0.0 | 0.031498 | 6.303021699990495 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-009:BA | 1 | 0.0 | 0.010666799999999999 | 9.074732799999765 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-010:BA | 1 | 0.0 | 0.010836799999999999 | 7.668821900006151 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-011:AB | 1 | 0.0 | 0.010784799999999999 | 7.66251779999584 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-012:AB | 1 | 0.0 | 0.031464 | 6.827342400007183 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-013:BA | 1 | 0.0 | 0.0106868 | 7.134035200011567 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-014:BA | 1 | 0.0 | 0.0107908 | 7.6859955999971135 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-015:AB | 1 | 0.0 | 0.0315 | 7.340493399999104 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-016:AB | 1 | 0.0 | 0.0105528 | 5.96050980000291 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-017:AB | 1 | 0.0 | 0.010928799999999999 | 8.59896160000062 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-018:BA | 1 | 0.0 | 0.010510799999999999 | 5.848505200003274 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-019:AB | 1 | 0.0 | 0.010872799999999998 | 8.080096399993636 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-020:BA | 1 | 0.0 | 0.0105588 | 7.178663200000301 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-021:AB | 1 | 0.0 | 0.0105128 | 5.94193180000002 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-022:BA | 1 | 0.0 | 0.0107928 | 6.6761387000005925 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-023:BA | 1 | 0.0 | 0.031488 | 6.394223399998737 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-024:AB | 1 | 0.0 | 0.0108068 | 7.578878599990276 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-025:BA | 1 | 0.0 | 0.0107128 | 7.414650000006077 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-026:AB | 1 | 0.0 | 0.031678 | 7.745832500004326 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-027:BA | 1 | 0.0 | 0.0108688 | 7.265576899997541 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-028:AB | 1 | 0.0 | 0.031612 | 6.193260600004578 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-029:AB | 1 | 0.0 | 0.031534 | 6.538074800002505 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-030:BA | 1 | 0.0 | 0.0105408 | 5.240689999991446 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-031:BA | 1 | 0.0 | 0.0106228 | 10.060299100005068 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-032:AB | 1 | 0.0 | 0.010862799999999999 | 10.172197799998685 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-033:AB | 1 | 0.0 | 0.031988 | 8.74474769999506 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-034:AB | 1 | 0.0 | 0.0105128 | 7.7581099000090035 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-035:BA | 1 | 0.0 | 0.0105968 | 6.65123410000524 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-036:BA | 1 | 0.0 | 0.010536799999999999 | 7.1825700999906985 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-037:AB | 1 | 0.0 | 0.0029371999999999996 | 28.735297500010347 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-038:AB | 1 | 0.0 | 0.0105448 | 6.307732900007977 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-039:AB | 1 | 0.0 | 0.0109188 | 6.445400500000687 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-040:AB | 1 | 0.0 | 0.010718799999999999 | 6.612404999992577 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-041:AB | 1 | 0.0 | 0.010860799999999999 | 9.33381460000237 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-042:BA | 1 | 0.0 | 0.010796799999999999 | 5.76245189999463 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-043:BA | 1 | 0.0 | 0.010588799999999999 | 5.720242600000347 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-044:AB | 1 | 0.0 | 0.010536799999999999 | 5.2418598999938695 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-045:AB | 1 | 0.0 | 0.0110088 | 6.805418899995857 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-046:AB | 1 | 0.0 | 0.010772799999999999 | 14.016052599996328 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-047:BA | 1 | 0.0 | 0.031504 | 7.455148699998972 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-048:AB | 1 | 0.0 | 0.010898799999999998 | 12.407413799999631 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-049:AB | 1 | 0.0 | 0.010638799999999999 | 6.040788500002236 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-050:BA | 1 | 0.0 | 0.010576799999999999 | 5.028778299994883 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-051:AB | 1 | 0.0 | 0.0105668 | 6.037057399997138 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-052:AB | 1 | 0.0 | 0.0108568 | 7.438801899988903 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-053:AB | 1 | 0.0 | 0.010902799999999999 | 8.157284400003846 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-054:BA | 1 | 0.0 | 0.0106568 | 6.828078799997456 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-055:AB | 1 | 0.0 | 0.010876799999999999 | 20.661594899997 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-056:BA | 1 | 0.0 | 0.010562799999999999 | 8.510851200000616 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-057:AB | 1 | 0.0 | 0.0109448 | 6.604395799993654 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-058:AB | 1 | 0.0 | 0.0108008 | 8.318970699998317 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-grounded-059:BA | 1 | 0.0 | 0.010600799999999999 | 5.7103519999946 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-000:BA | 1 | 0.0 | 0.0253928 | 28.92186609999044 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-001:BA | 1 | 0.0 | 0.0236228 | 24.461882899995544 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-002:BA | 1 | 0.0 | 0.0205728 | 23.788061400002334 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-003:BA | 1 | 0.0 | 0.021664799999999998 | 24.473467799994978 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-004:BA | 1 | 0.0 | 0.0227808 | 24.630997500004014 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-005:BA | 1 | 0.0 | 0.0329588 | 50.101863899995806 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-006:BA | 1 | 0.0 | 0.0327608 | 39.44923089999065 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-007:AB | 1 | 0.0 | 0.024432799999999998 | 25.685437399995863 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-008:AB | 1 | 0.0 | 0.0242688 | 22.71367929999542 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-009:BA | 1 | 0.0 | 0.035320800000000006 | 45.215468999987934 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-010:BA | 1 | 0.0 | 0.021716799999999998 | 23.05893030000152 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-011:AB | 1 | 0.0 | 0.0292508 | 32.304337299996405 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-012:AB | 1 | 0.0 | 0.0267708 | 28.13064360000135 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-013:AB | 1 | 0.0 | 0.045416 | 27.713994600009755 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-014:BA | 1 | 0.0 | 0.0238028 | 28.66510460000427 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-015:AB | 1 | 0.0 | 0.0080908 | 13.161026800007676 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-016:AB | 1 | 0.0 | 0.0246908 | 30.04499960000976 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-017:AB | 1 | 0.0 | 0.0203228 | 24.365117499997723 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-018:BA | 1 | 0.0 | 0.042062 | 22.585583399995812 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-019:BA | 1 | 0.0 | 0.0210188 | 25.961212200010777 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-020:BA | 1 | 0.0 | 0.0078108000000000006 | 6.864888099997188 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-021:AB | 1 | 0.0 | 0.021064799999999998 | 21.157416200003354 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-022:BA | 1 | 0.0 | 0.027062799999999998 | 44.36102899999241 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-023:BA | 1 | 0.0 | 0.0218188 | 28.201176600006875 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-024:BA | 1 | 0.0 | 0.0218948 | 27.420186100003775 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-025:BA | 1 | 0.0 | 0.0194808 | 21.139100700005656 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-026:BA | 1 | 0.0 | 0.0231468 | 25.96020149999822 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-027:BA | 1 | 0.0 | 0.023742799999999998 | 28.575807300003362 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-028:BA | 1 | 0.0 | 0.0245868 | 26.18673869999475 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-029:AB | 1 | 0.0 | 0.0242268 | 26.08567280000716 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-030:BA | 1 | 0.0 | 0.0223288 | 25.442889300000388 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-031:BA | 1 | 0.0 | 0.0313888 | 37.0129203999968 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-032:AB | 1 | 0.0 | 0.0263488 | 31.90697630000068 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-033:BA | 1 | 0.0 | 0.0209128 | 25.775711299997056 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-034:AB | 1 | 0.0 | 0.0327488 | 41.38943840000138 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-035:BA | 1 | 0.0 | 0.0303608 | 35.58562769999844 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-036:BA | 1 | 0.0 | 0.0231928 | 26.133440699995845 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-037:BA | 1 | 0.0 | 0.024016799999999998 | 33.378581999990274 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-038:BA | 1 | 0.0 | 0.007758800000000001 | 9.55952919999254 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-039:BA | 1 | 0.0 | 0.0228608 | 19.648591200006194 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-040:BA | 1 | 0.0 | 0.0259548 | 28.18175629999314 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-041:BA | 1 | 0.0 | 0.039634 | 20.234042500000214 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-042:BA | 1 | 0.0 | 0.028526799999999998 | 36.53487000000314 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-043:AB | 1 | 0.0 | 0.0203648 | 29.37788480000745 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-044:BA | 1 | 0.0 | 0.0271648 | 37.10803730000043 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-045:AB | 1 | 0.0 | 0.0080528 | 10.657880800004932 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-046:BA | 1 | 0.0 | 0.024262799999999998 | 22.92828870000085 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-047:BA | 1 | 0.0 | 0.0238828 | 29.223321700002998 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-048:AB | 1 | 0.0 | 0.0246128 | 31.212662500009174 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-049:AB | 1 | 0.0 | 0.0204768 | 26.926827600007528 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-050:BA | 1 | 0.0 | 0.0287828 | 37.16557300000568 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-051:AB | 1 | 0.0 | 0.0309048 | 27.57881950000592 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-052:BA | 1 | 0.0 | 0.028854 | 20.739060000007157 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-053:AB | 1 | 0.0 | 0.024772799999999998 | 31.874982699999237 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-054:AB | 1 | 0.0 | 0.0202828 | 28.14289909999934 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-055:AB | 1 | 0.0 | 0.0077288 | 10.738646900004824 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-056:BA | 1 | 0.0 | 0.0215168 | 28.815026600001147 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-057:BA | 1 | 0.0 | 0.0198808 | 26.14024929999141 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-058:BA | 1 | 0.0 | 0.0286088 | 34.32882819999941 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-instructions-059:AB | 1 | 0.0 | 0.0269888 | 33.314926499995636 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-000:AB | 1 | 0.0 | 0.035356 | 23.41870179999387 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-001:AB | 1 | 0.0 | 0.0098748 | 12.724729800000205 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-002:BA | 1 | 0.0 | 0.011438799999999999 | 18.317227699997602 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-003:AB | 1 | 0.0 | 0.009294799999999999 | 16.98777130000235 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-004:AB | 1 | 0.0 | 0.0101348 | 14.076395199997933 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-005:BA | 1 | 0.0 | 0.0112708 | 17.672964400000637 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-006:BA | 1 | 0.0 | 0.0124388 | 15.459384500005399 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-007:AB | 1 | 0.0 | 0.02924 | 8.075765899993712 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-008:BA | 1 | 0.0 | 0.010480799999999998 | 21.717033599998103 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-009:AB | 1 | 0.0 | 0.0099408 | 16.285729800001718 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-010:BA | 1 | 0.0 | 0.0107228 | 13.344938000009279 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-011:AB | 1 | 0.0 | 0.0121008 | 17.393653000006452 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-012:BA | 1 | 0.0 | 0.0148548 | 22.154835100009223 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-013:BA | 1 | 0.0 | 0.010090799999999999 | 14.480192000002717 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-014:BA | 1 | 0.0 | 0.0106308 | 18.527820899995277 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-015:AB | 1 | 0.0 | 0.0100808 | 16.270725999987917 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-016:AB | 1 | 0.0 | 0.0094448 | 12.647227199995541 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-017:AB | 1 | 0.0 | 0.0120728 | 17.32170609998866 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-018:BA | 1 | 0.0 | 0.015950799999999998 | 24.7301196000044 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-019:AB | 1 | 0.0 | 0.0101628 | 16.643497599987313 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-020:AB | 1 | 0.0 | 0.008432799999999999 | 10.404273099993588 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-021:BA | 1 | 0.0 | 0.008624799999999998 | 12.174017400000594 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-022:AB | 1 | 0.0 | 0.029744 | 16.202204900007928 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-023:BA | 1 | 0.0 | 0.0090248 | 12.325773799995659 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-024:AB | 1 | 0.0 | 0.0089468 | 11.23223069999949 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-025:AB | 1 | 0.0 | 0.0111168 | 16.77742220000073 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-026:BA | 1 | 0.0 | 0.010506799999999998 | 16.400145499996142 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-027:AB | 1 | 0.0 | 0.0094968 | 12.523922499996843 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-028:AB | 1 | 0.0 | 0.0083348 | 11.555870099997264 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-029:BA | 1 | 0.0 | 0.0090668 | 16.322388599990518 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-030:AB | 1 | 0.0 | 0.0114548 | 11.478263400000287 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-031:AB | 1 | 0.0 | 0.030226 | 13.225102800002787 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-032:AB | 1 | 0.0 | 0.0090888 | 13.348440900008427 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-033:BA | 1 | 0.0 | 0.009620799999999999 | 10.54036410000117 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-034:BA | 1 | 0.0 | 0.0094448 | 17.80628030000662 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-035:BA | 1 | 0.0 | 0.0090768 | 12.795041699995636 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-036:BA | 1 | 0.0 | 0.0134048 | 19.69745690000127 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-037:BA | 1 | 0.0 | 0.0089048 | 14.673580899994704 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-038:AB | 1 | 0.0 | 0.0099388 | 21.997407699993346 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-039:AB | 1 | 0.0 | 0.010144799999999999 | 20.101200299992342 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-040:AB | 1 | 0.0 | 0.0120348 | 16.278982199990423 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-041:BA | 1 | 0.0 | 0.011998799999999999 | 18.440963200002443 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-042:AB | 1 | 0.0 | 0.0141628 | 21.047748600001796 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-043:AB | 1 | 0.0 | 0.0130888 | 21.12634610000532 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-044:AB | 1 | 0.0 | 0.0157248 | 38.00174980000884 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-045:BA | 1 | 0.0 | 0.008428799999999998 | 15.311662100008107 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-046:AB | 1 | 0.0 | 0.0110628 | 19.488552100010565 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-047:AB | 1 | 0.0 | 0.0108408 | 16.84472550000646 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-048:AB | 1 | 0.0 | 0.0145948 | 23.22545509999327 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-049:AB | 1 | 0.0 | 0.0116668 | 19.55209460000333 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-050:AB | 1 | 0.0 | 0.009032799999999999 | 14.54944109999633 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-051:AB | 1 | 0.0 | 0.0112108 | 17.079133699997328 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-052:BA | 1 | 0.0 | 0.0091448 | 14.976196000003256 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-053:AB | 1 | 0.0 | 0.0085568 | 9.620921299996553 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-054:BA | 1 | 0.0 | 0.011160799999999998 | 12.555896500009112 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-055:AB | 1 | 0.0 | 0.0085028 | 12.10086940000474 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-056:BA | 1 | 0.0 | 0.008940799999999999 | 13.447468500002287 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-057:AB | 1 | 0.0 | 0.012066799999999999 | 19.245314400002826 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-058:BA | 1 | 0.0 | 0.0132588 | 22.605162899999414 |
| notebook33 | gpt-6.1-sol | codex | test:judge:test-worked-059:BA | 1 | 0.0 | 0.0096628 | 15.81730600001174 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-000:BA | 1 | 8.187e-05 | 0.0 | 2.6166205999907106 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-001:BA | 1 | 6.864e-05 | 0.0 | 2.307744099991396 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-002:AB | 1 | 8.439e-05 | 0.0 | 2.2214015000063227 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-003:BA | 1 | 5.952e-05 | 0.0 | 2.058842400001595 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-004:AB | 1 | 6.426e-05 | 0.0 | 2.628727399991476 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-005:BA | 1 | 5.163e-05 | 0.0 | 2.407833400007803 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-006:BA | 1 | 5.511e-05 | 0.0 | 2.813855100001092 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-007:AB | 1 | 6.543e-05 | 0.0 | 2.7899265000014566 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-008:AB | 1 | 6.864e-05 | 0.0 | 2.3952428000047803 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-009:AB | 1 | 8.265e-05 | 0.0 | 2.628021600001375 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-010:AB | 1 | 6.921e-05 | 0.0 | 3.3189530999952694 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-011:AB | 1 | 7.422e-05 | 0.0 | 3.3473854000039864 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-012:BA | 1 | 8.367e-05 | 0.0 | 2.6549509999895236 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-013:AB | 1 | 6.237e-05 | 0.0 | 1.9880578000011155 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-014:BA | 1 | 0.00011319 | 0.0 | 2.9642259999964153 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-015:AB | 1 | 6.042e-05 | 0.0 | 2.0412845000100788 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-016:BA | 1 | 6.591e-05 | 0.0 | 2.854554099991219 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-017:AB | 1 | 7.779e-05 | 0.0 | 2.480786400003126 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-018:BA | 1 | 6.375e-05 | 0.0 | 2.41376300000411 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-019:BA | 1 | 5.037e-05 | 0.0 | 1.9386118999973405 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-020:AB | 1 | 6.564e-05 | 0.0 | 1.8031988000002457 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-021:AB | 1 | 7.944e-05 | 0.0 | 2.357108399999561 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-022:AB | 1 | 7.941e-05 | 0.0 | 2.319716400001198 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-023:AB | 1 | 6.36e-05 | 0.0 | 2.6929078999964986 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-024:AB | 1 | 0.00014472 | 0.0 | 6.824248999997508 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-025:BA | 1 | 4.434e-05 | 0.0 | 3.109415300001274 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-026:BA | 1 | 4.632e-05 | 0.0 | 2.9704965999990236 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-027:BA | 1 | 4.983e-05 | 0.0 | 3.409097700001439 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-028:AB | 1 | 6.381e-05 | 0.0 | 2.6861919999937527 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-029:BA | 1 | 6.576e-05 | 0.0 | 2.3434866000025067 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-030:AB | 1 | 6.912e-05 | 0.0 | 2.6190539999952307 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-031:AB | 1 | 6.528e-05 | 0.0 | 2.2165635999990627 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-032:AB | 1 | 6.984e-05 | 0.0 | 2.4090131999982987 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-033:AB | 1 | 7.878e-05 | 0.0 | 1.4992127000004984 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-034:AB | 1 | 8.943e-05 | 0.0 | 4.581170300007216 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-035:BA | 1 | 6.225e-05 | 0.0 | 1.7673816999886185 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-036:AB | 1 | 9.393e-05 | 0.0 | 2.4440422000043327 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-037:AB | 1 | 0.00097566 | 0.0 | 76.04417549999198 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-038:BA | 1 | 7.932e-05 | 0.0 | 1.8018503000057535 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-039:BA | 1 | 5.838e-05 | 0.0 | 2.854740100010531 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-040:AB | 1 | 8.631e-05 | 0.0 | 4.394514600004186 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-041:BA | 1 | 5.949e-05 | 0.0 | 1.7843874999962281 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-042:AB | 1 | 7.395e-05 | 0.0 | 1.7525662999978522 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-043:BA | 1 | 5.022e-05 | 0.0 | 1.7872136000078171 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-044:BA | 1 | 7.44e-05 | 0.0 | 1.7802566000027582 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-045:BA | 1 | 8.022e-05 | 0.0 | 1.5208053000096697 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-046:AB | 1 | 6.576e-05 | 0.0 | 1.608537799998885 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-047:AB | 1 | 6.504e-05 | 0.0 | 1.8166812999988906 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-048:AB | 1 | 9.561e-05 | 0.0 | 2.0988227000052575 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-049:AB | 1 | 6.384e-05 | 0.0 | 2.3363564999890514 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-050:AB | 1 | 5.712e-05 | 0.0 | 2.008782999997493 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-051:BA | 1 | 5.868e-05 | 0.0 | 3.9573095999949146 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-052:AB | 1 | 6.381e-05 | 0.0 | 1.555070699992939 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-053:AB | 1 | 6.75e-05 | 0.0 | 1.632795099998475 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-054:AB | 1 | 7.308e-05 | 0.0 | 1.7686638000013772 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-055:BA | 1 | 5.247e-05 | 0.0 | 1.6438554000051226 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-056:BA | 1 | 6.165e-05 | 0.0 | 2.5211568999948213 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-057:AB | 1 | 8.115e-05 | 0.0 | 1.6760776000010082 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-058:AB | 1 | 7.494e-05 | 0.0 | 1.7020610000035958 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-code-059:BA | 1 | 5.46e-05 | 0.0 | 2.363182799992501 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-000:BA | 1 | 8.421e-05 | 0.0 | 2.9959573000087403 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-001:BA | 1 | 7.323e-05 | 0.0 | 1.7423309000005247 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-002:AB | 1 | 0.00021651 | 0.0 | 2.0190376000100514 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-003:BA | 1 | 0.00022431 | 0.0 | 2.8365245000022696 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-004:BA | 1 | 7.461e-05 | 0.0 | 1.769964399994933 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-005:BA | 1 | 7.803e-05 | 0.0 | 3.2248965999897337 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-006:BA | 1 | 7.029e-05 | 0.0 | 1.8324539000022924 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-007:AB | 1 | 0.00021831 | 0.0 | 1.9603665999893565 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-008:AB | 1 | 0.00023001 | 0.0 | 2.709488799999235 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-009:BA | 1 | 0.00034233 | 0.0 | 35.81861459999345 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-010:BA | 1 | 9.879e-05 | 0.0 | 4.227101700002095 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-011:AB | 1 | 0.00021531 | 0.0 | 1.803023700005724 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-012:AB | 1 | 0.00021396 | 0.0 | 1.8126045999961207 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-013:BA | 1 | 0.00021771 | 0.0 | 4.758718700002646 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-014:BA | 1 | 0.00022956 | 0.0 | 10.141439099999843 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-015:AB | 1 | 0.00021681 | 0.0 | 2.7482177000056254 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-016:AB | 1 | 0.00022317 | 0.0 | 1.9881371999945259 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-017:AB | 1 | 0.00030672 | 0.0 | 42.11258770000131 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-018:BA | 1 | 7.674e-05 | 0.0 | 10.461972400007653 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-019:AB | 1 | 0.00024186 | 0.0 | 14.924031600006856 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-020:BA | 1 | 0.00024297 | 0.0 | 12.780305799999041 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-021:AB | 1 | 0.00024357 | 0.0 | 10.44496419999632 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-022:BA | 1 | 0.00010059 | 0.0 | 20.580954599994584 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-023:BA | 1 | 0.00022221 | 0.0 | 6.050293699998292 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-024:AB | 1 | 0.00022767 | 0.0 | 3.200793399999384 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-025:BA | 1 | 0.00022311 | 0.0 | 5.166123700008029 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-026:AB | 1 | 0.00023547 | 0.0 | 9.086184600004344 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-027:BA | 1 | 0.00022317 | 0.0 | 2.825162299996009 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-028:AB | 1 | 0.00023817 | 0.0 | 10.169306199997663 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-029:AB | 1 | 0.00022227 | 0.0 | 2.6236212000076193 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-030:BA | 1 | 8.004e-05 | 0.0 | 11.96090250000998 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-031:BA | 1 | 7.371e-05 | 0.0 | 2.783716399993864 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-032:AB | 1 | 0.00022827 | 0.0 | 4.55797330000496 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-033:AB | 1 | 0.00022371 | 0.0 | 5.173915699997451 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-034:AB | 1 | 0.00021801 | 0.0 | 2.4926749000005657 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-035:BA | 1 | 6.981e-05 | 0.0 | 3.051152300002286 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-036:BA | 1 | 8.226e-05 | 0.0 | 6.735736100003123 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-037:AB | 1 | 0.00021561 | 0.0 | 6.189669800005504 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-038:AB | 1 | 0.00022641 | 0.0 | 5.5179808999964735 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-039:AB | 1 | 0.00022041 | 0.0 | 3.630227299989201 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-040:AB | 1 | 0.00021981 | 0.0 | 3.199922700005118 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-041:AB | 1 | 0.00021711 | 0.0 | 2.976155700001982 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-042:BA | 1 | 0.00022467 | 0.0 | 3.670891000001575 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-043:BA | 1 | 7.701e-05 | 0.0 | 3.5658420999970986 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-044:AB | 1 | 0.00021801 | 0.0 | 1.9017248999880394 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-045:AB | 1 | 0.00034101 | 0.0 | 11.204818400001386 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-046:AB | 1 | 0.00023661 | 0.0 | 2.96822679998877 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-047:BA | 1 | 7.176e-05 | 0.0 | 2.109651599996141 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-048:AB | 1 | 0.00021996 | 0.0 | 3.5952144999901066 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-049:AB | 1 | 0.00023697 | 0.0 | 3.887078300002031 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-050:BA | 1 | 0.00022086 | 0.0 | 2.5931380999973044 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-051:AB | 1 | 0.00021831 | 0.0 | 3.0501953000057256 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-052:AB | 1 | 0.00021291 | 0.0 | 1.9376131999888457 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-053:AB | 1 | 0.00022476 | 0.0 | 3.457030199992005 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-054:BA | 1 | 0.00021816 | 0.0 | 2.583267699999851 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-055:AB | 1 | 0.00022257 | 0.0 | 7.798532799992245 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-056:BA | 1 | 7.491e-05 | 0.0 | 4.792224999997416 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-057:AB | 1 | 0.00023301 | 0.0 | 8.970621799991932 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-058:AB | 1 | 0.00022497 | 0.0 | 3.1016875999921467 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-grounded-059:BA | 1 | 7.116e-05 | 0.0 | 5.750449300001492 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-000:BA | 1 | 8.505e-05 | 0.0 | 8.25896069999726 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-001:BA | 1 | 0.00012591 | 0.0 | 2.161742199998116 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-002:BA | 1 | 0.00012609 | 0.0 | 2.1132271999958903 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-003:BA | 1 | 4.227e-05 | 0.0 | 2.49158190000162 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-004:BA | 1 | 0.00012081 | 0.0 | 1.6768373000086285 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-005:BA | 1 | 8.955e-05 | 0.0 | 1.6662377000029664 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-006:BA | 1 | 0.00011037 | 0.0 | 1.4537714000034612 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-007:AB | 1 | 0.00012381 | 0.0 | 1.1756674000062048 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-008:AB | 1 | 0.00012045 | 0.0 | 1.2038712999928975 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-009:BA | 1 | 0.00012705 | 0.0 | 1.7723326999985147 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-010:BA | 1 | 0.00010665 | 0.0 | 1.1236300000018673 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-011:AB | 1 | 0.00012237 | 0.0 | 1.402568900011829 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-012:AB | 1 | 7.917e-05 | 0.0 | 2.5514381999964826 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-013:AB | 1 | 7.608e-05 | 0.0 | 4.563086199996178 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-014:BA | 1 | 8.661e-05 | 0.0 | 4.436449100001482 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-015:AB | 1 | 0.00012987 | 0.0 | 2.0097740999917733 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-016:AB | 1 | 0.00012261 | 0.0 | 1.4949275999970268 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-017:AB | 1 | 0.00012321 | 0.0 | 1.3126218999968842 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-018:BA | 1 | 0.00017964 | 0.0 | 10.850016500000493 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-019:BA | 1 | 0.00012852 | 0.0 | 1.4653152999962913 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-020:BA | 1 | 0.00012156 | 0.0 | 2.26405350001005 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-021:AB | 1 | 0.00012735 | 0.0 | 1.3160401999921305 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-022:BA | 1 | 0.00010113 | 0.0 | 1.2157817999977851 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-023:BA | 1 | 8.112e-05 | 0.0 | 1.4114750000007916 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-024:BA | 1 | 7.929e-05 | 0.0 | 2.6462529999989783 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-025:BA | 1 | 9.393e-05 | 0.0 | 4.275106600005529 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-026:BA | 1 | 0.00012297 | 0.0 | 1.3301716999994824 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-027:BA | 1 | 9.3e-05 | 0.0 | 1.9698535999923479 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-028:BA | 1 | 9.525e-05 | 0.0 | 1.7571973000012804 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-029:AB | 1 | 0.00012663 | 0.0 | 1.9601611999969464 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-030:BA | 1 | 0.00012576 | 0.0 | 1.2836402999964776 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-031:BA | 1 | 0.00012465 | 0.0 | 1.6633664999972098 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-032:AB | 1 | 0.00108006 | 0.0 | 125.58587830000033 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-033:BA | 1 | 0.00012555 | 0.0 | 2.5718014999874867 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-034:AB | 1 | 8.925e-05 | 0.0 | 2.190961899992544 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-035:BA | 1 | 0.0001353 | 0.0 | 7.43725909999921 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-036:BA | 1 | 0.00011241 | 0.0 | 1.7015320000064094 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-037:BA | 1 | 0.00011241 | 0.0 | 3.608003800007282 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-038:BA | 1 | 0.00011694 | 0.0 | 1.1937280999991344 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-039:BA | 1 | 9.039e-05 | 0.0 | 1.7958498999942094 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-040:BA | 1 | 0.00012669 | 0.0 | 1.1843023999972502 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-041:BA | 1 | 8.697e-05 | 0.0 | 3.10891840000113 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-042:BA | 1 | 0.00011403 | 0.0 | 6.399525100001483 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-043:AB | 1 | 0.00012801 | 0.0 | 1.2963616999913938 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-044:BA | 1 | 0.00012684 | 0.0 | 1.484675600004266 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-045:AB | 1 | 0.00012984 | 0.0 | 2.195599400001811 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-046:BA | 1 | 0.00012789 | 0.0 | 1.3472560000082012 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-047:BA | 1 | 0.00010545 | 0.0 | 1.3971831999951974 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-048:AB | 1 | 0.00012225 | 0.0 | 1.421965800007456 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-049:AB | 1 | 0.00012585 | 0.0 | 1.9668197999999393 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-050:BA | 1 | 0.00012549 | 0.0 | 1.5536685999977635 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-051:AB | 1 | 0.0001233 | 0.0 | 1.7018251999979839 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-052:BA | 1 | 7.944e-05 | 0.0 | 1.9213206000131322 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-053:AB | 1 | 0.00012849 | 0.0 | 1.4131857999891508 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-054:AB | 1 | 0.00012717 | 0.0 | 1.6489599000051385 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-055:AB | 1 | 0.00012186 | 0.0 | 1.3732030999963172 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-056:BA | 1 | 9.714e-05 | 0.0 | 1.7088019000075292 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-057:BA | 1 | 0.00012009 | 0.0 | 2.781191200003377 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-058:BA | 1 | 0.00010353 | 0.0 | 1.4669993999996223 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-instructions-059:AB | 1 | 0.00012456 | 0.0 | 1.5275550999940606 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-000:AB | 1 | 0.00015321 | 0.0 | 5.762894999992568 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-001:AB | 1 | 0.00012087 | 0.0 | 2.2663210000027902 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-002:BA | 1 | 0.0001212 | 0.0 | 1.9998986000136938 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-003:AB | 1 | 0.00015093 | 0.0 | 6.130650500010233 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-004:AB | 1 | 0.00011106 | 0.0 | 2.085038599994732 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-005:BA | 1 | 7.707e-05 | 0.0 | 2.6518784999934724 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-006:BA | 1 | 9.771e-05 | 0.0 | 3.2070111999928486 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-007:AB | 1 | 0.00011778 | 0.0 | 1.5172355999966385 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-008:BA | 1 | 0.00012975 | 0.0 | 2.059419999990496 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-009:AB | 1 | 0.00012747 | 0.0 | 2.0672486999974353 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-010:BA | 1 | 0.00011553 | 0.0 | 1.778217000013683 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-011:AB | 1 | 0.00012405 | 0.0 | 1.503619199997047 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-012:BA | 1 | 0.0001173 | 0.0 | 3.8651298999902792 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-013:BA | 1 | 0.00012531 | 0.0 | 1.940461400008644 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-014:BA | 1 | 0.00011658 | 0.0 | 2.7119005999993533 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-015:AB | 1 | 0.00012582 | 0.0 | 2.184717799987993 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-016:AB | 1 | 0.00011871 | 0.0 | 2.1795073000103002 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-017:AB | 1 | 0.00012261 | 0.0 | 1.7926109999971231 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-018:BA | 1 | 0.00016857 | 0.0 | 2.691720600007102 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-019:AB | 1 | 0.00031758 | 0.0 | 36.97328569999081 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-020:AB | 1 | 0.00011748 | 0.0 | 2.633026299998164 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-021:BA | 1 | 7.584e-05 | 0.0 | 2.2881580000102986 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-022:AB | 1 | 0.00011406 | 0.0 | 1.6985235000029206 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-023:BA | 1 | 0.00021411 | 0.0 | 17.562220000007073 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-024:AB | 1 | 0.00014952 | 0.0 | 4.502663400009624 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-025:AB | 1 | 0.00012594 | 0.0 | 1.9006976999953622 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-026:BA | 1 | 7.35e-05 | 0.0 | 1.8070062000042526 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-027:AB | 1 | 0.0001158 | 0.0 | 1.7044257999950787 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-028:AB | 1 | 0.00011685 | 0.0 | 2.271777899994049 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-029:BA | 1 | 7.203e-05 | 0.0 | 2.4327637999958824 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-030:AB | 1 | 0.00015261 | 0.0 | 2.226008500001626 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-031:AB | 1 | 0.00012708 | 0.0 | 2.0888942000019597 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-032:AB | 1 | 0.00012072 | 0.0 | 2.1146328000031644 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-033:BA | 1 | 7.758e-05 | 0.0 | 2.0016315999964718 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-034:BA | 1 | 7.497e-05 | 0.0 | 2.4589001999993343 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-035:BA | 1 | 0.00012123 | 0.0 | 2.6663503000017954 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-036:BA | 1 | 0.00016161 | 0.0 | 3.2498782000038773 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-037:BA | 1 | 7.284e-05 | 0.0 | 1.6937727000040468 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-038:AB | 1 | 0.00011868 | 0.0 | 2.5889270000043325 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-039:AB | 1 | 0.00012156 | 0.0 | 1.7885524999874178 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-040:AB | 1 | 0.00012117 | 0.0 | 1.7637189000088256 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-041:BA | 1 | 7.632e-05 | 0.0 | 1.608206099990639 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-042:AB | 1 | 0.00014901 | 0.0 | 2.7511045999999624 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-043:AB | 1 | 0.00012777 | 0.0 | 1.9044744999991963 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-044:AB | 1 | 0.00011286 | 0.0 | 1.5768677000014577 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-045:BA | 1 | 0.00011514 | 0.0 | 23.044025900002453 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-046:AB | 1 | 0.00013806 | 0.0 | 4.114694399992004 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-047:AB | 1 | 0.0001203 | 0.0 | 2.512910399993416 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-048:AB | 1 | 5.508e-05 | 0.0 | 3.3764553999935742 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-049:AB | 1 | 0.00011961 | 0.0 | 2.883540599999833 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-050:AB | 1 | 0.0001158 | 0.0 | 1.8639725999964867 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-051:AB | 1 | 0.00012075 | 0.0 | 1.851427200002945 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-052:BA | 1 | 6.762e-05 | 0.0 | 1.724867800003267 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-053:AB | 1 | 0.00011973 | 0.0 | 1.4191596000018762 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-054:BA | 1 | 0.00010656 | 0.0 | 2.567428700000164 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-055:AB | 1 | 7.017e-05 | 0.0 | 1.699614399985876 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-056:BA | 1 | 0.00011709 | 0.0 | 1.5825859000033233 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-057:AB | 1 | 0.00012327 | 0.0 | 2.1038752000022214 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-058:BA | 1 | 7.62e-05 | 0.0 | 3.9941296000033617 |
| notebook33 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:judge:test-worked-059:BA | 1 | 3.525e-05 | 0.0 | 1.8656412999989698 |
| notebook37 | claude-opus-5-5 | claude | capability:Opus | 1 | 0.0 | 0.0071448 | 10.676931800000602 |
| notebook37 | claude-opus-5-5 | claude | development:checklist_author | 24 | 0.0 | 0.8365192 | 257.98632719996385 |
| notebook37 | claude-opus-5-5 | claude | smoke:checklist_author | 4 | 0.0 | 0.1153232 | 50.18928260001121 |
| notebook37 | claude-opus-5-5 | claude | smoke:checklist_quality | 3 | 0.0 | 0.1355704 | 25.385999100006302 |
| notebook37 | claude-opus-5-5 | claude | test:checklist_author | 234 | 0.0 | 7.3781152 | 2849.847236299858 |
| notebook37 | claude-opus-5-5 | claude | test:checklist_quality | 180 | 0.0 | 8.322064 | 1707.9161668000015 |
| notebook37 | claude-opus-5-5 | claude | transport_check:2026-11-24:Opus | 1 | 0.0 | 0.0 | 4.158685300004436 |
| notebook37 | gpt-6-luna | codex | capability:Luna | 1 | 0.0 | 0.00015604000000000003 | 3.775069800001802 |
| notebook37 | gpt-6-luna | codex | development:free_form:original | 24 | 0.0 | 0.008865860000000001 | 121.21525789999578 |
| notebook37 | gpt-6-luna | codex | development:item_checklist:original | 24 | 0.0 | 0.01139302 | 125.58301419997588 |
| notebook37 | gpt-6-luna | codex | smoke:exam_prompt:original | 4 | 0.0 | 0.0015246600000000002 | 20.94539100000111 |
| notebook37 | gpt-6-luna | codex | smoke:exam_prompt:polished | 4 | 0.0 | 0.00446166 | 32.17435899999691 |
| notebook37 | gpt-6-luna | codex | smoke:free_form:original | 4 | 0.0 | 0.0034614800000000003 | 22.42493039999681 |
| notebook37 | gpt-6-luna | codex | smoke:free_form:polished | 4 | 0.0 | 0.00441776 | 22.29089789999125 |
| notebook37 | gpt-6-luna | codex | smoke:general_rubric:original | 4 | 0.0 | 0.0025767200000000002 | 198.3502208999853 |
| notebook37 | gpt-6-luna | codex | smoke:item_checklist:original | 4 | 0.0 | 0.00259522 | 27.78707769999164 |
| notebook37 | gpt-6-luna | codex | smoke:item_checklist:polished | 4 | 0.0 | 0.005527519999999999 | 32.91505139997753 |
| notebook37 | gpt-6-luna | codex | smoke:own_requirements:original | 1 | 0.0 | 0.00038024 | 4.261289300004137 |
| notebook37 | gpt-6-luna | codex | smoke:separate_scoring:original:A | 4 | 0.0 | 0.0014880600000000003 | 197.8343228999729 |
| notebook37 | gpt-6-luna | codex | smoke:separate_scoring:original:B | 4 | 0.0 | 0.00241452 | 21.772351499996148 |
| notebook37 | gpt-6-luna | codex | test:exam_prompt:polished | 120 | 0.0 | 0.0520836 | 570.3144038000755 |
| notebook37 | gpt-6-luna | codex | test:free_form:original | 240 | 0.0 | 0.10013216000000001 | 1200.3711096998013 |
| notebook37 | gpt-6-luna | codex | test:free_form:polished | 120 | 0.0 | 0.05228706 | 588.2214067001187 |
| notebook37 | gpt-6-luna | codex | test:general_rubric:original | 240 | 0.0 | 0.11031856000000001 | 1256.2364261995099 |
| notebook37 | gpt-6-luna | codex | test:item_checklist:original | 240 | 0.0 | 0.10720400000000001 | 1176.5783235995914 |
| notebook37 | gpt-6-luna | codex | test:item_checklist:polished | 120 | 0.0 | 0.0552339 | 601.1738732006052 |
| notebook37 | gpt-6-luna | codex | test:own_requirements:original | 60 | 0.0 | 0.028652260000000002 | 301.16505779996805 |
| notebook37 | gpt-6-luna | codex | test:separate_scoring:original:A | 240 | 0.0 | 0.10708104 | 1343.1264403001987 |
| notebook37 | gpt-6-luna | codex | test:separate_scoring:original:B | 240 | 0.0 | 0.10922620000000001 | 1283.055157299692 |
| notebook37 | gpt-6-luna | codex | transport_check:2026-11-24:Luna | 1 | 0.0 | 0.0011456 | 4.372666699986439 |
| notebook37 | gpt-6.1-sol | codex | capability:Sol | 1 | 0.0 | 0.0032968000000000003 | 6.224045899987686 |
| notebook37 | gpt-6.1-sol | codex | development:free_form:original | 24 | 0.0 | 0.3092984 | 291.674863299937 |
| notebook37 | gpt-6.1-sol | codex | development:item_checklist:original | 24 | 0.0 | 0.36632 | 344.6546748999681 |
| notebook37 | gpt-6.1-sol | codex | smoke:exam_prompt:original | 4 | 0.0 | 0.0909916 | 49.4509006000153 |
| notebook37 | gpt-6.1-sol | codex | smoke:exam_prompt:polished | 4 | 0.0 | 0.1414544 | 72.75660170000629 |
| notebook37 | gpt-6.1-sol | codex | smoke:free_form:original | 4 | 0.0 | 0.0720024 | 65.54818859999068 |
| notebook37 | gpt-6.1-sol | codex | smoke:free_form:polished | 4 | 0.0 | 0.11329320000000001 | 59.58677420001186 |
| notebook37 | gpt-6.1-sol | codex | smoke:general_rubric:original | 4 | 0.0 | 0.0831324 | 74.76887909999641 |
| notebook37 | gpt-6.1-sol | codex | smoke:item_checklist:original | 4 | 0.0 | 0.0884764 | 83.97364089998882 |
| notebook37 | gpt-6.1-sol | codex | smoke:item_checklist:polished | 4 | 0.0 | 0.1265656 | 75.18097269999271 |
| notebook37 | gpt-6.1-sol | codex | smoke:own_requirements:original | 1 | 0.0 | 0.0300848 | 32.246891000002506 |
| notebook37 | gpt-6.1-sol | codex | smoke:separate_scoring:original:A | 4 | 0.0 | 0.0732912 | 106.41880649999075 |
| notebook37 | gpt-6.1-sol | codex | smoke:separate_scoring:original:B | 4 | 0.0 | 0.08470240000000001 | 86.18977409999934 |
| notebook37 | gpt-6.1-sol | codex | test:exam_prompt:polished | 263 | 0.0 | 0.9129444 | 1256.0033942999144 |
| notebook37 | gpt-6.1-sol | codex | test:free_form:original | 547 | 0.0 | 1.4231768 | 2269.789479800049 |
| notebook37 | gpt-6.1-sol | codex | test:free_form:polished | 260 | 0.0 | 0.8409139999999999 | 1186.8192951002275 |
| notebook37 | gpt-6.1-sol | codex | test:general_rubric:original | 542 | 0.0 | 1.6780907999999999 | 2766.4614194996684 |
| notebook37 | gpt-6.1-sol | codex | test:item_checklist:original | 558 | 0.0 | 1.63638 | 2722.521663000167 |
| notebook37 | gpt-6.1-sol | codex | test:item_checklist:polished | 253 | 0.0 | 0.825946 | 1255.2887932001759 |
| notebook37 | gpt-6.1-sol | codex | test:own_requirements:original | 134 | 0.0 | 0.6842944 | 1152.0079110001097 |
| notebook37 | gpt-6.1-sol | codex | test:separate_scoring:original:A | 554 | 0.0 | 1.890328 | 3365.722800600066 |
| notebook37 | gpt-6.1-sol | codex | test:separate_scoring:original:B | 523 | 0.0 | 2.101708 | 3575.732220499791 |
| notebook37 | gpt-6.1-sol | codex | transport_check:2026-11-24:Sol | 1 | 0.0 | 0.024294 | 6.573559500015108 |
| notebook37 | ibm-granite/granite-4.2-8b-20260831 | openrouter | capability:Granite 8B | 1 | 5.97e-06 | 0.0 | 1.0531648000032874 |
| notebook37 | ibm-granite/granite-4.2-8b-20260831 | openrouter | development:free_form:original | 26 | 0.00419043 | 0.0 | 195.11941829998977 |
| notebook37 | ibm-granite/granite-4.2-8b-20260831 | openrouter | development:item_checklist:original | 25 | 0.00406188 | 0.0 | 82.44271609999123 |
| notebook37 | ibm-granite/granite-4.2-8b-20260831 | openrouter | smoke:exam_prompt:original | 6 | 0.00094914 | 0.0 | 136.3988524000015 |
| notebook37 | ibm-granite/granite-4.2-8b-20260831 | openrouter | smoke:exam_prompt:polished | 6 | 0.00063141 | 0.0 | 25.052303499993286 |
| notebook37 | ibm-granite/granite-4.2-8b-20260831 | openrouter | smoke:free_form:original | 6 | 0.00094764 | 0.0 | 89.10183099999267 |
| notebook37 | ibm-granite/granite-4.2-8b-20260831 | openrouter | smoke:free_form:polished | 6 | 0.00143592 | 0.0 | 322.0373561999877 |
| notebook37 | ibm-granite/granite-4.2-8b-20260831 | openrouter | smoke:general_rubric:original | 4 | 0.00066612 | 0.0 | 48.59556140001223 |
| notebook37 | ibm-granite/granite-4.2-8b-20260831 | openrouter | smoke:item_checklist:original | 5 | 0.00102459 | 0.0 | 84.13291499998013 |
| notebook37 | ibm-granite/granite-4.2-8b-20260831 | openrouter | smoke:item_checklist:polished | 4 | 0.00074748 | 0.0 | 66.43362760002492 |
| notebook37 | ibm-granite/granite-4.2-8b-20260831 | openrouter | smoke:own_requirements:original | 1 | 0.00013917 | 0.0 | 3.3745494000031613 |
| notebook37 | ibm-granite/granite-4.2-8b-20260831 | openrouter | smoke:separate_scoring:original:A | 4 | 0.0005683800000000001 | 0.0 | 77.97074640000938 |
| notebook37 | ibm-granite/granite-4.2-8b-20260831 | openrouter | smoke:separate_scoring:original:B | 6 | 0.0014487 | 0.0 | 288.7412589999876 |
| notebook37 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:exam_prompt:polished | 129 | 0.023891100000000002 | 0.0 | 868.5796704000823 |
| notebook37 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:free_form:original | 255 | 0.04004826 | 0.0 | 1082.3363827000721 |
| notebook37 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:free_form:polished | 127 | 0.02167593 | 0.0 | 713.3094930000807 |
| notebook37 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:general_rubric:original | 271 | 0.05631576 | 0.0 | 2350.1738918000337 |
| notebook37 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:item_checklist:original | 269 | 0.05335269 | 0.0 | 1787.7420384002035 |
| notebook37 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:item_checklist:polished | 129 | 0.02449851 | 0.0 | 658.6501359998074 |
| notebook37 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:own_requirements:original | 73 | 0.01640214 | 0.0 | 814.1410813997791 |
| notebook37 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:separate_scoring:original:A | 316 | 0.08256615 | 0.0 | 4819.801160899384 |
| notebook37 | ibm-granite/granite-4.2-8b-20260831 | openrouter | test:separate_scoring:original:B | 321 | 0.06732705 | 0.0 | 4681.105697799983 |
| notebook37 | ibm-granite/granite-4.2-8b-20260831 | openrouter | transport_check:2026-11-24:Granite 8B | 1 | 6.09e-06 | 0.0 | 3.4134910000138916 |


## Replay and live commands

From this notebook folder in PowerShell:

```powershell
Remove-Item Env:NB_LIVE -ErrorAction SilentlyContinue
$env:NB_PROFILE='full'
python -X utf8 -E -P -m nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 37_structured_judging.ipynb
```

Replay defaults full and disables requests.Session networking. Every model call is guarded and a cache miss fails; `data/replay_audit.json` must show zero_new_calls=true and unchanged cache counts. Notebook imports no repo helper. The embedded code matches `data/implementation_v1.py` plus `data/pipeline_v1.py`; those `.py` files are engineering sources, not imported during execution.

```powershell
$env:NB_LIVE='1'
$env:NB_PROFILE='full'
python -X utf8 -E -P -m nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 37_structured_judging.ipynb
```

Live without NB_PROFILE is a small development smoke. Full live requires completed smoke/development CSVs and reuses the frozen test checklist, order and polish. It resumes only missing request keys. Keep OPENROUTER_API_KEY in environment; never save it. Helpers select the native npm-packaged codex.exe (0.160.1 verified at Nov24 resume), with prompts on stdin, isolated empty cwd, and no tools; Opus through claude -p headless options. NB_CODEX_EXE may explicitly select the installed binary. Background engineering runners and logs live under ignored data/tmp/. Install requirements-replay.txt if needed. Do not commit scratch runners, HANDOFF.md or the .pyc cache; Claude removes HANDOFF.md before commit. No README.md or PROTOCOL.md was written by Codex.

If stopped for an actual quota: inspect data/quota_stop.json and data/nonfinal_attempts.jsonl, restore quota externally, then archive the stop marker inside data/tmp before explicitly resuming. The historical false-positive marker is archived at data/tmp/quota_stop_false_positive_20261030.json; its evidence is in quota_guard_diagnostic.json. The current guard scans only stderr, explicit error envelopes/events, and failed CLI channels; never successful model content. Never reuse quota-blocked/nonfinal replies as final. Resume missing requests and repeat zero-call replay.

## Surprises and narrative cautions

Smoke observed Sol separate-scoring totals tied on the worked case and chose the worse instruction answer even though its pairwise methods were correct on those four smoke items; inspect smoke_judgments.csv rather than generalizing that sample. Some Granite smoke attempts used the prescribed token-truncation escalation; all63 original smoke pair-condition outputs were ultimately readable under both readers. Complete raw attempts remain costed and preserved in attempt_diagnostics.csv.

The original instructions task already exposes all seven requirements, and all original instruction errors are one-word count violations in long messages. Repeating them is an attention intervention, not new information. The controlled instruction polish uses punctuation only. Original traps are only12 code items. The rubric's clarity scores and the polished claims of verification can conflict with checker correctness; describe actual examples from the exports. Do not claim a checklist was effective merely because it named a check, or name a method winner when scores are at a ceiling or its paired interval spans zero.


Observed outcome-pattern candidate counts:


| purpose | matching |
|---|---|
| end_to_end |  |
| checklist_caught_error | 55 |
| checklist_caught_error | 55 |
| checklist_caught_error | 55 |
| checklist_caught_error | 55 |
| structure_made_worse | 37 |
| structure_made_worse | 37 |
| structure_made_worse | 37 |
| structure_made_worse | 37 |
| rubric_made_worse | 31 |
| rubric_made_worse | 31 |
| rubric_made_worse | 31 |
| rubric_made_worse | 31 |
| typical_success | 285 |
| typical_success | 285 |
| typical_success | 285 |
| typical_success | 285 |
| typical_failure | 124 |

## Supplementary jointly-readable paired diagnostic

Specified during collection after the persistent Sol429 outage was observed; not preregistered before test freeze. Applies uniformly to all judges, conditions and all three readers. Compare each method with baseline (and polished with original) on the same items only when both sides are readable; undecided remains a failure. Primary summaries and paired analyses are unchanged. Conditioning on readability can select a different case mix and cannot repair the availability confound. `post_outage_analysis_record.json` records the specification timestamp and SHA-256 of `readable_analysis_v1.py`, embedded in the notebook. `readable_paired.csv` columns n/full_pair_count/excluded_unreadable identify the effective cohorts; difference_b_minus_a and ci_low/ci_high give paired differences and95% item-bootstrap intervals.

| judge | comparison | method | n | full_pair_count | excluded_unreadable | accuracy_a | accuracy_b | difference_b_minus_a | ci_low | ci_high |
|---|---|---|---|---|---|---|---|---|---|---|
| Sol | method_vs_exam | free_form | 99 | 240 | 141 | 0.9292929292929293 | 0.9292929292929293 | 0.0 | -0.06060606060606061 | 0.06060606060606061 |
| Sol | method_vs_exam | general_rubric | 100 | 240 | 140 | 1.0 | 0.92 | -0.08 | -0.14 | -0.03 |
| Sol | method_vs_exam | item_checklist | 95 | 240 | 145 | 0.9368421052631579 | 0.9263157894736842 | -0.010526315789473684 | -0.07368421052631578 | 0.05263157894736842 |
| Sol | method_vs_exam | separate_scoring | 91 | 240 | 149 | 0.978021978021978 | 0.7252747252747253 | -0.25274725274725274 | -0.3516483516483517 | -0.15384615384615385 |
| Sol | method_vs_exam | own_requirements | 26 | 60 | 34 | 0.9230769230769231 | 0.8076923076923077 | -0.11538461538461539 | -0.2692307692307692 | 0.0 |
| Sol | polished_vs_original | free_form | 17 | 120 | 103 | 0.9411764705882353 | 1.0 | 0.058823529411764705 | 0.0 | 0.17647058823529413 |
| Sol | polished_vs_original | exam_prompt | 58 | 120 | 62 | 1.0 | 0.9655172413793104 | -0.034482758620689655 | -0.08620689655172414 | 0.0 |
| Sol | polished_vs_original | item_checklist | 25 | 120 | 95 | 0.92 | 0.96 | 0.04 | -0.08 | 0.2 |
| Luna | method_vs_exam | free_form | 240 | 240 | 0 | 0.6916666666666667 | 0.6666666666666666 | -0.025 | -0.075 | 0.025 |
| Luna | method_vs_exam | general_rubric | 239 | 240 | 1 | 0.694560669456067 | 0.7238493723849372 | 0.029288702928870293 | -0.02092050209205021 | 0.08368200836820083 |
| Luna | method_vs_exam | item_checklist | 240 | 240 | 0 | 0.6916666666666667 | 0.7125 | 0.020833333333333332 | -0.029166666666666667 | 0.07083333333333333 |
| Luna | method_vs_exam | separate_scoring | 240 | 240 | 0 | 0.6916666666666667 | 0.5625 | -0.12916666666666668 | -0.20833333333333334 | -0.05 |
| Luna | method_vs_exam | own_requirements | 60 | 60 | 0 | 0.5166666666666667 | 0.5333333333333333 | 0.016666666666666666 | -0.15 | 0.16666666666666666 |
| Luna | polished_vs_original | free_form | 120 | 120 | 0 | 0.7083333333333334 | 0.8166666666666667 | 0.10833333333333334 | 0.041666666666666664 | 0.175 |
| Luna | polished_vs_original | exam_prompt | 120 | 120 | 0 | 0.7416666666666667 | 0.8 | 0.058333333333333334 | -0.008333333333333333 | 0.125 |
| Luna | polished_vs_original | item_checklist | 120 | 120 | 0 | 0.725 | 0.8333333333333334 | 0.10833333333333334 | 0.041666666666666664 | 0.175 |
| Granite 8B | method_vs_exam | free_form | 240 | 240 | 0 | 0.5958333333333333 | 0.6041666666666666 | 0.008333333333333333 | -0.0375 | 0.05416666666666667 |
| Granite 8B | method_vs_exam | general_rubric | 237 | 240 | 3 | 0.5991561181434599 | 0.6244725738396625 | 0.02531645569620253 | -0.029535864978902954 | 0.08016877637130802 |
| Granite 8B | method_vs_exam | item_checklist | 239 | 240 | 1 | 0.5983263598326359 | 0.6359832635983264 | 0.03765690376569038 | -0.0041841004184100415 | 0.0794979079497908 |
| Granite 8B | method_vs_exam | separate_scoring | 204 | 240 | 36 | 0.6274509803921569 | 0.2107843137254902 | -0.4166666666666667 | -0.4950980392156863 | -0.3382352941176471 |
| Granite 8B | method_vs_exam | own_requirements | 60 | 60 | 0 | 0.55 | 0.5166666666666667 | -0.03333333333333333 | -0.15 | 0.08333333333333333 |
| Granite 8B | polished_vs_original | free_form | 120 | 120 | 0 | 0.6083333333333333 | 0.6 | -0.008333333333333333 | -0.10833333333333334 | 0.09166666666666666 |
| Granite 8B | polished_vs_original | exam_prompt | 120 | 120 | 0 | 0.6166666666666667 | 0.525 | -0.09166666666666666 | -0.15 | -0.03333333333333333 |
| Granite 8B | polished_vs_original | item_checklist | 119 | 120 | 1 | 0.6470588235294118 | 0.6134453781512605 | -0.03361344537815126 | -0.12605042016806722 | 0.058823529411764705 |


## Manual pause and Nov24 transport amendment

- **2026-10-30 19:07:47 UTC:** Claude stopped the agent and `continue_run.py`/`runner.py` using `taskkill /T /F`, at the owner's request. This was a manual pause, not a quota stop or model failure. The progress log last printed920 rows, while an offline reconstruction on resume found1,517 of4,860 pair-condition verdicts available across all cached requests (including all720 reusable baseline verdicts). Progress depends on shuffled scheduling and is not the count of available baseline rows.
- **2026-11-24:** resumed after25 calendar days. All353 pre-existing JSON/JSONL files under data parsed cleanly. No manual file repairs. All16 frozen hashes and all13 source copies reverified against the moved D: notebook33 checkout at supplied commit cf854303. Source copies remain unchanged; from_33/SOURCE.md already records the D: paths.
- Five started requests had no return: two Codex and three OpenRouter. None is scored or represented by a final reply. Their cache misses are re-requested normally. `resume_validation_20261124.json` preserves the keys. Unknown OpenRouter charges reserveUSD0.00339484 in interrupted_attempts.json; unknown CLI usage is not assigned a fabricated estimate.
- The executable available via ordinary `codex.exe` lookup was obsolete0.142.4. The verified0.160.1 native binary was found inside the installed npm package. The resolver now selects that native executable, without invoking codex.cmd. No prompt, output setting, request key, reader, item or score changed. `resume_transport_amendment_20261124.json` records old/new code hashes. `freeze_record.json` is preserved byte-for-byte; its code hashes are verified against original snapshots in frozen_20261030/, and the current two code files against the explicit amendment hashes. Only executable resolution and this narrow verification exception changed in the frozen helpers after test freeze. The notebook also adds a run-accounting display from collection_periods.json under reproduction; it changes no model call, reader or score.
- Exactly one dated transport check for each of Sol, Luna and Granite passed using the frozen pins/settings and CoreWeave provider with fallback disabled. All returned correct JSON. Both Codex successes also emitted the fail-closed code-mode-host-disabled diagnostic; no tool was used.
- An additional Opus transport check returned `Failed to authenticate: OAuth session expired and could not be refreshed`, with zero model tokens and zero reported cost. This does not establish model discontinuation. All240 checklist records (232 unique test-author requests) and180 Opus quality-audit requests were verified available in cache; no new Opus request was needed to finish. No model substitution. See resume_transport_checks_20261124.json and resume_inventory_20261124.json.
- Per-item resource seconds sum timed CLI/HTTP attempts (and task-only authors where charged); they exclude harness backoff and gate waiting. Collection-period wall times include those waits. Many unpriced CLI error attempts have no returned usage; do not describe an estimated zero as a measured charge.
- The same requested model IDs span two collection periods. CLI pins are not independently immutable; a provider-side update over the25-day gap cannot be ruled out. The design and random job order were fixed before either period. Treat period comparisons as descriptive, not a new causal experiment.
- **Material transport limitation:** the Nov24 Sol calls developed sustained generic HTTP429 errors, with intermittent successes. The error events say `exceeded retry limit, last status: 429 Too Many Requests`; they contain no explicit usage/quota-limit message. Luna's early resumed calls were unaffected. The frozen maximum3-attempt policy (harness waits3s and6s, plus CLI internal retries) was retained. Exhausted errors are cached unreadable `transport_error` outcomes with `provider_rate_limit` diagnostic subtype. They are never wrong answers and are not replaced after seeing results. `collection_periods.json` gives exact affected attempt counts/times; `unreadable_summary.csv`, `attempt_diagnostics.csv`, `judgments.csv` and `summary.csv` give score-level counts. Do not attribute Sol's all-item accuracy collapse to instruction quality: comparison with fully readable historical baseline replies is confounded by transport availability. Readable-only accuracy uses fewer cases and may also differ in item mix. Report the limitation prominently in the narrative.


`data/resume_transport_amendment_20261124.json`:
```json
{
  "at": "2026-11-24T06:06:18.120114+00:00",
  "reason": "Authorized Nov24 resume: select native codex.exe 0.160.1 instead of stale wrapper/PATH binary; original freeze is preserved and explicitly verified alongside narrowly amended transport code.",
  "original_freeze_sha256_lf": "043796c5bab9613f917239b83bc1def838df968f1ab9bda8fd6aa6b4520862e7",
  "scope": "Executable resolution and verification of this transport amendment only. No prompt, request key, model setting, item, checklist, reader or score change.",
  "files": {
    "implementation_v1.py": {
      "before": "df3fe46ef5d34283bd4697723181f63af67f92574d652b4a69045d2e0a400e6b",
      "after": "698ec3837a410f06fb1eff936c87efd814d29bd2098765ca363ad0c276080f17",
      "original_snapshot": "frozen_20261030/implementation_v1.py"
    },
    "pipeline_v1.py": {
      "before": "63d91d453931953af17299a91ab85a487d78acc9693b795578128178e2a564ee",
      "after": "4bbbc79a68ec400a10ac387555085fec07bc3524339b17012ae6876aba7b8a42",
      "original_snapshot": "frozen_20261030/pipeline_v1.py"
    }
  }
}
```

`data/resume_code_validation_20261124.json`:
```json
{
  "at": "2026-11-24T06:14:19.463756+00:00",
  "passed": true,
  "implementation_changes": [
    "new cli_executable resolver",
    "transport exe assignment only"
  ],
  "pipeline_changes": [
    "freeze_test"
  ],
  "all_prompts_readers_scores_model_settings_unchanged": true,
  "model_calls": 0,
  "network_calls": 0
}
```

`data/post_outage_analysis_record.json`:
```json
{
  "at": "2026-11-24T08:22:50.548477+00:00",
  "reason": "Sustained generic Sol429 outage identified during collection. Add conditional paired analysis on the intersection of readable replies for both sides, uniformly for every judge/method/reader and polish comparison. No additional model calls, no primary outcome change, no selection on wrong answers.",
  "status": "Supplementary post-outage diagnostic, not preregistered before test freeze. Conditioning may change case mix; report retained and excluded counts.",
  "file": "data/readable_analysis_v1.py",
  "sha256_lf": "5c4b5ae05563cb962e82e56f2b5a0558ac8f546ebf59c16ddf8fd7738dbc26c7",
  "primary_files_unchanged": [
    "summary.csv",
    "paired_comparisons.csv",
    "polish_paired.csv"
  ],
  "output": "data/readable_paired.csv"
}
```

`data/example_selection_amendment_20261124.json`:
```json
{
  "at": "2026-11-24T08:44:29.466796+00:00",
  "reason": "Existing example selector used not-correct, which includes unreadable replies and undecided ties. Diagnostic examples labelled rescue, worse or typical failure now require lenient_wrong, which is readable and incorrect. Success and unreadable examples retain their rules; plot labels explicitly separate correct/wrong/undecided/unreadable.",
  "scope": "Display and candidate example selection only. Original frozen helpers preserved. No request, reader, score, primary table or model call changed.",
  "source": "data/worked_examples_readable_v1.py",
  "sha256_lf": "00fb79204622420f3e399f495b248ec99af48cdb8376f5c76d75cfaf5c7f8418",
  "original_function_source": "data/pipeline_v1.py worked_examples",
  "outputs": [
    "data/worked_examples.json",
    "figures/worked_cases.png"
  ],
  "initial_draft_sha256_lf": "0a421be44c08c9ea87ce7d53d7ad24b1e4ce4b6ffd9d86fb58c68b7cfa658cc3",
  "refined_at": "2026-11-24T08:45:19.065744+00:00",
  "additional_rule": "Missed-decisive-check examples require audit category absent, not partial. Both absent worked items remain available; partial coverage is reported separately in quality tables."
}
```

`data/figure_display_amendment_20261124.json`:
```json
{
  "at": "2026-11-24T09:23:46.504816+00:00",
  "reason": "Visual inspection found count labels crossing interval bars. Place labels above upper95% endpoints. Main title explicitly flags Sol429 confounding; own requirements axis label says instructions only. No score, request, reader, primary table or model call changed.",
  "file": "data/figure_display_v1.py",
  "sha256_lf": "937319a4a0503674d07cf714b67d94331b1db194e6b3f7934ea4e09917a2ad65",
  "primary_hashes_before_display_change": {
    "judgments.csv": "89a3445b69e100de804d82a40c98567d5835791b85400f627ba03379118a875c",
    "summary.csv": "d921c4ed2501ed86a4a918f8e1d1bff4ee3752c4bc70d8296583ddab2e362677",
    "paired_comparisons.csv": "89583919ee30afbc3fe85e00ecb0ffbff3327cf872f3ca6b830af62bb81701fa",
    "polish_paired.csv": "0a8034742a0424af10dcd521d69f39953eae713b4ab4b9b0f74a03f18bed58cc",
    "family_summary.csv": "36647491de38baced8f65417f8c17f134f3ec73e69791d1e993ab522dd8a2824",
    "trap_summary.csv": "300860839e2aa6e3429424aae92a6eb6dee617badc5a40bbf0c20deaba7d1f06",
    "unreadable_summary.csv": "1783ef5d1d7fd24965d003815c2d52b5e67c92b74de277d3fd90dcf6a40cd367",
    "quality_categories.csv": "ad0f870bb57661cbdba5fae2f27f99b9d0b577601a50b90086829a7ffe2d1754",
    "instruction_coverage.csv": "b9742bd9a3fa440f95fe2ea534774a65bbad75673dd7158153af5381f90dc2cc",
    "resources.csv": "2573dbf066cd8ea56b922f364cc65f57f400da005acc06002d9a8d6ee5600350",
    "readable_paired.csv": "9fbd25df66446a2cd844e608715d469aabb4ebdfa134dccce5df7fc0d284cc87"
  }
}
```

`data/collection_periods.json`:
```json
{
  "at": "2026-11-24T09:20:06.160492+00:00",
  "periods": [
    {
      "date": "2026-10-30",
      "started_attempts": 1716,
      "returned_attempts": 1711,
      "cached_or_nonfinal_attempts": 1711,
      "started_by_model": [
        {
          "backend": "claude",
          "model": "claude-opus-5-5",
          "count": 446
        },
        {
          "backend": "codex",
          "model": "gpt-6-luna",
          "count": 385
        },
        {
          "backend": "codex",
          "model": "gpt-6.1-sol",
          "count": 399
        },
        {
          "backend": "openrouter",
          "model": "ibm-granite/granite-4.2-8b-20260831",
          "count": 486
        }
      ],
      "first_event": "2026-10-30T17:11:29.258338+00:00",
      "last_event": "2026-10-30T19:07:37.507332+00:00",
      "elapsed_event_span_seconds": 6968.248994,
      "serial_returned_latency_seconds": 18847.853842699333
    },
    {
      "date": "2026-11-24",
      "started_attempts": 6155,
      "returned_attempts": 6155,
      "cached_or_nonfinal_attempts": 6155,
      "started_by_model": [
        {
          "backend": "claude",
          "model": "claude-opus-5-5",
          "count": 1
        },
        {
          "backend": "codex",
          "model": "gpt-6-luna",
          "count": 1322
        },
        {
          "backend": "codex",
          "model": "gpt-6.1-sol",
          "count": 3324
        },
        {
          "backend": "openrouter",
          "model": "ibm-granite/granite-4.2-8b-20260831",
          "count": 1508
        }
      ],
      "first_event": "2026-11-24T06:06:30.240805+00:00",
      "last_event": "2026-11-24T09:19:28.005261+00:00",
      "elapsed_event_span_seconds": 11577.764456,
      "serial_returned_latency_seconds": 35319.553780099435
    }
  ],
  "calendar_gap_days": 25,
  "manual_pause_at": "2026-10-30T19:07:47+00:00",
  "initiated_attempts": 7871,
  "returned_attempts": 7866,
  "unknown_manual_attempts": 5,
  "unknown_manual_cli_calls": 2,
  "unknown_manual_openrouter_calls": 3,
  "unknown_cli_cost": "Not estimated: no reply/usage was returned for two manually interrupted CLI calls.",
  "manual_openrouter_reservation_usd": 0.0033948399999999997,
  "outcomes_for_interrupted_requests": 0,
  "active_period_event_spans_seconds": 18546.01345,
  "wall_time_note": "Event spans include backoff and orchestration gaps within each date; exclude the25-day manual pause. Full collection_span_seconds in spend.json includes that pause. Unknown requests remain initiation counts, never scored outcomes.",
  "first_test_period_freeze_to_manual_pause_seconds": 3259.615781,
  "exact_manual_pause_to_collection_resume_seconds": 2113224.514127,
  "resumed_collector_wall_seconds": 11490.664495,
  "main_test_wall_seconds_excluding_manual_pause": 14750.280276000001,
  "timing_basis": "First test period: test freeze to owner-reported manual stop. Resumed collector: logged restart to collection audit after analysis/export. Includes local analysis and provider/backoff waits; excludes checklist author/development phases. Calendar-date difference25 is distinct from exact elapsed gap.",
  "transport_rate_limits": [
    {
      "model": "gpt-6-luna",
      "rate_limited_attempts": 2,
      "first_rate_limit_at": "2026-11-24T07:38:17.159848+00:00",
      "last_rate_limit_at": "2026-11-24T07:38:29.763985+00:00",
      "attempt_counts_by_purpose": {
        "test:general_rubric:original": 2
      }
    },
    {
      "model": "gpt-6.1-sol",
      "rate_limited_attempts": 2928,
      "first_rate_limit_at": "2026-11-24T06:32:55.021505+00:00",
      "last_rate_limit_at": "2026-11-24T09:09:58.118975+00:00",
      "attempt_counts_by_purpose": {
        "test:separate_scoring:original:B": 413,
        "test:free_form:polished": 204,
        "test:item_checklist:original": 463,
        "test:free_form:original": 447,
        "test:exam_prompt:polished": 204,
        "test:item_checklist:polished": 192,
        "test:separate_scoring:original:A": 455,
        "test:own_requirements:original": 108,
        "test:general_rubric:original": 442
      }
    },
    {
      "model": "ibm-granite/granite-4.2-8b-20260831",
      "rate_limited_attempts": 11,
      "first_rate_limit_at": "2026-10-30T17:19:26.540574+00:00",
      "last_rate_limit_at": "2026-10-30T19:04:45.864667+00:00",
      "attempt_counts_by_purpose": {
        "smoke:exam_prompt:original": 1,
        "smoke:free_form:original": 1,
        "smoke:exam_prompt:polished": 2,
        "smoke:free_form:polished": 1,
        "test:item_checklist:original": 4,
        "test:free_form:original": 1,
        "test:free_form:polished": 1
      }
    }
  ],
  "rate_limit_policy": "Frozen maximum3 attempts, with3s then6s harness backoff plus CLI internal retries. Every returned attempt remains cached and costed. Exhausted requests are unreadable outcomes, never wrong answers; no post-hoc replacement of failed replies. Persistent Sol429s materially confound new-condition vs historical baseline comparisons; inspect readable-only scores and per-condition counts. No explicit usage/quota-limit message was observed in these generic429 errors."
}
```

`data/cache_archive_manifest.json`:
```json
{
  "at": "2026-11-24T09:20:32.599740+00:00",
  "archive": "cache_requests.jsonl.gz",
  "rows": 8584,
  "uncompressed_bytes": 129400814,
  "compressed_bytes": 13727931,
  "raw_sha256": "3241292eb4b805686a8790300907879460cdae73b43e476e7ea76eef99ffb40d",
  "archive_sha256": "e21be13481397c8bdeb9eb003a5172f68945ca244b41abb8cd6c01944c9adc52",
  "lossless_verified": true,
  "requires_post_packaging_replay": true
}
```

`data/final_qa.json`:
```json
{
  "at": "2026-11-24T09:24:08.809675+00:00",
  "passed": true,
  "executed_code_cells": 20,
  "error_outputs": 0,
  "judgments": 4860,
  "baseline_reuses": 720,
  "polished_items": 120,
  "source_items": 240,
  "freeze_files_verified": 16,
  "cache_rows": 8584,
  "replay_new_calls": 0,
  "figures": {
    "accuracy.png": {
      "bytes": 179871,
      "sha256": "146815938154321cd499ef4511b30eb491100ddde941c1ca89a98bf1bf2b8652"
    },
    "paired_accuracy.png": {
      "bytes": 97790,
      "sha256": "82c1a557a52e0c7ebe944d6a151881e8364150521517e9d50ae14c00e2fd1ba6"
    },
    "family_accuracy.png": {
      "bytes": 152775,
      "sha256": "564c50298d6f0419c586971e36d194e97d6dd57247903260529717fdbe605ca9"
    },
    "polish_effect.png": {
      "bytes": 75536,
      "sha256": "41621230b241d6750af4093c5a298c832eb21b82313274c0e346cabbeb0b5b9f"
    },
    "outcomes.png": {
      "bytes": 159323,
      "sha256": "5a9d353d2b265fd7972c4a2214efec821684b83c31e7be35e9d1d92bf19ce04d"
    },
    "checklist_quality.png": {
      "bytes": 68512,
      "sha256": "e82742ab6b296627f232faac79f35e9d74c9c4dddb66f2e57ae8e96912f0ee76"
    },
    "worked_cases.png": {
      "bytes": 154519,
      "sha256": "9e20afc2a9bd8b3161c4a03347af8c47d57ebf0e7c4095e35aebdcecc22884b4"
    }
  },
  "openrouter_actual_usd": 0.40290051
}
```
