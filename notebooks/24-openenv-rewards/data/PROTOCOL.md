# Notebook 24 protocol history

This file records how the collection was run, in date order, for readers who want to check the work. The
reader-facing explanation is in the notebook and `README.md`. Times are Toronto time (UTC-4) as recorded in the
data files.

## Protocol version and fixed settings

- Protocol label `openenv-rewards-v1.1`. It is part of every cache key, so a change of protocol cannot reuse
  old responses.
- Environments: OpenEnv 0.10.0 at commit `21fbb0ecb2a3e74110b59cf38a1b195decc75c88`, with the official maze
  and Reasoning Gym environment packages from that commit; `reasoning-gym` 0.1.25. Servers run on 127.0.0.1
  through OpenEnv's own server factory and WebSocket clients, CPU only, no Docker (`provenance.json`,
  `manifest.json`, `requirements.txt`).
- Models through OpenRouter: `meta-llama/llama-3.2-3b-instruct` pinned to Parasail (BF16) and
  `google/gemma-3-4b-it` pinned to DeepInfra (BF16), with `allow_fallbacks: false` and
  `require_parameters: true`. OpenRouter returned the undated slugs, so no dated version was recorded.
  Hugging Face model-card revisions checked on 2026-10-24: Llama `0cb88a4f764b7a12671c53f0838cd831a0843b95`,
  Gemma `093f9f388b31de276ce2de164bdc2081324b9767`.
- Sampling: temperature 0.9, top-p 1.0. Maze moves: 48 output tokens and a strict JSON schema allowing only
  `{"action": 0..3}`. Questions: 256 output tokens, free text. Seeds: `202610240 + attempt number`, plus 1000 in
  the second round, plus `10000 x move number` within a maze attempt. Token probabilities requested for Llama
  only, because DeepInfra does not support them for Gemma.
- Size settings: 4 mazes, 4 questions, 4 attempts per group, 2 second-round tasks per model, 10 moves per maze.
  Caps: 96 attempts, 600 requests, $2.00 of accounted spend. Before each paid request the code reserved a
  conservative cost bound and refused to send if a cap would be exceeded.
- Early-stop rule (code name SARA): at least 2 attempts; stop when outcomes mix; give up when the estimated
  chance of a mixed group of four, `(4 - n) / 5` after `n` identical outcomes, falls below 0.30. The notebook
  describes this threshold as set before collection. No separate preregistration file exists.
- Score-guided choice (code name RIDGE): estimates `(successes + 0.5) / (4 + 1)`; target the mean estimate of the
  model's mixed tasks (tolerance at least 0.05), or 0.5 with tolerance 0.15 when there are none; score divided by
  mean calls per attempt; two tasks drawn without replacement using random keys from seed
  `2026102480 + model index`; the target moves only when a new mixed group appears.
- Coverage bonus (code name CovGPO): share of moves reaching a new square; applied only to all-failed maze groups
  whose coverage spread is at least 1e-6; scale 0.25.

## 2026-10-24

1. Source checks. The Hugging Face announcement, the OpenEnv release and the method papers were opened and
   recorded in `research_sources.json` (all HTTP 200). Model release dates, licences and the Llama
   knowledge cutoff were recorded in `provenance.json`. Snapshots of the OpenRouter catalogue
   (`model_catalogue.json`), the two models' provider lists (`endpoints_*.json`) and one page of the Hub dataset
   listing (`hub_catalogue.json`, 200 entries, 43 tagged `openenv`) were frozen.
2. 09:21. The 8 tasks were generated with seeds 2026102400 to 2026102403 (mazes) and 2026102410 to 2026102413
   (questions) and frozen in `tasks.json` with a SHA-256 hash each. All 8 were solved through the environments
   with the known answers before any model call (`environment_smoke.json`).
3. 09:21. Two setup requests, saved in `pilot_cache/` and excluded from all results:
   - Llama on Parasail, asked to "Return ONLY one digit 0, 1, 2, or 3" with a 16-token limit, replied in prose
     and stopped at the limit (`finish_reason: length`).
   - Gemma on Parasail returned HTTP 429 (rate limited upstream).

   Changes made before the measured collection: maze replies became schema-constrained JSON with the example
   `{"action": 3}` and a 48-token limit for both models, and Gemma was pinned to DeepInfra, which does not return
   token probabilities.
4. 09:22 to 09:27. Measured collection, in one run: 64 first-round attempts (fixed plan), then the score-guided
   choice, then 16 second-round attempts. 336 requests in total (320 first round, 16 second round).
   - 6 requests returned HTTP 429 from Parasail serving Llama, at 09:24:21, 09:24:37, 09:25:04, 09:25:37 (two)
     and 09:25:53. Each ended its attempt as a provider error. None was retried or repaired. The error bodies'
     `user_id` field was removed before saving and the removal is recorded in each cache file
     (`redacted_fields`).
   - No reply was empty, cut off or unreadable: all 330 replies ended with `finish_reason: stop`.
5. Spend, including the setup requests: $0.01531127 reported by OpenRouter for 331 requests, plus a conservative
   bound of $0.00186659 for the 7 failed requests that reported no cost. Prompt tokens 294,780; completion
   tokens 3,034; summed request time 234.1 seconds (`manifest.json`).
6. Replay check (`validation.json`): 14 code cells executed with 0 errors, 0 new model requests and 336 cache
   hits; 8 environment checks and 80 per-attempt reward audits passed; 24 local links and 6 figures checked.
7. Commits: `624cf85d` (09:53) added the notebook and data; `3e0b63b1` (09:56) added `.gitattributes` so file
   hashes match across platforms; `2ce5c428` (15:33) rewrote the introductions as text only.

## 2026-10-28

Text-only rewrite of `README.md` and the notebook's markdown cells. No code cell, output, figure or data file
changed, and no model was called. Counts added to the text were recomputed from `episodes.jsonl`,
`sara_decisions.jsonl`, `hub_catalogue.json` and the cache files with a read-only script. The method papers and
further-reading links were opened again on this date.
