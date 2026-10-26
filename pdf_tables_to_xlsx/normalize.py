"""Table cleanup: whitespace, empty rows/cols, headers, numbers."""
import re
from decimal import Decimal

_CTRL = re.compile(r"[\x00-\x08\x0e-\x1f\x7f]")
_CUR = re.compile(r"[$€£¥₫₹]|\b(?:USD|EUR|GBP|JPY|VND|CAD|AUD)\b", re.I)
_US = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?|\.\d+")
_EU = re.compile(r"\d{1,3}(?:\.\d{3})+,\d+")


def _cell(value) -> str:
    if value is None:
        return ""
    return " ".join(_CTRL.sub("", str(value)).split())


def clean_number(text: str):
    """Return int/float for unambiguous numeric text, else the text unchanged."""
    s = _CUR.sub("", text).strip()
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg, s = True, s[1:-1].strip()
    if s.startswith(("-", "−")):
        neg, s = True, s[1:].strip()
    pct = s.endswith("%")
    if pct:
        s = s[:-1].strip()
    if _EU.fullmatch(s):
        s = s.replace(".", "").replace(",", ".")
    elif _US.fullmatch(s):
        s = s.replace(",", "")
    else:
        return text
    if re.match(r"0\d", s):  # likely an ID / code, keep as text
        return text
    value = Decimal(s)
    if pct:
        value /= 100
    if neg:
        value = -value
    return float(value) if pct or "." in s else int(value)


def _headers(cells: list[str]) -> list[str]:
    out, seen = [], set()
    for i, cell in enumerate(cells, 1):
        base = cell or f"Column_{i}"
        name, n = base, 2
        while name.lower() in seen:
            name, n = f"{base}_{n}", n + 1
        seen.add(name.lower())
        out.append(name)
    return out


def normalize_table(raw, header: bool = True, clean: bool = False) -> list[list]:
    """Return cleaned rows (header first if requested); [] if table is empty."""
    rows = [[_cell(c) for c in r] for r in raw or []]
    rows = [r for r in rows if any(r)]
    if not rows:
        return []
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    keep = [i for i in range(width) if any(r[i] for r in rows)]
    rows = [[r[i] for i in keep] for r in rows]
    head, body = (_headers(rows[0]), rows[1:]) if header else (None, rows)
    if clean:
        body = [[clean_number(c) if c else c for c in r] for r in body]
    return ([head] if head else []) + body
