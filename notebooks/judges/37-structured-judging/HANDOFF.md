# Notebook 37 engineering handoff

## Status

In progress: collection is resumable from full-request caches.

Written UTC: 2026-10-30T17:55:39.161146+00:00. Final cache entries currently on disk: 1045. Full live collection, replay and final figures remain unfinished until the audit files say otherwise.

Historical first interruption (before the authorized transport correction):

- 720 reused baseline replies.
- 188 of240 item checklists available from 180 unique final author replies; 52 item checklists remain. Partial mapping: data/partial_checklists.json.
- 63 original smoke pair-condition verdicts, all readable under strict and lenient.
- Full test freeze, test judging, quality auditing, full execution/replay, results figures and final headline/error examples remain unfinished.
- No model calls were made while inspecting this interruption.

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
- No extra data generation or difficulty tuning: reuse the fixed level10 exam. Development uses notebook33's24 frozen dev pairs on free form and checklist for each judge, with separate smoke fixtures. Any smoke/development reading issues are reported; prompts are not tuned to test failures.
- Wilson95% intervals for proportions;5000 paired item-bootstrap percentile95% intervals for differences, fixed seed. Exact two-sided sign p-values are exploratory and unadjusted over many comparisons. Main paired comparisons are against the exam prompt; family and original trap subgroups are included.12 original traps, all code, are too few to rank methods. Controlled polish comparisons share items/order but use independent stochastic calls; no same-prompt repeat control exists.
- CLI concurrency2 codex and2 claude; OpenRouter3 per model; no Muse. Full-request per-key locks prevent duplicate in-flight requests. Transport retries only transient429/5xx/capacity/rate-limit and truncation, at most3 attempts. Policy refusals remain unreadable cached outcomes without retry. Usage/quota/credit-limit messages in error channels stop cleanly, keeping blocked and drained requests nonfinal. The pretest2026-10-30 transport amendment excludes successful model content from quota and transient-error matching;13 guard/cache tests pass in transport_amendment_validation.json. The prior false-positive and drained attempts stay in nonfinal_attempts.jsonl and were re-requested normally. OpenRouter guard reserves conservatively before each request and accounts returned usage, including capability/development/smoke. CLI estimates use returned tokens at Sol$2/$10 and Luna$0.10/$0.50 per million with cached input at5%; Claude uses reported CLI list cost. Estimates are not subscription charges.

## Exact planned counts and current cached counts

Main test design: 4860 pair-condition rows;5580 logical judge calls, comprising4860 new calls and720 reused baseline final replies. Per judge: free form240, exam prompt240 reused, general rubric240, item checklist240, separate scoring480 calls for240 pairs, own requirements60; polished free form120, exam prompt120, checklist120. This is1620 new calls plus240 reused per judge. Opus adds240 logical test checklist requests (232 unique task prompts,8 reused because task strings are identical) and180 quality audits. Retries, smoke, development and capabilities are extra and included in the actual ledger below. Do not present planned counts as finished collection when status is incomplete.

Actual final cache entries by model, purpose and origin:

| model | purpose | origin | calls |
|---|---|---|---|
| claude-opus-5-5 | capability:Opus | 37 new | 1 |
| claude-opus-5-5 | smoke:checklist_author | 37 new | 4 |
| claude-opus-5-5 | smoke:checklist_quality | 37 new | 3 |
| claude-opus-5-5 | test:checklist_author | 37 new | 232 |
| gpt-6-luna | capability:Luna | 37 new | 1 |
| gpt-6-luna | smoke:exam_prompt:original | 37 new | 4 |
| gpt-6-luna | smoke:free_form:original | 37 new | 4 |
| gpt-6-luna | smoke:general_rubric:original | 37 new | 4 |
| gpt-6-luna | smoke:item_checklist:original | 37 new | 4 |
| gpt-6-luna | smoke:own_requirements:original | 37 new | 1 |
| gpt-6-luna | smoke:separate_scoring:original:A | 37 new | 4 |
| gpt-6-luna | smoke:separate_scoring:original:B | 37 new | 4 |
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
| gpt-6.1-sol | capability:Sol | 37 new | 1 |
| gpt-6.1-sol | smoke:exam_prompt:original | 37 new | 4 |
| gpt-6.1-sol | smoke:free_form:original | 37 new | 4 |
| gpt-6.1-sol | smoke:general_rubric:original | 37 new | 4 |
| gpt-6.1-sol | smoke:item_checklist:original | 37 new | 4 |
| gpt-6.1-sol | smoke:own_requirements:original | 37 new | 1 |
| gpt-6.1-sol | smoke:separate_scoring:original:A | 37 new | 4 |
| gpt-6.1-sol | smoke:separate_scoring:original:B | 37 new | 4 |
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
| ibm-granite/granite-4.2-8b-20260831 | capability:Granite 8B | 37 new | 1 |
| ibm-granite/granite-4.2-8b-20260831 | smoke:exam_prompt:original | 37 new | 6 |
| ibm-granite/granite-4.2-8b-20260831 | smoke:free_form:original | 37 new | 6 |
| ibm-granite/granite-4.2-8b-20260831 | smoke:general_rubric:original | 37 new | 4 |
| ibm-granite/granite-4.2-8b-20260831 | smoke:item_checklist:original | 37 new | 5 |
| ibm-granite/granite-4.2-8b-20260831 | smoke:own_requirements:original | 37 new | 1 |
| ibm-granite/granite-4.2-8b-20260831 | smoke:separate_scoring:original:A | 37 new | 4 |
| ibm-granite/granite-4.2-8b-20260831 | smoke:separate_scoring:original:B | 37 new | 6 |
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


## Headline numbers and result provenance

`data/summary.csv`: n, correct, wrong, unreadable, undecided, accuracy, ci_low/high, readable_accuracy, ceiling/floor, split by variant/judge/method/parser. Values below are lenient original conditions.


Not available yet.


- `family_summary.csv`: same outcome columns by family; own_requirements has only instructions.
- `paired_comparisons.csv`: judge, condition_a/b, subgroup, parser, n, accuracy_a/b, difference_b_minus_a, ci_low/high, gains/losses, exact_sign_p. Positive difference means the named condition_b improved on exam_prompt. Intervals are unadjusted.
- `polish_paired.csv`: same paired columns, condition_a original and condition_b polished. Positive difference means polishing the worse answer improved judge accuracy; negative means it hurt. Show counts and intervals; do not rank n12 traps.
- `trap_summary.csv`: trap flag, correct/wrong/unreadable/undecided and n. All true traps are code; no cross-family generalization.
- `unreadable_summary.csv`: parser, variant, judge, method, unreadable_type, count. `judgments.csv`: diagnostic_subtype and per-reader reasons, raw cache keys, scores/checks and recovery types. Strict versus lenient results use the identical raw replies. No post-test parser amendment is intended.
- `instruction_coverage.csv`: item_id plus seven boolean rule columns; sum per row is constraints named. `checklist_quality.json` includes full per-item evidence and audit keys; `quality_categories.csv` gives fixed-category counts for each family. Relate coverage to observed rescue/failure without treating it as causal.
- `resources.csv`: judge_calls, checklist_calls, calls_per_item, judge_seconds_per_item, including_checklist_seconds_per_item, costs and reused_judge_calls. Standalone method costs charge checklist construction once per item; run totals count the shared generation only once and separately include quality auditing.
- `date_provenance.json`: item_dates, model cutoffs/releases and sources; event dates in grounded documents are fictional and are not item creation dates.

## Unreadable replies by type


Not available yet.


## Paired headlines


Not available yet.


Controlled polish:


Not available yet.


## Candidate worked examples

Selection is deterministic: first stable sorted rows satisfying each outcome pattern, up to3 per category. All details, exact input, expected winner, checklist, raw replies and every condition are in `data/worked_examples.json`; no absent category is invented.


Not available yet.


## Exact prompts

All template texts are in `data/prompt_templates.json`. Full exact prompts, settings, model IDs, provider payloads and returned replies are in `data/cache_requests.jsonl`, keyed by canonical full-request SHA-256. `checklists_v1.json` holds each task-only question list and author cache key; `baseline_index.json` maps reused originals. `pipeline_v1.py:prompt_for` supplies displayed order. Checklist quality includes only task/checklist and checker decisive evidence, never a prior judge verdict. No outside model HTTP/SDK access is used.

## Models table


| name | pinned_version | provider | access | size | precision | settings | date | date_basis | date_source | why_included |
|---|---|---|---|---|---|---|---|---|---|---|
| Opus | claude-opus-5-5 | Anthropic | claude -p | Not published | Not published | reasoning effort medium; no tools; isolated empty cwd | 2026-09-22 | release | https://www.anthropic.com/claude-opus-5-5 | Top judge writes task-only checklists and audits non-instruction checklist coverage. |
| Sol | gpt-6.1-sol | OpenAI | codex exec | Not published | Not published | reasoning effort medium; no tools; isolated empty cwd | 2026-04-30 | training cutoff | https://developers.openai.com/api/docs/models/gpt-6.1-sol | Strong OpenAI judge and development difficulty check |
| Luna | gpt-6-luna | OpenAI | codex exec | Not published | Not published | reasoning effort medium; no tools; isolated empty cwd | 2026-05-18 | training cutoff | https://developers.openai.com/api/docs/models/gpt-6-luna | Replaces Haiku after provider safety blocks; 0.715 baseline leaves room to improve. |
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


Test freeze has not been written yet. Do not describe the test as run.


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


## Spend and timing


```json
{
  "openrouter_actual_usd": 0.00574971,
  "openrouter_conservative_accounted_usd": 0.04076655,
  "new_cli_calls": 239,
  "cli_estimated_list_usd": 6.49234854,
  "unpriced_cli_calls": 0,
  "imported_baseline_calls": 720,
  "new_calls_this_execution": 0,
  "returned_attempts": 272,
  "collection_span_seconds": 1318.983227,
  "serial_call_seconds": 4033.910252199814,
  "execution_wall_seconds": 2.283881499999552,
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
| notebook37 | claude-opus-5-5 | claude | smoke:checklist_author | 4 | 0.0 | 0.1153232 | 50.18928260001121 |
| notebook37 | claude-opus-5-5 | claude | test:checklist_author | 182 | 0.0 | 5.8293056 | 2241.7033781998907 |
| notebook37 | gpt-6-luna | codex | capability:Luna | 1 | 0.0 | 0.00015604000000000003 | 3.775069800001802 |
| notebook37 | gpt-6-luna | codex | smoke:exam_prompt:original | 4 | 0.0 | 0.0015246600000000002 | 20.94539100000111 |
| notebook37 | gpt-6-luna | codex | smoke:free_form:original | 4 | 0.0 | 0.0034614800000000003 | 22.42493039999681 |
| notebook37 | gpt-6-luna | codex | smoke:general_rubric:original | 4 | 0.0 | 0.0025767200000000002 | 198.3502208999853 |
| notebook37 | gpt-6-luna | codex | smoke:item_checklist:original | 4 | 0.0 | 0.00259522 | 27.78707769999164 |
| notebook37 | gpt-6-luna | codex | smoke:own_requirements:original | 1 | 0.0 | 0.00038024 | 4.261289300004137 |
| notebook37 | gpt-6-luna | codex | smoke:separate_scoring:original:A | 4 | 0.0 | 0.0014880600000000003 | 197.8343228999729 |
| notebook37 | gpt-6-luna | codex | smoke:separate_scoring:original:B | 4 | 0.0 | 0.00241452 | 21.772351499996148 |
| notebook37 | gpt-6.1-sol | codex | capability:Sol | 1 | 0.0 | 0.0032968000000000003 | 6.224045899987686 |
| notebook37 | gpt-6.1-sol | codex | smoke:exam_prompt:original | 4 | 0.0 | 0.0909916 | 49.4509006000153 |
| notebook37 | gpt-6.1-sol | codex | smoke:free_form:original | 4 | 0.0 | 0.0720024 | 65.54818859999068 |
| notebook37 | gpt-6.1-sol | codex | smoke:general_rubric:original | 4 | 0.0 | 0.0831324 | 74.76887909999641 |
| notebook37 | gpt-6.1-sol | codex | smoke:item_checklist:original | 4 | 0.0 | 0.0884764 | 83.97364089998882 |
| notebook37 | gpt-6.1-sol | codex | smoke:own_requirements:original | 1 | 0.0 | 0.0300848 | 32.246891000002506 |
| notebook37 | gpt-6.1-sol | codex | smoke:separate_scoring:original:A | 4 | 0.0 | 0.0732912 | 106.41880649999075 |
| notebook37 | gpt-6.1-sol | codex | smoke:separate_scoring:original:B | 4 | 0.0 | 0.08470240000000001 | 86.18977409999934 |
| notebook37 | ibm-granite/granite-4.2-8b-20260831 | openrouter | capability:Granite 8B | 1 | 5.97e-06 | 0.0 | 1.0531648000032874 |
| notebook37 | ibm-granite/granite-4.2-8b-20260831 | openrouter | smoke:exam_prompt:original | 6 | 0.00094914 | 0.0 | 136.3988524000015 |
| notebook37 | ibm-granite/granite-4.2-8b-20260831 | openrouter | smoke:free_form:original | 6 | 0.00094764 | 0.0 | 89.10183099999267 |
| notebook37 | ibm-granite/granite-4.2-8b-20260831 | openrouter | smoke:general_rubric:original | 4 | 0.00066612 | 0.0 | 48.59556140001223 |
| notebook37 | ibm-granite/granite-4.2-8b-20260831 | openrouter | smoke:item_checklist:original | 5 | 0.00102459 | 0.0 | 84.13291499998013 |
| notebook37 | ibm-granite/granite-4.2-8b-20260831 | openrouter | smoke:own_requirements:original | 1 | 0.00013917 | 0.0 | 3.3745494000031613 |
| notebook37 | ibm-granite/granite-4.2-8b-20260831 | openrouter | smoke:separate_scoring:original:A | 4 | 0.0005683800000000001 | 0.0 | 77.97074640000938 |
| notebook37 | ibm-granite/granite-4.2-8b-20260831 | openrouter | smoke:separate_scoring:original:B | 6 | 0.0014487 | 0.0 | 288.7412589999876 |


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

Live without NB_PROFILE is a small development smoke. Full live requires completed smoke/development CSVs and reuses the frozen test checklist, order and polish. It resumes only missing request keys. Keep OPENROUTER_API_KEY in environment; never save it. Helpers use npm codex.cmd with prompts on stdin, isolated empty cwd, and no tools; Opus through claude -p headless options. Background engineering runners and logs live under ignored data/tmp/. Install requirements-replay.txt if needed. Do not commit scratch runners, HANDOFF.md or the .pyc cache; Claude removes HANDOFF.md before commit. No README.md or PROTOCOL.md was written by Codex.

If stopped for an actual quota: inspect data/quota_stop.json and data/nonfinal_attempts.jsonl, restore quota externally, then archive the stop marker inside data/tmp before explicitly resuming. The historical false-positive marker is archived at data/tmp/quota_stop_false_positive_20261030.json; its evidence is in quota_guard_diagnostic.json. The current guard scans only stderr, explicit error envelopes/events, and failed CLI channels; never successful model content. Never reuse quota-blocked/nonfinal replies as final. Resume missing requests and repeat zero-call replay.

## Surprises and narrative cautions

Smoke observed Sol separate-scoring totals tied on the worked case and chose the worse instruction answer even though its pairwise methods were correct on those four smoke items; inspect smoke_judgments.csv rather than generalizing that sample. Some Granite smoke attempts used the prescribed token-truncation escalation; all63 original smoke pair-condition outputs were ultimately readable under both readers. Complete raw attempts remain costed and preserved in attempt_diagnostics.csv.

The original instructions task already exposes all seven requirements, and all original instruction errors are one-word count violations in long messages. Repeating them is an attention intervention, not new information. The controlled instruction polish uses punctuation only. Original traps are only12 code items. The rubric's clarity scores and the polished claims of verification can conflict with checker correctness; describe actual examples from the exports. Do not claim a checklist was effective merely because it named a check, or name a method winner when scores are at a ceiling or its paired interval spans zero.

