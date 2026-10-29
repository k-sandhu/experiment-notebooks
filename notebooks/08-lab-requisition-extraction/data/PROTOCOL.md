# Protocol and run history: notebook 08, lab requisition extraction

This file records the settings and run details behind the notebook, in date order, for readers who want to check
the work. The reader-facing explanation is in `../README.md` and the notebook.

## Analysis plan

No analysis plan was written down before the results were seen. The scoring rules, the measures and the figures are
the ones in the notebook as committed.

## Pages and ground truth (date not recorded)

- 24 synthetic requisition images, made by a synthetic requisition generator that is not part of this repository.
  `data/` does not name the generator, its author or the date the pages were rendered.
- Seeds and record indexes (field `source` in each ground-truth file): seed 4422, records 0 to 9, for
  `form-scan-01` to `form-scan-10`; seed 8424, records 0 to 7, for `form-photo-01` to `form-photo-08`; seed 2284,
  records 0 to 5, for `style-scan-01` to `style-scan-06`. Every file has `source.deterministic: true`.
- Official layout (`layout.variant` `ohip_moh_2026_exact`, template version 1.0.0): form 4422-84, edition 2026-04,
  repository entry last updated 2026-04-20, official PDF SHA-256
  `80932e9d1b1d06efce295f2104a7cc23802eba46a325f0a677f4cac391cfa428` (fields `layout.source_*` and
  `layout.official_pdf_sha256`).
- Simpler layout (`layout.variant` `ontario_style_v1`) for the 6 style scans.
- Images are JPEG, 1,700 x 2,200 pixels at 200 dpi; each ground-truth file records the image's SHA-256, the scan or
  camera settings (rotation, blur, brightness, contrast, JPEG quality, speckle; for photos also orientation,
  quality profile, background, lighting, glare, shadow, perspective and the page-to-image homography), and the
  bounding box and polygon of every annotation in final image pixels.

## Repository history (from git)

- 2026-10-17, commit `2901f83d`: notebook, data, caches and figures first committed, together with notebooks 01 to 07.
- 2026-10-17, commit `1cf89c87`: contents, workflow diagram, call graph and explainers added (markdown only).
- 2026-10-17, commit `5630274b`: future work and further reading added; links checked on 17 October 2026.

The model calls were made before the first commit. Their date and time are not recorded in the caches.

## Run settings

- Prompt: one prompt for every model (notebook section 3), with the output format, the 31 standard test names and
  the marking rule. Each call sends one page image and the prompt.
- Hosted models, called through their command-line tools in an empty temporary folder, timeout 900 s per call:
  - Claude Opus 5.5: `claude -p --model claude-opus-5-5 --tools "" --safe-mode --no-session-persistence
    --input-format stream-json --output-format stream-json --verbose --effort medium`; image sent as base64 in the
    message.
  - GPT-6.1: `codex exec --skip-git-repo-check --ephemeral --ignore-user-config --sandbox read-only -m gpt-6.1-sol
    -c model_reasoning_effort=medium -i <image> --json -`.
  - Muse Wonder: `muse exec --preset empty --no-session-log --disable-web-tools --model muse-wonder-full-1.0
    --reasoning-effort medium --prompt-file <file> --image <image>`.
  - Up to 4 tries per call, with a back-off of 30 s, 60 s, 120 s when the error mentions a rate or usage limit.
  - Parallel workers: 4 for `claude`, 2 for `codex`, 3 for `muse`.
- Open-weight models, through OpenRouter's chat completions endpoint with the image as a base64 data URL,
  temperature 0, `max_tokens` 6,000, timeout 600 s, up to 5 tries per call on HTTP errors, 6 parallel workers. No
  provider was pinned. Requested IDs: `qwen/qwen3.8-flash`, `google/gemma-4-31b-it`,
  `nvidia/nemotron-3.5-super-vl`, `meta/muse-spark-open`. The caches record no dated version for any model.
- Retry rule: when an OpenRouter reply has no JSON object with a `patient` key and used at least 6,000 completion
  tokens, the same request is sent once more with `max_tokens` 20,000, and the second reply is scored.
- Failed calls are not cached, so a re-run retries them. Every cached reply is keyed by the SHA-256 of the full
  request (model, prompt, image digest and, for OpenRouter, `max_tokens`).
- Size knobs: `N_DOCS` (24; 3 with `NB_SMOKE=1`), `CLI_MODELS`, `OPEN_MODELS`.

## Calls and replies

- 72 CLI calls (24 per hosted model) and 104 OpenRouter calls (96 first calls and 8 retries) are in the caches.
- The 8 retried pages, with the completion tokens of the retry (from `cache_openrouter.jsonl`, `usage`):

  | Model | Page | First call | Retry |
  |---|---|---|---|
  | Muse Spark Open | form-scan-05 | 6,000 tokens, no text | 20,000 tokens (11,760 reasoning), no text: unreadable |
  | Muse Spark Open | form-photo-04 | 6,000 tokens, no text | 5,204 tokens, read |
  | Muse Spark Open | form-photo-05 | 6,000 tokens, cut off after 14 characters | 3,596 tokens, read |
  | Muse Spark Open | form-photo-06 | 6,000 tokens, no text | 4,161 tokens, read |
  | Qwen3.8 Flash | form-scan-06 | 6,000 tokens, cut off | 2,732 tokens, read |
  | Qwen3.8 Flash | form-photo-06 | 6,000 tokens, no text | 11,399 tokens (10,841 reasoning), read; listed 24 tests |
  | Nemotron 3.5 Super VL | form-photo-02 | 6,000 tokens, cut off | 8,420 tokens (7,891 reasoning), read; listed 31 tests |
  | Nemotron 3.5 Super VL | form-photo-08 | 6,000 tokens, no text | 6,216 tokens, read |

- 167 of the 168 scored replies contain a JSON object with a `patient` key. The one that does not is Muse Spark Open
  on form-scan-05 (empty text). It is scored as 20 blank details and an empty test list.
- Gemma 4 31B returned the JSON template with all 20 details blank and an empty test list for form-photo-04 and
  form-photo-06. These parse and are scored as read.
- Hosts of the scored OpenRouter replies (field `provider`): Qwen3.8 Flash, Alibaba 24; Gemma 4 31B, ModelRun 24;
  Nemotron 3.5 Super VL, DeepInfra 13, Crusoe 4, Together 3, Venice 2, CoreWeave 2; Muse Spark Open, Fireworks 21,
  Nebius 2, BaseTen 1.
- No model judged another; scoring is the fixed program in notebook section 4.

## Spend

- OpenRouter: $0.6747 over all 104 cached calls (sum of `usage.cost`). The notebook prints $0.536, the cost of the
  scored reply for each page; the first attempts of the 8 retried pages cost $0.1384 more. By model, scored replies
  plus first attempts: Muse Spark Open $0.4307 + $0.1247, Nemotron 3.5 Super VL $0.0471 + $0.0071, Qwen3.8 Flash
  $0.0361 + $0.0066, Gemma 4 31B $0.0224.
- Claude Opus 5.5: $1.422 at list price over 24 calls (`list_cost_usd` in `cache_cli.jsonl`), billed to a
  subscription. GPT-6.1 and Muse Wonder ran on subscriptions and report no price.

## 2026-10-28: text rewrite

The README and the notebook's markdown cells were rewritten to the repository's current writing rules. No model
was called, the notebook was not re-run, and no code cell, output, figure or data file was changed. Counts that the
earlier text did not give (unreadable and blank replies, scores without single pages, results by subset and fill
style, the full OpenRouter spend) were computed from the files in `data/` with read-only scripts.
