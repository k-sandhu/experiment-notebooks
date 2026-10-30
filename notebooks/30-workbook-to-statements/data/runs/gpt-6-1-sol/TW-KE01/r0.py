import calendar
import math
import re
from datetime import date
from numbers import Real

import openpyxl


def extract(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    try:
        sheets = {name: wb[name] for name in ("IS", "SOFP", "SCF")}

        def normalise(value):
            return " ".join(str(value).split()).casefold()

        def row_for(sheet, label):
            matches = [
                row[0].row
                for row in sheets[sheet].iter_rows(min_col=1, max_col=1)
                if row[0].value is not None
                and normalise(row[0].value) == normalise(label)
            ]
            if len(matches) != 1:
                raise ValueError(
                    f"{sheet}: expected exactly one row labelled {label!r}"
                )
            return matches[0]

        # These aliases identify exactly one entity in the supplied register.
        aliases = {
            "tarnwell e.a. ltd": "TW-KE01",
            "tarnwell east africa limited": "TW-KE01",
        }
        entity_names = []
        for ws in sheets.values():
            matches = [
                cell.value
                for row in ws.iter_rows(min_col=1, max_col=1)
                for cell in row
                if isinstance(cell.value, str)
                and normalise(cell.value) in aliases
            ]
            if len(matches) != 1:
                raise ValueError(f"{ws.title}: missing or ambiguous entity name")
            entity_names.append(matches[0])

        if len({aliases[normalise(name)] for name in entity_names}) != 1:
            raise ValueError("The statements identify different entities")

        # Discover year columns from their currency/unit headers.
        columns = {}
        year_pairs = []
        for name, ws in sheets.items():
            headers = {}
            for row in ws.iter_rows():
                for cell in row:
                    if not isinstance(cell.value, str):
                        continue
                    match = re.fullmatch(
                        r"\s*(\d{4})\s+KShs\s*['’]\s*000\s*",
                        cell.value,
                        re.IGNORECASE,
                    )
                    if match:
                        year = int(match.group(1))
                        previous = headers.get(year)
                        if previous is not None and previous != cell.column:
                            raise ValueError(f"{name}: ambiguous year columns")
                        headers[year] = cell.column

            if len(headers) != 2:
                raise ValueError(f"{name}: expected two KShs'000 year columns")
            cy, py = sorted(headers, reverse=True)
            if cy != py + 1:
                raise ValueError(f"{name}: years must be consecutive")
            columns[name] = {"cy": headers[cy], "py": headers[py]}
            year_pairs.append((cy, py))

        if len(set(year_pairs)) != 1:
            raise ValueError("Statement years differ")
        cy, py = year_pairs[0]

        # Read the reporting month/day from the balance-sheet heading.
        dates = []
        for row in sheets["SOFP"].iter_rows(min_col=1, max_col=1):
            value = row[0].value
            if not isinstance(value, str):
                continue
            match = re.fullmatch(
                r"\s*As at\s+(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})\s*",
                value,
                re.IGNORECASE,
            )
            if match:
                months = {
                    month.casefold(): i
                    for i, month in enumerate(calendar.month_name)
                    if month
                }
                month = months.get(match.group(2).casefold())
                if month is None:
                    raise ValueError("Unrecognised balance-sheet month")
                dates.append(
                    date(int(match.group(3)), month, int(match.group(1)))
                )
        if len(dates) != 1 or dates[0].year != cy:
            raise ValueError("Missing or inconsistent balance-sheet date")
        reporting_date = dates[0]

        def number(sheet, address):
            value = sheets[sheet][address].value
            if (
                isinstance(value, bool)
                or not isinstance(value, Real)
                or not math.isfinite(value)
            ):
                raise ValueError(f"{sheet}!{address} is not a finite number")
            return int(value) if isinstance(value, int) else float(value)

        def reference(sheet, label, year, factor=1):
            cell = sheets[sheet].cell(
                row_for(sheet, label), columns[sheet][year]
            )
            number(sheet, cell.coordinate)
            return {"sheet": sheet, "cell": cell.coordinate, "factor": factor}

        def reference_value(ref):
            return ref["factor"] * number(ref["sheet"], ref["cell"])

        keys = """
            revenue cost_of_sales distribution_costs administrative_expenses
            other_operating_income finance_income finance_costs income_tax_expense
            property_plant_equipment right_of_use_assets intangible_assets
            investments deferred_tax_assets inventories trade_receivables
            other_current_assets cash_and_cash_equivalents trade_payables
            other_current_liabilities current_borrowings current_tax_payable
            non_current_borrowings provisions deferred_tax_liabilities
            share_capital retained_earnings other_reserves net_cash_operating
            net_cash_investing net_cash_financing fx_effect_on_cash
            cash_at_beginning dividends
        """.split()
        fields = {
            key: {year: {"value": 0, "cells": []} for year in ("cy", "py")}
            for key in keys
        }

        mappings = {
            "IS": {
                "revenue": ["Sales"],
                "cost_of_sales": ["Cost of goods sold"],
                "distribution_costs": ["Selling and distribution expenses"],
                "administrative_expenses": [
                    "Administrative salaries",
                    "Office premises costs",
                    "Other administrative expenses",
                ],
                "other_operating_income": ["Other gains and losses (net)"],
                "finance_income": ["Interest received"],
                "finance_costs": ["Finance costs"],
                "income_tax_expense": ["Tax on profit"],
            },
            "SOFP": {
                "property_plant_equipment": ["Tangible assets"],
                "right_of_use_assets": ["Leased assets (right of use)"],
                "intangible_assets": ["Intangible assets"],
                "deferred_tax_assets": ["Deferred tax assets"],
                "inventories": ["Inventories"],
                "trade_receivables": ["Trade debtors"],
                "other_current_assets": ["Other receivables and prepayments"],
                "cash_and_cash_equivalents": ["Cash"],
                "share_capital": ["Share capital"],
                "retained_earnings": ["Accumulated profits"],
                "other_reserves": ["Other reserves"],
                "non_current_borrowings": ["Loans due after one year"],
                "provisions": ["Provisions"],
                "deferred_tax_liabilities": ["Deferred tax liabilities"],
                "trade_payables": ["Accounts payable"],
                "other_current_liabilities": ["Accruals and other payables"],
                "current_borrowings": ["Short-term borrowings"],
                "current_tax_payable": ["Income tax payable"],
                "dividends": ["Dividends paid to shareholders"],
            },
            "SCF": {
                "net_cash_operating": ["Net cash from operating activities"],
                "net_cash_investing": ["Net cash used in investing activities"],
                "net_cash_financing": ["Net cash from financing activities"],
                "fx_effect_on_cash": ["Foreign exchange differences on cash"],
                "cash_at_beginning": ["Cash at start of year"],
            },
        }
        for sheet, mapping in mappings.items():
            for key, labels in mapping.items():
                for year in ("cy", "py"):
                    refs = [
                        reference(
                            sheet, label, year, -1 if key == "dividends" else 1
                        )
                        for label in labels
                    ]
                    fields[key][year] = {
                        "value": sum(reference_value(ref) for ref in refs),
                        "cells": refs,
                    }

        formulas = {
            "gross_profit": "revenue - cost_of_sales",
            "operating_profit":
                "gross_profit - distribution_costs - administrative_expenses"
                " + other_operating_income",
            "profit_before_tax":
                "operating_profit + finance_income - finance_costs",
            "profit_for_year": "profit_before_tax - income_tax_expense",
            "total_non_current_assets":
                "property_plant_equipment + right_of_use_assets"
                " + intangible_assets + investments + deferred_tax_assets",
            "total_current_assets":
                "inventories + trade_receivables + other_current_assets"
                " + cash_and_cash_equivalents",
            "total_assets": "total_non_current_assets + total_current_assets",
            "total_current_liabilities":
                "trade_payables + other_current_liabilities"
                " + current_borrowings + current_tax_payable",
            "total_non_current_liabilities":
                "non_current_borrowings + provisions + deferred_tax_liabilities",
            "total_liabilities":
                "total_current_liabilities + total_non_current_liabilities",
            "total_equity": "share_capital + retained_earnings + other_reserves",
            "total_equity_and_liabilities": "total_equity + total_liabilities",
            "net_change_in_cash":
                "net_cash_operating + net_cash_investing + net_cash_financing",
            "cash_at_end":
                "cash_at_beginning + net_change_in_cash + fx_effect_on_cash",
        }

        def expression_value(expression, values):
            tokens = expression.split()
            result = values[tokens[0]]
            for i in range(1, len(tokens), 2):
                operator, key = tokens[i:i + 2]
                if operator not in ("+", "-"):
                    raise ValueError("Unsupported formula operator")
                result += values[key] * (1 if operator == "+" else -1)
            return result

        calculated = {}
        for year in ("cy", "py"):
            values = {key: fields[key][year]["value"] for key in keys}
            for key, expression in formulas.items():
                values[key] = expression_value(expression, values)
            calculated[year] = values

        source_totals = []

        def add_total(sheet, label, formula):
            for year in ("cy", "py"):
                source_totals.append({
                    **reference(sheet, label, year),
                    "year": year,
                    "formula": formula,
                })

        printed_totals = {
            "IS": {
                "Gross profit": "gross_profit",
                "Total administrative expenses": "administrative_expenses",
                "Profit from operations": "operating_profit",
                "Profit before tax": "profit_before_tax",
                "Net profit": "profit_for_year",
            },
            "SOFP": {
                "Total non-current assets": "total_non_current_assets",
                "Total current assets": "total_current_assets",
                "TOTAL ASSETS": "total_assets",
                "Total equity": "total_equity",
                "Total non-current liabilities": "total_non_current_liabilities",
                "Total current liabilities": "total_current_liabilities",
                "Total liabilities": "total_liabilities",
                "TOTAL EQUITY AND LIABILITIES": "total_equity_and_liabilities",
                "Profit for the year": "profit_for_year",
                "Closing retained earnings": "retained_earnings",
            },
            "SCF": {
                "Net change in cash and cash equivalents": "net_change_in_cash",
                "Cash at end of year": "cash_at_end",
            },
        }
        for sheet, totals in printed_totals.items():
            for label, formula in totals.items():
                add_total(sheet, label, formula)

        # Opening current-year retained earnings equals prior-year closing equity.
        source_totals.append({
            **reference("SOFP", "Opening retained earnings", "cy"),
            "year": "cy",
            "sum_of": [reference("SOFP", "Accumulated profits", "py")],
        })

        # Also check both printed retained-earnings reconciliations directly.
        for year in ("cy", "py"):
            source_totals.append({
                **reference("SOFP", "Closing retained earnings", year),
                "year": year,
                "sum_of": [
                    reference("SOFP", label, year)
                    for label in (
                        "Opening retained earnings",
                        "Profit for the year",
                        "Dividends paid to shareholders",
                    )
                ],
            })

        exceptions = []

        def check(check_id, actual, expected, explanation):
            difference = actual - expected
            if not math.isclose(difference, 0, rel_tol=0, abs_tol=1e-7):
                exceptions.append({
                    "check": check_id,
                    "difference": difference,
                    "explanation": explanation,
                })

        for total in source_totals:
            year = total["year"]
            if "formula" in total:
                expected = expression_value(
                    total["formula"], calculated[year]
                )
                explanation = (
                    "The printed amount minus the amount calculated from "
                    f"the mapped input lines ({total['formula']}) differs. "
                    "All source amounts have been preserved."
                )
            else:
                expected = sum(
                    reference_value(ref) for ref in total["sum_of"]
                )
                explanation = (
                    "The printed amount differs from its cited supporting "
                    "cells. All source amounts have been preserved."
                )
            check(
                f"T {total['sheet']}!{total['cell']} {year}",
                reference_value(total),
                expected,
                explanation,
            )

        for year in ("cy", "py"):
            values = calculated[year]
            check(
                f"R1 balance {year}",
                values["total_assets"],
                values["total_equity_and_liabilities"],
                "Mapped assets minus mapped equity and liabilities differs.",
            )
            check(
                f"R2 cash_at_end {year}",
                values["cash_at_end"],
                values["cash_and_cash_equivalents"],
                "Cash-flow closing cash minus balance-sheet cash differs.",
            )
        check(
            "R3 opening cash cy",
            calculated["cy"]["cash_at_beginning"],
            calculated["py"]["cash_and_cash_equivalents"],
            "Current-year opening cash minus prior-year balance-sheet cash differs.",
        )
        check(
            "R4 retained earnings cy",
            calculated["cy"]["retained_earnings"],
            calculated["py"]["retained_earnings"]
            + calculated["cy"]["profit_for_year"]
            - calculated["cy"]["dividends"],
            "Closing retained earnings minus prior retained earnings plus "
            "current profit less dividends differs.",
        )

        # Ensure new, unmapped numeric rows cannot silently escape coverage.
        covered = set()

        def cover(ref):
            covered.add((ref["sheet"], ref["cell"]))

        for field in fields.values():
            for line in field.values():
                for ref in line["cells"]:
                    cover(ref)
        for total in source_totals:
            cover(total)
            for ref in total.get("sum_of", []):
                cover(ref)

        for sheet, ws in sheets.items():
            for column in set(columns[sheet].values()):
                used_rows = [
                    ws[address].row
                    for covered_sheet, address in covered
                    if covered_sheet == sheet
                    and ws[address].column == column
                ]
                for row in ws.iter_rows(
                    min_row=min(used_rows),
                    min_col=column,
                    max_col=column,
                ):
                    cell = row[0]
                    if (
                        isinstance(cell.value, Real)
                        and not isinstance(cell.value, bool)
                        and (sheet, cell.coordinate) not in covered
                    ):
                        raise ValueError(
                            f"Unmapped numeric amount: {sheet}!{cell.coordinate}"
                        )

        return {
            "entity_code": aliases[normalise(entity_names[0])],
            "source_entity_name": entity_names[0],
            "currency": "KES",
            "unit": 1000,
            "period_end": {
                "cy": reporting_date.isoformat(),
                "py": reporting_date.replace(year=py).isoformat(),
            },
            "fields": fields,
            "source_totals": source_totals,
            "ignored": [],
            "source_exceptions": exceptions,
            "notes": (
                "Tarnwell E.A. Ltd is matched to Tarnwell East Africa Limited "
                "(TW-KE01); KShs'000 denotes thousands of Kenyan shillings. "
                "Administrative expenses use the three detailed expense rows; "
                "the printed administrative subtotal is checked separately, "
                "and any discrepancy is reported without adjustment. "
                "Dividends in the retained-earnings reconciliation are treated "
                "as the year's declared dividends and their negative source "
                "sign is reversed. Investments are absent and remain zero. "
                "Prior-year opening retained earnings support the prior-year "
                "reconciliation rather than a template input."
            ),
        }
    finally:
        wb.close()
