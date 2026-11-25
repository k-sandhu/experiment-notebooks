# Can an LLM plan a day's pickups?

A driver collecting freight from local shops starts with an empty van. At each address, the driver checks in, waits if the load is still being prepared, and takes on a little more weight. By the last stop, there has to be room for one more load and time to get the whole day's freight back to the depot. A useful plan tells each driver where to go, in what order and when to leave. Dispatch can send it out with confidence that every booked pickup fits.

The consequences show up at individual stops. If a truck gets to a dock just as it closes, the loading crew has gone home. If it arrives half an hour early, the driver may wait with the truck loaded. Distance still matters, because extra kilometres cost time and money. A dispatcher has to compare distance, wait time and equipment across the day, with the rest of the fleet already assigned to work of its own.

### Illustrative example of a dock closing at noon

Suppose a dispatcher has one dry van and one refrigerated van. Two shops have cartons ready any time this morning. A grocery dock has chilled cases ready at 11 and closes at noon. The driver needs 15 minutes to load the cases, so service has to start by 11:45. The first part of the plan is to give the grocery pickup to the refrigerated van.

The grocery dock is close to both shops on a map. Say the refrigerated van could reach the dock at 11:30 going straight there. A stop at one shop takes 10 minutes of extra driving and 10 minutes to load. That moves the grocery arrival to 11:50. Loading ends at 12:05, five minutes after close. The dry van could take the shop instead, or the refrigerated van could collect the chilled cases first if the equipment and freight allow it.

Now suppose the grocery dock tells dispatch it will close at 11:50 and one driver is already on the way to a shop. The morning plan is partly carried out. A revised plan has to preserve the trip already underway, use the vans from where they are, and account for what each one is carrying. A good answer can mean giving the dry van one or two new stops while keeping most of its list intact.

A route optimizer works with those limits as rules. It evaluates choices such as adding a stop after another stop, trading stops between two vehicles or changing a departure time. It keeps track of the best complete plan it has found. A language model can also read the manifest, group nearby pickups and write a stop list. Seeing the geography may help it choose groups. With an optimizer available, its draft can provide a first plan for the optimizer to improve, provided the draft is usable.

We call a plan **dispatchable** when every pending pickup is assigned exactly once and all the modeled operating rules hold. That is the first measure. A plan that serves 239 of 240 pickups can teach us a lot about where the method breaks, while dispatch still needs a route for the remaining pickup. We compare operating costs between plans on days when both pass.

## Question

On 24 simulated Toronto dispatch days, each with **24 vehicles and 240 pickups at real commercial addresses**, can GPT-6 Luna, GPT-6.1 Terra or GPT-6.2 Sol plan the day's work and handle an 11 a.m. disruption? How often does a labeled street map help, and does starting from either model's draft improve on a conventional optimizer working under the same deadline?

## Study in brief

**At the full fleet scale, the models produced 0 dispatchable morning plans in 144 attempts.** 45 of those attempts gave a readable route list. At 11 a.m. the pending workload dropped to 96–98 pickups. The models produced 5 dispatchable replans in 144 attempts (Luna 0 without a map and 0 with one, Terra 2 without a map and 3 with one, Sol 0 without a map and 0 with one). Sol timed out on 96/96 fleet sessions. Every model and map condition was tested on the same 24 days.

The configured unseeded optimizer passed 15/24 mornings and 11/24 replans. Giving it a simple insertion plan when one was available gave 15/24 and 15/24. Across the LLM arms, 5 drafts were accepted as solver starts and 1/96 jointly feasible pairs beat the unseeded solver's operating cost. These results depend on the solver's method of finding a first plan. One failed search does not imply the workload was infeasible.

The strongest small-scope result came when each truck already had its jobs. Across 72 model attempts, 59 single-truck orders matched the exact minimum. In a separate replan check, moving the three affected appointments within the existing driver lists repaired 24/24 days. The jobs and incidents are simulated. Both follow-ups benefit from knowing where the work was assigned before the disruption.

## Contents

1. [Data and the dispatch day](#1-data-and-the-dispatch-day)
2. [Planners and comparison](#2-planners-and-comparison)
3. [Checking a plan](#3-checking-a-plan)
4. [Morning and 11 a.m. results](#4-morning-and-11-am-results)
5. [Reading the plans that passed and failed](#5-reading-the-plans-that-passed-and-failed)
6. [Sequencing one truck in one part of the day](#6-sequencing-one-truck-in-one-part-of-the-day)
7. [Limitations](#7-limitations)
8. [How to reproduce](#8-how-to-reproduce)
9. [Future work and further reading](#9-future-work-and-further-reading)

```mermaid
flowchart LR
    G["241 real locations<br/>Two vehicle road matrices"] --> D["24 frozen operating days<br/>240 pickups and 24 vehicles each"]
    D --> M["Morning manifest<br/>240 pickup jobs"]
    D --> P["Replay a shared morning plan to 11 a.m.<br/>96 to 98 pending pickups"]
    M --> C["3 models × text or map<br/>144 morning sessions"]
    P --> E["3 models × text or map<br/>144 replan sessions"]
    C --> R["Independent route replay<br/>Score draft and solver-assisted route"]
    E --> R
    D --> A["Deterministic dispatch baselines<br/>48 day-stage states"]
    A --> R
    R --> O["Feasible days, operating costs,<br/>and changes to driver lists"]
    D --> B["24 fixed truck blocks<br/>72 sequencing sessions"]
    B --> X["Exact permutation check<br/>Feasibility and minimum cost"]
```

A day enters the morning comparison with 240 jobs and a new fleet sheet. A separate replay starts every 11 a.m. planner from the same operating state, leaving 96–98 jobs to assign. For example, day D01 starts with the same pickup addresses in both columns. The afternoon view removes completed or committed work and moves the affected deadlines. Every returned whole-fleet plan is checked against the same stage records.

## 1. Data and the dispatch day

The depot is the Ontario Food Terminal at 165 The Queensway. The addresses in the manifest cover 192 food premises such as grocers, bakeries and restaurants, plus 48 municipal address points inside buildings tagged industrial or warehouse. Street locations are real. The pickups and the carrier are fictional. A point on a map can locate an address, while its loading time, size of shipment and available equipment come from the experiment. The same address panel represents recurring customers across the 24 days. Every day draws new load quantities, time windows, shifts and vehicle assignments. [Geography sources and licences](data/geography_sources.md)

We use two different models of driving. A cargo van uses a standard road profile. The box truck is modeled at 3.35 m high, 2.55 m wide and 6.58 t gross weight, with a truck profile that checks mapped truck restrictions. Both use paths on the same pinned OpenStreetMap snapshot. The driving time from one address to another is allowed to differ in the reverse direction. One-way streets and the direction of turns can change which path is available. Each route leg rounds the travel time up to a whole minute. That way an estimated drive of 8 minutes and 2 seconds occupies 9 minutes in the schedule.

Across 57,840 directed pairs of different locations, the truck and van travel times differ on 23,698 pairs. The truck time is higher on 14,430 of those and lower on 9,268, with a median absolute difference of 31 seconds. One long discrepancy is the leg from **2795 Danforth Avenue to 1468 Queen Street West**. The van path is 15.578 km and takes 24 minutes 38 seconds. The truck path is 23.125 km and takes 33 minutes 56 seconds. That leg uses 25 minutes in the van timetable and 34 in the truck timetable. The routes can differ even though the pins on either map sit in the same places. This is why everybody gets road times in addition to coordinates. [Valhalla routing profiles](https://valhalla.github.io/valhalla/api/turn-by-turn/api-reference/)

| Vehicles per day | Configuration | Simulated freight and access | Simulated usable capacity |
| --- | --- | --- | --- |
| 12 dry cargo vans | Ford Transit configuration | Dry cartons and totes. Some sites have van-only access. | 1,080 kg and 10,200 L |
| 6 refrigerated vans | Transit van with insulated body and refrigeration | Chilled cases. The carrier assigns these vans to chilled freight. | 880 kg and 7,600 L |
| 6 liftgate box trucks | Isuzu NPR-HD with a 16 ft body and liftgate | Pallets at a dock or a curbside liftgate stop. Can also carry eligible dry cartons. | 2,250 kg, 22,000 L and 8 pallet positions |

The capacities are explicit assumptions for the fitted vehicles, allowing for the weight and space of the equipment. They are useful for testing assignment and capacity tracking. The manufacturer pages describe real vehicles and configurable bodies. The fictional carrier chooses the usable limits and the kinds of freight that each truck can accept. [Ford Transit specs](https://www.ford.ca/trucks/transit-passenger-van-wagon/2026/models/cargo-van/) · [Isuzu NPR-HD specs](https://www.isuzutruck.ca/en/nseries/nseries_diesel_specifications) · [Thermo King vans and small trucks](https://www.thermoking.com/na/en/road/trucks-and-vans/direct-drive-units.html)

The study has eight ordinary days, eight with narrower windows, and eight with less specialist capacity to spare. On the last eight, the reference routes load each refrigerated van and liftgate truck closer to its rated capacity. The liftgate routes each fill eight pallet positions.

We generate freight and service durations, put work in morning and afternoon waves, and create windows around a schedule. Independent replay verifies that schedule and a feasible replan. Both are saved with the input data. A planner can produce any valid sequence, times or vehicle assignments. At 11 a.m. every method starts from the state produced by the same reference schedule.

### What changes at 11 a.m.

At 11 a.m. a dock closes early and two pending pickups get earlier deadlines. The old list misses all three revised deadlines. A changed list can still serve all 240 pickups. Work finished or already committed is removed from the pending list.

A driver already on the way to a store keeps that visit. Replanning uses the projected location, time and load after it. Paid time starts then, including any further waiting. The saved snapshot identifies the completed and committed stops.

| Operating day | Days | Vehicles / pickups | Already complete | Committed at 11 | Pending at 11 |
| --- | --- | --- | --- | --- | --- |
| Ordinary | 8 | 24 / 240 | 119–120 | 24–24 | 96–97 |
| Tight windows | 8 | 24 / 240 | 118–120 | 23–24 | 96–98 |
| Scarce specialist capacity | 8 | 24 / 240 | 119–120 | 24–24 | 96–97 |

The counts show why the replan begins with less work than the morning plan. Each completed or committed job belongs to the morning manifest and is carried forward in the truck's state.

### A look at a real input table

These are the first four input rows, in pickup-ID order, for **D01**. A route lists the numeric ID. The address and map show where a driver has to go. The remaining fields determine whether a vehicle can serve the job and when it must finish.

| Pickup | Address | Freight | Window | Service min | Load added |
| --- | --- | --- | --- | --- | --- |
| 1 | 230 Belfield Rd | dry cartons and totes | 08:47–10:31 | 10 | 159 kg / 1,294 L / 0 pallet |
| 2 | 77 St Regis Cres | dry cartons and totes | 08:21–11:18 | 7 | 80 kg / 1,366 L / 0 pallet |
| 3 | 1910 Kennedy Rd | dry cartons and totes | 11:53–14:56 | 11 | 75 kg / 830 L / 0 pallet |
| 4 | 2803 Eglinton Ave E | liftgate pallet | 08:38–10:40 | 17 | 204 kg / 1,455 L / 1 pallet |

![Six labeled sectors of Toronto showing morning pickup points and the Ontario Food Terminal depot](figures/input_map.png)

The map shows the same day in six panels. The blue numbers are the pickup IDs and the depot is the orange star in the southwest. Grey lines show major roads. There are no route suggestions. Some numbers crowd together in the denser panels. The stop table still identifies every location and the road table gives directed drive times. A driver can use the image to see nearby sites, then use the tables to check whether it makes sense to put them on the same truck.

## 2. Planners and comparison

| Model | Version used | Provider and access | Size and precision | Output settings | Reason to include |
| --- | --- | --- | --- | --- | --- |
| GPT-6 Luna | gpt-6-luna | OpenAI through Codex CLI | Unpublished | Medium reasoning, one optional batched lookup | Owner-requested model with text and image input |
| GPT-6.1 Terra | gpt-6.1-terra | OpenAI through Codex CLI | Unpublished | Medium reasoning, one optional batched lookup | Owner-requested model with text and image input |
| GPT-6.2 Sol | gpt-6.2-sol | OpenAI through desktop Codex CLI | Unpublished | Medium reasoning, one optional batched lookup | Requested later as a newer model for the same routing cases |

These are the versioned model IDs selected in the Codex catalog. The CLI records which ID was requested and reports usage. This run's CLI records contain no dated backend revision or billed amount. Within each model, both image conditions use the same model settings and route response format.

OpenAI lists a May 18, 2026 knowledge cutoff for Luna and a June 1, 2026 cutoff for Terra and Sol. All pilot and held-out manifests and incidents were generated on November 18, 2026, after those dates. The public inputs locate the roads and addresses. The test targets are fresh assignments, loads and schedules generated for this experiment. [Luna model card](https://developers.openai.com/api/docs/models/gpt-6-luna) · [Terra model card](https://developers.openai.com/api/docs/models/gpt-6.1-terra) · [Sol model card](https://developers.openai.com/api/docs/models/gpt-6.2-sol)

Models get the same manifest, vehicle state, depot travel times and up to five nearby directed times per stop and eligible vehicle profile. They can ask for up to 72 more directed legs in one request. The lookup returns only times and distances. The map condition adds a street image with the same stop IDs, depot and vehicle origins.

```mermaid
flowchart TD
    P["Same manifest and fleet state<br/>Text or text plus map"] --> L["GPT-6 Luna, GPT-6.1 Terra or GPT-6.2 Sol<br/>Codex exec returns JSON"]
    L -->|"Optional lookup request"| T["Read-only leg table<br/>Up to 72 directed pairs"]
    T --> F["Same model via Codex exec<br/>JSON route list"]
    L -->|"Direct routes"| D["Independent checker<br/>Feasibility and cost"]
    F --> D
    D -->|"Validated routes"| W["OR-Tools starts from the model draft<br/>Uses remaining stage time"]
    D -->|"Unusable draft"| A["Unseeded OR-Tools fallback<br/>Uses remaining stage time"]
    W --> S["Independent replay of final plan"]
    A --> S
```

Each model and input condition runs in a separate session. The only second model turn is a reply to the optional travel request. If it is used, the planner waits for the requested time and distance rows. The method keeps the raw draft and scores it independently before using it for a solver start.

We score the direct draft and the solver-assisted plan. OR-Tools can start from a usable draft. For an unusable draft, we read the cold solver's best known plan at the time left after the model call. A timeout that consumes the whole budget leaves no time for a fallback.

Greedy insertion takes jobs in order of closing time and places each in the cheapest feasible position. It leaves a job unassigned if it finds no legal position. We compare OR-Tools from an empty start and from that simple order if it passes replay. OR-Tools searches for a complete plan and then tries to reduce cost. [OR-Tools routing tasks](https://developers.google.com/optimization/routing/routing_tasks)

Operating cost includes vehicle activation, mileage, and paid minutes driving, waiting and loading. All methods use the same simulated Canadian dollar rates.

### How the study got here

We tested two smaller schedules first, each with four vehicles and 24 pickups. Each model attempted four morning and four replan conditions at 75 seconds per session. The small schedules also let us inspect actual arrival calculations by hand.

| Model | Pilot sessions | Dispatchable mornings | Dispatchable replans | Unreadable | Timed out |
| --- | --- | --- | --- | --- | --- |
| Luna | 8 | 0 | 3 | 2 | 0 |
| Terra | 8 | 4 | 4 | 0 | 0 |
| Sol | 8 | 0 | 2 | 0 | 6 |

The pilot established that the pipeline could accept a draft and check it with or without an image. Two Luna map replies in the morning asked for too many road legs. For the held-out cases we kept the 72-leg allowance and returned the first 72 when a request was longer. We also made the paid time for active replan drivers start when they became ready, including wait time before moving. These changes are dated in the protocol. Pilot outcomes stay outside the held-out counts.

Sol joined after the first two models. The first CLI rejected its model ID at service startup. The installed desktop CLI supported it with the same account, so we reran the pilot through that version and used it for all Sol results below.

## 3. Checking a plan

The checker replays each vehicle's departure and stop order. It reads directed travel times, waits for opening, loads, checks the deadline and adds freight to the onboard weight, volume and pallet totals. It then checks the return trip against the shift end.

Timeouts, malformed replies and responses without routes provide no plan to score. In a readable plan, timing, equipment and capacity failures are counted separately. A stop can have more than one violation. Any violation makes the complete day's plan fail.

The partial pickup score helps explain invalid plans. For example, if a day needs 240 pickups and an answer serves 200 within their local windows, equipment and load rules, its partial coverage is 200/240, or 83.3%. That day contributes zero to the dispatchable-day count if any required pickup is missing or any route breaks a rule. The partial score credits distinct stops that pass their individual checks even if another copy appears in the plan or the truck eventually returns late. We pair operating cost only across days where both compared methods produce a clean plan, and we say how many days are in each comparison.

### A complete route from raw answer to score on pilot P01

Terra received the pickup table and its map. The first sentence of the prompt asks for an implementable plan for every listed pickup. The required JSON object uses the vehicle ID as a key and starts the value with a departure minute, followed by the pickup IDs in order. The same request text goes to Luna and Sol. The map conditions also receive the frozen image. The direct evaluator infers the start location and depot return from the manifest.

The opening instructions below are copied from the cached request. The full stop and road tables are in the linked record.

```text
Dispatch case P01, morning. Produce an implementable plan for every listed pickup. Each stop ID must appear exactly once across all ordered vehicle routes. Output one JSON object only. Format {"routes":{"V01":[480,12,5],"V02":[490,4]}} where the first integer is departure minute since midnight (480 is 08:00), then only pending pickup IDs. Omit vehicles with no new pickups.
```

The model returned the following route object.

```json
{"routes":{"V01":[510,13,21,7,3,6,22],"V02":[540,2,10,1,12,11,16,14],"V03":[530,23,17,24,15,8,19],"V04":[534,9,20,18,5,4]}}
```

Read the row for **V03**, the refrigerated van. Its sequence is 23 → 17 → 24 → 15 → 8 → 19. The evaluator checks that every one of these jobs allows a chilled vehicle, then works through the pickup clock and adds each new load to what is already inside the van.

| Pickup | Address | Window | Service min | Arrives | Starts | Ends | Load aboard |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 23 | 1928 Queen St E | 08:00–09:43 | 11 | 09:16 | 09:16 | 09:27 | 141 kg / 833 L |
| 17 | 1416 Victoria Park Ave | 08:19–10:14 | 11 | 09:42 | 09:42 | 09:53 | 236 kg / 1,501 L |
| 24 | 3601 Victoria Park Ave | 09:17–10:52 | 12 | 10:12 | 10:12 | 10:24 | 307 kg / 3,019 L |
| 15 | 3030 Don Mills Rd E | 12:27–13:16 | 9 | 10:33 | 12:27 | 12:36 | 403 kg / 3,525 L |
| 8 | 801 York Mills Rd | 12:27–14:17 | 13 | 12:49 | 12:49 | 13:02 | 492 kg / 4,533 L |
| 19 | 1 Valleybrook Dr | 12:27–14:30 | 9 | 13:07 | 13:07 | 13:16 | 633 kg / 5,473 L |

Take the first leg. The van leaves at 08:50. The drive to pickup 23 takes 26 scheduled minutes and it arrives at 09:16. Loading starts at 09:16 and takes 11 minutes, so the finish at 09:27 is checked against the 09:43 deadline. The remaining rows repeat that arithmetic with the van's new location and load. The van returns at 13:44, before its 16:30 shift deadline. The checker independently accepted all 24 pickups across the 4 vehicles on this pilot day. This small case demonstrates the output format and a genuine success. The held-out mornings have ten times as many pickups.

[Full request and reply, turn 1](data/cache/27edf8d63791063c8c5545c56edcaac908fea9c0204999dd554228e099b6bf76.json) · [Full request and reply, turn 2](data/cache/06ed09599439394dab79d4113949aa974e5c3f543c4cb148dd698bc9894b3aa5.json)

## 4. Morning and 11 a.m. results

### Did the entire dispatch plan work?

Read dispatchable days first. A full plan must fit every route rule for every remaining pickup. The figure counts days on the horizontal axis. The upper bars compare deterministic baselines, the middle bars show direct model plans, and the lower bars show model drafts with solver assistance.

![Dispatchable days by method, shown separately for 24 mornings and 24 replans](figures/dispatchable_days.png)

The day counts make it clear where the comparison sits near a floor. Luna returned 23/24 readable text drafts and 21/24 readable map drafts, with 0/48 dispatchable mornings. Terra returned 1/24 readable text drafts and 0/24 readable map drafts, with 0/48 dispatchable mornings. Sol returned 0/24 readable text drafts and 0/24 readable map drafts, with 0/48 dispatchable mornings. A count based on readable routes alone answers whether those drafted routes held up. The all-day count also includes attempts in which dispatch never received a route list.

#### Morning dispatch

| Method | Dispatchable | Readable but invalid | Unreadable / timeout / error | Pass on readable | Pickup coverage | Coverage on readable | Median seconds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Insertion | 3/24 | 21 | n/a | 3/24 | 98.0% | 98.0% | 0.2 |
| OR-Tools | 15/24 | 0 | 9 no plan | 15/15 | 62.5% | 100.0% | 150.0 |
| Insertion + solver | 15/24 | 0 | 9 no plan | 15/15 | 62.5% | 100.0% | 150.0 |
| Luna text | 0/24 | 23 | 1 / 0 / 0 | 0/23 | 4.8% | 5.0% | 14.9 |
| Luna map | 0/24 | 21 | 3 / 0 / 0 | 0/21 | 5.8% | 6.6% | 16.3 |
| Terra text | 0/24 | 1 | 20 / 3 / 0 | 0/1 | 3.8% | 90.4% | 23.8 |
| Terra map | 0/24 | 0 | 23 / 1 / 0 | n/a | 0.0% | n/a | 7.8 |
| Sol text | 0/24 | 0 | 0 / 24 / 0 | n/a | 0.0% | n/a | 151.4 |
| Sol map | 0/24 | 0 | 0 / 24 / 0 | n/a | 0.0% | n/a | 151.4 |
| Luna text + solver | 15/24 | 0 | 9 no plan | 15/15 | 62.5% | 100.0% | 150.0 |
| Luna map + solver | 15/24 | 0 | 9 no plan | 15/15 | 62.5% | 100.0% | 150.0 |
| Terra text + solver | 13/24 | 0 | 11 no plan | 13/13 | 54.2% | 100.0% | 150.0 |
| Terra map + solver | 14/24 | 0 | 10 no plan | 14/14 | 58.3% | 100.0% | 150.0 |
| Sol text + solver | 0/24 | 0 | 24 no plan | n/a | 0.0% | n/a | 151.4 |
| Sol map + solver | 0/24 | 0 | 24 no plan | n/a | 0.0% | n/a | 151.4 |

Morning OR-Tools found a dispatchable plan on 15/24 days. Insertion alone passed 3/24, and insertion followed by the solver passed 15/24. An empty optimizer result is shown in the no-plan column. A partial, readable insertion plan appears under invalid. The distinction matters when choosing whether to start from a cheap proposed plan or to start the search empty.

#### 11 a.m. replan

| Method | Dispatchable | Readable but invalid | Unreadable / timeout / error | Pass on readable | Pickup coverage | Coverage on readable | Median seconds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Insertion | 12/24 | 12 | n/a | 12/24 | 99.1% | 99.1% | 0.0 |
| OR-Tools | 11/24 | 0 | 13 no plan | 11/11 | 45.7% | 100.0% | 0.4 |
| Insertion + solver | 15/24 | 0 | 9 no plan | 15/15 | 62.4% | 100.0% | 120.0 |
| Luna text | 0/24 | 20 | 2 / 2 / 0 | 0/20 | 30.4% | 36.6% | 22.7 |
| Luna map | 0/24 | 18 | 5 / 1 / 0 | 0/18 | 26.5% | 35.4% | 24.3 |
| Terra text | 2/24 | 15 | 0 / 7 / 0 | 2/17 | 68.4% | 96.5% | 103.6 |
| Terra map | 3/24 | 16 | 1 / 4 / 0 | 3/19 | 75.9% | 95.9% | 91.0 |
| Sol text | 0/24 | 0 | 0 / 24 / 0 | n/a | 0.0% | n/a | 121.4 |
| Sol map | 0/24 | 0 | 0 / 24 / 0 | n/a | 0.0% | n/a | 121.4 |
| Luna text + solver | 10/24 | 0 | 14 no plan | 10/10 | 41.6% | 100.0% | 120.0 |
| Luna map + solver | 11/24 | 0 | 13 no plan | 11/11 | 45.7% | 100.0% | 120.0 |
| Terra text + solver | 10/24 | 0 | 14 no plan | 10/10 | 41.5% | 100.0% | 120.0 |
| Terra map + solver | 10/24 | 0 | 14 no plan | 10/10 | 41.6% | 100.0% | 120.0 |
| Sol text + solver | 0/24 | 0 | 24 no plan | n/a | 0.0% | n/a | 121.4 |
| Sol map + solver | 0/24 | 0 | 24 no plan | n/a | 0.0% | n/a | 121.4 |

At the interruption, the unseeded solver passed 11/24 and insertion followed by the solver passed 15/24. All stage comparisons get the same 11 a.m. state. The model's morning failure cannot affect its replan score. The two stages differ in the size of the remaining problem and in the committed work already aboard.

### How much of the work was covered?

The figure gives each readable direct plan one point. It plots the percentage of pending pickups that pass the local checks, with a small line for the median. A solver can use the entire cost matrix. The model must work from the exact legs quoted in the prompt and the optional bounded lookup. The points are useful for comparing two readable plans even when both fail as full dispatches.

![Individual pickup coverage among readable drafts, with text and map conditions side by side](figures/pickup_coverage.png)

The number of plotted replies differs because the models submit plans at different rates. For instance, a single readable draft can have a high coverage percentage while dozens of days still give dispatch nothing to work with. For operational comparisons use the all-day rate in the previous tables as well as the point distributions here.

### Did the map improve a paired attempt?

For each day and model we subtract the number of individually passing pickups in the text condition from the number in the map condition. The all-day comparison assigns zero passing pickups to replies that supply no plan. The last two columns repeat the comparison on case pairs with two readable plans. Positive differences favour maps.

| Stage | Model | Readable pairs | Map wins / ties / text wins (all) | Median additional stops (all) | Map wins / text wins (readable) | Median additional stops (readable) |
| --- | --- | --- | --- | --- | --- | --- |
| Morning dispatch | Luna | 20 | 6 / 11 / 7 | +0.00 | 6 / 6 | +0.00 |
| Morning dispatch | Terra | 0 | 0 / 23 / 1 | +0.00 | 0 / 0 | n/a |
| Morning dispatch | Sol | 0 | 0 / 24 / 0 | +0.00 | 0 / 0 | n/a |
| 11 a.m. replan | Luna | 17 | 7 / 6 / 11 | +0.00 | 7 / 8 | +0.00 |
| 11 a.m. replan | Terra | 12 | 13 / 3 / 8 | +1.00 | 6 / 3 | +0.50 |
| 11 a.m. replan | Sol | 0 | 0 / 24 / 0 | +0.00 | 0 / 0 | n/a |

Use both halves of the table. The map can change whether the model attempts to solve the case as well as what it writes. When many attempts tie at zero or few pairs have two readable plans, the comparison says little about map-assisted stop ordering. Small differences in full-plan counts are descriptive for this address panel and workload mix.

### What did the solver do with the available time?

On days where the configured unseeded solver found a plan, its median time to its first complete plan was 0.18 seconds in the morning and 0.06 seconds at 11 a.m. That first plan is the point at which dispatch could act. The solver often spends the rest of the 150 or 120 seconds searching for a cheaper valid list. The median time columns in the tables refer to when each process finishes.

The next table uses only days when both methods returned a dispatchable plan. The percentage difference compares operating costs on the same day. Negative values mean less cost. The saved table also reports changes in kilometres, driver hours and vehicles. [Paired operating measures](data/paired_cost.csv)

| Method | Morning paired | Cheaper | Median cost | 11 a.m. paired | Cheaper | Median cost |
| --- | --- | --- | --- | --- | --- | --- |
| Insertion | 3 | 0 | +33.89% | 8 | 0 | +11.13% |
| Insertion + solver | 15 | 1 | +0.00% | 11 | 4 | +0.00% |
| Luna text + solver | 15 | 0 | +0.00% | 10 | 0 | +0.00% |
| Luna map + solver | 15 | 0 | +0.00% | 11 | 0 | +0.00% |
| Terra text + solver | 13 | 0 | +0.02% | 9 | 0 | +0.75% |
| Terra map + solver | 14 | 0 | +0.00% | 9 | 1 | +0.37% |
| Sol text + solver | 0 | 0 | n/a | 0 | 0 | n/a |
| Sol map + solver | 0 | 0 | n/a | 0 | 0 | n/a |

![Paired change in operating cost compared with the configured unseeded optimizer](figures/operating_cost.png)

For morning dispatch, median hybrid cost changes range from +0.00% (Luna text + solver, 15 paired days) to +0.02% (Terra text + solver, 13 paired days). For 11 a.m. replan, median hybrid cost changes range from +0.00% (Luna text + solver, 10 paired days) to +0.75% (Terra text + solver, 9 paired days). A fallback gives the same optimizer fewer seconds to work, so an identical plan is possible and a weaker plan can reflect the lost search time. An accepted seed can instead change the part of the search space the optimizer starts in. Seed and fallback counts separate these mechanisms.

The solver accepted 5 model drafts. Across all stage and model arms, 169 conditions used a cold fallback with time left. The remaining timeouts could not run a fallback. [Seed and fallback counts by condition](data/summary.csv)

The configured optimizer starts with parallel cheapest insertion, then tries to improve the complete route it finds. In a supplemental check after freezing the experiment, the same solver with local cheapest insertion produced 10/24 mornings and 12/24 replans in two seconds. That included 1 mornings and 1 replans missed by the originally configured search. The short diagnostic shows why the precise initialization matters. The primary comparison keeps the originally configured search and timing.

### What changed for drivers?

The replan has three incident pickups per day, for 72 across the 24 days. The incident total counts each affected pickup if it passes its individual checks, even on a day that fails overall. The driver-change and time columns use dispatchable days only. Paid minutes are compared with the old list under the old windows, so the difference can be negative when the new list saves time.

| Method | Dispatchable | Incident pickups on time | Median lists changed | Median extra paid minutes |
| --- | --- | --- | --- | --- |
| OR-Tools | 11/24 | 33/72 | 24 | -253.00 |
| Insertion + solver | 15/24 | 45/72 | 24 | -259.00 |
| Luna text + solver | 10/24 | 30/72 | 24 | -250.00 |
| Luna map + solver | 11/24 | 33/72 | 24 | -250.00 |
| Terra text + solver | 10/24 | 30/72 | 24 | -239.00 |
| Terra map + solver | 10/24 | 30/72 | 24 | -236.50 |
| Sol text + solver | 0/24 | 0/72 | n/a | n/a |
| Sol map + solver | 0/24 | 0/72 | n/a | n/a |
| Luna text | 0/24 | 21/72 | n/a | n/a |
| Luna map | 0/24 | 13/72 | n/a | n/a |
| Terra text | 2/24 | 50/72 | 23.5 | -15.50 |
| Terra map | 3/24 | 57/72 | 24 | -51.00 |
| Sol text | 0/24 | 0/72 | n/a | n/a |
| Sol map | 0/24 | 0/72 | n/a | n/a |

A separate simple repair used the old list and kept each incident pickup on its original truck. Trying earlier places in that list yielded 24/24 dispatchable replans, with a median of 3 changed driver lists and +14.5 extra paid minutes under the scenario objective. This method starts with information the primary arms did not receive. The test generator deliberately built incidents repairable by changing those orders. For this scenario, it supplies a practical reference and shows why retaining the old schedule can matter.

### Where the test was hardest

| Method | Morning ordinary | Morning tight | Morning scarce | 11 a.m. ordinary | 11 a.m. tight | 11 a.m. scarce |
| --- | --- | --- | --- | --- | --- | --- |
| Insertion | 3/8 | 0/8 | 0/8 | 8/8 | 3/8 | 1/8 |
| OR-Tools | 8/8 | 4/8 | 3/8 | 7/8 | 0/8 | 4/8 |
| Insertion + solver | 8/8 | 4/8 | 3/8 | 8/8 | 3/8 | 4/8 |
| Luna text | 0/8 | 0/8 | 0/8 | 0/8 | 0/8 | 0/8 |
| Luna map | 0/8 | 0/8 | 0/8 | 0/8 | 0/8 | 0/8 |
| Terra text | 0/8 | 0/8 | 0/8 | 1/8 | 0/8 | 1/8 |
| Terra map | 0/8 | 0/8 | 0/8 | 2/8 | 0/8 | 1/8 |
| Sol text | 0/8 | 0/8 | 0/8 | 0/8 | 0/8 | 0/8 |
| Sol map | 0/8 | 0/8 | 0/8 | 0/8 | 0/8 | 0/8 |

Each cell above is eight days. The same address panel is used across workloads. The specialist-capacity group has fewer easy ways to move refrigerated or palletized freight across trucks. The tight-window days reduce the tolerated margin for a wrong sequence. Some individual days look very different inside a group. The table helps keep an overall mean from hiding failures concentrated in those more constrained days.

## 5. Reading the plans that passed and failed

The main tables separate whether the model returned a route list from whether the proposed route would work. Across the full fleet conditions, the replies with no readable plan included timeout 114, declined to provide routes 45, other format 8, empty plan reply 2. A model that explains why it cannot confidently dispatch may be giving useful commentary to a person, but it leaves the requested route pending. A model that returns JSON can still create extra work for the same dispatcher. The table counts individual operating-rule violations in readable direct plans.

| Issue in readable plans | Morning records | 11 a.m. records |
| --- | --- | --- |
| extra copies | 2026 | 1023 |
| incompatible | 1729 | 279 |
| invalid departure | 54 | 49 |
| late return | 107 | 6 |
| late window | 3481 | 838 |
| missing pickups | 7753 | 1946 |
| over kg | 1529 | 280 |
| over litres | 1542 | 293 |
| over pallets | 1398 | 186 |
| unknown vehicle | 72 | 0 |

One late truck can produce a string of late stops, so these counts are records, not independent days. An overloaded vehicle may stay overloaded for several visits because every pickup adds freight until the depot. Read the violation table together with the day counts and the concrete fixes below.

### A morning list that arrived after closing on D01

Luna map returned a readable plan on **D01**. It served **71 of 240** pickups under the local checks and had 138 late visit records. This is one readable reply near the middle of the partial-coverage range we inspected. The vehicle below is one route from the parsed output.

```json
{"V05":[480,5,58,136,125,85,103,62,83,3,179,110]}
```

Pickup **110** at **105 Midwest Rd** takes 10 minutes to load. It must finish by 14:16. Assigned vehicle **V05** gets there at 14:18, begins loading at 14:18, and finishes at 14:28. It is 12 minutes too late. Counting the stop in the JSON proves only that the model listed it. Dispatch would need to move it earlier or find another vehicle with room and time. The checker records that timing failure even if the equipment and address are correct.

[Exact cache record for this reply](data/cache/b0fbc8489b6c5cc3cedf35b801cd20350e76e251042abfd968c2e50d6c7f2855.json)

### A text and map disagreement on D23

We selected the largest gap in individually valid pickups among case–model pairs that had two readable plans. On **D23** at 11 a.m. replan, **Luna map** served 66 of 96 pickups. **Luna text** served 0. Both received the same input row for stop **3** at **18 Wynford Dr**. Its hours were 11:47–14:10, loading took 8 minutes, and its permitted vehicle types were chill.

| Attempt | Replayed pickup outcome |
| --- | --- |
| Luna text | Omitted from scored visits |
| Luna map | V19 finished at 12:38 and V21 finished at 13:59 (incompatible) and V23 finished at 14:27 (late_window, over_kg, over_litres) |

This example shows what one partial-score difference can look like in a dispatch list. A label on the map cannot explain why the model made its choice. The paired results use all eligible days, including days that show the opposite direction and days when one response never supplied a plan.

### A readable message with no route list on D01

Terra map was asked to return the complete route object for morning dispatch. It returned this message in the response stream.

```text
{"error":"I cannot verify a feasible plan covering all 240 pickups with the provided travel data and constraints."}
```

This message can tell a dispatcher that the model wants more help. The response never assigns a vehicle or gives a stop order, so the route checker cannot score it. We recorded this as a declined plan, separate from an attempted route with violations. Treating it as a wrong stop order would overstate what the benchmark observed.

[Full request and record](data/cache/d302953ef78a9f6a6b06653698b656c113dda0de7230be6d3871b0bfc5cbdc28.json)

### A loading dock closes early on D01

The figure follows one driver's remaining pickup list. Gray bars show other loading appointments and the coloured bar shows the affected pickup. The dashed line is the new cutoff.

![Timeline of a pickup moved ahead of the dock's new closing time](figures/replan_closing_time.png)

On **D01**, pickup **81** at **3027 Islington Ave** originally closed at 14:16. At 11 a.m. it moved to 12:51. The shared reference would have completed loading at 12:57. The verifier's revised list completes it at 12:46. The vehicle is V03. At the point where it can take a new instruction, it has 330 kg, 2,790 L and 0 pallet positions already in use. Those quantities remain on board throughout the suffix. The plan changes stop order to preserve the pickup.

The revised order shown is the feasibility witness frozen with the test inputs. Moving the visit is enough for this truck. Other policies can hand it to a different compatible vehicle or choose another time, as long as the full replay passes. By design, each unchanged day misses exactly three revised deadlines.

## 6. Sequencing one truck in one part of the day

A carrier can first assign jobs to a truck by area and period, then ask a planner to order the jobs inside each assignment. The first step still has to reserve enough refrigeration, box space and time across the fleet. For this follow-up we supplied the fixed assignments and tested the second step. That changes the task from dividing the whole day's work among 24 vehicles to visiting a small set of already assigned stops.

We selected one geographic and time block per held-out day, with 12 morning and 12 afternoon blocks. They contain 4–5 pickups. The median maximum directed road distance between jobs within a block is 14.0 km. The morning block starts at the depot and must reach a specific handoff before the next booking. The afternoon block starts from a truck's pending release point after 11 a.m., with its existing load, and finishes at the depot. Every planner gets the complete directed road table for the small block and uses the same fixed departure.

We checked every permutation of the assigned stops. Five stops have 5 × 4 × 3 × 2 × 1 = 120 possible orders. Any order that passes the checker is feasible. A feasible response earns the exact-minimum result if its operating cost equals the cheapest feasible order, including ties. That is a stronger quality reference than the whole-fleet study, where the search is time-limited.

| Model | Block | Cases | Feasible | Exact minimum | No readable plan | Median seconds |
| --- | --- | --- | --- | --- | --- | --- |
| Luna | Morning | 12 | 9 | 5 | 0 | 23.6 |
| Luna | Afternoon | 12 | 10 | 7 | 0 | 23.8 |
| Terra | Morning | 12 | 11 | 11 | 0 | 15.3 |
| Terra | Afternoon | 12 | 12 | 12 | 0 | 10.5 |
| Sol | Morning | 12 | 12 | 12 | 0 | 35.5 |
| Sol | Afternoon | 12 | 12 | 12 | 0 | 14.9 |

Luna found an exact minimum on 12/24 blocks and a feasible order on 19/24. Terra found an exact minimum on 23/24 blocks and a feasible order on 23/24. Sol found an exact minimum on 24/24 blocks and a feasible order on 24/24. Results combine the 12 morning and 12 afternoon blocks per model. The experiment changes both the size of the assignment and the road data available to the model. In this version each of the small blocks fits its whole distance table in one prompt.

![Feasible and minimum-cost orders for one truck at a time, by model and time block](figures/single_truck_blocks.png)

Solid bars count orders whose cost matches the verified minimum. The hatched bars include every feasible order. A gap between the bars means the method got the dispatch rules right and left some operating cost on the table.

### Worked single-truck block on D02, V01

The block begins at **708 Annette St** at 12:17, with 509 kg aboard, and must finish at **165 The Queensway** by 16:30. We counted 4 feasible orders among 24 permutations. The cheapest shown order is **51 → 196 → 1 → 97**. It reaches the endpoint at 13:55 at a scenario cost of CAD 64.67. Luna returned **51 → 196 → 1 → 97**, which matches the minimum cost.

| Pickup | Address | Opens | Must finish | Exact order starts | Exact order ends |
| --- | --- | --- | --- | --- | --- |
| 51 | 4906 Dundas St W | 12:08 | 12:40 | 12:27 | 12:33 |
| 196 | 1550 Jane St | 12:08 | 14:20 | 12:48 | 12:56 |
| 1 | 2179 Bloor St W | 12:08 | 13:25 | 13:10 | 13:19 |
| 97 | 196 Royal York Rd | 12:37 | 14:16 | 13:34 | 13:45 |

We substituted each feasible block back into the reference fleet plan, preserving the other driver lists. The independent checker accepted 66 of 66 replacements. This tests one substitution per day within its existing schedule. The bridge between blocks matters as much as finding a short order. A good morning ordering still has to hand the truck and its full load to the next part of its schedule at the agreed location and time. Errors in assigning the work to zones or capacity would affect the whole fleet even if each small order is optimal. Our upstream assignments come from a known feasible reference. The block scores do not measure whether a planner can create those assignments.

## 7. Limitations

The manifests reuse one Toronto address panel and follow the same morning and afternoon waves. Freight, access rules and time windows are simulated around a known schedule. Multiple depots, live requests or driver absences would expose other constraints.

Static road estimates omit observed traffic and depot queues. A [municipal restriction spot check](data/geography_sources.md) found a truck prohibition missing from the checked OpenStreetMap segment. Dispatchability here means the plan meets the modeled rules. Live dispatch would need current restriction and loading access checks.

The text and map conditions share the same bounded road lookup. The optimizer has the full matrix. This tests direct planning with that interface. A model writing and running a heuristic or translating dispatch notes into solver constraints is a different workflow.

At 11 a.m. almost every truck is already committed to its next stop. The assigned work and feasibility snapshots describe the end of those commitments. The experiment doesn't test a truck breakdown with cargo onboard. The old-list repair is particularly effective because the generator builds all three incidents so they can be repaired by moving stops within the current lists.

Paired cost compares only mutually feasible days. Whole-fleet solvers give time-limited results, and changing their first-plan strategy recovers some missed days. The small-block comparison checks exact costs on assigned jobs and includes a complete leg table. It measures stop ordering after assignment.

The original settings were fixed before the Luna and Terra held-out collection. Sol and the truck-block experiments came later at the owner's request. Sol used the newer Codex CLI. Time includes CLI execution and solver work. Prompt assembly, parsing, file writes and tracing sit outside it. [Protocol history](data/PROTOCOL.md)

## 8. How to reproduce

[The executed notebook](49_pickup_routing.ipynb) replays the responses offline, checks the routes and redraws the figures. Timed optimizer runs are saved as frozen plans.

Install the Python dependencies and run Jupyter from this experiment folder.

```bash
python -m pip install -r requirements.txt
python -m nbconvert --to notebook --execute --inplace 49_pickup_routing.ipynb
```

The notebook has switches for cache misses and local solver reruns. Fresh calls need the pinned Codex CLI and model access. Wall-clock search can produce different costs on replaying the solver. Each cache record stores the full request and reply, including the digest of any [map image](data/maps/).

- [Frozen city inputs and licences](data/geography_sources.md), [held-out dispatch cases](data/full_cases.json.gz), and [single-truck blocks](data/full_blocks.json.gz) contain the instances, reference plans and incident records.
- [Per-arm day scores](data/results.csv), [dispatch summary](data/summary.csv), [paired cost comparison](data/paired_cost.csv), and [map pairs](data/map_pairs.csv) contain the primary results.
- [Single-truck results](data/block_results.csv), [solver sensitivities](data/sensitivity_results.csv), and [unreadable reply audit](data/format_audit.csv) contain the follow-up evidence.
- [Individual model requests and replies](data/cache/), [timed comparison plans](data/full_solver.json.gz), and [run manifest](data/manifest.json) make the calculations traceable.

### Model usage and spend

| Batch | Sessions | CLI turns | Reported input tokens | Reported output tokens | Turns missing usage | Planning-rate estimate |
| --- | --- | --- | --- | --- | --- | --- |
| Fleet pilot | 24 | 35 | 462,653 | 29,485 | 5 | US$ 5.66 |
| Full fleet | 288 | 366 | 7,069,640 | 318,995 | 114 | US$ 81.86 |
| Truck-block pilot | 6 | 6 | 72,707 | 1,169 | 0 | US$ 0.77 |
| Full truck blocks | 72 | 72 | 880,505 | 38,227 | 0 | US$ 10.14 |

The scoped runs made 479 CLI turns. Reported usage totals **US$ 98.43** at the fixed planning rates of US$10 per million input tokens and US$35 per million output tokens. The CLI did not supply billed spend. Turns that supplied no usage contribute no known tokens, so the estimate leaves those tokens unknown. The eight prior Sol access errors are cached and are outside these scored sessions. Their provider responses included no usage.

## 9. Future work and further reading

Links checked November 18, 2026.

### Future work

1. **Validate the vehicle assignment as well as sequencing.** Assign work by geography, time and equipment. Vary the jobs per block and check whole-fleet feasibility after stitching. The local results motivate testing the assignment step.
2. **Replan with yesterday's list and a bigger disruption.** Give planners the old lists and simulate a truck failure or new urgent orders. Measure service and changes to drivers' lists. The old-list repair shows why retaining those lists matters.
3. **Test a solver portfolio and explicit stability costs.** Compare several starting strategies and add a documented cost for changing a driver list. Record first feasible plan and final cost at equal deadlines. The alternate constructor recovered some primaries, and rebuilding from an empty suffix can send many drivers a changed list.
4. **Offer richer road data and dispatch notes.** Match the exact road data available to LLMs and solvers at each scale, and vary the road lookup budget or provide an independent constraint tool. Then test a separate LLM step that turns a note such as “forklift is down, send a liftgate” into a checkable constraint. The morning model outputs show that being willing to offer a plan and returning a correct plan are separate problems.

### Further reading

- [Algorithms for the Vehicle Routing and Scheduling Problems with Time Window Constraints](https://pubsonline.informs.org/doi/10.1287/opre.35.2.254) (Solomon, 1987). Introduces benchmark instances and insertion strategies for routes with customer time windows.
- [A Review of Dynamic Vehicle Routing Problems](https://www.cirrelt.ca/documentstravail/cirrelt-2011-62.pdf) (Pillac et al., 2011). The authors' working-paper version describes ways to revise routes as new information becomes available.
- [PyVRP: A High-Performance VRP Solver Package](https://arxiv.org/abs/2403.13795) (Wouda et al., 2024). A documented alternative search framework for studying time windows and routing quality.
- [2021 Amazon Last Mile Routing Research Challenge: Data Set](https://pubsonline.informs.org/doi/10.1287/trsc.2022.1173) (Merchán et al., 2022). Observed delivery routes provide a different setting for studying what schedules and road costs miss about real driver behavior.
