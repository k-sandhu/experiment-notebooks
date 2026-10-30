"""Post-hoc, rendered-source counterfactual audit of non-round original errors.
Read-only: does not call models or modify cached sources/responses.
"""
from __future__ import annotations
import hashlib, importlib.util, json
from fractions import Fraction
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parent/'experiment_notebooks'/'notebooks'/'23-synthetic-data-curation'
MAIN=REPO/'data'/'high_v4'/'main'
FAIL=HERE/'high_failure_material_review.json'
SOURCE_AUDIT=HERE/'high_main_source_review.json'
OUT_JSON=HERE/'high_nonround_error_review.json'
OUT_MD=HERE/'high_nonround_error_review.md'
AUDIT_MOD_PATH=HERE/'audit_high_rendered_sources.py'
spec=importlib.util.spec_from_file_location('high_text_audit_for_nonround',AUDIT_MOD_PATH)
TEXT=importlib.util.module_from_spec(spec); spec.loader.exec_module(TEXT)


def read_jsonl(path):
    return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s.strip()]


def selected_rows(packet):
    cutoff=packet['cutoff']
    by_id={}
    for row in packet['ledger']:
        if row['recorded_at'] <= cutoff:
            if row['event_id'] not in by_id or row['row_revision'] > by_id[row['event_id']]['row_revision']:
                by_id[row['event_id']]=row
    return by_id


def shipment_units(row, packet, uom_day=None, allocation_day=None):
    """Convert one visible SHIP row using date-specific P03/P04 rows."""
    uom_day=uom_day or row['occurred_at'][:10]
    allocation_day=allocation_day or row['occurred_at'][:10]
    sku=row['sku']; line=packet['target_line_id']
    uoms=[x for x in packet['uom'] if x['sku']==sku and x['uom']==row['uom'] and x['effective_from']<=uom_day]
    if row['uom']=='EA': factor=Fraction(1)
    elif uoms: factor=Fraction(max(uoms,key=lambda x:x['effective_from'])['units'])
    else: return None
    allocs=[x for x in packet['allocations'] if x['key']==row['allocation'] and x['effective_from']<=allocation_day]
    if not allocs:
        if row['allocation'] in ('-', 'DIRECT', 'NONE'): share=Fraction(1)
        else: return None
    else:
        target=[x for x in allocs if x['line_id']==line]
        share=Fraction(max(target,key=lambda x:x['effective_from'])['share'],100) if target else Fraction(0)
    return Fraction(row['quantity'])*factor*share


def shipment_basis(row, packet):
    """Return the visible selected UOM factor and line allocation for a movement."""
    day=row['occurred_at'][:10]
    uoms=[x for x in packet['uom'] if x['sku']==row['sku'] and x['uom']==row['uom'] and x['effective_from']<=day]
    factor=Fraction(1) if row['uom']=='EA' else (Fraction(max(uoms,key=lambda x:x['effective_from'])['units']) if uoms else None)
    allocations=[x for x in packet['allocations'] if x['key']==row['allocation'] and x['effective_from']<=day]
    if not allocations:
        share=Fraction(1) if row['allocation'] in ('-', 'DIRECT', 'NONE') else None
    else:
        eligible=[x for x in allocations if x['line_id']==packet['target_line_id']]
        share=Fraction(max(eligible,key=lambda x:x['effective_from'])['share'],100) if eligible else Fraction(0)
    return factor, share


def raw_row_explanation(row, units, packet):
    return {'event_id':row['event_id'],'row_revision':row['row_revision'],'quantity':row['quantity'],'uom':row['uom'],
            'allocation':row['allocation'],'occurred_at':row['occurred_at'],'recorded_at':row['recorded_at'],
            'state':row['state'],'target_dispatch_units_if_counted':str(units) if units is not None else None,
            'unit_factor':str(shipment_basis(row,packet)[0]) if shipment_basis(row,packet)[0] is not None else None,
            'target_line_allocation':str(shipment_basis(row,packet)[1]) if shipment_basis(row,packet)[1] is not None else None}


def run():
    failures=json.loads(FAIL.read_text(encoding='utf-8'))['original_outputs']['schema_valid_wrong_value_cases']
    pre=json.loads(SOURCE_AUDIT.read_text(encoding='utf-8'))
    pre_cases={x['case_id']:x for x in pre['selected_level_case_audit']}
    sources={x['case_id']:x for x in read_jsonl(MAIN/'potential_cases.jsonl')}
    special=[]
    for f in failures:
        q=f['wrong_values'].get('quantity_units')
        if not q: continue
        delta=q['observed']-q['expected']
        if delta in (-100,-200): continue
        case=sources[f['case_id']]
        if case['split']!='collection': continue
        packet=TEXT.parse_packet(case['document'])
        answer, detail=TEXT.derive_from_text(case['document'])
        audited=pre_cases[case['case_id']]
        source_sha=hashlib.sha256(case['document'].encode('utf-8')).hexdigest()
        if source_sha!=audited['document_sha256'] or answer!=case['gold'] or answer!=audited['independent_answer']:
            raise AssertionError(f"Source/preaudit mismatch for {case['case_id']}")
        ledger_events=detail['ledger']['events']
        returns=[e for e in ledger_events if e['kind']=='RETURN' and e['rule']=='return on referenced shipment']
        valid_shipments=[e for e in ledger_events if e['kind']=='SHIP' and e['rule']=='shipment']
        reversal_removed=[e for e in ledger_events if e['kind']=='SHIP' and e['rule']=='active reversal removes shipment']
        current=selected_rows(packet)
        # A return omitted from net dispatch yields a quantity delta equal to its negative net units.
        return_matches=[]
        for e in returns:
            if not ((delta<0 and e['net_units']==delta) or (delta>0 and e['net_units']==-delta)):
                continue
            source_row=current.get(e['event_id'])
            referenced=current.get(e['reference'])
            if referenced is None:
                raise AssertionError(f"Missing selected shipment referenced by return {e['event_id']}")
            factor, share=shipment_basis(referenced,packet)
            calculated=-Fraction(source_row['quantity'])*factor*share if factor is not None and share is not None else None
            if calculated != e['net_units']:
                raise AssertionError(f"Return arithmetic mismatch for {case['case_id']} {e['event_id']}: {calculated} != {e['net_units']}")
            return_matches.append({'return_event':e['event_id'],'net_units':e['net_units'],'referenced_shipment':e['reference'],
                'counterfactual':'omit the return' if delta<0 else 'count the return twice',
                'source_row':{k:source_row[k] for k in ('row_revision','quantity','uom','allocation','occurred_at','recorded_at','state')} if source_row else None,
                'source_shipment':raw_row_explanation(referenced,shipment_units(referenced,packet),packet),
                'return_uom_factor_from_original_shipment':str(factor),'target_line_share_from_original_shipment':str(share),
                'computed_net_return_units':str(calculated)})
        shipment_matches=[{'shipment_event':e['event_id'],'dispatch_units':e['net_units'],
                           'counterfactual':'double-count the event for a negative delta; omit it for a positive delta'}
                          for e in valid_shipments if (delta<0 and e['net_units']==-delta) or (delta>0 and e['net_units']==delta)]
        reversed_matches=[]; reversal_rows=[]
        for e in reversal_removed:
            row=current.get(e['event_id'])
            if row is None: continue
            units=shipment_units(row,packet)
            item=raw_row_explanation(row,units,packet)
            reversal_rows.append(item)
            if units is not None and ((delta<0 and units==-delta) or (delta>0 and units==delta)):
                controls=[]
                for control in packet['ledger']:
                    if control['kind']!='REVERSAL' or control['reference']!=e['event_id'] or control['recorded_at']>packet['cutoff']:
                        continue
                    chosen_control=current.get(control['event_id'])
                    if chosen_control is not None and chosen_control['row_revision']==control['row_revision'] and chosen_control['state']=='POSTED' and chosen_control['occurred_at']<=packet['cutoff']:
                        controls.append({'event_id':chosen_control['event_id'],'row_revision':chosen_control['row_revision'],
                            'reference':chosen_control['reference'],'state':chosen_control['state'],'occurred_at':chosen_control['occurred_at'],
                            'recorded_at':chosen_control['recorded_at']})
                reversed_matches.append({'shipment':item,'active_reversal_controls':controls,
                    'counterfactual':'count a shipment that the active reversal removes'})
        # A stale movement revision is a separate counterfactual. Only compare posted,
        # timely rows for an event currently counted as a target shipment.
        revision_matches=[]
        for event in valid_shipments:
            eid=event['event_id']; selected=current.get(eid)
            if selected is None: continue
            correct=shipment_units(selected,packet)
            if correct is None: continue
            prior=[r for r in packet['ledger'] if r['event_id']==eid and r['recorded_at']<=packet['cutoff'] and r['row_revision']<selected['row_revision']
                   and r['kind']=='SHIP' and r['state']=='POSTED' and r['order_id']==packet['target_order_id'] and r['occurred_at']<=packet['cutoff']]
            for old in prior:
                alt=shipment_units(old,packet)
                if alt is not None and Fraction(correct)-alt==delta:
                    revision_matches.append({'event_id':eid,'older_revision':raw_row_explanation(old,alt,packet),
                        'selected_revision':raw_row_explanation(selected,correct,packet),
                        'counterfactual':'use the older event row instead of the selected highest recorded revision'})
        returns_total=sum(e['net_units'] for e in returns)
        implied_dispatch=packet['target_order_id']
        # Verify the independently reduced open balance directly from its visible terms and ledger.
        open_balance=answer['quantity_units']
        source_net_dispatch=sum(e['net_units'] for e in detail['ledger']['events'])
        resolved_ordered=detail['resolved_terms']['ordered_units']
        if resolved_ordered-source_net_dispatch != open_balance:
            raise AssertionError(f"Rendered-text ledger sum mismatch in {case['case_id']}")
        observed=q['observed']
        special.append({'case_id':case['case_id'],'family':case['family'],'content_hash':case['content_hash'],
            'document_sha256':source_sha,'model':f['model'],'sample':f['sample'],'split':case['split'],
            'target_order_id':packet['target_order_id'],'target_line_id':packet['target_line_id'],'target_sku':packet['target_sku'],
            'expected_quantity_units':open_balance,'observed_quantity_units':observed,'observed_minus_expected':delta,
            'ordered_units':resolved_ordered,'net_target_dispatch_units':source_net_dispatch,
            'selected_logical_event_count':detail['ledger']['selected_event_count'],'accepted_return_total_net_units':returns_total,
            'individual_return_omission_matches':return_matches,'single_shipment_contribution_matches':shipment_matches,
            'active_reversal_inclusion_matches':reversed_matches,'active_reversed_shipments':reversal_rows,
            'wrong_prior_revision_matches':revision_matches,
            'ignore_all_returns_counterfactual_delta':returns_total,
            'source_answer_evidence_audit_passed':audited['gold_match'] and audited['evidence_gold_match'],
            'model_answer':f['response']['answer']})
    # The seven named cases are the complete collection subset outside the two repeated offsets.
    expected_special=7
    if len(special)!=expected_special:
        raise AssertionError(f"Expected {expected_special} non-round collection cases; found {len(special)}")
    return {'status':'complete','description':'Post-hoc counterfactual arithmetic; never an inference about model reasoning.',
      'delta_definition':'observed quantity_units minus independently derived expected quantity_units',
      'non_round_collection_case_count':len(special),'distribution':{str(d):sum(1 for x in special if x['observed_minus_expected']==d) for d in sorted({x['observed_minus_expected'] for x in special})},
      'cases':special,'limitation':'Matching a counterfactual arithmetic path does not establish that the model used that path.'}


def write_markdown(report):
    lines=['# Non-round quantity errors in the original collection','',
      'This post-hoc review isolates the seven frozen collection responses whose quantity delta is outside the repeated −100/−200-unit offsets. Delta means observed quantity minus the answer independently derived from the literal packet. I reparsed each exact saved document with the independent Fraction reader, checked it against the pre-audited source record, and recomputed open balance from current ordered demand minus the net allocated dispatch ledger.','',
      'These are counterfactual arithmetic checks only. An exact numerical match shows that a hypothetical omitted, duplicated or wrongly revised event could produce the same delta. It does not show that the model made that mistake. The report does not describe any counterfactual as the model’s reasoning.','',
      '| Case | Family | Expected open units | Model output | Delta |','|---|---|---:|---:|---:|']
    for c in report['cases']:
        lines.append(f"| `{c['case_id']}` | {c['family']} | {c['expected_quantity_units']:,} | {c['observed_quantity_units']:,} | {c['observed_minus_expected']:+,} |")
    lines += ['', '## What the visible ledger permits us to say','']
    for c in report['cases']:
        delta=c['observed_minus_expected']
        lines += [f"### `{c['case_id']}`: {delta:+,} units",'',
          f"The text-derived answer is {c['expected_quantity_units']:,} open units: {c['ordered_units']:,} ordered minus {c['net_target_dispatch_units']:,} net allocated dispatched. The packet has {c['selected_logical_event_count']} selected logical events and its accepted returns total {c['accepted_return_total_net_units']:,} net units."]
        if c['individual_return_omission_matches']:
            matches=', '.join(f"{m['counterfactual']} `{m['return_event']}` ({m['source_row']['quantity']} units × {m['return_uom_factor_from_original_shipment']} units per {m['source_shipment']['uom']} × {m['target_line_share_from_original_shipment']} target-line share = {m['net_units']:+,} net units; references `{m['referenced_shipment']}`)" for m in c['individual_return_omission_matches'])
            lines.append(f"A return counterfactual matches the delta exactly: {matches}. The factor and allocation come from the selected original shipment and its occurrence date. This is a numerical match, not a claim about the model’s process.")
        if c['active_reversal_inclusion_matches']:
            for m in c['active_reversal_inclusion_matches']:
                s=m['shipment']; controls=', '.join(x['event_id'] for x in m['active_reversal_controls']) or 'the active reversal control'; lines.append(f"A second exact counterfactual is to count `{s['event_id']}` despite its active reversal `{controls}`. The visible row is {s['quantity']} {s['uom']} at allocation `{s['allocation']}`; {s['quantity']} × {s['unit_factor']} units per {s['uom']} × {s['target_line_allocation']} target-line share = {s['target_dispatch_units_if_counted']} units, exactly the magnitude of the error. The packet’s POSTED reversal means the row contributes zero under the stated rule.")
        if c['single_shipment_contribution_matches']:
            matches=', '.join(f"{m['shipment_event']} ({m['dispatch_units']:,} units)" for m in c['single_shipment_contribution_matches'])
            lines.append(f"A single-event arithmetic match also exists for {matches}. Counting such a valid shipment twice would produce the negative delta; omitting it would produce the positive delta. The cache alone cannot tell whether either happened.")
        if c['wrong_prior_revision_matches']:
            lines.append('A prior-revision counterfactual matches the delta:')
            for m in c['wrong_prior_revision_matches']:
                lines.append(f"Using {m['event_id']} revision {m['older_revision']['row_revision']} ({m['older_revision']['target_dispatch_units_if_counted']} target-line units) instead of selected revision {m['selected_revision']['row_revision']} ({m['selected_revision']['target_dispatch_units_if_counted']} units) changes the open-balance result by the observed delta.")
        if not (c['individual_return_omission_matches'] or c['active_reversal_inclusion_matches'] or c['single_shipment_contribution_matches'] or c['wrong_prior_revision_matches']):
            lines.append(f"No single accepted return, counted shipment, active-reversed shipment or earlier shipment revision tested here matches {delta:+,} units. Ignoring every accepted return would shift this answer by {c['ignore_all_returns_counterfactual_delta']:+,} units, which does not by itself reproduce the observed output. I leave the remaining discrepancy unexplained.")
        lines += ['', '']
    lines += ['## Reading these examples','',
      'Four of the seven deltas are −72 units, one is −144, one is +100, and one is −544. The source audit confirms all seven packets are internally solvable and their stored answers and evidence requirements match the rendered text. The −72 examples have exact single-return omission arithmetic; one also has an exact active-reversal inclusion alternative. The −144 example has a matching active-reversed shipment and valid-shipment amount. These alternatives overlap, so they do not identify which operation, if any, occurred. The +100 and −544 examples have no tested single-event match; for the −544 case, ignoring all returns gives −444, leaving a further −100-unit gap.','',
      'The repeated −100 and −200 errors are more common in the full collection, but this small set shows that other ledger-scale discrepancies occur. It does not establish a shared cause. The complete arithmetic trace, response values, row IDs, document hashes, and counterfactual candidate lists are in [high_nonround_error_review.json](high_nonround_error_review.json).','']
    OUT_MD.write_text('\n'.join(lines),encoding='utf-8',newline='\n')

if __name__=='__main__':
    result=run()
    OUT_JSON.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    write_markdown(result)
    print(json.dumps({'status':result['status'],'cases':result['non_round_collection_case_count'],'distribution':result['distribution']},indent=2))
