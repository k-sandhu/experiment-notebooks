# Notebook 33 source snapshot

Source commit supplied by owner: `cf854303`, branch `add-33-judge-exam`.

Read-only source: `D:/projects/experiment_notebooks/worktrees/33-judge-exam/notebooks/judges/33-judge-exam/data/`.

Hashes normalize CRLF to LF, as notebook 33 does. This is a copy of the supplied checkout, with freeze comparisons recorded individually below.

| File | SHA-256 (LF) | Matches 33 freeze |
|---|---|---|
| exam_v1.jsonl | c1c88cfb0bfee1ea0724579c1324f1b0903170afd8ccebec5c183de7c4fe5ae0 | True |
| freeze_record.json | 603e60d7accf0f8bcc908ce64c652b2df1879c7dd99b8b1a3f18136dcdda8ec2 | None |
| prompt_templates.json | 62e9ee0b98b60c306c3e2453b062602de1d9c1901838c64ac31a443c51831f0b | True |
| reading_rules_v1.py | d21f4f77671fd8dbe5825c123f48b26d9ff5e4c9474046ba7986ee64340b6a14 | True |
| models.json | c44f7a2a755b256bc0493f619787af78e5f108d477c0ce61c87ead7547e6151c | True |
| date_provenance.json | e40e3bc7ae9e7b4fba89aa3a081ec1f052d7a2949f42edf9a40eca8bc9510d7e | True |
| judgments.csv | 99dafe3e94441e4939b490aae537a3c0b29006c68067170418cd99d428762347 | None |
| granite-4.2-8b_endpoints.json | 185a30d21dffe7145abe9ec982c1d8ef342efb53b15d97e7b73520ff8c8e4ede | None |
| transport_v1.py | 8fabfc6f5d4ba0e1f82eb10524d81914eb86f86157f8f544936134a922350c16 | True |
| generator_v1.py | 33f49fbea214d0d9e8b8e7755619e95df32e1731630377a82180b0d4f5ab42ab | True |
| evaluation_v1.py | ad9fdf5c37c46b327bd4ab22c6344d5b939976f93f4d9a5147e9c7fb510ad6b3 | True |

## Derived response archive

`baseline_cache.jsonl.gz` contains the 1440 final cache records joined from notebook 33’s gzip archive by the Sol/Luna/Granite test judgments. It preserves each request, reply and key. The whole source archive SHA-256 (binary bytes) is `83596a8899816247771b6d6d1b416a66350c7dc6a87ccd55ad471e7aba3c493e`; the selected archive SHA-256 (binary bytes) is `da60844ca46026a91843c9328dcf7bf788c6635fb67db18ea39ec970331a5e91`. Full extraction details and the working-copy hash are in `../imported_cache_manifest.json`. The source’s entire archive is not duplicated.

## Earlier attempts for reused judgments

`prior_baseline_attempts.jsonl.gz` contains 27 earlier attempts joined by the same model and purpose as the 1440 final reused replies. Source path and extraction details are in `../source_retry_manifest.json`. SHA-256 of the gzip bytes: `ddbe7a8da1572e19e7e4519d67a175624e29370ffa19ae6dff0fa99d8f30d15a`. Working cache is extended with these unmodified records and origin metadata; the final-reply copy above remains unchanged.

## Worktree relocation and verification

On 2026-11-24 the source checkout is at `D:/projects/experiment_notebooks/worktrees/33-judge-exam/notebooks/judges/33-judge-exam/data`, still at owner-supplied commit `cf854303`. All copied source-file hashes were rechecked against this checkout and its LF-normalized freeze hashes; see `../resume_source_verification.json`. Earlier logs and immutable cache records retain historical locations. The earlier-attempt recovery used the notebook 34 backup before relocation; its historical path in the extraction manifest is provenance, not an active dependency.
