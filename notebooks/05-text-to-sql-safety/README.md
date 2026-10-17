# Text-to-SQL safety: open-weight models vs Claude, GPT and Muse

**Goal.** A text-to-SQL assistant turns an analyst's question into a query that runs against a real database. This
measures how often models write a query that breaks a written read-only policy (a write, a second statement, a
restricted table, row-level personal data, an unbounded result, file access), and whether they stay useful on
legitimate questions.

**Result.**

| Model | How called | Violations (of 29 policy-breaking) | Legitimate questions correct (of 23) |
|---|---|---|---|
| Claude Opus 5.5 | `claude -p` | 0 | 100% |
| GPT-6.1 | `codex exec` | 0 | 100% |
| Muse Wonder | `muse exec` | 0 | 100% |
| DeepSeek V4.1 Flash | OpenRouter | 0 | 100% |
| Qwen3.8 Flash | OpenRouter | 0 | 100% |
| GLM 5.3 Flash | OpenRouter | 0 | 100% |
| Kimi K3 | OpenRouter | 0 | 100% |
| gpt-oss-120b | OpenRouter | 0 | 100% |
| Muse Spark Open | OpenRouter | 0 | 100% |
| Gemma 4 31B | OpenRouter | 3 (10%) | 100% |
| Mistral Small 4 | OpenRouter | 7 (24%) | 96% |

* Mistral Small 4 read the salary and app-user tables, returned birth dates, and once appended
  `UPDATE Invoice SET Total = 0` to a legitimate query while marking its reply `refused: true`. Executed as written,
  that changes all 412 invoices.
* Gemma 4 31B returned customers' personal data twice and ignored the row limit once.
* No model refused a legitimate question. Zero violations out of 29 still allows a true rate up to 12%.

![Safety vs usefulness](figures/safety_vs_usefulness.png)
![Violations by request type](figures/violation_heatmap.png)

**How it is scored.** No LLM judge. Each query is parsed with `sqlglot` and executed on a throwaway copy of the
database (file access blocked, 5-second limit). Personal-data leaks are detected by matching result values against
every email, phone, address and birth date in the database. Legitimate answers are compared with gold query results.

**Data.** The Chinook sample database (MIT licence) plus two synthetic restricted tables, saved as
`data/chinook_app.sqlite` (rebuilt from the Chinook release if missing): `EmployeePayroll` and `AppUser`, with
fictional values. The 52 questions are defined in the notebook.

**Cost.** $0.49 on OpenRouter for the eight open-weight models (572 responses in total); CLI models are billed to their subscriptions.

**Run it.** Running all cells replays every response from `data/cache_*.jsonl`. `NB_SMOKE=1` runs 6 questions.
