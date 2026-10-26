# PDF Tables to Excel/CSV Extractor

> **Windows app — no Python needed.** A ready-to-run `.exe` build of this tool is available on [Gumroad](https://duonghai8.gumroad.com/l/pdf_tables_to_xlsx) ($19.00). Buying it supports development; this source code stays free under the MIT license.

Turn text-based PDFs into pivot-ready Excel workbooks or CSV files, fully offline.
No network access, no telemetry, no system binaries.

- One sheet per table (named `file_pN_tM`), or one CSV per table
- Cleans output: trims whitespace, drops empty rows/columns, uses the first row
  as header (blank/duplicate headers become `Column_3`, `Col_2`)
- Optional `--clean-numbers`: `1,234.50`, `(120)`, `45%`, `$9.99` become real numbers
- Detects scanned/image-only pages (no text layer) and warns; exits non-zero if
  no tables were found
- Prints tables found per page; never overwrites output without `--force`

## Install

    pip install .          # Python 3.12+, installs pdfplumber and openpyxl

## Usage

    pdf_tables_to_xlsx input.pdf [more.pdf ...] -o out.xlsx [--format xlsx|csv]
        [--pages 1-3,5] [--clean-numbers] [--no-header] [--text-tables] [--force]

    pdf_tables_to_xlsx report.pdf -o report.xlsx --clean-numbers
    pdf_tables_to_xlsx a.pdf b.pdf --format csv -o out_dir --pages 1-2

- `-o` is a `.xlsx` file, or a directory when `--format csv` (CSV is UTF-8 with BOM for Excel).
- `--no-header` writes all rows as data, with no header row.
- `--text-tables` also detects tables without ruled lines (aligned text); may give false positives.
- Percentages are stored as fractions (`45%` becomes `0.45`).
- Exit code 0 on success, non-zero on any error.

## Limitations

- No OCR: scanned or image-only PDFs are detected and reported, not converted.
- Detection relies on ruled lines (or aligned text with `--text-tables`);
  complex layouts and merged cells may need manual review.
- Number conversion is heuristic; ambiguous formats (e.g. `12,5`, `007`) stay text.
- Password-protected PDFs are not supported.

## Tests

    pip install -r requirements.txt && pytest

## Windows app

Don't want to install Python? Get the ready-to-run Windows build (single `.exe`, runs fully offline) on [Gumroad](https://duonghai8.gumroad.com/l/pdf_tables_to_xlsx).

## License

MIT — see [LICENSE](LICENSE).
