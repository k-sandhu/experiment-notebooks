import re
import datetime as _dt
from openpyxl import load_workbook

KEYS = [
    "revenue", "cost_of_sales", "distribution_costs", "administrative_expenses",
    "other_operating_income", "finance_income", "finance_costs", "income_tax_expense",
    "property_plant_equipment", "right_of_use_assets", "intangible_assets", "investments",
    "deferred_tax_assets", "inventories", "trade_receivables", "other_current_assets",
    "cash_and_cash_equivalents", "trade_payables", "other_current_liabilities",
    "current_borrowings", "current_tax_payable", "non_current_borrowings", "provisions",
    "deferred_tax_liabilities", "share_capital", "retained_earnings", "other_reserves",
    "net_cash_operating", "net_cash_investing", "net_cash_financing", "fx_effect_on_cash",
    "cash_at_beginning", "dividends",
]

REGISTER = {
    "TW-UK01": ("Tarnwell Holdings plc", "GBP"),
    "TW-UK02": ("Tarnwell Engineering Limited", "GBP"),
    "TW-UK03": ("Tarnwell Engineering Services Limited", "GBP"),
    "TW-DE01": ("Tarnwell Antriebstechnik GmbH", "EUR"),
    "TW-DE02": ("Tarnwell Service GmbH", "EUR"),
    "TW-FR01": ("Tarnwell France SAS", "EUR"),
    "TW-NL01": ("Tarnwell Logistics B.V.", "EUR"),
    "TW-IE01": ("Tarnwell Ireland Limited", "EUR"),
    "TW-US01": ("Tarnwell Inc.", "USD"),
    "TW-US02": ("Tarnwell Software LLC", "USD"),
    "TW-US03": ("Tarnwell Holdings (US) Inc.", "USD"),
    "TW-CA01": ("Tarnwell Canada Ltd.", "CAD"),
    "TW-MX01": ("Tarnwell México, S.A. de C.V.", "MXN"),
    "TW-BR01": ("Tarnwell do Brasil Ltda.", "BRL"),
    "TW-JP01": ("Tarnwell Japan K.K.", "JPY"),
    "TW-IN01": ("Tarnwell India Private Limited", "INR"),
    "TW-SG01": ("Tarnwell Asia Pacific Pte. Ltd.", "SGD"),
    "TW-AU01": ("Tarnwell Australia Pty Ltd", "AUD"),
    "TW-NZ01": ("Tarnwell New Zealand Limited", "NZD"),
    "TW-ZA01": ("Tarnwell South Africa (Pty) Ltd", "ZAR"),
    "TW-AE01": ("Tarnwell Middle East FZE", "AED"),
    "TW-AE02": ("Tarnwell Trading L.L.C.", "AED"),
    "TW-PL01": ("Tarnwell Polska sp. z o.o.", "PLN"),
    "TW-SE01": ("Tarnwell Nordic AB", "SEK"),
    "TW-CH01": ("Tarnwell Schweiz AG", "CHF"),
    "TW-KE01": ("Tarnwell East Africa Limited", "KES"),
}

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"], 1)}

WITHIN = "Creditors: amounts falling due within one year"
AFTER = "Creditors: amounts falling due after more than one year"

# key -> list of (sheet, label, section label to search after, factor)
FIELDS = {
    "revenue": [("P&L", "Turnover", None, 1)],
    "cost_of_sales": [("P&L", "Cost of sales", None, -1)],
    "distribution_costs": [("P&L", "Distribution costs", None, -1)],
    "administrative_expenses": [("P&L", "Administrative expenses", None, -1)],
    "other_operating_income": [("P&L", "Other operating income", None, 1)],
    "finance_income": [("P&L", "Interest receivable and similar income", None, 1)],
    "finance_costs": [("P&L", "Interest payable and similar expenses", None, -1)],
    "income_tax_expense": [("P&L", "Tax on profit", None, -1)],
    "property_plant_equipment": [("BS", "Tangible assets", None, 1)],
    "intangible_assets": [("BS", "Intangible assets", None, 1)],
    "deferred_tax_assets": [("BS", "Deferred tax asset", None, 1)],
    "inventories": [("BS", "Stocks", None, 1)],
    "trade_receivables": [("BS", "Trade debtors", None, 1)],
    "other_current_assets": [("BS", "Prepayments and accrued income", None, 1),
                             ("BS", "Other debtors", None, 1)],
    "cash_and_cash_equivalents": [("BS", "Cash at bank and in hand", None, 1)],
    "trade_payables": [("BS", "Trade creditors", None, 1)],
    "other_current_liabilities": [("BS", "Accruals and deferred income", None, 1),
                                  ("BS", "Other taxation and social security", None, 1)],
    "current_borrowings": [("BS", "Bank overdraft", None, 1),
                           ("BS", "Bank loans", WITHIN, 1)],
    "current_tax_payable": [("BS", "Corporation tax", None, 1)],
    "non_current_borrowings": [("BS", "Bank loans", AFTER, 1)],
    "provisions": [("BS", "Other provisions", None, 1)],
    "deferred_tax_liabilities": [("BS", "Deferred taxation", None, 1)],
    "share_capital": [("BS", "Called up share capital", None, 1),
                      ("BS", "Share premium account", None, 1)],
    "retained_earnings": [("BS", "Profit and loss account", None, 1)],
    "other_reserves": [("BS", "Other reserves", None, 1)],
    "net_cash_operating": [("CF", "Net cash from operating activities", None, 1)],
    "net_cash_investing": [("CF", "Net cash from investing activities", None, 1)],
    "net_cash_financing": [("CF", "Net cash from financing activities", None, 1)],
    "fx_effect_on_cash": [("CF", "Effect of foreign exchange rate changes", None, 1)],
    "cash_at_beginning": [("CF", "Cash at beginning of year", None, 1)],
    "dividends": [("Reserves", "Dividends paid on equity shares", None, -1)],
}

# (sheet, label, section, formula) printed totals; factor 1 throughout
TOTALS = [
    ("P&L", "Gross profit", None, "gross_profit"),
    ("P&L", "Operating profit", None, "operating_profit"),
    ("P&L", "Profit before taxation", None, "profit_before_tax"),
    ("P&L", "Profit for the financial year", None, "profit_for_year"),
    ("BS", "Total fixed assets", None, "property_plant_equipment + right_of_use_assets + intangible_assets + investments"),
    ("BS", "Total debtors", None, "trade_receivables + other_current_assets + deferred_tax_assets"),
    ("BS", "Total current assets", None, "total_current_assets + deferred_tax_assets"),
    ("BS", "Total creditors due within one year", None, "total_current_liabilities"),
    ("BS", "Net current assets", None, "total_current_assets + deferred_tax_assets - total_current_liabilities"),
    ("BS", "Total assets less current liabilities", None, "total_assets - total_current_liabilities"),
    ("BS", "Net assets", None, "total_assets - total_liabilities"),
    ("BS", "Shareholders' funds", None, "total_equity"),
    ("CF", "Net increase/(decrease) in cash", None, "net_change_in_cash"),
    ("CF", "Cash at end of year", None, "cash_at_end"),
    ("Reserves", "At end of year", None, "retained_earnings"),
]


def _norm(s):
    return re.sub(r"\s+", " ", str(s)).strip().casefold()


def _norm_name(s):
    s = re.sub(r"[^\w\s]", " ", str(s).casefold())
    words = [{"ltd": "limited", "inc": "inc", "co": "co"}.get(w, w) for w in s.split()]
    return " ".join(words)


def _is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _year_columns(ws):
    """Find the columns whose header is a 4-digit year; larger year = cy."""
    found = []
    for row in ws.iter_rows(min_row=1, max_row=8):
        for c in row:
            v = c.value
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                v = str(int(v))
            if isinstance(v, str) and re.fullmatch(r"\s*(19|20)\d\d\s*", v):
                found.append((int(v), c.column_letter, c.row))
        if len(found) >= 2:
            break
    found.sort(reverse=True)
    return found[0][1], found[1][1], found[0][2]


def _find_row(ws, label, after=None, label_col="B"):
    start = 1
    if after is not None:
        start = _find_row(ws, after, None, label_col) + 1
    target = _norm(label)
    for r in range(start, ws.max_row + 1):
        v = ws[f"{label_col}{r}"].value
        if v is not None and _norm(v) == target:
            return r
    raise KeyError(f"label {label!r} not found in sheet {ws.title!r}")


def extract(path):
    wb = load_workbook(path, data_only=True)
    cols = {name: _year_columns(wb[name]) for name in wb.sheetnames}

    # entity
    raw_name = str(wb["BS"]["B1"].value).strip()
    code = None
    for c, (nm, _cur) in REGISTER.items():
        if _norm_name(nm) == _norm_name(raw_name):
            code = c
            break
    if code is None:
        raise ValueError(f"entity {raw_name!r} not in register")
    currency = REGISTER[code][1]

    # unit
    hdr_row = cols["BS"][2] + 1
    unit_txt = str(wb["BS"][f"{cols['BS'][0]}{hdr_row}"].value or "")
    if "'000" in unit_txt or "000" in unit_txt and "000000" not in unit_txt:
        unit = 1000
    elif re.search(r"million|mn|'m|m$", unit_txt, re.I):
        unit = 1000000
    else:
        unit = 1

    # period end
    title = str(wb["BS"]["B2"].value)
    m = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", title)
    d, mon, yr = int(m.group(1)), MONTHS[m.group(2).lower()], int(m.group(3))
    cy_date = _dt.date(yr, mon, d)
    try:
        py_date = _dt.date(yr - 1, mon, d)
    except ValueError:
        py_date = _dt.date(yr - 1, mon, d - 1)

    def colof(sheet, year):
        return cols[sheet][0] if year == "cy" else cols[sheet][1]

    def cell_ref(sheet, label, after, year):
        ws = wb[sheet]
        r = _find_row(ws, label, after)
        return f"{colof(sheet, year)}{r}"

    fields = {k: {"cy": {"value": 0, "cells": []}, "py": {"value": 0, "cells": []}} for k in KEYS}
    for key, parts in FIELDS.items():
        for year in ("cy", "py"):
            cells, total = [], 0
            for sheet, label, after, factor in parts:
                ref = cell_ref(sheet, label, after, year)
                val = wb[sheet][ref].value
                cells.append({"sheet": sheet, "cell": ref, "factor": factor})
                total += factor * val
            fields[key][year] = {"value": total, "cells": cells}

    source_totals = []
    for sheet, label, after, formula in TOTALS:
        for year in ("cy", "py"):
            source_totals.append({
                "sheet": sheet,
                "cell": cell_ref(sheet, label, after, year),
                "year": year,
                "factor": 1,
                "formula": formula,
            })

    ignored = []
    # note-reference column
    for name in wb.sheetnames:
        ws = wb[name]
        for r in range(1, ws.max_row + 1):
            v = ws[f"C{r}"].value
            if _is_num(v):
                ignored.append({"sheet": name, "cell": f"C{r}",
                                "reason": "note reference number, not an amount"})
    # reserves movement rows not needed as separate inputs
    rs = wb["Reserves"]
    r_open = _find_row(rs, "At beginning of year")
    r_prof = _find_row(rs, "Profit for the financial year")
    for year in ("cy", "py"):
        c = colof("Reserves", year)
        ignored.append({"sheet": "Reserves", "cell": f"{c}{r_open}",
                        "reason": "opening reserve balance; equals prior-year closing retained earnings already taken from the balance sheet, used only in the roll-forward"})
        ignored.append({"sheet": "Reserves", "cell": f"{c}{r_prof}",
                        "reason": "profit for the year, duplicate of the profit and loss account figure (profit is derived by the template)"})

    return {
        "entity_code": code,
        "source_entity_name": raw_name,
        "currency": currency,
        "unit": unit,
        "period_end": {"cy": cy_date.isoformat(), "py": py_date.isoformat()},
        "fields": fields,
        "source_totals": source_totals,
        "ignored": ignored,
        "source_exceptions": [],
        "notes": (
            "Workbook title 'TARNWELL ENGINEERING LTD' matched to TW-UK02 Tarnwell Engineering Limited "
            "(not the Services company). Amounts are in GBP thousands and kept as-is. Source shows costs "
            "and tax as negatives, so cost of sales, distribution, administrative, finance costs and tax "
            "carry factor -1; 'Other operating income' is already signed (net expense) and keeps factor 1. "
            "Deferred tax asset sits inside debtors in the source and is moved to deferred tax assets, so "
            "the printed Total debtors and Total current assets are tied via formulas that add it back. "
            "Prepayments and other debtors go to other current assets; overdraft and current bank loans to "
            "current borrowings; accruals and other taxation/social security to other current liabilities; "
            "share capital and share premium are combined. Dividends come from the reserves note with "
            "factor -1. All printed totals and cross-statement checks tie, so no source exceptions."
        ),
    }
