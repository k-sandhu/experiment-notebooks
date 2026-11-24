# Issues the workflow authors found in the organisation files

The agents that wrote step-by-step workflows were told not to edit the organisation files. Where a
workflow's research or arithmetic disagreed with an organisation file, they reported it, and the reports
are collected here.

On 2026-11-17 the mechanical ones were applied by `tools/fixes_2026_11_17.py`: roles and systems the
workflows use were added to the organisation files, missing links were added, standing inputs that do not
start cases were moved from `triggered_by` to a new `inputs` field, and two facts stated in the pension
manager's annual report were corrected. Each entry below is marked applied or open. The open ones are
questions of headcount, volume, pay or structure that need someone who knows the organisation.

## public-asset-manager

Reported by the external manager and fund commitment workflows (`pam-ext-manager-*`, `pam-fund-commitment`,
`pam-capital-call-processing`):

- **Open.** The external manager research team (four analysts and a head) looks small. Monitoring 124 mandates
  implies about 2.5 analyst FTE and searches add about 1 more.
- **Open.** Fund commitments of about 15 a year are above the 6 to 8 named in the organisation's 2020 and 2021 news
  releases.
- **Open.** 60 capital calls a month implies about 4 calls per fund a year. A 45-fund study (Investec, 2022) found
  about 2 a year in 2019 to 2021.

Reported by the reporting and billing workflows (`pam-client-monthly-reporting`,
`pam-client-quarterly-reporting`, `pam-performance-attribution`, `pam-cost-allocation-billing`):

- **Applied.** Several `process_map` role lists leave out roles that do the work: compliance analyst, fund accountant,
  manager of client reporting and corporate accountant.
- **Open.** `cost-allocation-billing` lists client payments under `triggered_by`, but payments close the case.
- **Open.** Quarterly invoicing is unverified. The year-end receivable ($36.6M, about 62 days of 2021 recoveries) fits
  monthly invoicing just as well.
- **Applied in part: the three reports are now listed as sources and the cost recovery figure is cited to the 2021 report. The file's other numbers have not been re-checked against them.** The organisation file says the annual reports could not be read. This agent read the 2020 to 2022 reports,
  which confirm the SOC 1 reports (Type I 2021, Type II 2022), the Cost Allocation Committee and $216.6M of
  cost recoveries. The file's evidence tiers and sources should be updated from them.
- **Open.** The manager of client reporting and the manager of performance are costed at $60 to $135 an hour, which
  looks low.

Reported by the client workflows (`pam-client-onboarding-transition`, `pam-client-ips-asset-mix-review`,
`pam-client-cash-flow-instructions`, `pam-client-portfolio-rebalancing`):

- **Applied in part: the order is now listed as a source and noted in the assumptions. Controls in the file were not re-tiered.** The organisation file says the Ontario Securities Commission order could not be opened. This agent opened
  it (decision of 17 May 2017). It sets several controls, for example that pool units go only to members who
  are accredited investors.
- **Open.** The onboarding entry says the process starts after the agreement is signed, but lists the accepted proposal
  and the regulation change as triggers. The workflow includes the agreement negotiation.
- **Applied.** These process entries leave out roles the work needs: the compliance, reconciliation, risk, performance and
  total portfolio analysts, the public equities portfolio manager, and the cash and collateral manager.

Reported by the pool and settlement workflows (`pam-pool-unit-pricing`, `pam-pool-unit-transactions`,
`pam-trade-settlement-fails`, `pam-daily-reconciliation`):

- **Applied.** Several `process_map` role lists leave out roles that take part: the data analyst and vice president of
  investment operations in pricing, the cash manager in unit transactions, the vice president in
  reconciliation.
- **No change.** The cost note says wages for NOC 11101 were used as a stand-in, so this is intended. Analyst roles carry occupation code NOC 11109, but their cost notes say they are priced from NOC 11101.

Reported by the valuation, risk and close workflows (`pam-private-quarterly-valuation`,
`pam-daily-risk-limit-monitoring`, `pam-fund-accounting-close`):

- **Open.** Investment accounting has no manager between the director and five senior accountants, so the director
  approves every journal and package. This may overstate the director's load.
- **Open.** No role suits private credit direct holdings in the valuation process. The workflow used the
  infrastructure principal role.
- **Applied.** There is no business object for breach notices to clients or the board. The workflow used `risk_report`.

## equipment-finance-co

Reported by the documentation and funding workflows (`efc-prepare-lease-documents`,
`efc-audit-and-fund-contracts`, `efc-book-contracts`, `efc-sell-securitisation-pools`):

- **Open.** The funding team looks too small. Hands-on time implies about 8.6 FTE for funding audits and about 4.5
  for booking, roughly 13 against the file's 11 funding specialists, before registration support.
- **Open.** 2,000 lease document "packages" a month only fits 1,400 fundings if read as document requests. Reissued
  packages for one deal were modelled as rework inside a case.
- **Applied.** Conduit funding proceeds are listed as a trigger of the securitisation pool sale, but they arrive in the
  middle of that process. The workflow gives that trigger a share of zero.
- **Open.** No role owns setting up vendor bank details. The workflow gave it to the operations analyst to keep it
  separate from payment approval.

Reported by the origination and credit workflows (`efc-quote-point-of-sale-payments`,
`efc-intake-credit-applications`, `efc-adjudicate-small-ticket-credit`, `efc-underwrite-mid-ticket-credit`):

- **Applied.** The deal desk process says the vendor desk sends it off-card deals, but the process map has no link from
  quoting to it.
- **Applied.** There is no system for corporate registry searches. The intake workflow adds one.
- **Open.** Credit coordinators (9) and mid-ticket analysts (8) look about one person short each for the stated
  volumes.
- **Open.** It is unclear whether the director of credit approves inside underwriting or in the separate "approve
  above authority" process. The workflow sends about 30 files a month there, against the file's 60.
- **Applied.** Standing inputs listed as triggers (rate cards, system releases, policy changes, bureau reports) do not
  start cases. Workflows give them a share of zero.

Reported by the buyout, end-of-term and collections workflows (`efc-quote-and-process-buyouts`,
`efc-manage-end-of-term`, `efc-collect-early-stage`, `efc-collect-late-stage`):

- **Open.** Lease administration has 10 specialists. Payouts (3.5 FTE) and end of term (3.5 FTE) leave about 3 FTE
  for 1,250 title transfers a month plus restructures and assumptions, which looks understaffed.
- **Applied: collections now links to billing for disputes, and late stage to legal for insolvencies. The link to recoveries was left as the workflow modelled it.** Collections has no link back to billing for disputed charges, and late stage has no link to recoveries or
  legal for insolvencies.
- **Open.** End-of-term valuations (about 140 a month) are half the valuation process's 280, so a whole-organisation
  model should count them once.
- **Open.** The 16 early-stage collectors are more than the roughly 9.5 FTE the modelled work needs.

Reported by the billing, service and close workflows (`efc-bill-customers`, `efc-apply-customer-payments`,
`efc-handle-service-requests`, `efc-close-the-month`):

- **Applied.** `handle-service-requests` has no link to `manage-end-of-term` or `collect-early-stage`, although
  representatives route end-of-term choices and pass customers in arrears to collections.
- **Applied.** `close-the-month` has no link to `report-to-securitisation-funders`.
- **Open.** 9,000 manual payment items a month for seven clerks, who also handle returned payments, works out to
  about 4 to 5 minutes an item. That volume looks high.

## diagnostic-lab-services-co

Reported by the workplace and clinical trials workflows (`dls-wp-collection`, `dls-wp-tox-testing`,
`dls-ct-sample-testing`):

- **Open.** 35 occupational collectors cannot cover much on-site collection volume, so most collections were given to
  centre laboratory assistants.
- **Open.** 35 toxicology technologists look high; per-specimen work implies about 14. The 15 toxicology laboratory
  assistants are almost fully used.
- **Open.** 14 kit and sample technicians look tight. Sample receipt alone takes about 10, before building about 5,000
  kits a month.
- **Applied.** `ct-sample-testing` lists `it-lis-change` as a trigger. It is a precondition, not something that starts a
  case.
- **Open.** The medical review officer role could move up from tier C: a job posting for a medical review officer
  assistant exists.

Reported by the genetics, portal and billing workflows (`dls-gs-genetic-testing`, `dls-cd-portal-results`,
`dls-fin-provincial-billing`):

- **Applied.** The `gs-genetic-testing` role list leaves out the genetic counsellor and customer care roles.
- **Applied.** Nothing links `cd-portal-results` to `lp-privacy-incident`, or `fin-provincial-billing` to
  `fin-patient-billing` for uninsured claims.
- **Applied.** `fin-provincial-billing` lists remittances and the funding agreement as triggers, though they are inputs.
- **Open.** A 2026 job posting pays a senior billing clerk CAD 40,000 to 46,000 a year, below the file's cost range.
- **Open.** The 2017 Ontario Auditor General's report says some community-laboratory genetic tests were licensed only
  for non-Ontarians, which may bear on the genetics volume.

Reported by the testing, reporting and critical result workflows (`dls-cl-core-testing`,
`dls-cl-result-reporting`, `dls-cs-critical-result-notification`, `dls-hs-reference-testing`):

- **Applied.** There is no external party for OLIS (the Ontario Laboratories Information System), so submitting results
  to it cannot be listed as an interface.
- **Open.** 210 core laboratory staff for about 42 million tests a year is about twice the highest published
  productivity figure (CAP survey, top 10% of high-volume laboratories). Per-requisition work alone takes
  most of that headcount.
- **Open.** The reference laboratory's roughly 100 bench staff is tight for 60,000 requisitions a month of mostly
  manual testing.
- **Applied.** Some `triggered_by` entries are supporting inputs, not case triggers: `qc_record`, `lis_change`,
  `competency_record` and `notification_record`.
- **Applied.** `lab_assistant_reference` is used in reference testing but missing from that process's role list.

Reported by the insurance and mobile workflows (`dls-in-order-management`, `dls-in-paramedical-exam`,
`dls-in-tele-interview`, `dls-mb-ltc-collection`):

- **Open.** Contracted examiners are listed as an outside party, not a role. The exam workflow adds
  `contracted_health_professional` with `not_in_org_file`. A simulation should pool it with the employed
  examiners.
- **Open.** Headcounts are tight: order management alone needs about 58 to 70 of the 70 case coordinators, and
  long-term care collections need 88 of the 120 mobile laboratory assistants before house calls.
- **Open.** The monthly volumes for paramedicals, tele-interviews, attending physician statement requests and
  inspections add up to the 38,000 orders, so one order is one service.
- **Applied.** There is no link from tele-interviews back to order management, although disclosures in an interview
  often lead to new orders.
- **Open.** The file says the examiner calls the applicant to book; the company's pages say a customer care
  representative does.

Reported by the collection, accessioning and courier workflows (`dls-cl-psc-registration`,
`dls-cl-psc-collection`, `dls-cl-specimen-accessioning`, `dls-lg-route-pickup`):

- **Open.** Headcounts look too low for the volumes. Registration plus collection need about 12.4 minutes of staff
  time a visit, about 890 FTE against 635 centre staff. Courier stops need about 325 FTE against 220
  couriers. Accessioning needs about 200 FTE against 150 processing laboratory assistants.
- **Open.** The Ontario laboratory assistant role is 396 of 400 FTE allocated once `dls-wp-collection` is counted.
- **Applied.** Several `triggered_by` inputs enable the process and do not start cases: site openings, competency
  records, supply deliveries, client onboarding.
- **Applied.** The file has no health card validation system. The registration workflow adds one.

## pension-investment-manager

Reported by the reconciliation, accounting and valuation-run workflows (`pim-mkt-reconcile`,
`pim-fin-investment-accounting`, `pim-io-price-daily-nav`, `pim-fin-monthly-nav-close`):

- **Applied.** `fin-investment-accounting` says holding subsidiaries add consolidation entries. The F2022 annual report
  says the fund is an IFRS 10 investment entity, so those subsidiaries are carried at fair value and not
  consolidated.
- **Applied.** `tf-cpp-transfers` has 1 to 2 cases a month, but the annual report says transfers arrive weekly.
- **Applied.** The `mkt-reconcile` roles leave out trade support and corporate actions staff, who fix most breaks.
- **Applied.** The file has no reconciliation tool and no evaluated price feed among its systems.

Reported by the total fund, collateral and risk workflows (`pim-tf-balancing-rebalance`,
`pim-tf-liquidity-forecast`, `pim-io-collateral-margin`, `pim-risk-market-limit-monitoring`):

- **Open.** Loaded hourly costs are very high (total fund management principal C$571, managing director C$1,662), so
  labour cost per case is high. This comes from scaling pay to total personnel expense.
- **Open.** Total fund management headcount of 80 matches the F2022 annual report, but the F2021 report says 115.
- **Applied.** The process map leaves out roles these processes use: the liquidity principal and trader in rebalancing,
  and the funding principal in liquidity forecasting.

Reported by the private deal and valuation workflows (`pim-pe-direct-due-diligence`, `pim-tf-pec-approval`,
`pim-lc-negotiate-close`, `pim-fin-quarterly-valuation`):

- **Open.** Due diligence volume of 28 deals a month looks high. Direct private equity held 88 investments in F2021
  with C$3.5 billion of new investment, yet the volume implies about 7 closings a month and ties up about
  46 FTE.
- **Open.** There is no committee secretary role, and the Valuation Committee has no chair or members.
- **Applied.** The risk opinion is listed as a trigger for committee approval, but it is an input to every item.
- **Open.** `legal_md` is listed for closing but has no clear step.

Reported by the trade lifecycle workflows (`pim-mkt-execute-trades`, `pim-mkt-book-allocate`,
`pim-mkt-confirm-affirm`, `pim-mkt-settle-trades`):

- **Open.** Order capture already includes traders accepting and planning orders, which overlaps with execution. The
  execution workflow starts at the blotter.
- **Applied.** Four roles are used outside the process map's role lists: the portfolio manager, the head of trading
  desk, the investment data analyst, and the trader in confirmation.
- **Open.** Booking's driver is the settlements driver (48,000 a month), but its volume is 40,000.
- **Open.** Trader cost (C$373 an hour) is far above the Job Bank median wage (C$47).

Reported by the fund commitment, capital call and performance workflows (`pim-pe-fund-selection-commitment`,
`pim-io-capital-calls`, `pim-fin-performance-attribution`):

- **Open.** Legal negotiation of fund documents is in both `pe-fund-selection-commitment` and `lc-negotiate-close`,
  and the committee work overlaps with `tf-pec-approval`. A combined model should count each once.
- **Applied.** `tax_structure_memo` is listed as a trigger but arrives partway through the process.
- **Applied for the role list only.** `ra_principal` has no clear part in fund selection, which is still open. The performance process's role list lacks the fund
  accountant and controller.
- **Open.** Loaded hourly costs include incentive pay, so labour cost is about C$43,000 a commitment and C$50,000 a
  performance cycle.

## Second round: reports from the priority 2 workflows

On 2026-11-18 the fix script was run again: every role and system a workflow uses is now listed by its process, standing inputs the workflows declare were moved out of the triggers, and the few workflow links the map lacked were added. Entries about missing role listings are marked applied. Everything else is open.

### equipment-finance-co

Reported by `efc-manage-daily-cash`, `efc-account-for-leases-and-credit-losses`, `efc-file-sales-taxes`:

- **Open.** The daily cash process lists no borrowing base input and no flow of collections to the conduits. The
  chief financial officer is missing as back-up approver.
- **Applied for the role listings.** The lease accounting role list leaves out the asset manager (residual values) and the chief financial
  officer (quarterly committee).
- **Open.** Six sales tax returns a month only works as five monthly returns plus about one annual or amended
  return. The file never says whether the company is a financial institution for GST/HST purposes.

Reported by `efc-process-returned-payments`, `efc-track-equipment-insurance`,
`efc-restructure-and-defer-payments`, `efc-repossess-equipment`:

- **Open.** The process map has 1,300 returned payments a month. The early-collections workflow says 75% of its
  2,700 accounts come from returns, about 2,000. The two figures disagree.
- **Open.** Cash application clerks have 1.0 FTE left, but returns need about 1.5 FTE.
- **Open.** Insurance tracking has five staff, but the step times imply about 6 FTE at 4,400 cases a month.
- **Applied for the role listings.** The restructure process needs the securitisation analyst to check conduit limits, but the process map
  does not list that role.

Reported by `efc-recover-deficiencies-and-write-off`, `efc-remarket-equipment`,
`efc-report-to-securitisation-funders`, `efc-report-credit-facility-covenants`:

- **Open.** Late-stage collections sends about 58 referrals a month on its own, so deficiency volume is probably
  nearer 90 than the stated 70.
- **Open.** Insolvency files reach recoveries under the write-off request object, because there is no dedicated
  link for them.
- **Open.** Several triggers arrive partway through a case: auction house proceeds, the servicer-report data feeds
  and the risk report.
- **Open.** The `efc-close-the-month` workflow does not send closed balances to servicer reporting, although the
  process map now says it should.
- **Open.** The remarketing roles have no occupation codes.

Reported by `efc-communicate-credit-decisions`, `efc-originate-direct-deals`, `efc-monitor-portfolio-risk`,
`efc-search-and-register-security`:

- **Open.** Registration staffing is tight: funding specialists are fully allocated elsewhere and the 3
  registration clerks come out fully used.
- **Open.** 750 direct opportunities a month for 14 account executives is high; 13.5 of the 14 FTE are used.
- **Open.** At 66% approval, credit decisions produce about 1,830 document requests a month, against the file's
  2,000 document packages.
- **Open.** The process map has no output for discharging registrations on deals that never fund.

### pension-investment-manager

Reported by `pim-mkt-order-capture`, `pim-ae-fundamental-research`, `pim-ci-credit-underwriting`,
`pim-pe-source-screen`:

- **Open.** No process sends the restricted list to order capture. The workflow uses `lc-negotiate-close` as a
  standing input.
- **Open.** Credits approved within the Credit Investments department's own authority have no output. The workflow
  adds an approval sent to `lc-negotiate-close`.
- **Open.** 120 opportunities a month for private equity screening looks high: the direct portfolio grew from 85 to
  88 holdings in fiscal 2021.
- **Open.** `tf-capital-allocation` sends the department mandate as a trigger, but it starts no case.
- **Open.** Traders are almost fully used: 23.7 of 26 FTE are now claimed by workflows.

Reported by `pim-ex-board-reporting`, `pim-tf-strategic-portfolio-design`, `pim-tf-capital-allocation`,
`pim-tf-leverage-management`, `pim-cmf-select-external-managers`:

- **Open.** Board volume counts only the 36 regular meetings. Fiscal 2022 held about 54 including special meetings.
- **Open.** No process feeds HR and compensation committee papers into board reporting.
- **Applied for the role listings.** Roles are missing from process lists: the chief executive for delegated manager approvals and as chair
  of the senior management committee, an operational due diligence sign-off role, an associate for leverage work,
  and a risk role in capital allocation.
- **Open.** Board approval appears as a trigger for manager selection, but it happens inside a case.

Reported by `pim-pe-asset-management`, `pim-ra-due-diligence`, `pim-ra-asset-management`,
`pim-fin-quarterly-financial-statements`:

- **Open.** Neither asset management process links to screening, diligence or committee approval for follow-on
  investments.
- **Open.** `ra-due-diligence` lists the adviser reports, tax memo and ESG assessment as triggers. They arrive
  during a case.
- **Open.** Real Assets volumes look high: it added 25 investments in F2021 against 25 deals a month in deep
  diligence, and held 204 investments against 250 asset-quarters reviewed a quarter.
- **Applied for the role listings.** Several roles the workflows need are missing from the process map role lists, and the statements
  process does not show its input from the performance team.
- **Open.** The valuation workflow expects deal team value proposals about 10 days after quarter end, before the
  quarter-end company packs normally arrive.

Reported by `pim-fin-annual-report`, `pim-risk-transaction-review`, `pim-risk-limit-breach-escalation`,
`pim-io-private-cash-settlement`:

- **Open.** The process map allows 2 to 12 limit breaches a month, but the daily risk workflow issues formal notices
  on only about 1.6% of days, roughly 0.3 a month.
- **Open.** All risk roles sit in the `far_risk` unit, not the owner unit `risk_inv`.
- **Applied for the role listings.** Roles missing from process lists: the chief executive, rewards and board secretariat specialists, a
  deal-team role, the liquidity principal and the head of investment operations.
- **Open.** Standing inputs missing from the map: the year-end net asset value and valuations for the annual
  report, and the approval decision for cash settlement.

### public-asset-manager

Reported by `pam-pool-rebalancing-cash-deployment`, `pam-internal-equity-decisions`,
`pam-internal-fixed-income-credit-decisions`, `pam-private-credit-underwriting`, `pam-trade-execution`:

- **Open.** The equity and fixed income decision processes list the annual plan, reference data and compliance
  exceptions as triggers. Orders actually start from scheduled model runs and research.
- **Applied for the role listings.** Several role lists leave out the compliance analyst, the managing director of global credit and the
  senior managing director of equities and credit.
- **Open.** The file assumes an internal trading desk of four, and no source opened describes one.

Reported by `pam-distribution-processing`, `pam-investment-data-management`,
`pam-manager-fee-validation-payment`, `pam-annual-financial-statements-audit`, `pam-annual-cost-budget`:

- **Open.** The audit process lists the auditor's opinion as a trigger, but it is the result. The fee process lists
  the manager mandate as a trigger, but it is a standing input.
- **Open.** The scale item of about $100M a year in operating costs conflicts with the 2021 annual report, which
  shows operating expenses of $156.5M.
- **Open.** The securities regulator's order exempts the pools from the financial statement rules (NI 81-106), so
  the assumed four audited pool statement sets a year are not confirmed.

Reported by `pam-pe-coinvest-screening-dd`, `pam-real-asset-direct-investment-dd`, `pam-ext-manager-onboarding`,
`pam-ext-manager-termination-transition`, `pam-client-service-requests`:

- **Open.** `pe-coinvest-screening-dd` says seven direct and co-investments in 2021. The 2021 annual report says
  eight new deals plus two follow-ons.
- **Open.** Several triggers are standing inputs: the investment plan in both diligence processes, and the
  warehouse, risk and performance outputs in client service requests.
- **Open.** The manager research analyst role had only 0.88 FTE left before these workflows.

Reported by `pam-board-committee-meetings`, `pam-annual-investment-plan-benchmarks`,
`pam-investment-committee-approval`, `pam-liquidity-forecasting`, `pam-overlay-fx-leverage`:

- **Open.** The file has the investment committee chaired by the chief investment officer with the chief executive
  and chief risk officer. The 2021 and 2022 annual reports say the chief investment officer and chief risk officer
  co-chair it with the general counsel.
- **Open.** The board has no separate risk committee. In 2021 there were four committees: finance and audit, HR
  and compensation, nominating and governance, and a board investment committee created in September 2021.
- **Open.** The annual reports show 27 to 28 board and committee meetings a year, about 2.3 a month, against the
  file's 2.

Reported by `pam-risk-reporting-stress-testing`, `pam-new-investment-risk-review`, `pam-pool-launch`,
`pam-trade-capture-confirmation`, `pam-daily-cash-management`:

- **Applied for the role listings.** Process role lists leave out roles the work needs: the portfolio risk analyst, deal-team principals and
  the investment office in risk review; business systems analysts and a compliance analyst in pool launch; the
  trader and a total-portfolio manager in daily cash; the head of trading in trade capture.
- **Open.** The detailed risk review runs longer for full reviews of direct deals than the single four-day step the
  upstream workflows assume.

Reported by `pam-private-deal-closing-funding`, `pam-investment-legal-agreements`,
`pam-investment-compliance-monitoring`, `pam-recruit-onboard-staff`, `pam-annual-report-public-results`:

- **Open.** The organisation's reports give 207 staff at end 2020, 257 at end 2021 and 328 at end 2022. The file's
  242 employees for 2021 is low, and so is its 5 hires a month; the growth implies about 6 a month in 2021 and 8
  in 2022.
- **Open.** There is no generic hiring manager role. The recruiting workflow adds `hiring_manager` (not in the
  organisation file).
- **Applied for the role listings.** Roles that do the work (tax, cash, head of operations, general counsel, rewards) are missing from
  process role lists.

### diagnostic-lab-services-co

Reported by `dls-in-aps-collection`, `dls-wp-test-ordering`, `dls-wp-mro-review`, `dls-wp-result-reporting`:

- **Open.** The file has no medical review officer assistant role, although the company posts that job. The
  workflows add `mro_assistant` (not in the organisation file) at 9.0 FTE, with an estimated cost.
- **Open.** Attending physician statement coordinators look short: about 41 hands-on minutes a statement times
  8,000 a month implies about 42 FTE against 35 in the file.
- **Open.** Workplace program coordinators are nearly used up: about 15.2 of 18 are claimed, leaving about 2.8 for
  program set-up and occupational health. Medical review officers: 2.8 of 3 part-time physicians are used.
- **Open.** The physician's statement and the donor's explanation are listed as case triggers.
- **Open.** `dls-wp-tox-testing` sends negative results straight to employers. US DOT rules require medical review
  staff to check the custody form first, which `dls-wp-result-reporting` models. The two workflows disagree.

Reported by `dls-mb-ltc-scheduling`, `dls-hs-referral-intake`, `dls-hs-result-delivery`,
`dls-in-insurance-lab-testing`, `dls-in-case-review-release`:

- **Open.** Three roles are fully or nearly used by the workflows: referral laboratory assistants (25 of 25),
  evidence reviewers (15 of 15) and mobile schedulers (13 of 14).
- **Open.** Insurance laboratory results go straight to the insurer, but the process map lists only case review as
  the receiver.
- **Open.** Referrals arrive only through the company's own couriers in the map, although the file also lists air
  and overnight carriers.
- **Open.** The fax and telephony systems do not list the mobile scheduling desk among their users.

Reported by `dls-fin-patient-billing`, `dls-fin-client-invoicing`, `dls-cs-client-inquiries`,
`dls-fac-instrument-maintenance`:

- **Open.** Client payment remittances and the patient's payment are listed as triggers, but do not start a case.
- **Open.** No internal source is listed for scheduled in-house maintenance, and there is no link back to
  provincial billing for credits on tests that turn out to be insured.
- **Applied for the role listings.** Approving roles are missing from process role lists: billing manager, account manager, laboratory
  manager and charge technologist.
- **Open.** Ontario laboratory assistants (99%) and Quebec auxiliary nurses (95%) are almost fully used by the
  workflows.

Reported by `dls-gs-ihc-molecular-pathology`, `dls-gs-cdx-program`, `dls-cd-appointment-booking`,
`dls-qa-proficiency-testing`:

- **Open.** The molecular pathology unit has no laboratory assistant or transcriptionist, and its manager sits in
  the genetics laboratory.
- **Open.** `gs-cdx-program` lists the sponsor contract and the returned biomarker report as case triggers. Blood
  results for companion diagnostics patients have no process link.
- **Open.** The company's site says most visits need no appointment, which conflicts with the file's 57% booked
  share.
- **Open.** Proficiency testing omits SAMHSA as a recipient and the roles that sign attestations.

Reported by `dls-qa-accreditation-inspection`, `dls-qa-nonconformance-capa`, `dls-qa-new-test-validation`,
`dls-it-lis-change`:

- **Open.** Accreditation volume (0.2 to 1 a month) looks low. The company's licences page lists about 20
  accreditations, which suggests 10 or more visits a year.
- **Open.** There is no assessment notice business object, so the accreditation process is triggered by the
  accreditation report.
- **Open.** `cl-result-reporting` opens nonconformances, but the process map does not list that link.

Reported by `dls-cl-daily-qc`, `dls-cl-microbiology-testing`, `dls-cl-cytology-screening`,
`dls-cl-histology-processing`, `dls-cl-pathology-signout`:

- **Open.** The cytology unit holds only cytotechnologists, with no one to prepare slides. The workflow adds
  `cytology_lab_assistant` (not in the organisation file, 9 FTE), supported by a company job posting.
- **Open.** The pathologists' assistant cost of CAD 55 to 75 an hour looks high. A 2026 posting pays $28 to $30.50
  an hour, about CAD 38 to 41 loaded.
- **Open.** Microbiology lists the quality control record as a trigger. Daily quality control is triggered by a
  maintenance record but has no output for service calls.
- **Open.** The cytology and histology workflows feed about 17,100 cases a month to sign-out against the map's
  16,000, while `dls-cl-result-reporting` assumes only about 10,350 pathology reports a month.

# Issues reported for the seven operating companies (2026-11-24)

The 66 workflow batches for the oil field services company, electricity distributor, power generator, gold
miner, general contractor, trucking company and hospital each reported problems in their organisation file.
Their reports follow unedited, grouped by organisation and batch. None has been applied yet; all are open.
`tools/assemble_check.py` gives the counts behind them: 52 to 129 workflow roles per organisation are missing
from the process map's role lists, and 39 to 76 workflow interfaces are missing from the map.

The issues most likely to change results, in the order to settle them:

- **mining-operator-co. Applied 2026-11-24; see the status note under the mining heading below.** The
  reference mine's technical reports (SRK 2022, Wesdome 2016) contradict the
  organisation file. The mill recovers gold by gravity and Merrill-Crowe, not carbon-in-pulp and
  electrowinning. Tailings are filtered and dry-stacked. The mill is 16.6 km by road from the mine portal. The
  shaft hoists to a dump at the 70 m level. The assay lab is in Wawa. The fleet is 19 loaders and five 30-tonne
  trucks, with 8 loader and 24 truck operators. Mill crews work 7 on, 7 off. The mill workflows follow the
  reports; the organisation file needs rewriting to match.
- **freight-carrier-co. Applied 2026-11-24; see the status note under the trucking heading below.** Pickup and delivery drivers: 540 in the file, about 690 claimed by workflows and
  about 790 when scaled from Old Dominion's published ratio. Billing auditors, pricing analysts, dock workers
  and linehaul drivers are also short. Workflows claim 93% of all staff.
- **general-contractor-co. Applied 2026-11-24; see the status note under the contractor heading below.** About 10 contract awards a month in the file, but its own bid volumes and hit
  ratios give about 5. RFIs are about 50% above the published rate per $1M of work. Holdback releases and
  lien adjudications are too high.
- **power-generation-co. Applied 2026-11-24; see the status note under the generator heading below.** Major outage planning and execution, capital projects, coal-to-gas conversions and
  hedge trades are counted as project-months or all trades; workflows use 0.8, 4, 0.07 and 120 a month
  against 3 to 4, 60, 3 and 800. Operator staffing looks coal-era and wind technicians are short.
- **community-hospital-corp. Applied 2026-11-24; see the status note under the hospital heading below.** Operating room capacity (17 rooms) is about half what 3,700 cases a month need.
  ICU nurses look short (110 against about 130 to 150). There are no charge nurses. ED ambulance arrivals and
  discharges home are about 5 to 7% high.
- **electric-distribution-utility. Applied 2026-11-24; see the status note under the utility heading below.** Locates are contracted out in practice (about 38 FTE of work against 10
  locators). Major events are 0.19 a month, not 0.1, and 5 of 9 were Hydro One supply losses. Meter
  technicians, design technologists and billing analysts are short.
- **oilfield-services-co. Applied 2026-11-24; see the status note under the oilfield heading below.** Cementing units, bulk cement trucks and maintenance shop bays are far short of the
  stated job volume. Field tickets are about 750 a month (one per day of frac work), not 640.

Format limits found in this round, now fixed in format 0.3 and `tools/validate.py`: step `people` for crews,
overlap of steps named in `concurrent_with`, and productive hours by shift pattern in the staffing check.
Workflows written before the fix record crew steps as elapsed time (labour cost too low) or as summed person
time (cycle time too long); their `assumptions` say which.


## general-contractor-co

**Status 2026-11-24.** `tools/sync_map_from_workflows.py` and `tools/fixes_2026_11_24_contractor.py` applied
the reports below. Bird's 2020 annual information form (on Bird's CDN; the bird.ca links return 404) is the
outside check: about 880 salaried and 1,578 hourly employees at 31 December 2019, on $1,376.4 million of revenue.

Applied:

- The sync added the missing role listings (88) and links (37). Triggers that were really inputs
  (`levelled_trade_prices`, trade bids, the surety bond to contract award) are now inputs.
- Site staff are sized at 180 productive hours a month (`productive_hours_per_month`). This covers
  superintendents, assistant superintendents and field engineers, who work 10-hour days and some Saturdays
  in season.
- Nine roles were raised to cover their documented hands-on work at 97% load:
  - superintendents, 120 to 156
  - assistant project managers, 140 to 151
  - schedulers, 12 to 17
  - bid coordinators, 10 to 15
  - prequalification analysts, 5 to 8
  - field engineers, 120 to 122
  - estimators, 55 to 57
  - claims managers, 4 to 6
  - yard truck drivers, 0 to 14 (a new role)
- Foremen go from 90 to 135, one for each crew. The 45 come from the crews' own carpenters, labourers and
  cement finishers, so the hourly workforce is unchanged.
- Employees go from 2,800 to 2,880 (66 salaried, 14 hourly).
- Volumes now match the workflows:
  - RFIs: 2,200 a month
  - liens and adjudications: 5
  - holdback releases: 16
  - prequalifications: 110
  - P3 pursuits: 0.2 started a month
  - preconstruction engagements: 1.3 started a month
- Contract award keeps 10 a month. About 5 come from bids and proposals; the rest are recorded as negotiated
  repeat work and master service agreement work orders.
- Link fixes:
  - The lift plan link to the Ministry of Labour is removed.
  - The closeout now sends the consultant an application for substantial performance, not the certificate.
- The prompt-payment sentence is limited to Ontario contracts procured after 1 October 2019.

Still open:

- The salaried/hourly split. Bird's total (2,458 at the end of 2019) scales to about 2,680 at this company's
  revenue, near the file's 2,880. But Bird was about 36% salaried, and the file is about half. Bird's hourly
  count includes industrial self-perform trades that this file does not model.
- Superintendent time in daily site coordination. It averages about 4.7 hours per project-day across large and
  small jobs. If small jobs need much less, the 156 superintendents overstate.
- Roles with little documented work were not cut, because 44 of 81 processes have no workflow. Examples:
  precon managers (12 for about 4 FTE), VDC specialists and financial analysts.
- Some roles are tight once other work is counted:
  - AP clerks: supplier invoices are undocumented.
  - Safety coordinators: training and orientation are undocumented.
- Month-end close is still triggered by journal entries, the convention every file uses, because the format
  has no calendar trigger.
- The `hse-incident-management` volume is unchecked.

### Batch gc-01: bd-opportunity-pipeline, bd-stipulated-bid, bd-trade-tendering, bd-contract-award

- **Awards don't add up:** `bd-contract-award` and the `project-starts` driver show 10 awards a month. But 22 stipulated bids a month at 6:1 to 10:1 (the simulation gives a 14% low-bidder share) yield about 3 wins. Adding 5 proposals at 2:1 to 4:1 gives about 5 a month. Reaching 10 needs either about 45 stipulated bids a month or much more negotiated or repeat work.
- **Inputs listed as triggers:** `levelled_trade_prices` triggers `bd-stipulated-bid` (and `bd-p3-pursuit` and `bd-preconstruction-services`), but it doesn't start a case. Likewise, `subcontractor` and `supplier` `trade_bid` are listed as triggers of `bd-trade-tendering`. I treated all of these as inputs.
- **Roles missing from the process lists:**
  - `bd-opportunity-pipeline`: `bid-coordinator`, `treasury-manager`.
  - `bd-stipulated-bid`: `treasury-manager`, `spe-director`.
  - `bd-trade-tendering`: `prequal-analyst`.
  - `bd-contract-award`: `bd-manager`, `estimator`, `coo`, `treasury-manager`, `risk-insurance-manager`, `assistant-pm`.
- **Headcounts look tight:**
  - The work implies about 13 FTE of bid coordinators across three processes, against 10 in the organisation file. The trade file assumes estimators absorb some of it.
  - About 37 of the 55 estimators are taken by stipulated bids and trade tendering alone, leaving about 18 for CM proposals, preconstruction, P3 and the cost database.
- **Missing link:** `bd-contract-award` produces nothing to `p3-project-co`, though it is triggered by P3 award notices.

### Batch gc-02: bd-cm-proposal, bd-p3-pursuit, bd-preconstruction-services, scm-subcontractor-prequal

- **`bd-p3-pursuit` and `bd-preconstruction-services`:** the units "pursuit-month" and "project-month" don't fit a step-by-step workflow. I documented one whole pursuit (0.08–0.2–0.33 started per month) and one whole engagement (0.8–1.3–2 per month). These convert to the file's volumes.
- **Triggers:** `levelled_trade_prices` from `bd-trade-tendering` should be an input to both processes, not a trigger.
- **Missing links:** the P3 and CM entries both produce a `bond_request` for `fin-surety-bonding`. The P3 pursuit also sends an RFQ `prequal_submission` to `p3-project-co`, but `bd-prequalification` only sends these to `public-owner`.
- **Missing roles:**
  - `bd-cm-proposal` lacks `estimator`, `chief-estimator`, `scheduler`, `project-manager`, `operations-manager`, `contracts-counsel` and `treasury-manager`.
  - `bd-p3-pursuit` lacks `proposal-coordinator`, `chief-estimator`, `scheduler` and `treasury-manager`.
  - `bd-preconstruction-services` lacks `project-manager`, `superintendent`, `chief-estimator` and `operations-manager`.
  - `scm-subcontractor-prequal` lacks `risk-insurance-manager` and `treasury-manager`.
- **`scm-subcontractor-prequal` volume:** 40–90 a month looks like new firms only. Adding annual renewals gives about 110 (70–160), and I used that.
- **`prequal-analyst` headcount:** at that volume the work needs about 4.75 FTE. Five people is too few, because the same analysts also run `scm-vendor-master`.
- **`precon-manager` headcount:** 12 looks high. Precon services use only about 2.2 FTE (tier C estimate).


### Batch gc-03: ops-project-startup, scm-subcontract-buyout, hse-site-safety-plan, ops-schedule-management

- **Roles missing from the `process_map` entries** (all exist as org roles):
  - `ops-project-startup`: `regional-vp` and `assistant-pm`.
  - `scm-subcontract-buyout`: `prequal-analyst`, `operations-manager` (award approval) and `contracts-counsel`.
  - `ops-schedule-management`: `assistant-pm` and `field-engineer`.
- **Missing links:**
  - Startup should produce `wsib_clearance` and `insurance_certificate` to the owner; CCDC 2 GC 10.4.1 and GC 11.1 require them before work starts.
  - Buyout should produce `subcontract` to `ops-submittals`, and `trade_tender` to `bd-trade-tendering` when a package is re-tendered.
  - The safety plan should produce `site_safety_plan` to `subcontractor` and `ops-site-mobilization`.
  - The schedule should go to `private-owner` as well, and the accepted baseline to `ops-progress-draw` (CCDC 2 GC 3.4.1 requires it before the first payment application).
- **Headcount:** 12 schedulers is tight. If schedulers updated every project, the step times imply about 14 FTE, so I modelled 45% of updates (smaller jobs) as done by the assistant project manager. Subcontract administrators come to about 17 of 22 FTE on buyout alone; this is tight, but no change is needed.
- **Volumes:** buyout at 250 a month agrees with 10 starts times 25 packages. `ops-schedule-management` should also take about 10 baselines a month from `ops-project-startup`, which I modelled as a 4.5% trigger share.

### Batch gc-04: ops-site-coordination, ops-rfi, ops-submittals, ops-deficiency-closeout

- **`ops-rfi` volume is too high.** Navigant reports 17.2 RFIs per $1M of construction cost on $5M–50M projects. At about $1.5B of revenue that is about 2,150 a month, against the file's 3,300. I used 1,700 / 2,200 / 3,000.
- **`ops-submittals`:**
  - Its role list leaves out `superintendent`, who runs mock-up reviews.
  - `supplier` should also be a trigger, for rebar shop drawings and mix designs on self-performed work.
  - It is missing a link to `ops-change-order`, for review comments that add scope.
- **`ops-deficiency-closeout`:**
  - It is missing handover links to `p3-project-co` and an occupancy `inspection_request` to `municipality`.
  - The entry says it produces `substantial_performance_cert` to `consultant`, but the consultant issues that certificate. The contractor sends the application.
- **`ops-rfi` produces:** it lacks `rfi_response` to `subcontractor`.
- **Staffing:** headcounts are tight for the ops roles. In my files, superintendents spend about 86 of 120 FTE on these four processes alone, and field engineers about 98 of 120.

Ontario statutes and most Canadian specification PDFs could not be opened, so legal rules are cited from law-firm and contract summaries at tier B.

### Batch gc-05: ops-change-order, ops-subtrade-change, legal-claims-disputes, legal-lien-adjudication

- **`legal-lien-adjudication` volume (4-8-14 a month) looks too high.** Only 50 and 121 adjudications were started in all of Ontario in fiscal 2021 and 2022, about 16 and 39 of them commercial, public or industrial. I used 3-5-9 a month, mostly liens. The entry also leaves out:
  - roles `project-accountant` and `treasury-manager`
  - the `adjudication_notice` trigger from `subcontractor`
  - links to `surety` (bond request) and to `legal-claims-disputes` (lien actions).
- **`legal-claims-disputes`** leaves out:
  - roles `contracts-counsel` and `project-accountant`
  - triggers from `ops-subtrade-change` and `subcontractor` (claims from trades)
  - output to `private-owner`.
- **`ops-subtrade-change`** has no trigger from `ops-site-coordination`, although its description mentions site instructions. It also has no output to `legal-claims-disputes` for disputed trade extras. Its roles leave out `superintendent` and `operations-manager`.
- **`ops-change-order`** roles leave out `superintendent`, `scheduler` and `project-accountant`. It has no link to `p3-project-co`.
- I found nothing wrong with the headcounts.

### Batch gc-06: ops-progress-draw, ops-monthly-cost-forecast, fin-owner-receivables, fin-holdback-release

- **`fin-holdback-release` volume:** 15/25/40 is too high. About 10 projects reach substantial performance each month (`ops-deficiency-closeout` runs 7-14), so I used 10/16/24, counting early trade releases and phased releases as separate cases. Its `triggered_by` list also misses early subcontract-completion releases. It produces holdback invoices only to `public-owner`, when they should also go to `private-owner`, `p3-project-co` and `fin-owner-receivables`. It is missing two roles: `finance-manager` (approves the payment run) and `contracts-counsel` (vacates liens).
- **`ops-progress-draw`:** missing `superintendent` (walks the site for percent complete) and `operations-manager` (signs the statutory declaration). Also missing inputs: `schedule` and `wsib_clearance` from `wcb`.
- **`ops-monthly-cost-forecast`:** missing `superintendent` (measures self-performed work), `regional-vp` (approves margin fades), `finance-manager` and `financial-analyst` (loss provisions). Also missing inputs: `equipment_charges` and `schedule`.
- **`fin-owner-receivables`:** missing `owner_payment` from `p3-project-co`, the `holdback_invoice` trigger, and the `project-accountant` role (holdback ledger). Its process uses only about 3.9 FTE, so the 10 billing specialists must also carry other work.


### Batch gc-07: spe-concrete-placement, spe-crew-planning, spe-equipment-dispatch, spe-crane-operations

- **No truck driver role**, although it lists 14 boom trucks. I added `truck-driver` (NOC 73300, 12 FTE) with `not_in_org_file`.
- **`spe-equipment-dispatch`:** the roles leave out `superintendent` and `mechanic`. `equipment-operator` runs machines on site rather than dispatching them.
- **`spe-crane-operations`:**
  - The roles leave out `mechanic`, `labourer` (who acts as signaller) and `yard-coordinator`.
  - The link sending `lift_plan` to `ministry-labour` is not supported: I found no filing rule, and engineer reports stay on the project.
  - It is missing a `permit_application` link to `municipality` and a `rental_order` link to `equipment-rental`.
- **`spe-crew-planning`:** the roles leave out `operations-manager` and `yard-coordinator`.
- **`spe-concrete-placement`:** `test_report` from `testing-agency` is not listed as an input. Rebar is usually placed by a subcontractor, which the map does not show.
- **External parties:** there is no party for specialty formwork or crane engineers.
- **Volumes:** 600 pours a month uses about three quarters of the concrete division's hours, so that number holds.

### Batch gc-08: spe-field-timekeeping, fin-union-payroll, hr-hire-trades, fin-month-end-close

- `spe-field-timekeeping`: `project-controls` and `project-accountant` are missing; they review and reclassify miscoded hours.
- `fin-union-payroll`:
  - `union_remittance` and the WSIB payment are monthly (by the 15th of the next month in the agreement I read), not weekly. Only the month's last run produces them.
  - `labour-relations-manager`, `treasury-manager` and `foreman` (who hands out pay on site) are missing.
- `hr-hire-trades`: `recruiter`, `safety-trainer` and `foreman` are missing. Recalls overlap with `hr-layoff-recall`, so I excluded them.
- `fin-month-end-close`:
  - The close starts when the month ends, not when journal entries arrive; the entries are inputs.
  - `cfo`, `regional-vp`, `project-manager`, `ap-clerk` and `treasury-manager` are missing.
- `payroll-specialist` headcount of 10 is consistent: about 2 FTE on the hourly run and 2.8 on timecard entry.

### Batch gc-09: hse-daily-hazard, hse-site-inspection, hse-incident-management, fin-sub-invoice-payment, fin-surety-bonding

- **Roles missing from the process map entries:**
  - `hse-daily-hazard`: no superintendent, though superintendents sign work permits; no safety-manager.
  - `hse-site-inspection`: no worker member of the safety committee. I used carpenter.
  - `hse-incident-management`: no foreman or environmental-specialist, and no link to environment-regulator for spills.
  - `fin-sub-invoice-payment`: no assistant-pm (logs subcontractors' draft bills) or finance-manager (approves payment runs).
  - `fin-surety-bonding`: no cfo (signs and seals bonds) or bid-coordinator, and no output of final bonds to `bd-contract-award`.
- **Foreman headcount:** 90 foremen, but the resources list 135 crews (75 concrete, 25 finishing, 35 general).
- **ap-clerk (18):** subcontractor invoices alone need about 11 FTE, which leaves about 7 for 6,500 supplier invoices a month. That is tight.
- **safety-coordinator (45):** these three processes alone need about 33 FTE, before training, orientation and environmental work.
- **`fin-sub-invoice-payment` description:** "pay within 7 days of the owner's payment" applies only to Ontario contracts procured after 1 October 2019. Older contracts and the West and Atlantic regions (about half the work) paid on pay-when-paid terms. I did not check other provinces' laws.
- **`hse-incident-management` volume:** I kept 60–130 incidents a month but could not check it against Bird's published safety statistics (the annual report link returned 404).

## power-generation-co

**Status 2026-11-24.** `tools/sync_map_from_workflows.py` and `tools/fixes_2026_11_24_generator.py` applied
the reports below. The workflows checked most volumes against TransAlta's filings and AESO rules, so the map
now follows them.

Applied:

- The sync added the missing role listings (103), links (49) and nine systems, plus four roles the workflows
  needed: permit coordinator, hydro scheduler, accounting manager, and a budget-holder stand-in.
- Converted-unit operators are set from shift coverage: two sites, five crews, one shift supervisor per site
  per shift. Shift supervisors go from 12 to 10, control room operators from 45 to 25, and field operators
  from 55 to 40. That is 75 in all, against the 65 to 75 the gen-04 author estimated, and it covers the work
  the workflows record.
- The three wind workflows recorded only the lead technician's minutes. Their at-turbine steps now carry
  `people` 2, or 4 on lift days. Documented wind work rises to 35 FTE of 38 technicians.
- Seven roles were raised to cover their documented work at 97% load:
  - maintenance planners, 12 to 20
  - buyers, 12 to 14
  - crew leads, 5 to 7
  - hydro supervisors, 6 to 7
  - maintenance supervisors, 8 to 9
  - AP clerks, 9 to 10
  - budget holders, 1 to 2
- Employees go from 1,300 to 1,289. The wind control centre unit now holds its 11 listed people.
- Volumes and units of work follow the workflows:
  - major outages: 0.8 a month, planned and executed
  - capital projects: 4 started a month, counted per project
  - coal-to-gas conversions: 0.07 a month, counted per project
  - routine work orders: 1,400
  - work permits: 1,250
  - hedge trades: 120, no longer driven by all desk trades
  - reserve trading sessions: 21
  - emissions reports: 1.8
- Surges were copied from the workflows: maintenance, purchasing and stores at 1.4 to 1.5, and 12 that the map
  lacked.
- Reporting lines: accountants and AP clerks report to the new accounting managers, and internal audit reports
  to the CFO and the audit committee. Hydro technicians are on call after hours.
- Other fixes:
  - The per-shift job requisition link is gone.
  - The wind capacity note says that 630 MW applies only from November 2021.

Still open:

- Maintenance planners. The workflow's planning steps need 20, but the gen-05 author notes that 1 planner per 5
  crafts is already far above the recommended 1:20 to 1:30. Either the planning steps or the headcount is off.
- Declared FTE. `gas-operate-units` declares the whole operating crew (66 people), so the summed declared FTE
  for operators exceed headcount. The simulated work fits.
- Unverified volumes: forced outages (12 a month), restatements (600) and dispatches (3,000).
- Roles with little documented work were not cut, because 43 of 81 processes have no workflow. Examples:
  cogeneration operators, mine staff and most of finance.
- No external party for the TIER third-party verifier or a pension plan administrator.

### Batch gen-01: mkt-submit-energy-offers, mkt-restate-offers, mkt-respond-dispatch, mkt-offer-ancillary

- **`mkt-offer-ancillary`:**
  - Reserve auctions run on weekdays only, with multi-day buying on Fridays and before holidays, so it is about 21 sessions a month, not 28 to 31.
  - Missing roles: `realtime_lead`, `hydro_control_operator`, `roc_operator`.
  - Missing output: `ancillary_award` to `mkt-submit-energy-offers`, because awards close around 10:00 and the energy offers must be changed before the 12:00 deadline.
  - Missing inputs: `water_schedule` and `price_forecast`.
- **`mkt-submit-energy-offers`:**
  - Missing roles: `hydro_control_operator` and `gas_buyer`.
  - Missing input: `ancillary_award`.
  - The listed plants (`converted_gas_unit`, `hydro_plant`, `wind_farm`) are the assets being offered; preparing an offer does not tie them up.
- **`mkt-restate-offers`:**
  - Missing roles: `realtime_lead` (daily timeliness review), `compliance_officer` (self-reports), `gas_buyer`.
  - There is no business object for a self-report to the MSA, so I used `inquiry_response`.
- **`mkt-respond-dispatch`:**
  - `gas-start-stop-units` / `unit_status` is an input, not a trigger.
  - Missing output: `availability_change` to `mkt-restate-offers`. Rule 203.4 requires a restatement when a deviation lasts 20 minutes or more.
- **Systems missing:** the AESO dispatch system (ADaMS), the Watt-Ex reserve trading platform, and recorded phone lines. I added all three in the workflow files.
- **Volumes (600 restatements and 3,000 dispatches a month):** still unverified estimates.

### Batch gen-02: mkt-execute-hedges, mkt-procure-gas, fin-commodity-risk, mkt-forecast-generation

- **`mkt-execute-hedges` volume:** it says 400–1,500 trades a month, but that driver (`dd_trades`) counts every trade on the desk. The 2022 Alberta hedges in the MD&A (6,278 GWh of power, 50 million GJ of gas) support about 60–250 hedge trades a month.
- **Roles missing from the process entries:**
  - `mkt-execute-hedges`: `portfolio_optimizer`, `risk_analyst`, `credit_analyst`, `risk_manager`, `exec_officer`, `settlement_analyst`.
  - `fin-commodity-risk`: `term_trader`, `director_trading`, `exec_officer`. The MD&A says the CFO chairs the monthly Commodity Risk and Compliance Committee.
  - `mkt-procure-gas`: `portfolio_optimizer`, `shift_supervisor_gas`, `realtime_trader`.
  - `mkt-forecast-generation`: `realtime_trader`, `realtime_lead`, `shift_supervisor_gas`, `roc_operator`, `hydro_control_operator`.
- **Links missing from the process entries:**
  - `mkt-execute-hedges` is also started by `price_forecast` (from `mkt-market-analysis`) and `customer_contract` (from `mkt-originate-customer-contracts`).
  - `mkt-procure-gas` needs `dispatch_instruction` and `unit_status` as inputs, and its exchange gas buys should go to `mkt-settle-trades`.
  - `fin-commodity-risk` needs `exchange_statement` from `energy_exchange` as an input.
  - `mkt-forecast-generation` needs `price_forecast` and `unit_status` (from `wnd-monitor-fleet`) as inputs, and should send `availability_change` to `mkt-restate-offers`.
- **Gas plants as resources:** `mkt-procure-gas` lists the gas plants as resources, but the process does not hold them, so no step uses them.

### Batch gen-03: mkt-settle-aeso, mkt-settle-trades, mkt-originate-customer-contracts, hse-market-compliance

- **mkt-settle-aeso:** `treasury_analyst` is missing (treasury releases the AESO wire). Physical trades from `mkt-execute-hedges` should be an input, because bilateral trades settle through net settlement instructions. The 8–14 statements a month fits the evidence: four TransAlta pool participant entities, each with a preliminary and a final statement.
- **mkt-settle-trades:** `term_trader` (resolves confirmation breaks) and `treasury_analyst` are missing. It also needs `credit_limits` as an input and a `payment_request` link to `fin-treasury`.
- **mkt-originate-customer-contracts:** `credit_analyst`, `risk_analyst`, `lawyer` and `exec_officer` are missing. `reviewed_contract` returns inside a case rather than starting one, so I gave it share 0.
- **hse-market-compliance:** `director_hse` (signs off submissions) and `cyber_analyst` (reliability standard evidence gaps) are missing. Offer records from `mkt-submit-energy-offers` and `mkt-restate-offers` should be triggers, not standing inputs, since 91% of matters are self-reported. AESO referrals come in through the MSA. Penalties need a `payment_request` link to `fin-pay-suppliers`.
- **Headcounts:** none are wrong. The two settlement files model 5.6 of the 9 settlement analysts, which leaves room for customer billing.

### Batch gen-04: gas-operate-units, gas-start-stop-units, gas-respond-forced-outage, eng-report-outages-aeso

- **Headcounts:** the converted-unit operators (12 shift supervisors, 45 control room operators, 55 field operators, 112 in all) look like coal-era staffing. About 6 to 7 people per shift at each of two sites on a five-crew rotation needs about 65 to 75.
- **`gas-respond-forced-outage` volume:** 12 a month means about 4 trips or derates per unit per month. That is high and unverified.
- **`gas-respond-forced-outage` links:** `realtime_trader` is missing; under the rules the trading desk phones the AESO and restates the unit's capability. Site trades (`millwright`, `ie_technician`), `crew_lead` and `plant_manager_gas` are also missing. Failed starts send a `unit_trip` from `gas-start-stop-units` that the map does not show.
- **`gas-start-stop-units`:** `gas_buyer`, `chemistry_tech` and `realtime_trader` are missing from its roles.
- **`eng-report-outages-aeso`:**
  - The rule covers every generating asset of 5 MW or more, wind included. So `hyd-maintain-plants`, `wnd-scheduled-service` and `gas-routine-maintenance` should also send it outage plans.
  - The rule requires a monthly submission of all planned outages for the next 24 months.
  - Its roles lack `maintenance_planner`, `portfolio_optimizer`, `realtime_trader` and `compliance_officer`.
- **`gas-operate-units`:** listing `job_requisition` as a per-shift output is wrong. `realtime_trader` should be a role.
- **Converted units:** their running cost per hour should not be charged while a unit is down after a trip. Its available hours already exclude outage time, so I left the unit unoccupied during repairs.


### Batch gen-05: gas-routine-maintenance, gas-issue-work-permits, scm-purchase-materials, scm-manage-stores

- **`gas-routine-maintenance`:**
  - 2,000 work orders a month needs about 75 to 90 craft FTE, but the file has 60 crafts (34 millwrights, 26 technicians), who also work outages. I used 1,400.
  - Planned maintenance from `eng-reliability-analysis` starts about half of all cases but is listed only as an input.
  - `work_permit`, `issued_parts` and `crew_assignment` arrive partway through a case, so they are not triggers.
  - 12 planners for 60 crafts is 1:5; Palmer recommends 1:20 to 1:30.
- **`gas-issue-work-permits`:**
  - `control_room_operator_gas` and `safety_advisor` take part but are not listed.
  - There is no permit coordinator role. TransAlta's careers site shows the job title at Wabamun, but the page shows nothing else and dates from after 2022, so I added the role as tier B.
  - About 1,250 permits a month, not 1,600, fits 1,400 work orders.
- **`scm-purchase-materials`:**
  - Requisition approvers and requesters (`maintenance_supervisor`, `maintenance_planner`) are missing from the roles.
  - `hyd-maintain-plants` and `wnd-troubleshoot-turbines` also buy directly, but have no `triggered_by` link.
- **`scm-manage-stores`:**
  - `plant_engineer` (inspects critical spares) and `buyer` (handles receiving discrepancies) take part but are not listed.
  - The purchase order from `scm-purchase-materials` is a standing input, not a trigger.
  - Mine issues stop after 2021.
- **Surge multipliers:** a mode of 1.8 is too high for maintenance, purchasing and stores, because major-outage work belongs to `eng-execute-major-outage`. I used 1.4 to 1.5.

### Batch gen-06: wnd-monitor-fleet, wnd-troubleshoot-turbines, wnd-scheduled-service, wnd-main-component-exchange

- **`wnd-roc` headcount:** the unit says 10 people, but its roles add up to 11 (8 `roc_operator` plus 3 `performance_analyst`).
- **`wnd-monitor-fleet`:** no trigger is listed. I used the process itself with `unit_trip`, because a fault stop starts inside the fleet. A manufacturer's monitoring centre reports 80% of alarms resolved remotely, against the file's note that about 40% need a site visit. I modelled about 33% dispatched.
- **`wnd-scheduled-service`:** no trigger is listed. I used `maintenance_strategy` from `eng-reliability-analysis`. The file also lacks two outputs I added: a `work_request` for defects found, and a `timesheet`.
- **`wnd-troubleshoot-turbines`:** `issued_parts` is a standing input, not a trigger. `roc_operator` (the remote restart) is missing from the roles.
- **`wnd-main-component-exchange`:** it should also be triggered by scheduled service and by `eng-reliability-analysis` (condition monitoring). It should produce `work_order_history`, and `roc_operator` is missing. Published lead times of 3 to 6 months put typical downtime at months rather than weeks.
- **Wind technician headcount:** the four workflows use about 37 of the 38 technicians (22 troubleshooting, 13 scheduled service, 2.2 exchanges). That leaves almost nothing for training or on-call rest, so 38 is probably low.
- **Wind capacity:** Windrise (206 MW) only started in November 2021, so for most of 2019 to 2021 the fleet was about 420 MW net, not 630 MW.
- **Permits:** `gas-issue-work-permits` covers gas only, and there is no permit process linked to wind work.

### Batch gen-07: eng-plan-major-outages, eng-execute-major-outage, eng-reliability-analysis, eng-manage-capital-projects

- **eng-plan-major-outages:** the volume of 1/4/10 a month is too high for detailed thermal outage planning; about 0.5/0.8/1.5 fits. TransAlta's 2019 MD&A reports two planned major outages on its Alberta coal units in 2019, one in 2018 and four in 2017. Four roles that take part are missing: maintenance_planner, plant_engineer, safety_advisor and shift_supervisor_gas. The produces list also lacks a crew_request to eng-dispatch-specialist-crews.
- **eng-execute-major-outage:** 1/3/8 a month is too high for the same reason; 0.5/0.8/1.5 fits. Missing roles: shift_supervisor_gas, control_room_operator_gas, plant_engineer and reliability_engineer. Missing link: the return to service should send an availability_change to mkt-restate-offers.
- **eng-reliability-analysis:**
  - maintenance_planner is missing from the roles.
  - The process produces nothing for hyd-maintain-plants (maintenance_strategy) or scm-manage-stores (spare-part stocking changes).
  - Work order history only appears under inputs, though bad-actor reviews actually start cases.
- **eng-manage-capital-projects:**
  - The unit of work should be one project, not "one active project-month". About 4 starts a month lasting 12 to 18 months gives the file's 40 to 80 active projects.
  - Missing roles: plant_engineer, safety_advisor, accountant and vp_eng.
  - Missing links: a service_order to scm-contractor-management and journal_entries to fin-close-month.

The AESO rule 306.5 and OHS Code Part 15 citations are to pages I opened, but the AESO rule text is the 2023 version. Its revision history shows the planned-outage requirements did not change in 2020 to 2022.

### Batch gen-08: hyd-plan-water-schedule, hyd-operate-plants, hyd-maintain-plants, hyd-dam-safety

- **Missing role:** there is no hydro scheduler. TransAlta's 2026 control-centre operator posting names a Hydro Scheduling function. I added `hydro_scheduler` with `not_in_org_file` in `hyd-plan-water-schedule`.
- **Missing role:** there is no hydro maintenance planner, so I assumed supervisors plan the work in `hyd-maintain-plants`. The gas side has 12 planners.
- **`hyd-dam-safety` trigger:** its `triggered_by` list is empty. I used `aep`/`dam_safety_directive` as the calendar trigger and `hyd-maintain-plants`/`asset_condition_report` for conditions reported from site. It also needs links to `contractors` (`service_order`, for consultant dam safety reviews) and to `hyd-operate-plants` `flow_data` as an input.
- **`hyd-maintain-plants` trigger:** preventive orders, about 62% of volume, have no trigger. `eng-reliability-analysis` sends `maintenance_strategy` to gas and wind but not hydro.
- **`hyd-maintain-plants` roles:** `hydro_control_operator`, which does the isolations, and `crew_lead` are missing from its role list. `issued_parts` should be an input, not a trigger.
- **`hyd-plan-water-schedule` inputs:** `price_forecast` and `outage_schedule` are missing, and so is the province's power to set Ghost Reservoir levels from May 16 to July 7 under the Alberta–TransAlta agreement.
- **`hydro_tech` shift pattern:** it acts `on_call` after hours in operations, not `extended_hours`.
- **Volumes:** the work-order volume (550 a month) and the dam safety task volume (8 a month) are still tier C. Both are consistent with headcount.

### Batch gen-09: etr-convert-coal-units, hse-manage-incidents, hse-report-emissions-tier

- **`etr-convert-coal-units`:**
  - **Volume:** the unit "project-month" at 1 to 5 a month does not match the evidence. Three wholly owned conversions finished in February, July and December 2021, which is about 0.07 projects a month in 2019 to 2022.
  - **Duration:** "one to two years" fits only the notice-to-proceed-to-completion stretch (about 19+ months). From application in summer 2018 to completion took 31 to 36 months.
  - **Missing roles:** `regulatory_advisor`, `contract_specialist`, `outage_manager`, `shift_supervisor_gas`, `crew_lead`, `ie_technician`.
  - **Missing links:** `oem_providers`, `contractors`, `absa`, `auc`, `aep`.
  - **Missing resources:** `specialist_crew`, `turbine_hall_crane`, `mobile_crane`.
  - **Wrong trigger:** `regulatory_approval` arrives mid-project, so it is an input, not a trigger.
- **`hse-manage-incidents`:**
  - **Missing roles:** `hr_partner` (WCB claims and modified work) and `plant_manager_gas`. Night incidents are first handled by shift, hydro, wind and mine supervisors, not by `maintenance_supervisor` (office hours).
  - **Missing link:** `contractors`.
  - **Volume:** the evidence can now be tier B. The modelled company's TRIF was 0.82 on 4.13 million exposure hours in 2021, about 17 recordable injuries a year.
- **`hse-report-emissions-tier`:**
  - **Volume:** a mode of 1 a month is low. The facilities imply about 20 to 24 reports a year (about 1.8 a month), all prepared January to June.
  - **Missing outside party:** the third-party verifier.
  - **Missing systems:** ECCC Single Window and the Alberta credit registry.
  - **Missing roles:** `settlement_analyst`, `term_trader`, `plant_engineer`.
  - **Wrong trigger:** `emission_credits` is an input, not a trigger.

Some sources could not be opened: the TIER verification standard, the 2021 OHS bulletin on potentially serious incidents, and the ABSA and NFPA 85 rules. Steps that rely on them are tier B or C, with a note saying so.

### Batch gen-10: fin-pay-suppliers, fin-close-month, hr-run-payroll

- **`fin-pay-suppliers`:** the roles list is missing:
  - `storekeeper`, for missing goods receipts.
  - `maintenance_supervisor`, who confirms contractor work.
  - Managers who approve invoices; I added `budget_holder` (`not_in_org_file`).
  - `settlement_analyst` and `settlement_manager`, who check gas statements.
  - `controller` and `treasury_analyst`, who approve and release payments.

  The file also has no invoice-scanning system and no bank portal. I kept the volume as it is; I found no evidence to change it.
- **`fin-close-month`:** the roles list is missing `settlement_analyst`, `risk_analyst`, `treasury_analyst`, `fpa_analyst` and `tax_specialist`. There are no accounting managers, so about 48 people report straight to `controller`. That count includes `internal_auditor`, which normally reports to the audit committee to stay independent. Emissions data and gas nominations feed the close but are not linked as inputs.
- **`hr-run-payroll`:** the roles list is missing front-line supervisors (I used `shift_supervisor_gas` to stand for them), `treasury_analyst` and `accountant`. `produces` leaves out union dues to `unions`, and there is no external party for a pension plan administrator. `triggered_by` leaves out shift timesheets from `hyd-operate-plants` and the real-time trading desk. The IBEW Local 254 agreement for 2017–19 was ratified in January 2018, a year late, which supports the retroactive-pay rework in the process description.

## mining-operator-co

**Status, 2026-11-24.** Two scripts applied most of the reports below. Each fact was re-read in the 2022
technical report (Tables 16-9 and 16-10, sections 11, 16.4, 17, 18 and 20) or the 2016 report before it was
written.

- `tools/sync_map_from_workflows.py` copied what the workflows use into the process map: 132 role listings, 67
  links, 34 standing inputs, 3 systems, the roles `loading-pocket-operator`, `mine-clerk` and `sample-driver`, and
  12 resources the workflows had marked `not_in_org_file` (shotcrete rig, refinery, sample shuttle, forklifts,
  pickups, ambulance and others).
- `tools/fixes_2026_11_24_mining.py` corrected the facts:
  - The mill flowsheet is now gravity, leach and Merrill-Crowe. Tailings are filtered and stacked dry, the mill is
    16.6 km from the portal with a surface ore haul, and the shaft hoists to a dump at the 70 m level.
  - The assay office is in Wawa, uncertified, with a daily shuttle. The refiner is the Royal Canadian Mint, and gold
    is sold at spot only.
  - Fleet counts follow Table 16-9 and underground labour follows Table 16-10. Mill crews work 7 on, 7 off.
  - Grade control is 65 faces a month, assay batches 300 and smelts 6. Effluent sampling is 9 a month and the budget
    0.083. The annual shutdown lasts one to three weeks, and surface rig hours went up.
  - Four ids were renamed, because they named a technology the mill does not use:
    - `mill-elution-refining` became `mill-gold-room-refining`, and its workflow file was renamed to match.
    - `loaded_carbon` became `gold_concentrate`.
    - `tailings_slurry` became `filtered_tailings`.
    - `elution-circuit` became `refinery`.
- Contractor miners are recorded with a new optional role field, `contractor_headcount` (see SCHEMA.md). In 2022
  the contractor supplied 36 of the 147 people underground. Role headcounts include them, so the staffing check sees
  everyone who does the work. The employee count leaves them out. It is now 266, down from 300.

Still open:
- Buyers: there are 2, against about 3.7 FTE of purchase-order work.
- Payables: about 1,600 invoices a month may be high; the report suggests 1,000 to 1,200.
- Gold room operators: the FTE they need is not checked.
- Mill running cost: C$900 to C$1,500 an hour may be high.
- Mechanised bolters: Table 16-9 lists none.
- Surface ore haul: the report does not say who does it or how many trucks are used.
- Underground rotation: still assumed to be 14 on, 14 off.
- Mining method: captive sub-levels reached by Alimak raises.
- Neighbouring mine's samples: the assay office's work for it is mentioned in the text but not counted in volume.

### Batch mine-01: mine-shift-control, mine-dev-drill-blast, mine-ground-support, mine-stope-drilling

- **`mine-shift-control`:**
  - `triggered_by` is empty; I used `mine_plan` from `ts-short-range-plan`.
  - There is no `shift_lineup` link to `mine-ground-support`.
  - No role keys shift reports into spreadsheets; I added `mine-clerk` (not in the org file).
  - `maint-supervisor` takes part in practice but is not listed.
- **`mine-dev-drill-blast`:**
  - The roles list lacks `surveyor`, `mine-geologist`, `ug-services-worker` and `bolter-operator`.
  - The `survey_data` input from `ts-survey` is missing.
- **`mine-ground-support`:**
  - Rehab work (about 13% of cases) has no trigger; it should come from `ts-geotech` (`geotech_assessment`).
  - The `stores_issue` input from `site-warehouse` is missing.
  - The roles list lacks `geotech-engineer` and `ug-services-worker`.
  - There is no shotcrete sprayer resource; I added `shotcrete-rig`.
  - The three bolters work out at about 75% utilised, which explains the queues.
- **`mine-stope-drilling`:**
  - The roles list lacks `surveyor`, `mine-engineer` and `ug-services-worker`.
  - The inputs `survey_data` and `installed_services` are missing.
  - There is no as-drilled feedback to `ts-stope-design` and no `work_request` to `mnt-breakdown-repair`.
- **Headcounts and volumes:** these agree with the evidence I found.

### Batch mine-02: mine-mucking-haulage, mine-stope-blasting, mine-hoisting, ts-survey

- **`mine-hoisting` description:** the shaft lifts ore from the pocket below the 460 m level to a dump at the 70 m level, not to bins on surface. Trucks then haul it out the portal, and it goes 16.6 km by road to the mill. Most people enter by ramp, and the cage holds six.
- **`mine-hoisting` roles:**
  - The loading pocket is loaded by hand, but there is no pocket operator or cagetender role. I added `loading-pocket-operator`.
  - Reg. 854 s. 9(3) limits anyone to 8 hours at the hoist controls in 24, so each 12-hour shift needs a relief operator.
- **`lhd-operator` / `ug-truck-driver`:** the 2022 report lists 8 LHD operators and 24 truck operators, against 20 and 12 in the file.
- **`lhd` / `ug-truck` resources:** the report lists 19 LHDs (8 of them small 2-yard units) and five 30-tonne trucks, against 9 and 6.
- **`mine-stope-blasting` roles:** the file lists only `prod-miner` and `ug-shift-supervisor`. The work also needs `explosives-handler` and `mine-engineer`. Holes are charged with stick emulsion.
- **`mine-mucking-haulage`:** development rounds are mucked by `dev-miner`. Broken ore and rock are standing inputs, not what starts a case. Two outputs are missing: `face_sample` to `mill-assay-lab` and `work_request` to `mnt-breakdown-repair`.
- **`ts-survey`:**
  - Month-end measurement has no trigger. I added `ts-short-range-plan`.
  - `ug-shift-supervisor` confirms stopes are ready to scan.
  - Four surveyors work at close to full capacity.
- **Profile:** the 2016 report says mill crews worked 7 days on and 7 off, not 14 and 14.

### Batch mine-03: ts-short-range-plan, ts-stope-design, ts-grade-control, ts-reconciliation

- **Grade control volume too high (`ts-grade-control`).** The evidence gives about 40–100 faces a month (mode 65), not 130. Only ore headings and drifts on the vein are chip sampled, once per 3–4 m round. Waste capital development is under survey control and is not sampled.
- **Assay lab location (`mill-lab`, resource `assay-lab`).** The company lab is in Wawa, reached by a daily shuttle, not at the site.
- **Mill location.** The mill is not next to the shaft. Ore is trucked 16.6 km from a pad at the mine portal, so there are two stockpiles. The workflow adds a surface pickup truck, marked `not_in_org_file`.
- **Geology headcount (`techserv-geo`).** The report lists 10 mine geology staff, not 12. Mine engineering at 9 matches.
- **Missing roles:**
  - `ts-short-range-plan`: mine-geologist, mine-captain, maint-planner, geotech-engineer, gm.
  - `ts-stope-design`: surveyor, ts-manager.
  - `ts-grade-control`: lhd-operator (the muck samplers), ug-shift-supervisor, assay-technician, assay-supervisor.
  - `ts-reconciliation`: mine-geologist, mine-captain, surveyor.
- **Missing links:**
  - Into reconciliation: grade_control_model, mine_plan and hoist_log.
  - Into the short-range plan: grade_control_model, work_schedule and shift_report.
- **Mining method.** The report describes captive sub-levels reached by Alimak raises, with jacklegs, in transition to mechanised access. The organisation file's mechanised bolter crew may be overstated.

Every cited source was opened. The Python scripts that build the four files are in `kit/_mine03_build/` and the downloaded reports are in `kit/_mine03_dl/`.

### Batch mine-04: ts-lom-planning, ts-geotech, ts-reserve-estimate, expl-drilling

- **`ts-geotech`:**
  - One geotechnical engineer (`geotech-engineer`) on a 14-on/14-off rotation. The work needs about 1.8 FTE (about 235 hours a month), so a second engineer or technologist on the opposite rotation is likely.
  - Missing roles: `mine-engineer`, `ts-manager`, `trainer`.
  - Missing triggers: shift reports and incident reports from `mine-shift-control`, and the yearly consultant review from `consultants`.
  - Missing outputs: `investigation_report` to `hse-incident-mgmt`, `ground_control_standard` to `hse-training`.
- **`ts-lom-planning`:**
  - Missing roles: `mine-superintendent`, `maint-superintendent`, `mill-superintendent`, `site-controller`.
  - Missing inputs: `site_forecast`, `reconciliation_report`, `geotech_assessment`.
- **`ts-reserve-estimate`:**
  - `triggered_by` is empty.
  - Missing inputs: `exploration_results` from `expl-data`, `survey_data` from `ts-survey`, `cost_report`.
  - Missing output: to `corp-investor-relations`.
  - Missing roles: `surveyor`, `coo`, `general-counsel`.
  - Wesdome used independent consultants as qualified persons to do the estimate under company supervision, so the process should show that outside role.
- **`expl-drilling`:**
  - The trigger "`drilling-contractor` → `drill_core`" is backwards; core is an output of the process.
  - `surface-drill` (3 rigs at 450 hours a month) can do about 7 holes a month, not 15. In 2021 Wesdome had 3 surface rigs at the mine for 54,000 m, plus separate rigs for 42,000 m in Quebec. Closer to 5–6 rigs, or about 600 available hours each, fits the stated volume.
  - Missing roles: `gis-database`, `core-technician`, `community-relations`.
  - Missing outputs: `survey_data` to `expl-data`, `consultation_record` to `hse-community`.

### Batch mine-05: mill-grind-leach, mill-elution-refining, mill-crushing, mill-tailings

- **`mill-grind-leach`, `mill-elution-refining`:** the mill has no carbon-in-pulp, elution or electrowinning. Gold comes from a gravity concentrator and shaking table (43%) and Merrill-Crowe zinc precipitation (88%), 97% overall. The refinery burns press socks and smelts table concentrate. The process name, the `loaded_carbon` object, `elution-circuit` and the `mill-plant` name are wrong. Business objects for precipitate and table concentrate are missing, so I kept the `loaded_carbon` id as a stand-in. I added a `refinery` resource marked `not_in_org_file`.
- **`mill-elution-refining` volume:** socks are changed every two weeks. With weekly table smelts that is about 4 to 8 batches a month, not 6 to 10. A link to `mill-assay-lab` for bar samples is also missing.
- **`mill-tailings`:** tailings have been filtered and placed by conveyor, trucks and a dozer since 2007, not piped as slurry to spigots. The process omits `env-coordinator`, `mill-shift-supervisor` and the haul crew, and has no links to `ontario-mecp` or `hse-incident-mgmt` for releases.
- **`mill-plant` resource:** mill availability was 80.0% in 2020 and 87.3% in 2021, below the file's 640 to 710 hours a month. Its C$900 to C$1,500 an hour running cost also looks high.
- **Mill location:** the mill is 17 km by road from the mine, not beside the shaft. The truck haul of ore from mine to mill is missing.
- **Mill crews:** 12-hour shifts on seven days in, seven out, not 14/14.
- **Throughput:** 727 tpd in 2021.

The Merrill-Crowe and filtered-tailings design is backed by tier A or B evidence. The tier C estimates are event frequencies, the gold-room operator FTE and who hauls tailings.

### Batch mine-06: mill-met-accounting, mill-assay-lab, mill-dore-shipment, corp-gold-sales

- **`mill-elution-refining`, `mill-grind-leach` and the `elution-circuit` resource:** the Eagle River mill does not use carbon-in-pulp or electrowinning. It recovers gold by gravity and Merrill-Crowe zinc precipitation, and the gold room smelts table concentrate and burned press socks.
- **`mill-assay-lab`:**
  - The lab is the company assay office in Wawa, about 1.5 hours by road from the mine, not a room at the mill. It is not accredited.
  - It also assays Island Gold's production samples. That outside client is missing from the file.
  - A furnace batch holds 28 positions, not about 50, so the load is about 300 batches a month rather than 160.
  - Six technicians and one supervisor is too few. Hands-on time implies about 11 technicians, and the reports mention shift supervisors and an Assay Lab Superintendent. The shift pattern should be `extended_hours`, not `field_rotation`.
  - There is no driver role or vehicle for the daily sample shuttle.
- **`corp-gold-sales`:** there were no gold or currency forward contracts in 2020 or 2021, so sales are spot only. Gold went only to financial institutions. The process also needs `corp-accountant`, `corp-controller` (to match trades separately from the trader) and `mill-superintendent`.
- **`mill-met-accounting`:** add `gm` (approves monthly production). Add two inputs: `shipment_advice` from `mill-dore-shipment` and `stockpile_survey` from `mine-ore-stockpile`.
- **`mill-dore-shipment`:**
  - Add `site-controller`, who records doré in transit.
  - The 2016 report names the Royal Canadian Mint as the refiner.
  - The process name is garbled as "DorÃ©".
- **Mill crews:** they work 12-hour shifts on 7 days in, 7 days out (2016 report).

### Batch mine-07: mnt-mobile-pm, mnt-breakdown-repair, mnt-work-planning, mnt-shutdown

- **Missing roles:**
  - `mnt-mobile-pm`: add `maint-planner`, `warehouse-attendant`, `buyer` and operators (`lhd-operator`).
  - `mnt-breakdown-repair`: add `mill-shift-supervisor`, `warehouse-attendant`, `buyer`, `maint-planner` and `lhd-operator`.
  - `mnt-work-planning`: add `buyer`, `warehouse-attendant` and `mine-captain`.
  - `mnt-shutdown`: add `gm`, `maint-supervisor`, `mill-shift-supervisor`, `hoist-operator`, `safety-coordinator`, `trainer` and `site-admin-assistant`.
- **Missing links:**
  - `mnt-work-planning` lists only `hse-inspections` as a trigger. Work requests also come from `mine-shift-control`, mill operators, PM defects and breakdown follow-ups. It also lacks a `stores_request` to `site-warehouse`.
  - `mnt-breakdown-repair` sends repaired equipment only to the mine. Repaired mill plant also goes back to `mill-grind-leach` or `mill-crushing`.
  - `mnt-shutdown` has no link to `mine-hoisting`, no `shaft-hoist` resource, and no inputs from `site-contractors`.
- **Wrong shutdown description:** `mnt-shutdown` says "one to four days". Eagle River had an extended annual mill shutdown in August 2021 and July 2022, and mill availability was 86% in 2021 against 93.3% planned. I modelled one major shutdown of one to three weeks a year plus short stops. The volume (4–7 a year) is fine.
- **Headcount:** `hd-mechanic` is 22. The 2022 report lists 12 owner mine-maintenance staff and 8 mine electricians.
- **Other facts the 2022 report contradicts:**
  - The mill is 16.6 km by road from the mine portal, not next to the shaft.
  - It recovers gold by Merrill-Crowe, so the `mill-plant` resource should not be described as carbon-in-pulp.
  - There are 3 owner jumbos, not 4.
  - The hoist runs at most about 16 hours a day.

### Batch mine-08: hse-env-monitoring, hse-incident-mgmt, hse-training, site-warehouse

- **`hse-env-monitoring`:** volume should be about 8 to 13 a month, not 4 to 10 (mode 6), because two discharge points are each sampled weekly. Mill effluent leaves continuously at a controlled rate, not in batches. The mine's settling ponds discharge to Lake C7 on their own permit, so `mine-dewatering` should feed this process directly, not only through `mill-water-treatment`. Lab results come back within a case, so they are not a trigger.
- **`hse-incident-mgmt`:** incidents also start in `mill-grind-leach` and `site-contractors`. The process also produces maintenance work requests to `mnt-work-planning` and spill reports to `ontario-mecp`.
- **`hse-training`:** most courses are requested by supervisors in `mine-shift-control`, `mill-grind-leach` and `mnt-work-planning`, not only triggered by new hires. The file has no generic trainee role. The trainers have no shift pattern set.
- **`site-warehouse`:** it also takes requests from `mine-ug-services` and deliveries from `site-fuel`.
- **Missing resources:** the warehouse forklift, the environmental department's truck, the site ambulance and the training room.

### Batch mine-09: site-purchasing, site-ap, site-payroll, site-cost-reporting

- **`site-purchasing`:** 500 POs a month need about 3.7 FTE of buyer time, but there are 2 `buyer` roles. Job postings show buyers also handle expediting, change orders and invoice problems. The approvers `gm` and `coo` and the requisitioner `maint-planner` are missing from the roles list.
- **`site-ap`:**
  - 1,600 invoices a month need about 3.5 FTE, but the 3 `site-accountant` roles also do cost accounting. The note's "three invoices per PO" looks high; 1,000 to 1,200 a month seems more likely.
  - `triggered_by` leaves out invoices from the fuel, reagent and explosives suppliers (purchasing sends them POs), the mining contractor, travel providers, the power utility and the commercial lab.
  - The roles list is missing `gm`, `buyer`, `warehouse-attendant` and `treasury-tax-manager`.
- **`site-payroll`:** Only the mine and mill send timesheets; maintenance (53 hourly staff) has no link. I used `mnt-work-planning` as the nearest maintenance process. The roles list is missing `mill-shift-supervisor`, `maint-supervisor`, `mine-captain`, `hr-coordinator`, `treasury-tax-manager` and `site-accountant`.
- **`site-cost-reporting`:**
  - `triggered_by` is empty; I used the payables ledger from `site-ap` as the trigger.
  - `corp-budget` should send the `annual_budget` in as an input.
  - `corp-controller` is missing from the roles list.
- **Shift patterns:** `buyer`, `supply-manager`, `site-controller`, `site-accountant`, `payroll-admin` and `hr-coordinator` have no shift pattern. I set them to `office_hours` in the workflows.
- **Resources:** There is no site pickup truck for emergency part runs. I added one in purchasing marked `not_in_org_file`.

### Batch mine-10: corp-financial-reporting, corp-budget

- **`corp-financial-reporting` roles**: five listed, but `treasury-tax-manager` (tax provision, gold sales reconciliation), `gm` (operations commentary), `vp-ir` (news release), `general-counsel` (disclosure review) and `ceo` (signs the filing certificate, leads the call) also take part.
- **`corp-financial-reporting` links**: no `news_release` output to `shareholders` or `osc-tsx`. Missing inputs are `production_report` from `mill-met-accounting` and, at year end, `reserve_statement` from `ts-reserve-estimate`.
- **`corp-financial-reporting` evidence**: can be tier A. I opened NI 51-102: 45 days for quarterly statements, 90 days for annual, board or audit committee approval before filing.
- **`corp-budget` roles**: also missing `site-controller`, `mine-superintendent`, `mill-superintendent`, `maint-superintendent`, `vp-exploration`, `hr-director`, `treasury-tax-manager`, `vp-ir` and `general-counsel`.
- **`corp-budget` volume**: `cases_per_month` should be 0.083 (one budget a year). The mode of 0.1 and high of 0.17 imply a second full budget each year.
- **`corp-budget` links**: there is no output for the public guidance (`news_release` to `shareholders` and `osc-tsx`).

## freight-carrier-co

**Status 2026-11-24.** `tools/sync_map_from_workflows.py` and `tools/fixes_2026_11_24_trucking.py` applied
the reports below. The carrier is a composite, so most fixes make the file agree with the work its workflows
record; Old Dominion's 2021 10-K (5,644 P&D drivers, 5,350 dock staff, 12.88 million shipments) is the outside
check.

Applied:

- Drivers are sized on on-duty hours, using a new optional role field `productive_hours_per_month`: 195 for
  P&D drivers, 210 for linehaul drivers. P&D drivers go from 540 to 785 (Old Dominion's ratio gives about 789)
  and linehaul drivers from 240 to 357.
- Owner-operators were counted in truckload while the linehaul workflow also used them. Now 310 haul
  truckload and 70 pull LTL linehaul, recorded as `contractor_headcount` in the linehaul driver role. The total
  is still 380, and none of them are employees.
- 21 roles were raised to cover their documented hands-on work at 97% load. They include:
  - terminal service clerks, 45 to 121
  - terminal dock workers, 230 to 387 (hub and terminal docks together come to 717; Old Dominion's ratio gives about 748)
  - pricing analysts, 10 to 28
  - billing auditors, 10 to 23
  - OS&D clerks, 22 to 39
  - city dispatchers, 70 to 101
  - dock supervisors, 60 to 87
  - load planners, 14 to 25
  - driver managers, 36 to 49

  Employees go from 3,000 to 3,603. P&D trucks go from 560 to 830, and power units total 1,460.
- Driver pay now follows company drivers (a new demand driver), not all employees: 3,250 records a month for
  1,510 drivers paid every two weeks.
- Daily inspection reports and timecards now come from `ltl-pd-dispatch` once per driver-day, in the map and
  in the workflows that receive them.
- Other fixes:
  - Two mid-case triggers were removed: parts deliveries, and customs releases.
  - Owner-operator contracting now runs 50 a month, counting every contract event.
  - The pricing-quote surge is 1.2 to 1.8 (source: FreightWaves).
  - Four workflow surges were copied to the map.
  - Preventive maintenance runs 1,200 a month.
  - The Quebec SAAQ maintenance program is noted in the inspection process.
  - Brokerage is about 3% of revenue.
  - A 24-hour road call desk (5 people) was added.

Still open:

- `driver-recruiter` (14) does about 3 FTE of documented work; the frt-07 author thought 6 to 8 would do.
  Roles with little documented work (`terminal-ops-supervisor`, `technician`, `account-executive`) were not
  cut, because 52 of 89 processes have no workflow yet.
- `frt-ltl-delivery-execution` spreads route-level inspection over its stops while `frt-ltl-pd-dispatch`
  also records the daily inspection, which may double count about 3,000 driver hours a month (about 15
  drivers).
- Pickup shipper waiting is recorded as wait, not hands-on time, so the P&D driver count is a floor.
  Owner-operator linehaul trips use the company driver role in steps, so their cost per trip is low.
- Pricing analysts (28) and billing auditors (23) follow the stated volumes (2,500 quotes and 9,000
  corrections a month). The authors' alternatives were lower volumes, or customer service quoting simple spot
  rates.
- Other open items:
  - There is no link for accessorial charges found at delivery.
  - There is no business object for a claim declination letter.
  - The safety managers' after-hours on-call duty is not modelled.

### Batch frt-01: ltl-pickup-request, ltl-pd-dispatch, ltl-pickup-execution, ltl-origin-dock

- **`ltl-pickup-execution`:** it produces `dvir` and `driver_timecard` for every pickup stop, but drivers inspect trucks and record hours once a day. I moved both to `ltl-pd-dispatch`, which runs per terminal-day. The same applies to `ltl-delivery-execution`. This process also lacks `terminal-service-clerk`, who matches the paper bills of lading to closed pickups.
- **`ltl-origin-dock`:**
  - It has no input of `linehaul_load_plan` from `ltl-linehaul-planning`, though the dock loads trailers by that plan.
  - It has no trigger from `cartage-agent`, though cartage agents pick up in small towns. I estimate about 4% of origin freight.
  - Its resources lack `hub-dock-door`, though about 40% of origin shipments are handled at the hubs.
- **`ltl-pd-dispatch`:** it needs `labour_schedule` from `ltl-dock-labour-scheduling`, which covers city drivers. It should also send `terminal_kpi_data` to `ltl-terminal-performance`.
- **`ltl-pickup-request`:** `city-dispatcher` is missing; dispatchers decide which late requests run the same day.
- **`pd-driver` headcount of 540 looks low:** 100,000 pickups at about 36 minutes, about 115,000 delivery stops, and daily inspection and check-in need roughly 127,000 hours a month. That is about 620 to 650 drivers at 200 paid hours each.

### Batch frt-02: ltl-linehaul-planning, ltl-linehaul-dispatch, ltl-hub-crossdock, ltl-dest-dock

- **`linehaul-driver` (240):** at 14,000 trips a month, three quarters run by company drivers at about 5 on-duty hours each, every driver works about 220 hours a month. That is high. Either the headcount is 15 to 25% low (about 280 to 300 drivers) or the trip count is high.
- **Dock workers:** the four dock processes need about 550 to 640 dock workers. The file has 560 (330 hub, 230 terminal), which leaves nothing for absence, training or the autumn peak.
- **`linehaul-planner` (12):** about 7 minutes per departure works out to about 2,400 hours a month, enough for 14 to 15 planners.
- **`ltl-linehaul-planning`:** about 35% of departures are built at hubs, so `ltl-hub-crossdock` should also trigger it with `shipment_scan_data`. `dock-supervisor` is missing from its roles.
- **`ltl-linehaul-dispatch`:** the load plan starts each trip. Loaded trailers from the origin dock and hub are better recorded as inputs than as triggers.
- **`ltl-hub-crossdock`:** `trailer_move` from yard management is an input, not a trigger. The process should also send `shipment_scan_data` to planning and `wi_referral` to `ltl-reweigh-inspection`.
- **`ltl-dest-dock`:** these roles are missing:
  - `hub-dock-worker` (hub cities strip their own freight)
  - `city-dispatcher`
  - `osd-clerk`
  - `terminal-service-clerk`

  The `pd-truck` resource is missing, and the process should also link a misdirect back to `ltl-linehaul-planning`.

### Batch frt-03: ltl-delivery-execution, ltl-osd-exceptions, ltl-reweigh-inspection, ltl-dg-handling

- **`pd-driver` headcount (540) is too low.** Delivery alone needs about 385 FTE, and the other agent's pickup file states 250 more. Old Dominion's 2021 10-K (5,644 P&D drivers for 12.9M shipments), scaled to this carrier's 1.8M shipments, suggests about 790 drivers before cartage agents.
- **`wi-inspector` (12) cannot cover 12,000 inspections a month.** Hands-on time works out to about 22 FTE of inspector work. Either supervisors at satellite terminals do part of it, or the inspection count is lower.
- **`ltl-reweigh-inspection` is missing triggers.** It should also take `wi_referral` from `ltl-hub-crossdock` and from `fin-freight-bill-entry`, not only from the origin dock.
- **Missing roles:**
  - `ltl-delivery-execution` needs `city-dispatcher`, `cs-rep`, `terminal-service-clerk` and `terminal-dock-worker`.
  - `ltl-osd-exceptions` needs `terminal-dock-worker`.
  - `ltl-dg-handling` needs `dock-supervisor`, `terminal-service-clerk`, `linehaul-driver` and `city-dispatcher`.
- **Missing links:**
  - `ltl-dg-handling` starts at pickup, and refused or returned shipments go back to `shipper`.
  - `sls-freight-claims` receives `osd_report` but lists only `shipper` as a trigger.
  - OS&D cases closed with no loss answer `sls-shipment-tracing` with `trace_response`.
- **`pd_route` works better as a standing input** to delivery than as its trigger. I used `staged_freight` as the trigger.

Web research used 13 opened sources: Transport Canada's dangerous goods pages, the Hours of Service regulations, Day & Ross and Manitoulin bill of lading terms, a Manitoulin OS&D clerk job posting, Measurement Canada's rules for dimensioning devices, Old Dominion filings and two trade articles. Carrier PDFs (Gardewine's tariff, an MIT study) could not be read, so most step times are tier C estimates with notes.


### Batch frt-04: tl-load-tender, tl-load-planning, tl-trip-execution, tl-customs-emanifest

- **Staffing:**
  - `tl-customer-rep` (22 people): tender work alone implies about 31 FTE, before detention tracking and customer calls. About 30 reps would fit.
  - `load-planner` (14 people): about 21 FTE of planning work.
  - `customs-coordinator` (14 people): about 14 FTE including 24-hour cover, so the desk has almost no slack.
- **Volumes:** in `tl-load-planning`, 7,700 assignments a month is more than the roughly 7,400 tenders that reach the fleet; the difference is re-planned loads.
- **Missing links:**
  - Planners hand uncovered loads back to `tl-brokerage` (`tl-load-planning` to `tl-brokerage`, object `booked_load`).
  - Held trucks pass from `tl-customs-emanifest` to `tl-border-holds`.
  - The `customs_release` from `customs-broker` that the map lists as a trigger for `tl-customs-emanifest` is really a reply partway through a case.
- **Missing roles in the process map:**
  - `pricing-analyst` is not listed for `tl-load-tender`.
  - Company drivers and `owner-operator` are not listed for `tl-load-planning`; they accept or refuse assignments.
  - `road-service-tech` is not listed for `tl-trip-execution`.
- **Missing surge:** `tl-load-planning` has none, although the autumn peak applies to it.

### Batch frt-05: tl-driver-management, tl-oo-contracting, tl-brokerage, fin-oo-settlements

- **`tl-driver-management`:** 36 driver managers at 30 to 45 drivers each would cover 1,080 to 1,620 drivers. The carrier has 430 company drivers plus 380 owner-operators. My steps need about 15 FTE of driver-manager time for the 430. So either the headcount is high (about 18 to 25), or owner-operator weeks belong in the volume, which would make it about 3,500 a month. The role list is missing `load-planner`, `settlements-clerk`, `after-hours-dispatcher`, `compliance-specialist`, `driver-recruiter` and the driver roles.
- **`tl-oo-contracting`:** 6 to 16 a month fits signed new leases only. With renewals, tractor changes, terminations and declined applications it is about 35 to 70 a month. The roles are missing `compliance-specialist`, `driver-trainer`, `technician`, `settlements-clerk`, `driver-manager` and `owner-operator`. The `shop-bay` resource is also missing.
- **`tl-brokerage`:** 600 loads a month at about CAD 2,500 each (from TIA data) is about CAD 18M, roughly 3% of revenue, not the stated 6%. The other agent's load-tender workflow supports about 600 loads a month, so the 6% looks wrong. The roles are missing `load-planner`, `ap-clerk`, `customs-coordinator`, `tl-customer-rep`, `tl-ops-manager` and `security-coordinator`. There is no output for suspected fraud to `saf-cargo-security`.
- **`fin-oo-settlements`:** 1,650 statements a month is right. The roles are missing `driver-manager` and `owner-operator`. The trigger from `ltl-linehaul-dispatch` assumes some owner-operators pull LTL linehaul, but all 380 owner-operator tractors sit in `tl-fleet`. Settlements need about 5.5 of the 10 `settlements-clerk` FTE, leaving about 4.5 for `fin-driver-pay` at 2,650 cases a month, which is tight.

### Batch frt-06: mnt-preventive-maintenance, mnt-defect-repair, mnt-annual-inspection, mnt-roadside-breakdown, mnt-parts-inventory

- **mnt-roadside-breakdown:** the description names a "shop dispatcher", but no such role exists. I added a 24-hour breakdown and road call coordinator, marked `not_in_org_file` (about 5 people, 2.6 FTE on calls). The volume of 300 a month holds only if owner-operator and trailer calls are counted; TMC/FleetNet miles between road calls put company-only calls nearer 150 to 300. The process also lacks links to `fin-accounts-payable` (vendor invoices) and `tl-load-planning` (replacement equipment).
- **mnt-preventive-maintenance:** fleet counts and the practitioner guide's service intervals give about 1,200 a month (950 to 1,600), not a mode of 1,100. Links missing: odometer data from `ltl-pd-dispatch`, equipment availability to `ltl-pd-dispatch` and `tl-load-planning`, and work orders to `mnt-defect-repair`.
- **mnt-defect-repair:** no link from PM findings, and no sublet purchase order to `equipment-dealer`.
- **mnt-annual-inspection:** equipment availability back to dispatch is missing. Quebec units are maintained under the SAAQ preventive maintenance program instead of SAAQ inspection, which the file does not mention.
- **mnt-parts-inventory:**
  - **Trigger:** `parts-supplier` parts deliveries are listed as a trigger, but a delivery is a step inside a purchase order.
  - **Missing requisitions:** none from `mnt-collision-repair` or `mnt-yard-equipment`.
  - **Missing matched invoice:** no matched invoice goes to `fin-accounts-payable`. The file routes parts invoices straight from the supplier to payables, skipping the receipt check done in the shop.
- **Roles:** no single role covers drivers or dispatchers across the LTL and truckload divisions, so each workflow uses one representative role and says so in its assumptions.

### Batch frt-07: saf-driver-recruiting, saf-driver-onboarding, saf-hos-log-audit, saf-collision-management

- **Missing roles in the process map:**
  - `saf-driver-recruiting`: `driver-manager` and `terminal-manager` interview candidates.
  - `saf-driver-onboarding`: new and mentor drivers in finishing programs (about 40 FTE of driver time, using `tl-driver-longhaul`), plus `driver-manager`.
  - `saf-hos-log-audit`: `terminal-service-clerk` scans paper logs; `driver-manager` and `linehaul-supervisor` talk to drivers about violations.
  - `saf-collision-management`: `city-dispatcher`, the involved driver, `vp-safety` (chairs the review committee) and `safety-analyst` (accident register).
- **Missing links:**
  - `saf-driver-onboarding` sends new hires only to `ltl-pd-dispatch` and `tl-driver-management`. LTL linehaul hires need a link to `ltl-linehaul-dispatch`.
  - `saf-hos-log-audit` should produce `it_ticket` to `it-service-desk` for device malfunctions.
- **Headcount:** 14 `driver-recruiter` for 450 applications a month looks high. Hands-on time implies about 4.5 FTE, so either unlogged leads are much higher than applications or 6 to 8 recruiters would be enough.
- **Volume:** the audit produces about 490 confirmed hours-of-service violations a month. That is most of the 600 to 1,050 events `saf-driver-performance` handles from all sources, so that range looks low.
- **Shift pattern:** `safety-manager` has none in the org file, but in practice they cover collisions on call after hours.
- **Training tractors:** 10 `training-tractor` are enough for road tests. Finishing programs run in ordinary truckload tractors, which ties up about 15 to 20 `tl-tractor` at any time.

### Batch frt-08: sls-pricing-quotes, sls-contract-renewal, sls-shipment-tracing, sls-freight-claims

- **`sls-pricing-quotes` volume or headcount:** 2,500 requests a month implies about 21 FTE. Only 10 `pricing-analyst` exist, and they also cover RFPs and renewals. Either volume is nearer 1,300 to 1,800, or simple spot quotes are given by customer service, or more analysts are needed.
- **`sls-pricing-quotes` surge:** a multiplier of 2 to 4 is too high. FreightWaves says only 20 to 25% of LTL revenue is subject to the general rate increase, and it is applied to the tariff without new quotes. I used 1.2 to 1.8.
- **Roles missing from the process entries:**
  - `sls-pricing-quotes`: `network-analyst`, `vp-sales`
  - `sls-contract-renewal`: `billing-auditor`
  - `sls-shipment-tracing`: `terminal-service-clerk`, `osd-clerk`
  - `sls-freight-claims`: `osd-clerk`, `terminal-ops-supervisor`, `claims-specialist`
- **`sls-contract-renewal` trigger:** the carrier starts renewals from its own expiry calendar, not from a shipper sending a rate agreement. The account profitability report usually comes from pricing's costing model, not from month-end close.
- **Missing links:**
  - Tracing should also send `trace_response` to `consignee`.
  - Claims should take `delivery_receipt` from `ltl-pod-capture`, and file recovery claims against `interline-partner`.
  - Renewals that end in a bid should lead to `sls-rfp-response`.
  - Pricing should send spot `rate_quote` to `fin-rating-invoicing`.
  - There is no business object for a claim declination letter.
- **`cs-rep` headcount:** 60 looks tight. Tracing alone needs about 32 FTE, and the reps also take part in 100,000 pickup requests a month.


### Batch frt-09: fin-freight-bill-entry, fin-rating-invoicing, fin-billing-corrections, fin-driver-pay

- **`billing-auditor` (10 people) is too small.** At 9,000 corrections a month, about 19 minutes per case needs about 22 people. Either the headcount should be about 20, or the volume is nearer 4,000 a month.
- **`billing-clerk` (45 people) is slightly short.** Hands-on time needs about 33 for bill entry and 15 for rating, about 48 in total.
- **Roles missing from process entries:**
  - `fin-rating-invoicing`: `pricing-analyst`, `tl-customer-rep`, `terminal-service-clerk`.
  - `fin-billing-corrections`: `pricing-analyst`, `terminal-service-clerk`, `account-executive`, `credit-manager`.
  - `fin-driver-pay`: `terminal-ops-supervisor`, `linehaul-supervisor`, `finance-manager`, `payroll-administrator`.
  - `fin-freight-bill-entry`: `terminal-service-clerk` (scans the bills and answers queries, about 18 FTE).
- **`fin-driver-pay` uses the wrong demand driver.** It is set to `employees`. The 2,650 records a month fit about 1,210 company drivers paid every two weeks, not all employees.
- **Missing link:** nothing connects `ltl-delivery-execution` to billing for charges found at delivery, such as liftgate or waiting time. I assumed they are added before invoicing.
- **Pricing errors:** in `fin-billing-corrections`, the error report goes to pricing on only about 10% of corrected cases, but the interface format applies it to every corrected case.
- **The surge in `fin-billing-corrections` may be too big.** It triples volume during the rate-increase season. I kept it because I found no evidence to change it, but it looks high.

## community-hospital-corp

**Status 2026-11-24.** `tools/sync_map_from_workflows.py` and `tools/fixes_2026_11_24_hospital.py` applied
the reports below. The employee count is a sourced average (Halton's reported staff plus the medical staff), so
roles first use their units' unassigned headcount. A unit grows only where its listed roles exceed it.

Applied:

- The sync added the missing links (62), role listings (60), eight resources and six systems. It also added
  seven roles the workflows needed: charge nurses for medicine and the ICU, rehabilitation assistants, a nurse
  discharge coordinator, dialysis assistants, a hearing screener and an infection control physician.
- Operating room cases go from 3,700 to 2,450 a month. The annual reports count endoscopies as surgeries, and
  the map also counted them in `sx-endoscopy`. Elective bookings go to 2,150 and add-on cases to 320 (13%,
  Auditor General). Stated FTE in the two surgery workflows were scaled to match.
- ICU nurses go from 110 to 140, set from bedside coverage: 30 beds at one nurse to one or two patients, about
  97 FTE, which is about 140 people at the part-time share the medicine units imply.
- The 18 medicine charge nurses come out of the medicine RN headcount, and the infection control physician comes
  out of the consultant specialists.
- Five roles were raised to cover their documented work:
  - bed flow coordinators, 12 to 17
  - rehabilitation assistants, 9 to 14
  - ED assistants, 20 to 23
  - hospitalists, 40 to 42
  - surgical booking clerks, 10 to 11
- Volumes now match the workflows:
  - ambulance arrivals: 2,600 (Auditor General's 20%)
  - ED discharges home: 10,300 (CIHI)
  - admissions from the ED: 1,400
  - discharge planning: 1,700, now limited to medicine, surgery and complex care
- Employees go from 5,790 to 5,911. Several units already had more listed roles than people, among them
  medicine inpatient (790 against 700), health records, and portering and security. Halton reported 5,228 staff
  and 931 medical staff in 2021/22.
- Link fixes:
  - Portered patients are an input to imaging and surgery, not a trigger.
  - Dialysis nurses send specimens straight to the lab. They no longer send orders to the collection service,
    in the map or in the collection workflow.

Still open:

- Operating rooms are still short by about a quarter. 2,450 cases need about 3,700 room-hours, and 17 rooms
  give about 2,800. Possible reasons are procedure rooms outside the OR count, or the emergency room used after
  hours. No published room count was found.
- Headcounts are people, not FTE. The 97% resizing therefore treats each person as full-time, and part-time
  roles may be shorter than shown.
- Postpartum beds (45) would run at about 40% occupancy. The evidence supports about 25, so the count probably
  includes other bed types.
- The crisis team (25 people for about 8 FTE of documented work) and other roles with little documented work
  were not cut, because 54 of 88 processes have no workflow.
- Charge nurses on surgical, maternity and mental health units are not modelled.
- Registration's volume driver understates the visits it counts.

### Batch hosp-01: ed-ambulance-offload, ed-patient-triage, ed-physician-assessment, ed-specialist-consult

- **ed-ambulance-offload, volume:** the 2,800 a month is too high. The Auditor General reports 20% of Ontario ED visits arrive by ambulance, which gives about 2,100 to 2,700 a month (mode 2,600). Its roles also leave out `ed_assistant`, who prepares stretchers.
- **ed-physician-assessment, triggers:** lab results, imaging reports and consult notes are listed as triggers. They come back during a visit and do not start one, so I listed them under `inputs`.
- **ed-physician-assessment, evidence:** the audit's Appendix 3 gives each site's 2022/23 average time from triage to physician assessment: 1.5 h (Milton), 2.5 h (Georgetown) and 3.3 h (Oakville). The entry could cite these.
- **ed-specialist-consult, roles:** `hospitalist` is missing, though hospitalists admit most medical patients in Ontario community hospitals.
- **ed-specialist-consult, links:** there is no link to `amb-clinic-referral-booking` for clinic follow-up after a consult. The 15% consult rate is plausible; a tertiary study found 38%, which a community hospital would be expected to fall below.
- **ed-patient-triage, links:** there is no link to `wc-obstetric-triage` for pregnant patients sent to the birthing unit, since that process is triggered only by `patient`. `ed_assistant` (entrance screening in 2020 to 2022) is also missing.
- **ed-patient-triage, overlap:** the map gives triage of ambulance patients to both processes. My files put it in offload only.
- **ambulance_crew:** I added this resource to the offload file because offload delay ties up the crew. The organisation file does not have it.

### Batch hosp-02: ed-admission-boarding, ed-discharge-home, cs-bed-management, fs-environmental-cleaning

- **Wrong volume, `ed-discharge-home`:** the file has 8,800–10,900–11,400 a month, about 84% of ED visits. CIHI NACRS data for 2018/19 to 2021/22 put discharges home at 78.8–79.9% of visits, which gives about 8,300–10,300–10,700.
- **Volume, `ed-admission-boarding`:** the file's 1,350 a month is about 10.4% of visits. CIHI gives 10.6–12.4% and the Auditor General 12%, so a mode of about 1,400 fits better. This is minor.
- **Missing roles in process-map entries:**
  - `ed-admission-boarding` lacks `porter`, `med_rn` and `ed_assistant`.
  - `ed-discharge-home` lacks `ed_assistant`, `transcriptionist` and `him_clerk`.
  - `cs-bed-management` lacks `med_rn`, `unit_clerk` and `staffing_clerk`.
  - `fs-environmental-cleaning` lacks `unit_clerk` and `psw`.
- **Missing links:**
  - `sx-perioperative-case` should send a `bed_request` to `cs-bed-management`.
  - `cs-bed-management` should send a `transfer_acceptance` to `tertiary_hospital`.
  - `ed-discharge-home` should send a `home_care_referral` to `hccss` and a `dictation` to `dh-transcription`.
  - `ed-admission-boarding` should send an `ed_disposition` to `ed-discharge-home` for patients discharged while boarding, and a `transport_request` to `fs-patient-portering`.
- **Missing resources and systems:**
  - `fs-environmental-cleaning` lists no resources, although dirty beds are held. I used `bed_medicine` and `bed_surgical`, and added a UV disinfection device marked `not_in_org_file`.
  - The file has no system for Health Report Manager (OntarioMD), which delivers ED reports to family physicians. I added it as a workflow system.
- **Headcount, `bed_flow_coordinator`:** 12 people is tight. Bed management plus boarding alone take about 11.5 FTE, with 24/7 cover at the large site.

I did not edit the organisation file. The build scripts are in `_build_hosp02/` and downloaded sources in `_dl_hosp02/`. The Auditor General figures come from the copy of that report another agent saved in `_dl_hosp01/`. I read its text and checked that its size matches the PDF served at the cited URL.

### Batch hosp-03: med-inpatient-medical-care, med-medication-administration, cs-pharmacy-order-verification, med-icu-critical-care

- **Missing roles:**
  - No charge nurse on inpatient units or in the ICU. I added `med_charge_nurse` and `icu_charge_nurse`, both marked `not_in_org_file`.
  - No sterile compounding hoods for pharmacy IV preparation. I added the resource `sterile_hood`, also marked `not_in_org_file`.
- **Missing role links:** `hospitalist` takes part in `med-medication-administration` (held-dose calls) and in `cs-pharmacy-order-verification` (pharmacist clarification calls). `pharm_tech` takes part in medication administration (delivering missing doses).
- **Low headcount:** `icu_rn` is 110. Thirty beds at one nurse to one or two patients, around the clock, need about 90 to 100 productive FTE, which is roughly 130 to 150 heads.
- **Missing links:**
  - `med-icu-critical-care` has no trigger from surgery. CIHI shows about 18% of Ontario ICU stays are planned admissions after surgery.
  - ICU deaths (about 9%) have no path to `donation_agency` or `coroner`; the map only routes deaths through `med-end-of-life-care`. My ICU file adds both.
  - `med-inpatient-medical-care` lacks a trigger from `tertiary_hospital` (`repatriation_request`).
- **Volumes:** all four volumes in the map hold up against the evidence.
- **Pharmacy opening hours:** the map does not say whether pharmacy is open overnight. Only 9% of Canadian hospital pharmacies were open 24/7 in 2020/21, so I assumed 12% of orders wait until morning.


### Batch hosp-04: sx-surgical-booking, sx-or-scheduling, sx-perioperative-case, sx-sterile-reprocessing

- **`operating_rooms`:** 17 rooms at about 165 hours a month give about 2,800 room-hours. 3,700 cases a month at about 1.5 hours of room time each need about 5,500. Either the room count or hours are too low, or many of the reported surgeries are short procedures or endoscopies done outside these rooms.
- **`surg_booking_clerk`:** headcount 10, but step times imply about 15 FTE for 3,000 bookings a month.
- **`anesthesiologist`:** headcount 40, but perioperative work alone implies about 40 FTE at 130 hours a month, leaving no time for obstetric or ICU cover.
- **`mdrd_tech`:** headcount 60 against about 57 FTE implied for 9,500 trays, which leaves little slack.
- **Roles missing from process role lists:**
  - `sx-perioperative-case`: `registration_clerk`, `bed_flow_coordinator`, `porter`.
  - `sx-or-scheduling`: `bed_flow_coordinator`.
- **Missing links:** `sx-sterile-reprocessing` lacks `suppliers` as a trigger for vendor loaner sets. `sx-perioperative-case` lacks a return link to `sx-surgical-booking` for cases cancelled on the day of surgery.
- **Missing systems and resources:** there is no instrument tracking system, and no washer-disinfectors or automated endoscope reprocessors. I added these as not in the organisation file, estimating six washers and six reprocessors.
- **Emergency share:** the Auditor General of Ontario gives 13% of cases as emergencies, against the file's 12%. That puts elective bookings nearer 2,800–3,300 a month, so I raised the booking volume's upper end to 3,400.
- **Pre-operative documents:** from October 2019 the hospital required a Cumulative Patient Profile in the booking package instead of the pre-op history and physical (Halton letter). The file's process description is otherwise consistent with this.


### Batch hosp-05: wc-labour-delivery, wc-postpartum-newborn-care, mh-ed-crisis-assessment, med-hemodialysis

- **`wc-labour-delivery`:** A blood product is listed as a trigger, but it is a standing input. Booked caesareans (about 13% of births) arrive from `sx-or-scheduling`, a trigger the map lacks. When the baby goes to the NICU, the mother still goes to postpartum (`maternity_patient`), and that link is missing.
- **`wc-postpartum-newborn-care`:**
  - No hearing screener role exists; I added `hearing_screener`.
  - The 45 mother-baby beds would run at about 40% occupancy. The evidence supports about 23 to 25 beds, so the count probably includes other bed types.
- **`mh-ed-crisis-assessment`:**
  - The process roles leave out `ed_rn`, `ed_charge_nurse` and `bed_flow_coordinator`.
  - Missing outputs: `ed-interfacility-transfer`, `ed-discharge-home`, `police` and `qp-incident-management`.
  - The crisis team's 25 headcount is about three times the 8 FTE the volume needs.
  - The volume of 380 to 560 a month has no source. One downtown academic hospital found 8.1% of ED visits were mental health visits.
- **`med-hemodialysis`:**
  - No role for the assistants who clean stations between patients (about 6 FTE). The 8 technologists cannot absorb that work, so I added `dialysis_assistant`.
  - Nurses draw the monthly blood work themselves, so the right output is `lab_specimen` to `dx-lab-testing`, not `lab_order` to `dx-lab-specimen-collection`.
  - The published dialysis visit count may include some home-program visits.
  - At about 4.6 hours per session, the 40 stations run about 92% full.

### Batch hosp-06: dx-lab-specimen-collection, dx-lab-testing, dx-blood-transfusion, qp-ipac-surveillance

- **`dx-blood-transfusion` roles:** `mla` (who draws the group-and-screen sample) and `porter` (who picks up and returns units) are missing. Nurses outside medicine (ED, ICU, OR, labour and delivery, day medicine) also transfuse, but only `med_rn` is listed.
- **`dx-blood-transfusion` triggers:** `med-icu-critical-care`, `sx-surgical-inpatient-care` and `amb-systemic-therapy` are missing as sources of blood orders, and `amb-systemic-therapy` is missing as a recipient. The volume of 600–1,000 a month is plausible: Ontario transfused about 950 red cell units a day in 2021/22.
- **`qp-ipac-surveillance` roles:** there is no IPAC physician lead; I added `ipac_physician` with `not_in_org_file`. `bed_flow_coordinator` (single-room moves) and `med_rn` (placing precautions, swabbing contacts) are also missing.
- **`ipac_practitioner` headcount:** 12 is above the published Ontario average of 1 per 90 beds (about 7 for 639 beds). That is plausible for the COVID-19 years, but should be labelled as such.
- **`dx-lab-testing` produces:** there is no link back to `dx-lab-specimen-collection` for recollection requests. `dx_director` takes no part in individual tests.
- **`dx-lab-specimen-collection`:** `med-icu-critical-care` and the ED/ICU line draws are missing as triggers. The pneumatic tube system and the centrifuges are not in the resources list; I added both with `not_in_org_file`.
- **Lab test volumes:** these check out against the annual reports (2,597,035 tests in 2018/19 and 3,220,658 in 2021/22).

### Batch hosp-07: dx-imaging-exam, dx-radiology-reporting, amb-clinic-referral-booking, dh-patient-registration

- **`dx-imaging-exam`:** walk-in outpatients with a family doctor's requisition (`primary_care` `imaging_order`) are missing as a trigger; I gave them 19% of exams. `fs-patient-portering` `transported_patient` is a hand-off during the exam, not a trigger. The resources have no portable X-ray units; I added 8.
- **`dx-radiology-reporting`:** the process lists only `radiologist`, but `di_clerk` and `transcriptionist` also do the work. There is no output to `amb-clinic-visit` for clinic-ordered exams. The report-delivery system (Health Report Manager) is not in the systems list.
- **`amb-clinic-referral-booking`:** `amb_rn` is missing from the roles. There is no trigger from `cs-discharge-planning` for follow-up referrals after an inpatient stay.
- **`dh-patient-registration`:**
  - The volume driver `outpatient_clinic_visits` (15,000 to 25,000 a month) understates the work. Adding up the visit types gives about 45,000 to 55,000.
  - `him_clerk`, who reviews and merges duplicate records, is missing from the roles.
  - Triggers lack emergency admissions from `ed-admission-boarding` and walk-in imaging orders from `primary_care`.
  - Outputs lack `dx-imaging-exam` and `dx-lab-specimen-collection`.
  - `registration_clerk` headcount of 75 looks tight: this process plus emergency registration needs about 60 FTE (full-time equivalents).


### Batch hosp-08: cs-discharge-planning, cs-alc-management, cs-allied-health-referral, dh-chart-coding

- **Missing roles:**
  - A nurse discharge planner (patient care coordinator), common in Ontario community hospitals. Added as `patient_care_coordinator`.
  - The home care coordinators based in the hospital, who work for the LHIN home care organisation (HCCSS from 2021) and do the eligibility, home care and long-term care placement steps. Added as `hccss_care_coordinator` (external), with no hospital FTE.
  - PT/OT rehabilitation assistants. Added as `rehab_assistant`.
  - An inpatient charge nurse; `med_rn` covers it for now.
- **`cs-discharge-planning` volume:** 2,000 to 2,600 counts all inpatient discharges, but the only triggers are medicine, surgery and complex care. I used 1,500 to 1,950. Either lower the entry or add triggers from obstetric, paediatric and psychiatric care.
- **Wrong link types:** in `cs-discharge-planning`, `allied_health_assessment` and HCCSS `care_plan_confirmation` should be inputs rather than triggers. The same applies to the `ltc_homes` `bed_offer` in `cs-alc-management`.
- **Missing links:**
  - `cs-allied-health-referral` should send `imaging_order` to `dx-imaging-booking` for swallow studies.
  - `cs-alc-management` should send `transfer_package` to `ltc_homes` and `cleaning_request` to `fs-environmental-cleaning`.
  - `pharmacist` is missing from the discharge-planning roles (discharge medication reconciliation).
- **Headcounts:** the simulation needs about 26 coder FTE against 30 coders listed, which is plausible after leave and other duties.

### Batch hosp-09: hr-staff-scheduling, qp-incident-management

- **`hr-staff-scheduling`:**
  - Sick calls also come from the emergency department, intensive care, labour and delivery, operating rooms and cleaning staff. The file lists only `med-inpatient-medical-care` and `cs-bed-management` as triggers.
  - The roles list leaves out `admin_on_call`'s partners in the work: `bed_flow_coordinator` (blocks beds) and `hr_advisor` (grievances).
  - There is no inpatient charge nurse role. I used `med_rn`.
  - `hr_manager` is listed but does no step.
  - Two outputs are missing: `bed_status_update` to `cs-bed-management` when beds close, and `grievance` to `hr-labour-relations`.
- **`qp-incident-management`:**
  - The triggers leave out the largest source, `med-inpatient-medical-care` (falls). They also leave out `ed-physician-assessment`, `sx-surgical-inpatient-care`, `dx-lab-testing` and `mh-inpatient-psychiatry`.
  - The roles leave out people who do steps: `admin_on_call`, the physician who tells the patient (`hospitalist`), `dept_chief`, and the maternity and mental health managers.
  - The `quality_report` output to `qp-quality-improvement-plan` is missing.

The Ontario e-Laws pages for Regulation 965 would not open. The rules in the incident file come from the Ontario Auditor General's 2019 audit and an ISMP Canada report instead.

## electric-distribution-utility

**Status 2026-11-24.** `tools/sync_map_from_workflows.py` and `tools/fixes_2026_11_24_utility.py` applied
the reports below. The owner chose to resize roles to their documented work, as for the other companies, and to
record the gap to Hydro Ottawa's reported staff as the main open item.

Applied:

- The sync added the missing links (50), role listings (77), resource listings (27) and eight systems.
- Locates are contracted. The workflow needs 40 contract locators, recorded as contractor staff and not
  employees. In-house locators keep complex and urgent jobs.
- 19 roles were raised to cover their documented work at 97% load. The largest changes:
  - billing analysts, 16 to 34
  - field service representatives, 8 to 20
  - system operators, 20 to 30
  - work planners, 12 to 19
  - meter technicians, 12 to 19
  - power line technicians, 62 to 69
  - switching planners, 3 to 9
  - field dispatchers, 6 to 10
  - control room shift supervisors, 4 to 6
- Employees go from 571 to 658.
- Volumes now follow the workflows:
  - cable faults: 20 a month, from cable length and failure rates
  - asset inspections: 2,500, from the inspection cycles
  - vegetation: 125 km and urgent requests
  - major events: 0.19 a month, 9 in 48 months
- Surges were copied from the workflows for 19 processes. System monitoring now peaks at 1.1 to 2 times its
  normal desk hours, not 3 to 12 times, and the follow-up pole work at 1.5 to 4 times, not up to 40.
- Description fixes:
  - The ESA audit is done by an approved auditor, and an officer signs the declaration.
  - Major events were mostly Hydro One supply losses.
  - The station count note gives 92 from Hydro Ottawa's 2021 post.

Still open:

- 658 employees is about 13% above the 581 FTE that Hydro Ottawa reported for 2020. Either some workflow
  volumes and step times are high, or more work is contracted out than the file shows. The largest unsourced
  volumes are billing exceptions (6,000 a month), field service orders (1,300), collections (12,000) and meter
  exchanges (2,000). Meter seal campaigns may be partly contracted, as Hydro One does.
- The contact centre counts calls only. Emails and web forms (about 1,500 to 2,500 a month) are not counted.
- No fleet coordinator, no inspector role, and no bill print vendor party.
- The 2021 revenue requirement in the rate application description ($216.6 million, against the OEB's $203.9
  million base figure) needs checking.

### Batch edu-01: ops-trouble-response, ops-outage-restoration, ops-major-event-response, ops-system-monitoring

- **`ops-major-event-response`**:
  - There were 9 major events in 48 months, so the volume should be 0.19 a month, not 0.1.
  - Only 3 of the 9 opened an incident command centre, and only the May 2022 derecho used mutual aid. 5 of the 9 were supply losses from Hydro One, so the description overstates the storm response.
  - Roles missing from the entry: `system-operator`, `control-shift-supervisor`, `field-service-rep` (as damage assessors), `regulatory-analyst` (OEB report within 60 days).
  - Resources missing: `light-vehicle`, `warehouse`. Missing links: a trigger from `hydro-one` and an output to `oeb`.
- **`ops-outage-restoration`**: roles missing are `trouble-plt` (patrols and switching), `stores-attendant`, `apprentice-plt` and `safety-advisor` (spill reports). Resource missing: `warehouse`.
- **`ops-system-monitoring`**:
  - The surge multiplier of 3–12 describes events, not shifts. Storms make shifts longer and add a storm desk, roughly 1.1–2x the desk hours.
  - `control-shift-supervisor` has 4 people, but one seat around the clock needs about 4.9.
- **`system-operator` (20 people)**: the edu workflow files together claim about 24.5 operator FTE. I cut monitoring to 11 to keep the total near 20.
- **`ops-trouble-response`**: 900 orders a month uses nearly all the hours of two trucks per shift. Either day crews take some orders or the volume is high.

### Batch edu-02: ops-control-room-switching, ops-work-scheduling, ops-field-service-orders, ops-locates

- **`ops-locates` delivery model:** the file has in-house locators with contractor overflow. Ten `cable-locator` staff cannot mark about 5,000 field tickets a month; that takes about 38 FTE. A search excerpt from a later Hydro Ottawa rate filing says external vendors did the locates, at about $3.1M a year. I could not open that filing, so I added a `contract-locator` role and kept in-house locators for complex jobs. The same excerpt gives about 87,000 to 104,000 locates a year for 2017 to 2021, which fits the 7,500 a month in the file.
- **`ops-field-service-orders`:** 1,300 orders a month at about an hour per visit needs about 10 representatives. The file has 8 `field-service-rep`, so either the volume is high or the headcount is low.
- **`ops-work-scheduling`:** 12 `work-planner` staff for 2,000 orders a month is fully loaded at about 13 FTE. `design-technologist` should be added, since returned packages go back to design.
- **`ops-control-room-switching`:** `lines-supervisor` (and the underground and station supervisors) is missing from the roles, though they apply for work protection. Three `switching-planner` staff cannot write 350 orders a month alone, so night-shift system operators also write orders. The org file models field switching as about 15 FTE of `power-line-technician` time but does not show it.
- **Appointment rule:** the four-hour window comes from the org file. I could not verify it in the Distribution System Code.

### Batch edu-03: ops-overhead-construction, ops-underground-construction, ops-pole-replacement, ops-cable-fault-repair

- **`ops-cable-fault-repair` volume:** 25/40/70 a month looks too high for primary cable faults. Hydro Ottawa has about 5,000 km of cable (T&D World, 2016). At EPRI's median failure rate (1.9 per 100 conductor miles a year) that is about 60 faults a year; even with old cable at three to four times that rate, it comes to roughly 15–25 a month. I used 10/20/35.
- **`ops-cable-fault-repair` links:** it is missing an input of `work_protection` from `ops-control-room-switching`. The control room isolates the faulted section and issues the permit.
- **`ops-pole-replacement` roles:** `design-technologist` (who sends and chases transfer notices to telecom companies) is missing.
- **`ops-pole-replacement` surge:** the multiplier of up to 40 counts poles broken in storms. Those are replaced as emergency restoration work, so I used 1.5–4 for the planned follow-up work only.
- **Roles across all four entries:** `work-planner`, `switching-planner`, `system-operator` and `stores-attendant` are missing, and so is `construction-inspector` for the two construction processes. Each does steps in these processes.
- **Locate requests:** none of the four entries lists `locate_request` going to `ontario-one-call`.
- **Locate rule assumption:** the file says the five-business-day rule came from a page that was not opened. Hydro Ottawa's locates page confirms it, and gives ten business days for multi-address requests.

### Batch edu-04: ops-service-connection-work, ae-service-layouts, ae-developer-connections, ae-der-connection

- **`ops-service-connection-work`:** the high volume should be about 560, not 520. Hydro Ottawa's rate plan reports 6,067 residential connections a year in 2021-2023, about 505 a month. The process is missing `underground-supervisor` and `apprentice-cable`. The `line-crew` and `cable-crew` resources are 3-4 person construction crews, but service connections are done by 2-person crews.
- **`ae-service-layouts`:** `construction-inspector` is missing; Hydro Ottawa inspects every underground service trench twice.
- **`ae-developer-connections`:** `planning-engineer` and `construction-inspector` are missing. `developer:connection_agreement` arrives partway through a case, so I listed it as an input rather than a trigger.
- **`ae-der-connection`:** `meter-technician`, `pc-technologist` and `engineering-manager` are missing. The micro layout is a `connection_offer` to the applicant, which the map does not list as an output.
- **Headcounts:**
  - `design-technologist` (26): layouts and developer work alone take about 22 FTE, before capital design.
  - `connections-engineer` (5): about 3.9 FTE goes to developer and generation connections.
  - `cable-splicer` and `apprentice-cable` (44): service connections alone take about 16 FTE, which looks thin. This may be because developers' contractors install some subdivision services; I could not confirm that.

### Batch edu-05: ae-capital-plan, ae-system-planning, ae-asset-condition-assessment, ae-capital-project-delivery

- **`ae-capital-plan`:** the cycle starts from finance's annual budget call (`fin-budget`). Planning studies and asset condition results are standing inputs, not triggers. The roles list lacks `connections-engineer`, `ops-director`, `regulatory-analyst` (filing years) and `ceo` (board approval).
- **`ae-system-planning`:** the only trigger listed is `hydro-one`. Most studies start from `ae-developer-connections`, `ae-capital-plan`, `ae-reliability-analysis`, `ae-der-connection` or `ieso`. Missing roles are `gis-technician`, `switching-planner` and `design-technologist`. It also sends results to `hydro-one`.
- **`ae-asset-condition-assessment`:** missing roles are `stations-supervisor`, `lines-supervisor` and `gis-technician`. Missing outputs are to `fin-rate-application` and `ops-distribution-inspection`.
- **`ae-capital-project-delivery`:** the triggers list includes as-builts, design packages and inspection findings, which are inputs coming back to the project. Missing roles are `construction-inspector`, `work-planner`, `switching-planner` and `system-operator`. Missing outputs are to `contractor`, `ops-control-room-switching`, `ops-planned-outage-notice` and `ae-capital-plan` (deferred projects).
- **Systems:** Copperleaf C55 (investment planning), PowerDB (station test data), a power-flow tool and the City right-of-way portal are not in the file. I added them in the workflows.
- **Volumes and headcounts:** I found no evidence against them, so I kept them.


### Batch edu-06: ops-station-maintenance, ops-distribution-inspection, ops-vegetation-management, corp-fleet-maintenance

- **ops-distribution-inspection volume:** the entry's mode of 1,800 a month is too low. Hydro Ottawa's 2024 posts give a three-year cycle for transformers, switches and breakers and a 10-year test for all 49,000 poles. That works out to about 2,500 assets a month.
- **Inspection staffing:** that volume needs about 5 to 5.5 FTE of field service representatives, more than half of the 8, who also do disconnections. There is no inspector role; one should be added, or the work shown as contracted.
- **ops-vegetation-management volume:** cycles were 2 years urban and 3 years rural, which gives about 85 to 95 km a month against the entry's 75. Urgent tree requests (about 40 a month) are not counted.
- **Vegetation staffing:** the steps imply about 3.5 FTE of vegetation coordinators, against 3 in the file.
- **Vegetation trigger:** the cycle plan is missing as a trigger.
- **corp-fleet-maintenance triggers:** the only triggers are defects from outage restoration and overhead construction. Missing are defects from underground construction, trouble response and field service orders, and the fleet system's own preventive schedule.
- **Fleet supervisor:** fleet work alone needs about 0.85 FTE of the one supervisor, who also covers facilities. A fleet coordinator or parts clerk is missing.
- **Missing roles in the process maps:**
  - Switching planner and system operator for station maintenance.
  - System operator (reclose blocks) for vegetation management.
  - Field dispatcher and GIS technician for distribution inspection.
  - Overhead lines supervisor for fleet maintenance.
- **Station count:** 91 in the file, 92 in Hydro Ottawa's 2021 post.
- **Unconfirmed:** the monthly station inspection interval has no source I could open. I also could not read the Distribution System Code inspection table (the PDF did not render), so it is not cited.


### Batch edu-07: cs-contact-centre, cs-move-in-move-out, cs-collections, cs-billing-exceptions

- **cs-collections:** field-service-rep is missing from the roles. Disconnecting and reconnecting accounts takes about 450 and 300 visits a month, about 3.5 FTE. Combined with the 1,300 other field service orders a month, 8 field service reps is tight. The trigger object `payment` should be an unpaid bill. The 12,000 a month volume is unsourced.
- **cs-move-in-move-out:** meter-data-analyst is missing (for missing move-date reads), and business-customer is missing as a trigger. The 5,500 a month volume is unsourced.
- **cs-billing-exceptions:** settlement-analyst is missing (for retailer mismatches). With 10 billing-analyst FTE on exceptions and 2 on moves, only about 4 of the 16 analysts are left for the billing cycle. Either the 6,000 a month exception volume is high or the billing team is undersized.
- **cs-contact-centre:** the volume counts calls only. Emails and web forms, which I estimate at 1,500 to 2,500 a month, are not counted. Handling a call takes about 9 to 10 minutes, against the organisation file's note of about 6. Calls (27 FTE) and moves (11 FTE) use 38 of the 40 representatives, which leaves almost no one for written contacts.

### Batch edu-08: cs-meter-data-management, cs-billing, cs-meter-exchange, cs-ieso-settlement

- **`meter-technician` (12):** at 2,000 jobs a month, the exchange workflow needs about 21 FTE of hands-on time, and these 12 also staff the meter shop. Either the seal-expiry campaigns were partly contracted out (Hydro One uses a contractor) or the headcount is low.
- **`billing-analyst` (16):** the monthly billing run alone needs about 9 to 15 FTE. Adding billing exceptions (6,000 cases a month) makes 16 tight.
- **`cs-meter-data-management` triggers:** meter change records and field results are standing inputs to a daily cycle, not triggers. The cycle actually starts with the utility's own overnight meter read collection, not with the IESO.
- **`cs-ieso-settlement` triggers:** the case starts at month-end, and the IESO invoice arrives in the middle of it. Customer bills and retailer transactions are inputs.
- **Missing roles:**
  - `cs-meter-exchange` leaves out `work-planner` (routing jobs onto technicians' days) and `meter-data-analyst` (fixing rejected meter change records).
  - `cs-ieso-settlement` leaves out `finance-director`, the second signer on the IESO payment.
- **Missing system:** there is none for the IESO settlement portal. I added `ieso-portal` in the settlement workflow.
- **Missing outside party:** there is none for the bill print and mail vendor, so I modelled it as an outside step.

### Batch edu-09: fin-rate-application, fin-rrr-reporting, fin-procurement, fin-inventory-stores

- **Missing roles on processes.**
  - `fin-rrr-reporting`: lacks `asset-analyst` (reliability data from the OMS), `billing-analyst` (customer counts from the CIS), `vice-president` (RRR signing officer) and `ceo` (scorecard certification, RRR 2.2.2).
  - `fin-procurement`: lacks the requesting `project-manager`, `standards-engineer` (approves substitute materials) and `vice-president` (large awards).
  - `fin-inventory-stores`: lacks `apprentice-plt` (collects staged material) and `buyer` (expediting).
- **Missing links.**
  - `fin-rate-application` should take inputs from `ae-system-planning`, `ae-asset-condition-assessment` and `fin-regulatory-accounts`.
  - `fin-rrr-reporting` should take inputs from `cs-low-income-programs`, `cs-collections`, `ae-der-connection`, `cs-contact-centre` and `fin-regulatory-accounts`.
  - `fin-inventory-stores` is also started by outage-restoration and field-service requests, not only by the crew schedule.
- **Missing resource.** No forklift or yard loader is listed; I added 4 units marked `not_in_org_file`.
- **Volume and description.**
  - `fin-rrr-reporting`: the 1 to 4 a month range is about right. The RRR rules give about 21 returns a year (1.75 a month), but about 15 fall on April 30, so the work is very seasonal.
  - `fin-rate-application`: the description says the 2021 revenue requirement asked for was $216.6M. The OEB backgrounder gives a proposed 2021 base revenue requirement of $203.9M. These may be different measures (service versus base), so check before changing it.


### Batch edu-10: corp-health-safety, corp-public-safety-compliance

- **`corp-public-safety-compliance` description:** it says ESA audits compliance each year. Under the ESA audit guideline, the distributor hires an ESA-approved auditor every year and ESA reviews that auditor's report. The annual Declaration of Compliance must be signed by a professional engineer, director or officer.
- **`corp-public-safety-compliance` roles:** `lines-supervisor` (checks ESA findings in the field) and `vice-president` (signs the declaration) are missing. It also needs a link to `ops-work-scheduling` (`maintenance_work_order`) for repairs ESA asks for.
- **`corp-health-safety` triggers:** field audits, about 45% of cases, have no trigger; I added one from `ops-work-scheduling` (`crew_schedule`). Incidents also come from `ops-service-connection-work`, `ops-underground-construction` and `ops-station-maintenance`, which the map doesn't link.
- **`corp-health-safety` roles:** missing `hr-advisor` (WSIB Form 7, my assumption), `power-line-technician` (crew debriefs and witness statements) and `standards-engineer`.
- **Where public contacts come from:** they reach `corp-public-safety-compliance` only through `corp-health-safety`. In practice they come in from `ops-trouble-response` or `ops-locates`.
- **Volumes:** both are consistent with the evidence. That's 20 public contacts in 2021, and an all injury/illness frequency rate of 1.17 (lost workday severity 3.11), which comes to about 6 or 7 recordable injuries a year. The `corp-hse` headcount of 7 is consistent.


## oilfield-services-co

**Status 2026-11-24.** `tools/sync_map_from_workflows.py` and `tools/fixes_2026_11_24_oilfield.py` applied
the reports below. Trican's 2023 annual information form is the outside check: 1,124 full and part time
employees at the end of 2022. As for the utility, roles were resized to their documented work and the gap is
recorded here.

Applied:

- The sync added the missing links (35), role listings (81) and resource listings (36). It also added six
  resources the workflows needed: 40 shop service bays, iron test bays, and lab instruments.
- Cementing crews and bulk drivers are sized at 180 productive hours a month (`productive_hours_per_month`):
  they are on call, and nearly all their paid time is travel and job time. Cementing units now have about 400
  available hours a month and bulk cement trucks about 240, so 400 jobs a month fit the fleet.
- Six roles were raised to cover their documented work at 97% load:
  - completions design engineers, 16 to 24 (about 7 design cement slurries)
  - bulk plant operators, 15 to 21
  - cementing operators, 70 to 77
  - AP clerks, 10 to 13
  - buyers, 10 to 13
  - maintenance planners, 8 to 10
- Employees go from 1,350 to 1,387.
- Volumes now follow the workflows:
  - field tickets: 750 a month, one a day for frac and coiled tubing work
  - job calls: 580, leaving out frac wells that never come through dispatch
  - equipment moves: 18
- Surges were copied from the workflows for 20 processes.
- Other fixes:
  - The signed field ticket is no longer a trigger of its own preparation.
  - Incidents follow field headcount.
  - Pre-job hazard assessments are owned by field operations.

Still open:

- 1,387 employees is about 23% above Trican's 1,124. Frac crew sizes, contracted trucking or long workflow step
  times may explain it; the file's 1,350 was a tier C estimate from the start.
- The old `maintenance-shop` resource (5 shops) still sits beside the 40 service bays the workflows use.
- `frac-sand-operator`: the author estimated about 40 people, but the documented work fits the 30.
- `pump-technician` (25) is tight next to 75 heavy-duty mechanics.
- Other items:
  - Payroll is recorded as weekly although it runs biweekly; the format has no biweekly cadence.
  - There is no outside party for drug-testing labs.
  - The dual-fuel conversion claim in src2 is unchecked.

### Batch ofs-01: cs-tender-response, cs-msa-and-pricing-agreement, fo-dist-job-call-intake-and-dispatch, fo-dist-crew-scheduling-and-rotation

- **cs-tender-response:** it lists only the producer as receiver. The award should also go to `cs-msa-and-pricing-agreement` and `fo-frac-program-planning`. The input `prequal_record` from `hs-customer-safety-prequalification` is missing, and `frac-ops-manager` and `hse-coordinator` take part but are not listed.
- **cs-msa-and-pricing-agreement:** add `cs-tender-response` as a trigger. `pricing-analyst` and `risk-insurance-manager` are missing from roles. The executed agreement also goes to `fin-field-ticket-to-invoice`.
- **fo-dist-job-call-intake-and-dispatch:** the `total-jobs` driver includes about 50 frac wells a month that never come through job calls. Volume should be about 280/580/720. `cem-operator` and `ct-operator` drive the units but are not listed. Inputs `cement_program` (from `te-cement-slurry-design-and-lab-testing`) and `hos_exception` are missing.
- **fo-dist-crew-scheduling-and-rotation:** pad programs are the only trigger, but about 65% of rosters are cementing or coiled tubing on-call boards that follow dispatch bookings. `district-admin` compiles timesheets but is not listed. Links from `hr-onboarding` (`new_hire`) and to `hs-training-and-competency` (`training_enrolment`) are missing.
- **Headcounts:** I found none that the evidence contradicts.

### Batch ofs-02: fo-frac-program-planning, te-frac-treatment-design, fo-frac-rig-up-and-pressure-test, fo-dist-equipment-mobilization

- **Missing roles in `process_map`:**
  - `fo-dist-equipment-mobilization` lacks `dispatcher`, who does the permits and truck booking, and `field-mechanic`. It also lacks a link to `trucking-carrier` (`haul_order`).
  - `fo-frac-rig-up-and-pressure-test` lacks `frac-sand-operator` and `field-mechanic`.
  - `fo-frac-program-planning` lacks `frac-field-supervisor`, `logistics-coordinator` and `hse-advisor`.
  - `te-frac-treatment-design` lacks `lab-technician` and `completions-data-analyst`.
- **Missing link:** `cs-tender-response` should send a request to `te-frac-treatment-design`. About 30% of designs are tender designs, but today only `producer` triggers that process.
- **Volume:** I used 8-18-28 moves a month for `fo-dist-equipment-mobilization` instead of 8-20-30. That is one move per pad, about 18 a month, with fewer moves where a fleet works neighbouring pads. The other three volumes are kept as they are.
- **Direction of `move_permit`:** the org file shows the process sending it to `transport-regulator`, but the regulator issues the permit in reply to an application. I kept the org file's direction and said so in the assumptions.
- **Directive 083 source (`src9`):** the AER page now describes the November 2026 edition. The 2019-2022 period fell under earlier editions.

### Batch ofs-03: fo-frac-job-execution, fo-frac-onsite-proppant-and-fluid-management, fo-frac-screen-out-and-npt-handling, fo-frac-post-job-reporting

- **`fo-frac-screen-out-and-npt-handling`**:
  - Its roles leave out `frac-pump-operator` (who isolate and swap failed pumps) and `frac-data-tech` (who record stop and start times).
  - Its outputs lack a `field_ticket` link to `fo-dist-field-ticket-preparation`, although its own description says disputes over lost time hit field tickets.
  - Its outputs also lack a `repair_request` link to `em-field-breakdown-support`.
- **`fo-frac-onsite-proppant-and-fluid-management`**:
  - It has no inputs: no `chemical_delivery` from `sc-chemical-procurement-and-blending` and no `pad_program`, yet it manages chemical totes.
  - Its outputs lack `load_ticket` back to `sc-last-mile-sand-hauling` (for matching carrier invoices) and `qc_sample` to `te-fluid-and-proppant-quality-testing`.
- **`fo-frac-post-job-reporting`**: inputs lack `npt_report` (stoppages go into the report narrative) and `product_spec` from `chemical-supplier` (needed for the chemical disclosure).
- **Resource costs**: the `frac-pump` running cost overlaps the `frac-fleet` hourly cost, so they are counted twice if both are used. I used `frac-pump` only for pump swaps.
- **`frac-sand-operator` headcount**: 30 people is about 1.4 per shift to feed the blender and receive about 25 trucks a day. My tier C estimate is closer to 40.

### Batch ofs-04: fo-cem-bulk-blending-and-delivery, fo-cem-job-execution, te-cement-slurry-design-and-lab-testing, te-fluid-and-proppant-quality-testing

- **`cementing-unit`:** a unit is busy about 14 to 15 hours per job, counting travel and waiting. At 400 jobs a month, 16 to 17 units would each need about 350 to 450 available hours a month, not the mode of 200. Either the available hours or the job volume is too low.
- **`bulk-cement-truck`:** at 2 trucks per job and about 11 hours per trip, 400 jobs need roughly 8,800 truck-hours a month. 45 trucks at 190 hours give 8,550, so the fleet is fully used at ordinary volume and short in the winter peak.
- **`resources`:** `lab` is a whole laboratory, which one test does not tie up. I added consistometers, cement strength analysers, a sand crush press and a fluid test loop, each marked `not_in_org_file`.
- **Missing role:** there is no cement engineer. I used `design-engineer` (completions design engineer); about 7 of the 16 are needed for cement design.
- **Roles that take part but are missing from `process_map`:**
  - `dispatcher` and `lab-technician` in bulk blending.
  - `dispatcher` and `design-engineer` in the cement job.
  - `design-engineer` in quality testing.
- **`fo-cem-job-execution`:** it lists `bulk-truck-driver` and `bulk-cement-truck`. I counted them only in bulk blending to avoid double counting.
- **Missing links:**
  - `producer` should be a second source of slurry design requests (`technical_request`), about a quarter of them.
  - Bulk blending should send `load_ticket` to `fo-dist-field-ticket-preparation`.
  - Quality testing should send rejected chemical results to `sc-chemical-procurement-and-blending`.
- **Shipping link:** bulk blending sends `shipment_request` to `sc-dangerous-goods-shipping` on every job. Dry cement is not a regulated dangerous good, so this link should be occasional.

### Batch ofs-05: fo-ct-job-planning, fo-ct-job-execution, hs-pre-job-hazard-assessment, hs-incident-reporting-and-investigation

- **`fo-ct-job-planning`:**
  - Roles: missing `dispatcher` and `ct-operator`, who prepare the unit at the base.
  - Inputs: missing `iron_certificate` (blowout preventer and iron certificates) and producer well data.
  - Outputs: `ct_program` should also go to `hs-pre-job-hazard-assessment` and to `producer`.
- **`fo-ct-job-execution`:**
  - Roles: missing `design-engineer`; Trican says job data streams to its engineers in real time.
  - Resources: missing `nitrogen-unit` and `pickup-fleet`.
  - Volume: 80 jobs at about 1.9 days fits the file's 459 Q4 2019 operating days. STEP's 2021 utilisation suggests the true volume is nearer 60–80 a month.
- **`hs-pre-job-hazard-assessment`:**
  - Roles: missing the crews (`frac-pump-operator`, `cem-operator`, `ct-operator`, `nitrogen-operator`), `district-admin` and `hse-coordinator`.
  - Owner: supervisors in the service lines lead the assessments, not the HSE unit.
  - Volume: my count gives about 1,200 a month, so 1,100 is fine.
- **`hs-incident-reporting-and-investigation`:**
  - Roles: missing `cem-supervisor` and `ct-supervisor`.
  - Outputs: no link sending `spill_report` to `hs-environmental-spill-response`.
  - Driver: it is `null`; `field-headcount` would fit.

### Batch ofs-06: sc-proppant-procurement-and-rail-logistics, sc-last-mile-sand-hauling, sc-chemical-procurement-and-blending, sc-parts-procurement

- **`sc-parts-procurement`:**
  - Stock reorder points (from `sc-warehouse-and-inventory-management`, `replenishment_request`) are missing as a trigger; I estimate them at about a third of orders.
  - `warehouse-attendant` (receipts and hot-shot pickups) and `shop-manager` (approvals) are missing from the roles.
  - Hands-on time implies about 14 FTE against 10.7 stated. Buyers alone need about 8 FTE, so 10 `procurement-specialist` staff for all sand, chemical, cement, fuel and parts buying looks thin at 1,200 orders a month.
- **`sc-chemical-procurement-and-blending`:**
  - `design-engineer` (approving substitutes) and `frac-blender-operator` (receiving on location) are missing from the roles.
  - Inputs from `te-frac-treatment-design` and from the QC results of `te-fluid-and-proppant-quality-testing` are missing.
  - There is no base-stock replenishment trigger and no winter surge.
- **`sc-proppant-procurement-and-rail-logistics`:** `inventory-controller` is missing from the roles (it posts terminal receipts), and there is no output to `fin-accounts-payable` (`goods_receipt`).
- **`sc-last-mile-sand-hauling`:** the 38-tonne payload behind the 3,000 loads a month is unsourced. US pneumatic trucks carry about 21 tonnes (46,000 lb), so the load count is sensitive to truck type.
- **Duplicated work:**
  - The dangerous goods shipping document step in the chemical workflow repeats work in `sc-dangerous-goods-shipping`.
  - Goods receipt in the parts workflow repeats work in `sc-warehouse-and-inventory-management`.

  Both are noted in each file's `assumptions`.

### Batch ofs-07: em-preventive-maintenance, em-corrective-repair-and-pump-rebuild, em-pressure-iron-certification, em-field-breakdown-support

- **`maintenance-shop` resource:** 5 shops at about 500 hours a month gives 2,500 bay-hours. Preventive maintenance plus repairs need roughly 6,000 to 12,000 bay-hours a month, so I modelled about 40 service bays as a new resource. I also added 3 iron test bays, which the file lacks.
- **`em-corrective-repair-and-pump-rebuild` triggers:** the three listed triggers add up to about 170 work orders a month, against the 500 the file states. The missing source is crew defect write-ups from `fo-dist-yard-and-base-operations`, which I added at a 60% share.
- **Missing links:**
  - From repair to `fin-capital-planning-and-approval`, for units not worth repairing.
  - From field breakdown to `fo-frac-screen-out-and-npt-handling` (downtime records).
  - From `fo-frac-rig-down-and-move` to iron certification, since iron only comes home when fleets move.
- **Roles missing from process lists:**
  - `maintenance-planner` on all four processes, not just preventive maintenance.
  - `warehouse-attendant` and `yard-operator` on preventive maintenance and repair (warehouse on both, yard on preventive maintenance and iron).
  - `em-director` on repair approvals.
  - `shop-manager` and `equipment-engineer` on iron certification.
  - `dispatcher` and the frac field supervisor on field breakdowns.
  - The org has no dedicated iron shop technician role at all.
- **Headcounts:** shop work across these processes takes about 89 technician FTE out of 127 shop technicians. `pump-technician` at 25 is tight: about 22 FTE goes to fluid end and power end work and iron testing alone. That is low next to 75 heavy-duty mechanics, since pump work is the main maintenance load in pressure pumping.

### Batch ofs-08: fo-dist-field-ticket-preparation, fin-field-ticket-to-invoice, fin-accounts-receivable-and-collections, fin-accounts-payable

- **`fo-dist-field-ticket-preparation`:**
  - Volume should be about 750 tickets a month, not 640. Frac and coiled tubing work gets one ticket per day, while invoices are one per job.
  - Roles `frac-data-tech` and `district-manager` (who approves price overrides and non-billable work) are missing.
  - `customer-wellsite-supervisor` → `signed_field_ticket` is listed as a trigger, but it is what the process produces.
- **`fin-field-ticket-to-invoice`:**
  - Role `account-manager` is missing; it settles price disputes.
  - There is no link from `fin-accounts-payable` for the supplier invoices needed to rebill third-party costs.
- **`fin-accounts-receivable-and-collections`:**
  - Roles `billing-specialist` (credit memos) and `legal-counsel` (builders' liens) are missing.
  - About 1.5 FTE of `credit-analyst` time is needed for follow-ups, plus routine cash application. Five analysts covers that.
- **`fin-accounts-payable`:**
  - Roles `district-manager` (approves invoices with no purchase order), `accountant` (supplier set-up) and `treasury-ir-manager` (second release of bank payments) are missing.
  - The produces list lacks payments to the chemical, cement, fuel and gas suppliers.
  - Hands-on time implies about 12 `ap-clerk` FTE against a headcount of 10.
  - There is no system for scanning and reading supplier invoices. I added `ocr-capture`.

### Batch ofs-09: fin-payroll-processing, fin-month-end-close, hr-field-recruitment-and-hiring, hs-training-and-competency, em-equipment-manufacturing-and-upgrade

- **Missing roles in the process map:**
  - `fin-payroll-processing` lacks district-admin, treasury-ir-manager and accountant.
  - `fin-month-end-close` lacks billing-specialist, ap-clerk, inventory-controller, district-admin, district-manager and cfo.
  - `hr-field-recruitment-and-hiring` lacks hr-coordinator and the field supervisors. Cementing and coiled tubing managers also hire, not only frac-ops-manager.
  - `hs-training-and-competency` lacks the field supervisors who sign off competencies and the trainees, whose time is about 16 FTE.
  - `em-equipment-manufacturing-and-upgrade` lacks pump-technician, maintenance-planner, procurement-specialist, warehouse-attendant, shop-manager, field-mechanic and em-director. The frac-pump itself is also held out of service in the shop.
- **Missing links:**
  - Training is triggered by `fo-dist-crew-scheduling-and-rotation` (training_enrolment) and by recruitment (training_need).
  - Month-end close needs field tickets as an input.
  - No outside party exists for drug-testing labs.
- **Payroll cadence:** it is recorded as "weekly" but runs are biweekly; the format has no biweekly option.
- **Resource costs:** the frac-pump cost per hour is a pumping cost, and the maintenance-shop cost covers a whole shop. Applying them to shop work overstates the cost, so I left them off in that file.
- **Unchecked claims:** I could not confirm src2's "10 pumps converted to dual fuel in 2019"; I didn't open that source. The 2022 MD&A adds that a fifth Tier 4 fleet was approved for early 2024.
- **Volumes and headcounts:** all five agree with the evidence and my estimates.

