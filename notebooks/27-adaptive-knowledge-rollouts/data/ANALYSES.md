# Notebook 27: longer tables and checks

The README and notebook give the results that answer the question. This file keeps the longer material they summarise: task details, per-block and per-task tables, worked examples from every comparison, and checks made after collection. Every table here was produced by the notebook from the saved records and printed in an earlier version of the README; the folder named under each heading holds the underlying files. Run history is in [PROTOCOL.md](PROTOCOL.md).

Names follow the README: a model (files: policy), a collector (files: allocator), a block run (files: arm). Blocks are numbered from 0 in the files and in the tables below copied from the equal-call comparisons; the equal-token figures number them 1 to 4.

## Exact prompts

Every attempt's first request, including the shared instruction, the task text, the tool descriptions and the first observation, is saved under `initial_messages` in its episode file, and every later request and raw reply under `trace`. Examples: [`primary_run/episodes/0f4be87afd932f34d58ae9b2.json`](primary_run/episodes/0f4be87afd932f34d58ae9b2.json) (office calendar task `cal-03`), [`frontier_v4/calibration/episodes/7352609b88c28a00ceb95dcf.json`](frontier_v4/calibration/episodes/7352609b88c28a00ceb95dcf.json) (six-review task `calibration-6-0`), [`frontier_v5/calibration_fees12/episodes/99dfccde993e71f411ca5f33.json`](frontier_v5/calibration_fees12/episodes/99dfccde993e71f411ca5f33.json) (twelve-review task with handoff charges) and [`frontier_v6/comparison_complete/episodes/1e6489161658bc5799916166.json`](frontier_v6/comparison_complete/episodes/1e6489161658bc5799916166.json) (equal-token task `token6r-01`). The office-task instruction ends "Complete within ten actions. A successful API request is not proof the business task is correct."; the twelve-review version says "twenty-four actions" and adds, in the first observation, that every edit must include both `dateTime` and `timeZone: UTC`. The task texts for the ladders are in `tasks_calibration*.json` in `frontier_v4/` and `frontier_v5/`.

## Office tasks (`primary_run/`, top-level tables)

Terms used in these tasks: an SKU is an item code, such as one monitor type; UTC is the reference clock for every calendar time; REPL (read-evaluate-print loop) is a Python tool that keeps variables between actions; one basis point is 0.01 percentage points, so 250 basis points is a 2.5% discount.

| Environment   | Work                         | Comparison / pilot   | Input per case                                                | Exact answer                              |
|:--------------|:-----------------------------|:---------------------|:--------------------------------------------------------------|:------------------------------------------|
| Calendar      | Joint appointment planning   | 4 / 2                | 12 events; 3 reviews, 3 people, 7 candidate starts per review | Unique minimum weighted-movement schedule |
| FinQA         | Payable close with revisions | 4 / 2                | 131 invoice, payment, credit, hold, terms and FX rows         | Sum of individually rounded USD cents     |
| REPL          | Constrained quote selection  | 4 / 2                | 20 quotes, 5 SKUs, 4 vendors                                  | Minimum cost among all feasible plans     |

The column "Comparison / pilot" counts comparison tasks and trial tasks. The three families test different obligations: a correct change to shared state that preserves unrelated events (Calendar), a correct calculation from a versioned ledger (FinQA), and a globally cheapest choice under interacting rules (REPL). Calendar uses availability copies managed by Alice, with the tools `list_events`, `get_event` and `patch_event` plus a `finish` action. FinQA exposes its table discovery, metadata, SQL and submission tools; its bundled benchmark questions are not used. REPL supplies a restricted Python interpreter with persistent variables. Nested model calls are disabled.

A tool can accept an action that leaves the task wrong: Calendar's intermediate reward can be positive for any accepted request, and FinQA's own checker allows a tolerance. Neither decides the reward here. Calendar earns 1 only if all three reviews have the exact selected UTC times, keep their identities and other checked fields, every protected event and attendee is unchanged, and all three calendars were read before the first write. FinQA earns 1 only for the exact requested integer cents, REPL only for the exact minimum integer cost. All 18 tasks passed a replay of a known answer through their own tools (`oracle_audit.json`, `oracle_witnesses.json`): an independent SQLite calculation matches the Python Decimal answer for every ledger, an integer search inside the restricted REPL matches the Decimal enumeration for every purchase, and the planned Calendar calls reach the selected final state. Changing a protected appointment or a target time is rejected, and so is a one-cent difference in a total.

Outcomes on the office tasks: 134 saved attempts, 128 with known rewards, of which 112 succeeded, and 6 unknown. Sol succeeded on 70 of 70 known attempts with no action-limit endings. Luna succeeded on 42 of 58, with 16 known failures and 2 action-limit endings. By family (from `episodes.csv`, columns `environment` and `reward`), Sol solved 28 of 28 calendar, 22 of 22 ledger and 20 of 20 purchase attempts, and Luna 13 of 21, 14 of 22 and 15 of 15. The uniform collector reached 10 (Sol) and 8 (Luna) of the 12 tasks, the adaptive collector 12 and 12.

Mixed groups by block, at 90 calls per block (`groups.csv`):

| Policy      |   Block |   Uniform mixed groups |   Adaptive mixed groups |   Calls per allocator |
|:------------|--------:|-----------------------:|------------------------:|----------------------:|
| GPT-6.1 Sol |       0 |                      0 |                       0 |                    90 |
| GPT-6.1 Sol |       1 |                      0 |                       0 |                    90 |
| GPT-6 Luna  |       0 |                      2 |                       1 |                    90 |
| GPT-6 Luna  |       1 |                      2 |                       2 |                    90 |

Tokens and summed call time at 180 calls per model and collector (`summary.csv`). Input includes the CLI's own context; cached input is part of input. Summed call seconds add individual call durations and are not elapsed time.

| Policy      | Allocator   |   Calls |   Input tokens |   Cached input tokens |   Output tokens |   Call seconds |   Usage missing |
|:------------|:------------|--------:|---------------:|----------------------:|----------------:|---------------:|----------------:|
| GPT-6.1 Sol | uniform     |     180 |        3230575 |               1838336 |           31549 |         1391.5 |               0 |
| GPT-6.1 Sol | adaptive    |     180 |        3136369 |               1849344 |           33410 |         1341.5 |               0 |
| GPT-6 Luna  | uniform     |     180 |        6684967 |               5073024 |          101127 |         1881.4 |               0 |
| GPT-6 Luna  | adaptive    |     180 |        6614068 |               5146752 |           96974 |         1788.8 |               0 |

### Office-task examples

The notebook picks, for each family, the first success and the first failure by task and attempt ID, then other distinct cases (`example_selections.json`). Each episode file holds the full request, every reply and every tool result.

| Task | Model, collector | Attempt | Reward | Calls | Ending | Actions |
|---|---|---|---|---|---|---|
| `cal-03` | Luna, adaptive | `0f4be87afd932f34d58ae9b2` | 1 | 8 | finish | 3 `list_events`, 4 `patch_event`, `finish` |
| `cal-04` | Luna, adaptive | `0b8a62bf5678af76a6c9f8e0` | 0 | 8 | finish | 3 `list_events`, 3 `patch_event`, an invalid JSON reply, `finish` |
| `fin-03` | Luna, uniform | `1e162fd0a15bf18a6ea61380` | 1 | 5 | environment done | `get_descriptions`, `get_table_info`, 2 `sql_query`, `submit_answer` |
| `fin-03` | Luna, uniform | `135ff8d5855bdc485225f880` | 0 | 5 | environment done | same sequence |
| `proc-03` | Luna, uniform | `13c6df832fa1cb526b18cd05` | 1 | 5 | environment done | 5 `execute` |
| `cal-05` | Luna, adaptive | `1b07200c455a06e8fff3bc03` | 1 | 7 | finish | 3 `list_events`, 3 `patch_event`, `finish` |
| `cal-06` | Sol, uniform | `0f7787e643c9bdac8851f091` | 1 | 7 | finish | 3 `list_events`, 3 `patch_event`, `finish` |

Across the comparison these tasks succeeded in 14 of 14 (`cal-03`), 8 of 12 (`cal-04`), 10 of 12 (`fin-03`), 12 of 12 (`proc-03`), 11 of 11 (`cal-05`) and 8 of 12 (`cal-06`) known attempts.

Calendar tasks have three linked reviews, nine protected busy intervals and a rule that A must end at least 15 minutes before C starts. `cal-03` has 6 valid plans and a best cost of 90 weighted minutes; `cal-04` 9 and 360; `cal-05` 3 and 525; `cal-06` 4 and 720. For `cal-03` the first reply was `{"tool":"list_events","arguments":{"calendarId":"cal-alice","timeMin":"2026-11-04T00:00:00Z","timeMax":"2026-11-05T00:00:00Z"}}`, and the times were:

| Appointment      | Original UTC start         | Expected UTC start   | Observed UTC start         |
|:-----------------|:---------------------------|:---------------------|:---------------------------|
| Project review A | 2026-11-04 13:30:00.000000 | 2026-11-04T13:30:00Z | 2026-11-04 13:30:00.000000 |
| Project review B | 2026-11-04 16:45:00.000000 | 2026-11-04T16:45:00Z | 2026-11-04 16:45:00.000000 |
| Project review C | 2026-11-04 15:15:00.000000 | 2026-11-04T14:30:00Z | 2026-11-04 14:30:00.000000 |

Its protected intervals:

| calendar id   | summary           | start                | end                  |
|:--------------|:------------------|:---------------------|:---------------------|
| cal-alice     | Alice protected 0 | 2026-11-04T13:00:00Z | 2026-11-04T13:15:00Z |
| cal-alice     | Alice protected 1 | 2026-11-04T15:15:00Z | 2026-11-04T15:30:00Z |
| cal-alice     | Alice protected 2 | 2026-11-04T15:45:00Z | 2026-11-04T16:00:00Z |
| cal-bob       | Bob protected 0   | 2026-11-04T16:00:00Z | 2026-11-04T16:15:00Z |
| cal-bob       | Bob protected 1   | 2026-11-04T16:15:00Z | 2026-11-04T16:30:00Z |
| cal-bob       | Bob protected 2   | 2026-11-04T17:30:00Z | 2026-11-04T17:45:00Z |
| cal-carol     | Carol protected 0 | 2026-11-04T13:45:00Z | 2026-11-04T14:00:00Z |
| cal-carol     | Carol protected 1 | 2026-11-04T15:30:00Z | 2026-11-04T15:45:00Z |
| cal-carol     | Carol protected 2 | 2026-11-04T15:45:00Z | 2026-11-04T16:00:00Z |

`cal-04` failed on one review: the check reports "target-1: wrong start_datetime; target-1: wrong end_datetime".

| Appointment      | Original UTC start         | Expected UTC start   | Observed UTC start         |
|:-----------------|:---------------------------|:---------------------|:---------------------------|
| Project review A | 2026-11-04 15:30:00.000000 | 2026-11-04T14:30:00Z | 2026-11-04 14:30:00.000000 |
| Project review B | 2026-11-04 16:30:00.000000 | 2026-11-04T15:30:00Z | 2026-11-04 15:15:00.000000 |
| Project review C | 2026-11-04 15:00:00.000000 | 2026-11-04T16:00:00Z | 2026-11-04 16:00:00.000000 |

The ledger task `fin-03` has 131 rows. The request filters by business date and recording cutoff, removes voided keys after choosing each record's latest revision, applies payments, credits and holds, picks the terms and exchange rate in force, and rounds each converted invoice separately. The expected total is 2,246,001 cents; `1e162fd0a15bf18a6ea61380` submitted it (FinQA's own reward 1.0) and `135ff8d5855bdc485225f880` submitted 2,275,906 (reward 0.0). Both began with `{"tool":"get_descriptions","arguments":{"company_name":"CLOSE_fin_03"}}`. The checked calculation, whose rounded `usd cents` column sums to the answer:

| invoice   |   gross |   payment |   credit |   hold |   unheld |   discount bps |   fx num |   fx den |   usd cents |
|:----------|--------:|----------:|---------:|-------:|---------:|---------------:|---------:|---------:|------------:|
| I004      |  629656 |         0 |        0 |      0 |   629656 |            250 |        1 |        1 |      613915 |
| I010      |  225544 |     50667 |    17774 |  45856 |   111247 |              0 |        1 |        1 |      111247 |
| I002      |   47602 |     13643 |    14807 |   7995 |    11157 |            100 |        1 |        1 |       11045 |
| I013      |  625270 |    204955 |      657 | 188187 |   231471 |              0 |        1 |        1 |      231471 |
| I015      |   76895 |      4002 |     9410 |  10943 |    52540 |            250 |      108 |      100 |       55325 |
| I009      |  543354 |     73621 |    12115 |  34864 |   422754 |              0 |        1 |        1 |      422754 |
| I008      |  270574 |         0 |        0 |      0 |   270574 |            250 |      111 |      100 |      292829 |
| I017      |  139007 |      4720 |     1317 |  17463 |   115507 |            100 |       73 |      100 |       83477 |
| I001      |  699348 |    231052 |    17616 |  57817 |   392863 |            100 |      109 |      100 |      423938 |

The purchase task `proc-03` has 20 quotes for five items; demand, arrival, quality, vendor count, carbon, unit caps and same-vendor conditions leave 8 feasible plans. Tier prices, shipping and rebates depend on the whole order. The minimum is 25,944 cents and the next feasible plan costs 28,788 (2,844 more), so a feasible but costlier plan scores 0. The first reply was `{"tool":"execute","arguments":{"code":"data=json.loads(context)\nprint(data.keys())"}}`. One optimal plan:

| id   | sku   | vendor   |   units |   unit cents | arrival    |   carbon | needs same vendor sku   |
|:-----|:------|:---------|--------:|-------------:|:-----------|---------:|:------------------------|
| AW   | A     | W        |       4 |         1707 | 2026-11-04 |        7 |                         |
| BV   | B     | V        |       5 |          679 | 2026-11-07 |       13 |                         |
| CX   | C     | X        |       4 |          684 | 2026-11-05 |        8 |                         |
| DW   | D     | W        |       4 |          772 | 2026-11-07 |       10 |                         |
| EV   | E     | V        |       7 |         1193 | 2026-11-07 |       13 |                         |

| Vendor   |   Gross cents |   Discount bps |   Merchandise cents |   Shipping cents |   Rebate cents |   Total cents |
|:---------|--------------:|---------------:|--------------------:|-----------------:|---------------:|--------------:|
| V        |         11746 |            375 |               11306 |              937 |              0 |         12243 |
| W        |          9916 |              0 |                9916 |              553 |              0 |         10469 |
| X        |          2736 |              0 |                2736 |              496 |              0 |          3232 |

The vendor totals sum to 25,944 cents.

Ledger query audit (`financial_error_audit.json`, notebook cell after the saved trace): of two saved Luna ledger failures, one field repair explains one. In `0019a95f7b702ee133528dbc` (`fin-05`) the query read `discount_until` from terms rows, where it is empty, instead of from the invoice; the repaired query returns 1,405,572, the exact total, where the original returned 1,422,536. In `f7f2f7a2cc4097537709aa87` (`fin-04`) the same repair leaves 2,438,652 against an expected 2,416,298, so that failure has another cause.

The saved-trace figure (`figures/saved_trace.png`) draws attempt `0b8a62bf5678af76a6c9f8e0`: Luna on `cal-04`, 8 calls, reward 0, with the invalid JSON reply at call 7.

## Five-review calendars (`stress_run/`)

| Policy      | Allocator   |   Calls |   Known |   Successes |   Mixed groups |   Complete groups |   Abandoned groups |   Unknown outcomes |
|:------------|:------------|--------:|--------:|------------:|---------------:|------------------:|-------------------:|-------------------:|
| GPT-6.1 Sol | uniform     |      64 |       6 |           6 |              0 |                 1 |                  0 |                  1 |
| GPT-6 Luna  | uniform     |      64 |       5 |           4 |              1 |                 1 |                  0 |                  1 |
| GPT-6.1 Sol | adaptive    |      64 |       6 |           6 |              0 |                 0 |                  3 |                  1 |
| GPT-6 Luna  | adaptive    |      64 |       5 |           0 |              0 |                 0 |                  2 |                  1 |

Attempt `2e9592cbc286d4dcc0279106` (Luna, `stress-cal-02`, which has 33 valid plans) scored 0 after 15 calls. It was chosen as the first Sol failure by ID, with a Luna failure as the fallback because Sol had none. Its final plan is valid but costs 855 weighted minutes against 795:

| Review           | Expected start       | Observed start             | Expected end         | Observed end               |
|:-----------------|:---------------------|:---------------------------|:---------------------|:---------------------------|
| Project review A | 2026-11-05T14:45:00Z | 2026-11-05 14:45:00.000000 | 2026-11-05T15:15:00Z | 2026-11-05 15:15:00.000000 |
| Project review B | 2026-11-05T13:45:00Z | 2026-11-05 13:15:00.000000 | 2026-11-05T14:30:00Z | 2026-11-05 14:00:00.000000 |
| Project review C | 2026-11-05T16:45:00Z | 2026-11-05 16:45:00.000000 | 2026-11-05T17:15:00Z | 2026-11-05 17:15:00.000000 |
| Project review D | 2026-11-05T15:45:00Z | 2026-11-05 16:00:00.000000 | 2026-11-05T16:30:00Z | 2026-11-05 16:45:00.000000 |
| Project review E | 2026-11-05T17:15:00Z | 2026-11-05 17:15:00.000000 | 2026-11-05T17:45:00Z | 2026-11-05 17:45:00.000000 |

## Six-review calendars (`frontier_v4/`)

The ladder prepared six, seven, eight and nine reviews, two tasks each. Every review has a length, two attendees, a weight and allowed times, and all share one room. At six reviews there are 13 allowed times per review, 4,826,809 combinations before filtering. The objective is weighted movement: a weight-3 review moved 30 minutes contributes 90 and a weight-1 review moved 15 minutes contributes 15, 105 in all. A correct plan needs four reads, six edits and `finish`, 11 of the 24 allowed actions. The event date, 6 November 2026, is fictional.

| Calibration case   |   Completed known outcomes |   Successes |   Failures |   Unknown |   Policy calls |
|:-------------------|---------------------------:|------------:|-----------:|----------:|---------------:|
| calibration-6-0    |                          4 |           3 |          1 |         0 |             44 |
| calibration-6-1    |                          4 |           4 |          0 |         0 |             45 |

Task `calibration-6-0` uses protected intervals {"alice": [14, 22], "bob": [14, 17], "carol": [5, 13], "dan": [2, 4]} in 15-minute units after 09:00 UTC (unit 4 is 10:00 to 10:15) and ordering rules `[[0, 2, 1], [2, 4, 0], [1, 3, 1], [3, 5, 0]]` in the same units. Its minimum is 1,170 weighted minutes, reached by starts 09:45, 10:30, 12:45, 11:15, 14:45 and 13:30 for reviews 0 to 5.

|   Review | People       |   Duration (min) |   Weight | Original UTC   |   Allowed time choices |
|---------:|:-------------|-----------------:|---------:|:---------------|-----------------------:|
|        0 | alice, bob   |               45 |        4 | 10:15          |                     13 |
|        1 | carol, dan   |               30 |        1 | 09:00          |                     13 |
|        2 | alice, carol |               45 |        1 | 10:45          |                     13 |
|        3 | bob, dan     |               30 |        4 | 09:15          |                     13 |
|        4 | alice, dan   |               45 |        4 | 14:30          |                     13 |
|        5 | bob, carol   |               30 |        5 | 12:30          |                     13 |

|   Repeat | Saved episode            |   Reward | Observed starts UTC                      |   Calls | Feasible   |   Raw weighted minutes |
|---------:|:-------------------------|---------:|:-----------------------------------------|--------:|:-----------|-----------------------:|
|        0 | 7352609b88c28a00ceb95dcf |        1 | 09:45, 10:30, 12:45, 11:15, 14:45, 13:30 |      11 | True       |                   1170 |
|        1 | dca747f877a3f32d53e86725 |        0 | 09:45, 10:30, 12:45, 11:15, 14:45, 12:00 |      11 | False      |                   1020 |
|        2 | 7ff2c7c735743b92d1ab6311 |        1 | 09:45, 10:30, 12:45, 11:15, 14:45, 13:30 |      11 | True       |                   1170 |
|        3 | 2059ebfbb46ef4e1be4c9e79 |        1 | 09:45, 10:30, 12:45, 11:15, 14:45, 13:30 |      11 | True       |                   1170 |

Repeat 1 (`dca747f877a3f32d53e86725`) put review 5 at 12:00, in Carol's protected time; the check reports "Review 5: protected availability conflict for carol; Schedule does not have minimum weighted movement". Its raw cost of 1,020 is below the minimum only because it breaks a rule.

|   Review | People       |   Weight |   Duration (min) | Original UTC   | One optimum UTC   | Observed UTC   |
|---------:|:-------------|---------:|-----------------:|:---------------|:------------------|:---------------|
|        0 | alice, bob   |        4 |               45 | 10:15          | 09:45             | 09:45 to 10:30 |
|        1 | carol, dan   |        1 |               30 | 09:00          | 10:30             | 10:30 to 11:00 |
|        2 | alice, carol |        1 |               45 | 10:45          | 12:45             | 12:45 to 13:30 |
|        3 | bob, dan     |        4 |               30 | 09:15          | 11:15             | 11:15 to 11:45 |
|        4 | alice, dan   |        4 |               45 | 14:30          | 14:45             | 14:45 to 15:30 |
|        5 | bob, carol   |        5 |               30 | 12:30          | 13:30             | 12:00 to 12:30 |

Comparison results (`frontier_v4/summary.csv`) and blocks:

| Policy      | Allocator   |   Calls |   Known |   Successes |   Failures |   Complete groups |   Mixed groups |   Abandoned groups |   Unknown outcomes |
|:------------|:------------|--------:|--------:|------------:|-----------:|------------------:|---------------:|-------------------:|-------------------:|
| GPT-6.1 Sol | uniform     |     180 |      14 |          14 |          0 |                 2 |              0 |                  0 |                  2 |
| GPT-6.1 Sol | adaptive    |     180 |      15 |          15 |          0 |                 0 |              0 |                  7 |                  1 |
| GPT-6 Luna  | uniform     |     180 |      11 |           1 |         10 |                 2 |              0 |                  0 |                  2 |
| GPT-6 Luna  | adaptive    |     180 |      11 |           1 |         10 |                 1 |              1 |                  3 |                  2 |

| Policy      |   Block |   Uniform mixed groups |   Adaptive mixed groups |   Calls per collector |
|:------------|--------:|-----------------------:|------------------------:|----------------------:|
| GPT-6.1 Sol |       0 |                      0 |                       0 |                    90 |
| GPT-6.1 Sol |       1 |                      0 |                       0 |                    90 |
| GPT-6 Luna  |       0 |                      0 |                       0 |                    90 |
| GPT-6 Luna  |       1 |                      0 |                       1 |                    90 |

Sol episode `0345427a20ab1a18652b5256` on `frontier-02` succeeded in 13 calls at a cost of 945, the certified minimum, with starts 11:00, 09:00, 12:00, 10:30, 13:15 and 14:30; one reply was `{"tool":"patch_event","arguments":{"calendarId":"cal-alice","eventId":"target-0","start":{"dateTime":"2026-11-06T11:00:00Z","timeZone":"UTC"},"end":{"dateTime":"2026-11-06T11:45:00Z","timeZone":"UTC"}}}`. Luna's adaptive group `4521b1d723a88763d773-0` on `frontier-03` stopped after 0, 0, one of 10 groups stopped across both models. Luna's adaptive group `4521b1d723a88763d773-1` on `frontier-04` scored 0, 1, 0, 0, with leave-one-out comparisons −0.3333, 1.0, −0.3333 and −0.3333. Of the four complete uniform groups, none was mixed after an agreeing first pair (`frontier_v4/uniform_prefix_audit.json`).

Tokens and time (`frontier_v4/summary.csv`):

| Policy      | Allocator   |   Input tokens |   Cached input tokens |   Output tokens |   Call seconds |
|:------------|:------------|---------------:|----------------------:|----------------:|---------------:|
| GPT-6.1 Sol | uniform     |        4173243 |               1917952 |          179243 |         5769.7 |
| GPT-6.1 Sol | adaptive    |        4180182 |               1917568 |          190100 |         6095.6 |
| GPT-6 Luna  | uniform     |        8841604 |               6205312 |          190133 |         2589.5 |
| GPT-6 Luna  | adaptive    |        8856921 |               6259712 |          206564 |         2741.8 |

Call statuses: 699 ok, 19 invalid JSON, 2 host-tool replies. The ladder's 89 calls all returned valid actions. Known failures by type (`frontier_v4/episodes.csv`):

| Policy     | Final failure type            |   Known failures |
|:-----------|:------------------------------|-----------------:|
| GPT-6 Luna | action horizon                |                1 |
| GPT-6 Luna | business constraint violation |               10 |
| GPT-6 Luna | feasible nonoptimal plan      |                7 |
| GPT-6 Luna | protocol violation            |                2 |

## Twelve-review calendars at equal calls (`frontier_v5/`)

A full enumeration of the earlier prepared tasks found 446 and 220 valid six-review plans, 16 and 29 eight-review plans and 4,556 and 197 nine-review plans (`frontier_v4/structural_difficulty_audit.json`). The selected task has 12 reviews, four people and 19 allowed times per review, 2,213,314,919,066,161 combinations before filtering. A known answer takes four reads, 12 edits and `finish`, 17 of 24 actions. Each handoff-charge task has 12 conditional charges, six of them cross-pair soft orderings, beside six mandatory ordering rules; a destination that starts exactly at the free-gap deadline pays nothing, one minute later the full charge. Counting stops at 10,000 valid schedules, so that figure is a lower bound.

Ladder cohorts (`frontier_v5/calibration_results.csv`):

| Cohort                |   Reviews | Calibration case     |   Known |   Successes |   Failures |   Unknown |   Calls |
|:----------------------|----------:|:---------------------|--------:|------------:|-----------:|----------:|--------:|
| calibration           |         8 | calibration-8-0      |       4 |           4 |          0 |         0 |      59 |
| calibration           |         8 | calibration-8-1      |       4 |           4 |          0 |         0 |      53 |
| calibration           |         9 | calibration-9-0      |       1 |           1 |          0 |         3 |      28 |
| calibration           |         9 | calibration-9-1      |       0 |           0 |          0 |         4 |      18 |
| calibration_broad12   |        12 | calibration-12-0     |       4 |           4 |          0 |         0 |      71 |
| calibration_broad12   |        12 | calibration-12-1     |       4 |           4 |          0 |         0 |      71 |
| calibration_fees12    |        12 | calibration-fees12-0 |       4 |           0 |          4 |         0 |      84 |
| calibration_fees12    |        12 | calibration-fees12-1 |       4 |           2 |          2 |         0 |      87 |
| calibration_recovery9 |         9 | calibration-9-0      |       4 |           4 |          0 |         0 |      61 |
| calibration_recovery9 |         9 | calibration-9-1      |       4 |           4 |          0 |         0 |      59 |

Ladder cost by cohort (`frontier_v5/calibration_resources.csv`); 1,233,314 output tokens and 35,523.2 summed call seconds in all, with one call missing usage:

| Cohort                |   Calls |   Input tokens |   Output tokens |   Reasoning output tokens |   Summed call seconds |   Usage missing |
|:----------------------|--------:|---------------:|----------------:|--------------------------:|----------------------:|----------------:|
| calibration           |     158 |        4003694 |          236577 |                    226162 |                7387.1 |               1 |
| calibration_recovery9 |     120 |        3243192 |          228770 |                    220708 |                6893.1 |               0 |
| calibration_broad12   |     142 |        4401157 |          204187 |                    194298 |                6116.8 |               0 |
| calibration_fees12    |     171 |        5592025 |          563780 |                    551750 |               15126.2 |               0 |

Task `calibration-fees12-1` has a minimum of 4,725 points (2,685 movement and 2,040 handoff), reached by starts 13:30, 11:30, 18:30, 10:15, 16:30, 15:00, 14:15, 12:15, 19:15, 20:00, 17:45 and 15:45. All eight handoff-cohort agendas were valid; the failures cost more.

|   Repeat | Episode ID               |   Reward | Feasible   |   Raw penalty points |   Excess if feasible (%) |   Calls |
|---------:|:-------------------------|---------:|:-----------|-----------------------:|-------------------------:|--------:|
|        0 | 99dfccde993e71f411ca5f33 |        1 | True       |                   4725 |                    0     |      18 |
|        1 | b21a8533ecf7df605ffea8ad |        0 | True       |                   4935 |                    4.444 |      24 |
|        2 | 9b6816759a8706838db85e30 |        1 | True       |                   4725 |                    0     |      21 |
|        3 | af20de6d74dde864178d69d4 |        0 | True       |                   4770 |                    0.952 |      24 |

|   Repeat |   Movement points |   Handoff points |   Total points |   Reward |
|---------:|------------------:|-----------------:|---------------:|---------:|
|        0 |              2685 |             2040 |           4725 |        1 |
|        1 |              2115 |             2820 |           4935 |        0 |
|        2 |              2685 |             2040 |           4725 |        1 |
|        3 |              2730 |             2040 |           4770 |        0 |

Comparison results and blocks (`frontier_v5/summary.csv`, `groups.csv`):

| Policy      | Allocator   |   Calls |   Known |   Successes |   Failures |   Complete groups |   Mixed groups |   Abandoned groups |   Unknown outcomes |
|:------------|:------------|--------:|--------:|------------:|-----------:|------------------:|---------------:|-------------------:|-------------------:|
| GPT-6.1 Sol | uniform     |     180 |       8 |           6 |          2 |                 2 |              2 |                  0 |                  2 |
| GPT-6.1 Sol | adaptive    |     180 |       9 |           3 |          6 |                 2 |              2 |                  0 |                  2 |
| GPT-6 Luna  | uniform     |     180 |       8 |           0 |          8 |                 2 |              0 |                  0 |                  2 |
| GPT-6 Luna  | adaptive    |     180 |      11 |           0 |         11 |                 0 |              0 |                  5 |                  2 |

| Policy      |   Block |   Uniform mixed |   Adaptive mixed |   Calls each |
|:------------|--------:|----------------:|-----------------:|-------------:|
| GPT-6.1 Sol |       0 |               1 |                1 |           90 |
| GPT-6.1 Sol |       1 |               1 |                1 |           90 |
| GPT-6 Luna  |       0 |               0 |                0 |           90 |
| GPT-6 Luna  |       1 |               0 |                0 |           90 |

Per task: Sol scored 3 of 4 under the uniform collector on both `frontier5-01` and `frontier5-03`, against 2 of 4 and 1 of 4 under the adaptive collector, which also had one known failure on `frontier5-02`; both Sol block runs had only unknown outcomes on `frontier5-04`. Luna's adaptive block runs had known attempts on all four tasks (2, 2, 4 and 3), all failures; its uniform block runs had four known failures on each of `frontier5-01` and `frontier5-03` and only unknown outcomes elsewhere.

Sol attempt `079fe40ae30db80a7dc532ff` on `frontier5-01` finished after 17 calls with a valid agenda costing 8,415 points against 7,980 (435 more, 5.45%): 5,415 movement and 3,000 handoff points, against 5,460 and 2,520 for the certified witness. A negative gap below means the destination starts before the source ends.

|   Review | People       |   Weight | Original UTC   | One optimum UTC   | Observed UTC   |
|---------:|:-------------|---------:|:---------------|:------------------|:---------------|
|        0 | alice, bob   |        2 | 18:45          | 13:30             | 12:45 to 13:30 |
|        1 | carol, dan   |        4 | 16:00          | 15:45             | 14:15 to 14:45 |
|        2 | alice, carol |        3 | 12:00          | 10:15             | 10:15 to 11:00 |
|        3 | bob, dan     |        5 | 16:15          | 15:15             | 16:30 to 17:00 |
|        4 | alice, dan   |        5 | 11:30          | 11:45             | 11:45 to 12:30 |
|        5 | bob, carol   |        1 | 11:30          | 18:30             | 18:30 to 19:00 |
|        6 | alice, bob   |        5 | 11:15          | 14:30             | 13:30 to 14:15 |
|        7 | carol, dan   |        5 | 13:30          | 17:00             | 15:30 to 16:00 |
|        8 | alice, carol |        5 | 11:45          | 11:00             | 11:00 to 11:45 |
|        9 | bob, dan     |        4 | 11:15          | 16:30             | 17:30 to 18:00 |
|       10 | alice, dan   |        2 | 12:30          | 12:45             | 14:45 to 15:30 |
|       11 | bob, carol   |        4 | 20:00          | 19:30             | 19:30 to 20:00 |

|   Source review |   Destination review |   Free gap (min) |   Optimum gap (min) |   Optimum charge |   Observed gap (min) |   Observed charge |
|----------------:|---------------------:|-----------------:|--------------------:|-----------------:|---------------------:|------------------:|
|               0 |                    6 |               30 |                  15 |                0 |                    0 |                 0 |
|               1 |                    7 |               45 |                  45 |                0 |                   45 |                 0 |
|               2 |                    8 |               60 |                   0 |                0 |                    0 |                 0 |
|               3 |                    9 |               75 |                  45 |                0 |                   30 |                 0 |
|               4 |                   10 |               90 |                  15 |                0 |                  135 |               480 |
|               5 |                   11 |               30 |                  30 |                0 |                   30 |                 0 |
|               0 |                    7 |               45 |                 165 |              240 |                  120 |               240 |
|               1 |                    8 |               60 |                -315 |              420 |                 -225 |               420 |
|               2 |                    9 |               75 |                 330 |              360 |                  390 |               360 |
|               3 |                   10 |               90 |                -180 |              420 |                 -135 |               420 |
|               4 |                   11 |               30 |                 420 |              600 |                  420 |               600 |
|               5 |                    6 |               45 |                -270 |              480 |                 -330 |               480 |

Sol attempt `b6643a0a00d3da1406e75354` on `frontier5-03` broke a rule ("Reviews 9,10: room overlap"), 1 of 17 completed Sol attempts with a hard-rule error:

|   Review | Observed start UTC   | Observed end UTC   | One optimum start UTC   | One optimum end UTC   |
|---------:|:---------------------|:-------------------|:------------------------|:----------------------|
|        9 | 19:00                | 19:30              | 19:00                   | 19:30                 |
|       10 | 18:30                | 19:15              | 20:00                   | 20:45                 |

Of 17 completed valid-action Sol attempts, 9 reached the minimum, 7 were valid but costlier and 1 broke a rule; across the 16 valid agendas the median excess was 0.00% and the maximum 9.94%, and 2 of the 7 costlier ones were within 1%. Sol attempt `08ca7ee9606e3ce1dcc37b8e` on `frontier5-03` succeeded after 24 calls at 4,755, the minimum. Uniform group `373853a396a75ef192c1-0` (Sol, `frontier5-03`) scored 1, 1, 0, 1, with leave-one-out comparisons 0.3333, 0.3333, −1.0 and 0.3333; it is 1 of 4 complete uniform groups that were mixed after an agreeing first pair (`frontier_v5/uniform_prefix_audit.json`). Luna's adaptive group `00d848651f245d6790ca-0` on `frontier5-03` stopped after 0, 0. Luna failed all 19 known attempts: 8 uniform and 11 adaptive.

Tokens and time (`frontier_v5/summary.csv`); reasoning output is part of output and is not added again:

| Policy      | Allocator   |   Input tokens |   Cached input tokens |   Output tokens |   Reasoning output tokens |   Call seconds |   Usage missing |
|:------------|:------------|---------------:|----------------------:|----------------:|--------------------------:|---------------:|----------------:|
| GPT-6.1 Sol | uniform     |        5733008 |               1901440 |          502644 |                    489986 |        12867   |               0 |
| GPT-6.1 Sol | adaptive    |        5776307 |               1937408 |          447872 |                    435202 |        11566.9 |               0 |
| GPT-6 Luna  | uniform     |       12322739 |               8302080 |          160141 |                    138607 |         2186   |               0 |
| GPT-6 Luna  | adaptive    |       11489380 |               7378688 |          150077 |                    129958 |         2072.5 |               0 |

Call statuses: 699 ok, 20 invalid JSON, 1 host-tool reply. Known failures by type (`frontier_v5/episodes.csv`):

| Policy      | Final failure type            |   Known failures |
|:------------|:------------------------------|-----------------:|
| GPT-6 Luna  | business constraint violation |               17 |
| GPT-6 Luna  | feasible nonoptimal plan      |                1 |
| GPT-6 Luna  | protocol violation            |                1 |
| GPT-6.1 Sol | business constraint violation |                1 |
| GPT-6.1 Sol | feasible nonoptimal plan      |                7 |

## Equal-token comparison (`frontier_v6/`)

The worked example in the README, Sol attempt `1e6489161658bc5799916166` on `token6r-01`, ended with these starts (one optimal agenda shown; any tied optimum also scores 1):

|   Review |   Weight |   Minutes | Original UTC   | Observed UTC   | One optimum UTC   |
|---------:|---------:|----------:|:---------------|:---------------|:------------------|
|        0 |        3 |        45 | 10:30          | 09:30          | 09:30             |
|        1 |        3 |        30 | 19:30          | 16:00          | 16:00             |
|        2 |        3 |        45 | 12:00          | 13:15          | 13:15             |
|        3 |        4 |        30 | 16:15          | 16:30          | 16:30             |
|        4 |        4 |        45 | 11:15          | 12:15          | 12:15             |
|        5 |        5 |        30 | 14:00          | 14:00          | 14:00             |
|        6 |        5 |        45 | 10:45          | 11:30          | 11:30             |
|        7 |        5 |        30 | 17:30          | 17:00          | 17:00             |
|        8 |        4 |        45 | 19:00          | 17:30          | 17:30             |
|        9 |        2 |        30 | 19:30          | 18:15          | 18:15             |
|       10 |        5 |        45 | 14:00          | 14:30          | 14:30             |
|       11 |        2 |        30 | 16:15          | 15:15          | 15:15             |

Sol attempt `015f333def696026a8ccb13a` on `token6r-09` (valid, 7,260 against 6,975):

|   Review |   Weight |   Minutes | Original UTC   | Observed UTC   | One optimum UTC   |
|---------:|---------:|----------:|:---------------|:---------------|:------------------|
|        0 |        3 |        45 | 14:00          | 11:30          | 11:30             |
|        1 |        5 |        30 | 16:45          | 14:45          | 16:45             |
|        2 |        5 |        45 | 12:15          | 13:15          | 13:15             |
|        3 |        5 |        30 | 09:45          | 09:30          | 09:30             |
|        4 |        3 |        45 | 19:15          | 18:30          | 18:30             |
|        5 |        3 |        30 | 15:45          | 10:00          | 10:00             |
|        6 |        2 |        45 | 10:00          | 12:30          | 12:30             |
|        7 |        3 |        30 | 12:45          | 16:00          | 17:45             |
|        8 |        3 |        45 | 14:00          | 14:00          | 14:00             |
|        9 |        1 |        30 | 20:15          | 15:15          | 15:15             |
|       10 |        1 |        45 | 10:15          | 19:15          | 19:15             |
|       11 |        5 |        30 | 09:45          | 10:45          | 10:45             |

Luna attempt `010ddb8d43cddf109a8b781a` on `token6r-03` ("Review 5: protected availability conflict for carol; Reviews 1,8: room overlap; Schedule does not have minimum total penalty points"):

|   Review |   Weight |   Minutes | Original UTC   | Observed UTC   | One optimum UTC   |
|---------:|---------:|----------:|:---------------|:---------------|:------------------|
|        0 |        4 |        45 | 11:30          | 09:30          | 12:00             |
|        1 |        2 |        30 | 15:15          | 15:45          | 15:30             |
|        2 |        2 |        45 | 12:00          | 10:45          | 10:15             |
|        3 |        1 |        30 | 11:30          | 14:00          | 14:00             |
|        4 |        4 |        45 | 19:45          | 11:30          | 16:30             |
|        5 |        5 |        30 | 20:15          | 13:15          | 19:15             |
|        6 |        2 |        45 | 11:45          | 12:15          | 13:00             |
|        7 |        4 |        30 | 20:15          | 17:30          | 20:30             |
|        8 |        3 |        45 | 11:00          | 16:00          | 11:00             |
|        9 |        4 |        30 | 13:00          | 14:45          | 14:45             |
|       10 |        5 |        45 | 16:45          | 20:00          | 17:30             |
|       11 |        4 |        30 | 20:15          | 18:00          | 20:00             |

Blocks (`frontier_v6/paired.csv`, adaptive stops from `blocks.csv`), numbered 1 to 4 as in the figures:

| Model       |   Block |   Uniform mixed |   Adaptive mixed |   Adaptive minus uniform |   Adaptive abandoned |
|:------------|--------:|----------------:|-----------------:|-------------------------:|---------------------:|
| GPT-6.1 Sol |       1 |               2 |                2 |                        0 |                    0 |
| GPT-6.1 Sol |       2 |               1 |                2 |                        1 |                    0 |
| GPT-6.1 Sol |       3 |               0 |                0 |                        0 |                    3 |
| GPT-6.1 Sol |       4 |               1 |                0 |                       -1 |                    3 |
| GPT-6 Luna  |       1 |               0 |                0 |                        0 |                    2 |
| GPT-6 Luna  |       2 |               0 |                0 |                        0 |                    2 |
| GPT-6 Luna  |       3 |               0 |                0 |                        0 |                    2 |
| GPT-6 Luna  |       4 |               0 |                0 |                        0 |                    2 |

Uniform group `07b44195df3709695b3f-0` (Sol, `token6r-07`) scored 1, 0, 0, 1, with leave-one-out comparisons 0.6667, −0.6667, −0.6667 and 0.6667. No complete uniform mixed group in this comparison began with an agreeing pair (`groups.csv`, column `missed_after_unanimous_probe`). Luna's adaptive group `0254d3ce9b34c5e58c43-0` on `token6r-01` stopped after 0, 0.

Shared-prefix check (declared in the protocol, labelled post hoc there; `shared_eligible_sensitivity.csv`). Each pair of block runs is cut at the smaller of their eligible spends, so neither collector gets credit beyond the other's last eligible call. Sol then has 4 and 4 mixed groups at 23,936,942 shared tokens per collector, and Luna 0 and 0 at 23,799,373.

Incomplete groups with both outcomes (added after inspecting the boundary groups; `known_contrast_diagnostic.csv`, figure `figures/token6_partial_contrast.png`). This counts a group cut off at the budget when its known rewards already include a 0 and a 1; the unknown attempt stays unknown. It does not replace the measure, which needs four known outcomes.

| Model       | Collector   |   Complete mixed |   Additional partial contrast |   All observed contrast |
|:------------|:------------|-----------------:|------------------------------:|------------------------:|
| GPT-6.1 Sol | uniform     |                4 |                             2 |                       6 |
| GPT-6.1 Sol | adaptive    |                4 |                             0 |                       4 |
| GPT-6 Luna  | uniform     |                0 |                             0 |                       0 |
| GPT-6 Luna  | adaptive    |                0 |                             0 |                       0 |

Sol's uniform collector has two such groups, so including them gives 6 against 4. The first by ID is `0ae35e1ada8438698a7a-1` on `token6r-09` (block 3), with rewards 1, 0, 0 and one unknown. In the figure, the solid part of each bar is complete mixed groups and the hatched part these incomplete groups.

Actual spend per model and collector (`summary.csv`). The eligible calls end at 95,638,261 tokens in all, because whole calls can leave unused room before a boundary.

| Model       | Collector   |   CLI calls |   Input tokens |   Output tokens |   Actual total |   Beyond cutoff |
|:------------|:------------|------------:|---------------:|----------------:|---------------:|----------------:|
| GPT-6.1 Sol | uniform     |         677 |       22113174 |         1991442 |       24104616 |          104616 |
| GPT-6.1 Sol | adaptive    |         678 |       22152523 |         1950870 |       24103393 |          103393 |
| GPT-6 Luna  | uniform     |         352 |       23883331 |          321733 |       24205064 |          205064 |
| GPT-6 Luna  | adaptive    |         354 |       23976312 |          312340 |       24288652 |          288652 |

The resources figure (`figures/token6_resources.png`) stacks each collector's eligible tokens and its crossing calls against the dashed 24-million line in the left panel, and splits output into reasoning and other output in the right panel. The left panel's four bars are near-identical by design.

Known failures by type (`failure_types.csv`). The two Sol "action horizon" attempts ended on valid but costlier agendas, so the README counts 41 valid costlier Sol failures; Luna's protocol violation is the withheld reply.

| Model       | Final failure type            |   Known failures |
|:------------|:------------------------------|-----------------:|
| GPT-6 Luna  | business constraint violation |               34 |
| GPT-6 Luna  | feasible higher-cost plan     |                1 |
| GPT-6 Luna  | protocol violation            |                1 |
| GPT-6.1 Sol | action horizon                |                2 |
| GPT-6.1 Sol | business constraint violation |                3 |
| GPT-6.1 Sol | feasible higher-cost plan     |               39 |

## Related work noted during the study

The adaptive collector is a collection-only adaptation of SARA, not a replication of its training results. [VIGOR](https://arxiv.org/abs/2607.22002) allocates attempts progressively from observed reward variance. [PAIR](https://arxiv.org/abs/2608.11368) explains why adaptive inclusion changes the distribution of observed pairs, so deterministic stopping cannot give an unbiased full-pool gradient. [SERA](https://arxiv.org/abs/2609.36552) targets scale equalisation for a different objective, MaxRL. [Aperture](https://arxiv.org/abs/2610.25325) needs a trained probe, which this no-training study does not have. [CERO](https://arxiv.org/abs/2610.09679) (Zong et al., 2026) studies prompt exposure and budget pacing over a training run, and [Adaptive Decoding Methods for Token-Efficient Reinforcement Learning](https://arxiv.org/abs/2610.25860) (Li et al., 2026) token-support schedules during training, which the CLI does not expose. [Diagnosing and Correcting Reward Hacking in Verifiable Instruction Following](https://arxiv.org/abs/2610.19525) (Yoon et al., 2026) is another reason to check rewards against the real requested outcome, as the check here does with the final calendar; this study does not test that paper's method. Reasoning output is counted inside output, following the [official reasoning-token accounting](https://developers.openai.com/api/docs/guides/reasoning). The earlier README recorded checking the research links on 24 October 2026; `frontier_v6/research_checks.json` and `reading_checks.json` record the checks of 26 October 2026.
