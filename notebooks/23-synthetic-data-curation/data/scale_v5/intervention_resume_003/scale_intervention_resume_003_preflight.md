# Amendment 003 metadata-only preflight

## Result

**Passed.** I checked the public amendment package using its declaration, analysis plan, dispatch and request-plan metadata, review artifacts, process proof, frozen gate bindings, provenance hashes, and raw-cache byte hashes. I made no model or CLI calls. I did not parse or display model responses, verification flags, success rates, intervention rows, or the saved continuation stdout.

The public amendment is `6590b129a25b67b8d31a2c79a2027fee8f359e0e676e9c0245728eb7ffddadf5`. Its 1,540-entry inventory matches all 1,540 current gzip cache files byte-for-byte by SHA-256. All 24 amendment provenance files, 10 protected-file bindings, and all 38 original intervention-start gate bindings match. The amendment preserves the four unknown request identities from amendment 002 and adds four more, for eight unavailable response slots across four complete source pairs. Those identities match dispatch positions 116–119 and 416–419; no request key from the 780 unsent jobs appears in the recorded inventory.

The analysis plan retains 600 selected cases and 1,200 intervention slots. It sets 596 fully observed pairs, eight unknown response cells, 256 hypothetical binary completions, a 20,000-draw bootstrap with seed 246600, and the same all-completions McNemar claim rule. The runtime and analysis review sources match the packaged source snapshots, their supplied logs end with 13 and 8 passing tests respectively, the amendment is declared after the process-absence timestamp, and the final intervention manifest is absent.

The process proof reports no collector-owned workers, and documents one inaccessible Windows service process with a parent created before the collector. The bound launcher probe shows the controlled process was alive in a kill-on-close job before that job was closed; it exited within about five milliseconds instead of its planned 300-second natural exit. The WMI worker was outside that owned job, ran under the Windows service ancestry in a distinct job without `KILL_ON_JOB_CLOSE`, and completed after the owned job closed. This supports survival beyond the controlled parent job; it does not establish that the WMI worker is outside all Windows jobs.

## Limit

These checks establish the recorded request/cache accounting and the pre-call analysis plan. They cannot establish whether any of the eight pending requests physically started, returned an answer, or incurred billable usage. Keep those eight slots unavailable in the report, and stop for another independent review if any new infrastructure failure occurs.
