import openpyxl
from openpyxl.utils import get_column_letter


def _norm(s):
    return " ".join(str(s).split()).lower()


def extract(path):
    wb = openpyxl.load_workbook(path, data_only=True)

    def label_rows(ws):
        out = {}
        for r in range(1, ws.max_row + 1):
            v = ws.cell(r, 1).value
            if isinstance(v, str) and v.strip():
                out.setdefault(_norm(v), r)
        return out

    def year_cols(ws):
        # find the header row holding the two year strings, e.g. "2025" / "2024"
        for r in range(1, ws.max_row + 1):
            found = {}
            for c in range(1, ws.max_column + 1):
                v = ws.cell(r, c).value
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    v = str(int(v))
                if isinstance(v, str) and v.strip().isdigit() and len(v.strip()) == 4:
                    found[int(v.strip())] = c
            if len(found) >= 2:
                ys = sorted(found, reverse=True)
                return ys[0], ys[1], get_column_letter(found[ys[0]]), get_column_letter(found[ys[1]])
        raise ValueError("year header not found")

    sheets = {}
    for name in wb.sheetnames:
        ws = wb[name]
        sheets[name] = {"ws": ws, "rows": label_rows(ws), "cols": year_cols(ws)}

    cy_year, py_year, _, _ = sheets["ER"]["cols"]

    def cell_ref(sheet, label, year):
        s = sheets[sheet]
        r = s["rows"][_norm(label)]
        col = s["cols"][2] if year == "cy" else s["cols"][3]
        return col + str(r)

    def num(sheet, ref):
        v = sheets[sheet]["ws"][ref].value
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            raise ValueError(f"{sheet}!{ref} is not numeric")
        return v

    def line(items, year):
        cells = []
        total = 0
        for sheet, label, factor in items:
            ref = cell_ref(sheet, label, year)
            cells.append({"sheet": sheet, "cell": ref, "factor": factor})
            total += factor * num(sheet, ref)
        return {"value": total, "cells": cells}

    mapping = {
        "revenue": [("ER", "Ingresos por ventas netas", 1)],
        "cost_of_sales": [("ER", "Costo de ventas", 1)],
        "distribution_costs": [("ER", "Gastos de venta", 1)],
        "administrative_expenses": [("ER", "Gastos de administración", 1)],
        "other_operating_income": [("ER", "Otros ingresos (gastos) de operación, neto", 1)],
        "finance_income": [("ER", "Ingresos financieros", 1)],
        "finance_costs": [("ER", "Gastos financieros", 1)],
        "income_tax_expense": [("ER", "Impuesto sobre la renta causado", 1),
                               ("ER", "Impuesto sobre la renta diferido", 1)],
        "property_plant_equipment": [("ESF", "Propiedades, planta y equipo, neto", 1)],
        "right_of_use_assets": [("ESF", "Activos por derecho de uso", 1)],
        "intangible_assets": [("ESF", "Activos intangibles", 1)],
        "investments": [],
        "deferred_tax_assets": [("ESF", "Impuestos diferidos activos", 1)],
        "inventories": [("ESF", "Inventarios", 1)],
        "trade_receivables": [("ESF", "Cuentas por cobrar a clientes, neto", 1)],
        "other_current_assets": [("ESF", "Otras cuentas por cobrar y pagos anticipados", 1)],
        "cash_and_cash_equivalents": [("ESF", "Efectivo y equivalentes de efectivo", 1)],
        "trade_payables": [("ESF", "Proveedores", 1)],
        "other_current_liabilities": [
            ("ESF", "Otras cuentas por pagar y pasivos acumulados", 1),
            ("ESF", "Participación de los trabajadores en las utilidades (PTU) por pagar", 1)],
        "current_borrowings": [("ESF", "Préstamos bancarios a corto plazo", 1)],
        "current_tax_payable": [("ESF", "Impuestos a la utilidad por pagar", 1)],
        "non_current_borrowings": [("ESF", "Préstamos bancarios a largo plazo", 1)],
        "provisions": [("ESF", "Beneficios a los empleados", 1)],
        "deferred_tax_liabilities": [("ESF", "Impuestos diferidos pasivos", 1)],
        "share_capital": [("ESF", "Capital social", 1)],
        "retained_earnings": [("ESF", "Utilidades retenidas", 1)],
        "other_reserves": [("ESF", "Otras partidas del capital", 1)],
        "net_cash_operating": [("EFE", "Flujos netos de efectivo de actividades de operación", 1)],
        "net_cash_investing": [("EFE", "Flujos netos de efectivo de actividades de inversión", 1)],
        "net_cash_financing": [("EFE", "Flujos netos de efectivo de actividades de financiamiento", 1)],
        "fx_effect_on_cash": [("EFE", "Efectos por cambios en el valor del efectivo", 1)],
        "cash_at_beginning": [("EFE", "Efectivo al inicio del periodo", 1)],
        "dividends": [("EFE", "Dividendos decretados", -1)],
    }

    fields = {}
    for key, items in mapping.items():
        if items:
            fields[key] = {"cy": line(items, "cy"), "py": line(items, "py")}
        else:
            fields[key] = {"cy": {"value": 0, "cells": []}, "py": {"value": 0, "cells": []}}

    totals_spec = [
        ("ER", "Utilidad bruta", "gross_profit"),
        ("ER", "Utilidad de operación", "operating_profit"),
        ("ER", "Utilidad antes de impuestos a la utilidad", "profit_before_tax"),
        ("ER", "Utilidad neta del ejercicio", "profit_for_year"),
        ("ESF", "Total activo circulante", "total_current_assets"),
        ("ESF", "Total activo no circulante", "total_non_current_assets"),
        ("ESF", "Total activo", "total_assets"),
        ("ESF", "Total pasivo a corto plazo", "total_current_liabilities"),
        ("ESF", "Total pasivo a largo plazo", "total_non_current_liabilities"),
        ("ESF", "Total pasivo", "total_liabilities"),
        ("ESF", "Total capital contable", "total_equity"),
        ("ESF", "Total pasivo y capital contable", "total_equity_and_liabilities"),
        ("EFE", "Incremento (disminución) neto de efectivo", "net_change_in_cash"),
        ("EFE", "Efectivo al final del periodo", "cash_at_end"),
        # retained earnings statement on EFE
        ("EFE", "Utilidad neta del ejercicio", "profit_for_year"),
        ("EFE", "Saldo final", "retained_earnings"),
    ]
    source_totals = []
    for sheet, label, formula in totals_spec:
        for year in ("cy", "py"):
            source_totals.append({
                "sheet": sheet,
                "cell": cell_ref(sheet, label, year),
                "year": year,
                "factor": 1,
                "formula": formula,
            })

    ignored = []
    # note-reference columns
    for sheet in ("ER", "ESF", "EFE"):
        ws = sheets[sheet]["ws"]
        rows = [r for r in range(1, ws.max_row + 1)
                if isinstance(ws.cell(r, 2).value, (int, float))
                and not isinstance(ws.cell(r, 2).value, bool)]
        if rows:
            if len(rows) == 1:
                ignored.append({"sheet": sheet, "cell": f"B{rows[0]}",
                                "reason": "note reference number, not an amount"})
            else:
                ignored.append({"sheet": sheet, "range": f"B{rows[0]}:B{rows[-1]}",
                                "reason": "note reference numbers, not amounts"})
    for year in ("cy", "py"):
        ignored.append({
            "sheet": "EFE",
            "cell": cell_ref("EFE", "Saldo inicial", year),
            "reason": "opening retained earnings in the equity roll-forward; "
                      "equals prior-year closing balance already taken from the balance sheet",
        })

    ws_er = sheets["ER"]["ws"]
    source_name = ws_er["A1"].value

    return {
        "entity_code": "TW-MX01",
        "source_entity_name": source_name,
        "currency": "MXN",
        "unit": 1000,
        "period_end": {"cy": f"{cy_year}-12-31", "py": f"{py_year}-12-31"},
        "fields": fields,
        "source_totals": source_totals,
        "ignored": ignored,
        "source_exceptions": [],
        "notes": (
            "Workbook is in thousands of Mexican pesos (unit 1000, kept as is). "
            "Income tax expense is current plus deferred tax; the deferred credit is negative and reduces the charge. "
            "Employee profit sharing (PTU) payable is included in other current liabilities per the template. "
            "Employee benefits are mapped to provisions; short- and long-term bank loans to current and "
            "non-current borrowings. Dividends are shown negative in the source and are sign-flipped (factor -1). "
            "No investments or loans to group companies appear in the workbook. "
            "All printed totals, balance sheet, cash flow and retained earnings roll-forward were consistent."
        ),
    }
