"""V51.4 opt-in editable PDF table worksheets with fail-closed source audit.

PyMuPDF detects geometric tables heuristically; exact extraction consistency
is verified, not semantic correctness or original Excel formatting.
Author: Abdelhalim Talbi.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from statistics import median

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


def _text_table_candidates(page, clip=None):
    """Conservative text-grid fallback inside an unruled page region.

    Require multiple aligned rows with visible inter-column gutters; this
    rejects common prose falsely segmented into columns by PyMuPDF. Remove
    blank spacer rows, but never infer merged cells from whitespace.
    """
    words = page.get_text('words', clip=clip)
    for table in page.find_tables(strategy='text', clip=clip).tables:
        matrix = table.extract()
        width = max((len(row) for row in matrix), default=0)
        if not 2 <= width <= MAX_COLUMNS or len(table.rows) != len(matrix):
            continue
        if any(cell is None for row in table.rows for cell in row.cells):
            continue
        dense = []
        for row, geometry in zip(matrix, table.rows):
            if len(row) != width or len(geometry.cells) != width:
                dense = []
                break
            nonempty = sum(value not in (None, '') for value in row)
            if nonempty >= 2:
                dense.append((list(row), geometry))
            elif nonempty == 1:
                # Reject a merged-like header within the grid. A page title
                # far above the first table row may be ignored safely.
                if dense:
                    dense = []
                    break
        if len(dense) < 3 or len(dense) > MAX_ROWS_PER_TABLE:
            continue
        # A single-cell page heading before the table is permitted only if
        # there is a clear vertical gap to the first dense table row.
        first = next((i for i, row in enumerate(matrix)
                      if sum(v not in (None, '') for v in row) >= 2), None)
        if first is None:
            continue
        preceding = [i for i, row in enumerate(matrix[:first])
                     if any(v not in (None, '') for v in row)]
        if preceding:
            if len(preceding) != 1:
                continue
            centers = [((g.cells[0][1] + g.cells[0][3]) / 2) for _, g in dense]
            pitch = min((centers[i+1] - centers[i] for i in range(len(centers)-1)), default=0)
            title_rect = table.rows[preceding[0]].cells[0]
            title_y = (title_rect[1] + title_rect[3]) / 2
            if pitch <= 0 or centers[0] - title_y < pitch * 1.8:
                continue
        rows = [row for row, _ in dense]
        counts = [sum(row[c] not in (None, '') for row in rows) for c in range(width)]
        if min(counts) < 3 or sum(counts) * 4 < len(rows) * width * 3:
            continue
        # Validate real whitespace between adjacent columns, not just the
        # artificial cell boundaries returned by the text-table heuristic.
        gutters = 0
        for row, geometry in dense:
            boxes = []
            for col, value in enumerate(row):
                if value in (None, ''):
                    boxes.append(None)
                    continue
                rect = geometry.cells[col]
                found = [w for w in words if rect[0] <= (w[0]+w[2])/2 < rect[2]
                         and rect[1] <= (w[1]+w[3])/2 < rect[3]]
                boxes.append((min(w[0] for w in found), max(w[2] for w in found)) if found else None)
            for left, right in zip(boxes, boxes[1:]):
                if left is not None and right is not None:
                    if right[0] - left[1] < 12:
                        break
                    gutters += 1
            else:
                continue
            break
        else:
            if gutters >= len(rows):
                yield rows, width, tuple(table.bbox)


def _text_subclips(page, clip):
    """Split distant blocks before PyMuPDF can merge their column boundaries.

    The text strategy derives global x-columns from *all* visible words.
    A distant prose paragraph can split every table cell into fragments.
    Partition at unusually large vertical gaps between text baselines.
    """
    region = fitz.Rect(clip if clip is not None else page.rect)
    words = page.get_text('words', clip=region)
    centers = sorted((w[1] + w[3]) / 2 for w in words)
    lines = []
    for y in centers:
        if not lines or y - lines[-1][-1] > 3.5:
            lines.append([y])
        else:
            lines[-1].append(y)
    ys = [median(line) for line in lines]
    gaps = [b - a for a, b in zip(ys, ys[1:]) if b > a]
    if len(gaps) < 2:
        return (region,)
    small = sorted(gaps)[:max(1, (len(gaps) + 1) // 2)]
    threshold = max(45.0, 2.5 * median(small))
    boundaries = [(a + b) / 2 for a, b in zip(ys, ys[1:])
                  if b - a > threshold]
    if len(boundaries) > 32:
        raise ValueError('Texte trop fragmente : detection refusee')
    edges = [region.y0, *boundaries, region.y1]
    return tuple(fitz.Rect(region.x0, a, region.x1, b)
                 for a, b in zip(edges, edges[1:]) if b - a > 12)


def _text_only_tables(page, clip=None):
    for segment in _text_subclips(page, clip):
        yield from _text_table_candidates(page, segment)


def _rect_overlap(a, b):
    """True only for a positive-area intersection of two bounding boxes."""
    return max(a[0], b[0]) < min(a[2], b[2]) and max(a[1], b[1]) < min(a[3], b[3])


def _unruled_regions(page_rect, ruled_boxes, *, padding=2.0, limit=64):
    """Partition the page into disjoint rectangles excluding ruled tables.

    Using disjoint clips avoids the text heuristic merging separated tables or
    re-extracting ruled content. Cap fragments to prevent pathological pages.
    """
    free = [fitz.Rect(page_rect)]
    for box in ruled_boxes:
        b = fitz.Rect(box)
        b = fitz.Rect(b.x0 - padding, b.y0 - padding,
                      b.x1 + padding, b.y1 + padding) & page_rect
        next_free = []
        for region in free:
            overlap = region & b
            if overlap.is_empty or overlap.get_area() <= 0:
                next_free.append(region)
                continue
            pieces = (
                fitz.Rect(region.x0, region.y0, region.x1, overlap.y0),
                fitz.Rect(region.x0, overlap.y1, region.x1, region.y1),
                fitz.Rect(region.x0, overlap.y0, overlap.x0, overlap.y1),
                fitz.Rect(overlap.x1, overlap.y0, region.x1, overlap.y1),
            )
            next_free.extend(p for p in pieces if p.width > 12 and p.height > 12)
        if len(next_free) > limit:
            raise ValueError('Page trop fragmentee : detection mixte refusee')
        free = next_free
    return tuple(free)


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
            # Mixed pages: keep ruled tables, then inspect only geometrically
            # disjoint regions. Whole-page text detection can merge a ruled
            # table and a borderless table into a fictitious single grid.
            ruled = list(found.tables)
            candidates = [(table.extract(), None, table) for table in ruled]
            for clip in _unruled_regions(page.rect, [table.bbox for table in ruled]):
                for rows, width, bbox in _text_only_tables(page, clip=clip):
                    if any(_rect_overlap(bbox, table.bbox) for table in ruled):
                        raise ValueError('Tableau textuel chevauche un tableau borde')
                    candidates.append((rows, width, None))
            for table_number, (matrix, text_width, table) in enumerate(candidates, 1):
                count += 1
                if count > MAX_TABLES or table_number > 999:
                    raise ValueError('Trop de tableaux detectes')
                if not matrix or len(matrix) > MAX_ROWS_PER_TABLE:
                    raise ValueError('Dimensions de tableau invalides')
                columns = text_width if text_width is not None else max((len(row) for row in matrix), default=0)
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
                merges = () if table is None else _merged_regions(table, matrix, columns)
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
