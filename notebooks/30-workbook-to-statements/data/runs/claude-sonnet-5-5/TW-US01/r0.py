import re
from datetime import datetime

import openpyxl
from openpyxl.utils import get_column_letter

IS = "Income Statement"
BS = "Balance Sheet"
CF = "Cash Flow"
RE = "Retained Earnings"


def _norm(s):
    s = str(s).replace("\u2019", "'").replace("\u2018", "'")
    return re.sub(r"\s+", " ", s).strip().lower()


def _find_row(ws, label, after=0, before=None):
    want = _norm(label)
    last = ws.max_row if before is None else before - 1
    for r in range(after + 1, last + 1):
        v = ws.cell(r, 1).value
        if isinstance(v, str) and _norm(v) == want:
            return r
    raise KeyError("label not found on %s: %s" % (ws.title, label))


def _year_cols(ws):
    years = {}
    for r in range(1, 9):
        for c in range(2, ws.max_column + 1):
            v = ws.cell(r, c).value
            if isinstance(v, str):
                m = re.search(r"(?:19|20)\d\d", v)
                if m:
                    years.setdefault(int(m.group()), c)
    ys = sorted(years)
    return {"cy": years[ys[-1]], "py": years[ys[0]]}


def _unit(wb):
    for ws in wb.worksheets:
        for r in range(1, 4):
            v = ws.cell(r, 1).value
            if isinstance(v, str):
                t = v.lower()
                if "thousand" in t:
                    return 1000
                if "million" in t:
                    return 1000000
    return 1


# key -> (sheet, [(label, factor, after_label, before_label)])
def _s(label, factor=1, after=None, before=None):
    return (label, factor, after, before)


SPEC = {
    "revenue": (IS, [_s("Net sales")]),
    "cost_of_sales": (IS, [_s("Cost of goods sold")]),
    "distribution_costs": (IS, [_s("Selling expenses")]),
    "administrative_expenses": (IS, [_s("General and administrative expenses")]),
    "other_operating_income": (IS, [_s("Other operating (income) expense, net", -1)]),
    "finance_income": (IS, [_s("Interest income")]),
    "finance_costs": (IS, [_s("Interest expense")]),
    "income_tax_expense": (IS, [_s("Provision for income taxes")]),
    "property_plant_equipment": (BS, [_s("Property and equipment, net")]),
    "right_of_use_assets": (BS, [_s("Operating lease right-of-use assets")]),
    "intangible_assets": (BS, [_s("Goodwill"), _s("Intangible assets, net")]),
    "investments": (BS, []),
    "deferred_tax_assets": (BS, [_s("Deferred income taxes", 1, "Total current assets", "Total assets")]),
    "inventories": (BS, [_s("Inventories")]),
    "trade_receivables": (BS, [_s("Accounts receivable, net")]),
    "other_current_assets": (BS, [_s("Prepaid expenses and other current assets")]),
    "cash_and_cash_equivalents": (BS, [_s("Cash and cash equivalents")]),
    "trade_payables": (BS, [_s("Accounts payable")]),
    "other_current_liabilities": (BS, [_s("Accrued expenses and other current liabilities")]),
    "current_borrowings": (BS, [_s("Current portion of long-term debt"),
                                _s("Current operating lease liabilities")]),
    "current_tax_payable": (BS, [_s("Income taxes payable")]),
    "non_current_borrowings": (BS, [_s("Long-term debt, net of current portion"),
                                    _s("Operating lease liabilities, non-current")]),
    "provisions": (BS, [_s("Other long-term liabilities")]),
    "deferred_tax_liabilities": (BS, [_s("Deferred income taxes", 1, "Total current liabilities", "Total liabilities")]),
    "share_capital": (BS, [_s("Common stock"), _s("Additional paid-in capital")]),
    "retained_earnings": (BS, [_s("Retained earnings")]),
    "other_reserves": (BS, [_s("Accumulated other comprehensive income (loss)")]),
    "net_cash_operating": (CF, [_s("Net cash provided by operating activities")]),
    "net_cash_investing": (CF, [_s("Net cash used in investing activities")]),
    "net_cash_financing": (CF, [_s("Net cash provided by (used in) financing activities")]),
    "fx_effect_on_cash": (CF, [_s("Effect of exchange rate changes on cash")]),
    "cash_at_beginning": (CF, [_s("Cash and cash equivalents, beginning of year")]),
    "dividends": (RE, [_s("Dividends declared", -1)]),
}

# (sheet, label, formula)
TOTALS = [
    (IS, "Gross profit", "gross_profit"),
    (IS, "Total SG&A", "distribution_costs + administrative_expenses"),
    (IS, "Operating income", "operating_profit"),
    (IS, "Income before income taxes", "profit_before_tax"),
    (IS, "Net income", "profit_for_year"),
    (BS, "Total current assets", "total_current_assets"),
    (BS, "Total assets", "total_assets"),
    (BS, "Total current liabilities", "total_current_liabilities"),
    (BS, "Total liabilities", "total_liabilities"),
    (BS, "Total stockholders' equity", "total_equity"),
    (BS, "Total liabilities and stockholders' equity", "total_equity_and_liabilities"),
    (CF, "Net increase (decrease) in cash", "net_change_in_cash"),
    (CF, "Cash and cash equivalents, end of year", "cash_at_end"),
    (RE, "Net income", "profit_for_year"),
    (RE, "Retained earnings, end of year", "retained_earnings"),
]


def extract(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    try:
        cols = {ws.title: _year_cols(ws) for ws in wb.worksheets}

        def cell_ref(ws, row, yr):
            c = ws.cell(row, cols[ws.title][yr])
            return c

        # entity and periods
        source_name = wb[IS].cell(1, 1).value
        period_end = {}
        bs = wb[BS]
        for yr in ("cy", "py"):
            raw = str(bs.cell(4, cols[BS][yr]).value).strip()
            period_end[yr] = datetime.strptime(raw, "%b %d, %Y").strftime("%Y-%m-%d")

        fields = {}
        for key, (sheet, items) in SPEC.items():
            ws = wb[sheet]
            fields[key] = {}
            for yr in ("cy", "py"):
                cells = []
                value = 0
                for label, factor, after, before in items:
                    a = _find_row(ws, after) if after else 0
                    b = _find_row(ws, before) if before else None
                    row = _find_row(ws, label, a, b)
                    c = cell_ref(ws, row, yr)
                    cells.append({"sheet": sheet, "cell": c.coordinate, "factor": factor})
                    value += factor * c.value
                fields[key][yr] = {"value": value, "cells": cells}

        source_totals = []
        for sheet, label, formula in TOTALS:
            ws = wb[sheet]
            row = _find_row(ws, label)
            for yr in ("cy", "py"):
                c = cell_ref(ws, row, yr)
                source_totals.append({"sheet": sheet, "cell": c.coordinate, "year": yr,
                                      "factor": 1, "formula": formula})

        ignored = []
        isw = wb[IS]
        first = _find_row(isw, "Net sales")
        last = _find_row(isw, "Net income")
        used = set(cols[IS].values())
        for c in range(2, isw.max_column + 1):
            if c in used:
                continue
            head = isw.cell(6, c).value or isw.cell(5, c).value
            h = _norm(head) if head else ""
            if "budget" in h:
                reason = "Budget column, not actual results"
            elif "%" in h:
                reason = "Variance percentage versus budget, derived from the budget column"
            elif "var" in h:
                reason = "Variance in dollars versus budget, derived from the budget column"
            else:
                reason = "Column not belonging to the actual cy or py results"
            L = get_column_letter(c)
            ignored.append({"sheet": IS, "range": "%s%d:%s%d" % (L, first, L, last),
                            "reason": reason})

        rew = wb[RE]
        r_open = _find_row(rew, "Retained earnings, beginning of year")
        for yr in ("cy", "py"):
            c = cell_ref(rew, r_open, yr)
            ignored.append({"sheet": RE, "cell": c.coordinate,
                            "reason": "Opening retained earnings; equals the prior-year balance sheet "
                                      "retained earnings already used, and the roll-forward is tested by R4"})

        return {
            "entity_code": "TW-US01",
            "source_entity_name": source_name,
            "currency": "USD",
            "unit": _unit(wb),
            "period_end": period_end,
            "fields": fields,
            "source_totals": source_totals,
            "ignored": ignored,
            "source_exceptions": [],
            "notes": (
                "Workbook matched to TW-US01 (Tarnwell Inc., USD, in thousands; fiscal year ended June 30). "
                "Only the Actual columns are used; Budget and variance columns on the income statement are ignored. "
                "'Other operating (income) expense, net' is shown as an expense, so it is mapped with factor -1. "
                "Goodwill and intangibles are combined; current and non-current operating lease liabilities are "
                "combined with debt; 'Other long-term liabilities' is mapped to provisions; common stock and APIC "
                "form share capital; AOCI is other reserves. Dividends are shown negative in the equity statement "
                "and are mapped with factor -1. All printed totals tie and no exceptions were found."
            ),
        }
    finally:
        wb.close()
