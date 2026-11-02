# Protocol history

## 2026-11-01, before smoke generations

The owner changed every model's effort from low to high. This supersedes the initial study plan. Models are `gpt-6.1-sol`, `gpt-6.1-terra`, `claude-opus-5-5`, and `claude-sonnet-5-5`, called only with `codex exec` and `claude -p`. No direct generation APIs or SDKs are used.

Smoke: one complete public article, five independent invocations per model, 20 generations. The source is the October 29 Hugging Face article about Mistral Large 4. Its title and full body, including code, are supplied without editorial shortening. A longer article was chosen so that caching can be measured above providers' documented minimum lengths without adding padding to the prompt. Source text is local and git-ignored; the URL, retrieval time, extraction rule and hashes are public in `article.json`. Smoke is excluded from the main confirmatory sample; replace its topic before the later 20-topic study.

Exact prompt:

```text
Write a LinkedIn post based on the following article.

<article>
{{complete_article_text}}
</article>
```

The optional CLI base prompt is the same neutral line for all models: `You are a helpful assistant.` No writing, audience, length, formatting, novelty or variation instructions are added. Default supported sampling behaviour is preserved. High is a named setting, not a claim of equal computation. No resumed conversations, previous posts or correction messages are supplied.

### Cache amendment before collection

The owner asked to measure and maximise provider-side prefix-cache reuse. This replaces the initial plan's per-request randomisation with randomised model/article blocks: each block contains all five fresh requests consecutively. Block order uses seed 20261101. The first response completes before the next request starts, allowing its cache write to become available. Identical prompt bytes, system text, effort, CLI options, cwd and tool configuration are retained within a block. Run identifiers and replicate numbers stay in the local ledger, never the model prompt. No artificial source padding or prior assistant output is added. No extra warm-up generation is made. CLI-supported caching is used; unavailable API cache controls will not be added through an HTTP workaround.

For each generation retain the raw provider usage, cache reads, cache writes, ordinary input, total input, output, wall time and reported cost. For Claude the common input denominator is ordinary input + cache reads + cache writes. For Codex it is the reported inclusive input count. Report aggregate read tokens / aggregate input tokens, plus the same rate for requests 2-5. Missing counters stay null. Latency is not evidence of a cache hit. The first request is called initial rather than assumed cold, because an existing provider cache is possible. Provider caching reuses input computation; every replicate still requires a new model response. Local replay is separate and never counted as a new generation or provider hit.

### Isolation and limits

Run outside the repository with no project instructions loaded. Disable web search, command tools, browser/computer/image tools, connectors, MCP, plugins, hooks, multi-agent operation, memories and skill discovery through CLI controls. Clear inherited CLI session variables and API-key environment variables from child process environments; retain ordinary CLI authentication. No secret contents are logged.

Local preflight found that Codex's debug context still exposes mandatory runtime skill-catalogue/team directives and environment context despite feature disables. It contains no repository editorial rules. This residual cannot be described as an identical pure chat system prompt. Codex JSONL does not expose a complete advertised tool catalogue; disabled feature settings and absence of tool events are distinct checks. Claude's initial event exposes its tool catalogue and is required to contain no tools, MCP servers, skills or plugins. Any observed tool activity or nonempty Claude catalogue stops collection. This is a limitation to resolve before a strictly tool-free main comparison, not permission to silently call tools.

No automatic retry of content, refusal or malformed output. Keep failed requests and stop to diagnose. Maximum 20 new successful-generation slots; per-call CLI timeout 240 seconds; Claude's per-call dollar limit is $1.00. The claim issue's $10 smoke estimate is a planning envelope, not an enforceable Codex billing cap, because Codex does not offer the same per-call dollar limit. Record unknown dollar usage as unknown, never zero. The main 400-post collection is not authorised by this smoke-only implementation step.

### Frozen prose inventory and engineering gates

Freeze `prose_lexicon.json` before the first model call. Vocabulary and phrase candidates come from this repository's editorial watchlist; the two linked research papers motivate lexical analysis, but do not establish that every listed phrase is overused by these four models or on LinkedIn. Additional LinkedIn phrases and structure regexes are investigator hypotheses. Report zero counts as well as positive counts, words per denominator, post incidence, location and source occurrences. These are descriptive signals, not an authorship detector or automatic quality penalty. Patterns that need meaning or grammatical judgment require later contextual review.

The source overlap count is available when the local full article is present; saved count tables support offline replay without redistributing the article. Never count source-derived stock language as an independent model signature without examining it.

Smoke gates: 20 readable final posts, five distinct exact and whitespace/case-normalised outputs per model, one shared user-prompt hash, distinct session IDs, no observed tools, and successful cache/usage extraction or explicit unavailable values. Pairwise word-sequence similarity and word-trigram overlap describe near reuse. Identical responses would trigger a diagnosis of local caching, CLI resume, prompt stability and provider behaviour; do not add novelty instructions simply to make the test pass. Five distinct outputs do not prove independence or rule out future duplicates.

Primary smoke purpose is engineering. One source cannot establish cross-topic habits, family effects, quality rankings or engagement. Its observed phrases may be used to debug extraction, but not to redefine the main study's preregistered watchlist after looking at results without a labelled amendment.

Documentation checked 2026-11-01:

- https://learn.chatgpt.com/docs/config-file/config-reference
- https://developers.openai.com/api/docs/guides/prompt-caching
- https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- https://arxiv.org/abs/2406.07016
- https://arxiv.org/abs/2412.11385

## 2026-11-01, diagnostic v1 and v2 amendment

The first Opus request returned a readable post and no tools/MCP servers, but the harness stopped because the init event listed built-in skills and three built-in plugins even with safe mode. Its output, usage ($0.078204 reported) and initial configuration remain under `data/diagnostics/v1-claude-builtins/` and are excluded from the 20-post v2 smoke. No external tool was called.

V2 adds `--disable-slash-commands`, documented by the installed CLI as disabling all skills. Catalogue assertions distinguish executable tools/MCP from built-in inventory labels. Built-in plugin/skill labels that remain despite this switch are disclosed, never described as absent. No user-installed plugin or optional skill is enabled; no skills can be invoked through a model tool or slash command. The first v2 request may reuse the diagnostic's provider cache, so it is not assumed cold. Tool/MCP catalogue and observed call checks remain mandatory. The additional diagnostic is included in total spend and excluded from the planned 20 valid v2 slots.

## 2026-11-01, Codex configuration correction

After five successful v2 Opus generations, Codex rejected `tools.view_image=false` as an unknown configuration field under `--strict-config`, before generation. The official reference and installed binary differ on that field. Remove it and retain the supported `--disable view_image` feature switch. Preserve the failed launch under `data/diagnostics/v2-codex-config-rejection/`; no provider usage was returned. No Opus request, prompt, source, effort, phrase rule or cached output is changed.

## 2026-11-01, warning-parser correction from saved output

Terra's first successful response contained two `item.completed` records of type `error`: one warned about the experimental host-skill discovery flag, the other reported that Code Mode was unavailable because its host was disabled. Neither is a tool invocation. The initial parser incorrectly classified both as tool events and stopped. Preserve the initial classification in `data/diagnostics/parser-v1-classification.json`, separate these records into `cli_warnings`, and reparse the identical raw JSONL without another generation. Old parser: one flagged Terra response with two supposed tool events. Corrected parser: zero tool events, two CLI warnings, one readable response. A regression test covers this boundary. Failing closed on Code Mode is intended in this experiment. These settings and the original response remain unchanged.

## 2026-11-01, response-boundary amendment after all 20 outputs

All ten Claude outputs contain an editorial note after a horizontal rule concerning the source's 49B active-parameter prose versus A52B checkpoint name. Five Sonnet outputs and one Opus output also include a literal LinkedIn-post wrapper. The first location extractor treated these as opening/closing prose. Preserve the original lexical/location tables under `data/diagnostics/location-parser-v1/`, then separate only the observed literal wrappers and final horizontal-rule-delimited notes starting with Note, One note, The article, I left out or Before posting. Keep raw response, proposed post body and editorial note distinct. Count wrappers and notes explicitly as response-formatting habits. No response is deleted or rewritten. Exact-output hashes still describe raw final responses; add a separate post-body uniqueness check. This is a post-observation parser amendment, not a preregistered finding about writing quality. The fixed 111-entry lexicon remains unchanged.

## 2026-11-01, requested conversation-condition smoke, before new generations

After seeing the fresh-session cache results, the owner proposed sending subsequent requests to the same model within a single conversation. Add a separate 20-generation sensitivity condition: one new persistent conversation per model, five turns, the exact full article and instruction repeated in each user turn. Keep the completed fresh-session arm intact. Claude removes `--no-session-persistence` and uses `--resume <explicit session ID>`; Codex removes `--ephemeral` and uses `codex exec resume <explicit session ID>`. Never resume an unrelated or last session. Retain high effort and all isolation flags. Assert that the session ID stays constant within each model block. Save under `data/conversation/`.

This condition changes what the model can see: previous requests and assistant posts remain in context. It may change wording through imitation or deliberate variation, so do not pool it with fresh sessions or call it independent sampling. It also increases total input as history grows. Compare total reported input, cache reads/writes, ordinary input, output, latency and cost alongside percentages. Do not claim a higher hit fraction necessarily means a lower bill. Verify whether resumed CLI usage/cost fields are per-turn or cumulative before summing. These smoke arms use the same topic and occur in a fixed sequence, so cache state and execution order are not independently randomised; they are an engineering comparison, not a causal estimate of caching benefits. Main-study choices remain separate from this sensitivity test.

## 2026-11-01, exact short follow-up instruction

The owner clarified that subsequent conversation turns must contain only `Generate another post.` The initial turn alone includes the complete article. This supersedes the just-started repeated-full-article conversation condition. Two Opus turns from that superseded condition had completed before it was stopped; they are preserved under `data/diagnostics/superseded-full-article-conversation/` and excluded from the requested comparison. A third Opus request was interrupted during generation; its final provider usage/cost was not captured and is unknown, not zero. Record this interrupted attempt in the spend limitations. Start a new conversation for the requested short-follow-up condition so that the invalid second turn cannot affect later outputs.

For each model create one new persistent conversation. Turn 1: original minimal instruction plus complete article. Turns 2-5: exactly `Generate another post.` No repeated article, novelty advice, feedback or other text is appended. The CLI carries prior conversation history. Cache metrics and costs must use the actual growing input, not the short new user message alone. A started-at ledger is now written before each launch to make interruptions visible. The fresh-session comparison remains unchanged.

## 2026-11-01, resumed-counter scope verified

The resumed CLI counters have different scopes. Claude's result `usage` is per invocation, while `total_cost_usd` and `modelUsage.costUSD` accumulate across the saved session. Codex `turn.completed.usage` accumulates input, cache reads, output and reasoning across the saved session. Summing those raw resumed counters would overcount earlier turns. Preserve the native counters and derive per-turn increments by differencing within the same session. Verify Codex increments against its local rollout `token_count.info.last_token_usage` records, extracting only counters rather than full source-containing logs. The raw JSONL remains unchanged. Fresh-session counters need no subtraction. Claude dollar values are CLI list-price equivalents, not proof of an additional subscription charge.

Sentence-boundary parsing was also corrected so a trailing emoji after a question does not become the apparent closing sentence. Emoji-prefixed lines are counted separately from Markdown bullet markers; an emoji prefix is not automatically treated as a list item. These are deterministic extraction rules with regression fixtures, not model failures.

## 2026-11-01, completed smoke and replay validation

Completed 20 fresh-session responses and 20 responses under the requested short-follow-up conversation condition. Every model has five distinct normalised raw responses and five distinct post bodies in each condition. Fresh sessions have 20 distinct IDs; continued turns retain one ID per model. No tool invocation was observed. The exact initial prompt and the three-word follow-up hashes match their conditions.

Weighted cached-input shares on requests/turns 2-5 are: Sol 0% fresh versus 48.3891% continued; Terra 49.4635% versus 98.2600%; Opus 99.9713% versus 89.4302%; Sonnet 99.9713% versus 89.3360%. Both Codex models' per-turn counter differences match all ten native last-turn usage records. These results do not establish a causal cache saving because conditions ran in order and backend cache state is uncontrolled.

Nine regression fixtures pass. Strict offline replay with the full article absent and subprocess/network calls blocked reproduced all 12 CSV tables byte-for-byte. The notebook executes top to bottom from saved evidence with no model calls. Saved figures were visually inspected. The main 20-topic collection remains unrun; it will use one separate conversation per model/article, the full initial article, and exactly Generate another post. on turns 2-5, as requested. This smoke topic is excluded from later confirmation.

## 2026-11-01, full-run authorisation and preregistration

The owner explicitly authorised the full 20-topic run. Freeze the 20 source articles in `data/main/articles.json` before generation; keep complete extracted bodies locally in `data/local_inputs/main/`, with source URLs, dates, extraction selectors and hashes public. Remove navigation, related-story widgets and accessibility-only text, retain article paragraphs, lists, code, captions and corrections. The Mistral smoke article is excluded and replaced by the October 30 community-safeguards announcement. All items were published October 23-30, inside the requested recent-news window and after the model cutoff/release thresholds already recorded.

The initial extraction diagnostic contained inline-link line breaks and some navigation/related-story widgets. These were corrected and all bodies checked before preregistration or any main model call. Initial extraction metadata remains under `data/main/extraction_diagnostic.json`; it contains no scored model responses.

Main design: four fixed requested models, high effort, 20 independent article-specific conversations per model, five posts per conversation. Turn 1 receives the original minimal prompt and full article; turns 2-5 receive exactly `Generate another post.` All 400 main outputs are new generations. Existing smoke posts are excluded. One worker per model may run concurrently with other model workers; within each article/model block calls stay sequential and retain an explicit conversation ID. CLI context files are initialised once to avoid concurrent writes, and optional tool/skill/connector settings remain the smoke-tested settings. Runtime scaffolding limitations continue to apply.

Freeze the prior 111-entry inventory and a seeded 10-topic discovery / 10-topic confirmation split. Preregister cross-topic phrase thresholds, source-overlap checks, article-cluster uncertainty and failure handling in `data/main/preregistration.json`. The complete input is never padded for caching. Report cache reads/writes and inclusive input, differencing cumulative counters as verified in the smoke. Report missing dollar equivalents as unknown. The 400-generation cap and Claude per-call $1 limit apply; no paid judge model is added. No generation is discarded for repetitive or poor writing.

## 2026-11-01, collector default and full-run reporting

The explicitly authorised full collection began with a 400-new-call allowance. After launch, the saved collector's ordinary default was reduced to five calls; the already running process retains its registered 400-call allowance. Future full collection must explicitly pass `--max-new 400`. This changes no source, prompt, model setting, cached response or analysis threshold.

The main analysis replays raw saved responses, retains the fixed 111-entry inventory and requires the preregistered discovery/confirmation support before calling a phrase confirmed. It also provides both member models' counts for family comparisons. The smoke-only README/notebook presentation is replaced by one report of the full run; earlier smoke caches and protocol records remain intact. An inspected first-person attribution case is presented as an editing risk, not as a new numeric quality metric or a model ranking.

## 2026-11-01, completed full run and validation

Exactly 400 new main CLI invocations completed successfully: 20 article topics, four models, five posts per model/article conversation. All 400 responses were readable, all four models have 100 distinct normalised post bodies, and no tool invocation was observed. All 80 explicit conversation IDs remained constant within their five-turn blocks. Every turn-1 input matches its frozen complete article prompt; all 320 later turns match exactly Generate another post. All requested model efforts are high. There were no failed requests, content retries or fallback models in the main run.

Main follow-up cache-read fractions (weighted input-token counts, turns 2-5): Sol 76.0395%, Terra 90.7416%, Opus 83.4107%, Sonnet 83.5240%. The native last-turn token records independently verify all 200 Codex increments across 40 conversations. Main Claude list-price equivalents sum to $3.9388603; Codex dollar equivalents and actual total spend remain unavailable. Smoke and diagnostics are separate.

Fifteen regression tests pass. Offline replay with all full source articles absent and network/subprocess operations blocked reproduces all 11 main CSV tables byte-for-byte. The self-contained notebook executes top to bottom from caches. Four main figures were visually inspected. The full report uses one current summary and results narrative; smoke data are preserved only as design/audit evidence. No human quality scores, factual accuracy rate or LinkedIn engagement outcome was collected.
