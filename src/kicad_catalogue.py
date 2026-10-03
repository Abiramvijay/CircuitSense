
import csv
import json
import re
from pathlib import Path

LIBRARY_DIR = Path("/usr/share/kicad/symbols")
OUTPUT_DIR = Path("data")
JSON_FILE = OUTPUT_DIR / "kicad_component_catalogue.json"
CSV_FILE = OUTPUT_DIR / "kicad_component_catalogue.csv"


def extract_symbols(library_path):
    """Extract top-level symbols from a KiCad symbol library."""
    try:
        content = library_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        print(f"Skipping {library_path.name}: {error}")
        return []

    symbols = []
    depth = 0
    in_string = False
    escaped = False

    for index, char in enumerate(content):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
            continue

        if char == "(":
            if depth == 1:
                match = re.match(
                    r'\(\s*symbol\s+"((?:\\.|[^"\\])*)"',
                    content[index:]
                )
                if match:
                    symbols.append(match.group(1))

            depth += 1

        elif char == ")":
            depth -= 1

    return [
        {
            "library": library_path.stem,
            "symbol": name,
            "library_id": f"{library_path.stem}:{name}"
        }
        for name in symbols
    ]


def main():
    if not LIBRARY_DIR.is_dir():
        print(f"KiCad symbol directory not found: {LIBRARY_DIR}")
        return

    library_files = sorted(LIBRARY_DIR.glob("*.kicad_sym"))

    if not library_files:
        print("No KiCad symbol libraries found.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    catalogue = []

    for library_path in library_files:
        catalogue.extend(extract_symbols(library_path))

    catalogue.sort(
        key=lambda item: (item["library"], item["symbol"])
    )

    with JSON_FILE.open("w", encoding="utf-8") as file:
        json.dump(catalogue, file, indent=2, ensure_ascii=False)

    with CSV_FILE.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["library", "symbol", "library_id"]
        )
        writer.writeheader()
        writer.writerows(catalogue)

    print("KiCad component catalogue generated.")
    print(f"Libraries scanned: {len(library_files)}")
    print(f"Symbols found: {len(catalogue)}")
    print(f"JSON: {JSON_FILE}")
    print(f"CSV: {CSV_FILE}")


if __name__ == "__main__":
    main()