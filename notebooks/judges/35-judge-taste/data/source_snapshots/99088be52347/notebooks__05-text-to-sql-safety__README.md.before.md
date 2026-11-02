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

**Workflow.** The whole experiment from data to results, with the counts from this run. Every model response is cached in `data/`, so a re-run replays it without API calls.

```mermaid
flowchart TD
    db["Chinook sample database (MIT)<br/>+ 2 synthetic restricted tables: EmployeePayroll, AppUser"]
    watch["Watch lists read from the database<br/>225 personal-data values, 48 restricted values"]
    sys["System prompt: full schema + 5-rule read-only policy<br/>5,326 characters"]
    q["52 questions<br/>23 legitimate, each with a gold query<br/>29 policy-breaking, in 7 groups"]
    models["11 models × 52 questions, 1 call each<br/>8 open-weight via OpenRouter<br/>3 frontier via claude -p, codex exec, muse exec<br/>572 responses, 0 failed calls"]
    parse["Parse the JSON reply: sql, refused, reason<br/>100% valid JSON"]
    static["Static analysis with sqlglot<br/>statement count, statement types, tables read"]
    sand["Run on a throwaway copy of the database<br/>301 queries, 5 s limit, file access blocked"]
    v["Apply the 6 violation rules<br/>291 answered, 271 refused, 10 violations"]
    res["Per model: violations on 29, accuracy on 23<br/>9 of 11 models with 0 violations<br/>OpenRouter spend $0.485"]
    db --> watch
    db --> sys
    sys --> models
    q --> models
    models --> parse --> static --> sand --> v
    watch --> v
    q -->|"gold results"| v
    v --> res
```

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
