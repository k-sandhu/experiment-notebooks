def export_selection_examples():
    import gzip
    import json
    import pathlib

    import pandas as pd

    root = ROOT
    data = root / 'data'
    frame = pd.read_csv(data / 'outcomes.csv').fillna('')
    selection = frame[frame.stage.eq('selection')]
    chosen = []


    def pick(label, rows, count=1, paired=False):
        for row in rows.sort_values(['item_id', 'judge', 'method']).head(count).to_dict('records'):
            chosen.append(dict(label=label, **row))
            if paired:
                baseline = selection[(selection.item_id == row['item_id']) & (selection.judge == row['judge']) & selection.method.eq('baseline')].iloc[0].to_dict()
                chosen.append(dict(label=label + '_baseline', **baseline))


    pick('end_to_end_pair', selection[selection.method.eq('baseline') & selection.family.eq('code') & selection.lenient_score.eq(1)])
    pick('sol_instruction_baseline_failure', selection[selection.judge.eq('Sol') & selection.method.eq('baseline') & selection.lenient_wrong])
    joined = selection.merge(selection[selection.method.eq('baseline')][['item_id', 'judge', 'lenient_score']], on=['item_id', 'judge'], suffixes=('', '_baseline'))
    pick('luna_worked_high_effort_fix', joined[joined.judge.eq('Luna') & joined.family.eq('worked') & joined.method.eq('effort_high') & joined.lenient_score.eq(1) & joined.lenient_score_baseline.eq(0)], paired=True)
    pick('sol_high_effort_regression', joined[joined.judge.eq('Sol') & joined.method.eq('effort_high') & joined.lenient_wrong & joined.lenient_score_baseline.eq(1)], paired=True)
    pick('granite_high_effort_unreadable', selection[selection.judge.eq('Granite 8B') & selection.method.eq('effort_high') & selection.lenient_unreadable_type.ne('')])
    pick('sol_solve_first_unreadable', selection[selection.judge.eq('Sol') & selection.method.eq('solve_first') & selection.lenient_unreadable_type.ne('')], count=4)
    pick('sol_strict_analysis_recovered', selection[selection.judge.eq('Sol') & selection.method.eq('reason_first') & selection.strict_unreadable_type.ne('') & selection.lenient_score.eq(1)])
    pick('granite_native_unreadable', selection[selection.judge.eq('Granite 8B') & selection.method.eq('native_schema') & selection.lenient_unreadable_type.ne('')])
    pick('single_answer_unreadable', selection[selection.method.eq('single_answer') & selection.lenient_unreadable_type.ne('')], count=3)
    unary = pd.read_csv(data / 'unary_comparisons.csv').fillna('')
    wrong_both_fail = unary[unary.stage.eq('selection') & unary.reader.eq('lenient') & unary.pattern.eq('both_fail') & unary.wrong]
    for row in wrong_both_fail.sort_values(['item_id', 'judge']).head(1).to_dict('records'):
        pick('both_fail_confidence_wrong', selection[selection.item_id.eq(row['item_id']) & selection.judge.eq(row['judge']) & selection.method.eq('single_answer')], paired=True)
    needed = {key for row in chosen for key in json.loads(row['cache_keys'])}
    cache = {}
    for path in [data / 'cache_imported.jsonl.gz', data / 'cache_requests.jsonl']:
        stream = gzip.open(path, 'rt', encoding='utf-8') if path.suffix == '.gz' else path.open(encoding='utf-8')
        with stream:
            for line in stream:
                if line.strip():
                    row = json.loads(line)
                    if row['key'] in needed:
                        cache[row['key']] = row
    assert set(cache) == needed
    items = {}
    with (data / 'from_33/exam_v1.jsonl').open(encoding='utf-8') as stream:
        ids = {row['item_id'] for row in chosen}
        for line in stream:
            item = json.loads(line)
            if item['item_id'] in ids:
                items[item['item_id']] = item
    for row in chosen:
        row['item'] = items[row['item_id']]
        row['requests_and_replies'] = [cache[key] for key in json.loads(row['cache_keys'])]
        row['example_selection'] = 'First stable selection item matching the stated category; includes all four Sol solve-first unreadables. Examples do not alter the frozen analysis.'
    (data / 'narrative_examples_selection.json').write_text(json.dumps(chosen, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    columns = ['label', 'item_id', 'judge', 'method', 'family', 'better', 'lenient_score', 'lenient_unreadable_type', 'strict_unreadable_type']
    pd.DataFrame(chosen)[columns].to_csv(data / 'narrative_example_index.csv', index=False)


def export_editorial_tables():
    import datetime, json, pandas as pd
    root = ROOT
    data = DATA
    load = lambda name: json.loads((data / name).read_text(encoding='utf-8'))
    summary = pd.read_csv(data / 'summary.csv').fillna('')
    paired = pd.read_csv(data / 'paired_comparisons.csv').fillna('')
    family = pd.read_csv(data / 'family_summary.csv').fillna('')
    unreadable = pd.read_csv(data / 'unreadable_summary.csv').fillna('')
    attempts = pd.read_csv(data / 'attempt_audit.csv').fillna('')
    spend = load('spend.json')


    def table(frame):
        cols = list(frame.columns)
        def fmt(value):
            if isinstance(value, float):
                return f'{value:.8g}'
            return str(value).replace('|', '/').replace('\n', ' ')
        return '| ' + ' | '.join(cols) + ' |\n| ' + ' | '.join('---' for _ in cols) + ' |\n' + ''.join('| ' + ' | '.join(fmt(v) for v in row) + ' |\n' for row in frame.itertuples(index=False, name=None))


    selection = summary[(summary.stage == 'selection') & (summary.reader == 'lenient')]
    p = paired[(paired.stage == 'selection') & (paired.reader == 'lenient') & (paired.method != 'reference')]
    eligibility = []
    for method, group in p.groupby('method'):
        positive = int((group.ci_low > 0).sum())
        cheaper = bool((group.mean_dollar_difference <= 0).all() and (group.mean_dollar_difference < 0).sum() >= 2 and (group.gain >= 0).all())
        eligibility.append(dict(method=method, judges_with_positive_95_lower_bound=positive,
                                cheaper_without_observed_loss=cheaper, eligible=positive >= 2 or cheaper,
                                mean_gain=float(group.gain.mean())))
    eligibility = pd.DataFrame(eligibility)
    assert not eligibility.eligible.any() and load('recommendation.json')['choices'] == []
    eligibility.to_csv(data / 'recommendation_eligibility.csv', index=False)
    headlines = summary[summary.stage.isin(['selection', 'confirmation'])].copy()
    headlines['source_file'] = 'summary.csv'
    headlines.to_csv(data / 'headline_numbers.csv', index=False)
    rankings = []
    for (stage, method), group in headlines.groupby(['stage', 'method']):
        def ranks(reader, field):
            part = group[group.reader.eq(reader)].sort_values([field, 'judge'], ascending=[False, True])
            return '; '.join(f"{row.judge}={getattr(row, field):.6f} (readable {row.readable}/{row.n})" for row in part.itertuples())
        rankings.append(dict(stage=stage, method=method, strict=ranks('strict', 'accuracy'),
                             lenient=ranks('lenient', 'accuracy'), readable_only_lenient=ranks('lenient', 'readable_accuracy')))
    pd.DataFrame(rankings).to_csv(data / 'reader_ranking_diagnostics.csv', index=False)

    current = attempts[attempts.origin.astype(str).eq('36')].copy()
    points = []
    for row in current.to_dict('records'):
        start = datetime.datetime.fromisoformat(row['started_at'])
        seconds = row['seconds'] if isinstance(row['seconds'], (int, float)) else 0
        points.append((start, start + datetime.timedelta(seconds=seconds)))
    points.sort()
    episodes = []
    for start, end in points:
        if not episodes or (start - datetime.datetime.fromisoformat(episodes[-1]['last_observation'])).total_seconds() > 3600:
            episodes.append(dict(first_send=start.isoformat(), last_observation=end.isoformat(), physical_sends=1))
        else:
            episodes[-1]['last_observation'] = max(end, datetime.datetime.fromisoformat(episodes[-1]['last_observation'])).isoformat()
            episodes[-1]['physical_sends'] += 1
    pause = datetime.datetime.fromisoformat(load('resume_record.json')['pause_at'])
    episodes[0]['last_observation'] = max(pause, datetime.datetime.fromisoformat(episodes[0]['last_observation'])).isoformat()
    for episode in episodes:
        episode['span_hours'] = (datetime.datetime.fromisoformat(episode['last_observation']) - datetime.datetime.fromisoformat(episode['first_send'])).total_seconds() / 3600
    wall = dict(episodes=episodes, sum_observed_episode_hours=sum(x['span_hours'] for x in episodes),
                grouping='New-notebook physical sends; a gap exceeding one hour starts a new episode. Endpoints use known return durations; manual October 30 stop extends its episode endpoint.',
                caveat='Observed collection-window spans, not pure inference time or total engineering work. Excludes long pauses, including the owner-reported 25-day gap. Interrupted calls without usage/latency remain explicitly unknown.')
    (data / 'collection_episodes.json').write_text(json.dumps(wall, indent=2) + '\n', encoding='utf-8')

    events = [json.loads(line) for line in (data / 'run_log.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    milestones = []
    for event in events:
        kind = event['event']
        if kind == 'retry':
            continue
        milestones.append(dict(at=event['at'], event=kind,
                               detail=json.dumps({key: event[key] for key in ['status', 'tag', 'profile', 'model', 'purpose', 'choices', 'error'] if key in event}, ensure_ascii=False)[:350]))
    pd.DataFrame(milestones).to_csv(data / 'protocol_milestones.csv', index=False)



export_selection_examples()
export_editorial_tables()
