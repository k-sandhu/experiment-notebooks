# Process documentation format (version 0.3)

This format records how an organisation is structured and how its processes run, in enough detail to
build an operations simulation from the files alone. There are two kinds of file:

- An **organisation file** describes one organisation: its units, roles, systems, the things that flow
  between processes, and a map of every process it runs with the links between them.
- A **workflow file** describes one process step by step: who does what, how long it takes, how long work
  waits, where it branches or loops back, and which checks are mandatory.

Workflow files plug into an organisation file through shared ids, so that many workflows can later be
assembled into a model of the whole organisation. Every field below has a fixed meaning and unit.

Version 0.3 adds optional fields for organisations that do physical work in the field, in plants or on
wards: equipment, vehicles, crews and beds as limited `resources`, `shift_pattern` on roles, `surge` for
bursts of extra work, the step kind `travel`, the wait causes `weather`, `resource_availability` and
`site_access`, the control type `safety`, and `people` on steps for work done by a crew or a team at the same time. Files written to version 0.2 remain valid.

## Reference period

Describe how things ran in 2019 to 2022, with the ordinary software of that period (ERP, ticketing,
workflow tools, email, spreadsheets, and scanning or rule-based automation where it was already common).
Describe the common practice of organisations of this type, not the best practice and not a broken one.

## Evidence tiers

Every role, unit, volume, process, step and benchmark carries an `evidence` object:
`{"tier": "A", "sources": ["src3"], "note": ""}`.

| Tier | Meaning | Requirement |
|---|---|---|
| A | A number or fact taken from a published benchmark, annual report, event log, regulation, standard or study | At least one entry in `sources`, opened by the author, that states it |
| B | Derived from a documented description (a standard, manual, textbook, job posting, practitioner guide, company web page) | At least one source that describes it |
| C | The author's estimate from general knowledge | No source needed. Say what the estimate rests on in `note` |

Never cite a source that was not opened. Never invent a URL, a title or a statistic. A tier C estimate is
acceptable; a false tier A is not. When sources disagree, record the range in `low` and `high` and say so
in `note`.

A source's `url` may be empty when the link is withheld: three organisation files (the diagnostic laboratory,
the pension fund manager and the public asset manager) do not name the real organisations they were modelled
on, so links to those organisations' own pages are left out. The source was still opened when the file was
written; its title, publisher and summary are kept with the names replaced.

## Units and conventions

- Ids are lowercase with hyphens or underscores, unique within their list.
- Ranges are triangular: `{"low": n, "mode": n, "high": n}` with `low <= mode <= high`. `low` is a fast or
  small ordinary case, `mode` the most common, `high` a slow or large ordinary case.
- `touch_min`: hands-on working minutes for one unit of work at a step.
- `wait_before_min`: elapsed calendar minutes (nights and weekends included) between the work arriving at
  a step and the role starting it. One day in a queue is 1,440. A week is 10,080.
- Probabilities are between 0 and 1. The `prob` values in one step's `next` list sum to 1.
- Money is in the file's `currency` (`CAD` or `USD`). Loaded cost per hour is wage plus benefits and
  overhead; say which loading factor was used.
- `layer` is one of `individual_contributor`, `senior_specialist`, `supervisor`, `manager`, `director`,
  `executive`, `external_party`.
- `cadence` is one of `per_case`, `daily`, `weekly`, `monthly`, `quarterly`, `annual`, `ad_hoc`.
- `shift_pattern` (optional, on a role) is one of `office_hours` (weekday days), `extended_hours` (two
  shifts or weekend cover), `shift_24x7` (rotating shifts around the clock), `field_rotation` (blocks of
  days on site followed by days off, for example 14 on and 7 off), `on_call` (called out when needed).
  Leave it out for office roles. It explains waits: a step handled by an `office_hours` role that arrives
  on Friday evening waits for Monday.
  The staffing check counts productive hands-on hours a month per person by shift pattern: 130 for
  `office_hours` and `on_call`, 140 for `extended_hours`, 150 for `shift_24x7`, 200 for `field_rotation`.
  A role whose paid time is nearly all hands-on work (a driver whose on-duty hours are all route time) may
  set `productive_hours_per_month` (60 to 300) to replace that default, with the basis in its evidence note.
  Put the same value on the role in the organisation file and in each workflow that uses it.
- A `surge` (optional) is a burst of extra work with a known cause: `{"cause": "major storm",
  "events_per_year": range, "duration_days": range, "volume_multiplier": range, "evidence": {...}}`.
  `volume_multiplier` is the volume during the surge divided by the ordinary volume. Use it for storms,
  spring break-up, wildfire season, flu season, quarter-end rushes and similar bursts. Ordinary monthly
  ups and downs go in `seasonality`.

## Organisation file

Saved as `organisations/<id>.json`.

| Field | Meaning |
|---|---|
| `schema_version` | `"0.3"` |
| `id`, `name` | Id matches the file name. The name describes the type of organisation |
| `modelled_on` | Which real organisation or organisations the public information came from, or `null` |
| `sector`, `summary` | Summary: five to eight sentences a newcomer can follow on what the organisation does, who its customers are, how it earns money and how it is organised |
| `currency` | `CAD` or `USD` |
| `profile` | `period`, `country`, `employees`, `ownership`, `regulators` (list of names), `scale` (list of `name`, `value`, `unit`, `evidence`: revenue, assets, sites, volumes) |
| `units` | The organisation chart as a tree. Each: `id`, `name`, `parent` (unit id or `null`), `kind` (`division`, `department`, `team`, `shared_service`, `site_network`), `headcount` (people in this unit including its children), `purpose` (one or two sentences), `evidence` |
| `roles` | Every role that takes part in a process. Each: `id`, `title`, `unit`, `layer`, `reports_to` (role id or `null`), `headcount`, `loaded_cost_per_hour` (range), `occupation_code` (for example `NOC 12200` or `SOC 43-3031`, or `null`), `evidence`. Optional `shift_pattern`, optional `productive_hours_per_month`, and optional `contractor_headcount`: how many of the `headcount` people are supplied by a contractor rather than employed. `headcount` is everyone who does the role's work, so the staffing check uses it; `profile.employees` and unit headcounts leave the contractor staff out |
| `systems` | `id`, `name`, `kind` (`system_of_record`, `workflow`, `communication`, `document_store`, `analytics`, `spreadsheet`, `external_portal`, `instrument`, `other`), `used_by` (unit ids) |
| `resources` | Optional. Physical things whose limited number can hold work up: `id`, `name`, `kind` (`equipment`, `vehicle`, `crew`, `facility`, `plant`, `bed`), `unit` (owning unit id), `count`, `available_hours_per_month` (range, per item, after maintenance and downtime), `cost_per_hour` (optional range: running cost per hour of use, fuel and maintenance included, staff excluded), `evidence`. Examples: a fracturing fleet, a bucket truck, a line crew, a haul truck, a tower crane, a tractor-trailer, an operating room, an inpatient bed. A crew listed here is a fixed team that is dispatched as one unit; its members still appear in `roles` |
| `business_objects` | The things that pass between processes: `id`, `name`, `description` ("lease application", "specimen", "trade ticket", "invoice") |
| `external_parties` | `id`, `name`, `description` (customers, suppliers, regulators, custodians, partners) |
| `demand_drivers` | What sets the workload: `id`, `name`, `per_month` (range), `unit`, `evidence` ("credit applications received", "patient visits") |
| `process_map` | Every process the organisation runs. See below |
| `sources`, `assumptions`, `author` | Sources as in workflow files. `author` is `{"model": ..., "date": ...}` |

Each `process_map` entry:

| Field | Meaning |
|---|---|
| `id`, `name` | Process id and plain name |
| `owner_unit` | The unit accountable for it |
| `category` | `core` (delivers what customers pay for), `support` (finance, HR, IT, facilities, legal) or `management` (planning, governance, risk, compliance) |
| `description` | Two to four sentences: what happens, who is involved, what makes it hard |
| `unit_of_work` | The thing that flows through: "one credit application" |
| `cadence` | See conventions |
| `cases_per_month` | Range |
| `driver` | The demand driver id that sets its volume, or `null` |
| `triggered_by` | What starts a case: list of `from` (a process id or an external party id) and `object` (a business object id) |
| `inputs` | Optional. Standing inputs the process relies on that do not start a case (a rate card, a policy, a system release, a reference file), in the same form as `triggered_by` |
| `produces` | List of `to` (a process id or an external party id) and `object` |
| `roles` | Role ids that take part |
| `resources` | Optional. Resource ids the process uses |
| `surge` | Optional. See conventions |
| `detail_priority` | `1` for the processes most worth documenting step by step (high volume, high cost, central to the organisation), `2` next, `3` the rest |
| `evidence` | Tier and sources |

The map should let a reader follow one customer request from the outside party that starts it, through
every process it touches, to the outside party that receives the result, and should show which support
and management processes each unit depends on. Link every process to at least one other process or
outside party.

## Workflow file

Saved as `workflows/<id>.json`.

| Field | Meaning |
|---|---|
| `schema_version` | `"0.3"` |
| `id`, `name` | Id matches the file name |
| `org` | The organisation file id this workflow belongs to, or `null` for a general workflow |
| `process` | The `process_map` id it documents, or `null` |
| `sector`, `function` | Industry (or `cross-industry`) and owning function |
| `summary` | Three to five sentences a newcomer can follow: what the process is for, who is involved, what makes it slow or error-prone |
| `baseline` | `period`, `org_archetype` (one sentence), `org_size_employees`, `notes` |
| `currency` | `CAD` or `USD` |
| `unit_of_work`, `trigger`, `end_state` | The thing that flows through, what starts a case, what "done" means |
| `cadence` | See conventions |
| `volume` | `cases_per_month` (range), `seasonality`, `evidence`, and optionally `surge` (see conventions) |
| `interfaces` | `triggered_by`: list of `from`, `object`, `share` (shares sum to 1). `inputs` (optional): standing inputs that do not start a case, as a list of `from`, `object`. `produces`: list of `outcome` (an END outcome label from the steps, or `any`), `to`, `object`. When `org` is set, `from` and `to` are process ids or external party ids from the organisation file and `object` is a business object id. When `org` is `null`, use plain names |
| `roles` | `id`, `title`, `department`, `layer`, `fte_on_process` (full-time equivalents this role spends on this process), `loaded_cost_per_hour` (range), `occupation_code`, `evidence`. When `org` is set, use the organisation file's role ids, titles and costs; a role the organisation file lacks may be added with `"not_in_org_file": true` |
| `systems` | `id`, `name`, `kind`. When `org` is set, use the organisation file's system ids where they exist |
| `resources` | Optional. `id`, `name`, `kind`, `count`, `cost_per_hour` (optional range) for each resource the steps use. When `org` is set, use the organisation file's resource ids; one the organisation file lacks may be added with `"not_in_org_file": true` |
| `steps` | See below. The first step in the list is the start |
| `exceptions` | `name`, `share_of_cases`, `description`, `path` (list of step ids) |
| `benchmarks` | `metric`, `value`, `unit`, `population`, `evidence`. Include `cycle_time_days` with `value` `{"p50": n, "p90": n}` when any source supports it |
| `pain_points` | `description`, `steps` (ids), `evidence` |
| `sources` | `id`, `title`, `publisher`, `url`, `year`, `accessed`, `supports` |
| `assumptions` | Choices the author made that a reader should know |
| `author` | `model`, `date` |

### Steps

A step is one piece of work done by one role without handing over. Split a step when the role changes,
when the work waits in a queue, or when a decision sends cases down different paths. Aim for 18 to 30
steps, with every approval, review, lookup, re-keying between systems, chase and wait on an outside party
written as its own step.

| Field | Meaning |
|---|---|
| `id` | `s01`, `s02`, ... |
| `name` | Short verb phrase |
| `description` | Two to four sentences on what the person does: what they open, what they compare, what they type, what they decide and on what basis |
| `role` | A role id, or `system` for an automated step, or `external` for a party outside the organisation |
| `kind` | `intake`, `data_entry`, `lookup`, `validation`, `analysis`, `judgment`, `drafting`, `review`, `approval`, `communication`, `coordination`, `physical`, `travel`, `system_auto`, `external_wait`. `travel` is time a person or crew spends getting to or between sites; count it in `touch_min` because they are paid for it |
| `inputs`, `outputs` | Documents or data the step needs and produces |
| `systems` | System ids used |
| `touch_min`, `wait_before_min` | Ranges. See conventions |
| `wait_cause` | `none`, `queue`, `batch`, `external_party`, `calendar`, `approval_availability`, `transit`, `weather`, `resource_availability` (waiting for a truck, crew, rig, bed or other resource to come free), `site_access` (waiting for a site to be ready, a permit window, road bans or a customer to give access) |
| `error` | `introduces_defect_prob`, `defect_description`, `typically_caught_at` (a step id, `"downstream"`, or `null`) |
| `control` | `null`, or `type` (`segregation_of_duties`, `regulatory`, `licensed_signoff`, `policy`, `audit_requirement`, `accreditation`, `safety` for permits to work, lockout, hazard assessments, pre-job safety meetings and similar), `basis` (the rule, named), `removability` (`fixed_by_law`, `needs_policy_change`, `discretionary`) |
| `desk_work_share` | 0 to 1: the share of the step done at a desk on documents, data and systems, as opposed to physical work or dealing with someone in person |
| `experience_needed` | `low`, `medium`, `high`: how much the step depends on experience that is not written down |
| `concurrent_with` | Optional list of step ids that in practice run at the same time as this one. When a step and the step visited just before it name each other here, the simulation overlaps them: only the part of the later step that outlasts the earlier one adds to elapsed time |
| `people` | Optional, default 1. How many people in `role` do the step together, for example a six-person concrete crew, two operators on a shift, or eight accountants each closing their own projects in the same week. `touch_min` is then the elapsed working time of the step, and labour hours are `touch_min` times `people`. Use it instead of adding up each person's minutes in `touch_min`, which would stretch the elapsed time, and instead of entering one person's minutes for a whole crew, which would understate labour cost |
| `resources` | Optional list of `{"id": resource id, "occupied_min": range}`: resources the step ties up and for how many minutes per case. A frac fleet rigged up on a well pad, a bucket truck at a pole, an operating room during a case. `occupied_min` can exceed `touch_min` when the resource is held while people wait |
| `next` | List of `to` (a step id or `"END"`), `prob`, `condition`, and for `"END"` an `outcome` label. Rework is an edge back to an earlier step |
| `evidence` | Tier, sources, note |

The step graph is sequential with probabilistic branches. Where different roles work in parallel, list the
steps in sequence, set `wait_before_min` near zero for the later ones and name the earlier step in
`concurrent_with`. Where several people in the same role do the same work at once, use one step with `people`.

## Checking a file

```bash
python tools/validate.py organisations/<id>.json
python tools/validate.py workflows/<id>.json
```

For an organisation file the validator checks the structure and every reference, compares unit and role
headcounts with the stated employee count, and prints the process count by unit and category and any
process that links to nothing.

For a workflow file it checks the structure and references (against the organisation file when `org` is
set), then walks 5,000 simulated cases through the step graph and prints the median and 90th percentile
cycle time, hands-on time, handoffs, rework and labour cost. Compare those with the `cycle_time_days`
benchmark and with what the sources say. A large gap means the step times, the waits or the branch
probabilities are off; fix them or explain the gap in `assumptions`.
