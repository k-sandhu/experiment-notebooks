import re
import datetime as _dt

import openpyxl
from openpyxl.utils import get_column_letter

REGISTER_CCY = {
    "TW-UK01": "GBP", "TW-UK02": "GBP", "TW-UK03": "GBP", "TW-DE01": "EUR", "TW-DE02": "EUR",
    "TW-FR01": "EUR", "TW-NL01": "EUR", "TW-IE01": "EUR", "TW-US01": "USD", "TW-US02": "USD",
    "TW-US03": "USD", "TW-CA01": "CAD", "TW-MX01": "MXN", "TW-BR01": "BRL", "TW-JP01": "JPY",
    "TW-IN01": "INR", "TW-SG01": "SGD", "TW-AU01": "AUD", "TW-NZ01": "NZD", "TW-ZA01": "ZAR",
    "TW-AE01": "AED", "TW-AE02": "AED", "TW-PL01": "PLN", "TW-SE01": "SEK", "TW-CH01": "CHF",
    "TW-KE01": "KES",
}

# template key -> [(line code, factor)]; ledger is debit positive / credit negative
MAPPING = {
    "revenue": [("IS100", -1), ("IS110", -1)],
    "cost_of_sales": [("IS200", 1)],
    "distribution_costs": [("IS300", 1), ("IS310", 1)],
    "administrative_expenses": [("IS400", 1)],
    "other_operating_income": [("IS500", -1)],
    "finance_income": [("IS600", -1)],
    "finance_costs": [("IS610", 1), ("IS620", 1)],
    "income_tax_expense": [("IS700", 1)],
    "property_plant_equipment": [("BS200", 1)],
    "right_of_use_assets": [("BS210", 1)],
    "intangible_assets": [("BS220", 1)],
    "investments": [],
    "deferred_tax_assets": [("BS230", 1)],
    "inventories": [("BS120", 1)],
    "trade_receivables": [("BS110", 1)],
    "other_current_assets": [("BS130", 1)],
    "cash_and_cash_equivalents": [("BS100", 1)],
    "trade_payables": [("BS300", -1)],
    "other_current_liabilities": [("BS310", -1)],
    "current_borrowings": [("BS320", -1)],
    "current_tax_payable": [("BS330", -1)],
    "non_current_borrowings": [("BS400", -1), ("BS410", -1)],
    "provisions": [("BS420", -1)],
    "deferred_tax_liabilities": [("BS430", -1)],
    "share_capital": [("BS500", -1)],
    "retained_earnings": [("BS510", -1)],
    "other_reserves": [],
    "net_cash_operating": [("CF100", 1)],
    "net_cash_investing": [("CF200", 1)],
    "net_cash_financing": [("CF300", 1)],
    "fx_effect_on_cash": [("CF400", 1)],
    "cash_at_beginning": [("CF500", 1)],
    "dividends": [("EQ100", 1)],
}

# printed subtotal code -> (factor to template sign, template formula)
PRINTED_TOTALS = {
    "SUB-GP": (-1, "revenue - cost_of_sales"),
    "SUB-NPAT": (-1, "profit_for_year"),
    "SUB-TA": (1, "total_assets"),
    "SUB-TLE": (-1, "total_equity_and_liabilities"),
    "SUB-CF": (1, "cash_at_end"),
}

TOTAL_DEFS = {
    "gross_profit": "revenue - cost_of_sales",
    "operating_profit": "gross_profit - distribution_costs - administrative_expenses + other_operating_income",
    "profit_before_tax": "operating_profit + finance_income - finance_costs",
    "profit_for_year": "profit_before_tax - income_tax_expense",
    "total_non_current_assets": "property_plant_equipment + right_of_use_assets + intangible_assets + investments + deferred_tax_assets",
    "total_current_assets": "inventories + trade_receivables + other_current_assets + cash_and_cash_equivalents",
    "total_assets": "total_non_current_assets + total_current_assets",
    "total_current_liabilities": "trade_payables + other_current_liabilities + current_borrowings + current_tax_payable",
    "total_non_current_liabilities": "non_current_borrowings + provisions + deferred_tax_liabilities",
    "total_liabilities": "total_current_liabilities + total_non_current_liabilities",
    "total_equity": "share_capital + retained_earnings + other_reserves",
    "total_equity_and_liabilities": "total_equity + total_liabilities",
    "net_change_in_cash": "net_cash_operating + net_cash_investing + net_cash_financing",
    "cash_at_end": "cash_at_beginning + net_change_in_cash + fx_effect_on_cash",
}

MONTHS = {m: i + 1 for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"])}

SHEET = "Export"


def _ev(formula, d):
    total, sign = 0, 1
    for tok in re.findall(r"[+-]|\w+", formula):
        if tok == "+":
            sign = 1
        elif tok == "-":
            sign = -1
        else:
            total += sign * d[tok]
            sign = 1
    return total


def _all_totals(vals):
    d = dict(vals)
    for name, f in TOTAL_DEFS.items():
        d[name] = _ev(f, d)
    return d


def _is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _period_end(wb, fy_label):
    if "Parameters" not in wb.sheetnames:
        return None
    for row in wb["Parameters"].iter_rows(values_only=True):
        for v in row:
            if isinstance(v, str) and fy_label in v:
                m = re.search(r"to\s+(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", v)
                if m and m.group(2).lower() in MONTHS:
                    return _dt.date(int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1)))
    return None


def extract(path, entity=None):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb[SHEET]

    header = {}
    for c in ws[1]:
        if c.value is not None:
            header[str(c.value).strip().lower()] = c.column
    c_ent, c_name, c_fy = header["entity"], header["entity name"], header["fiscal year"]
    c_code, c_amt = header["line code"], header["amount"]
    amt_col = get_column_letter(c_amt)

    rows = []
    for r in range(2, ws.max_row + 1):
        ent = ws.cell(r, c_ent).value
        if ent is None:
            continue
        rows.append({
            "row": r, "ent": str(ent).strip(), "name": ws.cell(r, c_name).value,
            "fy": str(ws.cell(r, c_fy).value).strip(), "code": str(ws.cell(r, c_code).value).strip(),
            "amt": ws.cell(r, c_amt).value,
        })

    def to_code(e):
        return e if e in REGISTER_CCY else "TW-" + e

    if entity is None:
        entity = next(x["ent"] for x in rows if to_code(x["ent"]) in REGISTER_CCY)
    ent_raw = entity[3:] if entity.startswith("TW-") else entity
    entity_code = to_code(ent_raw)
    sel = [x for x in rows if x["ent"] == ent_raw]

    fy_nums = sorted({int(x["fy"][2:]) for x in sel})
    cy_label = "FY%02d" % fy_nums[-1]
    py_label = "FY%02d" % (fy_nums[-1] - 1)
    labels = {"cy": cy_label, "py": py_label}

    cy_end = _period_end(wb, cy_label)
    if cy_end is None:
        raise ValueError("fiscal year end date not found in Parameters")
    try:
        py_end = cy_end.replace(year=cy_end.year - 1)
    except ValueError:
        py_end = cy_end.replace(year=cy_end.year - 1, day=28)

    idx = {}
    for x in sel:
        idx.setdefault((x["fy"], x["code"]), []).append(x)

    used_rows = set()

    def cell_ref(x):
        return {"sheet": SHEET, "cell": "%s%d" % (amt_col, x["row"])}

    fields, vals = {}, {"cy": {}, "py": {}}
    for key, parts in MAPPING.items():
        fields[key] = {}
        for y in ("cy", "py"):
            cells, value = [], 0
            for code, factor in parts:
                for x in idx.get((labels[y], code), []):
                    if not _is_num(x["amt"]):
                        continue
                    ref = cell_ref(x)
                    ref["factor"] = factor
                    cells.append(ref)
                    value += factor * x["amt"]
                    used_rows.add(x["row"])
            fields[key][y] = {"value": value, "cells": cells}
            vals[y][key] = value

    tots = {y: _all_totals(vals[y]) for y in vals}

    source_totals, exceptions = [], []
    for code, (factor, formula) in PRINTED_TOTALS.items():
        for y in ("cy", "py"):
            for x in idx.get((labels[y], code), []):
                if not _is_num(x["amt"]):
                    continue
                ref = cell_ref(x)
                source_totals.append({**ref, "year": y, "factor": factor, "formula": formula})
                used_rows.add(x["row"])
                diff = factor * x["amt"] - _ev(formula, tots[y])
                if abs(diff) > 0.5:
                    exceptions.append({
                        "check": "T %s!%s %s" % (SHEET, ref["cell"], y),
                        "difference": diff,
                        "explanation": "Printed %s does not agree with the amounts reported in the workbook." % code,
                    })

    for y in ("cy", "py"):
        d = tots[y]
        diff = d["total_assets"] - d["total_equity_and_liabilities"]
        if abs(diff) > 0.5:
            exceptions.append({"check": "R1 balance " + y, "difference": diff,
                               "explanation": "Total assets differ from total equity and liabilities in the source."})
        diff = d["cash_at_end"] - d["cash_and_cash_equivalents"]
        if abs(diff) > 0.5:
            exceptions.append({"check": "R2 cash_at_end " + y, "difference": diff,
                               "explanation": "Cash flow closing cash differs from balance-sheet cash in the source."})
    diff = tots["cy"]["cash_at_beginning"] - tots["py"]["cash_and_cash_equivalents"]
    if abs(diff) > 0.5:
        exceptions.append({"check": "R3 opening cash cy", "difference": diff,
                           "explanation": "Opening cash differs from prior-year balance-sheet cash in the source."})
    diff = (tots["py"]["retained_earnings"] + tots["cy"]["profit_for_year"]
            - tots["cy"]["dividends"] - tots["cy"]["retained_earnings"])
    if abs(diff) > 0.5:
        exceptions.append({"check": "R4 retained earnings cy", "difference": diff,
                           "explanation": "Retained earnings do not roll forward from prior year, profit and dividends."})

    # ignored: every other numeric amount, grouped into contiguous runs with the same reason
    other_entities = sorted({x["ent"] for x in rows if x["ent"] != ent_raw})
    ignored, run = [], None

    def flush():
        if run:
            first, last, reason = run
            item = {"sheet": SHEET, "reason": reason}
            if first == last:
                item["cell"] = "%s%d" % (amt_col, first)
            else:
                item["range"] = "%s%d:%s%d" % (amt_col, first, amt_col, last)
            ignored.append(item)

    for x in rows:
        if x["row"] in used_rows or not _is_num(x["amt"]):
            continue
        if x["ent"] != ent_raw:
            reason = ("Rows of another entity (%s) in this combined export; not part of %s"
                      % (x["ent"], entity_code))
        elif x["fy"] not in (cy_label, py_label):
            reason = "Fiscal year %s is neither the current nor the prior year" % x["fy"]
        else:
            reason = "Line %s is not mapped to a template input line" % x["code"]
        if run and run[2] == reason and x["row"] == run[1] + 1:
            run[1] = x["row"]
        else:
            flush()
            run = [x["row"], x["row"], reason]
    flush()

    src_name = next((x["name"] for x in sel if x["name"]), None)
    notes = (
        "The export holds several entities (%s); this run extracts %s and ignores the other rows. "
        "Amounts are in ledger sign (debit positive, credit negative), so revenue, other operating income, "
        "finance income, liabilities and equity use factor -1. Fiscal year FY26 (1 Jul 2025 - 30 Jun 2026) is cy "
        "and FY25 is py. Store operating costs and marketing are mapped to distribution and selling costs; "
        "support office costs to administrative expenses. Accruals and employee entitlements go to other current "
        "liabilities, the bank facility is treated as non-current (no current/non-current split is shown), and "
        "lease finance costs and bank interest are combined in finance costs. Printed subtotals are listed in "
        "source_totals, not used as inputs."
        % (", ".join([ent_raw] + other_entities), entity_code)
    )

    return {
        "entity_code": entity_code,
        "source_entity_name": src_name,
        "currency": REGISTER_CCY[entity_code],
        "unit": 1,
        "period_end": {"cy": cy_end.isoformat(), "py": py_end.isoformat()},
        "fields": fields,
        "source_totals": source_totals,
        "ignored": ignored,
        "source_exceptions": exceptions,
        "notes": notes,
    }
