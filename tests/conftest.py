import pytest


def _esc(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _content(tables) -> str:
    """Draw each table as a ruled grid with Helvetica text."""
    x0, w, h, y = 50, 90, 24, 740
    ops = ["q 0.5 w"]
    for rows in tables:
        nr, nc = len(rows), max(len(r) for r in rows)
        for r in range(nr + 1):
            ops.append(f"{x0} {y - r * h} m {x0 + nc * w} {y - r * h} l S")
        for c in range(nc + 1):
            ops.append(f"{x0 + c * w} {y} m {x0 + c * w} {y - nr * h} l S")
        for r, row in enumerate(rows):
            for c, text in enumerate(row):
                if text:
                    ops.append(f"BT /F1 10 Tf {x0 + c * w + 5} {y - r * h - 16} Td ({_esc(text)}) Tj ET")
        y -= nr * h + 40
    ops.append("Q")
    return "\n".join(ops)


def build_pdf(path, pages):
    """pages: list of pages; each page is a list of tables (list of rows of str)."""
    n = len(pages)
    kids = " ".join(f"{4 + 2 * i} 0 R" for i in range(n))
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        f"<< /Type /Pages /Kids [{kids}] /Count {n} >>".encode(),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    for i, tables in enumerate(pages):
        body = _content(tables).encode("latin-1")
        objs.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {5 + 2 * i} 0 R >>".encode()
        )
        objs.append(b"<< /Length %d >>\nstream\n" % len(body) + body + b"\nendstream")
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    path.write_bytes(bytes(out))
    return path


@pytest.fixture
def make_pdf():
    return build_pdf
