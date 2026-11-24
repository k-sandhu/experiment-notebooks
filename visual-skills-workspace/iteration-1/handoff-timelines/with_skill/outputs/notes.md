# Handoff timelines: notes

## Message

When the planner hands cities to helpers one at a time, it sits idle for 66.3 s of a 120.2 s run. When it starts all three helpers at once and searches flights meanwhile, it never waits and finishes in 56.8 s. Its own work is about the same in both runs (53.9 s and 56.8 s), so the waiting accounts for the whole gap. A third run adds a second lesson: a message only counts if the receiver reads it. The planner's reply reached the Prague helper during that helper's last model call, so the helper never read it.

- Reader: someone who reads notebook 07, or sees the GIF, and knows nothing about agent coordination.
- Misconception: "More agents working in parallel is faster" (the sync run has the same 4 agents and was slower than one agent alone), and "a message that was sent was received".

## Form

The `explainer-director` skill picked `system-replay` in data-replay mode: actors, waiting and a lost message on a real timeline. It is built with the `explainer-kit` `K.player`, blueprint style, 380 x 330 viewBox, as one self-contained HTML file. It shows three runs as stacked swim-lane panels on one shared time axis (0-121 s): L1 sync handoff, L2 async spawn, L3 async with progress reports. Each panel has 4 lanes: planner, then the Lisbon, Rome and Prague helpers. Bars are spans (model call blue, search tool green, failed search red, planner waiting grey hatched), and vertical amber arrows are messages, each with a dot that travels along it when it is sent. A "now" line, a live header stat ("waiting for Lisbon: 12.4 s"), an event log and a scrubbable clock show the compression (x6.7, or x2.5 in the slowed stretch). `frame(t)` is a pure function of t, so scrubbing works both ways.

## Scenes (9 chapters, about 56 s of playback)

1. **Same trip, two ways**: the cast: three panels, lanes named, no bars yet.
2. **First handoffs** (run 0-36 s): sync hands Lisbon over and waits (hatched). Async spawns all three by 15.1 s and searches flights from 19.3 s.
3. **Async finishes** (36-56.8 s): the async answers arrived at 25.3, 30.6 and 34.5 s. Async is done at 56.8 s with 0 s waited, while sync is still waiting for Rome. A short hold follows.
4. **Sync, one by one** (56.8-120.2 s): sync waits 21.3 s for Rome and 20.0 s for Prague, and its flights start at 87.6 s. The dashed marker "one agent alone: 82.1 s" appears. Sync is done at 120.2 s.
5. **Where the time went**: an animated squeeze removes the sync planner's hatched waiting, and its bar shrinks to 53.9 s of own work beside async's 56.8 s. A dashed ghost box shows the removed 66.3 s.
6. **Progress reports** (L3, 0-38 s): helpers send progress messages. Prague's hotel search fails (red, "✗ 503"), and the helper switches to the backup search at 27.6 s.
7. **The reply came late** (38-55 s, slowed to x2.5): the alert at 40.0 s (red arrow up), then a tick marks "last call began 46.9 s". The planner's instruction at 49.8 s lands mid-call with a red ✗ and the label "reply never read".
8. **Finished anyway**: Prague answers from the backup data at 53.7 s, and the run is done at 68.8 s with the correct answer.
9. **What to take away**: all three panels in full. Start helpers together and keep the planner busy. Check that messages get read. One recorded run each.

## Where every number comes from

All drawn spans and events are copied by a build script from `files/data.json` (runs `L1_sync_handoff`, `L2_async_spawn`, `L3_progress_and_redirect`, plus `L0_single_agent.wall_s`) into `const DATA` in the page. Every number in captions, headers and the log is computed in JS from DATA, with nothing typed by hand, apart from two values (see the list after the table).

| On screen | Value | Derivation |
|---|---|---|
| Sync done / async done / L3 done | 120.2 / 56.8 / 68.8 s | `runs[].wall_s` (120.21, 56.76, 68.77; match comparison.csv) |
| One agent alone | 82.1 s | L0 `wall_s` 82.06 |
| Sync waited 66.3 s; waits 25.0, 21.3, 20.0 s | | sum and lengths of `main` spans kind=blocked (matches `main_blocked_s_from_spans` 66.3) |
| Own work 53.9 s (sync), 56.8 s (async) | | sum of `main` non-blocked spans; 53.91 + 66.30 = 120.21 |
| Sync took 63.4 s longer | | 120.21 − 56.76 (63.45, shown as 63.4 by toFixed) |
| Async helpers all started by 15.1 s; flights from 19.3 s | | last L2 spawn event 15.13; first main `search_flights` span 19.25 |
| Async answers at 25.3, 30.6, 34.5 s | | L2 result events |
| Sync flights start 87.6 s | | first L1 main `search_flights` 87.64 |
| Prague search fails at 24.0 s (HTTP 503); backup from 27.6 s | | L3 #4 `search_hotels` span 19.97-23.97 (failure from alert text "search_hotels failed ... HTTP 503"); `search_hotels_backup` start 27.58 |
| Alert 40.0 s; last call began 46.9 s; reply 49.8 s; Prague answer 53.7 s | | L3 alert event 39.97; last #4 llm span start 46.86; instruction event 49.83; #4 result 53.7 |
| EUR 3,316, all answers correct | | facts.md (correct total; `runs[].correct` = true) |
| Playback x6.7 / x2.5 | | design constants: 150 ms and 400 ms of playback per run second |

The city of each helper (#2 Lisbon, #3 Rome, #4 Prague) comes from the spawn message text in every run. The "use the backup data" quote shortens the L3 instruction text ("Proceed with the backup data..."). The sentence "messages are read when a call starts" restates facts.md: the helper's last call began at 46.9 s, so it never read the instruction. One zero-length L3 blocked span (54.34-54.34 s) is dropped; it has no width and adds 0 s.

## What I checked

- `render_check.py` at 360 px and 560 px, plus reduced motion. The final run has 0 FAIL and 0 WARN. Earlier runs found and I fixed: style colours read before the style loaded (a page error); log lines wrapping at 360 px, which left a clipped fragment above the log box (lines shortened and set to one line each); and caption/log overlap warnings caused by those wrapped lines.
- I looked at the chapter end states at 400 px and at 360 px, and at frames from the recorded MP4. Labels are legible and the "503", "reply never read" and "last call began" labels do not collide. I broke the 82 s dashed marker around the panel headers so it no longer runs through the header text. At 360 px the 9 chapter dots wrap to two rows. This is a constant height and the controls do not move.
- I checked the arithmetic in Python against data.json: own work + blocked = wall time for L1, L2 and L3.
- Recorded `explainer.mp4` (2.6 MB, 57.7 s) and `explainer.gif` (5.1 MB) with `record.py`. The source footnote is hidden in record mode so it does not peek into the crop.
- Not checked: the page in a real phone browser, and screen-reader output beyond the title and aria label.
