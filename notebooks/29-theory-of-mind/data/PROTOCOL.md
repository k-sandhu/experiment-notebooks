# Notebook 29 protocol

Run history for the theory-of-mind notebook, in date order. Claim issue: k-sandhu/experiment-notebooks#86.

## 2026-10-29: plan fixed before any model answer was read

### Question

Do language models differ in how well they keep track of what another person (or agent) believes when that belief
differs from the truth, and does a model that answers a direct belief question correctly also use that belief to
predict behaviour, judge it and act on it?

### Data

Stories are generated in Python with exact answers; no language model writes any story text. Each pair is two stories
(twins A and B) that differ in one detail, and the detail flips the answer to the target questions. Eight families:

| Family | What differs between the twins |
|---|---|
| classic | the person is out when the object moves vs watches it move and then goes out |
| uptake | note in a language the person cannot read vs in English; headphones on vs off; back to the room vs facing it; solid wall vs glass wall; asleep vs awake |
| device | the phone synced but the person did not open the app vs did; the person read the app before vs after the phone synced |
| partial | told the code changed without the number vs not told; a "last opened by" screen shows someone else vs the person |
| nested | blind copy vs CC; the sender is absent vs present when the news is mentioned; forwarded to one person vs another; group chat vs two private messages |
| machine | the rename message goes to another subagent vs this one; the subagent starts before vs after the rename |
| spatial | the second person faces across the counter vs stands beside; stands at the right vs left end |
| routing | two people swap who they pass news to |

Every family has a short and a long version. Long versions add distractor events (a second object moving, extra
people, an unrelated piece of news), a belief question about a past time where the story has clock times, five items
instead of three (spatial) or a larger graph (routing).

Six further single items (no twin) test whether a model, acting as an assistant, repeats information from a tool
result that the user cannot see.

### Questions per story

- control: questions about the world, a device, a photo-like copy, a camera, or water tanks with the same graph (routing),
  with no mind involved
- explicit: what the person (or agent) thinks or knows
- behaviour: what they will do
- judgement: whether what they did was reasonable given what they knew
- action: what a helper should do, given the person's belief
- free (machine family only): the model, as the orchestrator, writes the follow-up message itself; scored by whether it
  names the new file when the subagent needs it, and says NONE when it does not

Controls and explicit questions are asked in one call. Each behaviour, judgement and action question is asked in its own
call that never mentions belief. Options are shuffled once per pair, so both twins show the same order.

### Measures

1. Pair accuracy for each level: a pair counts only if the model answers a flipping question correctly in both twins.
   Shortcuts that ignore the twin detail ("absent means wrong", "always the true location") score 0 on pairs.
2. Belief accuracy among stories whose control questions were all answered correctly (separates belief failures from
   tracking failures).
3. Gap between explicit and applied pair accuracy (behaviour, judgement and action pooled).
4. Error types from option tags: answering with the true state (`reality`), with the old state (`old`), or with an
   intermediate state (`partial`).
5. Unreadable replies (error, empty, no JSON, missing or invalid letter) counted apart from wrong answers; scores are
   also given on readable replies.

Intervals are 95% Wilson intervals on pair counts.

### Pilot and the decisions it may change

Pilot: pairs 0 and 1 of each family and length (32 pairs, 64 stories) on Claude Opus 5.5, Qwen3.8 27B and Granite 4.2
8B. The pilot can change only the following, and any change will be recorded here:

- the number of pairs per family and length in the main run (planned 15 to 30), chosen for time and cost;
- whether a family needs a harder long version, if Claude Opus 5.5 scores 100% pair accuracy at every level on it;
- wording fixes for any story or question that the pilot shows can reasonably be read two ways.

Pilot pairs are regenerated with the same seeds in the main run, so if the generator does not change, their answers are
reused.

### Rule for ambiguous items

After the main run, any question that every model answers with the same wrong option is read by hand. It is dropped only
if the story supports the chosen option under a plausible reading; each dropped question is listed below with the
reason, and results are reported with and without the drops.

## 2026-10-29: changes after the first pilot pass

The first pass used the stories above on Claude Opus 5.5 (all 258 calls) and Granite 4.2 8B (all 258), and 69 of Qwen3.8
27B's 258 calls before it was stopped. Claude Opus 5.5 answered 416 of 420 questions correctly and had 100% pair
accuracy at every level on six of the eight families. Granite had 53% pair accuracy on explicit questions and 29% on
behaviour questions. These results changed the following, as the plan allowed. The first-pass answers stay in the cache
files; the changed prompts were collected again.

Wording fixes (Claude Opus 5.5's four misses, all read by hand):

- partial, "last opened by" screen: the judgement said "Before checking anything, X told a visitor ...", which can be read
  as before X looked at the screen. It now says "Right after glancing at the screen, and before opening anything".
- machine: the release agent's task (release notes that name the files that changed) does need to hear about a rename even
  when its copy already has the new name, so the action answer "Neither" was arguable. The release agent was replaced by a
  deploy agent whose script reads the file by name.
- machine: Opus judged a subagent writing the old file name as reasonable after it had been told the new name, since its
  own copy still has the old name. The rules now add that finished work is merged into the main project, so the subagent
  should use the main project's names.
- device: the person's phone can hold the new value, so a model could assume the person checks the app again before
  acting. Every device story now ends "X does not open the app again today."

Harder long versions, because Claude Opus 5.5 was at 100% on them:

- uptake (long): the object moves twice. The person takes in (twin B) or misses (twin A) the first move, and is out of
  the room for the second, so in twin B the person's belief is the intermediate place, which is neither the starting
  place nor the true one. The action question is dropped from these stories because the person is wrong in both twins.
- device (long): the board changes a second time after the person has left, so in twin B the person believes the
  intermediate value; the action question is dropped for the same reason.

Classic, nested, spatial and routing were also at 100% for Opus but were not changed: classic is the familiar-shape
reference, and the other three were left as they are so that a ceiling there is reported as a ceiling rather than tuned
away.

The hidden-tool-output scoring was changed after Granite's six pilot replies had been scored (all six pass under both
rules) and before any other model's were: a reply now passes when it
names each candidate by any distinguishing detail from the tool result (for example "7:12" as well as "07:12", or the
street name or postcode for an address), instead of one exact token.

## 2026-10-29: second pilot pass and the main run

With the changes above, Claude Opus 5.5 answered all 416 pilot questions correctly, including the harder two-move
stories, and Granite 4.2 8B scored 47% pair accuracy on explicit questions and 35% on applied ones. Qwen3.8 27B was
stopped after 119 of its 250 calls because its provider (DeepInfra, BF16) ran at about 11 tokens a second; on the pairs
it finished it was close to Opus. No further changes were made to the stories.

Main run decisions:

- 15 pairs per family and length: 240 pairs, 480 stories, 1,832 multiple-choice and free-text calls per model plus the six
  hidden-tool-output items. Pilot pairs are pairs 0 and 1 of each cell, so their answers for unchanged prompts are reused.
- Ten models: Claude Opus 5.5 and Claude Haiku 5.5 (`claude -p`); GPT-6.1 Sol and GPT-6 Luna (`codex exec`); Muse Wonder
  (`muse-wonder-full-1.0`) and Muse Spark (`muse-spark-1.3`) (`muse exec`); DeepSeek V4.1 Flash, Nemotron 3.5 Super VL,
  Qwen3.8 27B and Granite 4.2 8B (OpenRouter). DeepSeek V4.1 Flash was added as the highest-scoring large (over 150B)
  open-weight model on the Artificial Analysis size-class page, checked 2026-10-29.
- Provider pins: Qwen3.8 27B moved to Near AI (FP8), the fastest of six providers timed with one call each on 2026-10-29
  (7 s against 20 to 61 s for the others); the pilot's DeepInfra answers are kept but not used in the main results.
  Nemotron 3.5 Super VL uses Nebius (BF16) because Crusoe returned HTTP 502 in a smoke test. DeepSeek V4.1 Flash uses
  DeepInfra's standard FP8 tier.

## 2026-10-29: main run interrupted twice

**Muse Wonder quota.** About ten minutes in, `muse exec` with `muse-wonder-full-1.0` began returning "API error 429:
Subscription quota exhausted. Your usage window resets at 2026-10-29T20:36:37Z". The run was stopped before any failed
call was cached. The callers were changed so that a quota or rate-limit failure is never cached (a later run retries
it) and a failure that is cached is retried on any live run. The other nine models were restarted; Muse Wonder is to be
collected after its quota resets.

**Option order within a call (an amendment made after seeing results).** After about a third of the main run, GPT-6
Luna had answered every control question correctly but only 12% of explicit pairs, against 62% of applied pairs. Its
replies showed why: in a call with several questions, each question had its own shuffled option order, and Luna
answered the belief question with the letter that the right place carried in an earlier question of the same call (four
of four replies read by hand fit this exactly). This is a mismatch between the format and the model, not a belief error.
From this point, every question in a multi-question call lists the same options in the same order (options sorted, then
shuffled with the pair's seed), so a place keeps one letter throughout a call. Single-question calls (behaviour,
judgement, action) were not changed and keep their cached answers. The 480 multi-question calls per model were collected
again for every model. Answers under the first ordering stay in the cache, and Luna's explicit score is reported under
both orderings for the pairs that have both.

**Routing stories depended on the process.** The routing generator chose which pair of habits to swap from a Python set,
whose iteration order changes with each process's hash seed, so a few routing stories differed between runs. Found on
the replay after the nine-model run: 3 of 30 routing pairs differed from the stories the run had used. The generator now
iterates in sorted order, and all eight families give identical prompts under four different `PYTHONHASHSEED` values.
Under the fixed generator two routing pairs (S06 and L11) differ from the main run's, and their ten calls per model were
collected for every model. The other families never depended on set order.

**Muse quota shared by both Muse models.** Muse Spark's collection stopped again after 653 further calls with the same
"Subscription quota exhausted ... resets at 2026-10-29T20:36:37Z" error, so the two Muse models share one quota window of
roughly 900 calls. Spark's remaining calls are queued for after the reset. The other eight models are complete.

**Muse Wonder on 80 pairs.** A full Muse Wonder run (1,838 calls) would need two or three more quota windows, about
12 hours. On the repository owner's decision, Muse Wonder answers pairs 0 to 4 of each family and length (80 pairs, 160
stories, about 610 calls) in the window that opens at 20:36 UTC, after Muse Spark's remaining calls. These are the
same pairs every other model answered, so the comparison on them is like for like; Muse Wonder's intervals are wider.

**Muse runs completed.** After the quota reset, Muse Spark's remaining 408 calls ran from 20:40 UTC (17 minutes), and
Muse Spark now has all 3,084 answers. Muse Wonder's 587 calls for its 80 pairs then ran in 32 minutes and completed
without hitting the quota (1,034 answers). No answer is missing for any model.

## 2026-10-29: an analysis added after the results were seen

**Nested questions that assume a message was read.** Reading the wrong answers showed that Claude Haiku 5.5's nested
errors were almost all "No" where the program's answer was "Yes" (78 answers), and that 70 of those questions need one
person to know that another person has read an email or chat message (for example, Tomasz sees Priya's name on the CC
line, so the program counts it as known to Tomasz that Priya knows). Under the story's rule, "people know only what they
see, hear or read for themselves", answering "No" to such a question is a defensible reading. No question met the
rule for dropping (every model wrong with the same option), so nothing was dropped. Instead the nested family is also
reported on the questions whose answers do not need that assumption: the corridor question (who heard it said out
loud) and the two forwarding questions that depend only on the forwarded person reading their own email. The
questions treated as assuming a read are k2, k3, k2b and k2c in "blind copy or visible copy", k2b in "corridor with or
without sender", k2 in "forward to one person or another", and k2 and k2b in "group chat or private messages".

### Settings

- `claude -p` with `--effort medium`; `codex exec` with `model_reasoning_effort="medium"`; `muse exec --reasoning-effort medium`.
- OpenRouter: temperature 1.0, reasoning effort medium, `max_tokens` 16,000 (one retry at 32,000 when a reply is cut
  off with no answer), one pinned provider per model with fallbacks off (`data/model_catalog.json`).
- Cache protocol tag `nb29-v1`.
