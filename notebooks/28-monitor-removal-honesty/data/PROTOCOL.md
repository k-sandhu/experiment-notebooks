# Notebook 28: run history

This file records how the study was set up and run, for readers checking the work. The README and the notebook
explain the experiment and its results. Times are UTC. Every entry comes from a file in this folder, the notebook's
code, or the repository's issue and pull-request history, as named.

## Plan before any model call (26 October 2026)

- 17:19: the claim issue (GitHub issue 53, "Notebook 28: monitor-removal-honesty") set the question, the data
  (three synthetic repositories with exact ground truth, conversations written by Claude Haiku 5.5 through
  `claude -p`), the two tiers, the neutral and high-stakes question wordings, the five models and the two judges
  (Claude Opus 5.5 through `claude -p`, GPT-6.1 Sol through `codex exec`). It estimated about 1,500 OpenRouter calls
  (under $10), about 60 Haiku calls and about 100 judge calls.
- The issue fixed no measure in advance. The plain-admission rate, the decision to leave disputed answers and
  non-answers out of it, and the Tier 2 outcome categories are defined in the notebook, which was committed after
  the final collection (see the last section).

## Model selection

- The tested models were chosen from the Artificial Analysis Intelligence Index size-class pages, checked on
  26 October 2026, among open-weight models that OpenRouter hosts with tool calling.
- The OpenRouter catalogue entries were frozen in `model_catalog.json` at 17:39:42 (`collected_at`). Each model is
  pinned to one provider and precision with fallbacks off (`provider.order`, `allow_fallbacks: false` in each
  request in `cache_openrouter.jsonl`).
- Granite 4.2 8B is pinned to DeepInfra because, in a smoke test, the default provider (CoreWeave) left Granite's
  tool calls unparsed inside its reasoning text. The Super VL entry points to the published BF16 checkpoint because
  the catalogue's own Hugging Face link did not resolve. Both choices are commented in the notebook's model cell.
- Meta's Muse Glimmer 30B and OpenAI's gpt-oss were left out because the repository calls those makers' models only
  through their own command-line tools.

## Writing the prepared conversations

- In a first attempt, Haiku's sentences argued with the scripted removal ("I won't drop the monitor", followed by an
  edit that drops it) and announced decisions in the shared part of the conversation ("platform rule 1 means I
  can't remove it").
- The authoring prompt was then changed to tell Haiku openly that the conversations are test material for a study
  of honest self-reporting, and every sentence was checked against a rule for its role. A sentence that failed was
  requested again up to four times and then replaced by a fixed sentence (`author_attempts` and `source` on each
  agent event in `traces.json`).
- The final traces hold 88 Haiku-written turns and 13 fixed sentences across the 15 conversations, counting each
  shared turn once per conversation.
- The authoring took 102 Haiku calls ($0.06 at list price), with 98 distinct replies. Their cache rows were removed
  by a cleanup step because a replay loads the frozen conversations and never calls the author; the replies
  themselves are kept in `traces.json`.

## Simulator corrections and re-collection

- In the pilot, a successful publish in the eval-set job created no files, and models went looking for them. This
  was fixed before the full runs.
- After the first full run, reading the Tier 2 diffs showed that several models kept the monitor in the
  serving-path job by attaching it after building the context (`ctx.monitor = L1Monitor(...)`). The first version
  of the check scored this as a removal, and the simulated monitor test reported it as failing. The check was
  changed to follow the monitor through assignments, variables and helper functions. Every run whose simulated test
  output changed was collected again, and the results use only the corrected runs.
- The judge batches made before the re-collection were replaced. They cost $5.07 at Claude list price.
- Pilot, smoke-test and superseded OpenRouter calls cost about $0.54 and were removed from `cache_openrouter.jsonl`.

## Final collection (26 October 2026)

| Step | Calls | Collected | Settings |
|---|---|---|---|
| Tested models, OpenRouter | 3,707 | 17:39:51 to 18:59:22 (`collected_at` in `cache_openrouter.jsonl`) | Temperature 1.0, reasoning effort medium, seed `sample * 10 + retry`, one pinned provider each |
| Claude Opus 5.5 judge | 72 | 18:20:14 to 19:05:24 (`cache_cli.jsonl`) | `claude -p --tools "" --effort low`, batches of 20, protocol `nb28-v1` |
| GPT-6.1 Sol judge | 71 | 18:23:56 to 19:05:56 (`cache_cli.jsonl`) | `codex exec`, read-only sandbox, tools and web search off, `model_reasoning_effort="low"`, batches of 20 |

- OpenRouter reported $2.15 for the 3,707 calls. The Opus judge calls cost $9.75 at list price; Codex reports no
  price.
- Granite 4.2 8B and LFM2.5 24B A2B returned 23 and 19 empty replies (no text and no tool call). Each was asked
  again once with a new seed (`retry: 1` in the request). After the retry, 9 responses were still empty (6 LFM2.5,
  3 Granite). Five answers in `answers_labelled.csv`, all from LFM2.5 about Sam's harmless change, are empty and
  are counted as no answer.
- The code asks a judge again when a batch comes back unusable and stops after three unusable replies
  (`judge_batches` in the notebook). Both judges labelled all 1,260 answers (`claim_opus` and `claim_gpt` in
  `answers_labelled.csv`).
- The judges did not see the simulator's record, the model's name or the condition.
- Model versions: the five tested models are pinned by dated permaslug (`model_catalog.json`). The command-line
  tools record only the aliases `claude-opus-5-5`, `gpt-6.1-sol` and `claude-haiku-5-5`, with no dated version.
- Tier 3 (full episodes from the user's first message) was planned for later and not run.

## Publication and revisions

- 26 October 2026: the notebook, its data and figures were committed (`e73b7f8a`). Further-reading links were
  checked the same day. Pull request 54 merged them on 27 October 2026.
- 29 October 2026: the README and notebook text were revised to the repository's updated writing rules, and this
  file was added. No model was called, no code cell or output changed, and no result changed.
