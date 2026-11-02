# Intervention continuation 003 review

## Result

**Passed.** I reviewed the amendment-003 runtime companion, its mock-only tests, the supplied test log, and the outcome-blind declaration logic. I made no live calls and inspected no intervention answers, arm caches, verification results, recovery rates, or efficacy summaries.

The verifier binds the exact predecessor amendment 002 and implementation, the 1,540-entry raw-cache inventory, the 1,200-job dispatch, the current 420-slot prefix, request plans, and post-loss process proof. It requires exactly the eight pending keys at dispatch positions 116–119 and 416–419, with one fresh and one repair request for each of four cases. It verifies that every prefix cache still has its recorded hash and key, each pending record has only start time and timeout telemetry, the timeout is 900 seconds, and the start predates the interruption. It also checks that the original four unavailable identities remain unchanged.

The continuation reuses the byte-bound amendment-002 closures and expands only their in-memory inventory and unavailable allowlist. The prior wrapper projects all eight rows as unavailable, preserves raw pending bytes, and refuses to send recorded keys. The live gate requires the exact 1,540-cache prefix and no completed manifest. A new exclusive start receipt is written before the first live request, which prevents restart even if a process stops before writing a new cache. The inherited dispatcher keeps four-request waves and stops after draining the current wave on any new error.

The declaration fixes the original 600 selected cases and 1,200 intervention slots, with 596 fully observed pairs, four unavailable whole pairs, eight unknown response cells, 256 hypothetical binary completions, and 780 unsent jobs. It leaves model, reasoning effort, prompt, feedback, selection, allocation, scoring, and request order unchanged. It binds the analysis plan, runtime and analysis source, tests, test logs, review files, predecessor amendment, raw cache prefix and process proof. It prohibits resubmitting recorded keys and requires another independent review after any new infrastructure failure.

The process proof distinguishes one inaccessible Windows service process from collector-owned workers. Its parent `services.exe` creation time predates the collector by four days, there are no collector descendants or isolated-work-directory matches, and the proof records the access limitation rather than claiming all Windows process details were readable.

## Test evidence

The supplied runtime log records 13 passing mock tests. Coverage includes exact prefix and unknown identity checks, preservation of pending bytes, dispatch only of unsent keys, current-wave drain and stop on a new error, detection of changed cache bytes, prevention of post-install reissue, a persistent one-shot start receipt, rejection of unresolved inaccessible owned candidates, an embedded predecessor hash check, and offline replay without CLI calls. A first log with one order-only assertion failure is retained separately; the finalized log passes after the assertion was made order-independent while still checking the exact four unsent request keys.

## Scope limits

This review does not execute the companion against the live study directory or independently prove operating-system state beyond the bound process evidence. The harmless WMI probe confirms that the WMI worker is in a distinct service job without `KILL_ON_JOB_CLOSE`, outside the controlled tool-like kill-on-close job, and completes after that owned job is closed. The test process assigned to the controlled job was alive immediately before close and exited within five milliseconds instead of its planned 300-second natural completion. This supports the specific job-isolation contract; it does not claim that the worker is outside all Windows jobs. No efficacy result has been accessed.
