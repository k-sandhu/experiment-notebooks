# Reviewed interventions runner

The reviewed interventions-only runner passes static inspection at SHA-256 `5bf45d3c…e7ca6b58`. The test file is `854a1462…0c7c15dd`, with 15 mocked tests; the parent reports they pass. I inspected the tests and their log but did not execute them. This review made no live calls, read no intervention outcomes and changed no study data.

Before dispatch, the runner verifies the separate intervention-start declaration and its byte bindings for the runner, approved continuation companion, amendment, source review, runner review, protocol, allocation, original manifest and selection. It requires passing review artifacts with zero model/live calls and a completed originals phase. It then loads the exact archived continuation companion into a fresh namespace, installs the reviewed dispatcher, and calls only the frozen interventions phase.

Live mode is explicit and only allows an initial launch. It refuses a completed intervention manifest and scans the main cache for any existing repair, fresh-retry, or unknown-stage cache, preventing a live restart or re-query. Offline replay remains available. The approved dispatcher’s bypass condition is limited to the original collection’s single reviewed capacity failure; intervention-arm errors do not qualify. New errors drain the current four-request wave, write a separate stop receipt, preserve the original stop, and prevent later waves. Progress output omits answer and efficacy fields.

I found no blocking issues. The report records the exact runner, test and test-log hashes for the parent’s separate pre-intervention declaration.
