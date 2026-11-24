"""Independent audit of v4 model-visible text using SQL and Decimal arithmetic.

This module does not import the fixture parser, constructor, or reference reducer.
It derives the answer from the rendered text and compares with gold only afterward.
"""
import datetime as _hma_dt
import decimal as _hma_decimal
import hashlib as _hma_hashlib
import json as _hma_json
import re as _hma_re
import sqlite3 as _hma_sqlite


def high_material_answer(document):
    lines = document.splitlines()

    def header(label):
        found = [s.split(': ', 1)[1] for s in lines if s.startswith(label + ': ')]
        if len(found) != 1:
            raise ValueError('Nonunique or absent header: ' + label)
        return found[0]

    def table(name):
        start, end = 'BEGIN TABLE ' + name, 'END TABLE ' + name
        if lines.count(start) != 1 or lines.count(end) != 1:
            raise ValueError('Nonunique or absent table: ' + name)
        a, b = lines.index(start), lines.index(end)
        keys = lines[a + 1].split(' | ')
        rows = []
        for s in lines[a + 2:b]:
            values = s.split(' | ')
            if len(keys) != len(values):
                raise ValueError('Incomplete source row: ' + name)
            rows.append(dict(zip(keys, values)))
        if not rows:
            raise ValueError('Empty source table: ' + name)
        return rows

    def utc(value):
        if not _hma_re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', value):
            raise ValueError('Unexpected timestamp representation')
        return _hma_dt.datetime.fromisoformat(value.replace('Z', '+00:00'))

    target_order, target_line = header('Target-order'), header('Target-line')
    cutoff, issued = header('Cutoff-UTC'), header('Issued-UTC')
    utc(cutoff); utc(issued)
    p01, p02, p03, p04, p05, p06 = [table('P0' + str(i)) for i in range(1, 7)]
    target = [r for r in p01 if r['line_id'] == target_line]
    if len(target) != 1 or target[0]['sku'] != header('Target-SKU'):
        raise ValueError('Target line/SKU mismatch')
    target = target[0]
    winners = {}
    terms = {}
    for field in ['ordered_units', 'price_plan', 'currency', 'ship_date']:
        options = []
        defaults = {'price_plan': 'Default-price-plan', 'currency': 'Default-currency', 'ship_date': 'Default-ship-date'}
        if field in defaults:
            options.append(((0, 0, utc(issued), 0), header(defaults[field]), 'ORDER'))
        if target[field] != 'INHERIT':
            options.append(((1, 0, utc(issued), 0), target[field], target_line))
        for row in p02:
            if row['line_id'] not in ['ALL', target_line] or row['approved'] != 'YES' or row[field] == 'INHERIT':
                continue
            if max(utc(row['recorded_at']), utc(row['effective_at'])) > utc(cutoff):
                continue
            options.append(((int(row['line_id'] == target_line), int(row['authority']), utc(row['effective_at']), int(row['revision'])), row[field], row['approval_id']))
        top = max(r[0] for r in options)
        eligible = [r for r in options if r[0] == top]
        if len({r[1] for r in eligible}) != 1:
            raise ValueError('Conflicting term: ' + field)
        terms[field] = eligible[0][1]
        winners[field] = eligible[0][2]
    terms['ordered_units'] = int(terms['ordered_units'])

    db = _hma_sqlite.connect(':memory:')
    try:
        # Tables contain only independently parsed visible strings. SQL implements
        # the revision, eligibility and dated-reference joins separately.
        for name, rows in [('ledger', p06), ('uom', p03), ('alloc', p04)]:
            keys = list(rows[0])
            assert all(_hma_re.fullmatch(r'[a-z_]+', k) for k in keys)
            db.execute('CREATE TABLE ' + name + '(' + ','.join(k + ' TEXT' for k in keys) + ')')
            db.executemany('INSERT INTO ' + name + ' VALUES(' + ','.join('?' for _ in keys) + ')', [[r[k] for k in keys] for r in rows])
        db.execute('CREATE TABLE settings(cutoff TEXT, target_order TEXT, target_line TEXT)')
        db.execute('INSERT INTO settings VALUES(?,?,?)', [cutoff, target_order, target_line])
        db.executescript('''
        CREATE VIEW selected AS
          SELECT DISTINCT l.* FROM ledger l, settings p
          WHERE l.recorded_at <= p.cutoff
            AND NOT EXISTS (SELECT 1 FROM ledger newer
                WHERE newer.event_id=l.event_id AND newer.recorded_at<=p.cutoff
                  AND CAST(newer.row_revision AS INTEGER)>CAST(l.row_revision AS INTEGER));
        CREATE VIEW active AS
          SELECT l.* FROM selected l,settings p
          WHERE l.state='POSTED' AND l.order_id=p.target_order AND l.occurred_at<=p.cutoff;
        CREATE VIEW shipments AS
          SELECT l.* FROM active l WHERE l.kind='SHIP'
          AND NOT EXISTS(SELECT 1 FROM active rv WHERE rv.kind='REVERSAL' AND rv.reference=l.event_id);
        CREATE VIEW movements AS
          SELECT event_id,quantity,sku,uom,allocation,occurred_at,1 AS sign FROM shipments
          UNION ALL
          SELECT rt.event_id,rt.quantity,s.sku,s.uom,s.allocation,s.occurred_at,-1 AS sign
          FROM active rt JOIN shipments s ON s.event_id=rt.reference WHERE rt.kind='RETURN';
        ''')
        query = '''
        SELECT m.event_id,m.sign,CAST(m.quantity AS INTEGER),CAST(u.units AS INTEGER),
               COALESCE(CAST(a.share AS INTEGER),0),m.occurred_at,u.effective_from,a.effective_from
        FROM movements m
        JOIN uom u ON u.sku=m.sku AND u.uom=m.uom
          AND u.effective_from=(SELECT MAX(u2.effective_from) FROM uom u2
              WHERE u2.sku=m.sku AND u2.uom=m.uom AND u2.effective_from<=SUBSTR(m.occurred_at,1,10))
        CROSS JOIN settings p
        LEFT JOIN alloc a ON a.key=m.allocation AND a.line_id=p.target_line
          AND a.effective_from=(SELECT MAX(a2.effective_from) FROM alloc a2
              WHERE a2.key=m.allocation AND a2.effective_from<=SUBSTR(m.occurred_at,1,10))
        ORDER BY m.event_id
        '''
        contributions = []
        raw = db.execute(query).fetchall()
        n_movements = db.execute('SELECT COUNT(*) FROM movements').fetchone()[0]
        if len(raw) != n_movements or len({r[0] for r in raw}) != n_movements:
            raise ValueError('Missing/duplicate applicable UOM or allocation joins')
        for eid, sign, qty, units, share, occurred, rate_date, alloc_date in raw:
            product = qty * units * share
            if product % 100:
                raise ValueError('Fractional individual-unit contribution')
            contributions.append({'event_id': eid, 'net_units': sign * (product // 100), 'qty': qty,
                                  'units_per_uom': units, 'share': share, 'shipment_date': occurred,
                                  'uom_effective': rate_date, 'allocation_effective': alloc_date})
        net = sum(r['net_units'] for r in contributions)
    finally:
        db.close()

    matching = [r for r in p05 if r['plan'] == terms['price_plan'] and int(r['minimum']) <= terms['ordered_units']]
    chosen_minimum = max(int(r['minimum']) for r in matching)
    tiers = [r for r in matching if int(r['minimum']) == chosen_minimum]
    if len(tiers) != 1:
        raise ValueError('Nonunique price tier')
    tier = tiers[0]
    D = _hma_decimal.Decimal
    with _hma_decimal.localcontext() as context:
        context.prec = 90
        price = D(tier['gross_cents']) / D(tier['pack_units'])
        price *= (D(10000) - D(tier['rebate_a_bps'])) / D(10000)
        price *= (D(10000) - D(tier['rebate_b_bps'])) / D(10000)
        price += D(tier['fee_cents']) + D(tier['pack_fee_cents']) / D(tier['pack_units']) - D(tier['credit_cents'])
        cents = int(price.quantize(D(1), rounding=_hma_decimal.ROUND_HALF_UP))
    answer = {'order_id': target_order, 'sku': target['sku'], 'quantity_units': terms['ordered_units'] - net,
              'unit_price_cents': cents, 'currency': terms['currency'], 'ship_date': terms['ship_date'], 'status': 'active'}
    return answer, {'term_winners': winners, 'ordered_units': terms['ordered_units'], 'net_dispatched_units': net,
                    'open_units': answer['quantity_units'], 'contributions': contributions,
                    'selected_price_row': tier, 'unrounded_price_cents': str(price)}


def high_material_audit(cases):
    rows = []
    for case in cases:
        answer, trace = high_material_answer(case['document'])
        if answer != case['gold']:
            raise ValueError('Independent visible-text audit disagrees: ' + case['case_id'] + '\n' + _hma_json.dumps(answer))
        rows.append({'case_id': case['case_id'], 'content_hash': _hma_hashlib.sha256(case['document'].encode()).hexdigest(),
                     'passed': True, 'answer': answer, 'trace': trace})
    return {'passed': True, 'n_cases': len(rows), 'method': 'Independent text parser, SQL movement joins and Decimal pricing; no fixture helpers imported', 'cases': rows}
