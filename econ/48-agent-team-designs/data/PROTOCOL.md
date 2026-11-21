# Protocol history: notebook 48, agent team designs

Records for someone checking the work. Entries are in date order.

## 2026-11-18: design fixed before any model call

Claim issue: https://github.com/k-sandhu/experiment-notebooks/issues/125. Branch: `add-48-agent-team-designs`.

### Question

When several AI agents work one business process together, does the way they are organised change how many
cases they get right, and how does correct output grow as agents are added?

### Processes and cases

Four processes, each cut into eight stations in a fixed order. A station has its own instructions, its own
documents and its own fields to fill in. Cases are generated in code from a seed, and a rule engine in the
same code computes the exact answer for every field.

| Process | Source workflow (reference only) |
|---|---|
| Capital call processing at an asset manager | `pam-capital-call-processing` |
| Small-ticket credit application at an equipment lessor | `efc-intake-credit-applications`, `efc-adjudicate-small-ticket-credit` |
| Provincial billing claim at a medical laboratory | `dls-fin-provincial-billing` |
| Block trade allocation at a pension investment manager | `pim-mkt-book-allocate` |

The reference workflows were written by Claude Opus from public sources in the organisation redesign study.
They supply role names and step descriptions only. Case contents and answers come from the generators.

Every case has:

- a planted fact: one fact that appears only in a document seen by an early station and that changes a field
  decided by a late station;
- an intake note written by the harness. In a quarter of cases, chosen by seed, the note states one value
  wrongly. The document that shows the right value is seen only by an early station.

### Designs

| Design | Agents | What each agent sees |
|---|---|---|
| Owner | 1 | Every instruction, every document, the intake note |
| Pipeline | 2, 4 or 8 | Its own instructions and documents, the fields filled so far, the previous agent's note |
| Shared record | 4 | Its own instructions, every document, every earlier note and field |
| Pipeline with checker | 4 plus 1 | As pipeline; then a checker from the other vendor sees everything and may correct fields |

Teams of four and two are made by merging neighbouring stations. The same model runs every agent in a team.
No design includes a person, a coordinator agent or parallel work.

### Models

Claude Sonnet 5.5 (`claude -p`) and GPT-6.1 Terra (`codex exec`), each run as the team, with the other as the
checker. Weaker and stronger models are size knobs, not part of the first run.

### Measures, fixed in advance

1. Primary: share of cases with every scored field correct, by design, compared on the same cases.
2. Unreadable replies (empty, not parseable, missing fields, refusal, timeout) counted apart from wrong ones,
   with accuracy also given on readable cases.
3. Planted fact: share of cases where the field that depends on it is correct.
4. Injected error: among cases with a wrong intake note, share where the affected field is correct.
5. Cost: input and output tokens, list-price cost and wall time per case.
6. Scaling: for the pipeline with 1, 2, 4 and 8 agents, correct cases per token. With a fixed token budget per
   agent, a team of k produces output proportional to k times accuracy divided by tokens per case. The
   exponent is the slope of log output on log k.

Intervals are bootstrap intervals over cases. Paired differences between designs use the same cases.

### Expectations written down before the run

- Pipeline accuracy falls as the team grows.
- The planted fact survives less often in longer pipelines, and survives in the shared record.
- The shared record is at least as accurate as the pipeline of four, at a higher token cost.
- The checker raises accuracy and catches more injected errors than the pipeline alone.
- Trade allocation, which has under one handoff a case as documented, shows the smallest gaps between designs.
- The scaling exponent is below 1.

### Difficulty calibration

A calibration run on separate seeds (six cases a process, Claude Sonnet 5.5, owner and pipeline of four)
sets the number of complications per case so that owner accuracy falls between 50% and 90%. Calibration
cases are not scored. Any change made after the scored run starts is recorded below as an amendment.

## 2026-11-18: build and amendments before the scored run

No scored case had been run when these were made.

### Who wrote the code

GPT-6.1 Sol (`codex exec`, reasoning effort high) wrote `agent_teams.py` from a written specification. GPT-6
Astra reviewed nothing here; Claude Sonnet 5.5 subagents made the later fixes. `gpt-6.2-sol` was rejected by
the installed Codex command-line tool (0.160.1), so 6.1 was used.

### Amendment 1: Claude models run as Claude Code subagents

`claude -p` on this machine was signed out ("OAuth session expired and could not be refreshed"). The repo
owner said to use Claude Code's built-in subagents for Anthropic models. The Claude arm therefore runs as
one subagent per prompt (Workflow tool, model alias `sonnet`, effort `low`, default agent type), launched by
the orchestrating session. `agent_teams.py` exports the prompts it is waiting for, writes the workflow
script that carries them and imports the replies into its cache; a pipeline of k agents takes k rounds.
This departs from the repo rule that Anthropic models are called through `claude -p`.

Consequences: each subagent also receives the project instruction file and has tools available. Every
prompt on this route starts with a fixed instruction to use no tool and answer only from the text given.
Across 290 calibration and test calls the subagents made no tool call. Each call used about 72,000 tokens,
nearly all standing context. Replies carry no token counts or timings.

### Amendment 2: work is measured in characters

The Codex tool adds about 21,000 input tokens to every call (27,351 by default; 21,375 with
`--ignore-user-config` and a one-line instruction, which is what the runner uses) and subagents report no
tokens. Measure 5 (cost) and measure 6 (scaling) therefore use characters of prompt and reply per case for
both models. Token counts and list-price cost are still recorded for the Codex model, with the measured
overhead subtracted and shown.

### Amendment 3: prompt wording

In the first test the single-owner prompt listed all eight stations and then said "return only your owned
fields". Claude Sonnet 5.5 answered as station 1 and returned one field. Every prompt now states how many
agents are in the team, which one the reader is, and the full list of fields it must return. Replies made
under the earlier wording were discarded.

### Calibration results (Claude Sonnet 5.5, 24 cases, seeds from 4899)

| Complications per case | Owner correct | Pipeline of four correct | Planted fact kept, pipeline |
|---|---|---|---|
| 2 | 22 of 24 | 20 of 24 (1 unreadable) | 22 of 24 |
| 4 | 22 of 24 | 15 of 24 (1 unreadable) | 20 of 24 |

Saved as `calibration_difficulty2_sonnet.csv` and `calibration_results.csv`.

### Amendment 4: difficulty set to four, with owner accuracy one case above the band

Owner accuracy was 22 of 24 (92%) at both settings, one case above the 50% to 90% band. Doubling the
complications did not lower it, so the owner's errors do not come from the complications. It did lower
the pipeline of four from 20 to 15 of 24. The scored run uses four complications. The designs being compared
sit well below the ceiling; comparisons against the single owner are close to it, and the write-up must say
so. With 24 cases, 22 correct is consistent with a true rate anywhere from about 74% to 98%.

### Amendment 5: one team model, 20 cases a process

Decided by the repo owner on 2026-11-18, before any scored case was run. Teams are run with Claude Sonnet 5.5
only. GPT-6.1 Terra is used only as the independent checker on the pipeline of four. The original plan ran
every design with each model as the team; that asked a second question (does the effect hold across model
families) at twice the cost, and is left for later. The scored set is 20 cases a process, 80 in all, from
seed 4801: 1,520 Sonnet calls over eight rounds and 80 Terra calls.

## 2026-11-20: scored run finished, two control arms added afterwards

The scored run finished on 2026-11-18: 80 cases, 480 runs, 1,520 Claude Sonnet 5.5 subagent calls over eight
rounds (no tool call, no empty reply, no retry) and 80 GPT-6.1 Terra checker calls. Results are in
`results.csv`; a copy taken before the control arms is `results_before_controls.csv`.

### Amendment 6: two control arms, chosen after seeing the results

These were not planned in advance. They were added on 2026-11-20, with the repo owner's agreement, because
two results could not be read as effects of team design without them. They are exploratory.

- GPT-6.1 Terra as a single owner on the same 80 cases. The pipeline of four with a Terra checker scored 80
  of 80. The checker sees every document and instruction, so if Terra alone scores about the same, the
  result shows what Terra can do, not what checking adds.
- Claude Sonnet 5.5 as a single owner followed by three reviewers (`review`, four calls). Each reviewer sees
  everything the owner saw plus the record so far and returns every field. The shared record of four scored
  79 of 80 against 65 of 80 for one owner. If owner plus three reviews scores about the same as the shared
  record, the gain comes from repeated full passes, not from sharing a record among agents with divided
  work.

### Control arm results (exploratory)

Run on 2026-11-20 on the same 80 cases. 80 GPT-6.1 Terra calls and 240 Claude Sonnet 5.5 subagent calls over
three rounds (no tool call, no empty reply, no retry).

| Arm | Fully correct of 80 |
|---|---|
| GPT-6.1 Terra, single owner | 78 |
| Claude Sonnet 5.5, single owner then three reviewers | 80 |

Cases fully correct after each pass of the review arm: 65 after the owner, 77 after the first reviewer, 80
after the second, 80 after the third. In the shared record of four the count after each agent was 73, 77, 79,
79: its first agent already returned every field, so that design was also four full passes.

## 2026-11-21: a second parser, added after the results were seen

### Amendment 7: results reported under two parsers

The parsing rule fixed in advance takes the first complete JSON object in a reply. While the write-up was
being drafted, 25 of the 1,760 scored Claude Sonnet 5.5 replies were found to contain an answer followed by a
correction. In 23 of them the correction is a second complete object with a `fields` key; in the other two
(`capital-4811` and `lab-4808`, pipeline of two) the correction sits outside any object, so both parsers read
the first. The first draft had been scored, and in the pipelines it was also what the next agent received.

Both parsers are now reported. "First" is the rule fixed in advance; its results stay in `results.csv`,
unchanged. "Last" takes the last complete object that has a `fields` key when a reply holds more than one,
and otherwise behaves the same; its results are in `results_last_object.csv`. `parser_report.csv` lists every
reply that parses differently.

Under "last", 23 chains had to be re-run from the agent after the superseded draft, because that agent's
prompt changed: 6 in the pipeline of two, 3 in the pipeline of four (shared with the checker arm), 11 in the
pipeline of eight and 3 in the review control. That took 62 new Claude Sonnet 5.5 subagent calls over six
rounds and 3 new GPT-6.1 Terra checker calls, on 2026-11-21. Every other run was carried over unchanged.

| Arm | Correct of 80, first | Correct of 80, last |
|---|---|---|
| One owner | 65 | 67 |
| Pipeline of 2 | 54 (8 unreadable) | 59 (9 unreadable) |
| Pipeline of 4 | 57 (1 unreadable) | 60 (1 unreadable) |
| Pipeline of 8 | 39 (2 unreadable) | 47 (0 unreadable) |
| Shared record of 4 | 79 | 79 |
| Pipeline of 4 with Terra checker | 80 | 80 |
| Terra, one owner (control) | 78 | 78 |
| Owner then three reviewers (control) | 80 | 80 |

The figures are drawn under "last", because it scores what each agent finally said. The choice of parser was
made after seeing the results, so the write-up gives both wherever they differ.

## 2026-11-21: note on files

The reference workflows named in the processes table are not committed with this notebook. They were used
once, to give the case generator realistic role names and step descriptions, and nothing in the notebook
reads them.

One saved reply was edited before the commit. The first GPT-6.1 Terra test call (cache key starting `9f558816`,
made before `--ignore-user-config` was added) stored a Codex warning that quoted the path of a local settings
file. The user folder name in that path was replaced with `user`. The request, the cache key and the model's
answer are unchanged, and the scored run does not read this row.
