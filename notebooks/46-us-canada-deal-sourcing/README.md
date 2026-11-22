# Can AI find acquisition candidates in the U.S. and Canada?

An acquisition search begins with a description of the business a buyer wants to find. A buyer that already owns a laboratory might ask for a regional company that checks the accuracy of pressure gauges and temperature probes. The first job is to build a short list of distinct operating businesses and gather enough evidence to decide which ones deserve a closer look.

The analyst could start with an accreditation directory. A listing can lead to a document describing exactly what a laboratory can calibrate and where it does the work. The analyst then has to find the company behind the laboratory. A lab may have its own name and location while operating as a branch of a much larger company.

### An illustrative sourcing brief

Suppose an analyst finds a shop in Ohio whose website lists pressure and temperature calibration. The address is for a staffed lab and the shop sells its services to other manufacturers. The shop fits the service and location requirements. If its current ownership is also documented as independent, it can go forward for an initial review.

Now suppose the shop's old name still appears in search results, but a larger company bought the lab and operates it at the same address. Both pages can be correct about the services. The analyst needs something different for the ownership question, such as an acquisition announcement or a current company page identifying the lab as a branch. Keeping both names on the list would give the analyst two leads for one operation.

Some shops disclose little about who owns them. In those cases an analyst can carry the business forward as a lead with a question attached. That lets the sourcing team distinguish a company it should rule out from one it should check by asking for more information. The same logic applies to financials. An old contract value can indicate that the company has done work for a customer, while an income statement or dated transaction disclosure would answer a different question about revenue.

A directory gives an analyst a starting list with an explicit scope. Searching the web can turn up businesses outside that list and reveal ownership changes the directory was never designed to track. A model can do either job. It can search from an acquisition brief, or it can start from a directory list and look for evidence to prioritize each company. Once a candidate is known, the model can also prepare a short profile from public pages or from documents supplied by the analyst.

This study asks how often those approaches produce a candidate that passes the public-evidence screen, and which company facts the models can recover when researching the same companies.

## Study summary

On six real-world sourcing briefs and 24 shared company profiles, GPT-6.1 Sol and GPT-6 Luna found **7 distinct businesses outside the starting list that met our public-evidence screen**. That screen required positive evidence of the right service, a local operating site and independence. Each model flagged ownership as unresolved for every new lead that eventually passed. A reviewer had to finish that step.

The starting directory yielded 5 verified slots out of 60, and both models kept those five when they started from it. Open search returned 6 verified slots with Sol and 5 with Luna. On the shared company profiles the models matched 137 and 139 of 146 frozen fields from web search. With source packets, Sol matched 144 of 146. Luna matched 107 of 146 under the original parser and 143 of 146 when we removed the trailing tag that made six otherwise complete profiles unreadable. That puts both models near the maximum on the supplied evidence.

The comparison uses a small starting list in Michigan, Ohio, Ontario and Québec, and some public facts predate the models' cutoffs. We measured model working time. An analyst time comparison remains unmeasured.

## Contents

- [1. Sources and acquisition briefs](#1-sources-and-acquisition-briefs)
- [2. Discovery and company research](#2-discovery-and-company-research)
- [3. Shortlists and company profiles](#3-shortlists-and-company-profiles)
- [4. Worked examples and errors](#4-worked-examples-and-errors)
- [5. Limits of a public-data screen](#5-limits-of-a-public-data-screen)
- [6. Reproduction](#6-reproduction)
- [7. Future work and further reading](#7-future-work-and-further-reading)

```mermaid
flowchart LR
    briefs["3 briefs × 2 markets<br/>6 sourcing tasks"] --> dir["Public source list<br/>24 known businesses"]
    briefs --> web["Sol and Luna via codex exec<br/>12 searches from brief"]
    dir --> base["Filter and rank<br/>6 lists"]
    dir --> dirai["Sol and Luna via codex exec<br/>12 searches from list"]
    base --> review["Pool names and verify eligibility<br/>up to 300 ranked slots"]
    web --> review
    dirai --> review
    dir --> names["24 shared businesses<br/>12 per market"]
    names --> search["Sol and Luna via codex exec<br/>16 calls with web search"]
    names --> packet["Sol and Luna via codex exec<br/>16 calls with identical evidence"]
    search --> marks["96 profiles expected<br/>score against frozen facts"]
    packet --> marks
    review --> results["Shortlist and profile comparisons"]
    marks --> results
```

The Cincinnati lab formerly known as Alliance Calibration takes two routes through the study. When it appears in a sourcing list, the reviewer checks whether the operating lab can be acquired separately under the brief. When the models receive it by name in the company-research test, the task is to explain the services and identify the change in control. A profile can get that research right while leaving Alliance off an independent-company shortlist.

## 1. Sources and acquisition briefs

We used Michigan and Ohio for the U.S. briefs and Ontario and Québec for the Canadian briefs. Each geography got the same three service requirements. A calibration provider had to offer work to outside customers. For fire alarms, the test focused on companies that inspect or test commercial building systems and maintain or repair those same systems.

| Brief | What the analyst needs to verify | Easy mistake |
| --- | --- | --- |
| PT | The lab calibrates industrial instruments that measure pressure **and** temperature | A company sells pressure gauges and publishes a temperature-only calibration scope |
| DE | The lab calibrates dimensional instruments such as gauges **and** electrical instruments | An accredited facility calibrates only dimensional gauges |
| FA | The company inspects or tests **and** maintains or repairs commercial fire alarm systems | The company monitors alarms or inspects extinguishers |

These service pairs make a shortlist harder to verify than a keyword match. A customer who needs one supplier to calibrate both kinds of instruments still has to shop for a second vendor when the first one offers only half the work. We choose the conditions before seeing the responses. The same rule applies when a company offers several fire protection services and a site lists those services together without saying which systems the technicians inspect or maintain.

We read laboratory scopes and commercial service pages for service and location evidence. Certification directories help find labs or fire alarm providers in each geography. The publication date, access date, URL and brief factual paraphrase are saved with each research case. We used corporate records and acquisition disclosures where available. The Ohio Secretary of State explains that the state search supplies statutory-agent information and that its office does not maintain ownership lists. The Québec enterprise register offers establishment addresses and declared ultimate beneficiaries, and Corporations Canada publishes selected ownership-control information for federal business corporations. [Ohio business search guidance](https://www.ohiosos.gov/business/ohio-business-roadmap/frequently-asked-questions) · [Québec enterprise register](https://www.quebec.ca/entreprises-et-travailleurs-autonomes/obtenir-renseignements-entreprise/recherche-registre-entreprises/acceder-registre-entreprises) · [Corporations Canada disclosure](https://ised-isde.canada.ca/site/corporations-canada/en/how-find-information-about-individuals-significant-control)

An operating site identifies where work is performed. A statutory agent can give a business an address in a jurisdiction without operating a lab or service branch there. We used operating addresses and checked alternate names against source descriptions. For Québec, the web instructions allowed French and English terms such as *étalonnage*, *pression*, and *entretien de systèmes d’alarme incendie*. A company needed dated or current evidence of an in-region site for a verified discovery slot.

The 24 research cases span both sectors and include specialties with partial service evidence, acquired brands, and companies whose ownership is difficult to establish. These were selected for a pilot that exercises the screening rules. Their mix is not a random sample of companies in the four jurisdictions. The table in the notebook shows the operating city, sector, reference service labels and public ownership classification. [U.S. data](data/us_profiles.json) · [Canadian data](data/ca_profiles.json)

## 2. Discovery and company research

### What each approach can see

The directory baseline searches the same small public-source list used for the research test. It first filters the list to the right country and industry, then ranks by the number of required service facts in each entry. The two models that start with the directory receive the ranked names and service fields and can search for evidence to improve the ordering or leave a company out. The open-web models get only the brief and are free to find names outside the list. The baseline can fill at most the number of directory entries in its sector. This is a test against a bounded starting list. The number of firms in eligible accreditation directories is substantially larger. [A2LA directory](https://customer.a2la.org/?event=directory.index) · [ANAB directories](https://anab.ansi.org/directories/) · [UL fire-alarm service categories](https://www.ul.com/services/fire-alarm-service-provider-certification-and-compliance) · [ULC listing categories](https://canada.ul.com/ulcprograms/fireandsecurityalarmcertificateprograms/certificateserviceprocedures/)

For company research, both models get the same companies by name, across eight batches of three. They answer the same questions twice. With search enabled a model must find and interpret its own sources. With search disabled, each model gets the same short evidence packet and identifies what the supplied material supports. The packet comparison tests extraction from prepared evidence. It is easier to consult a short paraphrase than to interpret a lengthy accreditation schedule. The difference between web and packet therefore reflects evidence availability, source selection and extraction together.

| Model | CLI model ID | Provider and access | Published size and precision | Settings | Reason for inclusion |
| --- | --- | --- | --- | --- | --- |
| GPT-6.1 Sol | `gpt-6.1-sol`, dated revision unavailable in CLI replies | OpenAI, `codex exec` | Unpublished | Medium reasoning, live web or search disabled by task | General-purpose reference for open research |
| GPT-6 Luna | `gpt-6-luna`, dated revision unavailable in CLI replies | OpenAI, `codex exec` | Unpublished | Medium reasoning, same instructions and search settings | Compact model for repeated screening work |

For both models the prompt asks them to aim for up to 12 search or page operations in a task. This is an instruction. The CLI records web operations but does not impose a hard cap. Each call uses the same public-web setting for its arm and receives an isolated working directory. The user can inspect the prompt and full final response in the per-request cache. [Sol model page](https://developers.openai.com/api/docs/models/gpt-6.1-sol) · [Luna model page](https://developers.openai.com/api/docs/models/gpt-6-luna)

```mermaid
flowchart TD
    a["Acquisition brief"] -->|"From brief, or names from directory"| b["Sol / Luna via codex exec<br/>parallel runs<br/>ranked names and public citations"]
    p["Batch of 3 known companies"] -->|"Names and regions"| c["Sol / Luna via codex exec<br/>parallel live searches<br/>3 company profiles"]
    p -->|"Same dated evidence for both models"| d["Sol / Luna via codex exec<br/>parallel runs, search disabled<br/>3 company profiles"]
    b -->|"Wait for lists, pool company names"| v["Alias matching and evidence adjudication"]
    c -->|"Wait for profiles"| s["Field-by-field scoring"]
    d -->|"Wait for profiles"| s
```

There is one model call per arm, model and brief for discovery. A research call handles three companies at once, so the research denominator is the number of returned company profiles and fields. A call that times out can affect three profiles. Our models do not read each other's answers.

### What counts as a useful shortlist entry

A **verified fit** has positive public evidence for an operating site, all requested services, and independence. For a local or family business, affirmative language about current ownership can support the last criterion. If sources indicate a sale, merger or branch relationship, examine what transferred and how the business is operating now. If a lead is real and has an unresolved service, site or ownership question, it earns an unresolved label. A name whose identity the reviewers cannot match is tracked separately.

Each list gets ten slots. If a method returns only five names and three pass, the result is three verified fits out of ten slots. The five missing slots show how much of the requested shortlist was delivered. When a model includes an unresolved lead that reviewers can verify with additional evidence, the slot can still count. This measures the value of a returned name to a reviewer. The number is not a claim that the model itself had already completed the evidence check. We also count distinct verified companies found outside the source list. The same company can fit two briefs and use a slot in each, but it is only one new company in a country-level additions count.

The research score uses one field for the city, another for the state or province, one for control and one for each service. A fire-alarm example with a correct city, region, and two service fields but a wrong ownership label earns four of five. A cell earns credit for saying unknown if a field has no supporting evidence in the reference. A public statement discovered outside the packet may add useful information. Compare those claims to their cited evidence before treating them as verified improvements.

## 3. Shortlists and company profiles

### Shortlist yield

Compare the number of filled, verified slots for each method and market. The grey bar shows the same 30 slots on each side, ten for each of the three briefs. Dark bars count slots that passed after evidence review. The table also gives the reason for unfilled or unconfirmed slots and counts the unique companies that passed and were absent from the bounded list.

![Confirmed shortlist slots across the five workflows in each market](figures/shortlist_yield.png)

| Market   | Workflow            |   Verified |   Ruled out |   Unresolved |   Duplicate |   Empty |   Unreadable |   New companies |
|:---------|:--------------------|-----------:|------------:|-------------:|------------:|--------:|-------------:|----------------:|
| CA       | Directory list      |          2 |           5 |           11 |           0 |      12 |            0 |               0 |
| CA       | Luna with directory |          2 |           1 |            4 |           0 |      23 |            0 |               0 |
| CA       | Sol with directory  |          2 |           0 |            3 |           0 |      25 |            0 |               0 |
| CA       | Luna web search     |          3 |           1 |           16 |           0 |      10 |            0 |               2 |
| CA       | Sol web search      |          3 |           1 |            6 |           0 |      20 |            0 |               1 |
| US       | Directory list      |          3 |           5 |            9 |           2 |      11 |            0 |               0 |
| US       | Luna with directory |          3 |           1 |            3 |           0 |      23 |            0 |               0 |
| US       | Sol with directory  |          3 |           0 |            2 |           0 |      25 |            0 |               0 |
| US       | Luna web search     |          2 |           0 |           11 |           0 |      17 |            0 |               2 |
| US       | Sol web search      |          3 |           0 |            3 |           0 |      24 |            0 |               3 |

Open web search added four unique U.S. businesses and three Canadian businesses across both models. Sol returned 16 names across its six lists and produced 6 verified slots. Luna returned 33 names and produced 5 verified slots. The larger Luna lists yielded more leads that needed checking. In the U.S., both models found Fairfield Fire Protection. Their remaining verified additions were different. In Canada, each open-web arm filled three verified slots, which included Canadian Instrumentation Services Group in both runs.

When given the directory as a starting list, both models kept the same verified leads and returned shorter lists. The baseline contained ten ruled-out slots and two duplicates, while Sol with the directory returned zero ruled-out slots and Luna returned two. In this bounded comparison the models reduced the number of candidates needing review on the same starting names. They could only add new firms with the open brief. Several lists returned fewer than ten leads. Three briefs per market are enough to examine causes of failure, but the gap of one verified slot between the open-search models is too small for a general ranking.

### Accuracy against common company evidence

Compare the two web arms, then the two packet arms. The denominator is identical within each geography. The pilot has seven U.S. calibration and five fire cases, and six of each in Canada, so the U.S. has two more service fields overall. Fields whose evidence is unresolved are included because recognizing a gap changes what the reviewer has to check. The table shows the readable-only errors and agreement on unresolved fields to make that contribution visible.

![Exact agreement on company-profile fields for each market, model and evidence condition](figures/profile_agreement.png)

| Market   | Evidence   | Model   | Matches / fields   |   Unreadable profiles | Matches / readable   |   Readable field mismatches | Unresolved fields matched   |
|:---------|:-----------|:--------|:-------------------|----------------------:|:---------------------|----------------------------:|:----------------------------|
| CA       | packet     | Luna    | 69/72              |                     0 | 69/72                |                           3 | 12/14                       |
| CA       | packet     | Sol     | 70/72              |                     0 | 70/72                |                           2 | 12/14                       |
| CA       | web        | Luna    | 68/72              |                     0 | 68/72                |                           4 | 11/14                       |
| CA       | web        | Sol     | 66/72              |                     0 | 66/72                |                           6 | 9/14                        |
| US       | packet     | Luna    | 38/74              |                     6 | 38/38                |                           0 | 1/1                         |
| US       | packet     | Sol     | 74/74              |                     0 | 74/74                |                           0 | 11/11                       |
| US       | web        | Luna    | 71/74              |                     0 | 71/74                |                           3 | 9/11                        |
| US       | web        | Sol     | 71/74              |                     0 | 71/74                |                           3 | 9/11                        |

From the web, both models matched 71 of 74 U.S. fields. Across both markets their scores differed by 2 of 146 fields. Packet replies that could be read scored near the maximum. In the U.S., Sol got 74 of 74 and Luna got 38 of 38 on the six readable profiles. The two unreadable Luna calls each held three companies, so its overall U.S. packet score fell to 38 of 74.

Both unreadable messages held a complete JSON object followed by a final tag. One ended in `</final>` and the other in `</final`. Trimming just those terminal tags produced 74 of 74 U.S. fields for Luna and 143 of 146 across both markets. That changed the U.S. packet comparison to a tie. Across both markets, Sol matched 144 of 146 fields and Luna matched 143 after repair. One field does not separate the two models reliably. The saved replies let a reader verify both scores. [Parser sensitivity](data/research_summary_trimming_final_tag.csv)

Where both models had the same packet, most fields could be copied or left unresolved from relatively compact evidence. In open search, a mismatch can be a new fact outside the packet, a classification boundary, or a genuinely unsupported claim. A sourcing workflow needs both a usable response format and an evidence check that allows for those possibilities.

Source coverage is a different measure from agreement. All 128 assertions from Sol and all 125 from Luna in web research included URLs. A cited link tells the reviewer where to look, and a working link can still point to a page that supports a nearby service rather than the exact one in the brief. The saved field table records whether an asserted field came with a URL, and if a link in a packet reply matches a source supplied with that company. The worked cases below show where the cited page supports the claim and where reading the page changes the assessment. This pilot records source support for lead qualification and audits examples from the profile replies. The URL count measures how often the model offered a place to check.

## 4. Worked examples and errors

We selected the following cases for the decisions they illustrate. The complete set of ranked slots and fields remains in the saved tables. A case in two briefs can contribute two slots, while the same business counts once in a market-level list of additions.

### A lab that passes two service briefs

The Peterborough, Ontario, entry for Canadian Instrumentation Services Group (CA-01) pairs an accreditation-directory record with the lab's description of pressure, temperature, dimensional and electrical calibration for business customers. The company explicitly describes itself as independent and privately owned. This is affirmative public evidence for the first pass. The analyst would still confirm control with transaction diligence. [Accreditation record](https://customer.a2la.org/index.cfm?event=directory.detail&labPID=CF88E682-986D-4B36-9433-27140C3BC1C1) · [Company services and ownership](https://www.cisg.net/calibration/)

Sol's open search returned it for both Canadian calibration briefs. Luna returned it on the dimensional and electrical brief. Both directory-first runs kept it on both briefs. In the directory baseline it contributed two of the five verified shortlist slots across the two markets. This is the kind of company a good starting directory can already surface.

### A new name that still needed an ownership check

The open U.S. pressure-and-temperature brief sent to Sol requested firms with both services at an operating site in Michigan or Ohio and allowed unresolved leads. Sol returned only Grand Rapids Metrology (US-X07), with `"control":"unresolved"`. Its cited company information and service pages identified a family business and both service categories. A distributor's account also identifies the business as a fifth-generation family-owned company and names its Michigan locations. The source review therefore advanced the lead to verified fit under the pilot rubric. Grand Rapids Metrology was outside the starting list. A reviewer acting on Sol's answer would have had one lead to check and no second name from that call. [Company history](https://grmetrology.com/company/) · [Calibration services](https://grmetrology.com/accredited-calibration/) · [Distributor account](https://www.linkedin.com/posts/fairbanks-scales_metrology-industrialscales-familybusiness-activity-7482479033885159424-FThH)

This pattern held across the novel hits. Both models used the unresolved ownership label on all eight returned slots that ultimately became seven distinct verified additions. A human reviewer receiving these outputs would need to finish the same ownership step.

### End-to-end company research on Alliance Calibration

The web prompt gave the model the record below, alongside two other labs. It asked for the operating city, region, four calibration fields and control label. It asked for a public source and brief evidence for each assertion. The packet arm used these same fields and included paraphrases of the transaction and Cincinnati lab page.

```json
{"id":"US-06","company":"Alliance Calibration","region":"OH","sector":"calibration"}
```

The operating record points to a Cincinnati lab. Its current page describes pressure, temperature, dimensional and electrical work, and identifies the operation as formerly Alliance Calibration. The buyer's June 2022 announcement describes an acquisition of substantially all operating assets. For the company profile, the correct control field is `group`. The record does not imply that every legal entity that used the Alliance brand was bought outright. [Current operating site](https://www.transcat.com/calibration-lab-cincinnati-ohio) · [Acquisition disclosure](https://www.sec.gov/Archives/edgar/data/99302/000120677422001454/transcat4066851-ex991.htm)

This is a verbatim excerpt of two fields from Luna's cached web reply:

```json
{
  "control": "group",
  "control_url": "https://www.transcat.com/alliance-calibration-services"
}
```

The parser reads two strings and compares the first to the case's group label. It awards one control point. Luna also matched the city, region and all four services on this profile, for seven of seven fields. Both models returned the group control label on both research arms. The initial directory listed the lab under its prior name, so a team reading only the lab specialty would have spent a slot on a business the brief excludes. [Field-level scores](data/research_fields.csv)

### Two documents tell different parts of an ownership story

Alarme SL (CA-09) offers the requested fire-alarm work around Longueuil. Its careers page still describes a family business. The other party to the transaction, Sécur-Icare, documents a merger and a shared location. The two statements can be read together, but only the merger answers the question about current standalone operations. On web research Sol returned `group` citing Sécur-Icare. Luna returned `independent` citing Alarme SL's careers page. Both models returned the group label when given the merger in the packet. [Alarme SL careers](https://www.alarmesl.ca/carriere) · [Merger announcement](https://www.secur-icare.com/fr/chroniques-securite-entreprise/blog/fusion)

Les Gicleurs Québécois (CA-X10) was returned by Sol on the open fire-alarm brief as an unresolved lead described through its family history. The acquirer's law firm announced the acquisition by Partenaires A2 on 18 June 2026. This produced one of the two ruled-out slots across the two open-web methods. The transaction was disclosed after both model cutoffs, so an old company description was a particularly poor basis for clearing the independence requirement. [Transaction announcement](https://www.bcf.ca/intelligence-affaire/cas/bcf-partenaires-a2-acquisition-gicleurs-quebecois/)

### Missing evidence can make a correct search look wrong

Mitutoyo's Mississauga laboratory (CA-06) has a dimensional scope. Its original packet left control unresolved. Both web replies found group evidence, including Luna's link to Mitutoyo's overseas network, which identifies Mitutoyo Canada. Their control labels disagreed with the frozen packet. This is useful research supplied by the web arm, and it illustrates why agreement scores alone cannot tell us whether new claims are right or wrong. The parsed result and cited link remain available for inspection. [Mitutoyo network listing](https://www2.mitutoyo.co.jp/eng/corporate/network/overseas/list.html) · [Audit trail](data/research_fields.csv)

The opposite pattern appears at Accurate Fire and Security in Kettering, Ohio (US-12). Both web profiles labeled fire-alarm maintenance as supported. Their cited About page describes a general ability to maintain facility equipment. The Kettering service page names commercial inspections under alarm systems and lists detailed maintenance under extinguishers. A reviewer checking the exact wording would keep alarm maintenance unresolved. Both models left the field unresolved using the packet, including Luna's reply recovered by removing a trailing tag. [Kettering service categories](https://www.accuratefirepro.com/kettering-oh/) · [Company description](https://www.accuratefirepro.com/about-us/)

### A disclosed financial figure with the right scope

Across the 96 expected profiles, Sol's web reply about e2b calibration (US-07) was the only one to report a revenue number. It found that the acquired Ohio calibration operation contributed US$3.1 million of revenue to Transcat's fiscal 2024 results. The very same filing gives about US$3.1 million for the asset purchase price. These are different figures even though the dollars match. The model labeled the amount with its fiscal period and the acquired business scope. All other revenue entries and every EBITDA entry were null in the raw parsed replies. These results describe the disclosure found during the study. Other companies can have financial information outside the records searched. [Transcat fiscal 2024 filing, acquisition note](https://www.sec.gov/Archives/edgar/data/99302/000143774924018456/trns20240220_10k.htm)

## 5. Limits of a public-data screen

The four operating jurisdictions and selected industries are a starting point. Both industries have provider or service documentation that can be searched. A sector without common accreditation might return a less verifiable list or depend more heavily on customer contracts and company announcements. The regional counts here also depend on which cases we assembled and which public statements we could substantiate. They do not estimate the fraction of all owners in a country that an analyst can identify.

The evidence dates span old transactions and current sites. The briefs were written for this study and public pages were checked in November 2026. Some pages lack a date and some filings predate the published model cutoffs of 30 April 2026 for Sol and 18 May 2026 for Luna. The models could have seen older names and facts during training. The scores can overestimate performance on entirely new companies. A newer evaluation could focus on ownership changes publicly disclosed after both cutoffs.

A first-pass screen records evidence about a company's operations and ownership. It gives an analyst a reason to look further. The transaction decision also needs diligence on financials, control, strategic fit and seller interest. We report financial figures only when they were publicly disclosed with a period and scope, and the reported field agreement excludes finance. Asset sales and consolidated filings make it especially easy to attach a number to the wrong entity.

The workflow comparison uses a deterministic public-source baseline. The time-boxed human comparison and analyst review time require a participating analyst. The call elapsed times in the cache include the local CLI and web search and should be read as model workflow timing. The protocol records when rules were set, changes to the CLI invocation and any later evidence used to qualify candidates for scoring. [Protocol](data/PROTOCOL.md)

## 6. Reproduction

The notebook replays 56 cached calls through Python. The model requests originally ran using Codex CLI 0.160.1, under the existing subscription, with Python 3.13 and the open-model API routes unused. No separate API spend was incurred, and the CLI did not report dollar cost. The measured calls reported 5,600,940 input tokens including 3,767,936 cached input tokens, and 60,010 output tokens. The 24 recorded startup failures are retained outside the measured sample.

| task      | arm             | model   |   Calls |   Median seconds |   Recorded web operations |
|:----------|:----------------|:--------|--------:|-----------------:|--------------------------:|
| discovery | directory-first | Luna    |       6 |             26.1 |                        16 |
| discovery | directory-first | Sol     |       6 |             39.4 |                        25 |
| discovery | web             | Luna    |       6 |             43.5 |                        18 |
| discovery | web             | Sol     |       6 |             59   |                        25 |
| research  | packet          | Luna    |       8 |             17.5 |                         0 |
| research  | packet          | Sol     |       8 |             20.4 |                         0 |
| research  | web             | Luna    |       8 |             27.1 |                        16 |
| research  | web             | Sol     |       8 |             55.5 |                        32 |

The medians are per CLI call. A research call processes three businesses. A web-operation count includes visible search and page operations. Neither is an analyst labor measure.

From this folder, install the notebook runtime if needed and execute it:

```bash
python -m pip install jupyter pandas matplotlib requests
python -m nbconvert --to notebook --execute --inplace 46_us_canada_deal_sourcing.ipynb
```

The default `LIVE = False` raises on a cache miss, so replay makes no model or search calls. The saved request includes the model, task, full prompt, reasoning setting, web setting and cache version. The cache stores the final raw message, visible search events, token counts and elapsed time. Use those files for inspecting a reply. The public web changes over time, so a new live run can yield different pages and candidates and requires updated lead adjudication. Model and size settings sit at the top of the notebook code.

[Executed notebook](46_us_canada_deal_sourcing.ipynb) · [Shortlist slots](data/shortlist_slots.csv) · [Research field scores](data/research_fields.csv) · [Original responses](data/calls/) · [Protocol and amendments](data/PROTOCOL.md)

## 7. Future work and further reading

### Future work

- Give analysts the same six briefs in balanced order across manual and assisted conditions, measure verified fits per analyst hour, and record when an unsupported apparent lead causes extra work.
- Start from a frozen list of accreditation and fire-alarm certification entries in the four jurisdictions, then compare directory-only and mixed-source search over the same cap on reviewed firms. Measure how many of the web additions remain genuinely new with the larger baseline.
- Repeat the company-profile test on dated acquisitions published after both model cutoffs, with old and newly announced ownership evidence in the same packet. Measure whether the model correctly updates the label when the operating brand persists.
- Add a thesis without a common industry certification and compare service and ownership verification rates. This tests how much of the first-pass yield depends on the availability of scope records.

### Further reading

Links checked on 17 November 2026.

- [Accreditation vs. certification](https://www.nist.gov/nvlap/accreditation-vs-certification) (NIST, accessed 2026). Explains how a laboratory's accreditation scope relates to the actual tests and measurements it can carry out.
- [Directory of accredited organizations](https://customer.a2la.org/?event=directory.index) (A2LA, accessed 2026). Demonstrates why commercial availability, location and scope belong in a structured candidate search.
- [Find an authorized service provider](https://ised-isde.canada.ca/site/measurement-canada/en/authorized-service-providers/find-authorized-service-provider) (Measurement Canada, 2021). Shows where to identify recognized Canadian service providers for specific inspections and standards calibration.
- [Public disclosure of corporate information](https://ised-isde.canada.ca/site/corporations-canada/en/business-corporations/public-disclosure-corporate-information) (Corporations Canada, accessed 2026). Explains which fields are available in the Canadian federal search.
- [CanadaBuys award notices](https://open.canada.ca/data/en/dataset/a1acb126-9ce8-40a9-b889-5da2b1dd20cb?res_page=1) (Public Services and Procurement Canada, accessed 2026). The open-data catalogue offers award records that can give service and buyer evidence for government suppliers.
