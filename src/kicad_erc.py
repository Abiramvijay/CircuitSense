import json
import re
import subprocess
import tempfile
from pathlib import Path

from analysis_result import AnalysisResult


def run_schematic_erc(schematic_path):
    """Run KiCad ERC and convert its violations to analysis results."""
    schematic_path = Path(schematic_path).resolve()
    temp_dir = tempfile.TemporaryDirectory(
        prefix="circuitsense_erc_"
    )
    report_path = Path(temp_dir.name) / "erc.json"

    try:
        completed = subprocess.run(
            [
                "kicad-cli",
                "sch", "erc",
                "--format", "json",
                "--output", str(report_path),
                str(schematic_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout).strip()
            message = "KiCad ERC could not check the schematic."
            if detail:
                message = f"{message}\n\n{detail}"
            raise RuntimeError(message)

        if not report_path.is_file():
            raise RuntimeError(
                "KiCad ERC did not create the expected report."
            )

        with report_path.open(encoding="utf-8") as report_file:
            report = json.load(report_file)

        if (
            not isinstance(report, dict)
            or not isinstance(report.get("sheets"), list)
        ):
            raise ValueError(
                "KiCad ERC returned an invalid report."
            )

        results = []
        for sheet in report.get("sheets", []):
            for violation in sheet.get("violations", []):
                violation_type = violation.get("type", "unknown")
                items = violation.get("items", [])
                references = []

                for item in items:
                    description = item.get("description", "")
                    match = re.match(r"Symbol\s+(\S+)", description)
                    if match and match.group(1) not in references:
                        references.append(match.group(1))

                item_descriptions = [
                    item["description"]
                    for item in items
                    if item.get("description")
                ]
                message = violation.get(
                    "description",
                    "KiCad reported a schematic ERC violation.",
                )
                if item_descriptions:
                    message = (
                        f"{message}: "
                        + "; ".join(item_descriptions)
                    )

                results.append(
                    AnalysisResult(
                        f"ERC_{violation_type.upper()}",
                        violation.get("severity", "warning"),
                        ", ".join(references) or None,
                        message,
                        "Review and correct this issue in the schematic.",
                    )
                )

        return results
    finally:
        temp_dir.cleanup()
