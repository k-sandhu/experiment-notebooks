# Generated from 48_agent_team_designs.ipynb, do not edit. Regenerate it by setting WRITE_SCRIPT = True in the
# last code cell of the notebook and running that cell, then run: python agent_teams.py --selftest

# %% [markdown]
# # Splitting office work among AI agents
#
# ## One credit file on one desk
#
# A small construction company wants an excavator. It applies to an equipment-finance company, which will buy the machine and lease it to the company over five years. Before any money moves, someone in the credit team works the file: checks that the application is complete, looks up the credit score, adds up what the company already owes, decides whether to approve, refer to a manager or decline, and lists the conditions to meet before the machine is released. Each answer goes into a box on a form.
#
# A useful outcome is easy to state: every box is right. A wrong exposure figure can send the decision to someone without the authority to sign it; a missing condition can release the machine before something the customer promised has arrived. One wrong box can cost money even when the others are perfect, so a file counts as done only when all of them are right.

# %% [markdown]
# ### A small example
#
# This example is made up, with easy numbers. The company asks for $50,000 and already owes $20,000 on an earlier lease, so its total exposure would be $70,000. Its score is 700, the forms are signed and the business is four years old. The policy says such a file is approved, and an analyst may sign it because the exposure is under the analyst's limit. The clerk fills in the boxes: complete, score 700, exposure $70,000, approve, analyst. It is careful reading and simple arithmetic.
#
# Now add one complication. Among the papers is a two-line email from the colleague who manages the customer relationship: release must also wait for a signed environmental undertaking. It is not on any form. A clerk who reads it adds one more code to the conditions. A clerk who skims past it releases the excavator without the undertaking, and nothing else on the form would show the mistake.

# %% [markdown]
# ### When the work is split
#
# Large firms rarely leave a file with one person. A credit file usually passes along a line of specialists, from an intake coordinator to a credit analyst who decides and a release coordinator who writes the final conditions. Each sees the papers for their own step and the form as it arrives.
#
# Splitting the work changes where information lives. The relationship email lands with the intake coordinator at the start of the line, but the conditions box is filled in at the end. The sentence can travel only in the note each person writes for the next, and every handoff is a chance for it to be dropped, shortened, or retold so that it sounds less certain. The first person may also get a colleague's summary that states one value wrongly, to be checked against the signed papers.

# %% [markdown]
# ### Two ways to organise a team
#
# In a line, or **pipeline**, each person sees only their own papers, the boxes filled so far and the previous person's note, and cannot change earlier boxes. In a **shared record**, everyone sees every paper and everything written so far, and anyone may correct an earlier box. A pipeline can also end with a **checker**: one more person who sees everything and fixes what is wrong. The pipeline keeps each person's reading short but depends on the notes; the shared record and the checker remove that dependence at the cost of more full readings.

# %% [markdown]
# ### Why ask this about AI agents
#
# In this experiment an **AI agent** is a language model given a role, instructions and some documents, which returns the boxes it was asked to fill and a note for the next agent. Companies are starting to build teams of such agents that copy their organisation charts. Every added agent means more text to read and write, which is what model use is paid for, so if splitting the work loses facts, a bigger team could cost more and finish fewer files correctly.
#
# Economists who study firms ask how output grows as a firm adds workers. If each added agent brought the same amount of correct work, correct output would grow in proportion to the team; if handoffs lose information, it would grow more slowly or not at all. A useful result says which arrangement finishes the most files fully right, and how much each added agent buys.

# %% [markdown]
# ## The question
#
# When several AI agents work one piece of office work together, does the way they are organised change how many cases they get fully right, and how does correct output grow as agents are added? The experiment compares one agent that sees everything with pipelines of 2, 4 and 8 agents, a shared record of 4 and a pipeline of 4 followed by a checker, on the same 80 generated cases from four office processes, 20 each. Two arms added after the first results were seen test explanations for them: a second model alone, and one agent followed by three agents who each redo the whole case.

# %% [markdown]
# ## Study summary
#
# Eight arms worked the same 80 cases: capital call notices, small equipment-finance credit applications, laboratory claims to a provincial health plan and block trades, 20 of each. Each case has eight stations, an exact answer computed by code, and one easily missed sentence (the **planted fact**) in a document only the first station sees; in 17 cases a colleague's intake note also states one value wrongly. Claude Sonnet 5.5 formed every team; GPT-6.1 Terra was the checker and, in one control arm, worked alone. A case is **fully correct** only when every field is right. Scores use each agent's final answer, with the first-answer score in brackets where it differs.
#
# - Passing work down a line lost accuracy. One Sonnet agent with everything got **67 of 80** cases fully correct (65); pipelines of 2, 4 and 8 got 59 (54), 60 (57) and **47** (39). The pipeline of 8 trails one owner on the same cases by 25.0 points (interval 12.5 to 38.8; 32.5 on first answers). The pipelines of 2 and 4 trail by 10.0 and 8.8 points with intervals that reach zero under both readings. Nine of the pipeline of 2's failures were unreadable forms; on readable cases it scores 83.1%, beside the owner's 83.8%.
# - More agents meant more reading and writing for little more correct output. Work rose from 9,163 characters per case for one owner to 40,532 for the pipeline of 8. With the same work budget per agent, correct output grew with team size at an exponent of **0.13** (interval 0.03 to 0.22), where 1 is growth in proportion; on first answers, 0.07 (interval -0.05 to 0.18).
# - The shared record of 4 (79 of 80) and the pipeline of 4 with a Terra checker (80 of 80) were nearly perfect, but the control arms show neither result is about team structure. Terra alone got 78 of 80, 2 fewer than the checker arm (interval 0.0 to 6.2 points). One Sonnet owner followed by three full reviews got 80 of 80 (67, 78, 80 and 80 after each pass), and the shared record's first agent had already filled in every field, so it was also four full passes. These four arms differ by at most 2 cases, a ceiling at which this test cannot rank them.
#
# How a reply is read was changed after the results were seen. In 23 replies an agent wrote an answer, corrected itself and wrote a second one; the rule fixed in advance scored the first and, in pipelines, passed it on, so both readings are reported and the affected chains were re-run. Every conclusion above holds under both; the gap between the pipeline of 8 and one owner narrows, and the scaling exponent moves from indistinguishable from zero to a small rise still far below 1.
#
# In the credit office from the opening: dividing the papers among specialists lost correct files, a second full look at the whole file won them back, and one stronger worker with every paper beat every team that divided them. The caveats: the control arms and the second reading were chosen after seeing results; one model family formed the teams; and every case fits in one prompt, which favours one agent with everything. The wrong intake note sits at a ceiling (corrected in all 17 cases by every arm, apart from one unreadable form).
#
# ![Scatter of eight arms: characters of work per case against share of cases fully correct, on final answers.](figures/accuracy_vs_work.png)
#
# Each point is an arm: right means more work per case, up means more cases fully correct; hollow markers are control arms. The pipelines move right without moving up; the pipeline of 8 uses 4.4 times the owner's characters and finishes 20 fewer cases. The top-right group reaches 99% to 100% with 4.0 to 5.0 times the owner's work; Terra alone reaches 97.5% at the owner's cost.

# %% [markdown]
# ## Contents
#
# 1. [Setup and configuration](#1-setup-and-configuration)
# 2. [The cases and their exact answers](#2-the-cases-and-their-exact-answers)
# 3. [The team designs](#3-the-team-designs)
# 4. [Scoring and the measures](#4-scoring-and-the-measures)
# 5. [Reading a reply that holds two answers](#5-reading-a-reply-that-holds-two-answers)
# 6. [Running and caching](#6-running-and-caching)
# 7. [Replaying the scored run from the cache](#7-replaying-the-scored-run-from-the-cache)
# 8. [Offline checks of the code](#8-offline-checks-of-the-code)
# 9. [How the study got here](#9-how-the-study-got-here)
# 10. [One case from start to finish](#10-one-case-from-start-to-finish)
# 11. [Computing the tables and figures](#11-computing-the-tables-and-figures)
# 12. [Accuracy by design](#12-accuracy-by-design)
# 13. [What the control arms show](#13-what-the-control-arms-show)
# 14. [Accuracy by process](#14-accuracy-by-process)
# 15. [The planted fact and the wrong intake note](#15-the-planted-fact-and-the-wrong-intake-note)
# 16. [Work and scaling](#16-work-and-scaling)
# 17. [Unreadable forms and two ways to read a reply](#17-unreadable-forms-and-two-ways-to-read-a-reply)
# 18. [Error analysis](#18-error-analysis)
# 19. [Limitations](#19-limitations)
# 20. [What the evidence supports](#20-what-the-evidence-supports)
# 21. [Spend, data and how to reproduce](#21-spend-data-and-how-to-reproduce)
# 22. [Future work and further reading](#22-future-work-and-further-reading)
#
# ### How the experiment runs
#
# ```mermaid
# flowchart LR
#     G["Case generator (code)<br/>4 processes x 20 seeds = 80 cases<br/>12 short documents each"] --> T["Rule engine<br/>exact answer, 9 to 11 fields"]
#     G --> S["Second solver reads only the documents<br/>reproduces every answer"]
#     G --> A["8 arms on the same 80 cases<br/>1,822 Sonnet calls (Claude Code subagents)<br/>163 Terra calls (codex exec)"]
#     A --> P["Each reply read two ways<br/>first answer, final answer<br/>640 case results each"]
#     T --> C["Score every field<br/>correct, wrong or unreadable"]
#     P --> C
#     C --> R["Accuracy, paired differences,<br/>planted fact, intake note,<br/>characters, scaling exponent"]
# ```
#
# The notebook follows this path from left to right, replaying the model calls from a saved cache. One case travels through it like this. `credit-4802` is generated with 12 documents and an exact answer of 10 fields. The same documents go to every arm: one Sonnet call for the single owner, two to eight chained calls for a pipeline. Each arm's final form is compared field by field with the exact answer, and the characters of every prompt and reply are added up.

# %% [markdown]
# ## 1. Setup and configuration
#
# The first code cell imports the standard library, sets the size knobs and lists the two models. The knobs fix the 80 cases (20 for each of four processes, generated from one seed), the team sizes 2, 4 and 8, the four designs that run by default (the fifth, review, runs only when named), the number of bootstrap resamples behind every interval (4,000) and how many requests each provider may run at once. The notebook imports nothing from this repository. All code is below, and `agent_teams.py` beside the notebook is generated from it.
#
# A default run of the notebook makes no model call. Every reply was saved when the study ran, in `data/cache_requests.jsonl`, keyed by a hash of the whole request (model, prompt and settings). The notebook replays those replies, rebuilds both results tables from them, checks that the rebuilt tables equal the committed ones, and then draws the tables and figures. A cell that would call a model needs a command-line mode that this notebook never starts, and a guard cell in section 7 fails the run if any call or trace is attempted during a replay.

# %%
from __future__ import annotations

import argparse
import concurrent.futures as futures
import csv
import datetime as dt
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time

# Size knobs. A default run of this notebook replays the cache and calls no model; none of the
# knobs below makes a call by itself.
N_CASES_PER_PROCESS = 20
SEED = 4801
CALIBRATION_SEED = 4899
TEAM_SIZES = [2, 4, 8]
DESIGNS = ["owner", "pipeline", "shared", "checker"]
# "review" runs only when named (--designs review); it is not in the default list, so frozen runs are unchanged.
ALL_DESIGNS = DESIGNS + ["review"]
DIFFICULTY = 4
WORKERS = {"claude": 4, "codex": 2}
INJECTED_ERROR_SHARE = 0.25
# Replaces Codex's long built-in instructions; measured 21,375 input tokens for a one-line prompt
# with --ignore-user-config, against 27,351 by default and 25,441 with --ignore-user-config alone.
CODEX_INSTRUCTIONS = "You are a careful operations clerk. Answer from the material given."
OVERHEAD_PROBE_PROMPT = "Reply with the single word ok."
CALIBRATION_MODELS = ["Claude Sonnet 5.5"]
# "cli": the script calls the command-line tool. "subagent": Claude Code subagents answer outside the script;
# the script only exports the prompts it waits for and imports the replies (see --export-pending).
CLAUDE_ROUTE = "subagent"
SUBAGENT_AGENT_TYPE = None  # optional Claude Code agent type name for the workflow's agent() calls
SUBAGENT_PREFIX = "Answer the task below using only the text given here. Do not use any tool and do not read or write any file. Reply with the JSON object the task asks for and nothing else.\n\n"
MODELS = [
    {"name": "Claude Sonnet 5.5", "version": "claude-sonnet-5-5", "provider": "claude", "route": CLAUDE_ROUTE,
     "subagent_model": "sonnet", "subagent_effort": "low", "subagent_agent_type": SUBAGENT_AGENT_TYPE,
     "command": "claude -p", "reasoning_effort": None, "size_precision": "not published",
     "why": "First vendor team; independent checker for Terra"},
    {"name": "GPT-6.1 Terra", "version": "gpt-6.1-terra", "provider": "codex", "route": "cli",
     "command": "codex exec", "reasoning_effort": "low", "size_precision": "not published",
     "why": "Second vendor team; independent checker for Sonnet"},
]
DATA = Path("data")
TMP = DATA / "tmp"  # everything here can be rebuilt from data/cache_requests.jsonl (git-ignored)
RESULTS_FILES = {"first": DATA / "results.csv", "last": DATA / "results_last_object.csv"}
FIGURES = Path("figures")
NOTEBOOK = "48-agent-team-designs"
BOOTSTRAPS = 4000  # case resamples; one function and one seed produce every interval in tables and figures
# How a reply holding several JSON objects is read. "first" (the rule fixed in advance): the first complete object wins.
# "last": when a reply holds more than one complete top-level object with a "fields" key, the last one wins.
# The parser is never part of a cache key: a cached reply is the same text under either parser.
PARSER = "first"
PARSERS = ("first", "last")
PRIMARY_PARSER = "last"  # the parser the figures show (falls back to "first" when the "last" results are missing or incomplete)
PARSER_PHRASES = {"first": "scored on each agent's first answer", "last": "scored on each agent's final answer"}
PROCESS_NAMES = {
    "capital": "Capital call processing", "credit": "Small-ticket equipment credit",
    "lab": "Provincial laboratory billing", "trade": "Block trade allocation",
}
COMPLICATIONS = {
    "capital": ["over_unfunded", "excluded_purpose", "changed_bank", "callback_missing",
                "short_notice", "holiday", "fx_usd", "expense_cap", "fee_cap"],
    "credit": ["missing_consent", "low_bureau", "high_exposure", "excluded_industry",
               "used_equipment", "young_business", "fx_usd", "large_request", "bankruptcy"],
    "lab": ["expired_card", "version_mismatch", "duplicate_window", "uninsured_test",
            "unit_cap", "vitamin_ineligible", "holiday", "practitioner_missing", "fx_usd"],
    "trade": ["restricted_B", "restricted_C", "odd_lot", "holiday", "fx_usd",
              "commission_cap", "manual_ticket", "ssi_missing", "late_booking"],
}
MONEY_FIELDS = {"notice_amount", "eligible_amount", "cad_amount", "exposure_cad",
                "approved_amount", "plan_amount", "patient_amount", "average_price", "commission_cad"}
SET_FIELDS = {"exception_codes", "conditions", "payable_codes", "rejection_codes",
              "eligible_accounts", "exception_flags"}

# True inside a notebook kernel. Cells that only show results run when it is True, so importing
# the generated script never prints, replays or draws anything.
NOTEBOOK_RUN = "ipykernel" in sys.modules

# %% [markdown]
# The next cell holds small helpers shared by everything else: a canonical JSON writer (sorted keys, no spaces) so that identical requests give identical hashes, half-up rounding of money to cents, business-day arithmetic for deadlines and a function that renders a short business record.

# %%
def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def money(value):
    return format(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), ".2f")


def business_days(date, n, holidays=()):
    day = dt.date.fromisoformat(str(date))
    blocked = set(holidays)
    step = 1 if n >= 0 else -1
    for _ in range(abs(n)):
        day += dt.timedelta(days=step)
        while day.weekday() >= 5 or day.isoformat() in blocked:
            day += dt.timedelta(days=step)
    return day.isoformat()


def roll_business(date, holidays=()):
    day = dt.date.fromisoformat(date)
    while day.weekday() >= 5 or day.isoformat() in holidays:
        day += dt.timedelta(days=1)
    return day.isoformat()


def record(title, *lines):
    result = "\n".join([title, *lines, "Record status: issued for this case; amounts exclude tax unless stated."])
    assert 5 <= len(result.splitlines()) <= 25, title
    return result


def models_table(models=MODELS):
    try:
        import pandas as pd
        return pd.DataFrame(models)
    except ImportError:
        return "\n".join(canonical(model) for model in models)

# %% [markdown]
# ### The models
#
# | Model | Pinned version | Provider and how called | Size and precision | Settings that change output | Why included |
# |---|---|---|---|---|---|
# | Claude Sonnet 5.5 | `claude-sonnet-5-5`, Claude Code alias `sonnet` (version string in every cache row) | Anthropic; Claude Code 2.1 subagents, one per prompt, launched by a workflow script | not published | effort low; default agent type; every prompt starts with an instruction to use no tool | The team model in every Sonnet arm, so arms differ only in how work is divided |
# | GPT-6.1 Terra | `gpt-6.1-terra` | OpenAI; `codex exec` 0.160.1 with `--ignore-user-config`, read-only sandbox, one-line instruction | not published | reasoning effort low | Checker from a second vendor, and alone as a control, to separate what checking adds from what the model does alone |
#
# Sonnet ran as subagents because `claude -p` on the machine was signed out. Each subagent carried about 72,000 tokens of unreported standing context, including the project instruction file, and had tools it never used.

# %%
if NOTEBOOK_RUN:
    from IPython.display import Image, display
    import pandas as pd

    print(f"{N_CASES_PER_PROCESS} cases for each of {len(PROCESS_NAMES)} processes = {N_CASES_PER_PROCESS * len(PROCESS_NAMES)} cases; "
          f"team sizes {TEAM_SIZES}; designs {DESIGNS} (review only when named); {BOOTSTRAPS:,} bootstrap resamples; seed {SEED}.")
    display(pd.DataFrame(MODELS)[["name", "version", "provider", "route", "command", "reasoning_effort", "size_precision", "why"]])

# %% [markdown]
# ## 2. The cases and their exact answers
#
# The rules, names and amounts are fictional; they test careful reading and arithmetic, not knowledge of real regulation.
#
# | Process | What the case asks | Fields | Planted fact (late field it changes) |
# |---|---|---|---|
# | Capital call | Check a fund's request for money against the commitment and terms, deduct disallowed amounts, convert currency, check the bank account, set date and approval level | 9 | The release also needs a treasury or compliance countersignature (`release_control`, station 8) |
# | Equipment credit | The application from the opening | 10 | Release must await a signed environmental or ownership undertaking (`conditions`, station 8) |
# | Laboratory billing | Check the health card, decide which tests the plan pays, cap units and funding, price patient charges, list rejection codes, choose who is billed | 10 | An employer or study sponsor will receive every patient-pay charge (`billed_to`, station 7) |
# | Block trade | Split a share purchase among three accounts by weight in lots of 100, excluding restricted accounts; price, commission, settlement, flags | 11 | The ticket must carry a CLIENT_REVIEW or LEGAL_REVIEW flag (`exception_flags`, station 8) |
#
# Every case has 12 documents of 5 to 25 lines: the policy, a calendar, a currency rate confirmation, the relationship email holding the planted fact, and eight process records such as the bureau report. Each process has nine possible complications, such as a bankruptcy or a US-dollar request in credit, and each case draws four.
#
# The generator is code, so every case has an exact answer and nothing was written by a model that is also being tested. It works in four steps, each in its own cell below: draw the case parameters from a seed, compute the answer with a rule engine, write the twelve documents, and assemble the case with its intake note.

# %% [markdown]
# First, `make_parameters` draws the underlying amounts, dates and facts for one case, including which four of the nine complications apply and whether the intake note will carry a wrong value.

# %%
def make_parameters(process, seed):
    if process not in PROCESS_NAMES:
        raise ValueError(f"Unknown process {process!r}; choose {list(PROCESS_NAMES)}")
    if not 0 <= DIFFICULTY <= len(COMPLICATIONS[process]):
        raise ValueError("DIFFICULTY exceeds the available distinct complications")
    rng = random.Random(f"{process}/{seed}")
    complications = rng.sample(COMPLICATIONS[process], DIFFICULTY)
    c = set(complications)
    day = (dt.date(2026, 2, 2) + dt.timedelta(days=rng.randrange(240))).isoformat()
    day = roll_business(day)
    holidays = [business_days(day, 1)] if "holiday" in c else []
    p = {"seed": seed, "complications": complications, "date": day, "holidays": holidays,
         "name": rng.choice(["Maple Harbour", "Cedar Ridge", "Northlake", "Willow Creek"]),
         "currency": "USD" if "fx_usd" in c else "CAD", "fx": "1.3600" if "fx_usd" in c else "1.0000",
         "injected": rng.random() < INJECTED_ERROR_SHARE}
    if process == "capital":
        p.update(amount=money(rng.randrange(70000, 150001) + rng.randrange(100) / 100),
                 unfunded=money(rng.randrange(170000, 240001)),
                 investment=str(rng.randrange(30000, 50001)), expense="8000.00", fee="2000.00",
                 fee_base="400000.00", annual_fee="0.0200", period_days=90,
                 expense_cap="5000.00" if "expense_cap" in c else "10000.00",
                 purpose="PENALTY" if "excluded_purpose" in c else "INVESTMENT",
                 notice_bank="771902" if c & {"changed_bank", "callback_missing"} else "551700",
                 standing_bank="551700", callback="NO" if "callback_missing" in c else "YES",
                 planted_sentence=rng.choice([
                     "Mara asked that the final release also receive a treasury countersignature.",
                     "Mara asked that the final release also receive a compliance countersignature."]))
        if "over_unfunded" in c:
            p["unfunded"] = money(Decimal(p["amount"]) - 12000)
        if "fee_cap" in c:
            p["fee"] = "4500.00"
        p["due"] = business_days(day, 1 if "short_notice" in c else 7)
    elif process == "credit":
        p.update(requested=money(190000 if "large_request" in c else rng.randrange(18000, 75001)),
                 score=570 if "low_bureau" in c else rng.randrange(650, 791),
                 existing=money(230000 if "high_exposure" in c else rng.randrange(0, 40001)),
                 consent="NO" if "missing_consent" in c else "YES", invoice="YES", registry="ACTIVE",
                 industry="GAMBLING" if "excluded_industry" in c else "CONSTRUCTION",
                 equipment="USED" if "used_equipment" in c else "NEW", term=60,
                 age_months=8 if "young_business" in c else 48,
                 bankruptcy="YES" if "bankruptcy" in c else "NO",
                 planted_sentence=rng.choice([
                     "Leila mentioned that release must also await a signed environmental undertaking.",
                     "Leila mentioned that release must also await a signed ownership undertaking."]))
    elif process == "lab":
        p.update(version=rng.choice(["AB", "CD", "EF"]), card_end=business_days(day, -1 if "expired_card" in c else 90),
                 practitioner="MISSING" if "practitioner_missing" in c else str(rng.randrange(100000, 999999)),
                 vitamin_eligible="NO" if "vitamin_ineligible" in c else "YES",
                 tests=["CBC", "GLU", "VITD"] + (["TRAVEL"] if "uninsured_test" in c else []),
                 units={"CBC": 1, "GLU": 5 if "unit_cap" in c else 1, "VITD": 1, "TRAVEL": 1},
                 prior_glu=(dt.date.fromisoformat(day) - dt.timedelta(days=5 if "duplicate_window" in c else 45)).isoformat(),
                 remaining_cap=money(rng.choice([25, 50, 100])),
                 planted_sentence=rng.choice([
                     "Noah noted that the employer has agreed to receive every patient-pay charge.",
                     "Noah noted that the study sponsor has agreed to receive every patient-pay charge."]))
        p["submitted_version"] = "ZZ" if "version_mismatch" in c else p["version"]
    else:
        p.update(security=f"CA{rng.randrange(100000, 999999)}", weights={"A": rng.randrange(2, 8), "B": 3, "C": 2},
                 restricted=[a for a in ["B", "C"] if f"restricted_{a}" in c],
                 quantity=rng.randrange(7, 18) * 100 + (37 if "odd_lot" in c else 0),
                 price1=money(rng.randrange(1800, 4500) / 100), price2=money(rng.randrange(1800, 4500) / 100),
                 commission_rate="0.5000" if "commission_cap" in c else "0.0200", commission_cap="100.00",
                 ticket="MANUAL" if "manual_ticket" in c else "OMS",
                 ssi="MISSING" if "ssi_missing" in c else "VERIFIED", late="YES" if "late_booking" in c else "NO",
                 planted_sentence=rng.choice([
                     "Iris mentioned that the final ticket must carry the CLIENT_REVIEW flag.",
                     "Iris mentioned that the final ticket must carry the LEGAL_REVIEW flag."]))
        p["fill1"] = p["quantity"] // 2
        p["fill2"] = p["quantity"] - p["fill1"]
    return p

# %% [markdown]
# Second, `truth_from_params` is the rule engine. It computes every field of the exact answer directly from the parameters, step by step, following the fictional policy for the process.

# %%
def truth_from_params(process, p):
    D = Decimal
    if process == "capital":
        amount, unfunded = D(p["amount"]), D(p["unfunded"])
        allowed_fee = (D(p["fee_base"]) * D(p["annual_fee"]) * p["period_days"] / 360).quantize(D(".01"), ROUND_HALF_UP)
        excluded = D(p["investment"]) if p["purpose"] == "PENALTY" else D(0)
        allowed = max(D(0), amount - excluded - max(D(0), D(p["expense"]) - D(p["expense_cap"]))
                      - max(D(0), D(p["fee"]) - allowed_fee))
        eligible = min(unfunded, allowed)
        cad = D(money(eligible * D(p["fx"])))
        valid = amount <= unfunded
        wire = "MATCH" if p["notice_bank"] == p["standing_bank"] else ("VERIFIED_CHANGE" if p["callback"] == "YES" else "HOLD")
        approval = "VP" if cad > 150000 else "MANAGER" if cad > 50000 else "ANALYST"
        pay = max(roll_business(p["due"], p["holidays"]), business_days(p["date"], 3, p["holidays"]))
        flags = []
        for test, code in [(not valid, "OVER_COMMITMENT"), (excluded > 0, "EXCLUDED_PURPOSE"),
                           (D(p["expense"]) > D(p["expense_cap"]), "EXPENSE_CAP"),
                           (D(p["fee"]) > allowed_fee, "FEE_CAP"), (wire == "HOLD", "BANK_HOLD"),
                           (pay > roll_business(p["due"], p["holidays"]), "SHORT_NOTICE")]:
            if test:
                flags.append(code)
        return dict(notice_amount=money(amount), commitment_valid=valid, eligible_amount=money(eligible), cad_amount=money(cad),
                    wire_status=wire, approval_level=approval, payment_date=pay, exception_codes=flags,
                    release_control="TREASURY" if "treasury" in p["planted_sentence"] else "COMPLIANCE")
    if process == "credit":
        requested = D(money(D(p["requested"]) * D(p["fx"])))
        exposure = requested + D(p["existing"])
        complete = p["consent"] == "YES" and p["invoice"] == "YES" and p["registry"] == "ACTIVE"
        hard = p["score"] < 600 or p["bankruptcy"] == "YES" or p["industry"] == "GAMBLING"
        decision = "DECLINE" if hard else "REFER" if not complete or exposure > 250000 or p["age_months"] < 24 else "APPROVE"
        amount = min(requested, D(100000)) * (D("0.8") if p["equipment"] == "USED" else 1) if decision == "APPROVE" else D(0)
        term = min(p["term"], 36 if p["equipment"] == "USED" else 60) if amount else 0
        tier = "NONE" if not amount else "A" if p["score"] >= 720 else "B"
        authority = "MANAGER" if decision == "REFER" or exposure > 150000 else "SENIOR" if amount > 50000 else "ANALYST"
        conditions = ["ENV_UNDERTAKING" if "environmental" in p["planted_sentence"] else "OWNERSHIP_UNDERTAKING"]
        if not complete:
            conditions.append("COMPLETE_FILE")
        if p["equipment"] == "USED":
            conditions.append("VALUATION")
        if decision == "REFER":
            conditions.append("MANAGER_REVIEW")
        return dict(complete=complete, bureau_score=p["score"], exposure_cad=money(exposure), decision=decision,
                    approved_amount=money(amount), term_months=term, rate_tier=tier, authority=authority,
                    conditions=conditions, approval_expiry=business_days(p["date"], 10, p["holidays"]))
    if process == "lab":
        valid = p["date"] <= p["card_end"] and p["version"] == p["submitted_version"]
        codes, rejected = [], []
        patient, plan, units = D(0), D(0), 0
        duplicate = (dt.date.fromisoformat(p["date"]) - dt.date.fromisoformat(p["prior_glu"])).days <= 30
        for code in p["tests"]:
            n = min(p["units"][code], 2)
            eligible = valid and p["practitioner"] != "MISSING" and code != "TRAVEL" and (code != "VITD" or p["vitamin_eligible"] == "YES")
            if code == "GLU" and duplicate:
                rejected.append("DUPLICATE")
                continue  # Duplicate is neither province-pay nor patient-pay.
            fee = {"CBC": 12, "GLU": 5, "VITD": 30, "TRAVEL": 40}[code]
            if eligible:
                codes.append(code)
                units += n
                plan += fee * n
            else:
                patient += D(money(D(fee) * n * (D(p["fx"]) if code == "TRAVEL" else 1)))
                rejected.append("UNINSURED" if code == "TRAVEL" or code == "VITD" and p["vitamin_eligible"] != "YES" else "COVERAGE" if not valid else "PRACTITIONER")
            if p["units"][code] > 2:
                rejected.append("UNIT_CAP")
        if plan > D(p["remaining_cap"]):
            rejected.append("FUNDING_CAP")
        plan = min(plan, D(p["remaining_cap"]))
        billed = "EMPLOYER" if "employer" in p["planted_sentence"] else "SPONSOR"
        authority = "MANAGER" if patient > 100 else "SUPERVISOR" if rejected else "CLERK"
        return dict(card_valid=valid, card_version=p["version"], payable_codes=codes, payable_units=units,
                    plan_amount=money(plan), patient_amount=money(patient), rejection_codes=sorted(set(rejected)),
                    billed_to=billed, submission_date=business_days(p["date"], 1, p["holidays"]), authority=authority)
    eligible = [a for a in p["weights"] if a not in p["restricted"]]
    lots = p["quantity"] // 100
    total_weight = sum(p["weights"][a] for a in eligible)
    exact = {a: Fraction(lots * p["weights"][a], total_weight) for a in eligible}
    alloc = {a: exact[a].numerator // exact[a].denominator for a in eligible}
    ranking = sorted(eligible, key=lambda a: (-(exact[a] - alloc[a]), a))
    for a in ranking[:lots - sum(alloc.values())]:
        alloc[a] += 1
    avg = money((D(p["price1"]) * p["fill1"] + D(p["price2"]) * p["fill2"]) / p["quantity"])
    commission = money(min(D(p["commission_cap"]), D(p["quantity"]) * D(p["commission_rate"])) * D(p["fx"]))
    flags = ["CLIENT_REVIEW" if "CLIENT_REVIEW" in p["planted_sentence"] else "LEGAL_REVIEW"]
    for test, flag in [(bool(p["restricted"]), "RESTRICTED"), (p["quantity"] % 100 != 0, "ODD_LOT"),
                       (p["ssi"] == "MISSING", "SSI_HOLD"), (p["ticket"] == "MANUAL", "MANUAL"),
                       (p["late"] == "YES", "LATE")]:
        if test:
            flags.append(flag)
    auth = "DIRECTOR" if p["ssi"] == "MISSING" or p["restricted"] else "SENIOR" if p["ticket"] == "MANUAL" or D(avg) * p["quantity"] > 50000 else "ANALYST"
    return dict(security_code=p["security"], eligible_accounts=eligible,
                **{f"qty_{a}": alloc.get(a, 0) * 100 for a in "ABC"}, average_price=avg,
                commission_cad=commission, settlement_date=business_days(p["date"], 2 + (p["late"] == "YES"), p["holidays"]),
                authority=auth, exception_flags=flags, reconciled=p["quantity"] % 100 == 0)

# %% [markdown]
# Third, the policy for each process is a document in plain text. Every station reads it, and the rule engine and the documents must agree with it.

# %%
POLICIES = {
 "capital": [
    "Amounts are in notice currency. notice_amount is the signed notice total, not the intake summary.",
    "commitment_valid is true exactly when notice_amount <= unfunded; no recallable amounts are allowed.",
    "PENALTY investment purpose is excluded; INVESTMENT is permitted. Deduct excluded investment from the total.",
    "Allowed fee = fee base * annual fee * period days / 360, rounded to cents. Deduct fee excess only.",
    "Deduct expense excess over expense cap only. eligible_amount = min(unfunded, max(0, adjusted total)).",
    "cad_amount = eligible_amount * FX CAD per currency unit, half-up to cents. CAD uses rate 1.",
    "wire_status is MATCH for identical accounts; else VERIFIED_CHANGE with completed callback, else HOLD.",
    "approval_level is VP if cad_amount > 150000, MANAGER if > 50000, otherwise ANALYST; holds do not change it.",
    "payment_date is later of due date rolled forward to a business day and receipt plus 3 business days, even on HOLD.",
    "Business days exclude Saturday, Sunday and the calendar's closed dates; exclude the starting day when adding days.",
    "exception_codes: OVER_COMMITMENT if invalid; EXCLUDED_PURPOSE for PENALTY; EXPENSE_CAP or FEE_CAP for excess.",
    "Also BANK_HOLD if wire_status HOLD and SHORT_NOTICE if payment_date exceeds rolled due date; no other codes.",
    "release_control is TREASURY or COMPLIANCE if requested in early correspondence, otherwise STANDARD.",
    "Carry unscored facts needed later in your outgoing note; do not add them to the scored form.",
 ],
 "credit": [
    "complete is true iff consent YES, invoice YES and registry ACTIVE. bureau_score comes from the bureau report.",
    "Convert requested amount at FX CAD per unit, half-up to cents; exposure_cad is converted request plus existing CAD.",
    "DECLINE if score < 600, bankruptcy YES or industry GAMBLING (excluded); this outranks all referral rules.",
    "Otherwise REFER if incomplete, exposure_cad > 250000 or business age < 24 months; otherwise APPROVE.",
    "approved_amount is zero unless APPROVE; then min(converted request, 100000) times 0.8 for USED, else times 1.",
    "Round all money half-up to cents. Never reduce the exposure calculation by the approved-amount cap.",
    "term_months is zero if amount zero, else min(requested term, 36 for USED or 60 for NEW).",
    "rate_tier is NONE if amount zero, else A if bureau_score >= 720, otherwise B; A means 6%, B means 9%.",
    "authority is MANAGER if REFER or exposure > 150000; else SENIOR if approved_amount > 50000; else ANALYST.",
    "conditions includes COMPLETE_FILE if incomplete, VALUATION if USED, MANAGER_REVIEW if REFER, even on decline.",
    "Also include ENV_UNDERTAKING or OWNERSHIP_UNDERTAKING if requested in early correspondence, even on decline.",
    "approval_expiry is application date plus 10 business days, even on decline. No additional condition codes.",
    "Business days exclude weekends and calendar closures, and the starting date. CAD FX rate is 1.",
    "Keep unscored early facts, including bespoke undertakings, in outgoing notes for downstream colleagues.",
 ],
 "lab": [
    "card_valid iff service date <= coverage end and submitted version equals authoritative card version; start is already valid.",
    "card_version is the authoritative version, regardless of eligibility. Health numbers are synthetic.",
    "Payable schedules CAD/unit: CBC=12.00, GLU=5.00, VITD=30.00. TRAVEL=40.00 in travel currency is excluded.",
    "A GLU within 30 calendar days inclusive after prior GLU is DUPLICATE: omit entirely, no province or patient charge.",
    "Otherwise cap each test at 2 units; add UNIT_CAP if requested units > 2. Excess units are not billed.",
    "Insured if card valid, practitioner present, non-TRAVEL, and for VITD eligibility YES. Others go to patient-pay.",
    "payable_codes is the set of insured codes; payable_units is their capped units; plan_amount is their scheduled sum capped by remaining funding.",
    "Add FUNDING_CAP if insured sum exceeds remaining funding. Cap shortfall is written off, never billed to patient.",
    "patient_amount sums ineligible nonduplicate fees at capped units; convert TRAVEL at stated FX CAD/unit; half-up per line to cents.",
    "For each ineligible line add UNINSURED if TRAVEL or ineligible VITD, else COVERAGE if invalid card, else PRACTITIONER.",
    "rejection_codes is the set of these codes plus duplicate/unit/funding codes; no other codes.",
    "billed_to is EMPLOYER or SPONSOR if early correspondence accepts all patient-pay charges, otherwise PATIENT, even if zero charges.",
    "submission_date is service date plus 1 business day; exclude start, weekends and calendar closures.",
    "authority is MANAGER if patient_amount > 100; else SUPERVISOR if any rejection codes; otherwise CLERK.",
    "Pass early payer arrangements and source details in your outgoing note. This is a fictional plan, not actual provincial advice.",
 ],
 "trade": [
    "security_code is the identifier on the signed execution report, never the informal intake note.",
    "eligible_accounts excludes restricted accounts; redistribute all whole lots pro rata to remaining account weights.",
    "A lot is 100 shares. Floor block quantity / 100; hold residual shares unallocated (ODD_LOT).",
    "Exact lots = whole lots * eligible weight / sum eligible weights. Floor each; award remaining lots by largest fractional remainder.",
    "Tie break: alphabetical account code ascending. qty_A, qty_B, qty_C are allocated shares, zero for excluded accounts.",
    "average_price = sum(fill shares * fill price) / total shares, half-up to 2 decimals, in execution currency; include odd shares.",
    "commission_cad = min(total shares * agreed rate, commission cap in execution currency) * FX CAD/unit; half-up to cents.",
    "settlement_date = trade date + 2 business days, plus 1 more business day if booking after cutoff YES.",
    "Business days exclude starting day, weekends and calendar closures. CAD rate is 1.",
    "authority is DIRECTOR if SSI MISSING or any restricted account; else SENIOR if MANUAL or rounded average_price * total shares > 50000; else ANALYST.",
    "exception_flags includes RESTRICTED if any restriction, ODD_LOT for residual, SSI_HOLD if missing, MANUAL if manual, LATE if after cutoff.",
    "Add CLIENT_REVIEW or LEGAL_REVIEW if mentioned in early correspondence. No other flags.",
    "reconciled iff allocated shares equal executed shares; odd-share residuals make it false, even when intentionally held.",
    "Pass unscored execution facts and correspondence to colleagues in your note. Prices and fees are fictional.",
 ],
}

# %% [markdown]
# Fourth, `render_documents` writes the twelve short records from the parameters. The planted sentence goes into the relationship email only, and the amounts and dates appear in the form each record would use.

# %%
def render_documents(process, p):
    R = record
    head = f"{p['name']} | {p['date']} | file {p['seed']}"
    docs = {
        "policy": R(f"{PROCESS_NAMES[process]} | operating policy v1", *POLICIES[process]),
        "calendar": R("Operations business calendar", f"Case date: {p['date']}",
                      "Closed dates: " + (", ".join(p["holidays"]) or "NONE"),
                      "Weekend convention: Saturday and Sunday closed", "All dates are ISO YYYY-MM-DD; no other closures apply."),
        "fx": R("Treasury rate confirmation", f"Currency: {p['currency']}", f"CAD per currency unit: {p['fx']}",
                f"Value date: {p['date']}", "Use this fixed rate; no spread or tax is charged."),
        "correspondence": R(f"Relationship mailbox | {head}", "From: relationship administrator",
                            "Subject: additional handling on the attached file", p["planted_sentence"],
                            "The remaining administrative arrangements are unchanged."),
    }
    if process == "capital":
        docs.update({
          "notice": R(f"Signed capital call notice | {head}", f"Notice total: {p['amount']}",
                      f"Receipt date: {p['date']}", f"Due date: {p['due']}", f"Notice wire account: {p['notice_bank']}",
                      "General partner: Harbour Private Markets GP; LP: Maple Pension Trust"),
          "commitment": R("Private markets commitment register", f"Unfunded balance: {p['unfunded']}",
                          "Recallable balance: 0.00", "Limited partner: Maple Pension Trust", "Fund: Harbour Private Markets III"),
          "breakdown": R("Fund administrator component schedule", f"Investment component: {p['investment']}",
                         f"Purpose: {p['purpose']}", f"Expense component: {p['expense']}", f"Fee component: {p['fee']}",
                         "Other permitted investments make up the difference to the signed total."),
          "partnership": R("Partnership terms extract", f"Fee base: {p['fee_base']}", f"Annual fee: {p['annual_fee']}",
                           f"Fee period days: {p['period_days']}", f"Expense cap: {p['expense_cap']}", "Penalty investments are excluded."),
          "standing_wire": R("Verified standing wire instructions", f"Standing account: {p['standing_bank']}",
                             "Beneficiary: Harbour Private Markets III", "Bank: Dominion Custody Bank", "Known callback contact: Mara Chen, fund controller"),
          "callback": R("Manager callback log", f"Callback completed: {p['callback']}", "Contact obtained from verified directory",
                       "Manager: Rowan Patel", "A YES confirms the account on this notice; NO means unverified."),
          "authority": R("Delegated payment authority", "Analyst limit CAD: 50000.00", "Manager limit CAD: 150000.00",
                        "VP: above manager limit", "Separate correspondence countersignatures still apply."),
          "payment": R("Custodian payment preparation ticket", "Earliest lead time: 3 business days after receipt",
                      "Requested value date: due date from signed notice", "Custodian: Dominion Custody", "Calculate scheduled date even if wire remains on hold."),
        })
    elif process == "credit":
        docs.update({
          "application": R(f"Equipment finance application | {head}", f"Requested amount: {p['requested']}",
                           f"Requested term: {p['term']}", f"Consent signed: {p['consent']}", f"Invoice attached: {p['invoice']}",
                           "Originator: Cedar Equipment vendor desk"),
          "registry": R("Corporate registry extract", f"Registry status: {p['registry']}", f"Business age months: {p['age_months']}",
                       f"Industry: {p['industry']}", f"Legal name: {p['name']} Contracting Ltd."),
          "bureau": R("Commercial and guarantor bureau report", f"Verified bureau score: {p['score']}", f"Bankruptcy: {p['bankruptcy']}",
                     "Entity match: confirmed", "Report obtained with application consent or supplied historical consent."),
          "exposure": R("Lease management relationship extract", f"Existing CAD exposure: {p['existing']}",
                       "Related parties: included in total", "Arrears CAD: 0.00", "Exposure excludes the new requested transaction."),
          "equipment": R("Supplier invoice and valuation", f"Equipment condition: {p['equipment']}",
                        "Asset: compact excavator and attachments", "Supplier: Cedar Equipment Ltd.", "Used-asset advance factor: 0.80; new: 1.00"),
          "rate_card": R("Small-ticket rate card", "Tier A score minimum: 720; annual rate 6%", "Tier B minimum: 600; annual rate 9%",
                        "No funded decision: NONE", "Term limits months: used 36; new 60"),
          "authority": R("Credit delegation schedule", "Analyst amount limit CAD: 50000.00", "Senior exposure limit CAD: 150000.00",
                        "Manager handles referral or exposure over senior limit", "Exposure means full converted request plus existing balance."),
          "release": R("Vendor desk release checklist", "Offer life: 10 business days after application",
                      "Conditions must include bespoke relationship undertakings", "Release to: Cedar Equipment vendor desk", "Dates are recorded even for declined applications."),
        })
    elif process == "lab":
        test_lines = [f"Test {c}: units {p['units'][c]}" for c in p["tests"]]
        docs.update({
          "card": R(f"Eligibility service response | {head}", f"Authoritative card version: {p['version']}",
                   f"Coverage end: {p['card_end']}", "Coverage start: 2020-01-01", "Health number: SYNTHETIC-480000"),
          "requisition": R("Scanned signed laboratory requisition", f"Service date: {p['date']}", f"Submitted version: {p['submitted_version']}",
                          f"Practitioner number: {p['practitioner']}", f"Vitamin eligibility: {p['vitamin_eligible']}", "Patient: Avery Morgan (fictional)"),
          "lis_order": R("Laboratory information system completed order", *test_lines,
                        "Report status: final", "All listed tests were performed; no other tests were ordered."),
          "prior_claims": R("Provincial paid claim history", f"Prior GLU service date: {p['prior_glu']}",
                           "No other duplicate claims are on file", "Prior payer: provincial plan", "History matched to synthetic health number."),
          "fee_schedule": R("Fictional provincial laboratory fee schedule", "CBC: CAD 12.00/unit, insured",
                            "GLU: CAD 5.00/unit, insured", "VITD: CAD 30.00/unit if eligible", "TRAVEL: 40.00/unit in travel currency; uninsured"),
          "funding": R("Corporate funding cap workbook", f"Remaining funding CAD: {p['remaining_cap']}",
                      "Cap is applied to this order after line eligibility", "Above-cap amounts: written off", "Do not transfer funding shortfalls to patients."),
          "billing": R("Patient billing setup", "Default payer: PATIENT", "Early correspondence may replace default for all patient-pay items",
                      "No tax, deductibles or other coverages", "Send no invoice in this experiment; calculate disposition only."),
          "submission": R("Claims upload and escalation procedure", "Submit next business day following service",
                         "Manager reviews patient-pay above CAD 100; supervisor handles edits", "Clean claim authority: CLERK", "Use case calendar closures."),
        })
    else:
        docs.update({
          "execution": R(f"Signed execution report | {head}", f"Security identifier: {p['security']}", f"Executed shares: {p['quantity']}",
                        f"Trade date: {p['date']}", "Broker: Northlake Securities; side: BUY"),
          "mandates": R("Portfolio pre-allocation instruction", *[f"Account {a} weight: {p['weights'][a]}" for a in "ABC"],
                       "Weights are relative demand; all accounts use the same custody currency."),
          "restrictions": R("Compliance restriction register", "Restricted accounts: " + (", ".join(p["restricted"]) or "NONE"),
                           "Restriction applies to this security and date", "Restricted accounts must receive zero shares", "Redistribute demand to unrestricted accounts."),
          "fills": R("Broker execution fills", f"Fill 1: {p['fill1']} shares at {p['price1']}",
                    f"Fill 2: {p['fill2']} shares at {p['price2']}", "No cancelled fills", "Prices are in the execution currency on treasury confirmation."),
          "commission": R("Broker commission agreement", f"Commission per share: {p['commission_rate']}", f"Commission cap: {p['commission_cap']}",
                         "Cap currency: execution currency", "No taxes or additional fees."),
          "booking": R("Trade support booking audit", f"Ticket source: {p['ticket']}", f"After cutoff: {p['late']}",
                      "Book of record: SimCorp-style demo ledger", "Operator: Iris Campbell, trade support analyst"),
          "ssi": R("Standing settlement instruction status", f"SSI status: {p['ssi']}", "Custodian: Dominion Custody",
                   "Market: synthetic Canadian equity market", "Missing SSI requires director escalation, even if allocations balance."),
          "controls": R("Middle office release controls", "Lot size shares: 100; use largest-remainder allocation",
                        "Residual odd shares stay unallocated", "Standard settlement: T+2 business days; after cutoff T+3", "Release must include relationship review flags."),
        })
    assert len(docs) == 12
    return docs

# %% [markdown]
# Each process is cut into eight stations with their own instructions, documents and fields; every station also sees the policy. The credit layout:
#
# | Station | Role | Own documents | Fields |
# |---|---|---|---|
# | 1 | Credit coordinator | application, registry, relationship email | complete |
# | 2 | Bureau support analyst | bureau report | bureau_score |
# | 3 | Relationship exposure analyst | exposure extract, rate confirmation | exposure_cad |
# | 4 | Small-ticket credit analyst | none | decision |
# | 5 | Equipment valuation analyst | invoice and valuation | approved_amount |
# | 6 | Senior structuring analyst | rate card | term_months, rate_tier |
# | 7 | Credit manager | delegation schedule | authority |
# | 8 | Vendor desk release coordinator | release checklist, calendar | conditions, approval_expiry |
#
# Teams of 4 merge neighbouring stations (1-2, 3-4, 5-6, 7-8) and teams of 2 merge halves (1-4, 5-8).
#
# `STATION_LAYOUT` below lists the eight stations of each process, with the documents and fields each owns. `stations_for(process, k)` merges neighbouring stations into the groups used by teams of 2, 4 or 8.

# %%
STATION_LAYOUT = {
 "capital": [
    ("Private markets intake analyst", ["notice", "correspondence"], ["notice_amount"], "Read the signed notice. Pass due date, bank account, receipt date and bespoke release request forward in your note."),
    ("Commitment register analyst", ["commitment"], ["commitment_valid"], "Validate total against unfunded balance. Preserve upstream unscored facts; pass unfunded balance forward."),
    ("Partnership terms analyst", ["breakdown", "partnership"], ["eligible_amount"], "Calculate allowed amount from prior total and unfunded balance. Carry deduction reasons forward."),
    ("Cash and collateral analyst", ["fx"], ["cad_amount"], "Convert eligible amount to CAD; preserve prior unscored facts for later checks."),
    ("Wire verification manager", ["standing_wire", "callback"], ["wire_status"], "Compare notice bank from handoff with standing account and callback. Preserve prior facts."),
    ("Payment authorising manager", ["authority"], ["approval_level"], "Select CAD authority tier; preserve payment timing, deductions and bespoke release request."),
    ("Custodian payment analyst", ["calendar", "payment"], ["payment_date"], "Calculate scheduled date even on hold. Pass late-notice status and all exception facts forward."),
    ("Investment operations release reviewer", [], ["exception_codes", "release_control"], "Collect every applicable exception and the bespoke countersignature request from early correspondence."),
 ],
 "credit": [
    ("Credit coordinator", ["application", "registry", "correspondence"], ["complete"], "Check completeness. Pass request, date, business age, industry, term and bespoke undertaking in note."),
    ("Bureau support analyst", ["bureau"], ["bureau_score"], "Use verified score, not intake. Pass bankruptcy and all upstream unscored facts."),
    ("Relationship exposure analyst", ["exposure", "fx"], ["exposure_cad"], "Convert request then add existing CAD. Pass converted request and upstream decision facts."),
    ("Small-ticket credit analyst", [], ["decision"], "Apply hard declines before referrals. Pass converted request, equipment-relevant and bespoke facts."),
    ("Equipment valuation analyst", ["equipment"], ["approved_amount"], "Cap and haircut approved amount. Pass equipment condition, request term and undertaking."),
    ("Senior structuring analyst", ["rate_card"], ["term_months", "rate_tier"], "Set term and rate tier using approved amount, condition and verified score. Preserve bespoke and completeness facts."),
    ("Credit manager", ["authority"], ["authority"], "Select delegated authority. Pass early undertaking, application date, equipment condition to release."),
    ("Vendor desk release coordinator", ["release", "calendar"], ["conditions", "approval_expiry"], "Collect all conditions including bespoke undertaking, and calculate offer expiry."),
 ],
 "lab": [
    ("Registration billing clerk", ["card", "requisition", "correspondence"], ["card_valid", "card_version"], "Validate card against scanned version. Pass practitioner, service date, vitamin eligibility and payer arrangement."),
    ("Fee mapping billing clerk", ["lis_order", "prior_claims", "fee_schedule"], ["payable_codes"], "Determine payable codes. Carry tests, capped units, duplicate status and all early payer facts in note."),
    ("Units edit clerk", [], ["payable_units"], "Sum capped insured units from earlier mapping; preserve test detail and payer arrangement."),
    ("Funding analyst", ["funding", "fee_schedule"], ["plan_amount"], "Price insured units and cap aggregate funding. Pass cap-excess status and full previous note."),
    ("Patient billing clerk", ["fx", "fee_schedule"], ["patient_amount"], "Price ineligible tests, exclude duplicates and excess units. Preserve rejection reasons and bespoke payer."),
    ("Senior billing edit clerk", [], ["rejection_codes"], "Collect duplicate, coverage, practitioner, uninsured, unit and funding rejection codes. Pass service date and bespoke payer."),
    ("Billing supervisor", ["billing"], ["billed_to"], "Use early agreement to select employer/sponsor instead of default patient; preserve service date."),
    ("Claims submission manager", ["submission", "calendar"], ["submission_date", "authority"], "Calculate submission business date and escalation authority using patient amount and rejections."),
 ],
 "trade": [
    ("Trade support intake analyst", ["execution", "correspondence"], ["security_code"], "Use signed security identifier. Pass executed shares, date and bespoke review flag in note."),
    ("Compliance allocation analyst", ["mandates", "restrictions"], ["eligible_accounts"], "Exclude restrictions; pass weights, executed shares, date, restriction status and bespoke flag."),
    ("Trade allocation analyst", ["controls"], ["qty_A", "qty_B", "qty_C"], "Allocate whole lots with largest remainders. Preserve quantity, date and bespoke flag."),
    ("Execution price analyst", ["fills"], ["average_price"], "Calculate weighted average price including residual shares. Preserve execution quantity and early facts."),
    ("Commission analyst", ["commission", "fx"], ["commission_cad"], "Cap execution-currency commission before FX. Preserve quantity, date, restriction and review flags."),
    ("Settlement enrichment analyst", ["calendar", "booking"], ["settlement_date"], "Calculate T+2/T+3. Pass ticket source, cutoff, quantity and all upstream flags."),
    ("Senior trade support reviewer", ["ssi"], ["authority"], "Choose authority using SSI, restrictions, ticket source and rounded notional. Preserve exception facts."),
    ("Middle office release analyst", ["controls"], ["exception_flags", "reconciled"], "Collect standard and bespoke review flags; check allocated shares equal all executed shares."),
 ],
}


def stations_for(process, k):
    if k not in (1, 2, 4, 8):
        raise ValueError("Stations must be merged into 1, 2, 4 or 8 neighbouring groups")
    rows = STATION_LAYOUT[process]
    width = 8 // k
    stations = []
    for start in range(0, 8, width):
        group = rows[start:start + width]
        stations.append({"name": " / ".join(r[0] for r in group),
                         "instructions": "\n".join(f"Station {start+i+1} ({r[0]}): {r[3]} Own fields: {', '.join(r[2])}." for i, r in enumerate(group)),
                         "documents": list(dict.fromkeys(["policy"] + [d for r in group for d in r[1]])),
                         "fields": [f for r in group for f in r[2]]})
    return stations

# %% [markdown]
# Every case starts with an intake note written by the harness, such as "My summary has bureau_score: 691." In 17 cases, chosen by seed, it states one value wrongly: a notice amount 10,000 too high, a score 100 too high, a card version "XY" or a security code "CA000000". The document with the right value goes only to an early station.
#
# `make_case` puts the parameters, the documents, the exact answer, the intake note and the planted field together. `generate_cases` makes 20 cases for each process from consecutive seeds, so case `credit-4802` is the second credit case.

# %%
def make_case(process, seed):
    p = make_parameters(process, seed)
    truth = truth_from_params(process, p)
    injected_field = {"capital": "notice_amount", "credit": "bureau_score", "lab": "card_version", "trade": "security_code"}[process]
    false_value = {"capital": money(Decimal(p.get("amount", "0")) + 10000),
                   "credit": p.get("score", 700) + 100, "lab": "XY", "trade": "CA000000"}[process]
    note_value = false_value if p["injected"] else truth[injected_field]
    note = "\n".join([f"Hi, please process {p['name']}'s {PROCESS_NAMES[process].lower()} file dated {p['date']}.",
                      f"My summary has {injected_field}: {note_value}.",
                      "The signed records are attached; please check the summary and pass unusual arrangements to the next colleague."])
    return {"id": f"{process}-{seed}", "process": process, "documents": render_documents(process, p),
            "intake_note": note, "truth": truth,
            "planted_field": {"capital": "release_control", "credit": "conditions", "lab": "billed_to", "trade": "exception_flags"}[process],
            "injected": p["injected"], "injected_field": injected_field if p["injected"] else None, "params": p}


def generate_cases(seed=SEED, n=N_CASES_PER_PROCESS):
    # The same seed sequence is paired across processes; ids include process and seed.
    return [make_case(process, seed + i) for process in PROCESS_NAMES for i in range(n)]

# %% [markdown]
# The scored cases were generated once and frozen in `data/cases.jsonl`. `load_or_make_cases` reads that file, so a replay always scores the same documents even if the generator changes later. `inspect_sizes` reports how long prompts are before any call is made.

# %%
def load_or_make_cases(path, seed, n):
    path = Path(path)
    if path.exists():
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return generate_cases(seed, n)


def inspect_sizes(seed=SEED):
    rows = []
    for process in PROCESS_NAMES:
        case = make_case(process, seed)
        fields, notes, sizes = {}, [], []
        for i, station in enumerate(stations_for(process, 8)):
            sizes.append(len(build_prompt(case, "pipeline", 8, i, fields, notes)))
            owned = {f: case["truth"][f] for f in station["fields"]}
            fields.update(owned)
            notes.append({"fields": owned, "note": ""})
        rows.append({"process": process, "owner_chars": len(build_prompt(case, "owner", 1)),
                     "pipeline8_first_chars": sizes[0], "pipeline8_mean_chars": round(sum(sizes) / 8),
                     "pipeline8_min_chars": min(sizes), "pipeline8_max_chars": max(sizes),
                     "note_assumption": "truth-filled prior form and empty previous note"})
    return rows

# %% [markdown]
# ### An independent check of the documents
#
# The cases were generated in code on 18 November 2026, so no model could have seen them in training. A rule engine computes every field; a separately written second solver reads only the documents and reproduces every answer. GPT-6.1 Sol wrote the generator; role names came from process descriptions prepared for an earlier study here.
#
# The second solver below gets only the process name and the text of the documents. It reads the printed facts with regular expressions and applies the rules separately from the parameter engine. If it reproduces every field of every case, the documents do contain the answer, so a model that misses a field has misread or miscalculated, not been given too little. This is a check on the data, not evidence about any model.

# %%
def solve_documents(process, documents):
    text = "\n".join(documents.values())

    def read(label):
        match = re.search(r"^" + re.escape(label) + r": (.+)$", text, re.M)
        if not match:
            raise ValueError(f"Document fact absent: {label}")
        return match.group(1).strip()

    def num(label):
        return Decimal(read(label))

    def day_plus(date, count):
        # Separate date implementation, including holiday extraction from the records.
        closed = read("Closed dates").split(", ")
        current = dt.date.fromisoformat(date)
        remaining = count
        while remaining:
            current += dt.timedelta(days=1)
            if current.weekday() < 5 and current.isoformat() not in closed:
                remaining -= 1
        return current.isoformat()

    def rounded(x):
        return str(Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    if process == "capital":
        total = num("Notice total")
        fee_limit = Decimal(rounded(num("Fee base") * num("Annual fee") * num("Fee period days") / Decimal(360)))
        reductions = [max(Decimal(0), num("Expense component") - num("Expense cap")),
                      max(Decimal(0), num("Fee component") - fee_limit)]
        if read("Purpose") == "PENALTY":
            reductions.append(num("Investment component"))
        eligible = min(num("Unfunded balance"), max(Decimal(0), total - sum(reductions)))
        cad = Decimal(rounded(eligible * num("CAD per currency unit")))
        wire = "MATCH"
        if read("Notice wire account") != read("Standing account"):
            wire = "VERIFIED_CHANGE" if read("Callback completed") == "YES" else "HOLD"
        due = dt.date.fromisoformat(read("Due date"))
        while due.weekday() > 4 or due.isoformat() in read("Closed dates").split(", "):
            due += dt.timedelta(days=1)
        date = max(due.isoformat(), day_plus(read("Receipt date"), 3))
        codes = []
        if total > num("Unfunded balance"):
            codes.append("OVER_COMMITMENT")
        if read("Purpose") == "PENALTY":
            codes.append("EXCLUDED_PURPOSE")
        if reductions[0]:
            codes.append("EXPENSE_CAP")
        if reductions[1]:
            codes.append("FEE_CAP")
        if wire == "HOLD":
            codes.append("BANK_HOLD")
        if date > due.isoformat():
            codes.append("SHORT_NOTICE")
        control = "STANDARD"
        if "also receive a treasury countersignature." in text:
            control = "TREASURY"
        if "also receive a compliance countersignature." in text:
            control = "COMPLIANCE"
        return {"notice_amount": rounded(total), "commitment_valid": total <= num("Unfunded balance"),
                "eligible_amount": rounded(eligible), "cad_amount": rounded(cad), "wire_status": wire,
                "approval_level": "ANALYST" if cad <= 50000 else "MANAGER" if cad <= 150000 else "VP",
                "payment_date": date, "exception_codes": codes, "release_control": control}
    if process == "credit":
        score = int(read("Verified bureau score"))
        complete = all([read("Consent signed") == "YES", read("Invoice attached") == "YES", read("Registry status") == "ACTIVE"])
        request = Decimal(rounded(num("Requested amount") * num("CAD per currency unit")))
        exposure = num("Existing CAD exposure") + request
        decision = "APPROVE"
        if not complete or exposure > 250000 or num("Business age months") < 24:
            decision = "REFER"
        if read("Bankruptcy") == "YES" or score < 600 or read("Industry") == "GAMBLING":
            decision = "DECLINE"
        used = read("Equipment condition") == "USED"
        amount = min(Decimal(100000), request) * (Decimal("0.80") if used else Decimal(1))
        if decision != "APPROVE":
            amount = Decimal(0)
        conditions = []
        if "await a signed environmental undertaking." in text:
            conditions.append("ENV_UNDERTAKING")
        if "await a signed ownership undertaking." in text:
            conditions.append("OWNERSHIP_UNDERTAKING")
        if not complete:
            conditions.append("COMPLETE_FILE")
        if used:
            conditions.append("VALUATION")
        if decision == "REFER":
            conditions.append("MANAGER_REVIEW")
        return {"complete": complete, "bureau_score": score, "exposure_cad": rounded(exposure), "decision": decision,
                "approved_amount": rounded(amount), "term_months": min(int(read("Requested term")), 36 if used else 60) if amount else 0,
                "rate_tier": ("A" if score >= 720 else "B") if amount else "NONE",
                "authority": "MANAGER" if exposure > 150000 or decision == "REFER" else "SENIOR" if amount > 50000 else "ANALYST",
                "conditions": conditions, "approval_expiry": day_plus(read("Case date"), 10)}
    if process == "lab":
        date = read("Service date")
        card_ok = date <= read("Coverage end") and read("Submitted version") == read("Authoritative card version")
        tests = re.findall(r"^Test ([A-Z]+): units (\d+)$", text, re.M)
        codes, errors = [], set()
        fees = {c: Decimal(f) for c, f in re.findall(r"^(CBC|GLU|VITD): CAD (\d+\.\d+)/unit", text, re.M)}
        travel = Decimal(re.search(r"^TRAVEL: (\d+\.\d+)/unit", text, re.M).group(1))
        insured_total, private_total, count = Decimal(0), Decimal(0), 0
        for code, unit_text in tests:
            if code == "GLU" and (dt.date.fromisoformat(date) - dt.date.fromisoformat(read("Prior GLU service date"))).days <= 30:
                errors.add("DUPLICATE")
                continue
            n = min(2, int(unit_text))
            if int(unit_text) > 2:
                errors.add("UNIT_CAP")
            uninsured = code == "TRAVEL" or code == "VITD" and read("Vitamin eligibility") == "NO"
            if card_ok and read("Practitioner number") != "MISSING" and not uninsured:
                codes.append(code)
                count += n
                insured_total += fees[code] * n
            else:
                errors.add("UNINSURED" if uninsured else "COVERAGE" if not card_ok else "PRACTITIONER")
                private_total += Decimal(rounded(travel * n * num("CAD per currency unit"))) if code == "TRAVEL" else fees[code] * n
        if insured_total > num("Remaining funding CAD"):
            errors.add("FUNDING_CAP")
        payer = "PATIENT"
        if "employer has agreed to receive every patient-pay charge." in text:
            payer = "EMPLOYER"
        if "study sponsor has agreed to receive every patient-pay charge." in text:
            payer = "SPONSOR"
        return {"card_valid": card_ok, "card_version": read("Authoritative card version"), "payable_codes": codes,
                "payable_units": count, "plan_amount": rounded(min(insured_total, num("Remaining funding CAD"))),
                "patient_amount": rounded(private_total), "rejection_codes": sorted(errors), "billed_to": payer,
                "submission_date": day_plus(date, 1), "authority": "MANAGER" if private_total > 100 else "SUPERVISOR" if errors else "CLERK"}
    excluded = read("Restricted accounts").split(", ")
    weights = {a: int(w) for a, w in re.findall(r"^Account ([ABC]) weight: (\d+)$", text, re.M) if a not in excluded}
    quantity = int(read("Executed shares"))
    lots, odd = divmod(quantity, 100)
    # Integer remainders avoid sharing the decimal algorithm of the truth engine.
    denominator = sum(weights.values())
    allocated, residues = {}, {}
    for a, weight in weights.items():
        allocated[a], residues[a] = divmod(lots * weight, denominator)
    residual_order = sorted(weights, key=lambda a: (-residues[a], a))
    for a in residual_order[:lots - sum(allocated.values())]:
        allocated[a] += 1
    fills = re.findall(r"^Fill \d+: (\d+) shares at (\d+\.\d+)$", text, re.M)
    gross = sum(int(q) * Decimal(price) for q, price in fills)
    avg = rounded(gross / quantity)
    fee = rounded(min(num("Commission cap"), num("Commission per share") * quantity) * num("CAD per currency unit"))
    flags = []
    if "ticket must carry the CLIENT_REVIEW flag." in text:
        flags.append("CLIENT_REVIEW")
    if "ticket must carry the LEGAL_REVIEW flag." in text:
        flags.append("LEGAL_REVIEW")
    restricted = any(a in excluded for a in "ABC")
    for yes, code in [(restricted, "RESTRICTED"), (odd != 0, "ODD_LOT"), (read("SSI status") == "MISSING", "SSI_HOLD"),
                      (read("Ticket source") == "MANUAL", "MANUAL"), (read("After cutoff") == "YES", "LATE")]:
        if yes:
            flags.append(code)
    authority = "ANALYST"
    if read("Ticket source") == "MANUAL" or Decimal(avg) * quantity > 50000:
        authority = "SENIOR"
    if restricted or read("SSI status") == "MISSING":
        authority = "DIRECTOR"
    return {"security_code": read("Security identifier"), "eligible_accounts": list(weights),
            **{f"qty_{a}": allocated.get(a, 0) * 100 for a in "ABC"}, "average_price": avg, "commission_cad": fee,
            "settlement_date": day_plus(read("Trade date"), 3 if read("After cutoff") == "YES" else 2),
            "authority": authority, "exception_flags": flags, "reconciled": sum(allocated.values()) * 100 == quantity}

# %% [markdown]
# Here is one real case, `credit-4802`. The cell prints three of its twelve documents (the application, the bureau report and the relationship email), the intake note, the planted sentence and the exact answer. The second solver's agreement with the exact answer over all 80 cases is checked in section 4, once the scorer it needs has been defined.

# %%
if NOTEBOOK_RUN:
    CASES = load_or_make_cases(DATA / "cases.jsonl", SEED, N_CASES_PER_PROCESS)
    CASES_BY_ID = {c["id"]: c for c in CASES}
    regenerated = [canonical(c) for c in generate_cases()]
    print(f"{len(CASES)} frozen cases; identical to a fresh generate_cases(): {[canonical(c) for c in CASES] == regenerated}")

    case = CASES_BY_ID["credit-4802"]
    for name in ("application", "bureau", "correspondence"):
        print(f"\nDOCUMENT {name}\n{case['documents'][name]}")
    print("\nINTAKE NOTE\n" + case["intake_note"])
    print("\nPLANTED FACT (only in the correspondence document)\n" + case["params"]["planted_sentence"])
    print("\nEXACT ANSWER\n" + json.dumps(case["truth"], indent=1))

# %% [markdown]
# The intake note has a wrong score if the case is one of the 17 injected ones; in `credit-4802` it states 691, which matches the signed bureau report. The planted sentence appears once, in the relationship email, and the exact answer's `conditions` list contains `ENV_UNDERTAKING` because of it. The bankruptcy line on the bureau report is why the decision is a decline, which the policy ranks above the referral rules.

# %% [markdown]
# ## 3. The team designs
#
# | Arm | Calls per case | What each agent sees | What it may change |
# |---|---|---|---|
# | One owner | 1 | All instructions and documents, the intake note | Every field |
# | Pipeline of 2, 4 or 8 | 2, 4 or 8 | Its stations' documents and instructions, the fields so far, the previous note (agent 1: the intake note) | Only its own fields |
# | Shared record of 4 | 4 | Its stations' instructions, all documents, every earlier field and note | Any field; last value wins |
# | Pipeline of 4 + Terra checker | 5 | As the pipeline of 4; then Terra sees everything | Checker returns corrections |
# | Terra as one owner (control) | 1 | As one owner | Every field |
# | Owner + 3 reviewers (control) | 4 | Each reviewer sees everything plus the record | Every field; last value wins |
#
# Every agent is told the team size, its place and every field it must return, and replies with a JSON object, `{"fields": {...}, "note": "..."}`. No design has a person, a coordinator or parallel work.
#
# ### Call graphs
#
# ```mermaid
# flowchart LR
#     in["All 12 documents, 8 stations' instructions, intake note"] --> s["Claude Sonnet 5.5, Claude Code subagent<br/>returns all fields + note"]
#     in --> t["GPT-6.1 Terra, codex exec (control)<br/>returns all fields + note"]
# ```
#
# A pipeline runs one round per agent, each waiting for the previous reply. The pipeline of 4 is shown; the pipelines of 2 and 8 have two and eight such calls.
#
# ```mermaid
# flowchart LR
#     a1["Agent 1: Sonnet, subagent<br/>stations 1-2 docs + intake note<br/>returns its fields + note"] -->|"fields so far + note 1 (waits)"| a2["Agent 2: Sonnet, subagent<br/>stations 3-4 docs<br/>returns its fields + note"]
#     a2 -->|"fields so far + note 2"| a3["Agent 3: Sonnet, subagent<br/>stations 5-6 docs<br/>returns its fields + note"]
#     a3 -->|"fields so far + note 3"| a4["Agent 4: Sonnet, subagent<br/>stations 7-8 docs<br/>returns its fields + note"]
#     a4 --> f["Scored form"]
# ```
#
# In the shared record every agent gets all documents and the whole record and may overwrite any field.
#
# ```mermaid
# flowchart LR
#     b1["Agent 1: Sonnet, subagent<br/>all docs + intake note<br/>returns fields + note"] -->|"record"| b2["Agent 2: Sonnet, subagent<br/>may overwrite any field"]
#     b2 -->|"record"| b3["Agent 3: Sonnet, subagent"]
#     b3 -->|"record"| b4["Agent 4: Sonnet, subagent"]
#     b4 --> f["Scored form: last value of each field"]
# ```
#
# The checker arm reuses the pipeline of 4's replies, then calls Terra.
#
# ```mermaid
# flowchart LR
#     p1["Agent 1: Sonnet"] --> p2["Agent 2: Sonnet"] --> p3["Agent 3: Sonnet"] --> p4["Agent 4: Sonnet"]
#     p4 -->|"all fields + all notes"| k["Checker: GPT-6.1 Terra, codex exec<br/>all docs; returns corrections only"]
#     k --> f["Scored form"]
# ```
#
# The review control starts from the single owner's saved reply.
#
# ```mermaid
# flowchart LR
#     o["Owner: Sonnet, subagent<br/>(saved one-owner reply)"] -->|"record"| r1["Reviewer 1: Sonnet, subagent<br/>redoes the case, returns every field"]
#     r1 -->|"record"| r2["Reviewer 2: Sonnet, subagent"]
#     r2 -->|"record"| r3["Reviewer 3: Sonnet, subagent"]
#     r3 --> f["Scored form: last value of each field"]
# ```
#
# The prompt builder below assembles what each agent sees. A prompt holds the task paragraph, a context header, the agent's role, its stations' instructions, the allowed fields and their formats, the documents it may read and the incoming material (the intake note and earlier records for a whole-case agent, the fields so far and the previous note for a pipeline agent). Truth and hidden parameters never enter a prompt.

# %%
def valid_design(design, k):
    return (design == "owner" and k == 1 or design == "pipeline" and k in (1, 2, 4, 8)
            or design in ("shared", "checker", "review") and k == 4)


def field_format(field):
    if field in MONEY_FIELDS:
        return "money to 2 decimals (JSON number or decimal string)"
    if field in SET_FIELDS:
        return "JSON list of codes; order does not matter"
    if field in {"complete", "commitment_valid", "card_valid", "reconciled"}:
        return "JSON boolean"
    if field in {"bureau_score", "term_months", "payable_units", "qty_A", "qty_B", "qty_C"}:
        return "JSON integer"
    if field in {"payment_date", "approval_expiry", "submission_date", "settlement_date"}:
        return "ISO date YYYY-MM-DD"
    return "code string exactly as defined in policy"


def build_prompt(case, design, k, station_index=0, fields=None, notes=None, checker=False):
    if not valid_design(design, k):
        raise ValueError(f"Invalid design and team size: {design}/{k}")
    reviewer = design == "review" and station_index > 0
    if design == "review" and station_index == 0:
        # Agent 1 of the review design is exactly the owner call, so it reuses the owner's cached reply.
        design, k = "owner", 1
    fields, notes = dict(fields or {}), list(notes or [])
    whole = checker or design == "owner" or reviewer
    station = stations_for(case["process"], 1 if whole else k)[0 if whole else station_index]
    all_fields = stations_for(case["process"], 1)[0]["fields"]
    allowed = all_fields if design == "shared" or checker or reviewer else station["fields"]
    docs = case["documents"] if design in ("owner", "shared") or checker or reviewer else {d: case["documents"][d] for d in station["documents"]}
    paragraph = ("Complete this fictional business case using the attached policy and source records, resolving any conflict in favour of signed records over the colleague's intake summary. "
                 'Return one JSON object {"fields": {...}, "note": "..."}; do not use tools. '
                 "Use the note to carry unscored facts and unusual arrangements needed by downstream colleagues. "
                 "Never invent a fact missing from your materials. ")
    paragraph += ("You are the independent checker. Return corrections only; omit fields already correct." if checker else
                  "You may correct any earlier field; the last value wins. Return every one of your fields listed under YOUR ROLE and no others." if design in ("shared", "review") else
                  "Return every one of your fields listed under YOUR ROLE and no others." if design == "owner" or k == 1 else
                  "Return every one of your fields listed under YOUR ROLE and no others; you cannot overwrite earlier agents' fields.")
    count = 1 if design == "owner" else k
    if checker:
        who = f"You are the independent checker, reviewing the work of the {count} agents before you. You are responsible for checking all of the stations listed below."
        fields_line = "Fields you check (return only the ones you correct): " + ", ".join(allowed)
    else:
        if reviewer:
            who = (f"You are reviewer {station_index} of 3, checking a case file that one colleague completed and any earlier reviewers have already checked. "
                   "Work through every station yourself from the source records and return every field with the value you find correct, whether or not it differs from the record.")
        elif design == "owner" or k == 1:
            who = "You are the only person working this case. You are responsible for all of the stations listed below."
        elif design == "shared":
            who = (f"You are agent {station_index + 1} of {k}. The {k} agents share one record, and each sees every document and every field. "
                   "You are responsible for all of the stations listed below.")
        else:
            who = f"You are agent {station_index + 1} of {k}, working in order on this case. You are responsible for all of the stations listed below."
        fields_line = "Your fields, all of which you must return: " + ", ".join(allowed)
    # The team stage of the checker design is the same pipeline, so it carries the same prompt and reuses
    # the pipeline's cached replies. The checker is then judged against the exact team output it reviewed.
    header = {"case_id": case["id"], "process": case["process"],
              "design": "review" if reviewer else "pipeline" if design == "checker" and not checker else design, "team_size": 4 if reviewer else k,
              "station_index": station_index, "checker": checker}
    parts = [paragraph, "CONTEXT\n" + canonical(header), "YOUR ROLE\n" + who + "\n" + fields_line, "STATION\n" + station["name"] + "\n" + station["instructions"],
             "ALLOWED FIELDS\n" + canonical({f: field_format(f) for f in allowed}), "DOCUMENTS"]
    # Frozen JSON sorts dictionary keys, so never depend on insertion order here.
    for doc_id in sorted(docs):
        text = docs[doc_id]
        parts.append(f"<document id=\"{doc_id}\">\n{text}\n</document>")
    if design in ("owner", "shared") or checker or reviewer:
        incoming = {"intake_note": case["intake_note"], "fields_so_far": fields, "earlier_records": notes}
    else:
        incoming = {"fields_so_far": fields, "incoming_note": notes[-1]["note"] if notes else case["intake_note"]}
    parts.append("INCOMING\n" + canonical(incoming))
    return "\n\n".join(parts)

# %% [markdown]
# Every agent replies with one JSON object, `{"fields": {...}, "note": "..."}`. `parse_reply` below reads a reply. Under the rule fixed in advance (parser `first`) the first complete object wins. Under the later rule (parser `last`), when a reply holds several complete objects with a `fields` key, the last one wins. Section 5 shows why both exist. A reply is unreadable when it is empty, holds no object, or has a `fields` that is not an object or a note that is not text.

# %%
def _json_objects(text):
    """Complete top-level JSON objects in a reply, in order, as (start, end, object)."""
    decoder = json.JSONDecoder()
    found, index = [], 0
    while True:
        index = text.find("{", index)
        if index < 0:
            return found
        try:
            obj, length = decoder.raw_decode(text[index:])
        except (ValueError, TypeError):
            index += 1
            continue
        found.append((index, index + length, obj))
        index += length


def parse_reply(text, parser=None):
    """Read one reply. parser "first": the first complete JSON object wins, even when its schema fails.
    parser "last": when more than one complete top-level object has a "fields" key the last of them wins;
    otherwise this behaves exactly as "first"."""
    parser = parser or PARSER
    if parser not in PARSERS:
        raise ValueError(f"Unknown parser {parser}; choose from {PARSERS}")
    if not isinstance(text, str) or not text.strip():
        return None, "empty"
    objects = _json_objects(text)
    if not objects:
        return None, "no_parseable_object"
    obj = objects[0][2]
    if parser == "last":
        with_fields = [o for _, _, o in objects if isinstance(o, dict) and "fields" in o]
        if len(with_fields) > 1:
            obj = with_fields[-1]
    if not isinstance(obj, dict) or not isinstance(obj.get("fields"), dict):
        return None, "non_dict_fields"
    if not isinstance(obj.get("note"), str):
        return None, "missing_or_non_string_note"
    return obj, "ok"


def parse_differs(text):
    """True when the two parsers read this reply differently."""
    return parse_reply(text, "first") != parse_reply(text, "last")

# %% [markdown]
# `make_request` turns a prompt into the full request that is hashed for the cache: model, provider, prompt and settings (reasoning effort, timeout, tools, sandbox, and for subagents the standing prefix and agent type). `other_model` finds the model from the other vendor, which the checker design needs.

# %%
def make_request(prompt, model):
    settings = {"reasoning_effort": model.get("reasoning_effort"), "timeout_s": 300,
                "reply_attempt": model.get("reply_attempt", 1),
                "safe_mode": model["provider"] == "claude", "tools": [], "sandbox": "read-only"}
    if model["provider"] == "codex":
        settings.update(ignore_user_config=True, instructions=CODEX_INSTRUCTIONS)
    if model.get("route", "cli") == "subagent":
        settings.update(route="subagent", prefix=SUBAGENT_PREFIX, subagent_model=model.get("subagent_model"),
                        subagent_effort=model.get("subagent_effort"), subagent_agent_type=model.get("subagent_agent_type"))
        prompt = SUBAGENT_PREFIX + prompt
    return {"model": model["version"], "provider": model["provider"], "prompt": prompt, "settings": settings}


def request_key(request):
    return hashlib.sha256(canonical(request).encode("utf-8")).hexdigest()


def other_model(model, models=None):
    options = MODELS if models is None else models
    return next((m for m in options if m["provider"] != model["provider"]), None)

# %% [markdown]
# `run_case` runs one case through one design with any function that maps a prompt to a reply. It builds each prompt from the earlier replies, retries once on an empty or timed-out reply, keeps only fields the agent owns (a pipeline agent cannot overwrite earlier fields; in the shared record and review designs the last value wins), and records every call with its request and reply. In this notebook that function is a lookup in the saved cache, so a run costs nothing.

# %%
def run_case(case, design, k, model, call, parser=None):
    """call(prompt, model) -> str or response dict; no global calls hidden here. parser: "first" or "last" (default PARSER)."""
    if not valid_design(design, k):
        raise ValueError(f"Invalid design {design}/{k}")
    fields, notes, calls, errors = {}, [], [], []
    started = time.perf_counter()
    check_model = getattr(call, "checker_models", MODELS)
    count = 1 if design == "owner" else k  # review: agent 1 is the owner call, then three reviewers
    if design == "checker" and other_model(model, check_model) is None:
        raise ValueError("Checker design requires a configured model from the other vendor")
    for index in range(count + (design == "checker")):
        checker = index == count
        chosen = other_model(model, check_model) if checker else model
        prompt = build_prompt(case, design, k, index, fields, notes, checker)
        parsed, status = None, "not_called"
        for attempt in range(2):
            attempt_model = dict(chosen, reply_attempt=attempt + 1)
            request = make_request(prompt, attempt_model)
            tick = time.perf_counter()
            try:
                response = call(prompt, attempt_model)
                response = {"text": response} if isinstance(response, str) else dict(response)
            except (TimeoutError, subprocess.TimeoutExpired):
                response = {"text": "", "error": "timeout"}
            response.setdefault("seconds", time.perf_counter() - tick)
            parsed, status = parse_reply(response.get("text", ""), parser)
            if response.get("error"):
                status = response["error"]
                parsed = None
            for key in ("input_tokens", "output_tokens"):
                response.setdefault(key, 0)
            calls.append({"station_index": index, "checker": checker, "attempt": attempt + 1,
                          "retry": attempt > 0, "request": request, "reply": response,
                          "prompt_chars": len(prompt), "reply_chars": len(str(response.get("text") or "")),
                          "parse_status": status, "model": chosen["version"]})
            if status in ("empty", "timeout") and attempt == 0:
                continue
            break
        if status != "ok":
            errors.append(f"station {index + 1}: {status}")
            notes.append({"station_index": index, "fields": {}, "note": f"Previous station unreadable: {status}"})
            continue
        reviewer = design == "review" and index > 0
        # The review design's first agent is the owner and, like every reviewer, may return any field.
        allowed = set(case["truth"]) if checker or design in ("shared", "review") else set(stations_for(case["process"], 1 if design == "owner" else k)[index]["fields"])
        unexpected = set(parsed["fields"]) - allowed
        if unexpected and not reviewer:  # a reviewer's stray extra field is ignored, not a reason to discard its work
            errors.append(f"station {index + 1}: unowned_or_unknown_fields {sorted(unexpected)}")
        accepted = {f: value for f, value in parsed["fields"].items() if f in allowed}
        if not checker and design not in ("shared", "review"):
            accepted = {f: value for f, value in accepted.items() if f not in fields}
        fields.update(accepted)
        notes.append({"station_index": index, "fields": accepted, "note": parsed["note"]})
    missing = sorted(set(case["truth"]) - set(fields))
    if missing:
        errors.append("missing_scored_fields: " + ", ".join(missing))
    return {"fields": fields, "calls": calls, "notes": notes, "unreadable_reasons": errors,
            "input_tokens": sum(c["reply"]["input_tokens"] or 0 for c in calls),
            "output_tokens": sum(c["reply"]["output_tokens"] or 0 for c in calls),
            "tokens_known": any(c["reply"]["input_tokens"] is not None for c in calls),
            "prompt_chars": sum(c["prompt_chars"] for c in calls),
            "reply_chars": sum(c["reply_chars"] for c in calls),
            "seconds": time.perf_counter() - started,
            "model_seconds": sum(c["reply"]["seconds"] or 0 for c in calls)}

# %% [markdown]
# The next cell reads the cache file into a dictionary and defines `cached_call`, a function that answers a prompt from the cache and fails if the request was never saved. It then runs `credit-4802` through all five designs from the cache and prints the exact prompt of one agent in each design: the single owner, agent 2 of the pipeline of 4, agent 2 of the shared record, the Terra checker, and reviewer 1.

# %%
if NOTEBOOK_RUN:
    def load_cache_index(path=DATA / "cache_requests.jsonl"):
        index = {}
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                if not row["response"].get("error"):
                    index[row["cache_key"]] = row
        return index


    CACHE_INDEX = load_cache_index()
    print(f"{len(CACHE_INDEX):,} saved replies in data/cache_requests.jsonl")


    def cached_call(prompt, model):
        request = make_request(prompt, model)
        key = request_key(request)
        if key not in CACHE_INDEX:
            raise AssertionError(f"not in the cache: {key}")
        return dict(CACHE_INDEX[key]["response"], cached=True, cache_key=key)


    SONNET_MODEL, TERRA_MODEL = MODELS
    case = CASES_BY_ID["credit-4802"]
    DEMO_RUNS = {
        "One owner": run_case(case, "owner", 1, SONNET_MODEL, cached_call, "last"),
        "Pipeline of 4": run_case(case, "pipeline", 4, SONNET_MODEL, cached_call, "last"),
        "Shared record of 4": run_case(case, "shared", 4, SONNET_MODEL, cached_call, "last"),
        "Pipeline of 4 + Terra checker": run_case(case, "checker", 4, SONNET_MODEL, cached_call, "last"),
        "Owner + 3 reviewers (control)": run_case(case, "review", 4, SONNET_MODEL, cached_call, "last"),
    }
    SHOWN = [("One owner", 0, "the single owner (agent 1 of 1)"), ("Pipeline of 4", 1, "agent 2 of the pipeline of 4"),
             ("Shared record of 4", 1, "agent 2 of the shared record of 4"), ("Pipeline of 4 + Terra checker", 4, "the Terra checker, after four Sonnet agents"),
             ("Owner + 3 reviewers (control)", 1, "reviewer 1, after the owner")]
    for arm, index, what in SHOWN:
        call = DEMO_RUNS[arm]["calls"][index]
        text = call["request"]["prompt"]
        print("=" * 100)
        print(f"{arm}: {what}; model {call['model']}; {len(text):,} characters sent")
        print("=" * 100)
        print(text)

# %% [markdown]
# Each prompt starts with the standing instruction that Claude Code subagents receive (use no tool, reply with the JSON object only) and then the task paragraph. Reading across the five prompts shows the designs' differences directly. The owner's list of fields is every field and its documents are all twelve. Agent 2 of the pipeline lists only its own stations' fields and documents, and its incoming material is the previous agent's note. Agent 2 of the shared record sees all twelve documents and every field written so far. The checker is told to return corrections only. The reviewer is told to redo every station from the source records and to return every field.
#
# Next, one cached raw reply beside what `parse_reply` makes of it: agent 1 of the pipeline of 4 on the same case, which owns the fields of stations 1 and 2.

# %%
if NOTEBOOK_RUN:
    call = DEMO_RUNS["Pipeline of 4"]["calls"][0]
    raw = call["reply"]["text"]
    parsed, status = parse_reply(raw, "last")
    print(f"RAW REPLY ({len(raw):,} characters, cache key {call['reply']['cache_key'][:12]}...)\n{raw}")
    print(f"\nPARSED (status {status!r})")
    print("fields:", json.dumps(parsed["fields"]))
    print("note:  ", parsed["note"][:700] + (" [...]" if len(parsed["note"]) > 700 else ""))
    print("fields the agent may return:", [f for f in stations_for("credit", 4)[0]["fields"]])

# %% [markdown]
# The reply is one object, so both parsers read it the same way. The agent returned exactly the fields of stations 1 and 2 (`complete` and `bureau_score`), and a note for the next agent. The note is the only channel for anything not on a form, such as the relationship email.

# %% [markdown]
# ## 4. Scoring and the measures
#
# A case is **fully correct** when every scored field matches the exact answer; money compares to the cent and code lists compare as sets. A case is **unreadable** when the form cannot be scored: no parseable JSON object, a field the agent was not allowed to fill, a missing note, or a scored field never filled. A readable case that is not fully correct is **wrong**. Both count as failures, and accuracy on readable cases is also given.
#
# A reply can hold more than one JSON object. The **first-answer** reading, fixed in advance, takes the first complete object; the **final-answer** reading takes the last complete object with a `fields` key. They differ only when an agent revised itself within a reply (section 17).
#
# **Planted fact kept** is the share of cases in which the field that depends on the planted fact is correct; in credit and trade that field also lists other codes, so section 15 also counts cases where the planted code itself is missing. **Intake error caught** is the share of the 17 wrong-note cases in which the affected field is correct.
#
# **Characters per case** totals every prompt and reply in a case. Work is counted in characters because the subagents report no tokens and `codex exec` adds 21,375 tokens of fixed overhead per call; the count leaves out that standing context.
#
# Each accuracy has a **95% interval** from 4,000 bootstrap resamples: draw 80 cases with replacement, recompute the share, keep the middle 95%. An arm with 80 of 80 gets an interval with no width, though its true error rate could be up to about 4%.
#
# A **paired difference** compares two arms on the same cases: score each case 1 if fully correct, 0 if not, and average (first arm minus second). The shared record was right and one owner wrong on 13 cases, the reverse on 1, so the difference is (13 - 1) / 80 = +15.0 points. Its interval resamples the case pairs.
#
# The **scaling exponent** asks how correct output grows with team size when each agent has the same work budget. Output per 1,000 characters is k agents times accuracy divided by thousands of characters per case: 1 x 0.8375 / 9.163 = 0.091 for one owner, 8 x 0.5875 / 40.532 = 0.116 for the pipeline of 8, against 0.73 if output grew in proportion. The exponent is the slope of log output on log k over k = 1, 2, 4 and 8: 1 is proportional, 0 is no growth, and 0.13 means doubling the team multiplies output by about 1.1.
#
# The scorer below compares each field with the exact answer. Money is compared after half-up rounding to cents, code lists as sets, booleans and integers exactly and strings exactly. `score_case` returns the case status (correct, wrong or unreadable), a per-field flag, and the two handoff flags: the planted field, and on injected cases the field the wrong intake note touched.

# %%
def field_equal(field, expected, observed):
    try:
        if field in MONEY_FIELDS:
            if isinstance(observed, bool):
                return False
            d = Decimal(str(observed))
            return d.is_finite() and money(expected) == money(d)
        if field in SET_FIELDS:
            return isinstance(observed, list) and all(isinstance(v, str) for v in observed) and set(expected) == set(observed)
        if isinstance(expected, bool):
            return type(observed) is bool and observed == expected
        if isinstance(expected, int):
            return type(observed) in (int, float) and observed == expected
        return isinstance(observed, str) and observed == expected
    except (ValueError, TypeError, ArithmeticError):
        return False


def score_case(case, result):
    fields = result.get("fields", {})
    checks = {f: f in fields and field_equal(f, expected, fields[f]) for f, expected in case["truth"].items()}
    reasons = list(result.get("unreadable_reasons", []))
    missing = set(case["truth"]) - set(fields)
    if missing and not any("missing_scored_fields" in r for r in reasons):
        reasons.append("missing_scored_fields: " + ", ".join(sorted(missing)))
    status = "unreadable" if reasons else "correct" if all(checks.values()) else "wrong"
    return {"status": status, "per_field_correct": checks, "unreadable_reasons": reasons,
            "planted_correct": checks[case["planted_field"]],
            "injected_correct": checks[case["injected_field"]] if case["injected"] else None}

# %% [markdown]
# The cell below scores the single owner's saved reply on `credit-4802` field by field, and then checks the scorer on three small made-up inputs that show its rules: a code list in a different order, money that differs by half a cent and a field the agent never filled.

# %%
if NOTEBOOK_RUN:
    result = DEMO_RUNS["One owner"]
    score = score_case(case, result)
    print("status:", score["status"], "| planted field correct:", score["planted_correct"], "| intake error caught:", score["injected_correct"])
    rows = [{"field": f, "expected": json.dumps(case["truth"][f]), "returned": json.dumps(result["fields"].get(f)), "correct": ok}
            for f, ok in score["per_field_correct"].items()]
    print(pd.DataFrame(rows).to_string(index=False))

    print("\nScoring rules on made-up values (illustrative, not measured):")
    print("  conditions [A, B] vs [B, A, A] ->", field_equal("conditions", ["A", "B"], ["B", "A", "A"]))
    print("  exposure_cad 420000.00 vs 420000.004 ->", field_equal("exposure_cad", 420000.00, 420000.004))
    print("  exposure_cad 420000.00 vs 420000.01 ->", field_equal("exposure_cad", 420000.00, 420000.01))
    print("  one field never filled ->", score_case(case, {"fields": {k: v for k, v in case["truth"].items() if k != "decision"}})["status"])

    agree = 0
    for c in CASES:
        solved = solve_documents(c["process"], c["documents"])
        agree += all(f in solved and field_equal(f, t, solved[f]) for f, t in c["truth"].items())
    print(f"\nThe independent solver of section 2 agrees with the exact answer on every field in {agree} of {len(CASES)} cases.")
    assert agree == len(CASES)

# %% [markdown]
# ## 5. Reading a reply that holds two answers
#
#
# An agent sometimes writes an answer, notices a mistake and writes a second one in the same reply. The rule fixed before any call took the first complete JSON object, so the draft would be scored, and in a pipeline the draft's note would be passed to the next agent. The final-answer reading was added after the results were seen, when per-call records showed this happening. This notebook reports both, as `first` and `last`.
#
# The cell below finds a real reply of that kind: agent 7 of the pipeline of 8 on `trade-4806`. It prints the reply and what each parser makes of it. Which replies differ across the whole cache, and what that does to the scores, is counted in section 7 and section 17.

# %%
if NOTEBOOK_RUN:
    trade_case = CASES_BY_ID["trade-4806"]
    run8 = run_case(trade_case, "pipeline", 8, SONNET_MODEL, cached_call, "first")
    call = run8["calls"][6]
    raw = call["reply"]["text"]
    objects = _json_objects(raw)
    print(f"RAW REPLY of agent 7 ({len(raw):,} characters, {len(objects)} complete JSON objects)\n{raw}\n")
    for name in PARSERS:
        parsed, status = parse_reply(raw, name)
        print(f"parser {name!r}: status {status}; authority = {parsed['fields'].get('authority')!r}; note starts: {parsed['note'][:110]!r}")
    print("\nparse_differs:", parse_differs(raw))

# %% [markdown]
# The two objects give different values (authority SENIOR in the first, DIRECTOR in the second, with a different note), and the parsers keep a different one. In a pipeline the next agent's prompt is built from the kept fields and note, so a changed reply changes every later prompt in that chain. Those later prompts are new requests, which is why the affected chains were run again from the next agent and why the cache can serve one parser's chain only if it holds those replies.

# %% [markdown]
# ## 6. Running and caching
#
# Fresh model work goes through command-line tools only, never through an HTTP API. GPT-6.1 Terra is called with `codex exec`. Claude Sonnet 5.5 is configured with the route `subagent`: Claude Code subagents answer outside this program, because `claude -p` on the machine was signed out. The program exports the prompts it is waiting for, a workflow script carries them to subagents, and the replies are imported into the same cache. A pipeline needs one round per agent, because agent 2's prompt contains agent 1's reply. The cells in this section define that machinery. A default run of the notebook starts none of it.
#
# ```mermaid
# flowchart LR
#     run["run_all<br/>runs every case as far as the cache allows"] -->|"first uncached prompt of each waiting run"| pend["export_pending<br/>pending.json + pending_requests.jsonl"]
#     pend --> wf["make_workflow<br/>round_N.js files + round_parent.js"]
#     wf -->|"one subagent per prompt (Claude Code, run by hand)"| sub["Claude Sonnet 5.5 subagents<br/>reply with one JSON object"]
#     sub -->|"journal.jsonl of the workflow run"| imp["import_journal / import_replies<br/>one cache row per reply"]
#     imp --> cache[("data/cache_requests.jsonl")]
#     cache -->|"repeat for the next pipeline agent, up to 8 rounds"| run
#     run -->|"Terra calls: codex exec, cached on return"| cache
# ```
#
# The first cell wraps the two command-line tools. `run_cli` runs one command, keeps every attempt (a rate-limit error is retried up to three times) and never sends anything over a network by itself. `call_claude` and `call_codex` build each tool's command, read its reply and token counts, and name a failure precisely (signed out, timeout, provider error). A failed call is returned to the caller but never written to the cache, so a later run tries it again.

# %%
def clean_cli_environment():
    env = os.environ.copy()
    seen, entries = set(), []
    for entry in env.get("PATH", "").split(os.pathsep):
        entry = entry.strip().strip('"')
        key = os.path.normcase(os.path.abspath(entry)) if entry else ""
        if key and key not in seen and os.path.isdir(entry):
            seen.add(key)
            entries.append(entry)
    env["PATH"] = os.pathsep.join(entries)
    return env


def run_cli(command, prompt, env):
    """Only rate-limit errors retry here; run_case handles one empty/timeout retry."""
    attempts = []
    begin = time.perf_counter()
    for attempt in range(4):
        start = dt.datetime.now(dt.timezone.utc)
        try:
            proc = subprocess.run(command, input=prompt, text=True, encoding="utf-8", errors="replace",
                                  capture_output=True, timeout=300, env=env, shell=False)
            text_out, text_err, returncode = proc.stdout, proc.stderr, proc.returncode
            error = None if returncode == 0 else "cli_error"
        except subprocess.TimeoutExpired as exc:
            def decoded(value):
                return value.decode("utf-8", "replace") if isinstance(value, bytes) else value or ""
            text_out, text_err, returncode, error = decoded(exc.stdout), decoded(exc.stderr), None, "timeout"
        except OSError as exc:
            text_out, text_err, returncode, error = "", str(exc), None, "cli_error"
        entry = {"attempt": attempt + 1, "started": start.isoformat(), "stdout": text_out,
                 "stderr": text_err, "returncode": returncode, "error": error,
                 "ended": dt.datetime.now(dt.timezone.utc).isoformat()}
        attempts.append(entry)
        limited = bool(re.search(r"rate.?limit|too many requests|\b429\b", text_out + "\n" + text_err, re.I))
        if limited and attempt < 3:
            time.sleep(2 ** (attempt + 1))
            continue
        if limited:
            entry["error"] = "rate_limit"
        return {"transport_attempts": attempts, "stdout": text_out, "stderr": text_err,
                "error": entry["error"], "seconds": time.perf_counter() - begin}


AUTH_PATTERN = re.compile(r"failed to authenticate|oauth|not logged in|please (?:run )?/?log ?in|unauthori[sz]ed|\b401\b"
                          r"|invalid api key|sign in|login required", re.I)


class ModelBlocked(RuntimeError):
    """The model's command-line tool is signed out; its work stops, other models continue."""


class Waiting(Exception):
    """A subagent-route request has no cached reply yet; the caller marks the run as waiting."""
    request = None
    key = None
    cli = False


class CliMiss(Waiting):
    """Export mode met an uncached command-line request; it is never sent from export."""
    cli = True


def classify_failure(result):
    """Name a command-line failure precisely. Any result with an error is never cached."""
    if result.get("error") and result["error"] not in ("timeout", "executable_missing"):
        evidence = "\n".join([str(result.get("text", "")), str(result.get("stdout", "")), str(result.get("stderr", ""))])
        if AUTH_PATTERN.search(evidence):
            result["error"] = "auth_error"
        elif result.get("terminal_reason") == "api_error":
            result["error"] = "api_error"
    return result


def call_claude(prompt, model):
    env = clean_cli_environment()
    executable = shutil.which("claude", path=env["PATH"])
    if not executable:
        return {"text": "", "error": "executable_missing", "input_tokens": 0, "output_tokens": 0}
    raw = run_cli([executable, "-p", "--model", model["version"], "--output-format", "json",
                   "--safe-mode", "--tools", ""], prompt, env)
    result = dict(raw, text="", input_tokens=0, output_tokens=0)
    # Preserve and account for every printed JSON result, including rate-limit tries.
    for attempt in raw["transport_attempts"]:
        try:
            obj = json.loads(attempt["stdout"])
            if not isinstance(obj, dict):
                raise ValueError("CLI envelope must be an object")
            usage = obj.get("usage") or {}
            result["input_tokens"] += sum(int(usage.get(k, 0) or 0) for k in
                                          ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
            result["output_tokens"] += int(usage.get("output_tokens", 0) or 0)
            if attempt is raw["transport_attempts"][-1]:
                result["text"] = obj.get("result", "")
                result["usage"] = usage
                result["terminal_reason"] = obj.get("terminal_reason")
                if obj.get("is_error") or obj.get("terminal_reason") == "api_error":
                    result["error"] = result.get("error") or "provider_error"
        except (ValueError, TypeError):
            if attempt is raw["transport_attempts"][-1] and attempt["stdout"].strip() and not result["error"]:
                result["error"] = "invalid_cli_envelope"
    return classify_failure(result)


def call_codex(prompt, model):
    env = clean_cli_environment()
    executable = shutil.which("codex", path=env["PATH"])
    if not executable:
        return {"text": "", "error": "executable_missing", "input_tokens": 0, "output_tokens": 0}
    effort = model.get("reasoning_effort") or "low"
    raw = run_cli([executable, "exec", "-m", model["version"], "-c", f'model_reasoning_effort="{effort}"',
                   "--ignore-user-config", "-c", "instructions=" + json.dumps(CODEX_INSTRUCTIONS),
                   "--sandbox", "read-only", "--skip-git-repo-check", "--json", "-"], prompt, env)
    result = dict(raw, text="", input_tokens=0, output_tokens=0)
    for attempt in raw["transport_attempts"]:
        final_messages = []
        for line in attempt["stdout"].splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            item = event.get("item") or {}
            if event.get("type") == "item.completed" and item.get("type") == "agent_message":
                final_messages.append(item.get("text", ""))
            if event.get("type") == "turn.completed":
                usage = event.get("usage") or {}
                result["input_tokens"] += int(usage.get("input_tokens", 0) or 0)
                result["output_tokens"] += int(usage.get("output_tokens", 0) or 0)
                result["usage"] = usage
            if event.get("type") in ("turn.failed", "error") and attempt is raw["transport_attempts"][-1]:
                result["error"] = result.get("error") or "provider_error"
        if attempt is raw["transport_attempts"][-1]:
            result["text"] = final_messages[-1] if final_messages else ""
    return classify_failure(result)

# %% [markdown]
# The next cell is the optional trace to the owner's local Langfuse server, which keeps one trace for every fresh model call across all experiments. Tracing starts only when a live run asks for it (`start_tracing`), looks for the server with a two-second health check, and does nothing when the keys or the server are missing. A replay never starts it, and the notebook asserts that in section 7.

# %%
LANGFUSE_HOST = os.environ.get("LANGFUSE_HOST", "http://localhost:3300").rstrip("/")
LANGFUSE_AUTH = (os.environ.get("LANGFUSE_PUBLIC_KEY", ""), os.environ.get("LANGFUSE_SECRET_KEY", ""))
LANGFUSE_ON = False
_LANGFUSE_CHECKED = False


def _langfuse_running():
    if not all(LANGFUSE_AUTH):
        return False
    try:
        import requests
        return requests.get(f"{LANGFUSE_HOST}/api/public/health", timeout=2).ok
    except Exception:
        return False


def start_tracing():
    global LANGFUSE_ON, _LANGFUSE_CHECKED
    if not _LANGFUSE_CHECKED:
        LANGFUSE_ON = _langfuse_running()
        _LANGFUSE_CHECKED = True


def trace_call(cache_key, name, model, request, response, start, end, usage=None, cost_usd=None,
               session_id=None, metadata=None, error=None):
    """One fresh span, using the repository's OTLP helper; never affects the run."""
    if not LANGFUSE_ON:
        return
    try:
        import requests

        def attr(k, v):
            return {"key": k, "value": {"stringValue": v if isinstance(v, str) else json.dumps(v, default=str)}}

        tags = {"key": "langfuse.trace.tags", "value": {"arrayValue": {"values": [{"stringValue": f"nb{NOTEBOOK[:2]}"}]}}}
        attrs = [attr("langfuse.observation.type", "generation"), attr("langfuse.observation.model.name", model),
                 attr("langfuse.observation.input", request), attr("langfuse.observation.output", response),
                 attr("langfuse.trace.name", f"{NOTEBOOK[:2]} {name}"), tags,
                 attr("langfuse.environment", "notebook"), attr("langfuse.trace.metadata.notebook", NOTEBOOK),
                 attr("langfuse.trace.metadata.cache_key", cache_key)]
        if usage:
            attrs.append(attr("langfuse.observation.usage_details", usage))
        if cost_usd is not None:
            attrs.append(attr("langfuse.observation.cost_details", {"total": cost_usd}))
        if session_id:
            attrs.append(attr("langfuse.session.id", f"{NOTEBOOK}/{session_id}"))
        if error:
            attrs += [attr("langfuse.observation.level", "ERROR"), attr("langfuse.observation.status_message", str(error))]
        for k, v in (metadata or {}).items():
            attrs.append(attr(f"langfuse.observation.metadata.{k}", v))
        span = {"traceId": hashlib.sha256(f"{NOTEBOOK}|{cache_key}".encode()).hexdigest()[:32],
                "spanId": hashlib.sha256(f"{NOTEBOOK}|{cache_key}|gen|0".encode()).hexdigest()[:16],
                "name": name, "kind": 1, "attributes": attrs,
                "startTimeUnixNano": str(int(start.timestamp() * 1e9)),
                "endTimeUnixNano": str(int(end.timestamp() * 1e9))}
        body = {"resourceSpans": [{"resource": {"attributes": [attr("service.name", "experiment-notebooks")]},
                                   "scopeSpans": [{"scope": {"name": NOTEBOOK}, "spans": [span]}]}]}
        requests.post(f"{LANGFUSE_HOST}/api/public/otel/v1/traces", json=body, auth=LANGFUSE_AUTH, timeout=10)
    except Exception:
        pass

# %% [markdown]
# `RequestCache` is the append-only cache. Each row holds the full request beside the response, keyed by the hash of the request, and a lock makes concurrent identical requests run once. A cached reply is returned as it was; a replay-only cache raises an error on any miss instead of calling a model. When a fresh reply arrives it is appended to the file and sent to Langfuse if tracing is on.

# %%
class RequestCache:
    """Thread-safe, append-only cache shared by both provider pools in one runner."""
    def __init__(self, path=DATA / "cache_requests.jsonl", replay_only=False, backend=None, trace=True):
        self.path, self.replay_only = Path(path), replay_only
        self.backend = backend or self.live_call
        self.trace = trace and not replay_only
        self.rows, self.key_locks = {}, {}
        self.guard = threading.Lock()
        self.fresh_calls = 0
        self.cache_hits = 0
        self.checker_models = MODELS
        self.blocked = set()
        self.failed_calls = 0
        if self.path.exists():
            for number, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), 1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                    if request_key(row["request"]) != row["cache_key"]:
                        raise ValueError("cache key mismatch")
                    if row["response"].get("error"):
                        continue  # failed calls are never reused; a later run tries again
                    self.rows[row["cache_key"]] = row
                except (ValueError, KeyError) as exc:
                    raise ValueError(f"Invalid cache row {number} in {self.path}: {exc}") from exc

    @staticmethod
    def live_call(prompt, model):
        if model.get("route", "cli") == "subagent":
            raise Waiting()  # answered outside the script; see --export-pending
        return {"claude": call_claude, "codex": call_codex}[model["provider"]](prompt, model)

    def __call__(self, prompt, model):
        request = make_request(prompt, model)
        key = request_key(request)
        with self.guard:
            lock = self.key_locks.setdefault(key, threading.Lock())
        with lock:
            if model["version"] in self.blocked:
                raise ModelBlocked(model["version"])
            if key in self.rows:
                with self.guard:
                    self.cache_hits += 1
                return dict(self.rows[key]["response"], cached=True, cache_key=key)
            if self.replay_only:
                raise AssertionError(f"Replay cache miss: {key} ({model['version']})")
            start = dt.datetime.now(dt.timezone.utc)
            tick = time.perf_counter()
            try:
                response = self.backend(prompt, model)
            except Waiting as waiting:
                waiting.request, waiting.key = request, key
                raise
            response = {"text": response} if isinstance(response, str) else dict(response)
            response.setdefault("seconds", time.perf_counter() - tick)
            response.setdefault("input_tokens", 0)
            response.setdefault("output_tokens", 0)
            end = dt.datetime.now(dt.timezone.utc)
            if response.get("error"):
                # A command-line failure is returned to the caller but never written to the cache.
                with self.guard:
                    self.failed_calls += 1
                    first = response["error"] == "auth_error" and model["version"] not in self.blocked
                    if response["error"] == "auth_error":
                        self.blocked.add(model["version"])
                if first:
                    print(f"{model['name']}: the {model['provider']} command-line tool needs signing in; skipping this model.", flush=True)
                if response["error"] == "auth_error":
                    raise ModelBlocked(model["version"])
                return dict(response, cached=False, cache_key=key)
            row = {"cache_key": key, "request": request, "response": response,
                   "timestamp": end.isoformat(), "start": start.isoformat(), "end": end.isoformat()}
            with self.guard:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with self.path.open("a", encoding="utf-8") as stream:
                    stream.write(canonical(row) + "\n")
                    stream.flush()
                    os.fsync(stream.fileno())
                self.rows[key] = row
                self.fresh_calls += 1
            if self.trace and LANGFUSE_ON:
                try:
                    name, session = _trace_context(request)
                    trace_call(key, name, model["version"], request, response, start, end,
                               usage={"input": response["input_tokens"], "output": response["output_tokens"]},
                               session_id=session, error=response.get("error"))
                except Exception:
                    pass
            return dict(response, cached=False, cache_key=key)

# %% [markdown]
# `run_all` runs every case through every selected arm. Each provider has its own bounded pool of workers, including its checker calls, and case tasks run outside those pools so that a team can wait for the other provider without deadlock. Cases and per-call records are frozen beside the results table, so a replay uses the frozen cases rather than regenerating them. Interrupted runs keep their completed rows. The helpers before it count spend (calls, tokens where the tool reported them, characters) and let the second reading copy the runs whose replies parse the same under both parsers.

# %%
RESULT_COLUMNS = ["case_id", "process", "model", "provider", "design", "k", "injected", "planted_field",
                  "injected_field", "status", "final_fields", "per_field_correct", "unreadable_reasons",
                  "planted_correct", "injected_correct", "calls", "transport_attempts", "input_tokens", "overhead_input_tokens", "task_input_tokens", "output_tokens",
                  "prompt_chars", "reply_chars", "task_chars", "seconds", "model_seconds", "cached_calls", "difficulty", "case_hash"]


def design_sizes(design, sizes=None):
    return [1] if design == "owner" else (TEAM_SIZES if sizes is None else list(sizes)) if design == "pipeline" else [4]


def overhead_probe(model, cache):
    """Fixed input tokens the tool adds to any call, from one tiny prompt sent through the normal cached path.
    Returns None when the probe could not be answered."""
    response = cache(OVERHEAD_PROBE_PROMPT, dict(model, reply_attempt=1))
    if response.get("error") or not response.get("input_tokens"):
        return None
    return int(response["input_tokens"])


def measure_overheads(models, cache):
    overheads = {}
    for model in models:
        if model.get("route", "cli") == "subagent":
            overheads[model["version"]] = None  # subagent replies carry no token counts
            continue
        try:
            overheads[model["version"]] = overhead_probe(model, cache)
        except ModelBlocked:
            overheads[model["version"]] = None
        except Exception as exc:  # scripted test backends cannot answer the probe
            print(f"{model['name']}: overhead probe failed ({type(exc).__name__}); task tokens will equal raw input tokens.")
            overheads[model["version"]] = None
    return overheads


def spend_from_calls(calls, overheads=None):
    """Spend per model from call records, counting each distinct request once. Both tools ran on
    subscriptions, so there is no per-call bill: calls, tokens where the tool reported them, characters."""
    overheads = overheads or {}
    seen, table = set(), {}
    for call in calls:
        reply = call["reply"]
        key = reply.get("cache_key") or request_key(call["request"])
        if key in seen:
            continue
        seen.add(key)
        row = table.setdefault(call["model"], dict(model=call["model"], calls=0, token_calls=0, input_tokens=0, output_tokens=0,
                                                  prompt_chars=0, reply_chars=0))
        row["calls"] += 1
        row["prompt_chars"] += call["prompt_chars"]
        row["reply_chars"] += call["reply_chars"]
        if reply.get("input_tokens"):
            row["token_calls"] += 1
            row["input_tokens"] += reply["input_tokens"]
            row["output_tokens"] += reply.get("output_tokens") or 0
    for model, row in table.items():
        row["overhead_tokens"] = int(overheads.get(model) or 0) * row["token_calls"]
    return list(table.values())


def format_spend(rows):
    lines = ["Spend: both tools ran on subscriptions, so there is no per-call bill. Each distinct reply counts once.",
             f"{'model':<20}{'calls':>7}{'input tokens':>14}{'fixed overhead':>16}{'task input':>12}{'output tokens':>15}{'prompt chars':>14}{'reply chars':>13}"]
    for r in rows:
        if r["token_calls"]:
            tokens = (f"{r['input_tokens']:>14,}{r['overhead_tokens']:>16,}{r['input_tokens'] - r['overhead_tokens']:>12,}"
                      f"{r['output_tokens']:>15,}")
        else:
            tokens = f"{'not reported':>14}{'':>16}{'':>12}{'':>15}"
        lines.append(f"{r['model']:<20}{r['calls']:>7,}{tokens}{r['prompt_chars']:>14,}{r['reply_chars']:>13,}")
    return "\n".join(lines)


def details_path(output):
    """Per-call detail file for a results table. Files that can be rebuilt from the cache live in data/tmp."""
    output = Path(output)
    return TMP / (output.stem + ".calls.jsonl") if output.parent == DATA else output.with_suffix(".calls.jsonl")


def unchanged_runs(first_results=DATA / "results.csv"):
    """Runs of the "first" results whose replies all parse the same under both parsers: {"rows": ..., "details": ...},
    keyed (case_id, model, design, k). Parser "last" copies these runs instead of running them again."""
    first_results = Path(first_results)
    detail_file = details_path(first_results)
    out = {"rows": {}, "details": {}}
    if not first_results.exists() or not detail_file.exists():
        return out
    with first_results.open(newline="", encoding="utf-8") as stream:
        rows = {(r["case_id"], r["model"], r["design"], r["k"]): r for r in csv.DictReader(stream)}
    for line in detail_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        key = (d["case_id"], d["model"], d["design"], str(d["k"]))
        if key in rows and not any(parse_differs(c["reply"].get("text", "")) for c in d["result"]["calls"]):
            out["rows"][key], out["details"][key] = rows[key], line
    return out

# %%
def run_all(cases, models=MODELS, designs=DESIGNS, *, output=DATA / "results.csv", replay_check=False, cache=None,
            team_sizes=None, cases_path=None, overheads=None, details_file=None, quiet=False, parser=None, reuse=None):
    """parser: "first" or "last" (default PARSER). reuse: rows and detail lines of runs whose replies parse the same
    under both parsers (see unchanged_runs); those runs are copied unchanged instead of being run again."""
    parser = parser or PARSER
    cases = list(cases)
    if not models:
        raise ValueError("MODELS is empty")
    for design in designs:
        if design not in ALL_DESIGNS:
            raise ValueError(f"Unknown design {design}")
    # Keep defaults available as checker candidates during a one-model calibration.
    candidates = list(models) + [m for m in MODELS if m["provider"] not in {x["provider"] for x in models}]
    if "checker" in designs and any(other_model(m, candidates) is None for m in models):
        raise ValueError("No other vendor configured for checker")
    cache = cache or RequestCache(replay_only=replay_check, trace=not replay_check)
    if replay_check and not cache.replay_only:
        raise ValueError("Replay check requires a replay-only cache")
    if cache.trace and cache.backend == cache.live_call:
        start_tracing()
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    frozen = Path(cases_path) if cases_path else output.with_name("cases.jsonl" if output.name == "results.csv" else output.stem + "_cases.jsonl")
    frozen_text = "".join(canonical(c) + "\n" for c in cases)
    if frozen.exists() and frozen.read_text(encoding="utf-8") != frozen_text:
        raise ValueError(f"Frozen cases differ at {frozen}; use a new output path for a changed experiment")
    if not frozen.exists():
        frozen.write_text(frozen_text, encoding="utf-8")
    pools = {provider: futures.ThreadPoolExecutor(max_workers=WORKERS[provider]) for provider in {m["provider"] for m in candidates}}

    def pooled_call(prompt, model):
        return pools[model["provider"]].submit(cache, prompt, model).result()

    pooled_call.checker_models = candidates
    jobs = [(case, design, k, model) for case in cases for model in models for design in designs for k in design_sizes(design, team_sizes)]
    reuse = reuse or {"rows": {}, "details": {}}
    reused = [(c["id"], m["version"], d, str(k)) for c, d, k, m in jobs if (c["id"], m["version"], d, str(k)) in reuse["rows"]]
    jobs = [j for j in jobs if (j[0]["id"], j[3]["version"], j[1], str(j[2])) not in set(reused)]
    completed, waiting_runs, spent_calls = [], [], []
    trace_path = Path(details_file) if details_file else details_path(output)
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    if overheads is None:
        overheads = measure_overheads(models, cache)
    for model in models:
        if overheads.get(model["version"]) is None and model["version"] not in cache.blocked and model.get("route", "cli") == "cli":
            print(f"{model['name']}: overhead unknown; task input tokens equal raw input tokens.")
    # A limited run keeps rows from earlier runs that it does not redo.
    job_ids = {(c["id"], m["version"], d, str(k)) for c, d, k, m in jobs}
    kept_rows, kept_details = [], []
    if output.exists() and output.stat().st_size and not replay_check:
        with output.open(newline="", encoding="utf-8") as old:
            kept_rows = [r for r in csv.DictReader(old) if (r["case_id"], r["model"], r["design"], r["k"]) not in job_ids]
        if trace_path.exists():
            for line in trace_path.read_text(encoding="utf-8").splitlines():
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if (d["case_id"], d["model"], d["design"], str(d["k"])) not in job_ids:
                    kept_details.append(line)
    # Open the full result only after validating frozen inputs and the cache.
    try:
        with output.open("w", newline="", encoding="utf-8") as stream, trace_path.open("w", encoding="utf-8") as details:
            writer = csv.DictWriter(stream, fieldnames=RESULT_COLUMNS)
            writer.writeheader()
            for old_row in kept_rows:
                writer.writerow({c: old_row.get(c, "") for c in RESULT_COLUMNS})
            for line in kept_details:
                details.write(line + "\n")
            for key in reused:
                writer.writerow({c: reuse["rows"][key].get(c, "") for c in RESULT_COLUMNS})
                details.write(reuse["details"][key] + "\n")
            if reused and not quiet:
                print(f"{len(reused)} runs whose replies parse the same under both parsers were copied unchanged.")
            with futures.ThreadPoolExecutor(max_workers=sum(WORKERS.values())) as task_pool:
                pending = {task_pool.submit(run_case, *job, pooled_call, parser): job for job in jobs}
                for future in futures.as_completed(pending):
                    case, design, k, model = pending[future]
                    try:
                        result = future.result()
                    except ModelBlocked:
                        continue  # signed-out model: no row, other models carry on
                    except Waiting:
                        waiting_runs.append((case["id"], model["version"], design, k))
                        continue  # no row until the subagent replies are imported
                    score = score_case(case, result)
                    overhead = overheads.get(model["version"])
                    timed = sum(1 for c in result["calls"] if c["reply"].get("input_tokens"))
                    task_input = max(0, result["input_tokens"] - timed * (overhead or 0)) if result["tokens_known"] else None
                    row = dict(case_id=case["id"], process=case["process"], model=model["version"], provider=model["provider"],
                               design=design, k=k, injected=case["injected"], planted_field=case["planted_field"], injected_field=case["injected_field"],
                               status=score["status"], final_fields=canonical(result["fields"]),
                               per_field_correct=canonical(score["per_field_correct"]), unreadable_reasons=canonical(score["unreadable_reasons"]),
                               planted_correct=score["planted_correct"], injected_correct=score["injected_correct"],
                               calls=len(result["calls"]), transport_attempts=sum(len(c["reply"].get("transport_attempts", [None])) for c in result["calls"]),
                               input_tokens=result["input_tokens"] if result["tokens_known"] else None, overhead_input_tokens=overhead,
                               task_input_tokens=task_input, output_tokens=result["output_tokens"] if result["tokens_known"] else None,
                               prompt_chars=result["prompt_chars"], reply_chars=result["reply_chars"],
                               task_chars=result["prompt_chars"] + result["reply_chars"],
                               seconds=result["seconds"], model_seconds=result["model_seconds"],
                               cached_calls=sum(bool(c["reply"].get("cached")) for c in result["calls"]),
                               difficulty=len(case["params"]["complications"]), case_hash=hashlib.sha256(canonical(case).encode()).hexdigest())
                    writer.writerow(row)
                    details.write(canonical({"case_id": case["id"], "model": model["version"], "design": design, "k": k, "result": result}) + "\n")
                    stream.flush()
                    details.flush()
                    completed.append(row)
                    spent_calls.extend(result["calls"])
                    if not quiet:
                        print(f"{case['id']} {model['version']} {design}/{k}: {score['status']}", flush=True)
    finally:
        for pool in pools.values():
            pool.shutdown(wait=True)
        if waiting_runs:
            print(f"{len(waiting_runs)} runs wait for subagent replies and have no result row yet (--export-pending, then --import-replies).")
        if cache.failed_calls:
            print(f"Failed command-line calls (not cached): {cache.failed_calls}.")
        if not quiet:
            print(f"Fresh replies: {cache.fresh_calls}; cache hits: {cache.cache_hits}.")
    if replay_check:
        assert cache.fresh_calls == 0, "Replay unexpectedly called a backend"
        if not quiet:
            print("Replay check PASS: zero model calls.")
    if not quiet and spent_calls:
        print(format_spend(spend_from_calls(spent_calls, overheads)))
    return completed

# %% [markdown]
# The next three cells are the subagent route. `export_pending` runs each case as far as the cache allows and writes the first uncached prompt of every waiting run (nothing is called). `make_workflow` writes JavaScript files that Claude Code runs, each holding a chunk of prompts and one subagent call per prompt, plus a parent file that runs all chunks in parallel. `import_replies` and `import_journal` read the subagents' replies back and append them to the cache, matching each to its prompt by key and tracing each new reply once.

# %% [markdown]
# The export code needs to read a saved prompt back into its parts (the context header, the allowed fields, the incoming material and the documents), which `prompt_parts` does.

# %%
def prompt_parts(prompt):
    def section(name):
        return json.loads(prompt.split(name + "\n", 1)[1].split("\n\n", 1)[0])
    return (section("CONTEXT"), section("ALLOWED FIELDS"), section("INCOMING"),
            dict(re.findall(r'<document id="([^"]+)">\n(.*?)\n</document>', prompt, re.S)))

# %%
PENDING_PATH = TMP / "pending_requests.jsonl"


def _pending_keys(pending_path):
    pending_path = Path(pending_path)
    rows = {}
    if pending_path.exists():
        for line in pending_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                rows[row["key"]] = row["request"]
    return rows


def _export_backend(prompt, model):
    raise (Waiting() if model.get("route", "cli") == "subagent" else CliMiss())


def _collect_pending(cases, models, designs, team_sizes, cache, parser=None):
    """Run each selected case as far as the cache allows. Returns the first uncached request of every waiting run
    (items), the counts of complete, waiting and command-line-blocked runs, and the state of every run."""
    items, seen, complete, waiting, cli_blocked, runs = [], set(), 0, 0, 0, []
    for case in cases:
        for model in models:
            if model.get("route", "cli") != "subagent":
                continue
            for design in designs:
                for k in design_sizes(design, team_sizes):
                    try:
                        run_case(case, design, k, model, cache, parser)
                        complete += 1
                        runs.append((case["id"], model["version"], design, k, "complete"))
                    except CliMiss:
                        cli_blocked += 1
                        runs.append((case["id"], model["version"], design, k, "needs_command_line_call"))
                    except Waiting as w:
                        waiting += 1
                        runs.append((case["id"], model["version"], design, k, "waiting"))
                        if w.key in seen:
                            continue
                        seen.add(w.key)
                        context = prompt_parts(w.request["prompt"][len(SUBAGENT_PREFIX):])[0]
                        retry = w.request["settings"].get("reply_attempt", 1)
                        label = f"{case['id']}-{design}{k}-a{context['station_index']}" + (f"-r{retry}" if retry > 1 else "")
                        items.append({"key": w.key, "label": label, "prompt": w.request["prompt"], "request": w.request})
    return items, complete, waiting, cli_blocked, runs


def export_pending(cases, models, designs, team_sizes, out, cache_path=DATA / "cache_requests.jsonl",
                   pending_path=PENDING_PATH, parser=None):
    """Run each selected case as far as the cache allows; export the first uncached request of every run.
    parser: "first" or "last" (default PARSER); under "last" the requests that change are the ones built from a reply
    that parses differently."""
    cache = RequestCache(cache_path, backend=_export_backend, trace=False)
    items, complete, waiting, cli_blocked, _ = _collect_pending(cases, models, designs, team_sizes, cache, parser)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps([{k: v for k, v in it.items() if k != "request"} for it in items], ensure_ascii=True, indent=1), encoding="utf-8")
    known = _pending_keys(pending_path)
    Path(pending_path).parent.mkdir(parents=True, exist_ok=True)
    with Path(pending_path).open("a", encoding="utf-8") as stream:
        for it in items:
            if it["key"] not in known:
                stream.write(canonical({"key": it["key"], "request": it["request"]}) + "\n")
    print(f"Prompts pending now: {len(items)}; runs complete: {complete}; runs still waiting on a later round: {waiting}"
          + (f"; runs blocked on a command-line model not yet cached: {cli_blocked}" if cli_blocked else "") + ".")
    print(f"Wrote {out}.")
    return {"pending": len(items), "complete": complete, "waiting": waiting, "cli_blocked": cli_blocked}

# %%
WORKFLOW_TEMPLATE = """export const meta = {
  name: 'nb48-claude-round',
  description: 'Answer one round of notebook 48 case prompts with Claude subagents',
  phases: [{ title: 'Answer' }],
}
const MODEL = %(model)s
const EFFORT = %(effort)s
const ITEMS = %(items)s
const out = await parallel(ITEMS.map(it => () =>
  agent(it.prompt, { label: it.label, phase: 'Answer', model: MODEL, effort: EFFORT%(agent_type)s })
    .then(text => ({ key: it.key, text: String(text) }))))
return { answered: out.filter(Boolean).length, total: ITEMS.length }
"""


PARENT_TEMPLATE = """export const meta = {
  name: 'nb48-claude-round-all',
  description: 'Run every chunk of one round of notebook 48 case prompts with Claude subagents',
  phases: [{ title: 'Answer' }],
}
const FILES = %(files)s
const outs = await parallel(FILES.map(p => () => workflow({ scriptPath: p })))
return outs
"""
CHUNK_BYTE_LIMIT = 500_000  # the workflow tool refuses larger script files


def make_workflow(pending_file, out_prefix, chunk=40, models=None, agent_type=None, byte_limit=CHUNK_BYTE_LIMIT):
    """Write OUT_PREFIX_1.js, OUT_PREFIX_2.js, ... (at most `chunk` prompts each, each file under `byte_limit` bytes,
    so the chunk size drops automatically when prompts are long) and OUT_PREFIX_parent.js, which runs every chunk
    in parallel with workflow({ scriptPath }). Returns the chunk files as (path, item count)."""
    model = next((m for m in (MODELS if models is None else models) if m.get("route") == "subagent"), None)
    if model is None:
        raise ValueError("No model with route 'subagent' in the models table")
    agent_type = agent_type or model.get("subagent_agent_type")
    agent_option = ", agentType: '" + agent_type + "'" if agent_type else ""
    items = json.loads(Path(pending_file).read_text(encoding="utf-8"))
    items = [{"key": it["key"], "label": it["label"], "prompt": it["prompt"]} for it in items]

    def render(part):
        return WORKFLOW_TEMPLATE % {"model": "'" + model["subagent_model"] + "'", "effort": "'" + model["subagent_effort"] + "'",
                                    "items": json.dumps(part, ensure_ascii=True), "agent_type": agent_option}

    fixed = len(render([]).encode("utf-8"))
    parts, current, size = [], [], fixed
    for item in items:
        cost = len(json.dumps(item, ensure_ascii=True).encode("utf-8")) + 2  # the item and its ", " separator
        if current and (len(current) >= chunk or size + cost >= byte_limit):
            parts.append(current)
            current, size = [], fixed
        current.append(item)
        size += cost
    if current:
        parts.append(current)
    written = []
    for number, part in enumerate(parts, 1):
        path = Path(f"{out_prefix}_{number}.js")
        path.parent.mkdir(parents=True, exist_ok=True)
        text = render(part)
        path.write_text(text, encoding="utf-8", newline="\n")
        if len(text.encode("utf-8")) >= byte_limit:
            print(f"Warning: {path} is {len(text.encode('utf-8')):,} bytes with a single prompt; it exceeds the {byte_limit:,} byte limit.")
        written.append((str(path), len(part)))
        print(f"Wrote {path}: {len(part)} items")
    if not written:
        print("No pending items; no workflow file written.")
        return written
    if len(parts) > 1 and len(parts[0]) < chunk:
        print(f"Chunk size lowered to keep each file under {byte_limit:,} bytes (first file holds {len(parts[0])} items).")
    parent = Path(f"{out_prefix}_parent.js")
    paths = [os.path.abspath(p).replace("\\", "/") for p, _ in written]
    parent.write_text(PARENT_TEMPLATE % {"files": json.dumps(paths)}, encoding="utf-8", newline="\n")
    print(f"Wrote {parent}: runs {len(paths)} chunk file(s) in parallel.")
    return written

# %%
def _walk_replies(value, pending, found, unknown):
    if isinstance(value, dict):
        if isinstance(value.get("key"), str) and isinstance(value.get("text"), str):
            (found if value["key"] in pending else unknown).append((value["key"], value["text"]))
            rest = {k: v for k, v in value.items() if k not in ("key", "text")}
            _walk_replies(rest, pending, found, unknown)
            return
        for v in value.values():
            _walk_replies(v, pending, found, unknown)
    elif isinstance(value, list):
        for v in value:
            _walk_replies(v, pending, found, unknown)
    elif isinstance(value, str) and value.lstrip()[:1] in ("[", "{"):
        try:
            inner = json.loads(value)
        except ValueError:
            return
        _walk_replies(inner, pending, found, unknown)


def _trace_context(request):
    """Trace name and session id for a request, built the same way for fresh calls and imported replies."""
    context = json.loads(request["prompt"].split("CONTEXT\n", 1)[1].split("\n\n", 1)[0])
    return (f"{context['process']} {context['design']} station {context['station_index'] + 1}",
            f"{context['case_id']}/{context['design']}/{context['team_size']}")


def _store_replies(found, unknown, pending, cache_path, trace=True):
    """Append replies for pending requests to the cache. Replies already cached are never stored or traced again."""
    cache = RequestCache(cache_path, trace=False)
    imported = present = conflicts = 0
    first_text, fresh = {}, []
    now = dt.datetime.now(dt.timezone.utc)
    stamp = now.isoformat()
    Path(cache_path).parent.mkdir(parents=True, exist_ok=True)
    with Path(cache_path).open("a", encoding="utf-8") as stream:
        for key, reply in found:
            if key in first_text and first_text[key] != reply:
                conflicts += 1
                continue
            if key in cache.rows:
                present += 1
                continue
            first_text[key] = reply
            row = {"cache_key": key, "request": pending[key],
                   "response": {"text": reply, "input_tokens": None, "output_tokens": None, "seconds": None,
                                "source": "claude-code-subagent"},
                   "timestamp": stamp, "start": stamp, "end": stamp}
            stream.write(canonical(row) + "\n")
            cache.rows[key] = row
            fresh.append(row)
            imported += 1
    traced = 0
    if trace and fresh:
        start_tracing()
        if LANGFUSE_ON:
            for row in fresh:
                try:
                    name, session = _trace_context(row["request"])
                    trace_call(row["cache_key"], name, row["request"]["model"], row["request"], row["response"], now, now,
                               session_id=session, metadata={"source": "claude-code-subagent"})
                    traced += 1
                except Exception:
                    pass
    without = sum(1 for key in pending if key not in cache.rows)
    print(f"Replies imported: {imported}; already present: {present}; unknown keys ignored: {unknown}; "
          f"pending requests still without a reply: {without}."
          + (f" Conflicting duplicate replies ignored (first kept): {conflicts}." if conflicts else "")
          + (f" Traces sent to Langfuse: {traced}." if traced else ""))
    return {"imported": imported, "present": present, "unknown": unknown, "without": without, "conflicts": conflicts, "traced": traced}


def import_replies(files, cache_path=DATA / "cache_requests.jsonl", pending_path=PENDING_PATH, trace=True):
    pending = _pending_keys(pending_path)
    found, unknown = [], []
    for name in files:
        text = Path(name).read_text(encoding="utf-8")
        try:
            documents = [json.loads(text)]
        except ValueError:
            documents = []
            for line in text.splitlines():
                if line.strip():
                    try:
                        documents.append(json.loads(line))
                    except ValueError:
                        continue
        for doc in documents:
            _walk_replies(doc, pending, found, unknown)
    return _store_replies(found, len(unknown), pending, cache_path, trace)


def import_journal(run_dir, pending_file, cache_path=DATA / "cache_requests.jsonl", pending_path=PENDING_PATH, trace=True):
    """Import replies straight from the journal.jsonl files a workflow run leaves under RUN_DIR.
    A "started" line gives an agent's id and label; a "result" line gives the id and the reply text.
    Labels are matched to the keys in PENDING_FILE (the --out file of --export-pending)."""
    key_of = {item["label"]: item["key"] for item in json.loads(Path(pending_file).read_text(encoding="utf-8"))}
    pending = _pending_keys(pending_path)
    label_of, found, seen, unknown = {}, [], set(), 0
    journals = sorted(Path(run_dir).rglob("journal.jsonl"))
    for journal in journals:
        rows = []
        for line in journal.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    continue
        for row in rows:
            if row.get("type") == "started":
                label_of[row["agentId"]] = row.get("label")
        for row in rows:
            if row.get("type") == "result" and isinstance(row.get("result"), str):
                label = label_of.get(row["agentId"])
                if label in key_of and label not in seen:
                    seen.add(label)
                    if key_of[label] in pending:
                        found.append((key_of[label], row["result"]))
                    else:
                        unknown += 1
    print(f"{len(seen)} replies matched {len(key_of)} pending prompts in {len(journals)} journal file(s).")
    return _store_replies(found, unknown, pending, cache_path, trace)

# %% [markdown]
# The cell below looks at the saved cache and then shows the export and workflow steps on one case with an empty temporary cache. It reads the committed cache to count what it holds and to check that every row's key is the hash of its stored request. It then exports the first pending prompt of `credit-4802` in the pipeline of 2 into a temporary folder and writes a workflow file from it. No model is called and nothing is written to `data/`.

# %%
if NOTEBOOK_RUN:
    import collections, contextlib, io, tempfile

    by_source = collections.Counter((row["request"]["model"], row["response"].get("source", "cli")) for row in CACHE_INDEX.values())
    for (model_name, source), n in sorted(by_source.items()):
        print(f"{model_name:<18}{source:<22}{n:>6,} saved replies")
    bad = [k for k, row in CACHE_INDEX.items() if request_key(row["request"]) != k]
    print(f"rows whose key is not the hash of their stored request: {len(bad)}")

    sample = next(row for row in CACHE_INDEX.values() if row["request"]["settings"].get("route") == "subagent")
    print("\nOne cache row, request settings:", json.dumps(sample["request"]["settings"], indent=1)[:700])
    print("response fields:", sorted(sample["response"]))

    replay_cache = RequestCache(replay_only=True, backend=lambda *a: None, trace=False)
    try:
        replay_cache("A prompt that was never sent", SONNET_MODEL)
    except AssertionError as exc:
        print("\nreplay-only cache on an unsaved request ->", str(exc)[:90])

    helper_log = io.StringIO()  # the helpers print where they wrote; those lines name a temporary folder and are left out
    with tempfile.TemporaryDirectory() as folder, contextlib.redirect_stdout(helper_log):
        folder = Path(folder)
        stats = export_pending([CASES_BY_ID["credit-4802"]], [SONNET_MODEL], ["pipeline"], [2], folder / "pending.json",
                               cache_path=folder / "empty_cache.jsonl", pending_path=folder / "pending_requests.jsonl")
        files = make_workflow(folder / "pending.json", str(folder / "round1"))
        text = Path(files[0][0]).read_text(encoding="utf-8")
    print("\n".join(line for line in helper_log.getvalue().splitlines() if not line.startswith("Wrote ")))
    print(f"\nround1_1.js ({len(text):,} bytes), first 600 characters:\n{text[:600]}")
    print("\nLangfuse tracing started in this notebook:", LANGFUSE_ON, "(checked:", _LANGFUSE_CHECKED, ")")

# %% [markdown]
# ## 7. Replaying the scored run from the cache
#
# The replay rebuilds every row of the two results tables from the saved replies. For each of the 80 cases and each arm it runs the same code as a live run, with the cache as the only source of replies: the main comparison and the review arm for Claude Sonnet 5.5, then the single owner for GPT-6.1 Terra, then a calibration table (under the first reading only). A cache miss raises an error. Neither command-line tool is needed and nothing is traced. The rebuilt tables go to `data/tmp/` (git-ignored), and are compared with the committed `data/results.csv` (first answers) and `data/results_last_object.csv` (final answers) on case, model, design, team size, status, per-field correctness and the other columns listed below. Wall times and the count of cached calls describe the original run, so they are expected to differ and are not compared.
#
# The parser is never part of a cache key, so the same cached reply is read under either rule. Under the final-answer rule the next agent's prompt is built from the final fields and note, so the chains where a draft had been passed on were run again from the next agent (62 new Sonnet calls and 3 new Terra checker calls), and their replies are in the same cache.

# %% [markdown]
# The eight arms, their colours and the pairs of arms that are compared are defined once, here, because the replay, the parser report and the analysis all use them. Seven arms use Claude Sonnet 5.5 as the team model; one control arm uses GPT-6.1 Terra alone.

# %%
INK, MUTED, GUIDE, PAPER = "#0b0b0b", "#52514e", "#e1e0d9", "#fcfcfb"
COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
DESIGN_ORDER = ["owner", "pipeline", "shared", "checker", "review"]
FAMILIES = ["owner", "pipeline", "shared", "checker"]
FAMILY_COLORS = dict(zip(FAMILIES, COLORS))
FAMILY_LABELS = {"owner": "One owner", "pipeline": "Pipeline", "shared": "Shared record or review", "checker": "Pipeline + checker"}
SONNET, TERRA = MODELS[0]["version"], MODELS[1]["version"]
ARMS = [
    {"key": (SONNET, "owner", 1), "label": "One owner", "family": "owner", "control": False},
    {"key": (SONNET, "pipeline", 2), "label": "Pipeline of 2", "family": "pipeline", "control": False},
    {"key": (SONNET, "pipeline", 4), "label": "Pipeline of 4", "family": "pipeline", "control": False},
    {"key": (SONNET, "pipeline", 8), "label": "Pipeline of 8", "family": "pipeline", "control": False},
    {"key": (SONNET, "shared", 4), "label": "Shared record of 4", "family": "shared", "control": False},
    {"key": (SONNET, "checker", 4), "label": "Pipeline of 4 + Terra checker", "family": "checker", "control": False},
    {"key": (TERRA, "owner", 1), "label": "Terra, one owner (control)", "family": "owner", "control": True},
    {"key": (SONNET, "review", 4), "label": "Owner + 3 reviewers (control)", "family": "shared", "control": True},
]
ARM_BY_KEY = {a["key"]: a for a in ARMS}
ARM_BY_LABEL = {a["label"]: a for a in ARMS}
TABLE_NAMES = ("accuracy", "by_process", "paired", "scaling", "scaling_points")
PAIRS = [("Pipeline of 2", "One owner"), ("Pipeline of 4", "One owner"), ("Pipeline of 8", "One owner"),
         ("Pipeline of 8", "Pipeline of 4"), ("Shared record of 4", "One owner"), ("Shared record of 4", "Pipeline of 4"),
         ("Pipeline of 4 + Terra checker", "Pipeline of 4"), ("Pipeline of 4 + Terra checker", "Terra, one owner (control)"),
         ("Owner + 3 reviewers (control)", "One owner"), ("Owner + 3 reviewers (control)", "Shared record of 4"),
         ("Terra, one owner (control)", "One owner")]
TITLES, NUMBERS = {}, {}  # filled while the figures are drawn, printed at the end of analyse

# %%
REPLAY_KEY_COLUMNS = ["case_id", "model", "design", "k"]
REPLAY_SAME_COLUMNS = ["status", "per_field_correct"]
REPLAY_EXTRA_COLUMNS = ["final_fields", "planted_correct", "injected_correct", "calls", "input_tokens", "output_tokens",
                        "overhead_input_tokens", "prompt_chars", "reply_chars", "task_chars", "case_hash"]


def _replay_backend(prompt, model):
    raise AssertionError(f"Replay cache miss for {model['version']}; replay never calls a model")


def compare_tables(rebuilt, reference):
    """Compare two results CSV files row by row. Returns a dict with the number of rows, the mismatches per column
    and the rows missing from either side."""
    def load(path):
        with Path(path).open(newline="", encoding="utf-8") as stream:
            return {tuple(r[c] for c in REPLAY_KEY_COLUMNS): r for r in csv.DictReader(stream)}
    new, old = load(rebuilt), load(reference)
    mismatches = {}
    for key in new.keys() & old.keys():
        for column in REPLAY_SAME_COLUMNS + REPLAY_EXTRA_COLUMNS:
            if column in old[key] and column in new[key] and old[key][column] != new[key][column]:
                mismatches.setdefault(column, []).append(key)
    return {"rows": len(new), "reference_rows": len(old), "only_rebuilt": sorted(new.keys() - old.keys()),
            "only_reference": sorted(old.keys() - new.keys()), "mismatches": mismatches}


def replay_all(cache_path=DATA / "cache_requests.jsonl", cases_path=DATA / "cases.jsonl",
               calibration_cases_path=DATA / "calibration_cases.jsonl", reference=None,
               calibration_reference=DATA / "calibration_results.csv", out_dir=TMP, quiet=False, parser=None):
    """Rebuild results.csv and calibration_results.csv from the cache with zero model calls (see the section note).
    Returns True when both rebuilt tables agree with the committed ones. Raises on a cache miss.
    With parser "last" it rebuilds results_last_object.csv only (no calibration table) and fails until every request
    that parser needs is in the cache."""
    parser = parser or PARSER
    reference = reference or RESULTS_FILES[parser]
    cache_path, out_dir = Path(cache_path), Path(out_dir)
    for needed in (cache_path, Path(cases_path), Path(calibration_cases_path)):
        if not needed.exists():
            raise FileNotFoundError(f"Replay needs {needed}")
    cache = RequestCache(cache_path, replay_only=True, backend=_replay_backend, trace=False)
    sonnet = next(m for m in MODELS if m["version"] == SONNET)
    terra = next(m for m in MODELS if m["version"] == TERRA)
    out_dir.mkdir(parents=True, exist_ok=True)
    cases = load_or_make_cases(cases_path, SEED, N_CASES_PER_PROCESS)
    calibration = load_or_make_cases(calibration_cases_path, CALIBRATION_SEED, 6)
    terra_overhead = overhead_probe(terra, cache)  # a missing probe row raises
    if terra_overhead is None:
        raise ValueError("The cache has no usable overhead probe for GPT-6.1 Terra")
    plan = [("main comparison, Claude Sonnet 5.5", cases, [sonnet], DESIGNS, None, {SONNET: None}),
            ("review arm, Claude Sonnet 5.5", cases, [sonnet], ["review"], None, {SONNET: None}),
            ("single owner, GPT-6.1 Terra", cases, [terra], ["owner"], None, {TERRA: terra_overhead})]
    rows, details, merged_rows = [], [], []
    with tempfile.TemporaryDirectory(prefix="agent-teams-replay-", dir=out_dir) as temp:
        for number, (name, plan_cases, models, designs, sizes, overheads) in enumerate(plan):
            part = Path(temp) / f"part{number}.csv"
            got = run_all(plan_cases, models, designs, output=part, replay_check=True, cache=cache, team_sizes=sizes,
                          cases_path=cases_path, overheads=overheads, details_file=Path(temp) / f"part{number}.calls.jsonl", quiet=True,
                          parser=parser)
            if not quiet:
                print(f"Replayed {name}: {len(got)} runs.")
            with part.open(newline="", encoding="utf-8") as stream:
                merged_rows += list(csv.DictReader(stream))
            details += (Path(temp) / f"part{number}.calls.jsonl").read_text(encoding="utf-8").splitlines()
        main_output = out_dir / (RESULTS_FILES[parser].stem + "_replay.csv")
        with main_output.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=RESULT_COLUMNS)
            writer.writeheader()
            writer.writerows(merged_rows)
        details_path(RESULTS_FILES[parser]).write_text("".join(line + "\n" for line in details), encoding="utf-8")
        calibration_output = out_dir / "calibration_results_replay.csv"
        if parser == "first":
            run_all(calibration, [sonnet], ["owner", "pipeline"], output=calibration_output, replay_check=True, cache=cache,
                    team_sizes=[4], cases_path=calibration_cases_path, overheads={SONNET: None},
                    details_file=details_path(DATA / "calibration_results.csv"), quiet=True, parser=parser)
    assert cache.fresh_calls == 0, "Replay unexpectedly called a backend"
    ok = True
    checks = [(RESULTS_FILES[parser].name, main_output, reference)]
    if parser == "first":
        checks.append(("calibration_results.csv", calibration_output, calibration_reference))
    for name, rebuilt, committed in checks:
        if not Path(committed).exists():
            print(f"{name}: no committed file to compare with; rebuilt {rebuilt}.")
            continue
        report = compare_tables(rebuilt, committed)
        same = (report["rows"] == report["reference_rows"] and not report["only_rebuilt"] and not report["only_reference"]
                and not any(c in report["mismatches"] for c in REPLAY_SAME_COLUMNS))
        ok &= same
        print(f"Replay check {'PASS' if same else 'FAIL'} for {name}: rebuilt {report['rows']} rows, committed {report['reference_rows']}; "
              f"case, model, design, k, status and per-field correctness "
              + ("all equal." if same else f"differ (only rebuilt {len(report['only_rebuilt'])}, only committed {len(report['only_reference'])}, "
                                          f"mismatches { {c: len(v) for c, v in report['mismatches'].items() if c in REPLAY_SAME_COLUMNS} })."))
        extra = {c: len(v) for c, v in report["mismatches"].items() if c in REPLAY_EXTRA_COLUMNS}
        print(f"  other columns compared: {', '.join(REPLAY_EXTRA_COLUMNS)}; " + (f"rows that differ per column: {extra}." if extra else "all equal."))
    print(f"Replay made {cache.fresh_calls} model calls and sent no traces; {cache.cache_hits} cache hits. "
          f"Parser {parser}. Rebuilt files are in {out_dir} (per-call detail: {details_path(RESULTS_FILES[parser])}).")
    return bool(ok)

# %% [markdown]
# `parser_report` compares the two parsers over the cached replies. It lists every reply that parses differently, counts the chains whose later prompts change (and so would need new calls), shows what a first round of new prompts would hold, and scores the runs that need no new call. It makes no model call.

# %%
REPORT_COLUMNS = ["row_type", "case_id", "arm", "model", "design", "k", "agent_index", "is_checker", "status_first", "status_last",
                  "fields_differ", "note_differs", "downstream_prompt_changes", "replies_affected", "cases_affected",
                  "cases_to_rerun", "pending_round1", "rounds_needed", "runs_needing_command_line_call", "cases_scored_now",
                  "correct_first_same_cases", "correct_last_same_cases", "accuracy_first_all_cases", "accuracy_last_all_cases"]


def _agent_total(design, k):
    return (1 if design == "owner" else k) + (1 if design == "checker" else 0)


def parser_report(cases=None, cache_path=DATA / "cache_requests.jsonl", out_path=DATA / "parser_report.csv", arms=None, quiet=False):
    """Compare the two parsers over the cached replies. Returns (reply rows, summary rows); writes both to out_path."""
    arms = ARMS if arms is None else arms
    cases = list(cases) if cases else load_or_make_cases(DATA / "cases.jsonl", SEED, N_CASES_PER_PROCESS)
    by_version = {m["version"]: m for m in MODELS}
    base = RequestCache(cache_path, replay_only=True, backend=_replay_backend, trace=False)
    reply_rows, summary_rows = [], []
    for arm in arms:
        model_version, design, k = arm["key"]
        model = by_version[model_version]
        arm_replies, affected_cases, rerun, terra_calls = [], set(), 0, 0
        scored_now = correct_first = correct_last = 0
        total_correct_first = total_correct_last = 0
        reply_text = {}
        for case in cases:
            first = run_case(case, design, k, model, base, "first")
            first_ok = score_case(case, first)["status"] == "correct"
            total_correct_first += first_ok
            for call in first["calls"]:
                context = prompt_parts(call["request"]["prompt"])[0]
                reply_text[(case["id"], context["design"], context["team_size"], context["station_index"], context["checker"])] = call["reply"].get("text", "")
            for call in first["calls"]:
                text = call["reply"].get("text", "")
                if not parse_differs(text):
                    continue
                (obj_first, status_first), (obj_last, status_last) = parse_reply(text, "first"), parse_reply(text, "last")
                fields_a, fields_b = (obj_first or {}).get("fields", {}), (obj_last or {}).get("fields", {})
                differing = sorted(f for f in set(fields_a) | set(fields_b)
                                   if f not in fields_a or f not in fields_b or canonical(fields_a[f]) != canonical(fields_b[f]))
                note_differs = (obj_first or {}).get("note") != (obj_last or {}).get("note")
                has_next = not call["checker"] and call["station_index"] < _agent_total(design, k) - 1
                arm_replies.append({"row_type": "reply", "case_id": case["id"], "arm": arm["label"], "model": model_version, "design": design, "k": k,
                                    "agent_index": call["station_index"] + 1, "is_checker": call["checker"], "status_first": status_first,
                                    "status_last": status_last, "fields_differ": ";".join(differing), "note_differs": note_differs,
                                    "downstream_prompt_changes": bool(has_next and (differing or note_differs or status_first != status_last))})
                affected_cases.add(case["id"])
            try:
                last = run_case(case, design, k, model, base, "last")
            except AssertionError:
                rerun += 1
                continue
            scored_now += 1
            last_ok = score_case(case, last)["status"] == "correct"
            correct_first += first_ok
            correct_last += last_ok
            total_correct_last += last_ok
        # Requests the first round would send, and the rounds a chain needs if each re-run agent answers as it did before.
        sim = RequestCache(cache_path, backend=_export_backend, trace=False) if affected_cases else None
        pending_round1, rounds = 0, 0
        if affected_cases:
            affected = [c for c in cases if c["id"] in affected_cases]
            while rounds < 16:
                items, _, _, cli_blocked, runs = _collect_pending(affected, [model], [design], [k], sim, "last")
                if rounds == 0:
                    pending_round1 = len(items)
                if not items:
                    # Once every subagent round is done, these runs still wait for a new command-line (Terra) call.
                    terra_calls = sum(1 for r in runs if r[4] == "needs_command_line_call")
                    break
                rounds += 1
                for item in items:
                    context = prompt_parts(item["prompt"][len(SUBAGENT_PREFIX):])[0]
                    text = reply_text.get((context["case_id"], context["design"], context["team_size"], context["station_index"], context["checker"]), "")
                    sim.rows[item["key"]] = {"cache_key": item["key"], "request": item["request"], "response": {"text": text, "input_tokens": None, "output_tokens": None}}
            else:
                raise RuntimeError(f"{arm['label']}: chains do not finish within 16 rounds")
        n = len(cases)
        summary_rows.append({"row_type": "arm_summary", "arm": arm["label"], "model": model_version, "design": design, "k": k,
                             "replies_affected": len(arm_replies), "cases_affected": len(affected_cases), "cases_to_rerun": rerun,
                             "pending_round1": pending_round1, "rounds_needed": rounds, "runs_needing_command_line_call": terra_calls,
                             "cases_scored_now": scored_now, "correct_first_same_cases": correct_first, "correct_last_same_cases": correct_last,
                             "accuracy_first_all_cases": total_correct_first / n,
                             "accuracy_last_all_cases": total_correct_last / n if scored_now == n else ""})
        reply_rows += arm_replies
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with Path(out_path).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=REPORT_COLUMNS)
        writer.writeheader()
        writer.writerows(reply_rows + summary_rows)
    if not quiet:
        print(f"Replies that parse differently under the two parsers: {len(reply_rows)} (one row per reply and arm; a reply shared by two arms appears in both).")
        print(f"{'arm':<32}{'replies':>8}{'cases':>7}{'re-run':>8}{'round 1':>9}{'rounds':>8}{'Terra':>7}{'scored now':>12}{'first':>7}{'last':>6}")
        for r in summary_rows:
            print(f"{r['arm']:<32}{r['replies_affected']:>8}{r['cases_affected']:>7}{r['cases_to_rerun']:>8}{r['pending_round1']:>9}{r['rounds_needed']:>8}"
                  f"{r['runs_needing_command_line_call']:>7}{r['cases_scored_now']:>12}{r['correct_first_same_cases']:>7}{r['correct_last_same_cases']:>6}")
        print("re-run: cases whose chain has a prompt that is not in the cache under 'last'. round 1: new prompts the first round sends. "
              "rounds: rounds a chain needs, assuming each re-run agent answers as it did before. Terra: runs that also need a new GPT-6.1 Terra call. "
              "scored now: cases scored under 'last' from the cache; first/last: cases correct among those cases under each parser.")
        for r in summary_rows:
            if r["accuracy_last_all_cases"] != "":
                print(f"No new call needed: {r['arm']}: {round(r['accuracy_last_all_cases'] * len(cases))} of {len(cases)} correct under 'last' "
                      f"({r['accuracy_last_all_cases']:.1%}), {round(r['accuracy_first_all_cases'] * len(cases))} under 'first'.")
        print(f"Wrote {out_path}.")
    return reply_rows, summary_rows

# %% [markdown]
# The next cell is the guard for this section. It swaps the three functions that could reach a model or a server (`run_cli`, `start_tracing`, `trace_call`) for functions that record the attempt and fail, replays both parsers, and asserts afterwards that no attempt was made, that Langfuse was never started and that the rebuilt tables equal the committed ones in every column except wall-clock times and the cached-call count. The same pattern guards the analysis in section 11.

# %%
if NOTEBOOK_RUN:
    import contextlib

    CALLS_ATTEMPTED = []
    TIMING_COLUMNS = {"seconds", "model_seconds", "cached_calls"}


    @contextlib.contextmanager
    def no_model_calls():
        names = ("run_cli", "start_tracing", "trace_call")
        saved = {n: globals()[n] for n in names}

        def refuse(name):
            def blocked(*args, **kwargs):
                CALLS_ATTEMPTED.append(name)
                raise AssertionError(f"{name} was called during a replay")
            return blocked

        globals().update({n: refuse(n) for n in names})
        try:
            yield
        finally:
            globals().update(saved)


    def assert_tables_equal(rebuilt_path, committed_path):
        rebuilt = pd.read_csv(rebuilt_path, dtype=str, keep_default_na=False)
        committed = pd.read_csv(committed_path, dtype=str, keep_default_na=False)
        columns = [c for c in RESULT_COLUMNS if c not in TIMING_COLUMNS]
        key = ["case_id", "model", "design", "k"]
        rebuilt, committed = rebuilt.sort_values(key).reset_index(drop=True), committed.sort_values(key).reset_index(drop=True)
        assert len(rebuilt) == len(committed) == 640, (len(rebuilt), len(committed))
        differing = {c: int((rebuilt[c] != committed[c]).sum()) for c in columns if (rebuilt[c] != committed[c]).any()}
        assert not differing, differing
        return len(rebuilt), len(columns)


    REPLAY_STATUS = {}
    with no_model_calls():
        for parser_name in PARSERS:
            print(f"===== parser {parser_name!r} =====")
            assert replay_all(parser=parser_name), f"replay under {parser_name} does not match the committed table"
            rebuilt_path = TMP / (RESULTS_FILES[parser_name].stem + "_replay.csv")
            REPLAY_STATUS[parser_name] = assert_tables_equal(rebuilt_path, RESULTS_FILES[parser_name])
        print("\n===== which replies parse differently =====")
        REPORT_REPLIES, REPORT_SUMMARY = parser_report(out_path=TMP / "parser_report.csv")

    assert not CALLS_ATTEMPTED, CALLS_ATTEMPTED
    assert not LANGFUSE_ON and not _LANGFUSE_CHECKED
    for parser_name, (rows, columns) in REPLAY_STATUS.items():
        print(f"parser {parser_name!r}: {rows} rebuilt rows equal {RESULTS_FILES[parser_name]} in {columns} columns (timing columns left out)")
    same_report = (TMP / "parser_report.csv").read_bytes() == (DATA / "parser_report.csv").read_bytes()
    print("rebuilt parser_report.csv is byte-identical to the committed one:", same_report)
    print(f"model calls attempted during replay: {len(CALLS_ATTEMPTED)}; Langfuse started: {LANGFUSE_ON}; traces sent: 0")

# %% [markdown]
# Both rebuilt tables equal the committed ones, 640 rows each (80 cases in eight arms), with zero model calls and no trace. The parser report lists the replies that differ across the two readings: the arms in the report are the ones whose chains had a draft passed on (a reply shared by two arms, such as the owner's reply that the review arm starts from, appears under both). The re-run columns are all zero, because the cache now holds the re-run replies, so every arm replays under both rules.

# %% [markdown]
# ## 8. Offline checks of the code
#
# The experiment's code can be wrong in ways a model score would not show, so ten scripted checks run before any result is read. They use scripted agents instead of models. The oracle writes the exact answers. The careless agent reads only its visible records and form and never writes a handoff note, which shows the loss of early prose without inventing a hidden memory. The gullible agent gives the intake summary precedence over the documents. Temporary caches keep these tests out of the experiment's response cache and scored results, and the checks also cover the cache, the subagent export and import cycle, the review design and the two parsers.

# %%
def oracle_agent(case):
    def agent(prompt, model):
        context, allowed, incoming, _ = prompt_parts(prompt)
        earlier = incoming.get("fields_so_far", {})
        fields = {f: case["truth"][f] for f in allowed}
        if context["checker"]:
            fields = {f: value for f, value in fields.items() if not field_equal(f, value, earlier.get(f))}
        return canonical({"fields": fields, "note": "Scripted oracle handoff; exact answers supplied by the test."})
    return agent


def careless_agent(prompt, model):
    context, allowed, incoming, docs = prompt_parts(prompt)
    process = context["process"]
    if len(docs) == 12:
        solved = solve_documents(process, docs)
        return canonical({"fields": {f: solved[f] for f in allowed}, "note": ""})
    text = "\n".join(docs.values())
    form = incoming.get("fields_so_far", {})

    def read(label):
        m = re.search(r"^" + re.escape(label) + r": (.+)$", text, re.M)
        return m.group(1) if m else None

    # A partial visible-only solver. Unknown facts stay null, rather than reading
    # hidden params/truth, retaining a prior document or guessing an intake value.
    values = {f: None for f in allowed}
    if process == "capital":
        if "notice_amount" in allowed and read("Notice total"):
            values["notice_amount"] = money(read("Notice total"))
        if "commitment_valid" in allowed and read("Unfunded balance") and form.get("notice_amount") is not None:
            values["commitment_valid"] = Decimal(str(form["notice_amount"])) <= Decimal(read("Unfunded balance"))
        if "cad_amount" in allowed and form.get("eligible_amount") is not None:
            values["cad_amount"] = money(Decimal(str(form["eligible_amount"])) * Decimal(read("CAD per currency unit")))
        if "release_control" in allowed:
            values["release_control"] = "STANDARD"
    elif process == "credit":
        if "complete" in allowed:
            values["complete"] = read("Consent signed") == "YES" and read("Invoice attached") == "YES" and read("Registry status") == "ACTIVE"
        if "bureau_score" in allowed and read("Verified bureau score"):
            values["bureau_score"] = int(read("Verified bureau score"))
        if "conditions" in allowed:
            values["conditions"] = (["COMPLETE_FILE"] if form.get("complete") is False else []) + (["MANAGER_REVIEW"] if form.get("decision") == "REFER" else [])
    elif process == "lab":
        if "card_version" in allowed:
            values["card_version"] = read("Authoritative card version")
            values["card_valid"] = read("Service date") <= read("Coverage end") and read("Submitted version") == read("Authoritative card version")
        if "billed_to" in allowed:
            values["billed_to"] = "PATIENT"
    else:
        if "security_code" in allowed:
            values["security_code"] = read("Security identifier")
        if "eligible_accounts" in allowed:
            excluded = read("Restricted accounts").split(", ")
            values["eligible_accounts"] = [a for a in "ABC" if a not in excluded]
        if "exception_flags" in allowed:
            values["exception_flags"] = []
    return canonical({"fields": values, "note": ""})


def gullible_agent(case):
    base = oracle_agent(case)

    def agent(prompt, model):
        context, allowed, incoming, _ = prompt_parts(prompt)
        answer = json.loads(base(prompt, model))
        intake = incoming.get("intake_note", incoming.get("incoming_note", ""))
        field = case["injected_field"]
        if field and field in allowed:
            m = re.search(r"My summary has " + re.escape(field) + r": ([^\n]+)\.", intake)
            if m:
                value = m.group(1)
                answer["fields"][field] = int(value) if field == "bureau_score" else value
        # Carry the same intake summary onward, illustrating its propagation.
        answer["note"] = intake
        return canonical(answer)
    return agent

# %%
CHECK_NAMES = [
    "generators deterministic, seed-sensitive, planted and about one-quarter injected",
    "oracle scores 100% in every design and team size",
    "careless empty-note agent loses planted fact in pipeline/8 and retains it as owner",
    "gullible intake-note agent gets injected fields wrong",
    "scorer separates unreadable/wrong, code sets and cent-rounded money",
    "independent rendered-document solver matches every field for 50 seeds per process",
    "cache replay makes zero calls and identical concurrent requests run once",
    "subagent route: export, workflow files, reply and journal import (with traces) take four rounds and match the oracle run",
    "review design: agent 1 is the owner request, reviewers overwrite the record, three subagent rounds after the owner",
    "parsers: first and last read two-object replies differently; a superseded pipeline draft changes exactly its own chain, which the export, workflow and import cycle completes",
]


def selftest():
    cases = generate_cases()
    checks = []

    def check_generators():
        assert len(cases) == 4 * N_CASES_PER_PROCESS
        for process in PROCESS_NAMES:
            a, b = make_case(process, SEED), make_case(process, SEED + 1)
            assert canonical(a) == canonical(make_case(process, SEED))
            assert canonical(a["documents"]) != canonical(b["documents"])
            station_fields = [f for s in stations_for(process, 8) for f in s["fields"]]
            assert len(station_fields) == len(set(station_fields)) and set(station_fields) == set(a["truth"])
            assert 8 <= len(station_fields) <= 12
            assert all(5 <= len(t.splitlines()) <= 25 for t in a["documents"].values())
            assert 10 <= len(a["documents"]) <= 14
            assert len(a["params"]["complications"]) == DIFFICULTY
            assert len(a["intake_note"].splitlines()) in (3, 4)
            sentence = a["params"]["planted_sentence"]
            assert sum(sentence in text for text in a["documents"].values()) == 1
            early = {d for s in stations_for(process, 8)[:2] for d in s["documents"]}
            late = {d for s in stations_for(process, 8)[2:] for d in s["documents"]}
            assert "correspondence" in early and "correspondence" not in late
            assert a["planted_field"] in {f for s in stations_for(process, 8)[6:] for f in s["fields"]}
            without = {d: text.replace(sentence, "No additional arrangement was requested.") for d, text in a["documents"].items()}
            assert not field_equal(a["planted_field"], a["truth"][a["planted_field"]], solve_documents(process, without)[a["planted_field"]])
            trials = [make_case(process, SEED + i)["injected"] for i in range(400)]
            assert abs(sum(trials) / len(trials) - INJECTED_ERROR_SHARE) <= .08
        for process in PROCESS_NAMES:
            for k in (1, 2, 4, 8):
                assert set(f for s in stations_for(process, k) for f in s["fields"]) == set(make_case(process, SEED)["truth"])

    def check_oracle():
        for case in cases:
            for model in MODELS:
                for design, sizes in [("owner", [1]), ("pipeline", [1, 2, 4, 8]), ("shared", [4]), ("checker", [4])]:
                    for k in sizes:
                        result = run_case(case, design, k, model, oracle_agent(case))
                        assert score_case(case, result)["status"] == "correct", (case["id"], design, k, result)
                        expected_calls = 1 if design == "owner" else 5 if design == "checker" else k
                        assert len(result["calls"]) == expected_calls
                        if design == "checker":
                            assert result["calls"][-1]["request"]["provider"] != model["provider"]

    def check_careless():
        for case in cases:
            pipeline = score_case(case, run_case(case, "pipeline", 8, MODELS[0], careless_agent))
            owner = score_case(case, run_case(case, "owner", 1, MODELS[0], careless_agent))
            assert not pipeline["planted_correct"], case["id"]
            assert owner["planted_correct"] and owner["status"] == "correct", case["id"]

    def check_gullible():
        for process in PROCESS_NAMES:
            injected = next(make_case(process, SEED + i) for i in range(1000) if make_case(process, SEED + i)["injected"])
            for design, k in [("owner", 1), ("pipeline", 8), ("shared", 4)]:
                score = score_case(injected, run_case(injected, design, k, MODELS[0], gullible_agent(injected)))
                assert score["status"] == "wrong" and score["injected_correct"] is False, (process, design, score)

    def check_scoring():
        case = cases[0]
        assert score_case(case, {"fields": {}})["status"] == "unreadable"
        wrong = dict(case["truth"], notice_amount="0.00")
        assert score_case(case, {"fields": wrong})["status"] == "wrong"
        assert field_equal("conditions", ["A", "B"], ["B", "A", "A"])
        assert not field_equal("conditions", ["A"], "A")
        assert field_equal("notice_amount", "1.01", "1.005")
        assert not field_equal("notice_amount", "1.01", "1.004")
        assert not field_equal("notice_amount", "1.01", "NaN")
        assert not field_equal("card_valid", True, 1)
        assert parse_reply('prefix {"fields": {"x": 1}, "note": "ok"} trailing')[1] == "ok"
        for text in ("", "I cannot comply", '{"fields": [], "note": ""}', '{"fields": {}}'):
            assert parse_reply(text)[1] != "ok"
        # First complete object fails schema: do not skip it for a later usable one.
        assert parse_reply('{} {"fields": {}, "note": ""}')[1] == "non_dict_fields"
        for failure, expected_attempts in [("empty", 2), ("timeout", 2), ("bad_json", 1)]:
            hits = []

            def scripted(prompt, model):
                hits.append(model["reply_attempt"])
                if len(hits) == 1:
                    if failure == "timeout":
                        raise TimeoutError()
                    return "" if failure == "empty" else "broken"
                return oracle_agent(case)(prompt, model)

            result = run_case(case, "owner", 1, MODELS[0], scripted)
            assert len(hits) == expected_attempts
            assert score_case(case, result)["status"] == ("correct" if expected_attempts == 2 else "unreadable")
            if expected_attempts == 2:
                assert result["calls"][1]["retry"] and result["calls"][0]["request"] != result["calls"][1]["request"]
        # A later pipeline cannot change earlier fields, including a plausible error.
        def overwrite(prompt, model):
            _, allowed, _, _ = prompt_parts(prompt)
            answer = {f: case["truth"][f] for f in allowed}
            if "notice_amount" not in allowed:
                answer["notice_amount"] = "0.00"
            return canonical({"fields": answer, "note": ""})
        assert run_case(case, "pipeline", 8, MODELS[0], overwrite)["fields"]["notice_amount"] == case["truth"]["notice_amount"]
        def repairable(prompt, model):
            context, _, _, _ = prompt_parts(prompt)
            obj = json.loads(oracle_agent(case)(prompt, model))
            if context["station_index"] == 0:
                obj["fields"]["notice_amount"] = "0.00"
            return canonical(obj)
        for design in ("shared", "checker"):
            assert score_case(case, run_case(case, design, 4, MODELS[0], repairable))["status"] == "correct"
        # Parse CLI fixtures without executing any executable or making a request.
        from unittest import mock
        reply = canonical({"fields": {}, "note": "fixture"})
        claude_stdout = canonical({"result": reply, "usage": {"input_tokens": 10, "cache_read_input_tokens": 4,
                                   "cache_creation_input_tokens": 2, "output_tokens": 3}})
        codex_stdout = "\n".join([canonical({"type": "item.completed", "item": {"type": "agent_message", "text": reply}}),
                                  canonical({"type": "turn.completed", "usage": {"input_tokens": 16, "cached_input_tokens": 4, "output_tokens": 3}})])
        for model, stdout, caller in [(MODELS[0], claude_stdout, call_claude), (MODELS[1], codex_stdout, call_codex)]:
            fixture = {"stdout": stdout, "stderr": "", "error": None, "seconds": .01,
                       "transport_attempts": [{"stdout": stdout, "stderr": "", "returncode": 0, "error": None}]}
            with mock.patch.object(shutil, "which", return_value="fixture-executable"), mock.patch.dict(globals(), run_cli=lambda *args: fixture):
                parsed = caller("fixture prompt", model)
            assert parsed["text"] == reply and parsed["input_tokens"] == 16 and parsed["output_tokens"] == 3
        limited = subprocess.CompletedProcess([], 1, stdout="rate limit 429", stderr="")
        success = subprocess.CompletedProcess([], 0, stdout="ok", stderr="")
        with mock.patch.object(subprocess, "run", side_effect=[limited, limited, limited, success]) as fake, mock.patch.object(time, "sleep"):
            result = run_cli(["fixture-executable"], "fixture", clean_cli_environment())
        assert fake.call_count == 4 and len(result["transport_attempts"]) == 4 and result["error"] is None

    def check_documents():
        for process in PROCESS_NAMES:
            seen = set()
            for seed in range(SEED, SEED + 50):
                case = make_case(process, seed)
                seen.update(case["params"]["complications"])
                # Passing only detached document strings prevents access to params.
                solved = solve_documents(process, json.loads(canonical(case["documents"])))
                assert set(solved) == set(case["truth"])
                for field, truth in case["truth"].items():
                    assert field_equal(field, truth, solved[field]), (case["id"], field, truth, solved[field])
            if DIFFICULTY:
                assert seen == set(COMPLICATIONS[process]), (process, seen)

    def check_cache():
        with tempfile.TemporaryDirectory(prefix="agent-teams-selftest-") as temp:
            path = Path(temp) / "requests.jsonl"
            by_id = {c["id"]: c for c in cases}
            counters = {"count": 0}

            def scripted(prompt, model):
                counters["count"] += 1
                context, _, _, _ = prompt_parts(prompt)
                return {"text": oracle_agent(by_id[context["case_id"]])(prompt, model),
                        "input_tokens": 100, "output_tokens": 20, "seconds": .01}

            cache = RequestCache(path, backend=scripted, trace=False)
            case = cases[0]
            prompt = build_prompt(case, "owner", 1)
            with futures.ThreadPoolExecutor(max_workers=8) as pool:
                list(pool.map(lambda _: cache(prompt, MODELS[0]), range(16)))
            assert counters["count"] == cache.fresh_calls == 1
            for case in json.loads(canonical(cases[::N_CASES_PER_PROCESS])):
                for design in DESIGNS:
                    for k in design_sizes(design):
                        result = run_case(case, design, k, MODELS[0], cache)
                        assert score_case(case, result)["status"] == "correct"
            baseline = counters["count"]

            def forbidden(*args):
                raise AssertionError("Replay invoked model backend")

            replay = RequestCache(path, replay_only=True, backend=forbidden, trace=False)
            for case in cases[::N_CASES_PER_PROCESS]:
                for design in DESIGNS:
                    for k in design_sizes(design):
                        result = run_case(case, design, k, MODELS[0], replay)
                        assert score_case(case, result)["status"] == "correct"
            assert replay.fresh_calls == 0 and replay.cache_hits > 0 and counters["count"] == baseline
            try:
                replay(build_prompt(make_case("capital", 999999), "owner", 1), MODELS[0])
            except AssertionError:
                pass
            else:
                raise AssertionError("A missing cache key must fail closed")
            # Empty replies and their retry occupy distinct reproducible cache rows.
            retry_case = make_case("capital", 999998)

            def empty_then_oracle(prompt, model):
                return "" if model.get("reply_attempt", 1) == 1 else oracle_agent(retry_case)(prompt, model)

            retry_cache = RequestCache(Path(temp) / "retry.jsonl", backend=empty_then_oracle, trace=False)
            first = run_case(retry_case, "owner", 1, MODELS[0], retry_cache)
            assert score_case(retry_case, first)["status"] == "correct" and retry_cache.fresh_calls == 2
            retry_replay = RequestCache(retry_cache.path, replay_only=True, backend=forbidden, trace=False)
            second = run_case(json.loads(canonical(retry_case)), "owner", 1, MODELS[0], retry_replay)
            assert score_case(retry_case, second)["status"] == "correct" and retry_replay.fresh_calls == 0
            # Exercise both provider pools, file freezing, CSV and full-run replay.
            import contextlib
            import io
            with contextlib.redirect_stdout(io.StringIO()):
                output = Path(temp) / "results.csv"
                rows = run_all([cases[0]], [MODELS[0]], DESIGNS, output=output, cache=cache)
                frozen = load_or_make_cases(Path(temp) / "cases.jsonl", SEED, 1)
                replay_rows = run_all(frozen, [MODELS[0]], DESIGNS, output=Path(temp) / "replayed.csv", replay_check=True, cache=replay)
            assert len(rows) == len(replay_rows) == sum(len(design_sizes(d)) for d in DESIGNS)
            assert all(r["status"] == "correct" for r in replay_rows)
            assert replay.fresh_calls == 0

    def check_subagent_rounds():
        import contextlib
        import io
        model = MODELS[0]
        assert model["route"] == "subagent"
        two = [cases[0], cases[N_CASES_PER_PROCESS]]
        by_id = {c["id"]: c for c in two}
        with tempfile.TemporaryDirectory(prefix="agent-teams-subagent-") as temp:
            temp = Path(temp)
            cache_path, pending_path = temp / "cache.jsonl", temp / "pending.jsonl"
            rounds = 0
            while True:
                out = temp / f"pending_{rounds + 1}.json"
                with contextlib.redirect_stdout(io.StringIO()):
                    summary = export_pending(two, [model], ["pipeline"], [4], out, cache_path, pending_path)
                if summary["pending"] == 0:
                    break
                rounds += 1
                assert rounds <= 6, "too many rounds"
                assert summary["pending"] == 2 and summary["waiting"] == 2
                exported = json.loads(out.read_text(encoding="utf-8"))
                assert all(it["prompt"].startswith(SUBAGENT_PREFIX) and it["label"].count("-a") == 1 for it in exported)
                with contextlib.redirect_stdout(io.StringIO()):
                    written = make_workflow(out, str(temp / f"round{rounds}"), chunk=1)
                assert [n for _, n in written] == [1, 1]
                first = Path(written[0][0]).read_text(encoding="utf-8")
                assert first.startswith("export const meta = {") and first.isascii()
                both = []
                for path, _ in written:
                    text = Path(path).read_text(encoding="utf-8")
                    line = next(l for l in text.splitlines() if l.startswith("const ITEMS = "))
                    both += json.loads(line[len("const ITEMS = "):])
                assert both == exported
                parent = Path(str(temp / f"round{rounds}") + "_parent.js").read_text(encoding="utf-8")
                assert parent.startswith("export const meta = {") and "workflow({ scriptPath: p })" in parent
                listed = json.loads(next(l for l in parent.splitlines() if l.startswith("const FILES = "))[len("const FILES = "):])
                assert listed == [os.path.abspath(path).replace("\\", "/") for path, _ in written] and all("\\" not in f for f in listed)
                # A small byte limit lowers the chunk size by itself: 40 prompts per file would not fit, so each file holds one.
                with contextlib.redirect_stdout(io.StringIO()):
                    whole = make_workflow(out, str(temp / f"whole{rounds}"), chunk=40)
                    limited = make_workflow(out, str(temp / f"limited{rounds}"), chunk=40, byte_limit=Path(whole[0][0]).stat().st_size - 1)
                assert [n for _, n in whole] == [2] and [n for _, n in limited] == [1, 1]
                assert all(Path(path).stat().st_size < Path(whole[0][0]).stat().st_size for path, _ in limited)
                replies = []
                for it in exported:
                    plain = it["prompt"][len(SUBAGENT_PREFIX):]
                    case_id = prompt_parts(plain)[0]["case_id"]
                    replies.append({"key": it["key"], "text": oracle_agent(by_id[case_id])(plain, model)})
                reply_file = temp / f"replies_{rounds}.json"
                if rounds == 3:
                    # Round 3 comes back as workflow journals: started and result lines in two files, with lines to ignore.
                    run_dir = temp / "run_dir"
                    for number, it in enumerate(exported):
                        folder = run_dir / f"agent{number}"
                        folder.mkdir(parents=True)
                        rows = [{"type": "progress", "agentId": f"ag{number}"},
                                {"type": "started", "agentId": f"ag{number}", "label": it["label"]},
                                {"type": "started", "agentId": f"other{number}", "label": "not-a-pending-label"},
                                {"type": "result", "agentId": f"other{number}", "result": "reply to a label that is not pending"},
                                {"type": "result", "agentId": f"ag{number}", "result": {"not": "a string"}},
                                {"type": "result", "agentId": f"ag{number}", "result": replies[number]["text"]}]
                        (folder / "journal.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
                    sent = []

                    def fake_trace(*args, **kwargs):
                        sent.append((args, kwargs))
                    from unittest import mock
                    with contextlib.redirect_stdout(io.StringIO()), mock.patch.dict(globals(), trace_call=fake_trace, LANGFUSE_ON=True, _LANGFUSE_CHECKED=True):
                        stats = import_journal(run_dir, out, cache_path, pending_path)
                        assert stats["imported"] == 2 and stats["unknown"] == 0 and stats["traced"] == len(sent) == 2
                        again_journal = import_journal(run_dir, out, cache_path, pending_path)
                    # One trace per imported reply (start equal to end, the subagent source, a case/design/team-size session); none for cached replies.
                    assert again_journal["imported"] == 0 and again_journal["present"] == 2 and len(sent) == 2
                    assert all(a[5] == a[6] and k["metadata"] == {"source": "claude-code-subagent"} and k["session_id"].count("/") == 2 for a, k in sent)
                    assert sorted(a[0] for a, _ in sent) == sorted(it["key"] for it in exported)
                    continue
                if rounds % 2:
                    reply_file.write_text(json.dumps(replies), encoding="utf-8")
                else:
                    reply_file.write_text(json.dumps({"event": "result", "result": json.dumps(replies)}) + "\n", encoding="utf-8")
                with contextlib.redirect_stdout(io.StringIO()):
                    stats = import_replies([reply_file], cache_path, pending_path, trace=False)
                assert stats["imported"] == 2 and stats["unknown"] == 0
            assert rounds == 4, rounds
            assert summary["complete"] == 2 and summary["waiting"] == 0
            with contextlib.redirect_stdout(io.StringIO()):
                again = import_replies([temp / "replies_1.json"], cache_path, pending_path, trace=False)
            assert again["imported"] == 0 and again["present"] == 2
            none = {model["version"]: None}
            with contextlib.redirect_stdout(io.StringIO()):
                got = run_all(two, [model], ["pipeline"], output=temp / "results.csv", cache=RequestCache(cache_path, trace=False),
                              team_sizes=[4], overheads=none)

                def oracle_backend(prompt, m):
                    context = prompt_parts(prompt)[0]
                    return oracle_agent(by_id[context["case_id"]])(prompt, m)
                want = run_all(two, [model], ["pipeline"], output=temp / "direct.csv", cache=RequestCache(temp / "direct_cache.jsonl", backend=oracle_backend, trace=False),
                               team_sizes=[4], overheads=none)
            key = lambda r: r["case_id"]
            got, want = sorted(got, key=key), sorted(want, key=key)
            assert len(got) == len(want) == 2
            for a, b in zip(got, want):
                assert a["final_fields"] == b["final_fields"] and a["status"] == b["status"] == "correct"
                assert a["task_chars"] == b["task_chars"] > 0 and a["input_tokens"] is None

    def check_review():
        import contextlib
        import io
        model = MODELS[0]
        two = [cases[0], cases[N_CASES_PER_PROCESS]]
        by_id = {c["id"]: c for c in two}

        def recording(case, base):
            seen = []

            def agent(prompt, m):
                seen.append((prompt, make_request(prompt, m)))
                return base(prompt, m)
            return agent, seen

        for case in two:
            # The first request is the owner request, byte for byte, so the owner's cached reply is reused.
            owner_agent, owner_seen = recording(case, oracle_agent(case))
            run_case(case, "owner", 1, model, owner_agent)
            agent, seen = recording(case, oracle_agent(case))
            result = run_case(case, "review", 4, model, agent)
            assert len(seen) == 4 and seen[0][1] == owner_seen[0][1] and request_key(seen[0][1]) == request_key(owner_seen[0][1])
            assert score_case(case, result)["status"] == "correct"
            for i, (prompt, _) in enumerate(seen[1:], 1):
                context, allowed, incoming, docs = prompt_parts(prompt)
                assert context == {"case_id": case["id"], "process": case["process"], "design": "review", "team_size": 4,
                                   "station_index": i, "checker": False}
                assert set(allowed) == set(case["truth"]) and len(docs) == 12 and set(incoming) == {"intake_note", "fields_so_far", "earlier_records"}
                assert len(incoming["earlier_records"]) == i and set(incoming["fields_so_far"]) == set(case["truth"])
                assert f"You are reviewer {i} of 3, checking a case file that one colleague completed" in prompt
                assert "all of which you must return: " + ", ".join(case["truth"]) in prompt.replace(", ".join(allowed), ", ".join(case["truth"]))
        for case in cases:
            assert score_case(case, run_case(case, "review", 4, model, oracle_agent(case)))["status"] == "correct", case["id"]
        # An owner mistake is repaired by a reviewer; a reviewer that omits a field leaves the earlier value in place.
        case = two[0]
        target = next(iter(case["truth"]))
        wrong = "ZZ"

        def faulty(prompt, m):
            answer = json.loads(oracle_agent(case)(prompt, m))
            if prompt_parts(prompt)[0]["design"] == "owner":
                answer["fields"][target] = wrong
            return canonical(answer)
        result = run_case(case, "review", 4, model, faulty)
        assert result["fields"][target] == case["truth"][target] and score_case(case, result)["status"] == "correct"
        assert prompt_parts(result["calls"][1]["request"]["prompt"])[2]["fields_so_far"][target] == wrong

        def silent(prompt, m):
            answer = json.loads(faulty(prompt, m))
            if prompt_parts(prompt)[0]["design"] == "review":
                answer["fields"] = {}
            return canonical(answer)
        result = run_case(case, "review", 4, model, silent)
        assert result["fields"][target] == wrong and score_case(case, result)["status"] == "wrong"

        def absent(prompt, m):
            answer = json.loads(oracle_agent(case)(prompt, m))
            answer["fields"].pop(target)
            return canonical(answer)
        result = run_case(case, "review", 4, model, absent)
        assert score_case(case, result)["status"] == "unreadable" and any("missing_scored_fields" in r for r in result["unreadable_reasons"])
        with tempfile.TemporaryDirectory(prefix="agent-teams-review-") as temp:
            temp = Path(temp)
            cache_path, pending_path = temp / "cache.jsonl", temp / "pending.jsonl"

            def cycle(designs, tag):
                rounds = 0
                while True:
                    out = temp / f"pending_{tag}{rounds + 1}.json"
                    with contextlib.redirect_stdout(io.StringIO()):
                        summary = export_pending(two, [model], designs, [4], out, cache_path, pending_path)
                    if summary["pending"] == 0:
                        return rounds, summary
                    rounds += 1
                    assert rounds <= 6 and summary["pending"] == 2
                    exported = json.loads(out.read_text(encoding="utf-8"))
                    if designs == ["review"]:
                        assert sorted(it["label"] for it in exported) == sorted(f"{c['id']}-review4-a{rounds}" for c in two)
                    with contextlib.redirect_stdout(io.StringIO()):
                        make_workflow(out, str(temp / f"round{tag}{rounds}"), chunk=1)
                    replies = [{"key": it["key"], "text": oracle_agent(by_id[prompt_parts(it["prompt"][len(SUBAGENT_PREFIX):])[0]["case_id"]])(it["prompt"][len(SUBAGENT_PREFIX):], model)} for it in exported]
                    reply_file = temp / f"replies_{tag}{rounds}.json"
                    reply_file.write_text(json.dumps(replies), encoding="utf-8")
                    with contextlib.redirect_stdout(io.StringIO()):
                        import_replies([reply_file], cache_path, pending_path, trace=False)

            owner_rounds, _ = cycle(["owner"], "o")
            assert owner_rounds == 1
            review_rounds, summary = cycle(["review"], "r")
            assert review_rounds == 3 and summary["complete"] == 2 and summary["waiting"] == 0
            # A limited run keeps rows it does not redo.
            none = {model["version"]: None}
            output = temp / "results.csv"
            with contextlib.redirect_stdout(io.StringIO()):
                first = run_all(two, [model], ["owner"], output=output, cache=RequestCache(cache_path, trace=False), overheads=none)
                second = run_all(two, [model], ["review"], output=output, cache=RequestCache(cache_path, trace=False), overheads=none)
            with output.open(newline="", encoding="utf-8") as stream:
                kept = [(r["case_id"], r["design"], r["k"], r["status"]) for r in csv.DictReader(stream)]
            assert len(first) == len(second) == 2 and len(kept) == 4
            assert {(d, k) for _, d, k, _ in kept} == {("owner", "1"), ("review", "4")} and all(s == "correct" for *_, s in kept)
            assert all(r["calls"] == 4 and r["cached_calls"] == 4 for r in second)

    def check_parsers():
        import contextlib
        import io
        obj1 = canonical({"fields": {"a": 1}, "note": "draft"})
        obj2 = canonical({"fields": {"a": 2}, "note": "final"})
        two_objects = obj1 + "\nCorrection: the JSON above is superseded\n" + obj2
        assert parse_reply(two_objects, "first")[0]["note"] == "draft" and parse_reply(two_objects, "last")[0]["note"] == "final"
        assert parse_differs(two_objects)
        # One object, nested objects, an object without "fields" and a bare first object read the same under both parsers.
        nested = canonical({"fields": {"a": {"b": 1}}, "note": "n"})
        for text in (obj1, nested, "prefix " + obj1 + " trailing", obj1 + ' {"x": 1}', '{"x": 1} ' + obj2, '{} ' + obj1, "", "no json here", '{"fields": 3} ' + obj2):
            assert parse_reply(text, "first") == parse_reply(text, "last") or text == '{"fields": 3} ' + obj2, text
        assert parse_reply('{"fields": 3} ' + obj2, "first")[1] == "non_dict_fields" and parse_reply('{"fields": 3} ' + obj2, "last")[0]["note"] == "final"
        try:
            parse_reply(obj1, "middle")
        except ValueError:
            pass
        else:
            raise AssertionError("an unknown parser must raise")
        model = MODELS[0]
        two = [cases[0], cases[N_CASES_PER_PROCESS]]
        by_id = {c["id"]: c for c in two}

        def superseding(prompt, m):
            context = prompt_parts(prompt)[0]
            answer = json.loads(oracle_agent(by_id[context["case_id"]])(prompt, m))
            if context["station_index"] != 0:
                return canonical(answer)
            field = next(iter(answer["fields"]))
            draft = {"fields": dict(answer["fields"], **{field: "ZZ"}), "note": "draft note"}
            return canonical(draft) + "\nCorrection: the JSON above is superseded\n" + canonical(answer)

        with tempfile.TemporaryDirectory(prefix="agent-teams-parser-") as temp:
            temp = Path(temp)
            cache_path, pending_path = temp / "cache.jsonl", temp / "pending.jsonl"
            seed_cache = RequestCache(cache_path, backend=superseding, trace=False)
            first_runs = {c["id"]: run_case(c, "pipeline", 4, model, seed_cache, "first") for c in two}
            # Under "first" the draft is scored and handed on; the parser is not part of any cache key.
            assert all(score_case(c, first_runs[c["id"]])["status"] == "wrong" for c in two) and seed_cache.fresh_calls == 8
            replay = RequestCache(cache_path, replay_only=True, backend=lambda *a: None, trace=False)
            for c in two:
                again = run_case(c, "pipeline", 4, model, replay, "first")
                assert [x["request"] for x in again["calls"]] == [x["request"] for x in first_runs[c["id"]]["calls"]]
                try:
                    run_case(c, "pipeline", 4, model, replay, "last")
                except AssertionError:
                    pass
                else:
                    raise AssertionError("under last the chain after the superseded draft must need new requests")
            arm = {"key": (model["version"], "pipeline", 4), "label": "Pipeline of 4", "family": "pipeline", "control": False}
            report_rows, summary = parser_report(two, cache_path, temp / "report.csv", [arm], quiet=True)
            row = summary[0]
            assert len(report_rows) == 2 and all(r["agent_index"] == 1 and r["downstream_prompt_changes"] and r["fields_differ"] for r in report_rows)
            assert (row["replies_affected"], row["cases_affected"], row["cases_to_rerun"], row["pending_round1"], row["rounds_needed"]) == (2, 2, 2, 2, 3)
            assert row["cases_scored_now"] == 0 and row["accuracy_last_all_cases"] == ""
            rounds = 0
            while True:
                out = temp / f"pending_{rounds + 1}.json"
                with contextlib.redirect_stdout(io.StringIO()):
                    summary = export_pending(two, [model], ["pipeline"], [4], out, cache_path, pending_path, parser="last")
                if summary["pending"] == 0:
                    break
                rounds += 1
                assert rounds <= 5 and summary["pending"] == 2, rounds
                exported = json.loads(out.read_text(encoding="utf-8"))
                # Exactly the changed chain: agent 2, then 3, then 4 of each case, none of them in the cache yet.
                assert sorted(it["label"] for it in exported) == sorted(f"{c['id']}-pipeline4-a{rounds}" for c in two)
                assert not any(it["key"] in seed_cache.rows for it in exported)
                with contextlib.redirect_stdout(io.StringIO()):
                    make_workflow(out, str(temp / f"round{rounds}"), chunk=1)
                replies = [{"key": it["key"], "text": superseding(it["prompt"][len(SUBAGENT_PREFIX):], model)} for it in exported]
                reply_file = temp / f"replies_{rounds}.json"
                reply_file.write_text(json.dumps(replies), encoding="utf-8")
                with contextlib.redirect_stdout(io.StringIO()):
                    stats = import_replies([reply_file], cache_path, pending_path, trace=False)
                assert stats["imported"] == 2
            assert rounds == 3 and summary["complete"] == 2 and summary["waiting"] == 0
            replay = RequestCache(cache_path, replay_only=True, backend=lambda *a: None, trace=False)
            for c in two:
                last = run_case(c, "pipeline", 4, model, replay, "last")
                assert score_case(c, last)["status"] == "correct"
                # The first agent's own request is identical; every later prompt differs because it carries the final answer.
                assert last["calls"][0]["request"] == first_runs[c["id"]]["calls"][0]["request"]
                for i in (1, 2, 3):
                    assert last["calls"][i]["request"]["prompt"] != first_runs[c["id"]]["calls"][i]["request"]["prompt"]
                assert prompt_parts(last["calls"][1]["request"]["prompt"])[2]["incoming_note"] != "draft note"
                assert prompt_parts(first_runs[c["id"]]["calls"][1]["request"]["prompt"])[2]["incoming_note"] == "draft note"
            # Parser last copies unchanged runs: with no reply that parses differently, every run is reused as it was.
            assert not any(parse_differs(call["reply"]["text"]) for call in last["calls"][1:])


    for number, (name, test) in enumerate(zip(CHECK_NAMES, [check_generators, check_oracle, check_careless, check_gullible, check_scoring, check_documents, check_cache, check_subagent_rounds, check_review, check_parsers]), 1):
        try:
            test()
            passed, detail = True, ""
        except Exception as exc:
            passed, detail = False, f" ({type(exc).__name__}: {exc})"
            if os.environ.get("SELFTEST_TRACEBACK"):
                import traceback
                traceback.print_exc()
        print(f"{'PASS' if passed else 'FAIL'} {number}. {name}{detail}", flush=True)
        checks.append(passed)
    return all(checks)

# %% [markdown]
# The next cell runs all ten checks. The independent solver check runs over 50 seeds for each process. The whole run takes a few seconds, so the notebook runs the full version. Check 8 mocks the trace function, so no trace reaches Langfuse.

# %%
if NOTEBOOK_RUN:
    assert selftest(), "a selftest check failed"
    assert not LANGFUSE_ON and not _LANGFUSE_CHECKED

# %% [markdown]
# ## 9. How the study got here
#
# The design, measures and expectations were written down on 18 November 2026 before any model call. In the first test the single owner's prompt said to return "only your owned fields", and Sonnet answered as station 1; every prompt was rewritten to list every field to return, and those replies were discarded.
#
# A calibration run on 24 separate, unscored cases aimed for single-owner accuracy of 50% to 90%. With two complications per case the owner got 22 of 24 and the pipeline of 4 got 20; with four, the owner again got 22 and the pipeline of 4 fell to 15. The scored run uses four, with the owner at 92%, one case above the band, so comparisons against one owner sit near its ceiling.
#
# The plan also ran every design with Terra as the team; before the scored run the repo owner limited teams to Sonnet. Afterwards two results could not be read as effects of design, and the repo owner agreed to the two control arms (section 13), run on 20 November.
#
# While this write-up was drafted, the per-call records showed agents writing an answer, then a correction such as "the JSON above is superseded by this one" and a second answer; the first-answer rule had scored the draft and, in pipelines, passed it on. On 21 November the final-answer reading was added and the 23 chains where a draft had been passed on were re-run from the next agent (62 new Sonnet calls over six rounds, 3 new Terra checker calls); other runs were carried over.
#
# The calibration tables are in `data/`. The next cell counts them.

# %%
if NOTEBOOK_RUN:
    for name, label in (("calibration_difficulty2_sonnet.csv", "2 complications per case"), ("calibration_results.csv", "4 complications per case (scored run setting)")):
        table = pd.read_csv(DATA / name)
        counts = table.groupby(["design", "k"])["status"].value_counts().unstack(fill_value=0)
        print(f"{label}: 24 separate calibration cases, Sonnet")
        print(counts.to_string(), "\n")

# %% [markdown]
# With two complications per case the owner got 22 of 24 and the pipeline of 4 got 20 (one unreadable); with four, the owner again got 22 and the pipeline of 4 got 15 (one unreadable). The scored run uses four complications per case.

# %% [markdown]
# ## 10. One case from start to finish
#
# `credit-4802` is traced through the single owner because three later examples use it too. Lines from its documents:

# %%
if NOTEBOOK_RUN:
    case = CASES_BY_ID["credit-4802"]
    for doc_id in sorted(case["documents"]):
        if doc_id != "policy":
            print(f"[{doc_id}]")
            for line in case["documents"][doc_id].splitlines():
                if not line.startswith("Record status:"):
                    print(line)

# %% [markdown]
# The 8,088-character prompt states the task and role, lists all eight stations, the allowed fields with their formats, the 12 documents and the intake note:
#
# > Complete this fictional business case using the attached policy and source records, resolving any conflict in favour of signed records over the colleague's intake summary. [...] You are the only person working this case. [...] Your fields, all of which you must return: complete, bureau_score, exposure_cad, decision, approved_amount, term_months, rate_tier, authority, conditions, approval_expiry
#
# The policy gives the answer step by step. Consent is unsigned, so the file is incomplete. The score is 691, as the intake note says. Exposure is 190,000.00 x 1.0000 + 230,000.00 = 420,000.00. Bankruptcy is a hard decline that outranks the referral rules, so the decision is DECLINE with no amount, term or rate tier. Exposure over 150,000 puts authority with a MANAGER. Conditions are COMPLETE_FILE plus ENV_UNDERTAKING from the email, with no MANAGER_REVIEW because the file is declined, not referred. The offer expires 10 business days after Wednesday 13 May: 27 May.

# %%
if NOTEBOOK_RUN:
    prompt = DEMO_RUNS["One owner"]["calls"][0]["request"]["prompt"][len(SUBAGENT_PREFIX):]
    print(f"owner prompt: {len(prompt):,} characters (without the standing subagent prefix)")
    for marker in ("Complete this fictional", "You are the only person", "Your fields, all of which"):
        start = prompt.index(marker)
        print(" ...", prompt[start:start + 200].replace("\n", " "), "...")
    print("\nexact answer:", json.dumps(case["truth"]))

# %% [markdown]
# The owner's 780-character reply holds one object, so both readings agree:

# %%
if NOTEBOOK_RUN:
    reply = DEMO_RUNS["One owner"]["calls"][0]["reply"]["text"]
    print(f"{len(reply)} characters, {len(_json_objects(reply))} JSON object\n{reply}")

# %%
if NOTEBOOK_RUN:
    final = pd.read_csv(RESULTS_FILES["last"])
    first = pd.read_csv(RESULTS_FILES["first"])
    one = final[final["case_id"] == "credit-4802"].merge(first[first["case_id"] == "credit-4802"][["model", "design", "k", "status"]],
                                                        on=["model", "design", "k"], suffixes=("_final", "_first"))
    one["arm"] = [ARM_BY_KEY[(m, d, k)]["label"] for m, d, k in zip(one["model"], one["design"], one["k"])]
    one["MANAGER_REVIEW in conditions"] = ["MANAGER_REVIEW" in json.loads(f).get("conditions", []) for f in one["final_fields"]]
    one["fields correct"] = [f"{sum(json.loads(p).values())} of {len(json.loads(p))}" for p in one["per_field_correct"]]
    print(one[["arm", "status_final", "status_first", "fields correct", "MANAGER_REVIEW in conditions", "task_chars"]].to_string(index=False))
    print("\nunreadable reasons, pipeline of 2:", one[one["arm"] == "Pipeline of 2"]["unreadable_reasons"].iloc[0])
    owner_row = one[one["arm"] == "One owner"].iloc[0]
    print(f"owner work: {owner_row['prompt_chars']:,} + {owner_row['reply_chars']:,} = {owner_row['task_chars']:,} characters")

# %% [markdown]
# All 10 fields match (the conditions are in a different order, which is allowed), so the case is fully correct, the planted fact is kept, and the work is 8,088 + 780 = 8,868 characters. The pipeline of 2 was unreadable on this case (section 17) and the pipelines of 4 and 8 added MANAGER_REVIEW (section 18); the other arms were correct.

# %% [markdown]
# ## 11. Computing the tables and figures
#
# Accuracy counts complete cases with unreadable work in the denominator. Accuracy on readable cases answers a separate question about replies that could be scored. Each interval resamples whole cases 4,000 times with one fixed seed, which keeps paired comparisons paired. The scaling step treats the single owner as a one-agent pipeline: output is k times accuracy divided by the mean characters of prompt and reply per case, and the exponent is the slope of log output on log k. A scale with zero output has no logarithm, so the code reports it instead of assigning an exponent. Eight arms are compared on the same 80 cases; the last two are control arms added after the main run. Tables go to `data/`, figures (PNG only) to `figures/`, and every number in a figure title is printed at the end of the analysis.
#
# The cells below hold the single matplotlib style block, the resampling and table functions, the planted-fact helpers and the `analyse` function that draws all eleven figures. In the planted-fact trace, a handoff note counts as mentioning the planted sentence when it contains at least half of the sentence's distinctive words (words other than common stop words and speech verbs). That is a keyword match, not a reading of the note.

# %%
def apply_plot_style(plt):
    # The only matplotlib style block in the experiment.
    plt.rcParams.update({"figure.dpi": 160, "savefig.dpi": 160, "font.size": 10.5,
                         "figure.facecolor": PAPER, "axes.facecolor": PAPER, "savefig.facecolor": PAPER,
                         "text.color": INK, "axes.labelcolor": INK, "axes.edgecolor": MUTED, "axes.titlecolor": INK,
                         "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.grid": True, "grid.color": GUIDE, "grid.linewidth": 0.8, "axes.axisbelow": True,
                         "legend.frameon": False, "hatch.linewidth": 1.1, "axes.prop_cycle": plt.cycler(color=COLORS)})


def resample_index(n, np, seed=SEED):
    """Case indices for every bootstrap interval in the script: BOOTSTRAPS resamples of n cases, one fixed seed."""
    return np.random.default_rng(seed).integers(0, n, size=(BOOTSTRAPS, n))


def bootstrap_mean(values, np, seed=SEED):
    """95% percentile interval of a mean over case resamples (the only interval function for means)."""
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if not len(values):
        return math.nan, math.nan
    draws = values[resample_index(len(values), np, seed)].mean(axis=1)
    return tuple(float(v) for v in np.quantile(draws, [0.025, 0.975]))

# %%
def load_results(path, pd):
    path = Path(path)
    if not path.exists() or not path.stat().st_size:
        print(f"Missing scored results: {path}. No accuracy or scaling estimate is available.")
        return pd.DataFrame()
    try:
        data = pd.read_csv(path)
    except (pd.errors.EmptyDataError, pd.errors.ParserError) as exc:
        print(f"Results file has no readable complete table; no estimates available: {exc}")
        return pd.DataFrame()
    required = {"case_id", "process", "model", "design", "k", "status"}
    absent = required - set(data.columns)
    if absent:
        print("Missing required result columns: " + ", ".join(sorted(absent)))
        return pd.DataFrame()
    bad = ~data["status"].isin(["correct", "wrong", "unreadable"])
    if bad.any():
        print(f"Ignoring {int(bad.sum())} incomplete rows without a scored status.")
        data = data[~bad].copy()
    for col in ("k", "input_tokens", "output_tokens", "seconds"):
        if col not in data:
            print(f"Missing {col}: related estimates will be unavailable.")
            data[col] = float("nan")
        data[col] = pd.to_numeric(data[col], errors="coerce")
    for col in ("planted_correct", "injected_correct", "injected"):
        if col not in data:
            print(f"Missing {col}: handoff estimates may be unavailable.")
            data[col] = float("nan")
        else:
            data[col] = data[col].map(lambda x: 1.0 if str(x).lower() in ("true", "1", "1.0") else
                                    0.0 if str(x).lower() in ("false", "0", "0.0") else float("nan"))
    if "case_hash" not in data:
        # Old/partial files can still display unpaired accuracy; do not claim pairing.
        data["case_hash"] = None
        print("Missing case_hash: paired differences and scaling cannot verify identical inputs.")
    identities = ["case_id", "process", "model", "design", "k"]
    if data.duplicated(identities).any():
        print("Duplicate result identities found; retaining their final recorded rows.")
        data = data.drop_duplicates(identities, keep="last")
    data = data.dropna(subset=["case_id", "process", "model", "design", "k"])
    data["correct"] = (data["status"] == "correct").astype(float)
    data["label"] = data["design"] + "/" + data["k"].astype(int).astype(str)
    data["arm"] = [ARM_BY_KEY[(m, d, int(k))]["label"] if (m, d, int(k)) in ARM_BY_KEY else f"{m} {d}/{int(k)}"
                   for m, d, k in zip(data["model"], data["design"], data["k"])]
    if "task_input_tokens" not in data:
        print("Missing task_input_tokens: token estimates use raw input tokens, overhead included.")
        data["task_input_tokens"] = data["input_tokens"]
    data["task_input_tokens"] = pd.to_numeric(data["task_input_tokens"], errors="coerce")
    for col in ("prompt_chars", "reply_chars", "task_chars"):
        data[col] = pd.to_numeric(data[col], errors="coerce") if col in data else float("nan")
    if data["task_chars"].isna().all():
        print("Missing task_chars: work-per-case estimates and scaling are unavailable.")
    data["raw_tokens"] = data["input_tokens"] + data["output_tokens"]
    data["tokens"] = data["task_input_tokens"] + data["output_tokens"]  # task tokens: overhead removed
    return data


def accuracy_table(data, pd, np, by_process=False):
    keys = ["model", "design", "k"] + (["process"] if by_process else [])
    rows = []
    for group_key, group in data.groupby(keys, sort=True):
        row = dict(zip(keys, group_key))
        n = len(group)
        readable = group["status"] != "unreadable"
        low, high = bootstrap_mean(group["correct"], np)
        injected = group[group["injected"] == 1]
        arm = ARM_BY_KEY.get((row["model"], row["design"], int(row["k"])))
        row.update(arm=arm["label"] if arm else "", n=n, correct=int(group["correct"].sum()), wrong=int((group["status"] == "wrong").sum()),
                   unreadable=int((~readable).sum()), accuracy=group["correct"].mean(), low=low, high=high,
                   readable_accuracy=group.loc[readable, "correct"].mean() if readable.any() else math.nan,
                   planted_n=int(group["planted_correct"].notna().sum()), planted_correct=int(group["planted_correct"].sum()),
                   planted_survival=group["planted_correct"].mean(),
                   injected_n=len(injected), injected_catch=injected["injected_correct"].mean(),
                   input_tokens_per_case=group["input_tokens"].mean(), task_input_tokens_per_case=group["task_input_tokens"].mean(),
                   output_tokens_per_case=group["output_tokens"].mean(),
                   task_chars_per_case=group["task_chars"].mean(), prompt_chars_per_case=group["prompt_chars"].mean(),
                   reply_chars_per_case=group["reply_chars"].mean(),
                   tokens_per_case=group["tokens"].mean(), raw_tokens_per_case=group["raw_tokens"].mean(),
                   seconds_per_case=group["seconds"].mean())
        row["planted_low"], row["planted_high"] = bootstrap_mean(group["planted_correct"], np)
        row["catch_low"], row["catch_high"] = bootstrap_mean(injected["injected_correct"], np)
        rows.append(row)
    table = pd.DataFrame(rows)
    if table.empty:
        return table
    # Stable order for tables and charts: the arms in the order of ARMS, then anything else.
    order = {a["key"]: i for i, a in enumerate(ARMS)}
    rank = [order.get((m, d, int(k)), len(order)) for m, d, k in zip(table["model"], table["design"], table["k"])]
    table = table.assign(_rank=rank).sort_values(["_rank"] + (["process"] if by_process else []), kind="stable")
    return table.drop(columns="_rank").reset_index(drop=True)


def paired_differences(data, pd, np):
    """Difference in the share of cases fully correct, first arm minus second, on the same cases."""
    rows = []
    for left, right in PAIRS:
        a_arm, b_arm = ARM_BY_LABEL[left], ARM_BY_LABEL[right]
        a = data[data["arm"] == left].dropna(subset=["case_hash"])
        b = data[data["arm"] == right].dropna(subset=["case_hash"])
        paired = a.merge(b, on=["case_id", "process", "case_hash"], suffixes=("_a", "_b"))
        if paired.empty:
            print(f"Missing verified case pairs: {left} minus {right}.")
            continue
        delta = paired["correct_a"] - paired["correct_b"]
        lo, hi = bootstrap_mean(delta, np)
        rows.append({"comparison": f"{left} minus {right}", "first": left, "second": right, "n_pairs": len(delta),
                     "first_only_correct": int(((paired["correct_a"] == 1) & (paired["correct_b"] == 0)).sum()),
                     "second_only_correct": int(((paired["correct_a"] == 0) & (paired["correct_b"] == 1)).sum()),
                     "difference": float(delta.mean()), "low": lo, "high": hi,
                     "first_family": a_arm["family"], "first_control": a_arm["control"]})
    return pd.DataFrame(rows)


def scaling_fit(data, pd, np):
    rows, points = [], []
    pipeline_models = sorted(data.loc[data["design"] == "pipeline", "model"].unique())
    for model, group in data[data["model"].isin(pipeline_models)].groupby("model"):
        subset = group[((group["design"] == "pipeline") & group["k"].isin([2, 4, 8])) | (group["design"] == "owner")].copy()
        subset.loc[subset["design"] == "owner", "k"] = 1
        if set(subset["k"].unique()) != {1, 2, 4, 8}:
            print(f"Scaling missing one or more sizes 1,2,4,8 for {model}; owner supplies k=1.")
            continue
        subset = subset.dropna(subset=["case_hash", "task_chars"])
        # Only complete, identical-input panels enter both the fit and its resamples.
        counts = subset.groupby(["case_id", "case_hash"])["k"].nunique()
        valid = counts[counts == 4].index
        if not len(valid):
            print(f"Scaling has no complete verified four-size case panel for {model}.")
            continue
        panel = subset.set_index(["case_id", "case_hash"]).loc[valid].reset_index()
        correct = panel.pivot(index=["case_id", "case_hash"], columns="k", values="correct").reindex(columns=[1, 2, 4, 8]).to_numpy()
        tokens = panel.pivot(index=["case_id", "case_hash"], columns="k", values="task_chars").reindex(columns=[1, 2, 4, 8]).to_numpy()
        ks = np.array([1, 2, 4, 8], dtype=float)
        raw_means = {int(k): float(v) for k, v in panel.groupby("k")["raw_tokens"].mean().items()}
        token_means = {int(k): float(v) for k, v in panel.groupby("k")["tokens"].mean().items()}

        def fit(c, t):
            mean_t = t.mean(axis=0)
            if np.any(mean_t <= 0):
                return math.nan, np.full(4, np.nan)
            output = ks * c.mean(axis=0) / mean_t
            slope = float(np.polyfit(np.log(ks), np.log(output), 1)[0]) if np.all(output > 0) else math.nan
            return slope, output

        slope, output = fit(correct, tokens)
        slopes = []
        for ids in resample_index(len(correct), np):
            value, _ = fit(correct[ids], tokens[ids])
            slopes.append(value)
        finite = np.asarray(slopes)[np.isfinite(slopes)]
        lo, hi = np.quantile(finite, [0.025, 0.975]) if len(finite) else (math.nan, math.nan)
        undefined = BOOTSTRAPS - len(finite)
        if not math.isfinite(slope) or undefined:
            print(f"{model}: scaling slope {slope}; {undefined}/{BOOTSTRAPS} bootstrap fits undefined (zero accuracy/characters). Intervals use finite draws only.")
        rows.append({"model": model, "n_cases": len(correct), "slope": slope, "low": lo, "high": hi,
                     "undefined_bootstraps": undefined, "bootstrap_draws": BOOTSTRAPS})
        for k, value, accuracy, char_mean in zip(ks.astype(int), output, correct.mean(axis=0), tokens.mean(axis=0)):
            points.append({"model": model, "k": k, "output": value, "accuracy": accuracy,
                           "chars_per_case": char_mean, "tokens_per_case": token_means[int(k)], "raw_tokens_per_case": raw_means[int(k)],
                           "n_cases": len(correct)})
    return pd.DataFrame(rows), pd.DataFrame(points)

# %%
# Planted fact: does a handoff note still carry it? A keyword match, not a reading of the note.
_STOPWORDS = set("""a about all also an and any are as at be been but by can did do does for from had has have he her his if in into is it
its may more most must no not of on one only or our own she should so some such than that the their them then there these they this those to
too under up upon was we were what when which who will with would you your""".split())
_SPEECH = set("asked ask mentioned mention noted note said say requested request told agreed agree confirmed wants wanted".split())


def _stem(word):
    return word[:-1] if len(word) > 4 and word.endswith("s") else word


def distinctive_words(sentence):
    """Content words of the planted sentence (the generator's `params.planted_sentence`, which --show-case prints
    as PLANTED FACT), without stop words and speech verbs."""
    words = []
    for word in re.findall(r"[a-z0-9_]+", sentence.lower()):
        stem = _stem(word)
        if len(word) >= 3 and word not in _STOPWORDS and word not in _SPEECH and stem not in words:
            words.append(stem)
    return words


def mentions_planted(note, sentence):
    """True when the note contains at least half of the distinctive words of the planted sentence."""
    words = distinctive_words(sentence)
    have = {_stem(w) for w in re.findall(r"[a-z0-9_]+", str(note).lower())}
    return bool(words) and sum(w in have for w in words) >= math.ceil(len(words) / 2)


def load_details(path):
    """Per-call records: {(model, design, k): {case_id: result}}."""
    records = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            d = json.loads(line)
            records.setdefault((d["model"], d["design"], int(d["k"])), {})[d["case_id"]] = d["result"]
    return records


def pass_counts(records, cases_by_id, key, passes=4):
    """Cases fully correct after each pass, applying each pass's accepted fields in order."""
    totals = [0] * passes
    for case_id, result in records[key].items():
        case = cases_by_id[case_id]
        fields = {}
        for i, note in enumerate(sorted(result["notes"], key=lambda n: n["station_index"])[:passes]):
            fields.update({f: v for f, v in note["fields"].items() if f in case["truth"]})
            totals[i] += all(f in fields and field_equal(f, t, fields[f]) for f, t in case["truth"].items())
    return totals


def handoff_series(records, cases_by_id, key):
    """Share of cases whose outgoing note at each handoff still mentions the planted fact (keyword match)."""
    k = key[2]
    hits, cases = [0] * (k - 1), 0
    for case_id, result in records[key].items():
        sentence = cases_by_id[case_id]["params"]["planted_sentence"]
        notes = {n["station_index"]: n["note"] for n in result["notes"]}
        cases += 1
        for i in range(k - 1):
            hits[i] += mentions_planted(notes.get(i, ""), sentence)
    return [h / cases for h in hits], hits, cases

# %%
def analyse(paths=None, figure_dir=FIGURES, table_dir=DATA, primary=None):
    """Tables for every parser whose results file exists (each table has a `parser` column); figures for `primary`
    (default PRIMARY_PARSER), falling back to "first" when the "last" results are missing or incomplete."""
    try:
        import textwrap
        import numpy as np
        import pandas as pd
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.patches import Patch, Rectangle
        from matplotlib.lines import Line2D
        from matplotlib.ticker import FuncFormatter, PercentFormatter
    except ImportError as exc:
        print(f"Analysis unavailable: install numpy, pandas and matplotlib in your Python environment ({exc}).")
        return {}
    paths = {**RESULTS_FILES, **(paths or {})}
    primary = primary or PRIMARY_PARSER
    cases_by_id = {c["id"]: c for c in load_or_make_cases(DATA / "cases.jsonl", SEED, N_CASES_PER_PROCESS)}
    expected_cases = set(cases_by_id)
    target, table_target = Path(figure_dir), Path(table_dir)
    target.mkdir(parents=True, exist_ok=True)
    table_target.mkdir(parents=True, exist_ok=True)
    apply_plot_style(plt)
    TITLES.clear()
    NUMBERS.clear()
    loaded, tables_by, complete = {}, {}, {}
    for name in PARSERS:
        path = Path(paths[name])
        data = load_results(path, pd) if path.exists() else pd.DataFrame()
        if data.empty:
            print(f"Parser {name} ({PARSER_PHRASES[name]}): {path} is missing or empty, so it is left out.")
            continue
        loaded[name] = data
        present = set(zip(data["model"], data["design"], data["k"].astype(int)))
        missing = [a["label"] for a in ARMS if a["key"] not in present]
        short = sum(len(expected_cases - set(g["case_id"])) for _, g in data.groupby(["model", "design", "k"]))
        complete[name] = not missing and short == 0
        if missing:
            print(f"Parser {name}: arms with no results: " + "; ".join(missing))
        if short:
            print(f"Parser {name}: {short} arm-and-case runs are absent from {path}.")
        if not complete[name]:
            print(f"Parser {name} ({PARSER_PHRASES[name]}) is incomplete: {len(data)} of {len(ARMS) * len(expected_cases)} runs.")
        found = (accuracy_table(data, pd, np), accuracy_table(data, pd, np, by_process=True), paired_differences(data, pd, np), *scaling_fit(data, pd, np))
        tables_by[name] = dict(zip(TABLE_NAMES, found))
    if not loaded:
        return {name: pd.DataFrame() for name in TABLE_NAMES}
    tables = {}
    for table_name in TABLE_NAMES:
        frames = []
        for name in loaded:
            frame = tables_by[name][table_name].copy()
            if not frame.empty:
                frame.insert(0, "parser", name)
                frames.append(frame)
        tables[table_name] = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        print(f"\n{table_name}\n{tables[table_name].to_string(index=False) if not tables[table_name].empty else 'Missing usable observations.'}")
        tables[table_name].to_csv(table_target / f"{table_name}.csv", index=False)

    print("\nEach arm under both parsers (first = scored on the first answer, last = scored on the final answer)")
    print(f"{'arm':<32}{'parser':<7}{'correct':>8}{'wrong':>7}{'unreadable':>11}{'planted ok':>11}{'chars/case':>11}")
    for arm in ARMS:
        for name in loaded:
            rows = tables_by[name]["accuracy"]
            rows = rows[rows["arm"] == arm["label"]]
            if rows.empty:
                print(f"{arm['label']:<32}{name:<7}{'no results':>8}")
                continue
            r = rows.iloc[0]
            print(f"{arm['label']:<32}{name:<7}{int(r['correct']):>8}{int(r['wrong']):>7}{int(r['unreadable']):>11}{int(r['planted_correct']):>11}{r['task_chars_per_case']:>11,.0f}")

    effective = primary if complete.get(primary) else None
    if effective is None:
        effective = next((n for n in PARSERS if complete.get(n)), None)
        print(f"\nFigures: the {primary} results ({PARSER_PHRASES[primary]}) are missing or incomplete; "
              + (f"drawing the {effective} parser instead." if effective else "no complete results, so no figure is drawn."))
    all_records = {}

    def draw_figures(parser_name, save_png, compare=None):
        summary, process_summary, pairs, scaling, scaling_points = (tables_by[parser_name][t] for t in TABLE_NAMES)
        arms = list(ARMS)
        row_of = {r.arm: r for r in summary.itertuples() if r.arm}
        n_cases = int(summary["n"].max())
        detail_file = details_path(paths[parser_name])
        if not detail_file.exists() and parser_name == "first":
            print(f"{detail_file} is missing; rebuilding it from the cache with --replay.")
            replay_all(quiet=True, parser="first")
        records = load_details(detail_file)
        def figure(height):
            return plt.figure(figsize=(10.5, height), layout="constrained")

        def title(fig, name, text, numbers):
            text = text.rstrip(".") + ", " + PARSER_PHRASES[parser_name] + "."
            TITLES[(parser_name, name)] = text
            NUMBERS[(parser_name, name)] = numbers
            fig.suptitle(textwrap.fill(text, 92), x=0.005, ha="left", fontsize=12.5, fontweight="bold", color=INK)

        def save(fig, name):
            if save_png:
                fig.savefig(target / f"{name}.png")
            plt.close(fig)

        def lighter(color, amount=0.62):
            rgb = [int(color[i:i + 2], 16) for i in (1, 3, 5)]
            base = [int(PAPER[i:i + 2], 16) for i in (1, 3, 5)]
            return "#" + "".join(f"{round(c * (1 - amount) + b * amount):02x}" for c, b in zip(rgb, base))

        def face(arm, tint=False):
            color = FAMILY_COLORS[arm["family"]]
            if arm["control"]:
                return dict(facecolor=lighter(color, 0.55), edgecolor=color, hatch="///", linewidth=1.2)
            return dict(facecolor=lighter(color, 0.5) if tint else color, edgecolor=color, hatch=None, linewidth=1.2)

        def legend(fig, controls=True, extra=()):
            handles = [Patch(facecolor=FAMILY_COLORS[f], edgecolor=FAMILY_COLORS[f], label=FAMILY_LABELS[f]) for f in FAMILIES
                       if any(a["family"] == f for a in arms)]
            if controls:
                handles.append(Patch(facecolor=lighter(MUTED, 0.75), edgecolor=MUTED, hatch="///", label="Control arm (added after the main run)"))
            fig.legend(handles=handles + list(extra), loc="outside lower center", ncol=3 if len(handles) + len(extra) > 5 else 5, fontsize=9.5)

        def wrap_labels(ax, labels, width=13, size=9.5):
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels([textwrap.fill(l, width) for l in labels], fontsize=size, color=INK)

        def percent_axis(ax, label, top=1.0, axis="y"):
            ax.grid(False)
            ax.grid(axis=axis, color=GUIDE)
            formatter = PercentFormatter(1.0, decimals=0)
            (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(formatter)
            (ax.set_ylabel if axis == "y" else ax.set_xlabel)(label)

        def share_bars(ax, value, low, high, count, label):
            for i, arm in enumerate(arms):
                r = row_of[arm["label"]]
                ax.bar(i, getattr(r, value), 0.7, **face(arm))
                ax.errorbar(i, getattr(r, value), yerr=[[getattr(r, value) - getattr(r, low)], [getattr(r, high) - getattr(r, value)]],
                            fmt="none", ecolor=INK, capsize=4, linewidth=1.2)
                ax.text(i, min(1.0, getattr(r, high)) + 0.02, count(r), ha="center", va="bottom", fontsize=10, color=INK)
            ax.set_ylim(0, 1.13)
            ax.set_yticks([0, .25, .5, .75, 1.0])
            percent_axis(ax, label)
            ax.grid(axis="x", visible=False)
            wrap_labels(ax, [a["label"] for a in arms])

        def count_text(r):
            return f"{r.correct} of {r.n}"

        def pct(value):
            return f"{100 * value:.0f}%"

        owner, p2, p4, p8 = (row_of.get(l) for l in ("One owner", "Pipeline of 2", "Pipeline of 4", "Pipeline of 8"))
        shared, checker = row_of.get("Shared record of 4"), row_of.get("Pipeline of 4 + Terra checker")
        terra, review = row_of.get("Terra, one owner (control)"), row_of.get("Owner + 3 reviewers (control)")
        # 1. accuracy by arm
        fig = figure(6.4)
        ax = fig.add_subplot(111)
        share_bars(ax, "accuracy", "low", "high", count_text, f"Share of the {n_cases} cases with every field correct")
        ax.set_xlabel("Arm (same 80 cases in every arm)")
        title(fig, "accuracy_by_design",
              f"One owner gets {owner.correct} of {n_cases} cases fully correct, a pipeline of 4 gets {p4.correct}, a pipeline of 8 gets {p8.correct} and a shared record of 4 gets {shared.correct}.",
              [f"{a['label']}: {row_of[a['label']].correct} of {row_of[a['label']].n} ({pct(row_of[a['label']].accuracy)}), 95% interval {pct(row_of[a['label']].low)} to {pct(row_of[a['label']].high)}, wrong {row_of[a['label']].wrong}, unreadable {row_of[a['label']].unreadable}" for a in arms])
        legend(fig)
        save(fig, "accuracy_by_design")
        finite = summary["accuracy"].dropna()
        if (finite >= .95).all() or (finite <= .05).all():
            print("Scores sit near a ceiling or floor; this sample cannot reliably rank designs.")

        # 2. accuracy against work (headline)
        fig = figure(6.6)
        ax = fig.add_subplot(111)
        offsets = {"One owner": (10, -16, "left"), "Pipeline of 2": (-10, -18, "right"), "Pipeline of 4": (10, 6, "left"),
                   "Pipeline of 8": (10, 8, "left"), "Shared record of 4": (0, -28, "center"),
                   "Pipeline of 4 + Terra checker": (-10, -22, "right"), "Terra, one owner (control)": (10, -16, "left"),
                   "Owner + 3 reviewers (control)": (-10, 12, "right")}
        for arm in arms:
            r = row_of[arm["label"]]
            x, y = r.task_chars_per_case / 1000, r.accuracy
            color = FAMILY_COLORS[arm["family"]]
            ax.scatter([x], [y], s=150, marker="o", facecolor=PAPER if arm["control"] else color, edgecolor=color,
                       linewidth=2.6 if arm["control"] else 1.2, zorder=3)
            dx, dy, ha = offsets[arm["label"]]
            ax.annotate(arm["label"], (x, y), xytext=(dx, dy), textcoords="offset points", ha=ha, fontsize=10, color=INK)
        ax.set_ylim(0.3, 1.1)
        ax.set_yticks([0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
        percent_axis(ax, f"Share of the {n_cases} cases with every field correct")
        ax.set_xlabel("Mean characters of prompt and reply per case (thousands)")
        ax.set_xlim(0, summary["task_chars_per_case"].max() / 1000 * 1.12)
        ax.grid(axis="x", color=GUIDE)
        legend(fig, controls=False, extra=[Line2D([], [], marker="o", linestyle="", markersize=10, markerfacecolor=PAPER, markeredgecolor=MUTED, markeredgewidth=2.4, label="Control arm (hollow marker)")])
        ratio = lambda r: r.task_chars_per_case / owner.task_chars_per_case
        title(fig, "accuracy_vs_work",
              f"A shared record of 4 gets {pct(shared.accuracy)} of cases right with {ratio(shared):.1f} times the characters of one owner, while a pipeline of 8 uses {ratio(p8):.1f} times as many and gets {pct(p8.accuracy)}.",
              [f"{a['label']}: {row_of[a['label']].task_chars_per_case / 1000:.1f} thousand characters per case, {pct(row_of[a['label']].accuracy)} fully correct, {ratio(row_of[a['label']]):.2f} times one owner's characters" for a in arms])
        save(fig, "accuracy_vs_work")

        # 3. accuracy by process
        fig = figure(6.6)
        ax = fig.add_subplot(111)
        processes = list(PROCESS_NAMES)
        cell = {(r.arm, r.process): r for r in process_summary.itertuples() if r.arm}
        blue = FAMILY_COLORS["owner"]
        for i, arm in enumerate(arms):
            ax.add_patch(Rectangle((0, i + 0.04), 0.22, 0.92, **face(arm)))
            for j, process in enumerate(processes):
                r = cell[(arm["label"], process)]
                ax.add_patch(Rectangle((0.3 + j, i + 0.04), 0.96, 0.92, facecolor=lighter(blue, 0.9 - 0.65 * r.accuracy), edgecolor=PAPER, linewidth=1))
                ax.text(0.3 + j + 0.48, i + 0.5, f"{r.correct} of {r.n}", ha="center", va="center", fontsize=11, color=INK)
        ax.set_xlim(0, 0.3 + len(processes))
        ax.set_ylim(len(arms), 0)
        ax.grid(False)
        ax.set_yticks([i + 0.5 for i in range(len(arms))])
        ax.set_yticklabels([a["label"] for a in arms], fontsize=10, color=INK)
        ax.set_xticks([0.3 + j + 0.48 for j in range(len(processes))])
        ax.set_xticklabels([textwrap.fill(PROCESS_NAMES[p], 16) for p in processes], fontsize=10, color=INK)
        ax.xaxis.tick_top()
        ax.xaxis.set_label_position("top")
        ax.set_xlabel("Process (20 cases each; darker cell = larger share correct)")
        ax.tick_params(length=0)
        for side in ax.spines.values():
            side.set_visible(False)
        legend(fig)
        drops = {p: cell[("One owner", p)].correct - cell[("Pipeline of 8", p)].correct for p in processes}
        worst = max(drops, key=drops.get)
        best_p8 = max(processes, key=lambda p: cell[("Pipeline of 8", p)].correct)
        title(fig, "accuracy_by_process",
              f"The pipeline of 8 falls furthest behind one owner on {PROCESS_NAMES[worst].lower()} ({cell[('Pipeline of 8', worst)].correct} of 20 against {cell[('One owner', worst)].correct} of 20) and keeps up best on {PROCESS_NAMES[best_p8].lower()} ({cell[('Pipeline of 8', best_p8)].correct} of 20).",
              [f"{a['label']}: " + ", ".join(f"{PROCESS_NAMES[p]} {cell[(a['label'], p)].correct} of {cell[(a['label'], p)].n}" for p in processes) for a in arms])
        save(fig, "accuracy_by_process")

        # 4. planted fact survival
        fig = figure(6.4)
        ax = fig.add_subplot(111)
        share_bars(ax, "planted_survival", "planted_low", "planted_high", lambda r: f"{r.planted_correct} of {r.planted_n}",
                   f"Share of the {n_cases} cases where the planted-fact field is correct")
        ax.set_xlabel("Arm (same 80 cases in every arm)")
        title(fig, "planted_fact_survival",
              f"The field that depends on the planted fact is correct in {owner.planted_correct} of {owner.planted_n} cases for one owner, {p4.planted_correct} for a pipeline of 4, {p8.planted_correct} for a pipeline of 8 and {shared.planted_correct} for a shared record of 4.",
              [f"{a['label']}: {row_of[a['label']].planted_correct} of {row_of[a['label']].planted_n} ({pct(row_of[a['label']].planted_survival)}), 95% interval {pct(row_of[a['label']].planted_low)} to {pct(row_of[a['label']].planted_high)}" for a in arms])
        legend(fig)
        save(fig, "planted_fact_survival")

        # 5. review passes
        review_counts = pass_counts(records, cases_by_id, (SONNET, "review", 4))
        shared_counts = pass_counts(records, cases_by_id, (SONNET, "shared", 4))
        print(f"\nCases fully correct after each pass: owner + 3 reviewers {review_counts}; shared record of 4 {shared_counts}.")
        if parser_name == "first" and (review_counts != [65, 77, 80, 80] or shared_counts != [73, 77, 79, 79]):
            print("WARNING: pass counts differ from the expected 65, 77, 80, 80 and 73, 77, 79, 79.")
        fig = figure(5.6)
        ax = fig.add_subplot(111)
        for offset, label, counts in ((-0.2, "Owner + 3 reviewers (control)", review_counts), (0.2, "Shared record of 4", shared_counts)):
            arm = ARM_BY_LABEL[label]
            ax.bar(np.arange(4) + offset, counts, 0.38, **face(arm))
            for x, value in zip(np.arange(4) + offset, counts):
                ax.text(x, value + 1, str(value), ha="center", va="bottom", fontsize=10.5, color=INK)
        ax.set_xticks(range(4))
        ax.set_xticklabels(["After pass 1\n(owner or first agent)", "After pass 2", "After pass 3", "After pass 4"], fontsize=10, color=INK)
        ax.set_ylim(0, 92)
        ax.grid(False)
        ax.grid(axis="y", color=GUIDE)
        ax.set_ylabel(f"Cases fully correct (of {n_cases})")
        ax.set_xlabel("Pass: each agent applies its fields to the record in turn")
        fig.legend(handles=[Patch(facecolor=lighter(FAMILY_COLORS["shared"], .55), edgecolor=FAMILY_COLORS["shared"], hatch="///", label="Owner + 3 reviewers (control)"),
                            Patch(facecolor=FAMILY_COLORS["shared"], edgecolor=FAMILY_COLORS["shared"], label="Shared record of 4")],
                   loc="outside lower center", ncol=2, fontsize=9.5)
        title(fig, "review_passes",
              f"One owner followed by three reviewers goes from {review_counts[0]} to {review_counts[-1]} of {n_cases} cases fully correct, and the shared record of 4 goes from {shared_counts[0]} to {shared_counts[-1]}.",
              [f"Owner + 3 reviewers (control), cases fully correct after passes 1 to 4: {review_counts}", f"Shared record of 4, after passes 1 to 4: {shared_counts}"])
        save(fig, "review_passes")

        # 6. paired differences
        fig = figure(8.4)
        grid = fig.add_gridspec(1, 2, width_ratios=[3.1, 1.25])
        ax, table_ax = fig.add_subplot(grid[0]), fig.add_subplot(grid[1], sharey=None)
        y = np.arange(len(pairs))
        for i, r in enumerate(pairs.itertuples()):
            color = FAMILY_COLORS[r.first_family]
            ax.errorbar(100 * r.difference, i, xerr=[[100 * (r.difference - r.low)], [100 * (r.high - r.difference)]], fmt="o", markersize=9,
                        markerfacecolor=PAPER if r.first_control else color, markeredgecolor=color, markeredgewidth=2.2, color=color, capsize=4, linewidth=1.8)
            table_ax.text(0.02, i, f"{100 * r.difference:+.1f}  ({100 * r.low:+.1f} to {100 * r.high:+.1f})", va="center", fontsize=9.5, color=INK)
        ax.axvline(0, color=INK, linewidth=0.9)
        ax.set_yticks(y)
        ax.set_yticklabels([f"{r.first}\nminus {r.second}" for r in pairs.itertuples()], fontsize=9, color=INK)
        ax.set_ylim(len(pairs) - 0.5, -0.5)
        ax.grid(False)
        ax.grid(axis="x", color=GUIDE)
        ax.set_xlabel(f"Difference in share of cases fully correct, same {n_cases} cases (percentage points)")
        table_ax.set_ylim(len(pairs) - 0.5, -0.5)
        table_ax.set_xlim(0, 1)
        table_ax.axis("off")
        table_ax.set_title("Difference (95% interval)", fontsize=9.5, color=MUTED, loc="left")
        legend(fig, controls=False, extra=[Line2D([], [], marker="o", linestyle="", markersize=9, markerfacecolor=PAPER, markeredgecolor=MUTED, markeredgewidth=2.2, label="First arm is a control (hollow marker)")])
        pr = {r.comparison: r for r in pairs.itertuples()}
        sh, p8d = pr["Shared record of 4 minus One owner"], pr["Pipeline of 8 minus One owner"]
        title(fig, "paired_differences",
              f"On the same {n_cases} cases a shared record of 4 beats one owner by {100 * sh.difference:.1f} points ({100 * sh.low:.1f} to {100 * sh.high:.1f}), and a pipeline of 8 trails one owner by {-100 * p8d.difference:.1f} points ({-100 * p8d.high:.1f} to {-100 * p8d.low:.1f}).",
              [f"{r.comparison}: {100 * r.difference:+.1f} points (95% interval {100 * r.low:+.1f} to {100 * r.high:+.1f}), first arm only correct {r.first_only_correct}, second arm only correct {r.second_only_correct}, {r.n_pairs} pairs" for r in pairs.itertuples()])
        save(fig, "paired_differences")

        # 7. pipeline scaling
        sc = scaling[scaling["model"] == SONNET].iloc[0]
        pts = scaling_points[scaling_points["model"] == SONNET].sort_values("k")
        fig = figure(6.2)
        ax = fig.add_subplot(111)
        ks, out = pts["k"].to_numpy(dtype=float), 1000 * pts["output"].to_numpy()
        slope, intercept = np.polyfit(np.log(ks), np.log(out), 1)
        grid_k = np.array([1, 8])
        ax.plot(grid_k, np.exp(intercept) * grid_k ** slope, color=MUTED, linestyle="--", linewidth=1.6, label=f"Fitted slope {sc.slope:.2f}", zorder=1)
        ax.plot(grid_k, out[0] * grid_k, color=MUTED, linestyle=":", linewidth=2.2, label="Slope 1: output proportional to team size (leaves the chart)", zorder=1)
        label_offsets = {1: (12, -20), 2: (12, -20), 4: (12, 10), 8: (-12, 12)}
        for k, value in zip(ks, out):
            color = FAMILY_COLORS["owner"] if k == 1 else FAMILY_COLORS["pipeline"]
            ax.scatter([k], [value], s=150, color=color, zorder=3)
            dx, dy = label_offsets[int(k)]
            ax.annotate(f"{'One owner' if k == 1 else f'Pipeline of {int(k)}'}: {value:.3f}", (k, value), xytext=(dx, dy), textcoords="offset points",
                        ha="right" if dx < 0 else "left", fontsize=10, color=INK)
        ax.set_xscale("log", base=2)
        ax.set_yscale("log")
        ax.set_xticks([1, 2, 4, 8])
        ax.set_xticklabels(["1", "2", "4", "8"])
        ax.xaxis.set_minor_formatter(FuncFormatter(lambda v, _: ""))
        ax.set_ylim(0.07, 0.2)
        ax.set_yticks([0.07, 0.08, 0.1, 0.12, 0.15, 0.2])
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
        ax.yaxis.set_minor_formatter(FuncFormatter(lambda v, _: ""))
        ax.set_xlim(0.85, 9.5)
        ax.grid(False)
        ax.grid(color=GUIDE, which="major", linewidth=0.8)
        ax.set_xlabel("Number of agents k (the single owner supplies k = 1), log scale")
        ax.set_ylabel("k × share correct ÷ characters per case,\nper 1,000 characters (log scale)")
        ax.legend(loc="upper left", fontsize=9.5)
        fig.legend(handles=[Line2D([], [], marker="o", linestyle="", markersize=9, color=FAMILY_COLORS["owner"], label="One owner (k = 1)"),
                            Line2D([], [], marker="o", linestyle="", markersize=9, color=FAMILY_COLORS["pipeline"], label="Pipeline (k = 2, 4, 8)")],
                   loc="outside lower center", ncol=2, fontsize=9.5)
        if sc.low <= 0 <= sc.high:
            behaviour = "stays roughly flat as the team grows"
        else:
            behaviour = "rises with team size" if sc.low > 0 else "falls with team size"
        relation = "below" if sc.high < 1 else "not clearly below"
        title(fig, "pipeline_scaling",
              f"Output per character {behaviour}: the fitted log-log slope is {sc.slope:.2f} (95% interval {sc.low:.2f} to {sc.high:.2f}), {relation} the slope of 1 that output proportional to team size would give.",
              [f"slope {sc.slope:.3f}, 95% interval {sc.low:.3f} to {sc.high:.3f}, {int(sc.n_cases)} cases, {BOOTSTRAPS:,} resamples"] +
              [f"k = {int(r.k)}: share correct {pct(r.accuracy)}, {r.chars_per_case / 1000:.1f} thousand characters per case, output {1000 * r.output:.4f} per 1,000 characters" for r in pts.itertuples()])
        save(fig, "pipeline_scaling")

        # 8. work per case
        fig = figure(6.4)
        ax = fig.add_subplot(111)
        for i, arm in enumerate(arms):
            r = row_of[arm["label"]]
            prompt, reply = r.prompt_chars_per_case / 1000, r.reply_chars_per_case / 1000
            style = face(arm)
            if arm["control"]:
                style = dict(style, facecolor=lighter(FAMILY_COLORS[arm["family"]], 0.35))
            ax.bar(i, prompt, 0.7, **style)
            reply_style = dict(style, facecolor=lighter(FAMILY_COLORS[arm["family"]], 0.8 if arm["control"] else 0.6))
            ax.bar(i, reply, 0.7, bottom=prompt, **reply_style)
            ax.text(i, prompt + reply + 1, f"{prompt + reply:.1f}k", ha="center", va="bottom", fontsize=10, color=INK)
        ax.set_ylabel("Mean characters per case (thousands)")
        ax.set_xlabel("Arm")
        ax.set_ylim(0, summary["task_chars_per_case"].max() / 1000 * 1.1)
        ax.grid(False)
        ax.grid(axis="y", color=GUIDE)
        wrap_labels(ax, [a["label"] for a in arms])
        legend(fig, extra=[Patch(facecolor=MUTED, edgecolor=MUTED, label="Prompt (dark part)"), Patch(facecolor=lighter(MUTED, .6), edgecolor=MUTED, label="Reply (light part)")])
        title(fig, "work_per_case",
              f"One owner uses {owner.task_chars_per_case / 1000:.1f} thousand characters of prompt and reply per case, a pipeline of 8 uses {p8.task_chars_per_case / 1000:.1f} thousand and an owner with 3 reviewers uses {review.task_chars_per_case / 1000:.1f} thousand.",
              [f"{a['label']}: prompt {row_of[a['label']].prompt_chars_per_case / 1000:.1f} thousand + reply {row_of[a['label']].reply_chars_per_case / 1000:.1f} thousand = {row_of[a['label']].task_chars_per_case / 1000:.1f} thousand characters per case" for a in arms])
        save(fig, "work_per_case")

        # 9. unreadable and wrong
        fig = figure(6.0)
        grid = fig.add_gridspec(1, 2, width_ratios=[3.2, 1.2])
        ax, side = fig.add_subplot(grid[0]), fig.add_subplot(grid[1])
        for i, arm in enumerate(arms):
            r = row_of[arm["label"]]
            ax.barh(i, r.correct, 0.7, **face(arm))
            ax.barh(i, r.wrong, 0.7, left=r.correct, facecolor=lighter(MUTED, 0.45), edgecolor=MUTED, linewidth=1.2)
            ax.barh(i, r.unreadable, 0.7, left=r.correct + r.wrong, facecolor=PAPER, edgecolor=INK, hatch="xxx", linewidth=1.2)
            ax.text(r.correct / 2 if r.correct > 6 else r.correct + 0.5, i, str(r.correct), ha="center" if r.correct > 6 else "left", va="center", fontsize=10, color=INK)
            side.text(0.02, i, f"{r.wrong} wrong, {r.unreadable} unreadable", va="center", fontsize=9.5, color=INK)
        ax.set_yticks(range(len(arms)))
        ax.set_yticklabels([a["label"] for a in arms], fontsize=9.5, color=INK)
        ax.set_ylim(len(arms) - 0.5, -0.5)
        ax.set_xlim(0, n_cases)
        ax.grid(False)
        ax.grid(axis="x", color=GUIDE)
        ax.set_xlabel(f"Cases (of {n_cases}) by outcome")
        side.set_ylim(len(arms) - 0.5, -0.5)
        side.set_xlim(0, 1)
        side.axis("off")
        side.set_title("Counts outside the correct bar", fontsize=9.5, color=MUTED, loc="left")
        legend(fig, controls=True, extra=[Patch(facecolor=lighter(MUTED, 0.45), edgecolor=MUTED, label="Wrong (readable)"),
                                         Patch(facecolor=PAPER, edgecolor=INK, hatch="xxx", label="Unreadable")])
        total_runs, total_unreadable = int(summary["n"].sum()), int(summary["unreadable"].sum())
        total_wrong = int(summary["wrong"].sum())
        title(fig, "unreadable_and_wrong",
              f"Only {total_unreadable} of {total_runs} runs were unreadable, {p2.unreadable} of them in the pipeline of 2; the other {total_wrong} misses were readable wrong answers.",
              [f"{a['label']}: correct {row_of[a['label']].correct}, wrong {row_of[a['label']].wrong}, unreadable {row_of[a['label']].unreadable}" for a in arms] +
              [f"All arms: {total_runs} runs, {total_unreadable} unreadable, {total_wrong} wrong"])
        save(fig, "unreadable_and_wrong")

        # 10. planted fact along the pipeline of 8
        series8, hits8, runs8 = handoff_series(records, cases_by_id, (SONNET, "pipeline", 8))
        series4, hits4, runs4 = handoff_series(records, cases_by_id, (SONNET, "pipeline", 4))
        fig = figure(5.6)
        ax = fig.add_subplot(111)
        ax.bar(range(7), series8, 0.7, color=FAMILY_COLORS["pipeline"], edgecolor=FAMILY_COLORS["pipeline"])
        for i, (value, hit) in enumerate(zip(series8, hits8)):
            ax.text(i, value + 0.02, f"{hit} of {runs8}", ha="center", va="bottom", fontsize=10, color=INK)
        ax.set_xticks(range(7))
        ax.set_xticklabels([f"Agent {i + 1} to {i + 2}" for i in range(7)], fontsize=10, color=INK)
        ax.set_ylim(0, 1.12)
        ax.set_yticks([0, .25, .5, .75, 1.0])
        percent_axis(ax, f"Share of the {runs8} cases with the planted fact in the note")
        ax.set_xlabel("Handoff in the pipeline of 8 (the outgoing note of the first agent named)")
        ax.set_title(f"Keyword match: a note counts if it contains at least half of the distinctive words of the planted sentence; {PARSER_PHRASES[parser_name]}.",
                     fontsize=9.5, color=MUTED, loc="left")
        title(fig, "case_trace_pipeline8",
              f"In the pipeline of 8 the outgoing note mentions the planted fact in {pct(series8[0])} of cases at the first handoff, {pct(min(series8))} at the lowest (agent {series8.index(min(series8)) + 1} to {series8.index(min(series8)) + 2}) and {pct(series8[-1])} at the seventh.",
              [f"Pipeline of 8, handoffs 1 to 7: " + ", ".join(f"{h} of {runs8} ({pct(v)})" for h, v in zip(hits8, series8)),
               f"Pipeline of 4, handoffs 1 to 3: " + ", ".join(f"{h} of {runs4} ({pct(v)})" for h, v in zip(hits4, series4))])
        save(fig, "case_trace_pipeline8")


        # 11. the two parsers side by side
        if compare is not None:
            other_row = {r.arm: r for r in compare["summary"].itertuples() if r.arm}
            fig = figure(6.6)
            ax = fig.add_subplot(111)
            changes = []
            for i, arm in enumerate(arms):
                first_row, last_row = (row_of[arm["label"]], other_row[arm["label"]]) if parser_name == "first" else (other_row[arm["label"]], row_of[arm["label"]])
                changes.append(last_row.correct - first_row.correct)
                color = FAMILY_COLORS[arm["family"]]
                first_style = dict(facecolor=lighter(color, 0.8 if arm["control"] else 0.7), edgecolor=color, hatch="///" if arm["control"] else None, linewidth=1.2)
                ax.bar(i - 0.2, first_row.correct, 0.38, **first_style)
                ax.bar(i + 0.2, last_row.correct, 0.38, **face(arm))
                for x, r in ((i - 0.2, first_row), (i + 0.2, last_row)):
                    ax.text(x, r.correct + 1.2, f"{r.correct}\nof {r.n}", ha="center", va="bottom", fontsize=8.5, color=INK)
            ax.set_ylim(0, 100)
            ax.set_yticks([0, 20, 40, 60, 80])
            ax.grid(False)
            ax.grid(axis="y", color=GUIDE)
            ax.set_ylabel(f"Cases fully correct (of {n_cases})")
            ax.set_xlabel("Arm (left bar: first answer, right bar: final answer)")
            wrap_labels(ax, [a["label"] for a in arms])
            legend(fig, extra=[Patch(facecolor=lighter(MUTED, 0.7), edgecolor=MUTED, label="Scored on each agent's first answer (left, lighter bar)"),
                               Patch(facecolor=MUTED, edgecolor=MUTED, label="Scored on each agent's final answer (right, darker bar)")])
            moved = [c for c in changes if c]
            largest = max((abs(c) for c in changes), default=0)
            title(fig, "parser_comparison",
                  f"{len(moved)} of {len(arms)} arm totals change between the two parsers, by at most {largest} of {n_cases} cases.",
                  [f"{a['label']}: first {(row_of if parser_name == 'first' else other_row)[a['label']].correct} of {n_cases}, last {(other_row if parser_name == 'first' else row_of)[a['label']].correct} of {n_cases}, change {c:+d}"
                   for a, c in zip(arms, changes)])
            save(fig, "parser_comparison")
        return records


    for name in PARSERS:
        if not complete.get(name):
            continue
        other = next((o for o in PARSERS if o != name and complete.get(o)), None)
        compare = {"summary": tables_by[other]["accuracy"]} if (other and name == effective) else None
        all_records[name] = draw_figures(name, name == effective, compare)
    if effective and not any(complete.get(n) for n in PARSERS if n != effective):
        print("figures/parser_comparison.png is not drawn: it needs complete results under both parsers.")

    print("\nSpend")
    drawn_calls = [c for records in all_records.values() for per_case in records.values() for result in per_case.values() for c in result["calls"]]
    first_data = loaded.get("first", next(iter(loaded.values())))
    overheads = {m: (float(v) if v == v else None) for m, v in first_data.groupby("model")["overhead_input_tokens"].max().items()}
    print(format_spend(spend_from_calls(drawn_calls, overheads)))
    print(f"\nIntervals are 95% percentile intervals from {BOOTSTRAPS:,} case resamples (one function, fixed seed). Unreadable replies count as not correct.")
    print("Planted survival includes all cases; the handoff trace is a keyword match, not a reading of each note.")
    print("\nNumbers used in figure titles, under each parser that was drawn")
    names = []
    for parser_name, figure_name in TITLES:
        if figure_name not in names:
            names.append(figure_name)
    for figure_name in names:
        print(f"\n{figure_name}.png" + ("" if any(TITLES.get((n, figure_name)) and n == effective for n in PARSERS) else "  (not saved)"))
        for parser_name in PARSERS:
            if (parser_name, figure_name) in TITLES:
                print(f"  [{parser_name}] Title: {TITLES[(parser_name, figure_name)]}")
                for line in NUMBERS[(parser_name, figure_name)]:
                    print(f"    - {line}")
    return tables

# %% [markdown]
# The next cell runs the analysis under the same guard as the replay, so it cannot call a model or trace. It rewrites the five tables in `data/` (each has a `parser` column for the two readings) and the figures in `figures/`, and prints every table and the numbers behind the figure titles. Before and after, it compares the bytes of the tables with what was committed. The printed output is long; the sections that follow show each table and figure where it is discussed.

# %%
if NOTEBOOK_RUN:
    import io

    TABLE_FILES = [DATA / f"{name}.csv" for name in TABLE_NAMES]
    before = {p.name: p.read_bytes() if p.exists() else None for p in TABLE_FILES}
    log = io.StringIO()
    with no_model_calls(), contextlib.redirect_stdout(log):
        TABLES = analyse()
    after = {p.name: p.read_bytes() for p in TABLE_FILES}
    (TMP / "analyse.log").write_text(log.getvalue(), encoding="utf-8")
    text = log.getvalue()
    print(f"Full analysis log ({len(text):,} characters, written to data/tmp/analyse.log). The five tables are shown in the sections below; the log from the per-arm summary on:{chr(10)}")
    print(text[text.index("Each arm under both parsers"):])
    for name in before:
        state = "new file" if before[name] is None else "byte-identical to the committed table" if before[name] == after[name] else "DIFFERENT from the committed table"
        print(f"{name}: {state}")
    assert not CALLS_ATTEMPTED and not LANGFUSE_ON

# %% [markdown]
# ## 12. Accuracy by design
#
# Each bar is an arm's share of cases fully correct on final answers, with its count and 95% interval; hatched bars are control arms. Compare the pipelines with one owner, then the right-hand group with each other. First-answer counts are in brackets.
#
# The cell below reads the five tables written in section 11, defines the display helpers used in every results section, and shows the table and the figure.

# %%
if NOTEBOOK_RUN:
    TABLES = {name: pd.read_csv(DATA / f"{name}.csv") for name in TABLE_NAMES}
    CASES_BY_ID = {c["id"]: c for c in load_or_make_cases(DATA / "cases.jsonl", SEED, N_CASES_PER_PROCESS)}
    DETAILS = {name: load_details(details_path(RESULTS_FILES[name])) for name in PARSERS}
    ARM_LABELS = [a["label"] for a in ARMS]


    def by_parser(table, parser):
        frame = TABLES[table]
        return frame[frame["parser"] == parser].reset_index(drop=True)


    def show_figure(name, width=980):
        display(Image(filename=str(FIGURES / f"{name}.png"), width=width))


    def pct(value, digits=1):
        return f"{100 * value:.{digits}f}%"


    def points(value):
        return f"{100 * value:+.1f}"


    def arm_rows(table):
        first, final = by_parser(table, "first").set_index("arm"), by_parser(table, "last").set_index("arm")
        return first, final


    first_acc, final_acc = arm_rows("accuracy")
    rows = []
    for label in ARM_LABELS:
        a, b = final_acc.loc[label], first_acc.loc[label]
        rows.append({"Arm": label, "Correct": int(a.correct), "Correct (first)": int(b.correct), "Wrong": int(a.wrong), "Wrong (first)": int(b.wrong),
                     "Unreadable": int(a.unreadable), "Unreadable (first)": int(b.unreadable), "Accuracy": pct(a.accuracy),
                     "95% interval": f"{pct(a.low)} to {pct(a.high)}", "On readable": pct(a.readable_accuracy),
                     "Accuracy (first)": pct(b.accuracy), "Characters per case": f"{a.task_chars_per_case:,.0f}"})
    print("Cases out of 80 on final answers, with the first-answer reading marked (first)")
    print(pd.DataFrame(rows).to_string(index=False))
    show_figure("accuracy_by_design")

# %% [markdown]
# Every pipeline did worse than one owner, and the longest did worst: 47 of 80, 20 fewer than the owner. The pipelines of 2 and 4 are close (59 and 60), and on readable cases their order flips because 9 of the pipeline of 2's failures were unreadable. The other arms are all at 97.5% or above.

# %% [markdown]
# Each row compares two arms on the same cases; a dot right of zero means the first arm got more right, and a bar crossing zero means the gap could be chance. Counts are cases only the first arm got right, then only the second.

# %%
if NOTEBOOK_RUN:
    first_p, final_p = by_parser("paired", "first").set_index("comparison"), by_parser("paired", "last").set_index("comparison")
    rows = []
    for name in final_p.index:
        a, b = final_p.loc[name], first_p.loc[name]
        rows.append({"Comparison (first arm minus second)": name, "Final answers (interval)": f"{points(a.difference)} ({points(a.low)} to {points(a.high)})",
                     "Counts (only first, only second)": f"{a.first_only_correct}, {a.second_only_correct}",
                     "First answers (interval)": f"{points(b.difference)} ({points(b.low)} to {points(b.high)})"})
    print("Paired differences in points, on the same 80 cases")
    print(pd.DataFrame(rows).to_string(index=False))
    show_figure("paired_differences")

# %% [markdown]
# Every comparison points the same way under both readings, and every interval that excludes zero under one excludes it under the other. The pipeline of 8 is clearly behind one owner and the pipeline of 4; the pipelines of 2 and 4 may be behind one owner, but their intervals cross zero, and the pipeline of 2 got 10 cases right that the owner missed. The shared record beat the pipeline of 4 on 19 cases and lost none; section 13 shows why.

# %% [markdown]
# ## 13. What the control arms show
#
# The checker sees every document, so if Terra alone scores about the same, the checker arm measures Terra, not checking. Terra alone got 78 of 80, 2 fewer than the checker arm (interval 0.0 to 6.2 points) and 13.8 points more than the Sonnet owner with about the same work. Its two misses were each off by exactly 1.00 in a currency conversion (`capital-4812`, `credit-4805`).
#
# The shared record's first agent sees every document and returned every field in all 80 cases, so the design was four full passes. If one owner followed by three full reviews scores the same, the gain comes from repeated passes. It did.
#
# Bars show the record after each pass; hatched bars are the owner with reviewers, solid bars the shared record.
#
# The cell below counts how many cases are fully correct after each of the four passes in the two arms that make four passes, under both readings, lists the case-level changes at each pass, and looks at the two cases Terra alone missed.

# %%
if NOTEBOOK_RUN:
    def pass_flags(records, key, passes=4):
        """Per case, whether the record is fully correct after each pass (the rule of pass_counts, kept per case)."""
        flags = {}
        for case_id, result in records[key].items():
            case, fields, out = CASES_BY_ID[case_id], {}, []
            for note in sorted(result["notes"], key=lambda n: n["station_index"])[:passes]:
                fields.update({f: v for f, v in note["fields"].items() if f in case["truth"]})
                out.append(all(f in fields and field_equal(f, t, fields[f]) for f, t in case["truth"].items()))
            flags[case_id] = out
        return flags


    for label, key in (("Owner + 3 reviewers", (SONNET, "review", 4)), ("Shared record of 4", (SONNET, "shared", 4))):
        for parser_name in ("first", "last"):
            print(f"{label}, cases fully correct after passes 1 to 4, {parser_name} answers: {pass_counts(DETAILS[parser_name], CASES_BY_ID, key)}")

    print()
    for label, key in (("Owner + 3 reviewers", (SONNET, "review", 4)), ("Shared record of 4", (SONNET, "shared", 4))):
        flags = pass_flags(DETAILS["last"], key)
        for i in range(3):
            fixed = sorted(c for c, f in flags.items() if not f[i] and f[i + 1])
            broke = sorted(c for c, f in flags.items() if f[i] and not f[i + 1])
            print(f"{label}, final answers, pass {i + 1} to pass {i + 2}: fixed {len(fixed)}, broke {len(broke)} {broke}")
        print(f"  still wrong after pass 4: {sorted(c for c, f in flags.items() if not f[3])}")

    owner_flags = {c: r for c, r in ((cid, score_case(CASES_BY_ID[cid], res)["status"] == "correct") for cid, res in DETAILS["last"][(SONNET, "owner", 1)].items())}
    shared_first = {c: f[0] for c, f in pass_flags(DETAILS["last"], (SONNET, "shared", 4)).items()}
    print(f"\nShared record's first agent {sum(shared_first.values())} correct, one owner {sum(owner_flags.values())} correct; "
          f"only the shared first agent right: {sum(shared_first[c] and not owner_flags[c] for c in owner_flags)}, only the owner right: {sum(owner_flags[c] and not shared_first[c] for c in owner_flags)}")

    terra = pd.read_csv(RESULTS_FILES["last"])
    terra = terra[(terra["model"] == TERRA) & (terra["status"] != "correct")]
    for _, row in terra.iterrows():
        case_row = CASES_BY_ID[row["case_id"]]
        bad = [f for f, ok in json.loads(row["per_field_correct"]).items() if not ok]
        returned = json.loads(row["final_fields"])
        for f in bad:
            print(f"Terra alone, {row['case_id']}: {f} expected {case_row['truth'][f]}, returned {returned.get(f)} (difference {float(returned.get(f)) - float(case_row['truth'][f]):+.2f})")
    show_figure("review_passes")

# %% [markdown]
# The first reviewer fixed 12 of the owner's 13 wrong cases and broke one (`trade-4801`), for 78; the second repaired it and fixed `credit-4804`, for 80; the third changed nothing (65, 77, 80, 80 on first answers). In the shared record (73, 77, 79, 79 under both readings) the second agent fixed six cases and broke two, the third repaired both, and `credit-4806` stayed wrong.
#
# The shared record's first agent got 73 right where the owner, with a prompt that differs only in its role text, got 67; they disagreed on 18 cases (12 against 6), so gaps of about 6 cases between single passes need care.

# %% [markdown]
# ## 14. Accuracy by process
#
# Each cell counts fully correct cases out of 20 on final answers, first-answer counts in brackets.
#
# The cell below prints the same grid as a table, final answers with first answers beside them, then shows the figure.

# %%
if NOTEBOOK_RUN:
    first_p, final_p = by_parser("by_process", "first"), by_parser("by_process", "last")
    grid = []
    for label in ARM_LABELS:
        row = {"Arm": label}
        for process in PROCESS_NAMES:
            a = final_p[(final_p["arm"] == label) & (final_p["process"] == process)].iloc[0]
            b = first_p[(first_p["arm"] == label) & (first_p["process"] == process)].iloc[0]
            row[process] = f"{int(a.correct)}" if a.correct == b.correct else f"{int(a.correct)} ({int(b.correct)})"
        grid.append(row)
    print("Cases fully correct out of 20, final answers (first answers in brackets where they differ)")
    print(pd.DataFrame(grid).to_string(index=False))
    show_figure("accuracy_by_process")

    trade8 = pd.read_csv(RESULTS_FILES["last"])
    trade8 = trade8[(trade8["model"] == SONNET) & (trade8["design"] == "pipeline") & (trade8["k"] == 8) & (trade8["process"] == "trade") & (trade8["status"] != "correct")]
    wrong_fields = collections.Counter(f for p in trade8["per_field_correct"] for f, ok in json.loads(p).items() if not ok)
    print(f"\nBlock trade, pipeline of 8: {len(trade8)} cases not fully correct; wrong fields: {dict(wrong_fields)}")
    commission_agent = next(i for i, s in enumerate(stations_for("trade", 8)) if "commission_cad" in s["fields"])
    note_right = 0
    for _, row in trade8.iterrows():
        if not json.loads(row["per_field_correct"]).get("commission_cad", True):
            notes = {n["station_index"]: n["note"] for n in DETAILS["last"][(SONNET, "pipeline", 8)][row["case_id"]]["notes"]}
            expected = money(CASES_BY_ID[row["case_id"]]["truth"]["commission_cad"])
            returned = json.loads(row["final_fields"]).get("commission_cad")
            in_note = expected in notes[commission_agent]
            note_right += returned is not None and in_note
            print(f"  {row['case_id']}: commission_cad returned {returned}, expected {expected}; agent {commission_agent + 1}'s own note holds {expected}: {in_note}")
    print(f"commission wrong although the same agent's note holds the right figure (field filled, not left empty): {note_right} cases")

# %% [markdown]
# Block trade allocation was expected to show the smallest gaps between designs. It showed the largest: one owner got all 20 and the pipeline of 8 got 11. Commission was wrong in 5 of its 9 failures; in 3 the agent's note had the right figure after a wrong field ("CORRECTION: commission_cad is 136.00, not 907.20", `trade-4805`). In capital calls the pipelines of 4 and 8 beat the owner (17 and 16 against 15), and in laboratory billing the pipeline of 2 did (19 against 15). With 20 cases per cell, gaps of three or four cases are within chance, so the rows show where losses happened, not a ranking.

# %% [markdown]
# ## 15. The planted fact and the wrong intake note
#
# Each bar counts cases in which the late field that depends on the planted sentence came out right. The middle column, counted from the final forms in the two results files, gives cases where the planted code itself is missing.
#
# Two measures are printed. The planted fact is kept when the late field that depends on the planted sentence is correct. The planted code is missing when the form does not contain the code the sentence calls for: the sentence's countersignature or payer for the scalar fields (capital call, laboratory billing), and the undertaking or review code for the two list fields (credit conditions, trade flags). The intake error is caught when the field the wrong note touched is correct, counted over the 17 injected cases.

# %%
if NOTEBOOK_RUN:
    PLANTED_CODE = {
        "capital": lambda c: c["truth"]["release_control"],
        "credit": lambda c: "ENV_UNDERTAKING" if "environmental" in c["params"]["planted_sentence"] else "OWNERSHIP_UNDERTAKING",
        "lab": lambda c: c["truth"]["billed_to"],
        "trade": lambda c: "CLIENT_REVIEW" if "CLIENT_REVIEW" in c["params"]["planted_sentence"] else "LEGAL_REVIEW",
    }


    def planted_missing(frame):
        """Rows whose final form lacks the code the planted sentence calls for."""
        out = []
        for _, row in frame.iterrows():
            case = CASES_BY_ID[row["case_id"]]
            value = json.loads(row["final_fields"]).get(case["planted_field"])
            code_ = PLANTED_CODE[case["process"]](case)
            out.append(code_ not in value if isinstance(value, list) else value != code_)
        return frame.assign(missing=out)


    missing = {p: planted_missing(pd.read_csv(RESULTS_FILES[p])) for p in PARSERS}
    first_acc, final_acc = arm_rows("accuracy")
    rows = []
    for label in ARM_LABELS:
        a, b = final_acc.loc[label], first_acc.loc[label]
        arm_key = ARM_BY_LABEL[label]["key"]
        miss = {p: int(m[(m["model"] == arm_key[0]) & (m["design"] == arm_key[1]) & (m["k"] == arm_key[2])]["missing"].sum()) for p, m in missing.items()}
        rows.append({"Arm": label, "Planted fact kept": int(a.planted_correct), "(first)": int(b.planted_correct), "Planted code missing": miss["last"],
                     "(first) ": miss["first"], "Intake error caught of 17": round(a.injected_catch * a.injected_n), "(first)  ": round(b.injected_catch * b.injected_n)})
    print(pd.DataFrame(rows).to_string(index=False))
    show_figure("planted_fact_survival")

    final_missing = missing["last"]
    for k in (4, 8):
        sub = final_missing[(final_missing["model"] == SONNET) & (final_missing["design"] == "pipeline") & (final_missing["k"] == k) & final_missing["missing"]]
        print(f"\nPipeline of {k}: planted code missing in {len(sub)} cases by process: {dict(collections.Counter(sub['process']))}")
    for p, m in missing.items():
        arms_missing = m[(m["model"] == SONNET) & m["missing"]]
        print(f"{p}: planted code missing in {len(arms_missing)} case results over all Sonnet arms; in arms whose agents all see the email: "
              f"{len(arms_missing[arms_missing['design'].isin(['owner', 'shared', 'review'])])}")

# %% [markdown]
# The fact was kept less often in the longer pipelines: 67 of 80 cases with four or eight agents, against 79 for one owner. The planted code was missing in 7 pipeline-of-4 cases, all laboratory billing, and 9 pipeline-of-8 cases (5 laboratory, 2 credit, 1 capital, 1 trade), and never where agents saw the original email.

# %% [markdown]
# Each bar is a handoff in the pipeline of 8 and counts notes containing at least half of the planted sentence's distinctive words: 80 of 80 after agent 1, 57 after agent 5, then 76 and 76. The late rise needs care: the match also counts notes saying the fact is absent, so the chart counts mentions, not correct use.

# %%
if NOTEBOOK_RUN:
    show_figure("case_trace_pipeline8")

# %% [markdown]
# Reading the 16 pipeline cases with the planted code missing gives a clearer picture. In 14, the fact reached the agent that fills the field as a colleague's retelling, and that agent declined to act on an unsigned second-hand claim. In 2 (`credit-4807`, `credit-4808`, pipeline of 8), the seventh agent's note covered only its own field and the fact vanished. None traces to a draft. On first answers there were 26: the same 14 and 2, plus 10 where the next agent got a draft note without the fact while the agent's own revision carried it, which is why the second reading exists.
#
# The cell below checks the first count in that paragraph from the saved notes. For each of the 16 pipeline cases (final answers) whose form lacks the planted code, it takes the agent that fills the planted field and asks whether the note it received mentions the planted sentence, using the same keyword match as the figure.

# %%
if NOTEBOOK_RUN:
    rows = []
    for k in (4, 8):
        sub = final_missing[(final_missing["model"] == SONNET) & (final_missing["design"] == "pipeline") & (final_missing["k"] == k) & final_missing["missing"]]
        for _, row in sub.iterrows():
            case = CASES_BY_ID[row["case_id"]]
            stations = stations_for(case["process"], k)
            owner_index = next(i for i, s in enumerate(stations) if case["planted_field"] in s["fields"])
            notes = {n["station_index"]: n["note"] for n in DETAILS["last"][(SONNET, "pipeline", k)][row["case_id"]]["notes"]}
            rows.append({"case": row["case_id"], "pipeline of": k, "agent filling the field": owner_index + 1,
                         "incoming note mentions the fact": mentions_planted(notes.get(owner_index - 1, ""), case["params"]["planted_sentence"])})
    table = pd.DataFrame(rows)
    print(table.to_string(index=False))
    print("\nincoming note mentions the fact:", int(table["incoming note mentions the fact"].sum()), "of", len(table),
          "| not:", table[~table["incoming note mentions the fact"]]["case"].tolist())

# %% [markdown]
# The wrong intake note was caught in all 17 cases by every arm except the pipeline of 2, whose one miss (`credit-4805`) was an unreadable form with the field never filled. This test is at a ceiling. A possible link, untested: the rule that guards against the wrong note (prefer signed records) is the one late agents cited when they set aside a retold planted fact.

# %% [markdown]
# ## 16. Work and scaling
#
# Each bar is the mean characters per case, prompt in the darker part. The pipelines of 2, 4 and 8 used 1.56, 2.59 and 4.42 times the owner's characters, mostly reading. The arms at 97.5% or more used 37,050 to 45,470 characters, except Terra alone at 9,081.
#
# The cell below prints work per case, the output measure behind the scaling chart and the fitted exponents.

# %%
if NOTEBOOK_RUN:
    rows = []
    owner_chars = final_acc.loc["One owner"].task_chars_per_case
    for label in ARM_LABELS:
        a = final_acc.loc[label]
        rows.append({"Arm": label, "Prompt characters": f"{a.prompt_chars_per_case:,.0f}", "Reply characters": f"{a.reply_chars_per_case:,.0f}",
                     "Total per case": f"{a.task_chars_per_case:,.0f}", "Times the owner's work": f"{a.task_chars_per_case / owner_chars:.2f}",
                     "Accuracy": pct(a.accuracy)})
    print(pd.DataFrame(rows).to_string(index=False))
    show_figure("work_per_case")

# %% [markdown]
# The scaling chart puts agents and the output measure from section 4 on log scales, so a line's slope is the exponent; the dotted line is proportional growth.
#
# The printed points below are the output per 1,000 characters for each team size, and the fitted exponent with its interval.

# %%
if NOTEBOOK_RUN:
    points_first, points_final = by_parser("scaling_points", "first"), by_parser("scaling_points", "last")
    rows = []
    for name, frame in (("final", points_final), ("first", points_first)):
        row = {"Reading": name}
        for _, r in frame.iterrows():
            row[f"k={int(r.k)}"] = f"{1000 * r.output:.3f}"
        rows.append(row)
    print("Correct output per 1,000 characters (k x accuracy / thousand characters per case)")
    print(pd.DataFrame(rows).to_string(index=False))
    for name in ("last", "first"):
        s = by_parser("scaling", name).iloc[0]
        pts = by_parser("scaling_points", name)
        ratio = pts[pts["k"] == 8]["output"].iloc[0] / pts[pts["k"] == 1]["output"].iloc[0]
        print(f"{name}: exponent {s.slope:.2f} (interval {s.low:.2f} to {s.high:.2f}), {int(s.n_cases)} cases; eight agents give {ratio:.3f} times one owner's output per character")
    show_figure("pipeline_scaling")

# %% [markdown]
# On final answers the points are 0.091 for one owner, then 0.103, 0.126 and 0.116 for pipelines of 2, 4 and 8, an exponent of 0.13 (interval 0.03 to 0.22); on first answers, 0.089, 0.095, 0.120 and 0.096, an exponent of 0.07 (interval -0.05 to 0.18). With the same budget per agent, eight agents produced about 27% more correct cases than one (8% on first answers), where proportional growth would give eight times as many.
#
# The scatter from the study summary, repeated here, puts work and accuracy together. Each point is an arm: right means more work per case, up means more cases fully correct; hollow markers are control arms. The pipelines move right without moving up; the pipeline of 8 uses 4.4 times the owner's characters and finishes 20 fewer cases. The top-right group reaches 99% to 100% with 4.0 to 5.0 times the owner's work; Terra alone reaches 97.5% at the owner's cost.

# %%
if NOTEBOOK_RUN:
    show_figure("accuracy_vs_work")

# %% [markdown]
# ## 17. Unreadable forms and two ways to read a reply
#
# Each bar splits an arm's cases into correct, wrong and unreadable. On final answers 10 of 640 case results were unreadable and 80 were wrong (11 and 97 on first answers). Nine unreadable cases were in the pipeline of 2 (credit-4802, 4803, 4805, 4809, 4816, 4817, 4819, 4820, trade-4803): agent 1 returned only its first stations' fields, and agent 2 was not allowed to fill the rest. The tenth, lab-4806 in the pipeline of 4, never filled payable_codes. In eight of the nine the notes held the right values for every missing field and every filled field was right; in `credit-4817` the conditions also lacked VALUATION.
#
# The cell below prints the counts for each arm under both readings, then every unreadable case under the final-answer reading with the fields it never filled and whether the fields it did fill were right.

# %%
if NOTEBOOK_RUN:
    rows = []
    for label in ARM_LABELS:
        a, b = final_acc.loc[label], first_acc.loc[label]
        rows.append({"Arm": label, "Correct": int(a.correct), "Wrong": int(a.wrong), "Unreadable": int(a.unreadable),
                     "Correct (first)": int(b.correct), "Wrong (first)": int(b.wrong), "Unreadable (first)": int(b.unreadable)})
    print(pd.DataFrame(rows).to_string(index=False))
    print(f"\nAll arms: {int(final_acc.n.sum())} case results; final answers {int(final_acc.unreadable.sum())} unreadable, {int(final_acc.wrong.sum())} wrong; "
          f"first answers {int(first_acc.unreadable.sum())} unreadable, {int(first_acc.wrong.sum())} wrong")
    show_figure("unreadable_and_wrong")

    final_rows = pd.read_csv(RESULTS_FILES["last"])
    unreadable = final_rows[final_rows["status"] == "unreadable"].sort_values(["design", "k", "case_id"])
    for _, row in unreadable.iterrows():
        per_field = json.loads(row["per_field_correct"])
        filled = json.loads(row["final_fields"])
        filled_ok = all(per_field[f] for f in filled)
        print(f"{row['case_id']:<13}{row['design']}/{row['k']}: {row['unreadable_reasons']}; every filled field correct: {filled_ok}")

# %% [markdown]
# ### Worked example: `credit-4802` in the pipeline of 2
#
# The first unreadable case in id order, unreadable under both readings. Agent 1's prompt says "Your fields, all of which you must return: complete, bureau_score, exposure_cad, decision". It returned `{"fields":{"complete":false}, ...}` with a note holding the inputs:
#
# > consent signed is NO, so complete is false [...] Intake summary bureau_score 691 matches the bureau report's verified score 691. Bankruptcy per bureau report: YES. Existing CAD exposure 230000.00 [...]
#
# Agent 2, covering stations 5 to 8, worked out the missing answers in its note, but they were not its fields:
#
# > Decision is DECLINE: the bureau report shows bankruptcy YES, and policy says this outranks the referral rules, so MANAGER_REVIEW is not included. [...] Exposure is 420000.00 CAD (190000.00 requested + 230000.00 existing) [...]

# %%
if NOTEBOOK_RUN:
    def excerpts(text, words=(), width=300, limit=3):
        """Up to `limit` short excerpts of a note, each around one of the keywords (the start of the note when none is found)."""
        text = " ".join(str(text).split())
        spans, found = [], []
        for word in words:
            i = text.find(word)
            if i < 0 or any(a <= i < b for a, b in spans):
                continue
            start = max(0, i - width // 5)
            spans.append((start, start + width))
            found.append(("[...] " if start else "") + text[start:start + width] + (" [...]" if start + width < len(text) else ""))
            if len(found) == limit:
                break
        return found or [text[:width] + (" [...]" if len(text) > width else "")]


    def snippet(text, words=(), width=300):
        return excerpts(text, words, width, limit=1)[0]


    def agent_view(case_id, design, k, parser="last", agents=None, words=(), width=300, model=None):
        result = DETAILS[parser][(model or SONNET, design, k)][case_id]
        case = CASES_BY_ID[case_id]
        print(f"{case_id}, {design} of {k}, {parser} answers; status {score_case(case, result)['status']}")
        for note in result["notes"]:
            number = note["station_index"] + 1
            if agents and number not in agents:
                continue
            shown = {f: (v if not isinstance(v, float) else round(v, 2)) for f, v in note["fields"].items()}
            print(f"  agent {number} fields {json.dumps(shown)}")
            for piece in excerpts(note["note"], words, width):
                print(f"          note: {piece}")


    agent_view("credit-4802", "pipeline", 2, words=("consent signed", "Decision is DECLINE"), width=420)
    print("\nexpected:", {f: CASES_BY_ID["credit-4802"]["truth"][f] for f in ("complete", "bureau_score", "exposure_cad", "decision")})

# %% [markdown]
# Its six fields were all right. The expected bureau_score 691, exposure_cad 420000.00 and decision DECLINE appear in the notes but not the form; the owner got the case right in one call. Eight of 20 credit cases failed this way in the pipeline of 2.
#
# ### Two ways to read a reply
#
# Left bars are first-answer scores, right bars final-answer scores. Four arm totals change: one owner by 2 cases, the pipelines of 2, 4 and 8 by 5, 3 and 8.
#
# The cell below counts the replies that hold more than one JSON object, splits them by arm, and lists how the case results changed between the two readings. Then the figure.

# %%
if NOTEBOOK_RUN:
    distinct = {}
    for parser_name in PARSERS:
        for (model_key, design, k), per_case in DETAILS[parser_name].items():
            if model_key != SONNET:
                continue
            for case_id, result in per_case.items():
                for call in result["calls"]:
                    distinct.setdefault(call["reply"]["cache_key"], (design, k, case_id, call["reply"]["text"]))
    multi = {key: v for key, v in distinct.items() if len(_json_objects(v[3])) > 1}
    differ = {key: v for key, v in multi.items() if parse_differs(v[3])}
    print(f"Distinct Sonnet replies in the scored arms (both readings): {len(distinct):,}")
    print(f"  hold more than one JSON object: {len(multi)}; the later object has a fields key and changes the reading: {len(differ)}")
    first_chains = {key for (model_key, design, k), per_case in DETAILS["first"].items() if model_key == SONNET
                    for result in per_case.values() for call in result["calls"] for key in [call["reply"]["cache_key"]]}
    order = {"owner": 0, "pipeline": 1, "shared": 2, "checker": 3, "review": 4}
    by_arm = collections.Counter()
    for key, (design, k, case_id, text) in differ.items():
        if key in first_chains:
            by_arm[(design, k)] += 1
    print("  of those, by the arm that first used the reply (a reply shared by two arms counts once):",
          {f"{d}/{k}": n for (d, k), n in sorted(by_arm.items(), key=lambda x: (order[x[0][0]], x[0][1]))})
    outside = sorted(v[2] + " " + f"{v[0]}/{v[1]}" for key, v in multi.items() if key not in differ)
    print("  more than one object, but the later one has no fields key (both readings take the first):", outside)

    changes = final_rows.merge(pd.read_csv(RESULTS_FILES["first"])[["case_id", "model", "design", "k", "status"]], on=["case_id", "model", "design", "k"], suffixes=("_final", "_first"))
    changed = changes[changes["status_final"] != changes["status_first"]]
    print(f"\nCase results whose status differs between the readings: {len(changed)}")
    print(changed.groupby(["status_first", "status_final"]).size().to_string())
    for _, row in changed[changed["status_final"] != "correct"].iterrows():
        print(f"  {row['case_id']} {row['design']}/{row['k']}: {row['status_first']} -> {row['status_final']}")
    print("  arms with a changed total:", {label: (int(first_acc.loc[label].correct), int(final_acc.loc[label].correct)) for label in ARM_LABELS if first_acc.loc[label].correct != final_acc.loc[label].correct})
    show_figure("parser_comparison")

# %% [markdown]
# Twenty-five Sonnet replies held more than one JSON object. In 23 the later object has a `fields` key and is what the final-answer reading takes: 2 from the owner, 6, 3 and 11 from the pipelines of 2, 4 and 8, and 1 from a reviewer. In the other 2 (`capital-4811`, `lab-4808`, pipeline of 2) the correction sits outside any object with fields, so both readings take the first. Re-reading and re-running changed 20 case results: 18 became correct, `credit-4820` (pipeline of 2) went from wrong to unreadable because the revision dropped two fields, and `credit-4819` (pipeline of 8) from unreadable to wrong because the revised exposure was also wrong.

# %% [markdown]
# #### Worked example: `trade-4806` in the pipeline of 8
#
# Chosen because one reply, read two ways, changes the rest of the chain. The email says "Iris mentioned that the final ticket must carry the CLIENT_REVIEW flag", and 37 shares are left over after whole lots. Expected: flags CLIENT_REVIEW, RESTRICTED, ODD_LOT; reconciled false; commission 44.53. One owner got all 11 fields right.
#
# Agents 1 to 6 carried the flag and the odd lot. Agent 7 wrote a first object with authority SENIOR and a note only about authority, then "Correction: the JSON above is superseded by this one", and a second with DIRECTOR and a note keeping "flags ODD_LOT (37 residual shares, executed 1637, allocated 1600, reconciled false), RESTRICTED, CLIENT_REVIEW".
#
# The cell below prints the agents' fields and notes for that case under each reading.

# %%
if NOTEBOOK_RUN:
    for parser_name in PARSERS:
        agent_view("trade-4806", "pipeline", 8, parser=parser_name, agents=(7, 8), words=("Correction", "ODD_LOT", "only RESTRICTED", "CLIENT_REVIEW", "commission"), width=420)
        print()
    case = CASES_BY_ID["trade-4806"]
    print("expected:", json.dumps({f: case["truth"][f] for f in ("exception_flags", "reconciled", "commission_cad")}))
    for parser_name in PARSERS:
        result = DETAILS[parser_name][(SONNET, "pipeline", 8)]["trade-4806"]
        print(parser_name, "wrong fields:", [f for f, ok in score_case(case, result)["per_field_correct"].items() if not ok])

# %% [markdown]
# On first answers, agent 8 received the draft note and wrote "no explicit ODD_LOT, MANUAL, LATE, SSI_HOLD, CLIENT_REVIEW or LEGAL_REVIEW information was given, so only RESTRICTED is flagged": four fields wrong. On final answers, agent 8, re-run with the revised note, wrote "37 residual odd shares held unallocated (ODD_LOT), so reconciled is false. Accounts B and C restricted (RESTRICTED). CLIENT_REVIEW carried from early correspondence": only the commission was wrong, where agent 5's note computed 44.53 but its field said 43.52.

# %% [markdown]
# ## 18. Error analysis
#
# Each example is one case of a pattern, on final answers unless stated; how common it is comes from counts over all 80 cases.
#
# The cells below print the agents' fields and note excerpts for each example from the saved records, so that every quotation can be found in the data. A cell's excerpts are chosen by a keyword; an agent's full note is in `data/tmp/results_last_object.calls.jsonl` after the replay in section 7.

# %% [markdown]
# ### A typical pipeline success: `credit-4811`, pipeline of 4
#
# An ordinary success (60 of 80 pipeline-of-4 cases were fully correct) that also tests the intake note, which said 670 where the bureau report says 570. Agent 1 wrote "verified score 570 (the intake summary's 670 is wrong; the signed bureau report governs)" and "include OWNERSHIP_UNDERTAKING in conditions". Agent 2 declined on three hard rules, noting "MANAGER_REVIEW applies only if REFER". Agents 3 and 4 repeated the undertaking, and all 10 fields came out right under both readings.

# %%
if NOTEBOOK_RUN:
    agent_view("credit-4811", "pipeline", 4, words=("670 is wrong", "include OWNERSHIP_UNDERTAKING", "applies only if REFER", "hard rules", "ownership undertaking"), width=260)
    c = CASES_BY_ID["credit-4811"]
    print("intake note:", c["intake_note"].splitlines()[1], "| bureau report:", [l for l in c["documents"]["bureau"].splitlines() if "score" in l][0])

# %% [markdown]
# ### The planted fact lost in the pipeline of 8: `credit-4807` and `trade-4817`
#
# `credit-4807` is one of the two cases where the fact was dropped; one owner got it right. The email says "Leila mentioned that release must also await a signed ownership undertaking", so the conditions should be OWNERSHIP_UNDERTAKING and the authority ANALYST. Agents 1 to 6 carried it ("OWNERSHIP_UNDERTAKING applies even on decline", agent 6). Agent 7's note discussed only authority, and its field said MANAGER although its own note ended "so authority = ANALYST". Agent 8 wrote "They also contain no early correspondence, so no ENV_UNDERTAKING or OWNERSHIP_UNDERTAKING request is recorded" and returned empty conditions: two fields wrong, under both readings, since agent 7's correction sits in its note.
#
# `trade-4817` shows the commoner kind, 14 of the 16: the fact reaches the end, but its standing erodes. Agent 1 wrote "Bespoke review flag: LEGAL_REVIEW." Agent 3 added "not a signed record"; agent 6, "downstream should treat it as unverified". Agent 8: "LEGAL_REVIEW not set: it appears only in the relationship administrator's account of Iris, not in a signed record or confirmed early correspondence, so it is unverified."

# %%
if NOTEBOOK_RUN:
    agent_view("credit-4807", "pipeline", 8, agents=(1, 6, 7, 8), words=("applies even on decline", "so authority = ANALYST", "no early correspondence"), width=300)
    print("planted sentence:", CASES_BY_ID["credit-4807"]["params"]["planted_sentence"])
    print("expected conditions:", CASES_BY_ID["credit-4807"]["truth"]["conditions"], "| expected authority:", CASES_BY_ID["credit-4807"]["truth"]["authority"])
    print("one owner on this case:", score_case(CASES_BY_ID["credit-4807"], DETAILS["last"][(SONNET, "owner", 1)]["credit-4807"])["status"])
    print()
    agent_view("trade-4817", "pipeline", 8, agents=(1, 3, 6, 8), words=("Bespoke review flag", "not a signed record", "should treat it as unverified", "LEGAL_REVIEW not set"), width=300)

# %% [markdown]
# ### Laboratory billing in the pipeline of 4: `lab-4801`
#
# The first of seven laboratory cases the pipeline of 4 got wrong on `billed_to` under both readings, all of which the owner got right. The email says "Noah noted that the employer has agreed to receive every patient-pay charge". Agent 1 wrote "relationship mailbox says employer agreed to receive every patient-pay charge (billed_to EMPLOYER)". Agent 3 passed it on but changed its source: "this is from the intake summary and I could not verify it against a signed record, so confirm". Agent 4, which owns `billed_to` and sees "Default payer: PATIENT", wrote:
#
# > billed_to is PATIENT because no signed early correspondence is in the records. The EMPLOYER arrangement comes only from the intake summary (relationship mailbox), which the previous agent said it could not verify.
#
# Every other field was right. The owner, reading the email itself, set EMPLOYER, and Terra as checker restored it. In all seven laboratory losses the last agent set the arrangement aside as unverified.

# %%
if NOTEBOOK_RUN:
    rows = pd.read_csv(RESULTS_FILES["last"])
    pipe4 = rows[(rows["model"] == SONNET) & (rows["design"] == "pipeline") & (rows["k"] == 4) & (rows["process"] == "lab")]
    bad = [r["case_id"] for _, r in pipe4.iterrows() if not json.loads(r["per_field_correct"])["billed_to"]]
    owner_ok = [c for c in bad if json.loads(rows[(rows["model"] == SONNET) & (rows["design"] == "owner") & (rows["case_id"] == c)]["per_field_correct"].iloc[0])["billed_to"]]
    print(f"laboratory cases the pipeline of 4 got wrong on billed_to: {len(bad)} {bad}; one owner right on all of them: {len(owner_ok) == len(bad)}")
    agent_view("lab-4801", "pipeline", 4, agents=(1, 3, 4), words=("employer agreed to receive", "could not verify it against", "billed_to is PATIENT"), width=300)
    print("\nexpected billed_to:", CASES_BY_ID["lab-4801"]["truth"]["billed_to"])

# %% [markdown]
# ### An owner error a reviewer corrected: `capital-4803`
#
# The first capital case among the 12 owner errors the first reviewer fixed. The schedule says "Purpose: INVESTMENT", the fee equals the allowed fee and expenses are 8,000.00 against a 5,000.00 cap, so the only deduction is 3,000.00: eligible amount 84,680.72, codes EXPENSE_CAP and BANK_HOLD. The owner deducted 9,000.00 and listed EXCLUDED_PURPOSE, a penalty that does not exist. Reviewer 1:
#
# > the earlier record deducted 9000 and listed EXCLUDED_PURPOSE, but no PENALTY investment exists (the breakdown schedule shows INVESTMENT purpose only). The only deduction is the expense excess of 3000.00
#
# Five of the owner's 13 errors were capital calls, four with wrong deduction amounts, and five were laboratory rejection-code lists; a pass that redoes the work from the documents catches them.

# %%
if NOTEBOOK_RUN:
    c = CASES_BY_ID["capital-4803"]
    owner = DETAILS["last"][(SONNET, "owner", 1)]["capital-4803"]
    print("owner returned:", {f: owner["fields"][f] for f in ("eligible_amount", "exception_codes")}, "| expected:", {f: c["truth"][f] for f in ("eligible_amount", "exception_codes")})
    review = DETAILS["last"][(SONNET, "review", 4)]["capital-4803"]
    print("reviewer 1 note:", snippet(review["notes"][1]["note"], ("the earlier record deducted",), 420))
    owner_wrong = [cid for cid, res in DETAILS["last"][(SONNET, "owner", 1)].items() if score_case(CASES_BY_ID[cid], res)["status"] != "correct"]
    print(f"\nowner errors: {len(owner_wrong)}; by process {dict(collections.Counter(CASES_BY_ID[c]['process'] for c in owner_wrong))}")
    lab_codes = [c for c in owner_wrong if CASES_BY_ID[c]["process"] == "lab" and not score_case(CASES_BY_ID[c], DETAILS["last"][(SONNET, "owner", 1)][c])["per_field_correct"]["rejection_codes"]]
    print("laboratory errors on the rejection-code list:", len(lab_codes))

# %% [markdown]
# ### A rule read two ways: MANAGER_REVIEW on a declined file
#
# The policy says "conditions includes COMPLETE_FILE if incomplete, VALUATION if USED, MANAGER_REVIEW if REFER, even on decline." The exact answer adds MANAGER_REVIEW only to referred files, but "even on decline" can be read as covering it. That reading appeared once for the owner, once in the shared record, 5 times in the pipeline of 4 and 3 times in the pipeline of 8. On `credit-4802` in the pipeline of 4, agent 2 wrote "MANAGER_REVIEW and COMPLETE_FILE apply as conditions even on decline", and the last agent copied it.

# %%
if NOTEBOOK_RUN:
    final_rows = pd.read_csv(RESULTS_FILES["last"])
    credit = final_rows[(final_rows["process"] == "credit") & (final_rows["model"] == SONNET)]
    extra = {}
    for _, r in credit.iterrows():
        truth = CASES_BY_ID[r["case_id"]]["truth"]["conditions"]
        got = json.loads(r["final_fields"]).get("conditions", [])
        if "MANAGER_REVIEW" in got and "MANAGER_REVIEW" not in truth:
            extra[(r["design"], r["k"])] = extra.get((r["design"], r["k"]), 0) + 1
    print("credit cases whose conditions add MANAGER_REVIEW although the exact answer has none, by arm:", extra)
    print("\npolicy line:", [l for l in CASES_BY_ID["credit-4802"]["documents"]["policy"].splitlines() if "MANAGER_REVIEW" in l][0])
    agent_view("credit-4802", "pipeline", 4, agents=(2, 4), words=("MANAGER_REVIEW and COMPLETE_FILE apply", "MANAGER_REVIEW"), width=300)

# %% [markdown]
# ## 19. Limitations
#
# The control arms and the final-answer reading were chosen after the results were seen; first-answer results are reported beside them, and no conclusion depends on which is used. The design and measures were fixed before any model call; later changes are recorded with reasons in [`data/PROTOCOL.md`](data/PROTOCOL.md).
#
# Only Sonnet formed the teams, at low effort; another model or more reasoning might carry notes better or revise less. Every case fits in one prompt of about 8,000 characters, which favours one agent with everything. With 80 cases the pipelines of 2 and 4 are not clearly separated from one owner, and process-level gaps rest on a few cases.
#
# Agents also corrected themselves inside notes, which neither reading uses (`credit-4807`, the trade commissions), and the 10 unreadable forms count as failures. The teams have no people, sign-offs, separation of duties or parallel work, and no agent could ask a question back up the line. The instruction to prefer signed records may have made late agents distrust retold facts.
#
# Sonnet ran as Claude Code subagents rather than through `claude -p` as this repository's rules ask. GPT-6.1 Sol wrote the code that generates the cases and rules, Claude Sonnet 5.5 subagents made later fixes, and Claude designed the analysis and wrote this text. Sol and Terra come from the same vendor; whether that helps Terra is untested.

# %% [markdown]
# ## 20. What the evidence supports
#
# For work of this size, where the case fits in one prompt, give one agent every document: the pipeline of 8 used 4.4 times the work and finished 20 fewer cases. If a second agent is affordable, use it for a full second pass over the whole case: one reviewer took the owner from 67 to 78, a second reached 80, a third changed nothing. A stronger model alone reached 78 of 80 at the owner's cost.
#
# If the work must be divided, give every agent the original documents rather than a colleague's retelling, since most lost facts arrived and were set aside as unverified. Decide in advance which object in a reply counts, and test that rule on replies that revise themselves.
#
# Whether design matters when no agent can hold the whole case, or for other models, needs another experiment.

# %% [markdown]
# ## 21. Spend, data and how to reproduce
#
# Both tools ran on subscriptions with no per-call bill. Counts are distinct replies in the scored arms; tests and calibration add 290 Sonnet and about 37 Terra calls. The next cell prints the spend table for the scored arms, as the analysis prints it, and splits the Sonnet calls by origin.

# %%
if NOTEBOOK_RUN:
    all_calls = [c for parser_name in PARSERS for per_case in DETAILS[parser_name].values() for result in per_case.values() for c in result["calls"]]
    overheads = {TERRA: float(pd.read_csv(RESULTS_FILES["first"]).groupby("model")["overhead_input_tokens"].max().get(TERRA))}
    print(format_spend(spend_from_calls(all_calls, overheads)))


    def distinct_requests(parser_name):
        """Distinct requests of one reading: cache key -> (model that answered, designs of the runs that used it)."""
        keys = {}
        for (_, design, k), per_case in DETAILS[parser_name].items():
            for result in per_case.values():
                for call in result["calls"]:
                    model_name, designs = keys.setdefault(call["reply"]["cache_key"], (call["model"], set()))
                    designs.add(design)
        return keys


    first_keys, last_keys = distinct_requests("first"), distinct_requests("last")
    sonnet_first = {k for k, v in first_keys.items() if v[0] == SONNET}
    main_keys = {k for k in sonnet_first if first_keys[k][1] != {"review"}}
    review_only = sonnet_first - main_keys
    new_sonnet = {k for k, v in last_keys.items() if v[0] == SONNET} - sonnet_first
    terra_first = {k for k, v in first_keys.items() if v[0] == TERRA}
    new_terra = {k for k, v in last_keys.items() if v[0] == TERRA} - terra_first
    print(f"\nSonnet calls: {len(main_keys)} main comparison, {len(review_only)} review arm (its first agent reuses the owner's reply), {len(new_sonnet)} re-runs for the final-answer reading.")
    print(f"Terra calls: {len(terra_first)} in the first-answer run (80 checker, 80 single owner), {len(new_terra)} checker re-runs.")
    print("Calls and traces made by this notebook: 0 and 0.")

# %% [markdown]
# Files, all beside this notebook:
#
# - `agent_teams.py` is generated from this notebook (see the last cell), with the same code in the same order, and adds the command line described below.
# - `data/results_last_object.csv` and `data/results.csv`: one row per case and arm, scored on final answers and on first answers.
# - `data/accuracy.csv`, `by_process.csv`, `paired.csv`, `scaling.csv` and `scaling_points.csv`: the tables above, each with a `parser` column; `data/parser_report.csv`: the replies the two readings differ on.
# - `data/cases.jsonl`: the 80 cases; `data/cache_requests.jsonl`: every request and response, keyed by a hash of the full request; `data/calibration_*.csv`: the separate calibration cases.
# - `data/PROTOCOL.md`: the design fixed before any call and every recorded change.
# - `data/tmp/` (git-ignored): per-call records under each reading, rebuilt from the cache by section 7.
# - `figures/`: the eleven figures, drawn by section 11.
#
# To reproduce with no model calls, install the repository's `requirements.txt` and run `python -m nbconvert --to notebook --execute --inplace 48_agent_team_designs.ipynb` in this folder. The run replays every reply from the cache, rebuilds both results tables and checks them against the committed ones, and redraws the tables and figures. New Claude replies are collected in rounds, one per pipeline agent: `python agent_teams.py --run --export-pending --parser last` writes the waiting prompts (default `data/tmp/rounds/pending.json`), `--make-workflow data/tmp/rounds/pending.json data/tmp/rounds/round1` writes workflow files and `round1_parent.js`, the parent file is run in Claude Code, and `--import-journal RUN_DIR data/tmp/rounds/pending.json` imports the replies. GPT calls go through `codex exec` from `--run`.
#
# ### Command line
#
# The two code cells below define the command line; the generated script moves them to its end. `main` offers these modes, and the final cell runs it only when the generated script is started from a terminal (never in a notebook): `--selftest`, `--show-case PROCESS SEED`, `--run`, `--calibrate`, `--export-pending`, `--make-workflow`, `--import-replies`, `--import-journal`, `--replay`, `--parser-report`, `--analyse` and `--smoke`, with `--parser first|last`, `--models`, `--designs` and `--team-sizes` for the live modes. Only `--run`, `--calibrate` and `--smoke` can call a model, and only when named.

# %% [markdown]
# ### Keeping the script in step with the notebook
#
# `agent_teams.py` must not drift from this notebook, so it is generated from it. The cell below converts the notebook's cells into the script: markdown cells become `# %% [markdown]` comments, code cells keep their text, the cells that only show results (tagged `notebook-only`) are wrapped in `if NOTEBOOK_RUN:`, so importing or running the script prints and draws nothing, and the command-line cells (tagged `command-line`) move to the end. The default is not to write. Set `WRITE_SCRIPT = True` and run the cell to regenerate the script.

# %%
if NOTEBOOK_RUN:
    WRITE_SCRIPT = False
    NOTEBOOK_FILE = Path("48_agent_team_designs.ipynb")
    SCRIPT_FILE = Path("agent_teams.py")
    SCRIPT_HEADER = ("# Generated from 48_agent_team_designs.ipynb, do not edit. Regenerate it by setting WRITE_SCRIPT = True in the\n"
                     "# last code cell of the notebook and running that cell, then run: python agent_teams.py --selftest\n")


    def notebook_to_script(notebook, header=SCRIPT_HEADER):
        parts, command_line = [header], []
        for cell in notebook["cells"]:
            text = "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"]
            tags = cell.get("metadata", {}).get("tags", [])
            if cell["cell_type"] == "markdown":
                parts.append("# %% [markdown]\n" + "\n".join(("# " + line).rstrip() for line in text.split("\n")) + "\n")
            elif cell["cell_type"] == "code":
                if "notebook-only" in tags:
                    text = "if NOTEBOOK_RUN:\n" + "\n".join(("    " + line) if line.strip() else line for line in text.split("\n"))
                (command_line if "command-line" in tags else parts).append("# %%\n" + text + "\n")
        return "\n".join(parts + command_line)


    if WRITE_SCRIPT:
        SCRIPT_FILE.write_text(notebook_to_script(json.loads(NOTEBOOK_FILE.read_text(encoding="utf-8"))), encoding="utf-8", newline="\n")
        print(f"wrote {SCRIPT_FILE} from {NOTEBOOK_FILE}")
    else:
        print("WRITE_SCRIPT is False: agent_teams.py was not touched.")

# %% [markdown]
# ## 22. Future work and further reading
#
# ### Future work
#
# - Make cases too large for one prompt (say 60 documents) and measure whether the pipeline or shared record catches up with one owner. Motivated by the owner's lead when every case fits in about 8,000 characters.
# - Require notes to quote the original sentence and name its source, and measure the planted fact kept in the pipelines of 4 and 8. Motivated by the 14 of 16 lost facts that arrived as a retelling and were set aside.
# - Put the note before the fields and allow one object per reply, and measure how often agents still revise. Motivated by the 23 replies revised after a first answer, 20 in pipelines.
# - Run the designs with Terra as the team, as first planned, and measure whether the ranking holds for a second model family.
# - Compare one reviewer with two, and a reviewer who sees the owner's form with one who works blind, measuring cost per fully correct case. Motivated by the first reviewer fixing 12 cases and breaking 1.
#
# ### Further reading
#
# Links checked on 21 November 2026.
#
# - [Organizing Intelligence](https://storage.googleapis.com/deepmind-media/papers/organizing-intelligence.pdf) (Imas, Koh and Legg, 2026). A model of firms where competence raises output and coordination sets how output grows with size; Terra's lead and the small exponent here are measured cases of each.
# - [Why Do Multi-Agent LLM Systems Fail?](https://arxiv.org/abs/2503.13657) (Cemri et al., 2025). A taxonomy of 14 failure modes from seven multi-agent frameworks, including inter-agent misalignment, which the dropped and distrusted notes here resemble.
# - [TheAgentCompany](https://arxiv.org/abs/2412.14161) (Xu et al., 2024). Single agents on office tasks in a simulated software company, the best completing about 30%; longer tool-using work than these cases.
# - [The Cybernetic Teammate](https://www.nber.org/papers/w33641) (Dell'Acqua et al., 2025). A field experiment with 776 professionals where one person with AI matched a two-person team without it, a human parallel to the single agent here.
# - [Drop the Hierarchy and Roles](https://arxiv.org/abs/2603.28990) (Dochkina, 2026). Eight coordination protocols over 25,000 tasks; a lightly structured sequential protocol beat centralised coordination by 14%. It varies who coordinates, this notebook who sees which documents.

# %%
def main(argv=None):
    global PARSER
    parser = argparse.ArgumentParser(description="Notebook 48: agent team designs (offline unless a live mode is explicit)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--selftest", action="store_true")
    mode.add_argument("--show-case", nargs=2, metavar=("PROCESS", "SEED"))
    mode.add_argument("--calibrate", action="store_true")
    mode.add_argument("--run", action="store_true")
    mode.add_argument("--analyse", action="store_true")
    mode.add_argument("--smoke", action="store_true")
    mode.add_argument("--make-workflow", nargs=2, metavar=("PENDING_FILE", "OUT_PREFIX"),
                      help="write OUT_PREFIX_1.js, OUT_PREFIX_2.js, ... and OUT_PREFIX_parent.js from an exported pending file")
    mode.add_argument("--import-replies", nargs="+", metavar="FILE", help="import subagent replies into the cache")
    mode.add_argument("--import-journal", nargs=2, metavar=("RUN_DIR", "PENDING_FILE"),
                      help="import replies from every journal.jsonl under RUN_DIR, matching agent labels to the keys in PENDING_FILE")
    mode.add_argument("--parser-report", action="store_true",
                      help="list every cached reply that parses differently under the two parsers, count the chains to re-run "
                           "and the first round's prompts, and score the runs that need no new call; writes data/parser_report.csv")
    mode.add_argument("--replay", "--replay-check", dest="replay", action="store_true",
                      help="rebuild results.csv and calibration_results.csv from the cache with zero model calls; fails on any cache miss")
    parser.add_argument("--export-pending", action="store_true",
                        help="with --run or --calibrate: list the subagent prompts waiting for replies (needs --out)")
    parser.add_argument("--out", default=str(TMP / "rounds" / "pending.json"), help="output file for --export-pending (default data/tmp/rounds/pending.json)")
    parser.add_argument("--parser", choices=PARSERS, help="how a reply with several JSON objects is read: first (fixed in advance) or last; "
                        "honoured by --run, --calibrate, --export-pending, --replay and --analyse (default: first; --analyse draws figures for PRIMARY_PARSER)")
    parser.add_argument("--agent-type", help="agentType option for each agent() call in --make-workflow")
    parser.add_argument("--chunk", type=int, default=40, help="most items per workflow file for --make-workflow (lowered automatically to keep each file under 500,000 bytes)")
    parser.add_argument("--models", help="comma-separated model names from the models table (with --run or --calibrate)")
    parser.add_argument("--designs", help="comma-separated designs: owner,pipeline,shared,checker,review (with --run or --calibrate); review runs only when named")
    parser.add_argument("--team-sizes", help="comma-separated pipeline sizes, for example 4 (with --run or --calibrate)")
    args = parser.parse_args(argv)
    chosen = args.parser or PARSER
    PARSER = chosen
    selected_models = list(MODELS)
    if args.models:
        wanted = [n.strip() for n in args.models.split(",") if n.strip()]
        unknown = [n for n in wanted if n not in {m["name"] for m in MODELS}]
        if unknown:
            parser.error(f"Unknown model(s) {unknown}; choose from {[m['name'] for m in MODELS]}")
        selected_models = [m for m in MODELS if m["name"] in wanted]
    selected_designs = list(DESIGNS)
    if args.designs:
        selected_designs = [d.strip() for d in args.designs.split(",") if d.strip()]
        unknown = [d for d in selected_designs if d not in ALL_DESIGNS]
        if unknown:
            parser.error(f"Unknown design(s) {unknown}; choose from {ALL_DESIGNS}")
    selected_sizes = None
    if args.team_sizes:
        try:
            selected_sizes = [int(v) for v in args.team_sizes.split(",")]
        except ValueError:
            parser.error("--team-sizes takes comma-separated integers")
        bad = [k for k in selected_sizes if k not in TEAM_SIZES]
        if bad:
            parser.error(f"Unsupported team size(s) {bad}; choose from {TEAM_SIZES}")
    if (args.models or args.designs or args.team_sizes) and not (args.run or args.calibrate):
        parser.error("--models, --designs and --team-sizes apply only with --run or --calibrate")
    if args.export_pending and not (args.run or args.calibrate):
        parser.error("--export-pending needs --run or --calibrate")
    if args.make_workflow:
        make_workflow(args.make_workflow[0], args.make_workflow[1], args.chunk, agent_type=args.agent_type)
        return 0
    if args.import_replies:
        import_replies(args.import_replies)
        return 0
    if args.import_journal:
        import_journal(*args.import_journal)
        return 0
    if args.parser_report:
        parser_report()
        return 0
    if args.replay:
        return 0 if replay_all(parser=chosen) else 1
    if args.export_pending:
        if args.calibrate:
            names = [n.strip() for n in args.models.split(",")] if args.models else CALIBRATION_MODELS
            export_models = [m for m in MODELS if m["name"] in names]
            export_cases = generate_cases(CALIBRATION_SEED, 6)
            export_designs = selected_designs if args.designs else ["owner", "pipeline"]
            export_sizes = selected_sizes or [4]
        else:
            export_models, export_designs, export_sizes = selected_models, selected_designs, selected_sizes
            export_cases = load_or_make_cases(DATA / "cases.jsonl", SEED, N_CASES_PER_PROCESS)
        export_pending(export_cases, export_models, export_designs, export_sizes, args.out, parser=chosen)
        return 0
    if args.selftest:
        return 0 if selftest() else 1
    if args.show_case:
        process, seed = args.show_case
        case = make_case(process, int(seed))
        for name, text in case["documents"].items():
            print(f"\nDOCUMENT {name}\n{text}")
        print("\nINTAKE NOTE\n" + case["intake_note"])
        print("\nTRUTH\n" + json.dumps(case["truth"], indent=2))
        print("\nPLANTED FACT\n" + case["params"]["planted_sentence"])
        print("\nOWNER PROMPT\n" + build_prompt(case, "owner", 1))
        return 0
    if args.analyse:
        analyse(primary=args.parser or PRIMARY_PARSER)
        return 0
    if args.run:
        print(models_table())
        cases = load_or_make_cases(DATA / "cases.jsonl", SEED, N_CASES_PER_PROCESS)
        # Parser "last" copies the runs whose replies parse the same under both parsers and runs only the others.
        reuse = unchanged_runs(RESULTS_FILES["first"]) if chosen == "last" else None
        run_all(cases, selected_models, selected_designs, output=RESULTS_FILES[chosen], team_sizes=selected_sizes,
                cases_path=DATA / "cases.jsonl", parser=chosen, reuse=reuse)
        return 0
    if args.calibrate:
        # Calibration never touches the scored files: it has its own results and case files.
        names = args.models.split(",") if args.models else CALIBRATION_MODELS
        models = [m for m in MODELS if m["name"] in [n.strip() for n in names]]
        if not models:
            parser.error("Calibration needs at least one model from the models table")
        designs = selected_designs if args.designs else ["owner", "pipeline"]
        sizes = selected_sizes or [4]
        cases = generate_cases(CALIBRATION_SEED, 6)
        calibration_cache = RequestCache()
        start_tracing()
        print(models_table(models))
        rows = run_all(cases, models, designs, output=DATA / ("calibration_results.csv" if chosen == "first" else "calibration_results_last_object.csv"),
                       cache=calibration_cache, team_sizes=sizes, cases_path=DATA / "calibration_cases.jsonl", parser=chosen)
        for model in models:
            owner = [r["status"] == "correct" for r in rows if r["design"] == "owner" and r["model"] == model["version"]]
            if not owner:
                print(f"{model['name']}: no owner results to calibrate (see messages above).")
                continue
            accuracy = sum(owner) / len(owner)
            print(f"{model['name']}: calibration owner accuracy {accuracy:.1%} ({sum(owner)}/{len(owner)}); target 50-90%; DIFFICULTY={DIFFICULTY}. "
                  + ("Within target." if .5 <= accuracy <= .9 else "Outside target; review difficulty before scored work."))
        return 0
    if args.smoke:
        start_tracing()
        cache = RequestCache()
        case = make_case("capital", CALIBRATION_SEED)
        for model in MODELS:
            print(model["name"])
            try:
                overhead = overhead_probe(model, cache)
                result = run_case(case, "owner", 1, model, cache)
            except ModelBlocked:
                continue  # one-line message already printed; the other models still run
            except Waiting:
                print(f"{model['name']}: route is subagent; no cached reply (use --run --export-pending --out FILE).")
                continue
            for call in result["calls"]:
                reply = call["reply"]
                raw_in = reply["input_tokens"]
                task_in = max(0, raw_in - (overhead or 0)) if raw_in else 0
                print(call["reply"]["text"][:400])
                print(f"Parse: {call['parse_status']}; raw input tokens: {raw_in}; overhead: {overhead}; "
                      f"task input tokens: {task_in}; output tokens: {reply['output_tokens']}")
        print(f"Smoke fresh calls: {cache.fresh_calls}. Failed calls not cached: {cache.failed_calls}.")
        return 0
    parser.print_help()
    print("\nModel configuration:\n", models_table())
    return 0

# %%
if __name__ == "__main__" and "__file__" in globals():
    raise SystemExit(main())
