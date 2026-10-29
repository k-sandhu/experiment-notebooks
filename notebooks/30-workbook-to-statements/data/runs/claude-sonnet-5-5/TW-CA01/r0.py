import datetime
import re

import openpyxl
from openpyxl.utils import get_column_letter

ENTITY_CODE = "TW-CA01"
CURRENCY = "CAD"

IS_MAP = {
    "revenue": [("Net sales", 1)],
    "cost_of_sales": [("Cost of goods sold", 1)],
    "distribution_costs": [("Selling expenses", 1)],
    "administrative_expenses": [
        ("Staff costs (administration)", 1),
        ("Rent and building costs", 1),
        ("Other overheads", 1),
    ],
    # Row 6900 is a gain: it is added in the printed operating profit.
    "other_operating_income": [("Other gains and losses (net)", 1)],
    "finance_income": [("Finance income", 1)],
    "finance_costs": [("Interest on bank loans", 1), ("Interest on lease liabilities", 1)],
    "income_tax_expense": [("Income tax expense", 1)],
}

BS_MAP = {
    "property_plant_equipment": [("Fixed assets (net book value)", 1)],
    "right_of_use_assets": [("Leased assets (right of use)", 1)],
    "intangible_assets": [("Intangible assets", 1)],
    "deferred_tax_assets": [("Deferred tax asset", 1)],
    "trade_receivables": [("Accounts receivable", 1)],
    "other_current_assets": [("Other receivables and prepayments", 1)],
    "cash_and_cash_equivalents": [("Cash at bank and in hand", 1)],
    "trade_payables": [("Accounts payable", 1)],
    "other_current_liabilities": [("Accruals and other payables", 1)],
    "current_borrowings": [("Borrowings (current)", 1)],
    "current_tax_payable": [("Corporation tax", 1)],
    "non_current_borrowings": [("Long-term borrowings", 1)],
    "provisions": [("Long-term provisions", 1)],
    "deferred_tax_liabilities": [("Deferred taxation", 1)],
    "share_capital": [("Share capital", 1)],
    "retained_earnings": [("Retained earnings", 1)],
    "other_reserves": [("Translation reserve", 1)],
}

CF_MAP = {
    "net_cash_operating": [("Net cash from operating activities", 1)],
    "net_cash_investing": [("Net cash from investing activities", 1)],
    "net_cash_financing": [("Net cash from financing activities", 1)],
    "fx_effect_on_cash": [("Foreign exchange differences on cash", 1)],
    "cash_at_beginning": [("Opening cash and cash equivalents", 1)],
    "dividends": [("Dividends paid to shareholders", -1)],
}

ALL_KEYS = (
    list(IS_MAP) + [
        "property_plant_equipment", "right_of_use_assets", "intangible_assets",
        "investments", "deferred_tax_assets", "inventories", "trade_receivables",
        "other_current_assets", "cash_and_cash_equivalents", "trade_payables",
        "other_current_liabilities", "current_borrowings", "current_tax_payable",
        "non_current_borrowings", "provisions", "deferred_tax_liabilities",
        "share_capital", "retained_earnings", "other_reserves",
    ] + list(CF_MAP)
)


def _norm(v):
    return re.sub(r"\s+", " ", str(v)).strip().lower() if v is not None else ""


def _find_row(ws, label, label_col):
    target = _norm(label)
    for r in range(1, ws.max_row + 1):
        if _norm(ws.cell(r, label_col).value) == target:
            return r
    raise KeyError("label not found on %s: %s" % (ws.title, label))


def _header_cols(ws, header_row, pred):
    return [c for c in range(1, ws.max_column + 1) if pred(ws.cell(header_row, c).value)]


def _parse_date(v):
    if isinstance(v, datetime.datetime):
        return v.date().isoformat()
    if isinstance(v, datetime.date):
        return v.isoformat()
    s = str(v).strip()
    for fmt in ("%b %d, %Y", "%B %d, %Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            pass
    raise ValueError("cannot parse date: %r" % (v,))


def extract(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws_is, ws_bs, ws_cf = wb["IS"], wb["BS"], wb["CF"]

    # Column discovery by headers
    is_cols = _header_cols(ws_is, 5, lambda v: _norm(v) == "total")
    is_cy, is_py = is_cols[0], is_cols[1]
    bs_cols = _header_cols(ws_bs, 4, lambda v: v is not None and str(v).strip() != "")
    bs_cy, bs_py = bs_cols[0], bs_cols[1]
    cf_cols = _header_cols(ws_cf, 4, lambda v: v is not None and str(v).strip() != "")
    cf_cy, cf_py = cf_cols[0], cf_cols[1]

    period_end = {
        "cy": _parse_date(ws_bs.cell(4, bs_cy).value),
        "py": _parse_date(ws_bs.cell(4, bs_py).value),
    }

    def cell_ref(ws, row, col, factor=1):
        return {"sheet": ws.title, "cell": "%s%d" % (get_column_letter(col), row), "factor": factor}

    def build_line(ws, label_col, col, items):
        cells, total = [], 0
        for label, factor in items:
            r = _find_row(ws, label, label_col)
            ref = cell_ref(ws, r, col, factor)
            cells.append(ref)
            total += factor * ws.cell(r, col).value
        return {"value": total, "cells": cells}

    fields = {k: {"cy": {"value": 0, "cells": []}, "py": {"value": 0, "cells": []}} for k in ALL_KEYS}

    for key, items in IS_MAP.items():
        fields[key] = {
            "cy": build_line(ws_is, 2, is_cy, items),
            "py": build_line(ws_is, 2, is_py, items),
        }
    for key, items in BS_MAP.items():
        fields[key] = {
            "cy": build_line(ws_bs, 1, bs_cy, items),
            "py": build_line(ws_bs, 1, bs_py, items),
        }
    for key, items in CF_MAP.items():
        fields[key] = {
            "cy": build_line(ws_cf, 1, cf_cy, items),
            "py": build_line(ws_cf, 1, cf_py, items),
        }

    # Printed totals
    source_totals = []

    def add_total(ws, label_col, label, cols, formula):
        r = _find_row(ws, label, label_col)
        for year, col in cols:
            source_totals.append({
                "sheet": ws.title,
                "cell": "%s%d" % (get_column_letter(col), r),
                "year": year,
                "factor": 1,
                "formula": formula,
            })

    is_yc = [("cy", is_cy), ("py", is_py)]
    bs_yc = [("cy", bs_cy), ("py", bs_py)]
    cf_yc = [("cy", cf_cy), ("py", cf_py)]

    add_total(ws_is, 2, "Gross profit", is_yc, "gross_profit")
    add_total(ws_is, 2, "Operating profit", is_yc, "operating_profit")
    add_total(ws_is, 2, "Profit before tax", is_yc, "profit_before_tax")
    add_total(ws_is, 2, "Net profit", is_yc, "profit_for_year")

    add_total(ws_bs, 1, "Total non-current assets", bs_yc, "total_non_current_assets")
    add_total(ws_bs, 1, "Total current assets", bs_yc, "total_current_assets")
    add_total(ws_bs, 1, "TOTAL ASSETS", bs_yc, "total_assets")
    add_total(ws_bs, 1, "Total shareholders' funds", bs_yc, "total_equity")
    add_total(ws_bs, 1, "Total non-current liabilities", bs_yc, "total_non_current_liabilities")
    add_total(ws_bs, 1, "Total current liabilities", bs_yc, "total_current_liabilities")
    add_total(ws_bs, 1, "Total liabilities", bs_yc, "total_liabilities")
    add_total(ws_bs, 1, "TOTAL EQUITY AND LIABILITIES", bs_yc, "total_equity_and_liabilities")

    add_total(ws_cf, 1, "Net change in cash and cash equivalents", cf_yc, "net_change_in_cash")
    add_total(ws_cf, 1, "Cash at end of year", cf_yc, "cash_at_end")
    add_total(ws_cf, 1, "Profit for the year", cf_yc, "profit_for_year")
    add_total(ws_cf, 1, "Retained earnings at end of year", cf_yc, "retained_earnings")

    # Ignored
    is_first = _find_row(ws_is, "Net sales", 2)
    is_last = ws_is.max_row
    q_first, q_last = get_column_letter(is_cy - 4), get_column_letter(is_cy - 1)
    ob = _find_row(ws_cf, "Retained earnings at start of year", 1)
    ignored = [
        {
            "sheet": "IS",
            "range": "%s%d:%s%d" % (q_first, is_first, q_last, is_last),
            "reason": "Quarterly columns Q1-Q4 of fiscal 2026; the full-year Total column is used instead.",
        },
        {
            "sheet": "IS",
            "range": "A%d:A%d" % (is_first, is_last),
            "reason": "GL account codes (identifiers, not amounts).",
        },
        {
            "sheet": "CF",
            "range": "%s%d:%s%d" % (get_column_letter(cf_cy), ob, get_column_letter(cf_py), ob),
            "reason": "Opening retained earnings in the movement table; equals the prior-year balance-sheet "
                      "retained earnings already used, so it is a repeat, not a new amount.",
        },
    ]

    notes = (
        "Workbook name is 'Tarnwell Canada Limited'; matched to TW-CA01 (Tarnwell Canada Ltd., CAD). Fiscal year ends "
        "31 March; amounts are whole Canadian dollars (unit 1). Income statement amounts come from the full-year Total "
        "columns, not the quarters. 'Other gains and losses (net)' is a net gain, since the printed operating profit "
        "only reconciles when it is added, so it is mapped as positive other operating income. Overheads (staff, rent, "
        "other) are mapped to administrative expenses; bank-loan and lease interest to finance costs. Accounts "
        "receivable maps to trade receivables, other receivables and prepayments to other current assets, accruals to "
        "other current liabilities, corporation tax to current income tax payable, and deferred taxation to deferred "
        "tax liabilities. Dividends use the 'paid' line from the retained earnings movement, sign-flipped; no separate "
        "'declared' figure is shown, and the roll-forward ties to it. All printed totals and cross-statement checks "
        "were consistent, so no source exceptions are declared."
    )

    return {
        "entity_code": ENTITY_CODE,
        "source_entity_name": str(ws_is["A1"].value).strip(),
        "currency": CURRENCY,
        "unit": 1,
        "period_end": period_end,
        "fields": fields,
        "source_totals": source_totals,
        "ignored": ignored,
        "source_exceptions": [],
        "notes": notes,
    }
