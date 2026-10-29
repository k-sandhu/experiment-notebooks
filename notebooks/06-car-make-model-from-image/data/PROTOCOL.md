# Notebook 06: run settings and history

This file keeps the records someone checking the work may need: how the data was collected, the exact call settings, retries, refusals and what changed later. The README and the notebook explain the experiment itself. Entries are in date order.

## Collection, committed 17 October 2026

The notebook, its photos, both caches and the results files were first committed on 17 October 2026 (commit `2901f83d`, "Add eight self-contained LLM experiment notebooks"). The caches carry no timestamps and `data/` records no retrieval date for the photos, so the collection date is known only to be no later than that commit. Nothing was collected after it.

### Photo set

- Lead images came from the Wikipedia API: `action=query`, `prop=pageprops`, `ppprop=page_image_free`, following redirects, for the English article named in the label list. Titles in the German, French, Italian, Spanish and Dutch editions came from `prop=langlinks` on the English article, and their lead images from the same `pageprops` query on each edition.
- Author, licence, page link and a 960-pixel thumbnail link came from Wikimedia Commons: `prop=imageinfo`, `iiprop=url|extmetadata`, `iiurlwidth=960`. The licence is the `LicenseShortName` field and the author the `Artist` field with HTML removed, cut to 120 characters.
- A file was kept when its licence matched `^(cc[ -]by|cc0|public domain|pd)` (case-insensitive) and its name ended in `.jpg`, `.jpeg` or `.png`. Up to `IMAGES_PER_MODEL = 2` distinct files were kept per car, English first, then German, French, Italian, Spanish and Dutch.
- Each kept file was downloaded from the thumbnail link, converted to RGB, reduced to fit 960 x 960 pixels and saved as JPEG at quality 88 in `data/images/`.
- Requests went 50 titles at a time with a 1-second pause, and downloads 1.5 seconds apart. On HTTP 429 the code waited for the server's `Retry-After` value, capped at 30 seconds, or 5 x 2^attempt seconds. A file the server kept refusing after 4 tries was skipped.
- The result was 146 photos, two for each of the 73 tested cars, recorded in `data/images.csv`.

### Decisions API

- Endpoint `https://openrouter.ai/api/alpha/decisions`, model `openai/gpt-6-luna-decisions`. Responses carry `answers` and `usage` only; no model version or dated identifier was returned or recorded.
- The photo goes in the request's `state` as an `image_url` part holding a base64 data URL, with `detail` set to `high` (full list, make first) or `low` (low detail). The notebook's helper notes stated that an `input_image` part is also accepted but is billed as text tokens and the model does not see the picture, and that this was checked while building the notebook. No record of those check calls is kept in `data/`.
- Questions. Full list and low detail: a `car` choice question over the 109 labels, each option's text being the label itself, with the instruction "Which car make and model is shown in the photo? Choose the single best match.", plus a `body_type` choice question over 8 body styles. Make first: call 1 a `make` choice question over the 28 makers ("Which car manufacturer (make) built the car in the photo?"); call 2 the `car` question over the labels of the two most likely makers (4 to 17 options); each label scored as the maker probability times the label probability.
- Retries: up to 6 tries, with 2^attempt seconds between them, on HTTP 429, 500, 502, 503 and 504. An HTTP 502 whose body contains "refused" is returned as a refusal and cached. Other failures are returned uncached, so a new run retries them. Timeout 180 seconds. 8 calls at a time.
- Cache key: SHA-256 of the JSON (sorted keys) of model, image fingerprint (first 16 hex digits of the file's SHA-256), detail, text (`null`) and questions.
- 584 calls cached: 146 full list, 292 make first, 146 low detail. Every call recorded 0 output tokens and a cost of $0.10 per million input tokens. Total recorded spend: $0.0749 (full list $0.0287, make first $0.0233, low detail $0.0229).
- 3 refusals, each the body `{"error":{"message":"OpenAI refused to answer question \"car\"","code":502}}`: `bmw-i3-it` (full list), `bmw-5-series-de` and `nissan-leaf-en` (low detail). They are scored as misses.

### Command-line models

- Claude Opus 5.5: `claude -p --model claude-opus-5-5 --tools "" --safe-mode --no-session-persistence --input-format stream-json --output-format stream-json --verbose --effort <medium|low>`, with the image as a base64 content block in one stream-JSON user message. Effort `low` for the 146 annotation calls, `medium` for the 146 identification calls.
- GPT-6.1: `codex exec --skip-git-repo-check --ephemeral --ignore-user-config --sandbox read-only -m gpt-6.1-sol -c model_reasoning_effort=medium -i <image> --json -`, with the prompt on standard input.
- Muse Wonder: `muse exec --preset empty --no-session-log --disable-web-tools --model muse-wonder-full-1.0 --reasoning-effort medium --prompt-file <file> --image <image>`.
- All three ran from an empty temporary folder with a 900-second timeout, up to 4 tries, and a wait of 30 x 2^attempt seconds when the error mentioned 429, a rate limit or a usage limit. Failed calls are not cached. 4 Claude, 2 Codex and 3 Muse calls ran at a time.
- Cache key: SHA-256 of backend, model, effort, system prompt (`null`), prompt and image fingerprints.
- 584 calls cached: 146 annotation calls and 146 identification calls for each of the three models. None failed in the final cache. None of the three tools returned a dated model version.
- Recorded usage: Claude's `total_cost_usd`, stored as `list_cost_usd`, totals $5.64 ($2.28 annotation, $3.36 identification), billed to the subscription. Codex's `usage` sums to 2,682,907 `input_tokens` and 7,180 `output_tokens` over 146 calls, with no price. Muse recorded no usage.

### Reading the replies

- Annotation: the first JSON object with a `view` key. 114 of the 146 replies were not bare JSON (mostly a code fence around it); all 146 were read.
- Identification: the first JSON object with a `top3` key; labels not on the list are dropped, and a reply with no listed label would count as unreadable. None did. Two Claude replies had text outside the JSON: `subaru-outback-en` (a sentence naming a Forester before the JSON) and `volkswagen-polo-en`, whose first JSON object listed "Seat Ibiza" third and was followed by a corrected object; the parser used the first object and dropped "Seat Ibiza". GPT-6.1 named an off-list third label five times: Mercedes-Benz V-Class (`mercedes-benz-sprinter-en`), Kia Sorento (`kia-sportage-en`), Porsche Cayman (`porsche-911-de`), Volkswagen Touareg (`porsche-cayenne-en`) and Toyota iQ (`smart-fortwo-fr`). No first answer was affected.

### Scoring

- Top-1, top-3 and make accuracy over all 146 photos, with refusals as misses. The notebook's interval is a bootstrap over 2,000 resamples (seed 0).
- Calibration error uses ten equal confidence bands; the reliability chart draws five bands and only those with at least 5 photos.
- The auto-accept table uses the levels 0, 0.5, 0.7, 0.9 and 0.97, set in the notebook's code for the best-scoring Decisions method (the full list).
- No record says whether the scoring rules or the levels were fixed before the results were seen. Treat the analysis as not registered in advance.

## Later edits on 17 October 2026

- Commit `1cf89c87` added the contents list, workflow diagram, call graph and explainers (markdown only).
- Commit `5630274b` added the future work and further reading section. Its links were checked on 17 October 2026.

## Text rewrite, 28 October 2026

- The README and the notebook's markdown cells were rewritten to the repository's writing rules. No code cell, output, figure or data file changed, no model was called, and the spend was $0.
- New counts in the text were computed read-only from the caches. Each cache key was rebuilt from the notebook's request format, and all 584 Decisions and 584 command-line entries matched an image and method. The counts are: Wilson intervals; unreadable replies apart from wrong answers; top-1 on readable replies; the split by legible logo; the make-first auto-accept table; paired McNemar tests; results on the close-ups and collages; years in the Commons file names; and the format deviations listed above.
- Opening the 8 photos the annotation marks as "other" view showed 4 close-ups of a badge or logo (`ford-mustang-fr`, `chevrolet-corvette-it`, `bmw-5-series-de`, `bmw-i3-it`) and 4 collages of several generations (`mercedes-benz-c-class-fr`, `mercedes-benz-e-class-fr`, `land-rover-range-rover-fr`, `renault-clio-fr`). The earlier text described two badge close-ups.
- The file name of `audi-a4-de` (`Audi_80L_2-door_(ca_1975)_B1.JPG`) shows an Audi 80 filed under Audi A4.
- Figures were left unchanged. Problems to fix on a re-run: the accuracy chart's title names one of two tied models as best, its legend covers the low-detail bar, and its bootstrap intervals cannot show uncertainty at 100%; the badge chart is not saved to `figures/` and has no logo split; the misses grid does not mark sibling-model errors; the calibration chart's right panel starts its vertical axis at 0.80.
