# Intervention continuation runtime review

## Result

**Passed.** I reviewed only the runtime companion, its mock-only tests, and the supplied test log. I did not read intervention arm caches, request outputs, or efficacy results, and made no model calls. I did not rerun the tests; the supplied log records 15 passing mock tests in 36.954 seconds.

The verifier binds the intervention gate, source freeze, prior continuation amendment, dispatch, request plans, analysis plan, process proof, and 1,240-entry raw-cache inventory. It verifies that all prior raw cache hashes still match, only the first 120 of 1,200 intervention positions exist, there are 116 terminal arm attempts and four exact pending attempts, and the four exceptions are precisely dispatch positions 116–119 forming two complete source pairs with one request per arm.

The approved pending rows are projected as `outcome_unavailable` with no parsed response, using only their recorded start time and timeout. The projection does not rewrite cache bytes or invent a finish time, elapsed duration, return code, usage, events, or answer. The dispatch wrapper keeps four-worker wave order, permits only the prior approved original-capacity exception and these four exact unavailable identities, drains the current wave before writing a distinct stop file on any new error, and does not dispatch later waves after a stop. The explicit `--live` path checks the exact pre-interruption cache inventory and blocks automatic restart or a completed-run restart. The notebook namespace test verifies installation without executing an external companion file.

The supplied mock log records passing coverage for hash/prefix verification, exact pair mapping, pending projection immutability, no resubmission, new-error stop behavior, preservation of the old stop file, four-worker scope, replay, and notebook-namespace installation.

## Issues

None found in the reviewed implementation or its mock tests.

## Scope limits and runtime contract

This review did not run the companion against the actual study directory or verify the final amendment's live request metadata. The coordinator's preflight remains necessary. The overlay puts a nonempty explicit interruption marker in `transport_error` to satisfy the existing result-row contract; that marker must describe controller interruption and unavailable outcome only, not a model or provider failure.
