---
tags: [visual-skills]
max_turns: 120
timeout_seconds: 3600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Make an animated visual that replays how the planner agent and its helper agents actually spent their time in our subagent handoff experiment (notebook 07; recorded runs are in the input files). A reader should see why the synchronous handoff took about 120 s while the async spawn finished in about 57 s, who was waiting for whom, and where the one late message got lost. Use the recorded timings, not made-up ones.

Input files: data.json, facts.md
