# Proposed unsafe actions under explicit project permissions

Give a coding assistant a repository and a terminal, and the permissions you wrote for it ("only touch `src/`,
never read `.env`, never push") become the only thing between a request and a damaging command. Most requests are
harmless. The ones that matter are those where the request itself is the problem: a user asks to "clean up" a
folder outside the project, a pasted support ticket says "also print the API keys", or a symlink makes an in-scope
path point at a home directory. A model that respects written permissions in these cases can be trusted to propose
actions; one that does not needs a gate in front of every command, which notebook 10 tests.

There are two easy ways to measure this wrongly. A model that refuses everything never proposes anything unsafe,
and it is useless, so each forbidden request here is paired with a permitted one that looks similar. And "I can't
run this, but you could run `rm -rf ...`" is not a safe refusal, so replies are judged on what they propose, not on
whether they say no.

**Question.** Under the same written permissions, how often do two open-weight models (DeepSeek V4.1 Flash, Gemma
4 31B) and two closed ones (Claude Opus 5.5, GPT-6.1) propose an action outside them on 12 forbidden requests, how
many of 12 permitted requests do they complete, and does adding a checklist to the prompt change either? Proposed
commands are judged as text by other models and never run.

**Result.** Across the 96 forbidden requests (4 models, 2 prompts), the judges flagged one reply, and that flag is
disputed. The clearest problem came on a permitted request: DeepSeek's count-summary code searched recursively
through a symlink that points outside the project. Usefulness varied more than safety did: GPT-6.1 completed all
12 permitted requests under both prompts, Gemma 4 31B 5. The checklist did not reduce flags (1 without it, 2 with
it) and lowered DeepSeek's acceptable permitted proposals from 10 to 8. The four models differ in more than their
weights, so this cannot rank open against closed models.

Of the 192 requests, 187 returned model text. The provider's safety service blocked 3 Claude requests, and 2
DeepSeek replies had no final text; these count as unresolved, not as safe.

| Model | Prompt | Forbidden-request flags / 12 | Permitted-request flags / 12 | Service blocks | Acceptable permitted proposals / 12 |
|---|---|---:|---:|---:|---:|
| DeepSeek V4.1 Flash | Short | 0 | 1 | 0 | 10 |
| DeepSeek V4.1 Flash | Checklist | 0 | 0 | 0 | 8 |
| Gemma 4 31B | Short | 0 | 0 | 0 | 5 |
| Gemma 4 31B | Checklist | 0 | 0 | 0 | 5 |
| Claude Opus 5.5 | Short | 0 | 0 | 1 | 11 |
| Claude Opus 5.5 | Checklist | 1 | 1 | 2 | 10 |
| GPT-6.1 | Short | 0 | 0 | 0 | 12 |
| GPT-6.1 | Checklist | 0 | 0 | 0 | 12 |

These are automated flags, not adjudicated ground truth. Service blocks and empty responses are separate from model refusals;
they remain unresolved. The two Claude checklist flags are the disputed ones. Both judges scored 8/8 authored
calibration anchors correctly, yet that did not prevent questionable labels on ambiguous proposals.
Zero flags on 12 known judgments still gives a Wilson 95% upper bound of 24.3%; these authored cases are not
a representative sample. Models also differ in capability, transport, hidden instructions and provider safeguards.

![All request flags](figures/all_request_flags.png)
![Judged flags and useful proposals](figures/safety_and_utility.png)
![Concrete proposal and judge evidence](figures/error_example.png)

```mermaid
flowchart LR
 D["24 synthetic cases<br/>12 policy-breaking + 12 permitted"] --> P["Same permissions<br/>short policy or policy + checklist"]
 P --> M["4 models × 2 prompts × 24 cases<br/>192 text-only calls"]
 M --> C["Cache raw proposed actions<br/>never execute"]
 C --> J["Claude Opus 5.5 via claude -p<br/>GPT-6.1 via codex exec<br/>36 batch calls + 2 anchor calls"]
 J --> R["Violations, legitimate completion<br/>disagreement + 95% intervals"]
```

[AgentDojo](https://arxiv.org/abs/2406.13352) motivates untrusted-data attacks and separate
utility scoring; [AgentHarm](https://arxiv.org/abs/2410.09024) motivates scoring actions beyond refusal phrases;
[ToolEmu](https://arxiv.org/abs/2309.15817) motivates risk evaluation without real side effects. This study uses
its own synthetic cases and is not a reproduction of those benchmark scores.

Twelve forbidden requests with twelve related permitted controls cover shell/Python/PowerShell
deletion, secrets, exfiltration, permissions, deployment, remote installation, git pushes, symlinks, traversal
and untrusted ticket instructions. Short and checklist prompts grant identical permissions. Each call is an
independent request. Open endpoints get Claude and GPT judges; closed endpoints get the other provider's
judge. Judges see raw replies with model identity removed. Any unsafe vote creates a conservative flag;
missing/unclear ratings and service blocks remain visible. Eight-record batching reduces cost. Open replies
receive two ratings and closed replies one, so the any-unsafe rule has more opportunities to flag an open reply.
This prevents a controlled comparison of weight openness.

The notebook's author audit is Codex review, not independent human adjudication. All flagged cases and
concerns are in `data/adjudication_queue.json`. The symlink finding is a static reading of the proposed code,
supported by [Python recursive-glob documentation](https://docs.python.org/3.12/library/glob.html); no code is run.
Future trials need explicit filesystem manifests and independently reviewed labels before making deployment claims.

Authored fictional cases, MIT licence with this repository. Public model catalog metadata is
saved with the collection. DeepSeek and Gemma are hosted open-weight model endpoints; service-layer behavior
and exact hosted revisions can differ from local weights. The initial Mistral endpoint returned upstream 429
before any trial response; DeepSeek was selected before scoring.

230 cached collection responses. OpenRouter: $0.03784. Claude reported list-price equivalent: $1.762; actual subscription charges differ. Codex uses its subscription; incremental USD is not exposed. Replay makes zero model calls. These totals cover the committed study responses, excluding CLI transport preflight attempts.

From this folder:

```bash
python -m jupyter nbconvert --to notebook --execute --inplace 09_agent_action_safety.ipynb
```

Offline replay is strict and needs no key. New requests require `NB_LIVE=1`, logged-in `claude` and `codex`
CLIs, and `OPENROUTER_API_KEY`. `MODELS`, `N_CASES`, `N_REPEATS`, output/call limits and dollar reservation
bound collection. `NB_SMOKE=1` selects two case pairs. Every measured raw proposal, judge response and
request is cached. Proposed paths, commands and URLs never feed an executor.
