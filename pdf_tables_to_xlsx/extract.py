"""PDF reading: page ranges, scanned-page detection, table extraction."""
import re
from dataclasses import dataclass, field
from pathlib import Path

import pdfplumber

from .normalize import normalize_table


class ToolError(Exception):
    """User-facing error."""


@dataclass
class Table:
    source: str
    page: int
    index: int
    rows: list


@dataclass
class PdfResult:
    name: str
    tables: list = field(default_factory=list)
    page_counts: dict = field(default_factory=dict)
    scanned: list = field(default_factory=list)


def parse_pages(spec: str) -> list[tuple[int, int]]:
    """Parse '1-3,5' into inclusive (start, end) ranges."""
    ranges = []
    for part in spec.split(","):
        m = re.fullmatch(r"(\d+)(?:-(\d+))?", part.strip())
        if not m:
            raise ToolError(f"Invalid --pages value {spec!r} (example: 1-3,5)")
        a, b = int(m[1]), int(m[2] or m[1])
        if a < 1 or b < a:
            raise ToolError(f"Invalid page range {part!r} in --pages")
        ranges.append((a, b))
    return ranges


def extract_pdf(path, ranges=None, header=True, clean=False, text_tables=False) -> PdfResult:
    """Extract normalized tables from one PDF."""
    p = Path(path)
    if not p.is_file():
        raise ToolError(f"Input file not found: {p}")
    with p.open("rb") as f:
        if b"%PDF-" not in f.read(1024):
            raise ToolError(f"Not a PDF file: {p}")
    settings = {"vertical_strategy": "text", "horizontal_strategy": "text"} if text_tables else {}
    res = PdfResult(p.name)
    try:
        with pdfplumber.open(p) as pdf:
            for num, page in enumerate(pdf.pages, 1):
                if ranges and not any(a <= num <= b for a, b in ranges):
                    continue
                if not (page.extract_text() or "").strip():
                    res.scanned.append(num)
                    res.page_counts[num] = 0
                    continue
                count = 0
                for raw in page.extract_tables(settings):
                    rows = normalize_table(raw, header, clean)
                    if rows:
                        count += 1
                        res.tables.append(Table(p.stem, num, count, rows))
                res.page_counts[num] = count
    except Exception as exc:  # pdfminer raises many types (encrypted, corrupt...)
        raise ToolError(
            f"Cannot read {p.name}: {type(exc).__name__}: {exc} "
            "(password-protected or corrupt PDFs are not supported)"
        ) from exc
    return res
