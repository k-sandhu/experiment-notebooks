# Real-agent experiments to run next

Agreed with the repo owner on 2026-11-21, after notebook 48 merged (PR 131). Each becomes its own claimed
notebook, or several become designs in one notebook. Notebook 48's agents were single calls that saw a prompt
and returned one JSON reply; these move toward agents that act.

- [ ] **Larger tasks.** Cases too large for one prompt (for example 60 or more documents in a folder), with
  agents that read files through tools and decide what to open. Tests whether the single owner's lead in
  notebook 48 (67 of 80 against 47 for a line of 8) survives when no agent can hold the whole case.
- [ ] **Messaging.** Agents can send questions and replies to each other, or back up the line, instead of
  passing one note forward. Notebook 48 found 14 of 16 lost planted facts arrived as a retelling and were set
  aside as unverified; measure whether asking recovers them, how often agents ask, and what it costs.
- [ ] **Access to subsections of data.** Vary what each agent may see: only its own documents, its own plus
  the originals of anything passed to it, or everything. Separates information loss from the handoff itself.
- [ ] **Different responsibilities.** Agents with distinct roles and authority (preparer, approver,
  coordinator that splits and assembles the case, independent checker), including a coordinator with
  parallel workers, the most common design in real agent systems and absent from notebook 48. Include
  explicit decision rights: who settles a disagreement between agents, and whether a later agent may overrule
  an earlier one.
- [ ] **Broadened role across stages over time** (from the Anthropic report below). One agent owns a customer
  across several stages that happen days apart (for example application, funding, servicing) and must carry
  context between them, against a handoff at each stage. The report's example merged three sales roles because
  handoffs lost context; notebook 48 showed the same loss within one case, not across time.
- [ ] **Review under a limited budget** (from the Anthropic report below). A reviewer can read only part of
  the team's output (a fixed number of cases or characters). Compare reviewing everything, random sampling,
  routing by the agent's own stated doubt, and reading transcripts against reading final forms. Measures
  errors caught per unit of review. Notebook 48 gave its reviewers unlimited attention; the report names
  review of AI output as the recurring bottleneck.
- [ ] **Shared memory across a stream of cases** (from the Anthropic report below). Agents keep a shared notes
  or skills file that they update as they work through 100 or more cases in order. Measures whether accuracy
  rises over the stream and whether wrong lessons spread.

Measurement for all of them: tool calls, messages, tokens and wall-clock time per case, not only characters.
Token counts need `claude -p` signed in (the owner's step); the Claude Code subagent route works without it.

## Source for the items marked "from the Anthropic report"

Wilmers, Massenkoff and McCrory, "Working with AI", Anthropic, published 23 November 2026,
https://www.anthropic.com/research/working-with-ai (report PDF linked from the page). 66 interviews at 58 US
companies adopting AI; qualitative and not a representative sample. Points used here: the most valuable uses
came with organisational change; firms broadened roles so one person or small team owns a whole workflow,
because handoffs lose context; review of AI output swamped scarce human attention; decision rights and
accountability were often unclear.
