# High-v4 original failure material audit

Audit status: **complete**. This is a read-only review of cached requests and responses; it makes no model calls.

## Source integrity

The prepared source set has 264 cases. Each request document is checked against that source set and the selected-level preaudit, then reparsed with the independent rendered-text Fraction reader. The task instruction hash is `0d74782473e7b1b8079f76f004aa87d0d2341bb8c37e4210b5b85acf3d7567b8`. There are 0 source/preaudit discrepancies.

## Cached originals

The cache currently contains 354 request files: 309 generation/retry requests and 45 repair requests. Of these, 264 of 264 original sample-0 calls have terminal `turn.completed` responses; 0 requests across stages remain incomplete. Intervention retries are not counted as original failures. The failure list includes only schema-valid original responses with at least one answer value different from the independent text-derived answer. It does not infer why a model returned that value.

| Case | Model | Sample | Field | Expected from source | Observed |
|---|---|---:|---|---:|---:|
| `account-56fd10ed56500a83af17` | gpt-6.1-sol | 0 | `quantity_units` | 91504 | 91432 |
| `account-bc7c8bb6170cfa4520c2` | gpt-6.1-sol | 0 | `quantity_units` | 90879 | 90779 |
| `account-0edc30e0d7e9affdbe30` | gpt-6.1-sol | 0 | `quantity_units` | 90418 | 90318 |
| `account-20f906a986d33a72c939` | gpt-6.1-sol | 0 | `quantity_units` | 90753 | 90653 |
| `account-2bef75a9b16fdd86a083` | gpt-6.1-sol | 0 | `quantity_units` | 90671 | 90571 |
| `account-5877bbf619e7f5280f7b` | gpt-6.1-sol | 0 | `quantity_units` | 88012 | 87912 |
| `account-6096dbb0d4b1dff23766` | gpt-6.1-sol | 0 | `quantity_units` | 88232 | 88160 |
| `account-528aa9951e8b4f4a0049` | gpt-6.1-sol | 0 | `quantity_units` | 89827 | 89727 |
| `account-6fed1adc842836fb4e78` | gpt-6.1-sol | 0 | `quantity_units` | 91409 | 91309 |
| `account-3e17d6a73a9f22cd29d7` | gpt-6.1-sol | 0 | `quantity_units` | 88514 | 88314 |
| `account-1cd2c1dc96c81b94ed32` | gpt-6.1-sol | 0 | `quantity_units` | 91011 | 90911 |
| `account-2d00cd667712b0a7a987` | gpt-6.1-sol | 0 | `quantity_units` | 87807 | 87707 |
| `account-81ae28dafc747351824c` | gpt-6.1-sol | 0 | `quantity_units` | 87801 | 87729 |
| `account-3d30b5051585ca6d95c9` | gpt-6.1-sol | 0 | `quantity_units` | 91468 | 91368 |
| `account-ca690cd116b4ec7c81db` | gpt-6.1-sol | 0 | `quantity_units` | 90524 | 90424 |
| `account-32a516f8796e5fb2abf0` | gpt-6.1-sol | 0 | `quantity_units` | 88543 | 88343 |
| `account-490f59b02c4f4da6c75e` | gpt-6.1-sol | 0 | `quantity_units` | 90468 | 90268 |
| `account-cef264bdbcc8139e0c0b` | gpt-6.1-sol | 0 | `quantity_units` | 90347 | 90247 |
| `account-2d7bc0d18b99a44388e8` | gpt-6.1-sol | 0 | `quantity_units` | 91123 | 91023 |
| `account-1be460677c4e8c24128c` | gpt-6.1-sol | 0 | `quantity_units` | 91835 | 91735 |
| `account-5f017d944672443a8051` | gpt-6.1-sol | 0 | `quantity_units` | 91559 | 91359 |
| `account-efc19a32f1ecc24a24b1` | gpt-6.1-sol | 0 | `quantity_units` | 87409 | 87309 |
| `account-9c3fa4f97055b7fb2cb5` | gpt-6.1-sol | 0 | `quantity_units` | 90380 | 90480 |
| `account-7d2061cdf08d078b6e22` | gpt-6.1-sol | 0 | `quantity_units` | 90490 | 90390 |
| `account-f415500cab640a6b597c` | gpt-6.1-sol | 0 | `quantity_units` | 87732 | 87632 |
| `account-07f06481e8d04eed7aa6` | gpt-6.1-sol | 0 | `quantity_units` | 90975 | 90775 |
| `account-d9d72de7388ce56ac9bb` | gpt-6.1-sol | 0 | `quantity_units` | 88316 | 88116 |
| `account-fec037740b6811d6ce5e` | gpt-6.1-sol | 0 | `quantity_units` | 88026 | 87482 |
| `account-2efbb8adf8cc35777885` | gpt-6.1-sol | 0 | `quantity_units` | 91907 | 91807 |
| `account-d6789405445707ad4e0c` | gpt-6.1-sol | 0 | `quantity_units` | 89152 | 89052 |
| `account-fbe34fbd343002dd8ca9` | gpt-6.1-sol | 0 | `quantity_units` | 89970 | 89870 |
| `account-4d8733233adfbb136cb4` | gpt-6.1-sol | 0 | `quantity_units` | 87991 | 87891 |
| `account-d241e3325a75cd3ad130` | gpt-6.1-sol | 0 | `quantity_units` | 87418 | 87318 |
| `account-ff063de4c5006a400e7d` | gpt-6.1-sol | 0 | `quantity_units` | 88043 | 87971 |
| `account-b725d241dccca0d390f5` | gpt-6.1-sol | 0 | `quantity_units` | 88403 | 88203 |
| `account-83c602f0946172f48ebd` | gpt-6.1-sol | 0 | `quantity_units` | 90637 | 90537 |
| `account-fe6aaf920d601621b82a` | gpt-6.1-sol | 0 | `quantity_units` | 88586 | 88486 |
| `account-2d282a312db253242ca6` | gpt-6.1-sol | 0 | `quantity_units` | 87815 | 87715 |
| `account-9d23f9539977f7f02372` | gpt-6.1-sol | 0 | `quantity_units` | 87319 | 87219 |
| `account-72bd3f5e4216d77ab54c` | gpt-6.1-sol | 0 | `quantity_units` | 88929 | 88829 |
| `account-8cb652029e7c81f2095f` | gpt-6.1-sol | 0 | `quantity_units` | 88138 | 88038 |
| `account-3103d8f1bf640574d96a` | gpt-6.1-sol | 0 | `quantity_units` | 87641 | 87541 |
| `account-f3fc844a1c0b64528f2d` | gpt-6.1-sol | 0 | `quantity_units` | 87400 | 87256 |
| `account-8c14690c4df5e3cba67b` | gpt-6.1-sol | 0 | `quantity_units` | 90778 | 90678 |
| `account-3f40f1d351fc27b0cbb0` | gpt-6.1-sol | 0 | `quantity_units` | 88864 | 88764 |
| `account-47d7cde4bb041e82d491` | gpt-6.1-sol | 0 | `quantity_units` | 90139 | 90039 |
| `account-9d7a6ce1dd1483ccc9dd` | gpt-6.1-sol | 0 | `quantity_units` | 89048 | 88948 |
| `account-114b7e001470a28afde9` | gpt-6.1-sol | 0 | `quantity_units` | 90307 | 90107 |
| `account-3a533b72612eb7af54ae` | gpt-6.1-sol | 0 | `quantity_units` | 90520 | 90420 |

Every row can be traced to its cache filename and source document SHA-256 in the adjacent JSON report. The response object and full source-derived comparison are retained there.

## Selection and feedback

A frozen selection file is present; 45 value-failure cases are selected. All selected IDs match independently confirmed sample-0 value failures, all selected source hashes match the frozen source documents, and the pre-intervention failed-field flags match the actual wrong-value fields: True. The selected-case flag objects contain field names and a schema Boolean only; they contain no expected answer values or calculation traces.
The cache contains 45 fresh retries and 45 feedback repairs across the frozen selected cases. Every fresh retry has no feedback field. For every repair, the audit checks that the feedback repeats the exact original sample-0 response and contains only generic wrong-field, schema-failure, and evidence-failure flags; those flags match the source-verified original errors and contain no expected answer values or calculation traces. It also checks that request hashes and prompts match their cached full requests. The repair-feedback checks passed for 45 of 45 repairs; both intervention arms cover exactly the frozen selection: True.

## Audit boundaries

This audit checks the request payload, response schema, values against the exact rendered sources, and feedback contents. A numerical mismatch is an observed result, not evidence of a particular hidden calculation. Pending, timed-out, malformed, or otherwise unusable responses are listed as incomplete or response issues, never recast as value errors.
