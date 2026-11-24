def response_subtype(response):
    text = response_diagnostics(response)
    failed = bool(response.get('error') or response.get('returncode', 0) or response.get('status', 200) != 200)
    if quota_message(response):
        return 'usage_quota_limit'
    if re.search(r"OS can.t spawn worker thread|os error 1450|Insufficient system resources", text, re.I):
        return 'local_resource_exhaustion'
    if failed and re.search(r'acceptable.use|\bAUP\b|usage.policy|Details:\s*\[bio\]|safety.{0,20}(block|filter)|content[_ ]filter', text, re.I):
        return 'provider_safety_block'
    if 'Timeout' in str(response.get('error')):
        return 'timeout'
    if response.get('status') == 429 or (failed and re.search(r'rate.?limit|too many requests', text, re.I)):
        return 'rate_limit'
    if response.get('finish_reason') == 'length':
        return 'token_limit'
    if failed:
        return 'transport_error'
    body = response.get('text', '').strip()
    if not body:
        return 'empty'
    if re.search(r'\b(I cannot|I can.t|unable to)\s+(evaluate|choose|assist|comply|check)', body, re.I):
        return 'refusal'
    return 'returned_text'


def attempt_location(request, historical=False):
    purpose = request.get('purpose', '')
    parts = purpose.split(':')
    if historical:
        return 'source33', 'original_baseline'
    if len(parts) >= 2 and parts[0] in ('development', 'selection', 'confirmation'):
        return parts[0], parts[1]
    return 'probe', parts[0] or 'unspecified'


def build_attempt_audit(cache, outcomes_frame):
    names = {value['model']: name for name, value in JUDGES.items()}
    final_keys, used_attempt_keys = set(), set()
    choices_by_key = {}
    if not outcomes_frame.empty:
        for row in outcomes_frame.to_dict('records'):
            final_keys.update(json.loads(row['cache_keys']))
            used_attempt_keys.update(json.loads(row['attempt_keys']))
            for key in json.loads(row['cache_keys']):
                choices_by_key[key] = json.loads(row['choices'])
    rows = []

    def add(row, disposition, number, returned=True):
        request = row['request']
        response = row.get('response', {})
        historical = bool(row.get('origin'))
        stage, method = attempt_location(request, historical)
        backend = request['backend']
        usage = response.get('usage') or {}
        estimate = cli_estimate(row)[0] if returned and backend == 'codex' else None
        cost = response.get('cost') if returned and backend == 'openrouter' else None
        reservation = float(response.get('unpriced_reservation', row.get('reservation_usd', 0)) or 0)
        choices = choices_by_key.get(row['key'])
        if choices is None:
            choices = load(DATA/'recommendation.json')['choices'] if method == 'recommended' and (DATA/'recommendation.json').exists() else [method]
        readings = {reader: parse_format(row, reader == 'strict', choices) for reader in ['strict', 'lenient']} if returned else {}
        rows.append(dict(
            attempt_id=f"{row['key']}:{disposition}:{number}", key=row['key'],
            origin='33' if historical else '36', stage=stage, method=method,
            judge=names.get(request['model'], request['model']), model=request['model'], backend=backend,
            purpose=request.get('purpose', ''), disposition=disposition, returned=returned,
            retry_index=request.get('attempt', 0), is_retry=request.get('attempt', 0) > 0,
            used_as_final_component=row['key'] in final_keys,
            used_in_outcome_attempt_keys=row['key'] in used_attempt_keys,
            diagnostic_subtype=response_subtype(response) if returned else 'interrupted_no_reply',
            strict_unreadable_type=readings['strict']['unreadable_type'] if returned else 'unobserved_interrupted',
            lenient_unreadable_type=readings['lenient']['unreadable_type'] if returned else 'unobserved_interrupted',
            openrouter_known_usd=float(cost) if cost is not None else None,
            openrouter_usage_missing=backend == 'openrouter' and cost is None,
            openrouter_known_or_reserved_usd=float(cost) if cost is not None else reservation if backend == 'openrouter' else 0.,
            cli_estimated_usd=float(estimate) if estimate is not None else None,
            cli_usage_missing=backend == 'codex' and not bool(usage),
            seconds=response.get('latency_s') if returned else None,
            started_at=response.get('started_at', row.get('at')),
            client_configuration='source33_original' if historical else 'file_stdio_tokio2' if request.get('client_stdio') else 'legacy_or_http',
        ))

    for number, row in enumerate(cache.values()):
        add(row, 'cached_return', number)
    for number, row in enumerate(NONFINAL):
        add(row, row.get('disposition', 'nonfinal_return'), number)
    interrupted_path = DATA/'interrupted_attempts.json'
    if interrupted_path.exists():
        for number, record in enumerate(load(interrupted_path)['attempts']):
            request = record.get('request') or dict(
                model=record['model'], backend=record['backend'], purpose=record.get('purpose', ''), attempt=0)
            add(dict(key=record['key'], request=request, at=record.get('at'),
                     reservation_usd=record.get('reservation_usd', 0)),
                'interrupted_no_reply', number, False)
    audit = pd.DataFrame(rows)
    audit.to_csv(DATA/'attempt_audit.csv', index=False)
    groups = ['origin', 'stage', 'judge', 'method', 'backend']
    counts = audit.groupby(groups, dropna=False).agg(
        started_attempts=('attempt_id', 'size'), returned_attempts=('returned', 'sum'),
        retry_attempts=('is_retry', 'sum'), final_component_attempts=('used_as_final_component', 'sum'),
        openrouter_known_usd=('openrouter_known_usd', 'sum'),
        openrouter_usage_missing=('openrouter_usage_missing', 'sum'),
        openrouter_known_or_reserved_usd=('openrouter_known_or_reserved_usd', 'sum'),
        cli_estimated_usd=('cli_estimated_usd', 'sum'), cli_usage_missing=('cli_usage_missing', 'sum'),
        returned_seconds=('seconds', 'sum')).reset_index()
    counts['unreturned_attempts'] = counts.started_attempts - counts.returned_attempts
    counts.to_csv(DATA/'physical_attempt_counts.csv', index=False)
    diagnostics = audit.groupby(groups + ['disposition', 'diagnostic_subtype'], dropna=False).size().rename('attempts').reset_index()
    diagnostics.to_csv(DATA/'transport_diagnostics.csv', index=False)
    reading_rows = []
    for reader in ['strict', 'lenient']:
        view = audit[audit.returned].copy()
        view['unreadable_type'] = view[reader+'_unreadable_type'].replace('', 'readable')
        view['reader'] = reader
        reading_rows.append(view.groupby(groups + ['reader', 'unreadable_type'], dropna=False).size().rename('attempts').reset_index())
    pd.concat(reading_rows, ignore_index=True).to_csv(DATA/'request_reading_summary.csv', index=False)
    return audit, counts, diagnostics


def outcome_status(row, reader, suffix=''):
    if row[reader+'_unreadable_type'+suffix]:
        return 'unreadable'
    if row[reader+'_undecided'+suffix]:
        return 'undecided'
    return 'correct' if row[reader+'_score'+suffix] == 1 else 'wrong'


def enrich_paired_reports(frame):
    transitions, additions = [], []
    if frame.empty:
        return pd.DataFrame(), pd.DataFrame()
    for (stage, judge, method), group in frame.groupby(['stage', 'judge', 'method']):
        if method == 'baseline':
            continue
        baseline = frame[(frame.stage == stage) & (frame.judge == judge) & (frame.method == 'baseline')]
        paired = group.merge(baseline, on='item_id', suffixes=('_m', '_b'))
        for reader in ['strict', 'lenient']:
            before = [outcome_status(row, reader, '_b') for row in paired.to_dict('records')]
            after = [outcome_status(row, reader, '_m') for row in paired.to_dict('records')]
            common = dict(stage=stage, judge=judge, method=method, reader=reader)
            counts = Counter(zip(before, after))
            for (old, new), count in counts.items():
                transitions.append(dict(**common, baseline_status=old, method_status=new, items=count))
            extra = dict(common)
            for status in ['correct', 'wrong', 'unreadable', 'undecided']:
                extra['baseline_'+status] = before.count(status)
                extra['method_'+status] = after.count(status)
            extra.update(full_corrections=counts['wrong', 'correct'],
                         full_regressions=counts['correct', 'wrong'],
                         unreadable_to_correct=counts['unreadable', 'correct'],
                         wrong_to_undecided=counts['wrong', 'undecided'],
                         correct_to_undecided=counts['correct', 'undecided'])
            additions.append(extra)
    transition_frame = pd.DataFrame(transitions)
    transition_frame.to_csv(DATA/'paired_transitions.csv', index=False)
    additions_frame = pd.DataFrame(additions)
    paired_base = paired_table(frame)
    if not paired_base.empty:
        paired_base = paired_base.merge(additions_frame, on=['stage', 'judge', 'method', 'reader'], how='left')
        paired_base.to_csv(DATA/'paired_comparisons.csv', index=False)
    return paired_base, transition_frame


def unary_reports(frame):
    grade_rows, comparison_rows = [], []
    items_by_id = {item['item_id']: item for item in all_items}
    if frame.empty:
        return pd.DataFrame(), pd.DataFrame()
    for row in frame.to_dict('records'):
        if 'single_answer' not in json.loads(row['choices']):
            continue
        item = items_by_id[row['item_id']]
        metadata = json.loads(row['component_meta'])
        for reader in ['strict', 'lenient']:
            parsed = json.loads(row[reader+'_component_reads'])
            observed = {}
            for meta, answer, cache_key in zip(metadata, parsed, json.loads(row['cache_keys'])):
                original = meta['answer']
                expected = 'pass' if original == item['better'] else 'fail'
                readable = not bool(answer['unreadable_type'])
                observed[original] = answer['winner'] if readable else None
                grade_rows.append(dict(
                    stage=row['stage'], judge=row['judge'], method=row['method'], reader=reader,
                    family=row['family'], item_id=row['item_id'], candidate=original, cache_key=cache_key,
                    expected=expected, observed=answer['winner'], readable=readable,
                    correct=readable and answer['winner'] == expected,
                    wrong=readable and answer['winner'] != expected,
                    unreadable_type=answer['unreadable_type'], confidence=answer['confidence']))
            better = observed[item['better']]
            worse = observed['B' if item['better'] == 'A' else 'A']
            if better is None or worse is None:
                pattern = 'unreadable'
            elif better == worse:
                pattern = 'both_pass' if better == 'pass' else 'both_fail'
            else:
                pattern = 'only_better_passes' if better == 'pass' else 'only_worse_passes'
            comparison_rows.append(dict(
                stage=row['stage'], judge=row['judge'], method=row['method'], reader=reader,
                family=row['family'], item_id=row['item_id'], pattern=pattern,
                score=row[reader+'_score'], correct=row[reader+'_score'] == 1,
                wrong=row[reader+'_wrong'], undecided=row[reader+'_undecided'],
                unreadable=bool(row[reader+'_unreadable_type'])))
    grades = pd.DataFrame(grade_rows)
    comparisons = pd.DataFrame(comparison_rows)
    if grades.empty:
        return grades, comparisons
    grades.to_csv(DATA/'unary_grades.csv', index=False)
    comparisons.to_csv(DATA/'unary_comparisons.csv', index=False)
    summary_rows = []
    grouping = ['stage', 'judge', 'method', 'reader', 'family', 'expected']
    for group, subset in grades.groupby(grouping):
        meta = dict(zip(grouping, group))
        n = len(subset)
        readable = int(subset.readable.sum())
        correct = int(subset.correct.sum())
        passed = int(subset.observed.eq('pass').sum())
        low, high = wilson(passed, readable)
        summary_rows.append(dict(**meta, n=n, readable=readable, correct=correct,
                                 wrong=int(subset.wrong.sum()), unreadable=n-readable,
                                 accuracy=correct/n, readable_accuracy=correct/readable if readable else None,
                                 pass_rate_readable=passed/readable if readable else None,
                                 pass_ci_low=low, pass_ci_high=high))
    pd.DataFrame(summary_rows).to_csv(DATA/'unary_grade_summary.csv', index=False)
    patterns = comparisons.groupby(['stage', 'judge', 'method', 'reader', 'pattern']).agg(
        items=('item_id', 'size'), correct=('correct', 'sum'), wrong=('wrong', 'sum'), undecided=('undecided', 'sum'),
        unreadable=('unreadable', 'sum'), total_score=('score', 'sum')).reset_index()
    patterns.to_csv(DATA/'unary_pattern_summary.csv', index=False)
    selection_rows = comparisons[(comparisons.stage == 'selection') &
                                 (comparisons.reader == 'lenient') &
                                 (comparisons.method == 'single_answer')]
    if not selection_rows.empty:
        categories = ['both_pass', 'both_fail', 'only_better_passes', 'only_worse_passes', 'unreadable']
        labels = ['Both pass', 'Both fail', 'Only better passes', 'Only worse passes', 'Unreadable']
        colors = ['#8bb4db', '#dfad87', '#77b6a0', '#c57c86', '#aaaaaa']
        hatches = ['', '//', 'xx', '..', '++']
        pivot = selection_rows.groupby(['judge', 'pattern']).size().unstack(fill_value=0).reindex(index=JUDGES, columns=categories, fill_value=0)
        fig, ax = plt.subplots(figsize=(10, 4.8))
        y = np.arange(len(pivot))
        left = np.zeros(len(pivot))
        for category, label, color, hatch in zip(categories, labels, colors, hatches):
            values = pivot[category].to_numpy()
            ax.barh(y, values, left=left, label=label, color=color, hatch=hatch,
                    edgecolor='white', linewidth=.7)
            for index, count in enumerate(values):
                if count >= 6:
                    ax.text(left[index]+count/2, index, str(int(count)), va='center', ha='center')
            left += values
        both_pass = int(pivot.both_pass.sum())
        ax.set_yticks(y, pivot.index)
        ax.invert_yaxis()
        ax.set_xlabel('Collected selection items per judge')
        ax.set_title(f'Both answers pass in {both_pass} of {len(selection_rows)} unary comparisons')
        ax.legend(loc='upper center', bbox_to_anchor=(.5, -.18), ncol=2, frameon=False)
        fig.tight_layout()
        fig.savefig(FIG/'unary_grading_patterns.png')
        plt.show()
    return grades, comparisons


def supplemental_reports(frame, cache):
    calls_before = new_calls
    items_by_id = {item['item_id']: item for item in all_items}
    checked_scores = 0
    for row in frame.to_dict('records'):
        item = items_by_id[row['item_id']]
        assert row['better'] == item['better']
        choices = json.loads(row['choices'])
        components = json.loads(row['component_meta'])
        for reader in ['strict', 'lenient']:
            reads = [parse_format(cache[key], reader == 'strict', choices)
                     for key in json.loads(row['cache_keys'])]
            result = aggregate(reads, components, choices)
            score = 0. if result['unreadable_type'] else .5 if result['undecided'] else float(result['winner'] == item['better'])
            assert score == row[reader+'_score'], (row['item_id'], row['method'], reader)
            checked_scores += 1
    attempts, counts, diagnostics = build_attempt_audit(cache, frame)
    paired, transitions = enrich_paired_reports(frame)
    grades, unary = unary_reports(frame)
    if not frame.empty:
        primary = summarize(frame, ['stage', 'judge', 'method'])
        current = counts[counts.origin == '36'].drop(columns=['origin', 'backend'])
        enriched = primary.merge(current, on=['stage', 'judge', 'method'], how='left')
        for column in ['started_attempts', 'returned_attempts', 'retry_attempts',
                       'unreturned_attempts', 'openrouter_usage_missing', 'cli_usage_missing']:
            enriched[column] = enriched[column].fillna(0).astype(int)
        enriched.to_csv(DATA/'condition_audit.csv', index=False)
    record = dict(at=now(), scored_reader_rows_checked=checked_scores,
                  physical_attempt_records=len(attempts),
                  historical_source_attempts=int(attempts.origin.eq('33').sum()),
                  notebook36_started_attempts=int(attempts.origin.eq('36').sum()),
                  new_calls_before=calls_before, new_calls_after=new_calls,
                  primary_scores_unchanged=True, no_model_calls=True,
                  scope='Descriptive postcollection diagnostics; not used by selection rule',
                  files=['attempt_audit.csv', 'physical_attempt_counts.csv', 'transport_diagnostics.csv',
                         'request_reading_summary.csv',
                         'paired_transitions.csv', 'paired_comparisons.csv', 'condition_audit.csv',
                         'unary_grades.csv', 'unary_grade_summary.csv', 'unary_comparisons.csv', 'unary_pattern_summary.csv'])
    assert new_calls == calls_before
    save(DATA/'supplemental_reporting_audit.json', record)
    for name in ['replay_audit.json', 'live_complete.json']:
        path = DATA/name
        if path.exists():
            existing = load(path)
            existing['figures'] = sorted(path.name for path in FIG.glob('*.png'))
            existing['supplemental_reporting_audit'] = record
            save(path, existing)
    handoff = ROOT/'HANDOFF.md'
    if handoff.exists():
        marker = '## Additional reporting audits'
        body = handoff.read_text(encoding='utf-8').split(marker)[0]
        extra = [marker, json.dumps(record, indent=2),
                 'physical_attempt_counts.csv counts every cached return, nonfinal return and interrupted start exactly once. Source 33 is historical, not new spend. Cached source retries are included. Unknown charges and usage are marked explicitly; known sums are lower bounds when usage is absent.',
                 'paired_comparisons.csv now includes baseline/method correct, wrong, unreadable and undecided counts on matched items. fixed/broke retain their original score-change meaning. full_corrections/full_regressions distinguish wrong-to-correct from partial-credit tie transitions; paired_transitions.csv preserves all transitions.',
                 'unary_grade_summary.csv separates wrong individual grades from unreadable grades; unary_pattern_summary.csv counts both-pass, both-fail and separating verdicts. unary_grading_patterns.png is the descriptive error-analysis figure.',
                 'Physical attempts by stage, model and condition:',
                 markdown_table(counts),
                 'Transport diagnostic subtypes:', markdown_table(diagnostics)]
        for name in ['source_retry_manifest.json', 'client_resource_smoke.json']:
            path = DATA/name
            if path.exists():
                extra += [name, '```json\n'+json.dumps(load(path), indent=2)+'\n```']
        handoff.write_text(body+'\n\n'+'\n\n'.join(extra)+'\n', encoding='utf-8')
    return record, counts, diagnostics, paired


supplement_audit, physical_counts, transport_counts, paired_with_counts = supplemental_reports(outcomes, CACHE)
display(physical_counts)
display(transport_counts[transport_counts.diagnostic_subtype.ne('returned_text')])
display(paired_with_counts)
print(json.dumps(supplement_audit, indent=2))
