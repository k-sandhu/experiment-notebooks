# Follow-up data and interpretation

The new fixtures were generated in Python for this experiment on 2026-10-20 (America/Toronto), using the repository MIT licence. No model call generates the test data or labels. The coding assistant authored the templates, so template and wording bias remain limitations.

The 288 ledger claims cover 144 ledgers and 72 independent seed clusters. Each cluster shares its sign and void masks across amount magnitudes, with both an exact claim and a one-cent mismatch. The revised benchmark has 144 pilot cases and 768 held-out cases. Its family-level selection was saved before held-out API calls. Every held-out cell is reported; no test item was removed.

The four models and providers use the original notebook's pins. Cutoff or release sources, pricing snapshots and the date filter are retained in [the model date record](../model_dates.json) and [endpoint catalog](../model_catalog.json). The original response cache is unchanged. Clef's undated checkpoint remains a reproducibility limit.

The first held-out benchmark collection had fast connection failures across providers and Clef hosted-concurrency limits. A separately frozen replication repeated all held-out cases with one sequential stream per provider, keeping request bodies and pilot selection unchanged. The replication eliminated the earlier connection failures but still encountered Clef rate limits. Report operational, valid-only and common-valid-case scores separately; missingness can bias conditional scores.

cache_requests.jsonl retains the initial follow-up requests. cache_replication_requests.jsonl retains the controlled replication. Partitioning preserves every raw line, request, response and key. Requests are cached by the full ordered wire body and local draw ID; no secret header is stored. No failed case was replaced or retried.

The row-label and Python arithmetic system is an assisted control. Perfect results on that system, exact-net controls and metadata-only controls do not contribute to standalone model ranking. Metadata-only paired scores are 50% among valid replies; OpenAI refused several fact-free questions.

The original README had a reporting error: the hardest ledger results were 16/32 for OpenAI, Mercury and Clef, and 15/32 for Jev. The original cached predictions and aggregate scores were already correct.

The audit finds no explicit label field or case identifier in the primary wire requests, and paired metadata is identical across opposite labels. This finite audit does not prove the absence of every statistical shortcut. The old evidence task is solved by equality of two supplied dictionaries, so its 100% scores are a ceiling result. The rejected original severity v1 reference leak remains excluded; the corrected severity control is retained.

Primary readings checked on 2026-10-20:

- [Decisions guide](https://developers.openai.com/api/docs/guides/decisions), especially separate calls for dependent decisions.
- [CheckList](https://arxiv.org/abs/2005.04118), controlled behavioral and shortcut tests.
- [PAL](https://arxiv.org/abs/2211.10435), language interpretation separated from code execution.
- [Program of Thoughts](https://arxiv.org/abs/2211.12588), external computation for numerical tasks.
