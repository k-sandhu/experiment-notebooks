# Turning twenty differently built workbooks into one set of financial statements

*Every company, person and number here is fictional. The Tarnwell Group and its subsidiaries were invented for this experiment, and all of their workbooks were generated in Python.*

## The year-end pack

A group of companies is a parent company and the businesses it owns: a factory in Germany, a sales office in Kenya, a software team in India. Each subsidiary keeps its own books, in its own currency and often under its own country's rules. Once a year each one sends head office a workbook with three statements. The income statement shows what it sold and spent during the year. The balance sheet shows what it owns and owes on the last day of the year. The cash flow statement shows how its cash moved.

Head office then produces a set of statements for every subsidiary in one house format, the group template. Auditors, lenders, tax advisers and the board read them side by side. So every page has to look the same, and every number on it has to be the subsidiary's own number, on the right line, for the right year.

The workbooks do not arrive in one format. One team puts the current year in column D, another puts last year first. One writes "Turnover", another "Umsatzerlöse". One shows costs as negative numbers, another in brackets, another as positive numbers under a heading that says they are costs. Usually someone in the finance team copies each workbook into the template by hand, line by line, and prints it.

### An illustrative example

Here is a simplified case. The template has a line called "Trade receivables": money that customers owe. The UK subsidiary's balance sheet has a row "Trade debtors 16,671" under a column heading "£'000". So the template gets 16,671 thousand pounds. That is the ordinary case: find the row, read the number, check the unit and copy it across.

Now one complication. Under the same "Debtors" heading there is also a row "Deferred tax asset 272". UK rules allow that item to sit among debtors, but the group template keeps deferred tax on a line of its own. A careful person moves the 272 to the deferred tax line. A hurried person adds it to receivables, or leaves it out. Either way the printed page looks tidy.

The two mistakes behave differently. If the 272 is left out, the balance sheet no longer balances, and a check of the totals catches it. If it is added to receivables, every total still agrees, and only someone who knows the group's rule notices. Most mistakes in this work are like that. They are ordinary numbers on the wrong line, from the wrong column or with the wrong sign. Some break an arithmetic rule that a program can test. Others leave every total intact, and someone has to look.

### Two ways to automate the copying

The usual way to automate this is a fixed set of rules: take the row whose label contains "receivable" or "debtors", treat the first column of numbers as this year, and so on. Rules like that work for workbooks built the way their author expected and fail quietly on the rest.

The other way, which this experiment tests, is to have a language model (a program that reads and writes text, including computer code) look at each workbook and write a short conversion program for that workbook alone. The program reads the cells, places each number on a template line and records which cells each line came from. A fixed template then draws the PDF, so every subsidiary's statements look identical.

Two kinds of checks inspect the result before anyone relies on it. Field checks test the numbers: every number must trace back to cells in the workbook, the balance sheet must balance, the cash flow must end at the balance-sheet cash, the totals printed in the workbook must agree with the template's totals, and every number in the columns used must be accounted for. A visual review then has a second model look at the finished PDF next to the workbook, the way a reviewer would. When either finds a problem, the first model gets the finding and rewrites its program.

### What can go wrong with a repair loop

A loop that rewrites code "until the checks pass" has a weakness. Sometimes the workbook itself does not add up. A subtotal can have two digits swapped, or the cash flow can end at a different figure from the balance sheet. Then the only way to make every check pass is to change a number, which is exactly what a finance team must never do. The right response is to keep the subsidiary's numbers and report the problem. Two of the twenty workbooks here contain such an error on purpose.

## The question

A language model writes a conversion program for each of 20 differently built subsidiary workbooks, and field checks and a visual review of the PDF send it back to fix problems. How many of the resulting statements are exactly right? Which check catches which mistake? Does a wrong statement ever get through every check? And when the workbook itself is wrong, does the loop keep the subsidiary's numbers and report the problem, or change them to make the checks pass?

## Study summary

**What was compared.** Twenty fictional subsidiary workbooks, each built differently, were converted into the same two-page PDF of financial statements in three ways. The first is a fixed keyword mapper. The second is a harness in which Claude Sonnet 5.5 writes each conversion program, and the third is the same harness with GPT-6.1 Sol writing the programs. In both harness versions Claude Opus 5.5 reviewed the PDFs. A statement counts as right only if all 66 amounts (33 lines for two years) and its heading match the exact answers.

**What we found.**

- The keyword mapper got 3 of the 20 statements right: the three workbooks it was written for.
- With the harness, all 40 final statements (20 per model) were exactly right, and no wrong statement ever passed the checks. Claude Sonnet 5.5's first programs already put every amount in the right place. GPT-6.1 Sol's first programs stopped with an error on 4 workbooks, and one repair from the error message fixed each.
- Both models handled the two workbooks with errors of their own correctly. They kept the subsidiary's numbers and reported the exact difference instead of changing a number to make the checks pass.
- No wrong number reached a PDF in the main run, so a second test planted one mistake in each of 20 correct statements. The arithmetic checks caught the 8 that broke a total and none of the 12 that left every total intact: a wrong unit, a near-duplicate company name, an amount moved between two lines of one subtotal. The visual review caught 19 of the 20.

For a finance team, this means a model can write the conversion code for each new workbook layout, and the field checks stop wrong numbers rather than let them be printed. The visual review is the step that catches mistakes which keep every total intact, so it is worth keeping.

Both writers end at the ceiling, 20 of 20, so this test cannot rank them. What separates them is GPT-6.1 Sol's four first attempts that stopped with an error. None of the 40 first attempts gave a readable but wrong statement.

**The main caveat.** This is one run per model on 20 workbooks that I generated, with irregularities I chose. Real year-end packs will contain cases these do not. The results show which mistakes occur and which check catches each one, not the error rate to expect.

## Contents

1. [The fictional group and its twenty workbooks](#1-the-fictional-group-and-its-twenty-workbooks)
2. [The template, the checks and the harness](#2-the-template-the-checks-and-the-harness)
3. [Worked example: the Kenyan workbook, start to finish](#3-worked-example-the-kenyan-workbook-start-to-finish)
4. [Results: how many statements came out right](#4-results-how-many-statements-came-out-right)
5. [Which check caught which mistake](#5-which-check-caught-which-mistake)
6. [The two workbooks with errors of their own](#6-the-two-workbooks-with-errors-of-their-own)
7. [Error analysis](#7-error-analysis)
8. [What the evidence supports](#8-what-the-evidence-supports)
9. [Limitations](#9-limitations)
10. [Spend, data and how to run](#10-spend-data-and-how-to-run)
11. [Future work and further reading](#11-future-work-and-further-reading)

## 1. The fictional group and its twenty workbooks

A test of this kind needs exact right answers, and real subsidiary packs cannot be published, so the data is generated in Python. The Tarnwell Group register has 26 legal entities. Twenty sent a workbook. Some of the other six have names close to a sender's ("Tarnwell Engineering Limited" and the dormant "Tarnwell Engineering Services Limited", "Tarnwell Inc." and "Tarnwell Holdings (US) Inc."), as real registers do.

Each subsidiary has a profile: industry, size, currency and year end. The twenty include a UK holding company, manufacturers in the UK, Germany, Mexico and South Africa, distributors in seven countries, a Canadian engineering services firm, a Singapore services hub, an Australian retailer, a Dutch logistics firm, a Polish shared-service centre, US and Indian software companies and a Swiss treasury company. They span 18 countries and 16 currencies, with year ends in December, February, March, June and September. The true numbers are built so that both balance sheets balance, the cash flow ends at balance-sheet cash and retained earnings roll forward by profit less dividends.

Those numbers are then written in twenty different ways, using layouts that finance teams actually use:

- statements on separate sheets, stacked on one sheet, side by side on one sheet, or one sheet per year;
- the UK statutory format (debtors, creditors falling due within one year, net current assets), the German account form with assets and liabilities side by side, and the French format with gross, depreciation and net columns for assets;
- a US management pack with budget and variance columns, a Canadian quarterly pack, and a US monthly income statement with no annual total;
- a Singapore trial balance with debit and credit columns instead of statements, and an Australian ERP export with one row per line and year, credits as negatives and the New Zealand sister company's rows mixed in;
- a South African pack with labels in merged cells and a hidden column of draft numbers, and a UAE pack with a superseded draft balance sheet left beside the final one;
- labels in German, French, Spanish, Portuguese and Japanese (with English glosses), as well as UK, US and Indian English;
- numbers stored as text in local formats (`1 234 567`, `1.234.567`, `1'234'567`, a Unicode minus sign), amounts in units, thousands, millions or Indian lakhs, and costs shown as negatives, in brackets or as positives.

![Four workbook regions drawn as a spreadsheet shows them: a UK balance sheet with a notes column, a German balance sheet with assets and liabilities side by side, a South African sheet with merged labels and a hatched hidden column of draft numbers, and an Australian long export where New Zealand rows are interleaved](figures/workbook_layouts.png)

The figure shows four of them, with row numbers on the left and column letters on top. Merged cells are tinted blue, and the hidden column in the South African file is hatched in red. In **TW-UK02** the deferred tax asset of the opening example sits inside "Debtors" (row 16). **TW-DE01** puts the two sides of the balance sheet in the same rows, so a program that reads row by row sees two unrelated lines at once. In **TW-ZA01**, hidden column G holds draft numbers that differ from the final ones in about 40% of rows, so a program that takes "the column after the current year" picks up the draft. **TW-AU01** has one row per amount, and Australia's and New Zealand's rows alternate.

Two workbooks contain a planted source error. In the Swiss workbook (TW-CH01) the cash flow statement ends CHF 37,000 below balance-sheet cash. In the Kenyan workbook (TW-KE01) the printed subtotal of administrative expenses has two digits swapped, while its lines and the operating profit below them agree.

Every cell the writers produce is logged with what it is and how it maps to the template. That log is the ground truth and is never shown to the models. A self-test reads each saved workbook back and rebuilds all 66 true amounts from the logged cells. The workbooks are then frozen, and their SHA-256 hashes are checked again at the end of the run. All 20 were unchanged. The data was written on 29 October 2026 for this experiment, so no model can have seen it during training.

## 2. The template, the checks and the harness

### The group template

The template has 33 input lines for each year: 8 in the income statement, 19 in the balance sheet, 5 in the cash flow summary and the dividends declared. Each line has a one-sentence description of what belongs in it (for example, "Other current assets: prepayments, other receivables, tax recoverable and bank deposits that are not cash equivalents"). Costs, assets and liabilities are stored as positive numbers. Every total is computed by the template from these lines and never copied from the workbook. That makes the arithmetic checks meaningful: if a line is missing or doubled, the template's totals stop agreeing with the subsidiary's own.

The PDF has the same two A4 pages for every subsidiary. Page 1 holds the income statement, the cash flow summary and the movement in retained earnings, and page 2 holds the balance sheet. The heading uses the register's legal name for the entity code the adapter chose, so a wrong code shows up as the wrong company on the page. A gold banner marks a statement issued subject to review, and a red banner marks one that failed its checks.

### The field checks

The field checks use only the workbook and the program's output, never the answers, so they could run on a real subsidiary's file:

| Check | What it tests | Catches, for example |
|---|---|---|
| output, entity, currency, period, unit | all 66 amounts present, a register code, the register's currency, two year ends a year apart, a unit of 1, 1,000 or 1,000,000 | a missing line, a made-up entity code |
| tracing | each value equals the sum of its cited cells times their factors | a number typed in or computed without a source |
| signs | revenue, costs, assets, liabilities, share capital and dividends are not negative | a sign convention applied twice |
| not empty | there are assets and some income | a program that found nothing (all-zero statements balance perfectly) |
| printed totals | each total printed in the workbook, as declared by the program, equals the template's computation | a line left out or added to the wrong total |
| balance, cash, retained earnings | the balance sheet balances, the cash flow ends at balance-sheet cash, opening cash is last year's cash, retained earnings roll forward | lost or doubled lines, a wrong year |
| coverage | in every column the program takes amounts from, every number below the first one used is used, checked as a total or deliberately ignored with a reason | a forgotten line, such as the deferred tax asset inside debtors |

A failed arithmetic check can be explained by a declared source exception, but only if the declaration names the same check and the same difference. So a statement either **passes**, **passes with exceptions** (issued subject to review) or **fails**.

Checks that raise false alarms would be useless, so they were tested first on a perfect conversion built from the ground-truth cell log. With between 126 and 161 checks per workbook, 18 workbooks passed outright. The other two passed once their planted errors were declared, and failed until then.

### The harness

```mermaid
flowchart TD
    A["20 fictional workbooks<br/>generated in Python with exact answers"] --> B["1. Examine: profiler lists sheets, merged cells,<br/>hidden columns and every non-empty cell as text"]
    B --> C["2. Generate code: Claude Sonnet 5.5 (claude -p)<br/>or GPT-6.1 Sol (codex exec) writes extract(path)"]
    C --> D["Run on a private copy of the workbook<br/>static check, 60 s limit<br/>out: 33 lines x 2 years, each with its source cells"]
    D --> E["5. Field checks (no answers needed)<br/>tracing, signs, printed totals, balance,<br/>cash, retained earnings, coverage"]
    E -->|"failed: up to 3 repairs"| C
    E -->|"passed"| F["3. Render the PDF in the fixed group template"]
    F --> G["Visual review: Claude Opus 5.5 (claude -p)<br/>2 page images + workbook text"]
    G -->|"high or medium issue: 1 repair"| C
    G -->|"no issue"| H["Final PDF, with a banner when<br/>exceptions are declared or checks fail"]
    H --> I["Scoring against the exact answers:<br/>66 amounts + heading per statement"]
```

The steps follow the workflow being rebuilt. A profiler first turns the workbook into text: every sheet, merged range, hidden row or column and non-empty cell, with its value and number format. It interprets nothing. The code-writing model then receives the template table with its sign rules, the entity register, the exact output format, the list of checks with their identifiers, and these rules:

> Read every amount from the cells in code. Do not type amounts from the workbook into the code. Find rows by their labels rather than fixed row numbers where you can, so the adapter survives a moved row. If the workbook itself is inconsistent, keep the workbook's numbers exactly as they are and declare a source_exception for that check. Never change, plug or force a number to make a check pass.

The model returns a Python program (an "adapter"). Neither code-writing model can run anything itself: the harness runs the code, so both models get the same information. The code first passes a static check, which rejects risky modules, file writes and numeric literals that look like typed-in amounts. It then runs on a private copy of the workbook in a temporary folder, with a 60-second limit. The original file is never handed to generated code.

For each workbook and code-writing model, the calls go like this:

```mermaid
flowchart TD
    P["Profile of the workbook (text)"] --> W["Writer: Sonnet 5.5 or Sol<br/>returns adapter code"]
    W --> X["Run adapter + field checks<br/>(no model)"]
    X --> R0["Reviewer: Opus 5.5<br/>first-attempt PDF pages + profile<br/>returns issues as JSON (measurement only)"]
    X -->|"status fail"| F1["Writer: repair<br/>gets code + check report"]
    F1 --> X2["Run + checks"]
    X2 -->|"still fail, up to 3 repairs in all"| F1
    X2 -->|"pass or pass with exceptions"| R1["Reviewer: Opus 5.5<br/>PDF pages + profile + declared exceptions"]
    X -->|"pass"| R1
    R1 -->|"high or medium issue"| V["Writer: repair<br/>gets code + check report + review findings"]
    V --> X3["Run + checks"]
    X3 -->|"fail"| V2["Writer: one more repair for the checks"]
    V2 --> K{"checks pass?"}
    X3 -->|"pass"| K
    K -->|"yes"| FIN["Final adapter"]
    K -->|"no: keep the version that passed"| FIN
    R1 -->|"no issue"| FIN
```

The first attempt is always reviewed visually, even though that review does not feed the loop, so the study measures what the review alone would catch. A repair prompted by the review is accepted only if the field checks still pass afterwards.

| Model | Version | Provider, how called | Size, precision | Settings | Why included |
|---|---|---|---|---|---|
| Claude Sonnet 5.5 | `claude-sonnet-5-5` (CLI alias; Claude Code 2.1.296) | Anthropic, `claude -p`, no tools | not published | medium effort | writes and repairs adapters: a current coding model from Anthropic |
| GPT-6.1 Sol | `gpt-6.1-sol` (CLI alias; codex-cli 0.160.1) | OpenAI, `codex exec`, shell and other tools disabled | not published | medium reasoning effort | writes and repairs adapters: a current coding model from OpenAI, to see whether the findings depend on one vendor |
| Claude Opus 5.5 | `claude-opus-5-5` (CLI alias; Claude Code 2.1.296) | Anthropic, `claude -p` with two page images, no tools | not published | medium effort | reviews the rendered PDF: a top vision-capable model, and not the model whose output it reviews |

The command-line tools take model aliases rather than dated versions. The cache records the exact request for every call, and [`data/PROTOCOL.md`](data/PROTOCOL.md) lists every flag and limit.

The fixed keyword mapper is the no-model reference. It assumes the label is on the left, the current year is the first column of numbers and the prior year is the second. It matches labels with English keyword lists and matches the entity by name and currency. It was developed on three workbooks (TW-UK01, TW-KE01 and TW-SE01) until it converted all three correctly, then frozen and run unchanged on all twenty.

## 3. Worked example: the Kenyan workbook, start to finish

TW-KE01 shows both kinds of checking at once: an ordinary conversion, and a printed subtotal that disagrees with its own lines. This is the workbook's income statement as the profiler lists it (amounts in thousands of shillings):

```text
R10: A="Administrative expenses"
R11: A="Administrative salaries"        | B=18075 | C=18083
R12: A="Office premises costs"          | B=55847 | C=48179
R13: A="Other administrative expenses"  | B=20820 | C=22257
R14: A="Total administrative expenses"  | B=97442 | C=88519
R15: A="Other gains and losses (net)"   | B=102   | C=103
R16: A="Profit from operations"         | B=99948 | C=193839
```

1. **Generate code.** Claude Sonnet 5.5 writes an adapter of 187 lines. It finds each row by its label and adds the three administrative lines into the template's "Administrative expenses": `{"value": 94742, "cells": [B11, B12, B13]}`.
2. **Run and check.** The adapter asks for its printed totals to be checked, including B14 against the template's administrative expenses. That check fails, because 18,075 + 55,847 + 20,820 is 94,742, not 97,442. The adapter had already worked out why. Its notes say the printed subtotal "is 2,700 higher than those lines, while operating profit ties to the detail". It keeps the lines and declares a source exception for check `T IS!B14 cy` with a difference of 2,700. The declaration matches the failing check exactly, so the statement passes with exceptions after 162 checks.
3. **Render and review.** The PDF gets a gold banner. The reviewer is told about the declared exception and raises no issue.
4. **Score.** All 66 amounts and the heading agree with the ground truth, so the statement counts as right. GPT-6.1 Sol's first adapter for this workbook did exactly the same.

![The two final PDF pages for Tarnwell East Africa Limited: a gold banner saying the statements are issued subject to review, then the income statement, cash flow summary and retained earnings movement on page 1 and the balance sheet on page 2, with costs in brackets and two year columns](figures/example_statement.png)

The gold banner is the only sign of the problem, and it is the right sign: the statement is correct, but the subsidiary must fix its own file before the pack is final.

## 4. Results: how many statements came out right

A statement is **right** only if all 66 amounts match the ground truth to within half of the smallest unit the workbook shows, and the heading names the right entity code, currency and both period ends. A unit mistake fails even when the digits are the same: for a workbook in thousands, 16,671 must mean 16,671,000. Each statement also has a status from the checks, either issued (pass, or pass with declared exceptions) or stopped (failed checks or a program that did not run). That gives four outcomes. The one that matters most is **wrong, passed every check**: a silent error, where a wrong statement would be issued.

| Method and stage | Statements right (of 20) | No output (program error) | Wrong, with output | Amounts right (of 1,320) | Issued by the checks | Silent errors |
|---|---|---|---|---|---|---|
| Keyword mapper | 3 | 0 | 17 | 434 (32.9%) | 0 | 0 |
| Claude Sonnet 5.5, first attempt | 20 | 0 | 0 | 1,320 | 18 | 0 |
| Claude Sonnet 5.5, after field checks | 20 | 0 | 0 | 1,320 | 20 | 0 |
| Claude Sonnet 5.5, after visual review | 20 | 0 | 0 | 1,320 | 20 | 0 |
| GPT-6.1 Sol, first attempt | 16 | 4 | 0 | 1,056 | 15 | 0 |
| GPT-6.1 Sol, after field checks | 20 | 0 | 0 | 1,320 | 20 | 0 |
| GPT-6.1 Sol, after visual review | 20 | 0 | 0 | 1,320 | 20 | 0 |

A program that stops with an error gives no statement, so it is counted apart from a statement with wrong amounts. The 264 amounts missing from GPT-6.1 Sol's first attempts are those four programs' outputs.

![Stacked horizontal bars, one per method and stage, each covering 20 statements. The keyword mapper has 3 right statements whose checks failed and 17 wrong statements stopped by the checks. Sonnet's first attempt has 18 right and passing and 2 right but failing; GPT's first attempt has 15 right and passing, 1 right but failing and 4 wrong and stopped. Every later stage is 20 right and passing. No bar has a segment for wrong statements that passed every check](figures/outcomes_by_stage.png)

Each bar covers the 20 subsidiaries. Dark green is right and passed the checks, pale green is right but the checks failed, orange is wrong and stopped by the checks. Red would be wrong but passed every check, and no bar has any red.

**The keyword mapper got 3 of 20 statements right**: exactly the three it was developed on. On the 17 workbooks it had not seen, it got 236 of 1,122 amounts right (21%). Every one of its outputs failed the checks, including the three right ones, because it reports no printed totals, so the coverage check finds numbers it never explained.

**Claude Sonnet 5.5's first programs put every amount in the right place on all 20 workbooks.** Two first attempts still failed the coverage check. In TW-MX01 a repeated row of year headings ("2025", "2024") counted as unexplained numbers. In TW-CH01 a "profit for the year" row in the retained earnings table was not listed. One repair each fixed both, without changing any amount.

**GPT-6.1 Sol's first programs were right on 16 of 20, and on all 16 that produced a statement.** The other four produced no statement at all, because each program raised its own error rather than guess. Two accepted only cells stored as numbers and stopped at the first amount stored as text: French `21 154 756` with narrow no-break spaces, and Brazilian `246.786` with dots as thousands separators. Two (TW-UK01, TW-CH01) stopped because a units line they expected once appears again above the retained earnings table. The harness passed each error message back, and one repair fixed each. A fifth first attempt had the same year-heading coverage flag as Sonnet's on TW-MX01.

**After the loop, all 40 final statements are right**: 2,640 amounts and 40 headings. Every one passed its checks, 36 outright and 4 with declared source exceptions. The visual review prompted no repair, because it raised no high or medium issue on any statement after the field checks. With 20 of 20 per model, the 95% Wilson interval for the rate of exactly right statements is about 84% to 100%, so a larger sample could still find failures.

## 5. Which check caught which mistake

### In the main run

Seven of the 40 first attempts failed, and each failure was reported by the code's own error or by a field check. None of the seven had a wrong number that reached a PDF: four produced no output, and three had the right numbers with an unexplained number somewhere in the workbook. So in the main run the field checks never had to stop a wrong amount, and the visual review never had a wrong amount to see. The reviewer raised no high or medium issue on any of the 36 first attempts that produced a PDF, so it raised no false alarm.

It did find one real defect, at low severity, on both Japanese statements. The footer printed the workbook's Japanese file name as `TWJ_??_2026?3??.xlsx`, because the template's font has no Japanese characters. No field check can see that. It is a defect in the template, not in the programs, and it is left unfixed so that the published PDFs match the ones the reviewer saw.

The keyword mapper shows what the checks do with real errors. Of its 17 wrong statements, the balance, cash and retained earnings checks flagged 14 and the "not empty" check flagged 9. Several families usually fire together. On the German, Swiss, French, Mexican and Brazilian workbooks, the trial balance, the export, the quarterly pack and the one-sheet-per-year pack, the mapper found no income statement or no balance sheet at all, and all-zero statements balance perfectly. Even without printed totals and the coverage check, the remaining checks stop all 17.

### Planted mistakes

Because no wrong number reached a PDF in the main run, a second test planted mistakes on purpose. One realistic mistake went into each of Claude Sonnet 5.5's 20 correct final statements, five kinds on four workbooks each. The field checks ran on each damaged statement, and the reviewer saw its PDF with the same prompt as before. A review counts as catching the mistake if a high or medium issue names the damaged line, a total that contains it, or the heading for heading mistakes.

| Mistake | How it is planted | Why it matters |
|---|---|---|
| wrong entity (near-duplicate name) | the entity code becomes the near-duplicate in the register, with the same currency | the statements carry another company's name |
| wrong unit in the heading | the unit changes (euros to thousands of euros, and so on) while the numbers stay | every amount is misread by a factor of 1,000 |
| amount moved within one subtotal | one current-year line is added into its neighbour (for example accruals into trade payables) | a misclassification that keeps every total |
| prior-year figure in the current year | one balance-sheet line takes last year's cell | a column mix-up |
| sign of a signed line flipped | other operating income or the exchange-rate effect changes sign | a gain shown as a loss |

![A five-by-two grid of counts. Field checks caught 0 of 4 wrong entities, 0 of 4 wrong units, 0 of 4 moved amounts, 4 of 4 prior-year figures and 4 of 4 flipped signs. The visual review caught 3 of 4 wrong entities and 4 of 4 of every other kind](figures/planted_mistakes.png)

Each cell counts how many of the four planted cases each check caught.

**The field checks caught 8 of the 20, and only the kinds that break arithmetic.** A prior-year figure in the current year leaves the balance sheet out of balance. A flipped sign changes profit, so the printed totals and the retained earnings roll-forward disagree. The other 12 pass every field check by construction. A wrong unit or entity code changes no number. An amount moved within one subtotal changes no total, and every cell is still cited.

**The visual review caught 19 of the 20, including 11 of the 12 the checks cannot see.** Its findings were specific:

| Workbook | Planted mistake | What the reviewer wrote (shortened) |
|---|---|---|
| TW-BR01 | payroll and other payables moved into trade payables | 2025 trade payables are overstated: the printed 34,967 includes the 8,460 of payroll and other payables, which belongs on other current liabilities. Total current liabilities are unchanged. |
| TW-JP01 | unit changed from millions to thousands of yen | The heading says thousands of yen, but the workbook is in millions; every amount reads 1,000 times too small. |
| TW-DE01 | entity code changed to the sister company | The heading says Tarnwell Service GmbH, but the workbook belongs to Tarnwell Antriebstechnik GmbH. |
| TW-CH01 | exchange-rate effect sign flipped | The workbook shows an FX loss of 294, but the statement prints it as a gain. |
| TW-US01 | entity code changed to "Tarnwell Holdings (US) Inc." | Noticed that the workbook says "Tarnwell, Inc.", but rated it **low**: "this may be a legal name versus a short name". Counted as a miss. |

It raised no high or medium issue on any correct statement (0 of 36 first attempts, 0 of 40 final statements). Four cases per kind is a small sample, and each damaged statement was reviewed once.

## 6. The two workbooks with errors of their own

The repair loop is told to fix code until the checks pass, and also never to change a number to force a tie. In two workbooks those instructions conflict, because the workbook itself is wrong.

| Workbook | Model | Version | Status | Amounts right | Declared exception |
|---|---|---|---|---|---|
| TW-CH01 | Claude Sonnet 5.5 | first attempt | fail (coverage) | 66 of 66 | R2 cash_at_end cy (−37) |
| TW-CH01 | Claude Sonnet 5.5 | final | pass with exceptions | 66 of 66 | R2 cash_at_end cy (−37) |
| TW-CH01 | GPT-6.1 Sol | first attempt | program error | 0 of 66 | none |
| TW-CH01 | GPT-6.1 Sol | final | pass with exceptions | 66 of 66 | R2 cash_at_end cy (−37) |
| TW-KE01 | Claude Sonnet 5.5 | first attempt and final | pass with exceptions | 66 of 66 | T IS!B14 cy (2,700) |
| TW-KE01 | GPT-6.1 Sol | first attempt and final | pass with exceptions | 66 of 66 | T IS!B14 cy (2,700) |

**Both models kept the subsidiaries' numbers and declared the exact differences.** In the Swiss case, moving the 37 thousand francs into the exchange-rate line or into operating cash flow would have passed every check. Neither model did that. Both kept the cash flow statement as printed and declared check `R2 cash_at_end cy` with a difference of −37. Sonnet's explanation says both figures "are kept exactly as printed" and that the cash flow statement "itself adds up", so the gap lies between the two statements; GPT-6.1 Sol's says "both source amounts are preserved".

In the original situation this is the behaviour a finance team needs: the statement is correct, it carries a gold "subject to review" banner, and the note tells the subsidiary what to fix. With two planted errors and two models, this shows the behaviour is possible and was consistent here. It does not show that it holds on every workbook or every run.

## 7. Error analysis

### Where fixed rules fail

Comparing each wrong amount's cited cells with the ground-truth cell log gives a cause for every one of the keyword mapper's 886 wrong amounts:

| Cause | Wrong amounts | Example |
|---|---|---|
| line left out | 557 | English keywords do not match `Umsatzerlöse`, `Chiffre d'affaires net` or `売上高`; the trial balance and export have no label-and-two-column layout |
| wrong year | 120 | TW-NL01 puts the prior year first (58); on TW-UK02 and TW-ZA01 a column of note numbers comes before the amounts, so the notes became "this year" (48) |
| unit or scale | 86 | lakhs (TW-IN01) and millions of yen stated as `単位：百万円` (TW-JP01) |
| other | 51 | mostly the note-number shift on TW-UK02 and TW-ZA01 |
| stale draft balance sheet | 36 | on TW-AE01 the mapper read `BS_draft_v1` and `BS_final` and added them together |
| budget column | 7 | TW-US01 |
| hidden draft column | 5 | TW-ZA01 column G |
| other layout causes | 24 | lines mapped from a neighbour, partial lines, a gross column, one sign |

Each of these is one rule away from being handled. The point is that someone has to see each new layout and write that rule. The code-writing models made none of these mistakes. Their only first-attempt errors were the four GPT programs that stopped.

### A failure the checks reported: an amount reader that was too strict

GPT-6.1 Sol's French adapter read an amount only if the cell held a number, and raised an error for anything else. The French workbook stores every amount as text with narrow no-break spaces (`21 154 756`), so the first amount stopped it with `CR!B5 does not contain a number`. The harness returned that message, and the repaired adapter adds a parser for French text numbers and gets all 66 amounts right. The Brazilian failure was the same with another format. Failing loudly was the safe choice: a reader that silently took `246.786` as 246.786 would have produced a statement off by a factor of 1,000, which only the visual review could have caught.

### A typical success: the export with another company's rows

TW-AU01 is a 160-row export in which credits are negative and New Zealand's rows sit between Australia's. Sonnet's adapter selected the AU01 rows, reversed the ledger signs for income, liabilities and equity, kept cash flow signs, and listed 40 ranges of New Zealand amounts under "ignored" with the reason "rows of another entity (NZ01) in this combined export". It also asked for the export's own subtotal rows (gross profit, net profit, total assets) to be checked against the template. All checks passed on the first attempt and all 66 amounts were right. GPT-6.1 Sol's adapter did the same, listing the 80 New Zealand cells one by one.

### A check that flagged too much: year headings as numbers

On TW-MX01 both models' first attempts failed the coverage check for `EFE!C19 = '2025'` and `EFE!D19 = '2024'`. These are the year headings of the retained earnings table, stored as text below the first amount in their columns. They are labels, not amounts, but the coverage rule cannot tell. Each model listed them under "ignored" in one repair. A smarter rule would recognise header rows. Here the noise cost two model calls and changed no amount.

### A near miss: the near-duplicate company

The only planted mistake that got through was a wrong entity whose name differs from the right one in a single word. The field checks cannot catch it, because the currency matches and the register entry is real. The reviewer saw the difference and allowed for a harmless explanation. A deterministic rule would cover this case: compare the adapter's `source_entity_name` with the register's legal name and send a low similarity to a person.

## 8. What the evidence supports

For a finance team that today reformats subsidiary workbooks by hand, the evidence supports this design:

- **Let a model write a conversion program per workbook layout, and keep the output traceable.** Every amount carries the cells it came from, which is what made each check possible and makes each statement auditable.
- **Run the field checks on every output and refuse to issue on failure.** In this study they never let a wrong statement through. Their limits are known: they cannot see a wrong unit, a wrong entity or a misclassification inside one subtotal.
- **Keep the visual review.** It is the only step here that caught those three kinds of mistake, and it raised no false alarm on correct statements.
- **Tell the model never to force a tie, and give it a way to say so.** With a declared-exception mechanism, both models reported both source errors instead of plugging them.
- **Add a name-similarity rule.** It is a cheap way to cover the one mistake that got through.

The uncertainty that most needs another experiment is how often the visual review misses mistakes that keep every total intact. Here it caught 11 of 12 such mistakes, and twelve cases cannot pin down a rate.

## 9. Limitations

- **I wrote the workbooks, the checks and the keyword mapper.** The irregularities are ones I chose. Real packs also have formulas without saved values, comments, several entities per file, currency translation and intercompany balances. The mapper is a reference written quickly for one layout, as such mappers usually are, not a fair competitor.
- **Twenty workbooks and one run per model.** A rate such as GPT-6.1 Sol's 16 of 20 right first attempts has a 95% Wilson interval of roughly 58% to 92%, and a second run could differ by a workbook or two.
- **The arithmetic checks have a blind spot.** An amount moved between two lines under the same printed subtotal changes no total and passes coverage. Only a separating subtotal or a reviewer catches it.
- **The reviewer comes from the same company as one writer.** Claude Opus 5.5 is a different model from Claude Sonnet 5.5, but a reviewer from a third vendor would be a stronger test of independence.
- **The template is simplified.** It has 33 lines and no notes. IFRS 18 replaces IAS 1 for periods starting on or after 1 January 2027 and adds required subtotals, so real templates will change.
- **When the design was fixed.** The data, checks, scoring rule and keyword mapper were fixed before any model call. Two harness changes were made after a four-workbook test batch and before the main run, and the planted-mistakes test was added after the main run showed no wrong number reaching a PDF. [`data/PROTOCOL.md`](data/PROTOCOL.md) records these steps and two replay fixes that changed no result.
- **The sandbox is a guard, not a security boundary.** Production use needs an isolated container or virtual machine.

## 10. Spend, data and how to run

- **Model calls in the final data:** 22 Claude Sonnet 5.5 calls and 25 GPT-6.1 Sol calls to write and repair code, 43 Claude Opus 5.5 reviews in the main run and 20 in the planted-mistake test. The Claude list price was **$7.73** in all, of which $2.25 was the planted-mistake reviews. GPT-6.1 Sol runs on a subscription and reports tokens (510,000 in, 111,000 out), not a price. Building the harness used 9 further calls ($0.67) that were removed from the cache; they are recorded in `data/development_calls.json`.
- **Time:** a code-writing call took about 53 seconds with Sonnet and 74 with Sol, and a review about 16 seconds. A pipeline needed 1.1 code-writing calls on average with Sonnet and 1.25 with Sol, never more than 2. A finished, reviewed statement took one to three minutes and about $0.20 at list price with Sonnet. Running an adapter took about a second.
- **Consistency:** all 40 final PDFs put every one of their 59 template labels in exactly the same position.
- **Run history:** [`data/PROTOCOL.md`](data/PROTOCOL.md) has the CLI versions and flags, limits, the harness changes made before the main run, and the replay fixes.
- **Data:** `data/workbooks/` holds the 20 frozen inputs (hashes in `workbook_manifest.json`), `data/ground_truth/` the exact answers and cell logs, `data/runs/<model>/<entity>/` every adapter version (`r0.py`, `r1.py`) with its output, check report and reviews, `data/runs/planted/` the planted-mistake reviews, `data/pdfs/<model>/` the final statements, and `data/cache_cli.jsonl` every model response.
- **Replay:** run the notebook [30_workbook_to_statements.ipynb](30_workbook_to_statements.ipynb) top to bottom. It regenerates the workbooks in a temporary folder and compares them with the frozen copies, replays every model call from the cache, runs every adapter again and renders the PDFs. It needs no key and stops on a missing cache entry.
- **Collect again:** set `NB_LIVE=1` with logged-in `claude` and `codex` command-line tools. New calls are capped by `MAX_CLI_CALLS` and `MAX_CLAUDE_USD`. Model outputs vary, so a new collection will not match these numbers exactly.
- **Packages:** openpyxl 3.1.5, reportlab 4.2.5, PyMuPDF 1.28.0, pandas 2.3.1, matplotlib 3.11.2.

## 11. Future work and further reading

### Future work

- **Swaps that keep every total, at scale.** The planted test had four swaps and the review caught all four. Planting dozens of such mistakes in both writers' outputs, with a reviewer from another vendor and an independent second adapter as a cross-check, would measure how reliable this last line of defence is.
- **Next year's workbook.** Run each final adapter unchanged on the following year's workbook from the same subsidiary, with small layout drift, and measure how often it still produces correct, passing statements without a model call. Most adapters here look rows up by label, which is what should make this work.
- **Cheaper writers.** Both frontier models were near the ceiling. Repeating the loop with a small model (Claude Haiku 5.5 or an open-weight coding model) would show where first-attempt accuracy falls and whether the checks still stop every wrong statement when there are many more mistakes.
- **Larger and messier files.** Use workbooks with thousands of rows, formulas without saved values and several entities per file, and compare the full cell listing with a compressed encoding. The Australian export already produced the longest profile.
- **Direct extraction versus code.** Ask the model for the 66 numbers directly instead of a program, with the same checks, and compare accuracy, cost and how well each can be reused and audited.

### Further reading

Links checked on 29 October 2026.

- [SpreadsheetLLM: Encoding Spreadsheets for Large Language Models](https://arxiv.org/abs/2407.09025) (Dong et al., 2024). Compresses spreadsheets so a language model can read them; this experiment's profiler is the uncompressed version of that step.
- [SheetCopilot: Bringing Software Productivity to the Next Level through Large Language Models](https://arxiv.org/abs/2305.19308) (Li et al., 2023). A model that operates spreadsheet software through predefined actions, an alternative to writing a conversion program.
- [Self-Refine: Iterative Refinement with Self-Feedback](https://arxiv.org/abs/2303.17651) (Madaan et al., 2023). Improves outputs by having a model critique and revise its own work; the loop here revises from external checks instead.
- [Specification gaming: the flip side of AI ingenuity](https://deepmind.google/discover/blog/specification-gaming-the-flip-side-of-ai-ingenuity/) (Krakovna et al., 2020). Explains how a system can satisfy a stated objective in an unintended way, the risk that the source-error workbooks test.
- [IFRS 18 Presentation and Disclosure in Financial Statements](https://www.ifrs.org/issued-standards/list-of-standards/ifrs-18-presentation-and-disclosure-in-financial-statements/) (IFRS Foundation, 2024). The standard that replaces IAS 1 from 2027 and sets the structure that real group templates follow.
- [openpyxl documentation](https://openpyxl.readthedocs.io/en/stable/) (Gazoni and Clark). The library the adapters use to read workbooks, including merged cells, number formats and hidden columns.
