# Data, dates and licences

The primary inputs are fresh synthetic records generated in the notebook on 2026-10-20 (America/Toronto). They are fictional and contain no private information. The generator code, authored templates, records and exact labels use the repository MIT licence. No model call generates the test items or gold labels. The coding assistant authored the templates, so wording bias remains possible.

The pilot uses a different seed namespace from the held-out test. Both members of each pair share one opaque record reference and choice order. No gold labels, split names, seed numbers or difficulty fields are included in primary requests.

Model responses are collected through the authorized OpenRouter Decisions endpoint and saved as evaluation evidence. Provider terms apply to the service and its outputs. This folder redistributes no model weights.

The endpoint catalogs are frozen in model_catalog.json, including source URLs and retrieval timestamps. Model dates, sources, pins and the fresh-data rule are in model_dates.json. OpenAI's base GPT-6 Luna cutoff is 2026-05-18; the other models do not publish a cutoff in these sources, so release dates are recorded as the fallback. All evaluation records were authored after the listed releases. Clef Flash exposes no dated permaslug; its PrimeIntellect provider is pinned, while checkpoint immutability remains unverified.

Primary sources checked on 2026-10-20:

- [OpenAI Decisions guide](https://developers.openai.com/api/docs/guides/decisions).
- [GPT-6 Luna model and cutoff](https://developers.openai.com/api/docs/models/gpt-6-luna).
- [OpenRouter Decisions request schema](https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-request).
- [Jev 1.14](https://openrouter.ai/typesafe/jev-1.14).
- [Mercury Decide](https://openrouter.ai/inception/mercury-decide).
- [Clef Flash](https://openrouter.ai/cloudflare/clef-flash).

The initial severity diagnostic used references containing the gold level. That diagnostic was rejected and replaced with opaque references for all providers. The initial inputs and raw attempts are retained for the spend audit; only severity_cases_v2.json is analyzed in the final diagnostic. No primary item was removed or replaced.

Returned choice probability vectors whose sum is within 0.02 of one are normalized for analysis. This scoring correction was applied uniformly after discovering a Jev vector summing to 0.99. Raw responses and original requests are preserved.
