"""Command-line interface."""
import argparse
import sys
from pathlib import Path

from .extract import ToolError, extract_pdf, parse_pages
from .writer import unique_name, write_csv, write_xlsx


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pdf_tables_to_xlsx",
        description="Extract tables from text-based PDFs into Excel or CSV (offline, no OCR).",
    )
    p.add_argument("inputs", nargs="+", help="input PDF file(s)")
    p.add_argument("-o", "--output", required=True, help=".xlsx file, or directory for csv")
    p.add_argument("--format", choices=["xlsx", "csv"], default="xlsx")
    p.add_argument("--pages", help="page ranges, e.g. 1-3,5")
    p.add_argument("--clean-numbers", action="store_true", help="convert '1,234.50', '(120)', '45%%', '$9.99' to numbers")
    p.add_argument("--no-header", action="store_true", help="do not treat the first row as a header")
    p.add_argument("--text-tables", action="store_true", help="also detect tables without ruled lines (aligned text)")
    p.add_argument("--force", action="store_true", help="overwrite existing output")
    return p


def run(args) -> None:
    out = Path(args.output)
    is_xlsx = args.format == "xlsx"
    if is_xlsx and out.suffix.lower() != ".xlsx":
        raise ToolError("Output for --format xlsx must end with .xlsx")
    if is_xlsx and out.is_dir():
        raise ToolError(f"Output path is a directory: {out}")
    if not is_xlsx and out.exists() and not out.is_dir():
        raise ToolError(f"For --format csv, output must be a directory: {out}")
    inputs = [Path(i) for i in args.inputs]
    if out.resolve() in {i.resolve() for i in inputs}:
        raise ToolError("Output path must differ from the input files")
    ranges = parse_pages(args.pages) if args.pages else None

    named, used, scanned_total = [], set(), 0
    for path in inputs:
        res = extract_pdf(path, ranges, not args.no_header, args.clean_numbers, args.text_tables)
        for page, n in res.page_counts.items():
            print(f"{res.name}: page {page}: {n} table(s)")
        for page in res.scanned:
            print(f"warning: {res.name} page {page} has no text layer (scanned/image-only); "
                  "OCR is not supported", file=sys.stderr)
        scanned_total += len(res.scanned)
        named += [(unique_name(t.source, t.page, t.index, used), t.rows) for t in res.tables]

    if not named:
        hint = (f" {scanned_total} page(s) have no text layer (scanned/image-only); OCR is not supported."
                if scanned_total else "")
        raise ToolError("No tables found." + hint)

    targets = [out] if is_xlsx else [out / f"{n}.csv" for n, _ in named]
    existing = [t for t in targets if t.exists()]
    if existing and not args.force:
        raise ToolError(f"Output exists: {existing[0]} (use --force to overwrite)")
    (out.parent if is_xlsx else out).mkdir(parents=True, exist_ok=True)
    if is_xlsx:
        write_xlsx(out, named)
    else:
        for target, (_, rows) in zip(targets, named):
            write_csv(target, rows)
    print(f"Wrote {len(named)} table(s) to {out}")


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        run(args)
    except ToolError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
