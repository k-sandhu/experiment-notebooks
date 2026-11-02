# V4 level-2 pilot source review

Reviewed 2026-10-26 from the completed cached responses available at review time. I read the model-visible packet from the pilot's saved source JSONL and confirmed it exactly matches the cached request's `documents` string. The packet hash is `ab61d23132d0c6c47618bebe646810f0644a52159587a7cfa22f66cd63c08e21`; the cached request key is `7ed3b9754b76f126bebaf2b0e0758b4a09a3a94dc0dd5130557d585715ee2234`. I then recomputed the answer from P01-P06 with the independent `Fraction` reader, whose derivation does not read the stored answer key.

## Case `account-42e7ad7c8c3683f346b9`

The packet targets PO-206220, line L03, SKU GSK-983. P02's AP-09 is the governing ordered-quantity row: it is approved, applies to L03, has authority 2, revision 5, and is effective and recorded before the noon UTC cutoff. It yields 94,717 ordered units. AP-03 has the same line, authority and effective timestamp but revision 4, so AP-09 wins. AP-04 has lower authority; AP-05 was recorded after cutoff; AP-06 is future-effective; AP-08 is unapproved. AP-02 supplies PLAN-C at line scope, which takes precedence over the order-wide PLAN-B default. AP-10 supplies the current requested ship date, November 13. P01 supplies EUR and active status.

The rendered P06 history resolves to 86 logical events after selecting the highest revision recorded by cutoff. The independent calculation sums 6,583 target-line dispatched units across the included shipment events and subtracts 520 units from accepted returns. It excludes other-order rows, selected VOID rows, a future-occurring row and shipments removed by active reversals. Net dispatch is 6,063, so the open balance is `94,717 - 6,063 = 88,654` individual units.

The resolved PLAN-C tier is the 94,000-unit row. Its price is `8,520 / 10 × (1 - 550/10,000) × (1 - 1,250/10,000) + 2.75 + 9.75/10 - 0.75 = 707.4725` cents, rounded half-up to 707 cents. The independent answer is `{order_id: PO-206220, sku: GSK-983, quantity_units: 88654, unit_price_cents: 707, currency: EUR, ship_date: 2026-11-13, status: active}`. The source audit finds no answer-key or required-evidence mismatch.

The cached response has valid JSON/schema and returns `quantity_units: 88554`, 100 below the source-derived answer. Its other six values are correct. Its citations include all required source groups; the extra P01 context on quantity and price is allowed by the instructions. Thus the observed error is a quantity-value error, not a schema or citation-only rejection. The response alone does not reveal how the model obtained that number, so this review makes no claim about its internal calculation.

## Other completed level-2 cache entries

At the time of review, seven of eight level-2 requests had terminal answers and one remained pending. Independent comparisons found three completed quantity-value failures: the case above (`88554` versus `88654`), `account-7a4281d037871e80827b` (`87892` versus `87992`), and `account-417f3eef36f372cc6111` (`91358` versus `91458`). Each had valid schema, correct other six values and sufficient citations. The other four completed cases were exact on all seven values and had sufficient citations. The eighth case, `account-0989be767d71a08b19f1`, had no terminal response and is not classified as an answer or failure here.

The three observed quantity discrepancies share a numerical offset of 100 units. This is a description of these cached outputs only; it does not establish a common cause. All level-2 packets in the frozen pilot source set passed the independent rendered-text answer and evidence audit. These cases are synthetic and do not establish performance on real procurement records.
