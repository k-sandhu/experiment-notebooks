# Collecting scored attempts to train a small model

## Learning by trying

One way to improve a language model is to let it practise. The model tries a task, a program checks the result, and the model is then adjusted so that it becomes more likely to repeat what it did in its better tries. Done over many tasks and many tries, this is called reinforcement learning. [DeepSeekMath](https://arxiv.org/abs/2402.03300) is one published example: its authors used it to improve a model's maths answers.

Practice of this kind needs two things before any training starts. The first is a program that sets the task, accepts the model's moves and scores them. Such a program is called an environment. The second is a record of every try: what the model was shown, what it chose, what happened next and how each step was scored. Training papers call one recorded try a rollout. This page calls it an attempt.

A useful collection is a set of attempts whose scores can be trusted and which separate better tries from worse ones. Collecting it costs model calls, and a team pays that cost before it learns whether the attempts will teach the model anything. This experiment is about that collection step. It trains no model.

### A small maze (illustrative)

Here is a made-up case that uses the real scoring rules of the maze environment in this study. A model is shown a 4 by 4 grid with a few walls. It starts in one square, and the exit is two squares away: one square up, then one square to the right. On each turn the model names one direction. The environment moves it, or reports a wall and leaves it where it was.

The environment scores every move. An ordinary move into a new square costs 0.05 points, and reaching the exit earns 10. The two-move route therefore scores -0.05 + 10 = 9.95. These per-move scores are the step rewards. If the model first walks into a wall, that bump costs 0.75, and the same route then totals 9.20.

There is also a simpler question: did the model reach the exit within ten moves? The answer is recorded as 1 or 0 and is called the outcome. Both routes above have outcome 1. A model that walks into the same wall ten times in a row has outcome 0, whatever its step rewards add up to. In this study the outcome decides success; the step rewards are kept beside it.

### Why a group of attempts needs both a success and a failure

The training methods this collection prepares for learn by comparison. The model tries the same maze four times. Suppose one try reaches the exit and three do not, so the outcomes are 0, 0, 1, 0. Their average is 0.25. The successful try is above the average, so a trainer would make its choices more likely. The three failures are below it, so their choices would become less likely.

Now suppose all four tries fail: 0, 0, 0, 0. Every try equals the average, and there is nothing to push towards. The same is true when all four succeed. Those four attempts cost model calls and teach nothing under this rule. This page calls a group of four attempts at one task a **mixed group** when it holds at least one success and at least one failure. The number of mixed groups is the measure of how useful a collection is.

### Why collection can be wasteful

A maze attempt can take ten model calls, one per move. A question takes one. A small model that almost never finds a maze exit produces group after group of four failures, so most of the calls spent on mazes buy nothing. A model that answers an easy question right every time wastes calls in the other direction. The tasks worth collecting are the ones the model solves some of the time.

### Two ways to spend less

The plain approach is to give every task the same number of tries, here four. It is easy to run and easy to check, and it spends as much on hopeless tasks as on useful ones.

The first alternative is to stop early. Watch the first few tries at a task. If the first three all fail, or all succeed, skip the fourth, on the reasoning that it is unlikely to differ. This saves calls, but it can throw away a group whose fourth try would have been its first success.

The second alternative is to choose where the next round of tries goes. After a first round, give more tries to tasks whose results so far suggest the model solves them some of the time, and prefer cheap tasks (one call) over expensive ones (up to ten calls). This could find more mixed groups for the same spend, or it could chase noise in four results.

A team that plans to train a small model needs to know whether that model produces mixed groups at all on its tasks, and whether either shortcut keeps them while spending less. On 28 September 2026 Hugging Face [made such environments easy to find on its Hub](https://huggingface.co/blog/rl-environments), and several 2026 papers proposed stopping and choosing rules for large training runs. This experiment tries those rules at small scale, with two small models, on tasks generated for the experiment so that every answer can be checked exactly.

## The question

Two small open-weight models (models whose trained weights are published, so anyone can run or train them), Llama 3.2 3B and Gemma 3 4B, each make four scored attempts at 8 freshly generated tasks: 4 mazes and 4 questions (two arithmetic expressions and two lists of words to reverse). How many of these groups of four contain both a success and a failure, which is what training by comparison needs? And would stopping a task once its first attempts agree, or choosing second-round tasks from the first round's scores, find those groups with fewer model calls?

## Study summary

Each model made four attempts at each of the 8 tasks, which gives 16 groups and 64 attempts in a first round. A second round spent 16 more attempts on 4 tasks chosen from the first round's scores. That is 80 attempts and 336 model calls in all. Every reply that came back could be read and scored; 6 Llama attempts got no reply because the provider rate-limited the requests, which left 3 of Llama's 8 first-round groups incomplete.

Only **2 of the 13 complete first-round groups** were mixed, both from Llama (`maze-01` and `reason-03`). Mazes were the main obstacle: 1 of 29 scored maze attempts reached the exit, against 11 of 30 question attempts. Gemma's maze results sit at the floor (0 of 16), and in 7 of its 8 groups its four attempts were identical, move for move or word for word, so repeating a task gave it no contrast at all.

Replayed on the saved attempts, the early-stop rule would have used 193 of the 261 calls spent on complete groups (26% fewer) and kept both mixed groups. With four tries per task, the rule amounts to skipping the fourth try when the first three agree. The score-guided second round chose four question tasks; of the 3 groups that finished complete, none was mixed.

In the original situation: most of what a small model's practice cost here went on groups that would teach a trainer nothing, above all maze attempts it never solved (288 of the 336 calls bought 1 success). Skipping obvious repeats saves about a quarter of the calls; the larger need is tasks the model solves some of the time, and attempts that actually differ from each other.

The main caveat is size: eight tasks and two models give counts too small to rank the collection plans, and the early-stop saving is a replay on attempts that were all collected and paid for.

## Contents

1. [The eight tasks and how answers are checked](#1-the-eight-tasks-and-how-answers-are-checked)
2. [How an attempt runs and is scored](#2-how-an-attempt-runs-and-is-scored)
3. [The models](#3-the-models)
4. [The measure and the collection plans](#4-the-measure-and-the-collection-plans)
5. [How the study got here](#5-how-the-study-got-here)
6. [Results: successes and groups with both outcomes](#6-results-successes-and-groups-with-both-outcomes)
7. [Results: stopping early](#7-results-stopping-early)
8. [Results: choosing second-round tasks](#8-results-choosing-second-round-tasks)
9. [Error analysis](#9-error-analysis)
10. [What the evidence supports](#10-what-the-evidence-supports)
11. [Limitations](#11-limitations)
12. [Spend, data and how to run](#12-spend-data-and-how-to-run)
13. [Future work and further reading](#13-future-work-and-further-reading)

## 1. The eight tasks and how answers are checked

The tasks were generated in code with fixed seeds on 24 October 2026 and frozen in [`data/tasks.json`](data/tasks.json), each with a hash so a re-run scores the same items. Mazes have walls placed at random and routes of 2, 4, 6 and 8 moves. The questions come from Reasoning Gym, a library of generated puzzles with checkable answers.

| Task | What the model is asked | Correct answer | Model calls per attempt |
|---|---|---|---|
| `maze-01` | 4 by 4 map, start `[0,1]`, exit `[1,0]` | Shortest route 2 moves (up, right) | Up to 10 |
| `maze-02` | 4 by 4 map, start `[1,2]`, exit `[3,0]` | Shortest route 4 moves | Up to 10 |
| `maze-03` | 5 by 5 map, start `[4,3]`, exit `[0,3]` | Shortest route 6 moves | Up to 10 |
| `maze-04` | 5 by 5 map, start `[0,3]`, exit `[1,0]` | Shortest route 8 moves | Up to 10 |
| `reason-01` | `Calculate 2 - 40.` | `-38` | 1 |
| `reason-02` | `Calculate ( 551 * -29 ) + ( -355 * 717 - 71 ) * 164.` | `-41771363` | 1 |
| `reason-03` | Reverse the list `it, in, say, the, stress, copies` | `copies, stress, the, say, in, it` | 1 |
| `reason-04` | Reverse a 20-word list starting `to, Wilkins, change` | 20 words starting `bore, BUT, the` | 1 |

Positions are written `[column, row]`, counting from 0 at the top left. Each correct answer is established without a language model. For mazes, breadth-first search (which checks every square one move away, then every square two moves away, and so on) finds a shortest route and proves the exit can be reached within ten moves; the model never sees that route. The arithmetic is recomputed by a small evaluator that accepts only numbers, `+`, `-`, `*` and brackets, and the list reversal by reversing the word list in Python; both must agree with Reasoning Gym's answer. No language model wrote or graded any task. Before any model was called, each task was solved through the same environment using the known answer, and all 8 passed ([`data/environment_smoke.json`](data/environment_smoke.json)).

The tasks were created after both models were released (Llama 3.2 on 25 September 2024, Gemma 3 on 12 March 2025), so no model can have seen these boards, expressions or lists. The task types are old, and the reversal words come from Reasoning Gym's bundled vocabulary, which [`data/provenance.json`](data/provenance.json) records as public-domain Jules Verne text. The freshness rules out memorised items, not familiarity with mazes, arithmetic or list reversal.

The environments are the official maze and Reasoning Gym environments from [OpenEnv 0.10.0](https://github.com/huggingface/OpenEnv/tree/v0.10.0), Hugging Face's library for running such programs, run on the local machine. A frozen page of the Hub listing ([`data/hub_catalogue.json`](data/hub_catalogue.json)) holds 200 entries, 43 tagged `openenv`; this study generates its own tasks and scores no Hub benchmark.

## 2. How an attempt runs and is scored

An attempt begins when the environment starts a fresh copy of the task. For a maze, the model then sees this message (the first request of attempt `uniform-maze-01-meta-llama-2`, copied from its cache file):

```text
Reach the exit in this grid. Coordinates are [column,row]; [0,0] is top left. 0=up (row-1), 1=down (row+1), 2=left (column-1), 3=right (column+1). In the map 1 is a wall and 0 is a free square. Return ONLY JSON with one integer field, for example {"action": 3}. Choose a legal move toward the exit.
{"exit":[1,0],"legal_actions":[0,1],"map":[[0,0,0,0],[0,1,0,1],[0,0,1,0],[0,0,1,0]],"moves_remaining":10,"position":[0,1]}
```

The reply must be JSON with one field, `action`, holding 0, 1, 2 or 3; the provider enforces that shape. The environment applies the move and returns the new position, which goes into the next message together with the conversation so far. This repeats until the model reaches the exit or uses its ten moves. A question gets one message ("Solve the task. Return only the final answer in the requested format, without explanation or Markdown.") and one reply.

```mermaid
flowchart LR
    reset["Environment starts a fresh attempt"] --> obs["Message to the model<br/>map, position, legal moves, moves left<br/>(or the question)"]
    obs --> llm["Llama 3.2 3B or Gemma 3 4B<br/>one OpenRouter call, one reply"]
    llm --> raw["Full reply saved to the cache<br/>read as JSON move or answer text"]
    raw --> step["Environment applies the move<br/>new position and step reward"]
    step -->|"maze not finished and moves left<br/>(next call waits for this result)"| obs
    step -->|"exit reached, 10 moves used,<br/>or question answered"| record["Attempt saved<br/>step rewards and outcome 1/0"]
    raw -->|"no reply, unreadable reply<br/>or reply cut off"| record
```

The environment's step rewards follow fixed rules, checked for every move by an audit in the notebook:

| Event | Step reward |
|---|---|
| Maze move into a wall or off the edge (the model stays put) | -0.75 |
| Maze move into a square not visited before | -0.05 |
| Maze move into a square visited before | -0.25 |
| Maze move onto the exit | +10 |
| Question answer that matches exactly | 1 |
| Question reply that contains the exact answer inside longer text | answer length divided by reply length |
| Any other question reply | 0 |

The outcome is stricter. A maze attempt scores 1 only if the environment reports the exit reached within ten moves. A question scores 1 only if the reply, with spaces and line breaks trimmed from its ends, equals the frozen answer.

An attempt can fail in three ways, and they are counted apart. It can get no reply, when the provider returns an error. It can get a reply the program cannot score: an empty reply, a maze reply that is not the required JSON, or a reply cut off at its length limit. These two end the attempt and are never repaired or retried. Or it can get a readable reply that is wrong.

## 3. The models

| Model | Pinned version | Provider and how called | Size and precision | Settings | Why included |
|---|---|---|---|---|---|
| Llama 3.2 3B Instruct | Dated version not recorded; OpenRouter returned the undated slug `meta-llama/llama-3.2-3b-instruct`. Model-card revision `0cb88a4f` checked on 2026-10-24 | OpenRouter, pinned to Parasail with no fallback | 3 billion parameters, BF16 | Temperature 0.9, top-p 1.0; 48 output tokens per maze move, 256 per question; a recorded seed per attempt | Small open-weight model that could later be trained locally; the one model whose provider returned token probabilities, which a trainer needs |
| Gemma 3 4B Instruct | Dated version not recorded; OpenRouter returned `google/gemma-3-4b-it`. Model-card revision `093f9f38` checked on 2026-10-24 | OpenRouter, pinned to DeepInfra with no fallback | 4 billion parameters, BF16 | Same as Llama | Small open-weight model from a second maker, so the result does not rest on one model family |

Llama 3.2 was released on 25 September 2024, and its [model card](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct) gives a December 2023 knowledge cutoff. Gemma 3 was [released on 12 March 2025](https://blog.google/innovation-and-ai/technology/developers-tools/gemma-3/); no cutoff was verified from its model card, so the release date serves as the freshness boundary (OpenRouter's catalogue snapshot in [`data/model_catalogue.json`](data/model_catalogue.json) lists 31 August 2024). Both models carry custom licences (the Llama 3.2 Community License and the Gemma Terms of Use) rather than unrestricted open-source licences, which a later training use would need to check. The notebook does not record why these two were chosen over newer small models.

## 4. The measure and the collection plans

### Mixed groups and comparison scores

A **group** is the four attempts one model makes at one task in one round. A group is **complete** when all four attempts got a scored outcome; a provider error makes it incomplete. A complete group is **mixed** when it holds at least one success and one failure. The main measure is the number of mixed groups. Higher is better, and each one is a task where a trainer has something to compare.

Within a group, each attempt gets a **comparison score** (training papers call it the advantage): its outcome minus the group's average outcome, divided by the spread of the four outcomes (their standard deviation). For outcomes 0, 0, 1, 0 the average is 0.25 and the spread is 0.433. The success gets (1 - 0.25) / 0.433 = +1.73 and each failure gets (0 - 0.25) / 0.433 = -0.58. For 0, 1, 0, 1 the scores are -1, +1, -1, +1. For 0, 0, 0, 0 the spread is zero and every score is 0. This within-group rule is the one used by GRPO, the training method introduced in [DeepSeekMath](https://arxiv.org/abs/2402.03300). The notebook also saves the scores without the division by the spread, a choice that [Dr. GRPO](https://arxiv.org/abs/2503.20783) discusses. No score is used to train anything here.

### The fixed plan

Every model makes four attempts at every task: 64 attempts in the first round. This is the simplest plan and the baseline. Because every group was collected in full, it also serves as an audit: each shortcut below can be checked against what the full groups contained.

### The early-stop rule

After each attempt, the rule estimates the chance that the group will end up mixed by its fourth attempt, given the outcomes so far. It always makes at least two attempts. It stops and keeps the group as soon as the outcomes are mixed, and it gives up on the task once the chance falls below 0.30. With n identical outcomes so far, the estimate (starting with no preference between success and failure) is (4 - n) / 5. After two failures it is 0.4, so the rule continues; after three it is 0.2, so it stops. With a cap of four attempts, the rule therefore skips the fourth attempt whenever the first three agree.

The rule comes from [SARA](https://arxiv.org/abs/2607.26253) (Nomand et al., 2026), which also moves the saved calls to new tasks. Here it is replayed on the first-round attempts in the order they were collected. At each point it sees only the attempts it would have collected by then, and the full group afterwards shows what it missed. All four attempts were collected and paid for, so the replay measures calls that could be saved, not money that was saved, and it does not test spending those calls elsewhere.

### The score-guided second round

After the first round, each task gets an estimated success rate from its four outcomes, with a mild correction so that 0 of 4 is not read as impossible: (successes + 0.5) / 5. So 0 of 4 gives 0.1, 1 of 4 gives 0.3 and 4 of 4 gives 0.9. Each task then gets a score that is highest when its estimate is close to a target rate, with closeness judged more loosely when the estimate is uncertain. The target is the average estimate of the model's mixed tasks (Llama: 0.30, with a tolerance of 0.05), or 0.5 with a tolerance of 0.15 when the model has none (Gemma). The score is divided by the average number of calls per attempt, which favours one-call questions over mazes. Two tasks per model are drawn at random with chances in proportion to these scores, and each gets four new attempts. Tasks whose first-round group was incomplete are not eligible.

The rule comes from [RIDGE](https://arxiv.org/abs/2610.25330) (Duncun et al., 2026), where the cost was the number of web-tool calls; here it is model calls per attempt. The simplest alternative, drawing two tasks with equal chances, was not run, so the second round is described rather than compared.

### The coverage bonus

When every attempt in a maze group fails, all comparison scores are zero. The coverage bonus gives such a group something to compare: the share of each attempt's moves that reached a square not visited before. Those shares are turned into scores within the group the same way as outcomes, then multiplied by 0.25 so they stay small. The outcomes stay 0. The bonus applies only to all-failed maze groups whose attempts differ in coverage. It comes from [CovGPO](https://arxiv.org/abs/2607.22724v2) (Yang et al., 2026), and its known risk is that it rewards wandering.

### How the study runs

```mermaid
flowchart TD
    T["8 tasks generated in code on 2026-10-24<br/>4 mazes + 4 questions, answers known"] --> E["OpenEnv maze and Reasoning Gym environments, run locally<br/>8 of 8 tasks solved with the known answer first"]
    E --> R1["First round, fixed plan<br/>2 models x 8 tasks x 4 attempts = 64 attempts<br/>320 model calls through OpenRouter"]
    R1 --> G["16 groups: 13 complete, 3 incomplete<br/>(5 Llama attempts got no reply, HTTP 429)<br/>2 mixed groups"]
    G --> STOP["Early-stop rule replayed on the 13 complete groups<br/>193 of 261 calls, 2 of 2 mixed groups kept"]
    G --> COV["Coverage bonus on the 5 all-failed maze groups<br/>gives scores to 1"]
    G --> PICK["Score-guided choice<br/>2 question tasks per model"]
    PICK --> R2["Second round: 4 tasks x 4 attempts = 16 attempts, 16 calls<br/>1 no reply; 3 complete groups, 0 mixed"]
    STOP --> OUT["80 saved attempts with step rewards, outcomes and scores<br/>no model trained"]
    COV --> OUT
    R2 --> OUT
```

### One task from start to finish

Llama's four attempts at `maze-01` pass through every step of the diagram. The maze is the 4 by 4 grid from the prompt above. The start is `[0,1]`, the exit `[1,0]`, and the shortest route is up, then right.

Attempt `uniform-maze-01-meta-llama-2` went like this:

| Move | Reply | Move asked for | Position after | Step reward |
|---|---|---|---|---|
| 1 | `{"action": 3}` | right, into the wall at `[1,1]` | `[0,1]` | -0.75 |
| 2 | `{"action": 0}` | up | `[0,0]` | -0.05 |
| 3 | `{"action": 3}` | right, onto the exit | `[1,0]` | +10 |

The step rewards total -0.75 - 0.05 + 10 = 9.20, one wall bump short of the best possible 9.95, and the outcome is 1. The attempt used 3 model calls. The full first reply in the cache is `{"role": "assistant", "content": "{\"action\": 3}", "refusal": null, "reasoning": null}`, and the [cache file](data/cache/07d7dfffe06f1640d4db7dcf301ae3abcf3a2dfb01d7270e3f33e677ab597428.json) holds the request, finish reason, token probabilities and token counts.

The other three attempts failed. Attempt 0 asked to move right ten times and never left the start (step rewards -7.50). Attempts 1 and 3 wandered and ran out of moves (-3.70 and -4.20). The group's outcomes are 0, 0, 1, 0, so it is mixed, and the comparison scores are +1.73 for attempt 2 and -0.58 for each of the others. The four attempts used 10 + 10 + 3 + 10 = 33 calls.

The early-stop rule saw a failure after attempt 0 (its minimum is two attempts), a second failure after attempt 1 (chance of a mix 0.4, continue), then the success in attempt 2, which made the group mixed, so it stopped and kept the group after 23 calls instead of 33. Had the success come in attempt 3 instead, the rule would have stopped after three failures and lost the only mixed maze group in the study.

The score-guided choice gave this task an estimated success rate of 0.3, exactly on Llama's target. But its attempts cost 8.25 calls on average, so its chance of being drawn first was 5.8%, against 47.6% for `reason-03`, which had the same 1 success in 4 at one call per attempt. It was not chosen for the second round.

## 5. How the study got here

Two setup requests, sent before the measured collection on 24 October 2026, changed the design. Both are saved in `data/pilot_cache/`, left out of the results and counted in the spend.

The first asked Llama for "ONLY one digit 0, 1, 2, or 3" with a 16-token limit. Llama replied in prose ("Based on the provided information, we can see that the current position is (0") and ran out of tokens. Maze replies were therefore changed, for both models, to JSON constrained to one `action` field, with the example `{"action": 3}` in the prompt and a 48-token limit. The second request, to Gemma on the Parasail provider, was refused with HTTP 429 (rate limited), so Gemma was pinned to DeepInfra, which does not return token probabilities. The measured collection then ran once, between 09:22 and 09:27 Toronto time. The full history is in [`data/PROTOCOL.md`](data/PROTOCOL.md).

## 6. Results: successes and groups with both outcomes

The success rates come first, because a model that never or always succeeds at a task cannot produce a mixed group there.

![Bar chart of exact success rates in the first round: Llama 1 of 13 scored maze attempts, Gemma 0 of 16; Llama 3 of 14 scored question attempts, Gemma 8 of 16; error bars from resampling the four tasks](figures/success_rates.png)

Each bar is one model on one kind of task, blue for Llama and hatched orange for Gemma. The height is the share of first-round attempts with a known outcome that succeeded; the label above it, such as "1/13 valid", gives successes over attempts with a known outcome, so provider errors are left out. The error bars come from resampling the four tasks 5,000 times. With four tasks they carry little information (Gemma's question interval runs from 0% to 100%), so the per-task table below is the better view.

Mazes were far harder than questions for both models: 1 of 29 scored maze attempts reached the exit (Llama 1 of 13, Gemma 0 of 16), against 11 of 30 question attempts (Llama 3 of 14, Gemma 8 of 16). Gemma's maze result is a floor. If Llama's 5 first-round attempts without a reply are counted as failures, its rate is 4 of 32 instead of 4 of 27; if they are counted as successes, 9 of 32. Gemma's 8 of 32 lies inside that range, so the two models cannot be ranked overall. The per-task results come from the outcome lists printed by the notebook's collection step and [`data/groups.csv`](data/groups.csv).

| Task | Llama 3.2 3B, first round | Gemma 3 4B, first round | Second round |
|---|---|---|---|
| `maze-01` | 1 of 4 (0, 0, 1, 0), mixed | 0 of 4 | |
| `maze-02` | 0 of 2, 2 no reply | 0 of 4 | |
| `maze-03` | 0 of 3, 1 no reply | 0 of 4 | |
| `maze-04` | 0 of 4 | 0 of 4 | |
| `reason-01` | 2 of 2, 2 no reply | 4 of 4 | |
| `reason-02` | 0 of 4 | 0 of 4 | Llama 0 of 4 |
| `reason-03` | 1 of 4 (1, 0, 0, 0), mixed | 4 of 4 | Llama 0 of 3, 1 no reply; Gemma 4 of 4 |
| `reason-04` | 0 of 4 | 0 of 4 | Gemma 0 of 4 |

Apart from the 6 attempts that got no reply, every failure was a readable reply that was wrong. The table below sorts all 80 attempts (from [`data/episodes.jsonl`](data/episodes.jsonl), field `stop_reason`).

| Model | Round | Attempts | No reply (HTTP 429) | Unreadable reply | Wrong | Succeeded |
|---|---|---|---|---|---|---|
| Llama 3.2 3B | First | 32 | 5 | 0 | 23 | 4 |
| Llama 3.2 3B | Second | 8 | 1 | 0 | 7 | 0 |
| Gemma 3 4B | First | 32 | 0 | 0 | 24 | 8 |
| Gemma 3 4B | Second | 8 | 0 | 0 | 4 | 4 |
| Total | | 80 | 6 | 0 | 58 | 16 |

All 330 replies that came back ended normally and could be scored. Of the 58 wrong attempts, 28 were mazes that used all ten moves without reaching the exit and 30 were wrong answers to questions. Ten of the wrong arithmetic answers included working despite the instruction to return only the answer, but their final numbers were also wrong, and the environment's partial-credit rule, which rewards a correct answer inside longer text, gave none of the 30 any credit. So no reply was a right answer in the wrong format.

![Bar chart counting complete first-round groups by type: Llama 3 all failed, 2 mixed, 0 all succeeded; Gemma 6 all failed, 0 mixed, 2 all succeeded](figures/group_signal.png)

This chart counts the 13 complete first-round groups by type: all four failed, mixed, or all four succeeded. Blue is Llama (5 complete groups), hatched orange Gemma (8). Only the middle pair matters for training by comparison.

Only 2 of 13 complete groups were mixed, and both were Llama's: `maze-01` and `reason-03`, each with 1 success in 4. Llama had 3 all-failed groups; 3 more of its groups were incomplete. Gemma had 6 all-failed and 2 all-succeeded groups. So 11 of 13 complete groups give every attempt a comparison score of zero, including Gemma's two perfect groups. A model can score better on a task and still give a trainer less to learn from it.

Gemma's lack of mixed groups has a visible cause in its replies. In 7 of its 8 first-round groups, its four attempts were identical: the same ten moves on each maze, the same text on three of the four questions (counted from `data/episodes.jsonl`, comparing each attempt's moves or trimmed reply). Only `reason-02` drew different replies, three distinct wrong numbers. Llama's attempts differed in every maze group; its only exact repeats were the two `-38` answers to `reason-01` and two identical wrong reversals of `reason-03`. With identical attempts, a group of four is one attempt paid for four times. Section 9 shows examples.

The coverage bonus gave scores to 1 of the 5 complete all-failed maze groups, Llama's `maze-04`. Gemma's four all-failed maze groups had identical moves, so their coverage did not differ and the bonus stayed zero. With the bonus, 12 attempts in complete groups have a non-zero score instead of 8 ([`data/advantages.jsonl`](data/advantages.jsonl)). Section 9 shows that the extra scores reward the wrong attempts.

## 7. Results: stopping early

![Bar chart of model calls on the 13 complete first-round groups: all four attempts used 85 Llama calls and 176 Gemma calls; the early-stop rule would have used 61 and 132](figures/sara_cost.png)

The left pair of bars is the calls actually made on the 13 complete first-round groups, per model; the right pair is the calls the early-stop rule would have made on the same groups. The right-hand calls are a subset of the left-hand ones, not a separate collection: every call was made and paid for. The chart's labels use the code name SARA for the early-stop rule and "counterfactual" for the replay.

| Model | Complete groups | Attempts, all four | Attempts, early stop | Calls, all four | Calls, early stop | Mixed groups kept |
|---|---|---|---|---|---|---|
| Llama 3.2 3B | 5 | 20 | 14 | 85 | 61 | 2 of 2 |
| Gemma 3 4B | 8 | 32 | 24 | 176 | 132 | 0 of 0 |

The rule would have used 38 of 52 attempts and 193 of 261 calls, 68 fewer (26.1%), and it kept both mixed groups. It gave up on all 11 groups whose first three outcomes agreed, and stopped the two mixed groups as soon as they mixed. Of the 68 calls it would have skipped, 56 were fourth attempts at tasks whose first three agreed and 12 were attempts after a group had already mixed; 60 of the 68 were maze calls, because a maze attempt costs up to ten times as much as a question (counted from [`data/sara_decisions.jsonl`](data/sara_decisions.jsonl), field `audit_only_calls`).

No mixed group was lost, but the only mixed maze group survived by one attempt (Section 4). Gemma's `maze-01` group shows the ordinary case: three failures, the chance of a mix fell to 0.2, and the rule would have stopped at 30 calls instead of 40; the fourth attempt was the same ten moves again. The three incomplete Llama groups are left out of these numbers, because stopping after a provider error would otherwise count as a saving. And the calls saved were not spent on new tasks, so the replay cannot say whether moving them would have found more mixed groups.

## 8. Results: choosing second-round tasks

![Bar chart of each task's chance of being drawn first by the score-guided choice, per model; stars mark the four chosen model and task pairs; x marks Llama tasks left out after provider errors; a dashed line marks one in eight](figures/ridge_selection.png)

Each pair of bars is one task. The height is the task's share of the model's total score, which is its chance of being drawn as the first of the two picks (the axis calls this the "normalized RIDGE sampling score"). Stars mark the tasks actually chosen; an x marks a Llama task that was not eligible because a provider error left its first-round group incomplete. The dashed line at 1/8 is the chance with equal draws over eight tasks. It fits Gemma, but Llama had only 5 eligible tasks, so its equal-draw chance would be 1/5.

| Model | Chosen task | First-round result | Estimated success rate | Calls per attempt | Chance of being drawn first |
|---|---|---|---|---|---|
| Llama 3.2 3B | `reason-02` | 0 of 4 | 0.10 | 1.00 | 22.2% |
| Llama 3.2 3B | `reason-03` | 1 of 4 | 0.30 | 1.00 | 47.6% |
| Gemma 3 4B | `reason-03` | 4 of 4 | 0.90 | 1.00 | 22.7% |
| Gemma 3 4B | `reason-04` | 0 of 4 | 0.10 | 1.00 | 22.7% |

The choice went only to questions. The cost division decided it: Llama's two mixed groups had the same estimate, 0.3, but `maze-01` got 5.8% because its attempts cost 8.25 calls, while `reason-03` got 47.6%. For Gemma the score could not tell its four questions apart. With no mixed group, its target sat at 0.5, and its estimates of 0.1 and 0.9 lie at equal distances from it, so all four questions scored 22.7% and the pick was a random draw among them ([`data/ridge_selection.csv`](data/ridge_selection.csv)).

The second round produced no mixed group. Gemma repeated its first-round results exactly: 4 of 4 on `reason-03`, 0 of 4 on `reason-04`. Llama failed all 4 attempts at `reason-02` and 3 attempts at `reason-03`, where its fourth got no reply, so that group is incomplete; it had solved `reason-03` once in the first round. Of the 15 second-round attempts with an outcome, 4 succeeded, all Gemma's. Because no new group was mixed, neither model's target moved (Llama stayed at 0.30 with tolerance 0.05, Gemma at 0.5 and 0.15). With two picks per model and Gemma's ties, this round is too small to say whether score-guided choice beats equal draws.

## 9. Error analysis

The examples below come from the first maze successes and failures, the first question successes and failures, the all-failed maze group with the most spread in coverage (the rule the notebook uses to pick them, saved in [`data/case_ids.json`](data/case_ids.json)), and from the groups that explain the results above.

![Four maze maps for Llama: maze-01 attempt 2 reaching the exit, maze-01 attempt 0 stuck at the start, maze-04 attempt 0 stuck at the start, and maze-04 attempt 1 moving along the bottom row](figures/maze_cases.png)

Each panel is one Llama attempt drawn on its map: black squares are walls, S the start, E the exit, and the line the path. The small numbers give the move after which the model was on that square, with 0 for the start; "0..10" means it was there from the start through move 10, because every move hit a wall. The panel title gives the outcome and why the attempt ended ("horizon" means it used all ten moves). Top left is the successful attempt from Section 4; top right is `uniform-maze-01-meta-llama-0`; the bottom row is `uniform-maze-04-meta-llama-0` and `-1`.

### Walking into the same wall

`uniform-maze-01-meta-llama-0` replied `{"action": 3}` (right) ten times. The square to the right of the start is a wall, so the model never moved, collected ten penalties of -0.75 (-7.50) and outcome 0. This was common for Llama: 72 of its 125 first-round maze moves (57.6%) were into a wall or off the edge, and 79 of the 125 (63%) asked for "right". The prompt's only example is `{"action": 3}`, which may pull the model towards "right", but no prompt without that example was tried, so the cause is open.

### Legal moves that go nowhere

Gemma made no illegal moves in 160 first-round maze moves and still reached no exit. On `maze-01`, all four of its attempts (`uniform-maze-01-google-0` to `-3`) made the same ten moves: down to `[0,2]`, then right and left between `[0,2]` and `[1,2]` until the moves ran out. The exit is up from the start. Its other three mazes show the same pattern of four identical attempts. The requests asked for temperature 0.9 and used a different seed for each attempt; the saved responses record nothing that shows why the replies were identical, so it is not known whether the model or the provider's sampling produced the repeats.

### When the step rewards mislead

Gemma's maze attempts average -1.95 in step rewards and Llama's -3.79 ([`data/results.csv`](data/results.csv), `mean_native_return`), so by step rewards Gemma did better. That comes from avoiding walls, not from progress: Gemma's back-and-forth costs 0.25 a move, Llama's wall bumps 0.75, and only Llama ever reached an exit. A collection judged by its step-reward totals would have preferred the model that never solved a maze, which is why the outcome decides success here.

The coverage bonus misleads in a similar way. In Llama's all-failed `maze-04` group, attempt `uniform-maze-04-meta-llama-0` never left the start, while `uniform-maze-04-meta-llama-1` moved down and along the bottom row, reaching three new squares. The exit is at `[1,0]`, at the top, so the second attempt went the wrong way.

![Two-panel bar chart for Llama's maze-04 group: coverage shares 0, 0.3, 0.3, 0.3 in the upper panel; coverage-bonus scores -0.43, +0.14, +0.14, +0.14 and outcome-only scores of zero in the lower panel](figures/coverage_signal.png)

The upper panel gives each of the four attempts' share of moves that reached a new square: 0, 0.3, 0.3 and 0.3. The lower panel gives the comparison scores: black dots are the outcome-based scores, all zero, and orange bars the coverage-bonus scores, -0.43 for the attempt that stayed put and +0.14 for each of the three that moved. The bonus would tell a trainer to prefer moving along the bottom row, away from the exit. Moving at all may still be better than ten wall bumps, but these four attempts cannot show that it leads towards the exit.

### A typical success

`uniform-reason-01-meta-llama-0` received `Calculate 2 - 40.` and returned `-38`: step reward 1, outcome 1. Gemma answered `-38` in all four attempts, so its group's comparison scores are all zero.

### Arithmetic that goes wrong early

`reason-02` asks for `( 551 * -29 ) + ( -355 * 717 - 71 ) * 164`, whose value is -41771363: 551 x -29 = -15979, -355 x 717 - 71 = -254606, and -15979 + (-254606 x 164) = -41771363. Every attempt by both models failed, in both rounds. `uniform-reason-02-meta-llama-0` returned `-66621503`. Gemma wrote out its working, against the instruction; in `uniform-reason-02-google-0` the first line is `-15995 + (-253735 - 71) * 164`, so the first product is already off by 16, and the final line is `-41753579`. A looser reader that took the last number would not have changed any of these scores.

### One task, two models, opposite usefulness

`reason-03` asks for the reverse of `it, in, say, the, stress, copies`. Gemma returned the exact answer, `copies, stress, the, say, in, it`, in all four first-round attempts and all four second-round attempts. Llama returned it once (`uniform-reason-03-meta-llama-0`); attempts 1 and 2 both returned `say, the, stress, copies, in, it`, which keeps the words but not the order. Gemma is the better model on this task and gives a trainer nothing; Llama's single success among three failures is one of the two useful groups in the study. In the second round, Llama's three answered attempts all failed, one of them `say the stress copies in it` without commas, so the contrast did not repeat.

### A near miss repeated eight times

`reason-04` asks to reverse a 20-word list. Gemma returned the same 19-word reply in all eight attempts across both rounds: it drops the first word, `bore`, and swaps `BUT` and `the`. Llama's four first-round replies were all different and all wrong: each drops or reorders several words, and one adds the word `second`, which is not in the list. For Gemma, the second round bought four more copies of an answer already seen four times.

### Lost attempts

All 6 provider errors were HTTP 429 replies ("temporarily rate-limited upstream") from Parasail serving Llama, between 09:24 and 09:26, and none was retried. In two of the lost groups the errors came late: `reason-01` had 2 successes before them, and `maze-03` had 3 failures, enough for the early-stop rule to give up before the fourth attempt's error.

These examples show what the models returned, not why. The pattern they share is that the groups with no contrast came from two sources: tasks the model could not do (most mazes, `reason-02`, `reason-04`) and, for Gemma, attempts that repeated each other exactly.

## 10. What the evidence supports

- Before collecting at scale, measure a small model's success rate per task, and drop or replace tasks it never solves. Here 288 of the 336 calls went to mazes and bought 1 success; the useful groups came from tasks solved once in four.
- Check that repeated attempts actually differ. Counting distinct replies per group is cheap, and it would have shown at once that Gemma's four attempts were one attempt repeated, which no stopping or choosing rule can fix.
- Skipping the fourth attempt when the first three agree is a safe, small saving on tasks like these: 26% fewer calls with no mixed group lost. With only one mixed maze group, and that one kept by a single attempt, the risk of losing late successes is not measured.
- Do not judge collection by step-reward totals or the coverage bonus alone. Here both favoured attempts that made no progress towards the exit.
- Score-guided choice found no new mixed groups, and for Gemma it reduced to a random draw among tied tasks. Whether it beats equal draws needs a larger task pool.

The uncertainty that most needs another experiment is whether the early-stop rule still keeps its mixed groups, and finds new ones, when the calls it saves are actually spent on fresh tasks of graded difficulty.

## 11. Limitations

Eight tasks, two models and one setting per model (one provider, temperature 0.9) make every count here an illustration rather than a rate. The tasks are freshly generated, but their types are old, and a model can know how to reverse a list without having seen this list.

The early-stop result is a replay on attempts collected in full and in a fixed order. A different order of the same attempts can change its decisions, and the replay does not test spending the saved calls on new tasks, which is how the rule is meant to be used.

Provider errors removed 3 of Llama's 8 first-round groups, and there is no reason to assume the lost attempts would have matched the rest. The ten-move limit is part of the task: a maze attempt that ran out of moves might have succeeded with more. The prompt's example move, `{"action": 3}`, was added after the setup request and may have shaped Llama's choices.

Both models were released in 2024 and 2025, and the notebook does not record why they were chosen over newer small models. Neither hosted provider confirms which weights, tokenizer or chat template it served, and the dated model version was not recorded.

The saved attempts are not ready-made training data. A trainer that updates a model needs attempts produced by that exact model, with its tokens and their probabilities; here the messages, moves and scores are saved, but token IDs, a confirmed weight version and Gemma's token probabilities are not, and every record is marked `exact_on_policy_ready=false` in [`data/rollouts_for_training_demo.jsonl`](data/rollouts_for_training_demo.jsonl). A later training run should collect again from the model it trains.

The notebook describes the early-stop threshold of 0.30 as set before collection, and the saved cache holds a single collection run; there is no separate preregistration file. The two design changes (Section 5) came before any measured attempt. Details are in [`data/PROTOCOL.md`](data/PROTOCOL.md).

## 12. Spend, data and how to run

| Item | Amount |
|---|---|
| Measured model calls | 336 (320 first round, 16 second round) |
| Setup requests | 2 |
| Failed requests (all HTTP 429) | 7 (6 measured, 1 setup) |
| Cost reported by OpenRouter | $0.0153 |
| Upper bound for the 7 failed requests, which reported no cost | $0.0019 |
| Prompt and completion tokens, including setup | 294,780 and 3,034 |
| Sum of request times | 234 seconds |

The total is under $0.018. Llama's token probabilities are saved as Parasail returned them; DeepInfra does not offer them for Gemma.

| File in `data/` | What it holds |
|---|---|
| `tasks.json` | The 8 frozen tasks with answers, seeds, creation time and hashes |
| `cache/` | One JSON file per model call: full request, full response, cost, time |
| `pilot_cache/` | The 2 setup requests |
| `episodes.jsonl`, `steps.jsonl` | All 80 attempts with every move, reply, step reward and outcome, and one row per move (the files call an attempt an episode; `uniform` is the first round, `ridge` the second) |
| `groups.csv`, `results.csv`, `advantages.jsonl` | Group types, success rates, comparison scores |
| `sara_decisions.jsonl`, `ridge_selection.csv`, `ridge_plans.json` | Early-stop decisions and score-guided choices |
| `rollouts_for_training_demo.jsonl` | All 80 attempts joined with their scores, in a training-style layout |
| `provenance.json`, `model_catalogue.json`, `endpoints_*.json`, `hub_catalogue.json`, `manifest.json`, `validation.json` | Model dates, licences, provider and Hub snapshots, package versions, file hashes, counts, spend and checks |
| `PROTOCOL.md` | Run history |

Running the notebook replays everything from the cache with no network calls; the environments run again on the local machine. Install the pinned packages in a separate virtual environment and run from this folder:

```bash
python -m pip install -r requirements.txt
python -m ipykernel install --user --name openenv-rewards
python -m nbconvert --to notebook --execute --inplace --ExecutePreprocessor.kernel_name=openenv-rewards 24_openenv_rewards.ipynb
```

A missing cache entry stops the run before any paid request. New collection needs `NB_LIVE=1` and an `OPENROUTER_API_KEY`, in a separate copy with empty `data/cache/` and `data/pilot_cache/` folders; the size settings and the 600-request and $2 caps sit at the top of the notebook. The full analysis is in [24_openenv_rewards.ipynb](24_openenv_rewards.ipynb).

## 13. Future work and further reading

### Future work

- Enlarge the task pool from 8 to at least 100 tasks of graded difficulty, with several seeds, and measure mixed groups per dollar. The present pool gave 2 mixed groups, too few to compare plans.
- Run the early-stop rule live, spending each skipped fourth attempt on a new task at the same total budget, and count mixed groups found and lost. Here the 68 skipped calls were only marked, not moved.
- Measure attempt diversity directly: repeat Gemma's groups at several temperatures and on a second provider, and count distinct replies per group. Gemma's attempts were identical in 7 of 8 groups.
- Remove the `{"action": 3}` example and limit replies to the legal moves, in a paired prompt comparison, and measure wall bumps and exits. Llama asked for "right" in 79 of 125 moves and bumped into walls in 72.
- Compare the coverage bonus with distance to the exit on all-failed maze groups, and count how often they rank attempts differently. In `maze-04`, coverage rewarded moving away from the exit.

### Further reading

Links were opened on 2026-10-28. [`data/research_sources.json`](data/research_sources.json) records an earlier check on 2026-10-24.

- [DAPO: An Open-Source LLM Reinforcement Learning System at Scale](https://arxiv.org/abs/2503.14476) (Yu et al., 2025). Its dynamic sampling step drops prompts whose sampled answers are all right or all wrong, the same groups this notebook counts as giving no contrast.
- [CERO: Where and When to Allocate Rollouts for RL Post-Training](https://arxiv.org/abs/2610.09679) (Zong et al., 2026). Spreads a fixed attempt budget across a whole training run, the setting in which the early-stop and choosing rules would be used.
- [TRACE: A Unified Rollout Budget Allocation Framework for Efficient Agentic Reinforcement Learning](https://arxiv.org/abs/2606.11119) (Zou et al., 2026). Predicts success from partly finished agent attempts and steers sampling towards states likely to give mixed outcomes, a finer version of the choice tested here.
- [Reasoning Gym: Reasoning Environments for Reinforcement Learning with Verifiable Rewards](https://arxiv.org/abs/2505.24760) (Stojanovski et al., 2025). Describes the generated puzzles and exact checks behind the four questions.
- [GRPO Trainer](https://huggingface.co/docs/trl/grpo_trainer) (Hugging Face, 2026). Shows how group comparison scores are used in an actual training run, the step this notebook stops before.
- [Proximal Policy Optimization Algorithms](https://arxiv.org/abs/1707.06347) (Schulman et al., 2017). The training method GRPO builds on; its probability ratios are why a trainer needs the token probabilities of the model that produced each attempt, which the Gemma provider did not return.
