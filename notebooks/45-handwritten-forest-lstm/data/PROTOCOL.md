# Protocol history, notebook 45

Records for someone checking the work: pilot runs, the plan fixed before the main collection, settings, and anything
that went wrong. Dates are 2026, Toronto time.

## 5 November: first quick test (not used in the notebook)

A single Claude Sonnet 5.5 request per task, `claude -p` with no tools.

- Forest: five numeric features, three classes (a diagonal boundary x1 + x3 > 11 and a box x0 > 6 and x2 < 4),
  8% label noise, 300 visible rows, 3,000 hidden rows, at most 10 trees of depth 6. Sonnet's forest scored 71.5%;
  a trained 10-tree forest with the same limits scored 85.0%, the noise-free rule 94.3%.
- LSTM: a series with a 12-step cycle. Sonnet's weights scored RMSE 2.02; the trained same-size LSTM 1.48 and a
  trained linear model 1.21.

Both tasks were judged too easy to separate methods (a diagonal and a box are close to what a tree does anyway, and
one cycle is close to what a linear model does), so harder tasks were designed.

## 5 to 7 November: pilot on the harder tasks

Script `quicktest2.py` (kept outside the repo in the session scratchpad). The tasks are the ones the notebook calls
"Rules, 600 rows" and "Weekly cycle", with the same seeds, prompts and scoring as the notebook.

| Request | Forest accuracy | LSTM RMSE |
|---|---|---|
| Sonnet 5.5, three forest and two LSTM requests | 38.5%, 39.5%, 42.5% | 3.30, 3.03 |
| Opus 5.5, two each | 91.6%, 91.0% | 4.57, 2.70 |
| Fable 5.1, two each | 91.9%, 59.8% | 2.81, 3.13 |

References at the time: trained 20-tree depth-8 forest 65.0%, gradient boosting 84.7%, noise-free rule 92.6%;
trained LSTM chosen on held-out visible days 3.87 (the pilot first reported 4.10, the lowest-training-loss seed, and
then switched to validation choice), trained linear model 2.47, true formula 1.97. Spend about US$18 for 13
requests; Fable forest requests took 13 to 19 minutes.

Sonnet used a 64,000-token output allowance and a US$5 budget flag; Opus and Fable used 128,000 tokens and US$20.

What the pilot changed: the full study uses three requests per model per task (two Fable forests differed by 32
points), the same 128,000-token allowance and US$20 flag for every Claude model, adds models from other vendors,
and adds variants: fewer and more rows, labels without a short rule, and a second seasonal cycle.

## 9 November: plan fixed before the main collection

Written before any main-collection reply was scored.

- Models: Claude Opus 5.5, Fable 5.1 and Sonnet 5.5 via `claude -p` (Claude Code 2.1.296; `--tools ""`,
  `--safe-mode`, empty MCP configuration, effort high, `CLAUDE_CODE_MAX_OUTPUT_TOKENS=128000`, `--max-budget-usd 20`,
  system prompt "You are a numerical model author. Return only the requested JSON data."). GPT-6.1 Sol via
  `codex exec` 0.160.1 (`--ignore-user-config --ignore-rules --ephemeral`, read-only sandbox, shell, code mode,
  browser, multi-agent, skills, plugins, apps, memories and web search disabled, a two-sentence neutral instruction
  file in place of Codex's agent instructions, reasoning effort high). Muse Wonder Full 1.0 via `muse exec` 1.4.14
  (`--preset empty`, reasoning effort high). Kimi K3.1 Pro (`moonshotai/kimi-k3.1-pro-20261023`, provider Moonshot
  AI mxfp4), GLM 5.3 (`z-ai/glm-5.3-20260816`, provider Z.AI fp8) and DeepSeek V4.1 Flash
  (`deepseek/deepseek-v4.1-flash-20261017`, provider DeepSeek) via OpenRouter chat completions, streaming,
  reasoning effort high, `max_tokens` 128,000, provider pinned without fallback.
- Open-weight choice: the top three large open-weight models on the Artificial Analysis ranking for that class on
  9 November (Kimi K3.1 Pro, DeepSeek V4.1 Flash 1017, GLM 5.3).
- Tasks: rules-200, rules-600, rules-1500, smooth-600, weekly, two-cycles, as defined in the notebook. Prompts for
  rules-600 and weekly are byte-identical to the pilot.
- Three requests per model per task (144 in all), each a fresh single-turn request. Repeat 0 of every model and task
  is collected first and checked for harness faults before repeats 1 and 2.
- A transport failure (CLI crash, HTTP error, no final answer) is retried up to three times, 30 and 60 seconds
  apart, and every attempt is logged in `attempts.jsonl`. A request that still fails is counted as "no reply". A
  request running for 90 minutes is stopped and counted as a timeout. A reply that ends at the output limit is
  counted as cut off.
- Scoring: strict parser (one surrounding code fence removed, nothing else), forest accuracy on 5,000 hidden rows,
  LSTM RMSE on 140 hidden days. Unreadable replies are counted by kind and reported apart from scores. A lenient
  parser (first complete JSON object anywhere in the reply) is reported beside the strict one.
- References: commonest class, trained depth-8 tree, trained forest with 20 trees and depth 8, trained 200-tree
  forest, histogram gradient boosting, noise-free rule; repeat yesterday, same weekday last week, linear model on
  the same inputs, the same LSTM trained with exact gradients (six starts, iteration count and start chosen on days
  476 to 559), and the true formula. All references use scikit-learn or NumPy defaults with `random_state=0`.

## Main collection log

Entries are added as the collection runs.
