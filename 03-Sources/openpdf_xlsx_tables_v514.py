"""V51.4 opt-in editable PDF table worksheets with fail-closed source audit.

PyMuPDF detects geometric tables heuristically; exact extraction consistency
is verified, not semantic correctness or original Excel formatting.
Author: Abdelhalim Talbi.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz
from openpyxl import load_workbook

MAX_TABLES = 256
MAX_CELLS = 200_000
MAX_ROWS_PER_TABLE = 4096
MAX_COLUMNS = 128
MAX_CELL_UTF16 = 32767


@dataclass(frozen=True)
class TableEvidence:
    tables: int
    cells: int
    pages_with_tables: tuple[int, ...]



def _merged_regions(table, matrix, columns):
    """Map only geometrically proven PDF spans to Excel merged cells.

    PyMuPDF represents covered cells as None in ``table.rows[*].cells``.
    No merge is inferred from text, whitespace or visual proximity alone.
    Ambiguous geometry aborts the opt-in conversion rather than guessing.
    Returns (start_row, start_col, end_row, end_col) in Excel coordinates.
    """
    geometry = [tuple(row.cells) for row in table.rows]
    if len(geometry) != len(matrix) or any(len(row) != columns for row in geometry):
        raise ValueError('Grille PDF incoherente : fusion non fiable')
    if not any(cell is None for row in geometry for cell in row):
        return ()

    def edges(axis):
        values = [float(table.bbox[axis]), float(table.bbox[axis + 2])]
        for row in geometry:
            for rect in row:
                if rect is not None:
                    values.extend((float(rect[axis]), float(rect[axis + 2])))
        values.sort()
        groups = []
        for value in values:
            if not groups or abs(value - groups[-1][-1]) > 0.75:
                groups.append([value])
            else:
                groups[-1].append(value)
        return [sum(group) / len(group) for group in groups]

    x_edges, y_edges = edges(0), edges(1)
    if len(x_edges) != columns + 1 or len(y_edges) != len(matrix) + 1:
        raise ValueError('Frontieres de cellules PDF ambigues : fusion refusee')

    def boundary(value, candidates):
        matches = [i for i, edge in enumerate(candidates) if abs(float(value) - edge) <= 0.75]
        if len(matches) != 1:
            raise ValueError('Cellule PDF hors grille : fusion refusee')
        return matches[0]

    owners = {}
    merged = []
    for row_number, row in enumerate(geometry):
        for column_number, rect in enumerate(row):
            if rect is None:
                continue
            x0, y0, x1, y1 = rect
            c0, c1 = boundary(x0, x_edges), boundary(x1, x_edges)
            r0, r1 = boundary(y0, y_edges), boundary(y1, y_edges)
            if (r0, c0) != (row_number, column_number) or r1 <= r0 or c1 <= c0:
                raise ValueError('Ancrage de cellule PDF incoherent')
            for r in range(r0, r1):
                for c in range(c0, c1):
                    if (r, c) in owners:
                        raise ValueError('Cellules PDF chevauchantes')
                    owners[(r, c)] = (row_number, column_number)
            if r1 - r0 > 1 or c1 - c0 > 1:
                merged.append((r0 + 3, c0 + 1, r1 + 2, c1))
    for r, row in enumerate(geometry):
        for c, rect in enumerate(row):
            if (r, c) not in owners:
                raise ValueError('Cellule PDF sans ancrage')
            if (rect is None) != (owners[(r, c)] != (r, c)):
                raise ValueError('Fusion PDF incoherente')
    return tuple(sorted(merged))


def _sheet_merges(sheet):
    return tuple(sorted((m.min_row, m.min_col, m.max_row, m.max_col)
                        for m in sheet.merged_cells.ranges))


def _tables(source):
    count = 0
    cells = 0
    pages = []
    with fitz.open(source) as pdf:
        if pdf.needs_pass:
            raise ValueError('PDF chiffre : extraction des tableaux refusee')
        for page_number, page in enumerate(pdf, 1):
            if page_number > 9999:
                raise ValueError('Nombre de pages hors limite du mode tableaux')
            found = page.find_tables()
            for table_number, table in enumerate(found.tables, 1):
                count += 1
                if count > MAX_TABLES or table_number > 999:
                    raise ValueError('Trop de tableaux detectes')
                matrix = table.extract()
                if not matrix or len(matrix) > MAX_ROWS_PER_TABLE:
                    raise ValueError('Dimensions de tableau invalides')
                columns = max((len(row) for row in matrix), default=0)
                if not 1 <= columns <= MAX_COLUMNS:
                    raise ValueError('Nombre de colonnes hors limite')
                for row in matrix:
                    if len(row) > columns:
                        raise ValueError('Tableau irregulier')
                    for value in row:
                        if value is not None and not isinstance(value, str):
                            raise ValueError('Cellule PDF non textuelle')
                        if value is not None and len(value.encode('utf-16-le')) // 2 > MAX_CELL_UTF16:
                            raise ValueError('Cellule Excel trop longue : pas de troncature')
                cells += len(matrix) * columns
                if cells > MAX_CELLS:
                    raise ValueError('Trop de cellules detectees')
                if page_number not in pages:
                    pages.append(page_number)
                merges = _merged_regions(table, matrix, columns)
                yield page_number, table_number, matrix, columns, merges
    if count == 0:
        raise ValueError('Aucun tableau detecte : aucune sortie enrichie')


def _expected(source):
    result = list(_tables(source))
    return result, TableEvidence(len(result), sum(len(rows) * width for _, _, rows, width, _ in result),
                                 tuple(dict.fromkeys(page for page, _, _, _, _ in result)))


def enrich_xlsx_with_tables(source, destination):
    """Add editable table worksheets to the legacy text-preserving XLSX stage.

    Must be called only on a private temporary workbook, before atomic publish.
    """
    source, destination = Path(source), Path(destination)
    expected, evidence = _expected(source)
    wb = load_workbook(destination)
    try:
        if len(wb.worksheets) != 1 or wb.worksheets[0].title != 'Texte PDF':
            raise ValueError('Classeur Excel source inattendu')
        for page, index, rows, columns, merges in expected:
            sheet = wb.create_sheet(f'P{page:04d}-T{index:03d}')
            sheet['A1'] = 'Page PDF'
            sheet['B1'] = page
            sheet['C1'] = 'Tableau'
            sheet['D1'] = index
            for row_number, row in enumerate(rows, 3):
                for column_number in range(1, columns + 1):
                    value = row[column_number - 1] if column_number <= len(row) else None
                    if value not in (None, ""):
                        cell = sheet.cell(row_number, column_number, value)
                        cell.data_type = 's'  # Never evaluate a PDF-origin Excel formula.
            for r0, c0, r1, c1 in merges:
                sheet.merge_cells(start_row=r0, start_column=c0,
                                  end_row=r1, end_column=c1)
        wb.save(destination)
    finally:
        wb.close()
    verify_xlsx_tables(source, destination)
    return evidence


def verify_xlsx_tables(source, destination):
    """Re-extract source tables and compare every cell to the saved workbook."""
    expected, evidence = _expected(source)
    wb = load_workbook(destination, read_only=False, data_only=False)
    try:
        if len(wb.worksheets) != len(expected) + 1 or wb.worksheets[0].title != 'Texte PDF':
            raise ValueError('Feuilles Excel manquantes ou supplementaires')
        for position, (page, index, rows, columns, merges) in enumerate(expected, 1):
            sheet = wb.worksheets[position]
            if sheet.title != f'P{page:04d}-T{index:03d}':
                raise ValueError('Ordre ou nom des tableaux Excel invalide')
            if (sheet['A1'].value, sheet['B1'].value, sheet['C1'].value, sheet['D1'].value) != ('Page PDF', page, 'Tableau', index):
                raise ValueError('Provenance du tableau Excel invalide')
            if _sheet_merges(sheet) != merges:
                raise ValueError('Fusions de cellules Excel modifiees ou manquantes')
            if sheet.max_row != len(rows) + 2 or sheet.max_column != max(columns, 4):
                raise ValueError('Dimensions du tableau Excel modifiees')
            for row_number, row in enumerate(rows, 3):
                for column_number in range(1, columns + 1):
                    cell = sheet.cell(row_number, column_number)
                    value = row[column_number - 1] if column_number <= len(row) else None
                    if cell.value != (None if value == '' else value) or cell.data_type == 'f':
                        raise ValueError('Cellule de tableau Excel modifiee ou formule')
        return evidence
    finally:
        wb.close()
