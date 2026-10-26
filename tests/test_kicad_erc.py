import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from kicad_erc import run_schematic_erc


class SchematicErcTests(unittest.TestCase):
    @patch("kicad_erc.subprocess.run")
    def test_converts_kicad_violations_to_analysis_results(self, run):
        def write_report(command, **kwargs):
            report_path = Path(
                command[command.index("--output") + 1]
            )
            report_path.write_text(
                json.dumps(
                    {
                        "sheets": [
                            {
                                "violations": [
                                    {
                                        "type": "pin_not_connected",
                                        "severity": "error",
                                        "description": "Pin not connected",
                                        "items": [
                                            {
                                                "description": (
                                                    "Symbol U2 Pin 9 "
                                                    "[VDDA, Power input]"
                                                )
                                            }
                                        ],
                                    }
                                ]
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            return SimpleNamespace(
                returncode=0,
                stdout="",
                stderr="",
            )

        run.side_effect = write_report

        results = run_schematic_erc("board.kicad_sch")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].rule_id, "ERC_PIN_NOT_CONNECTED")
        self.assertEqual(results[0].severity, "error")
        self.assertEqual(results[0].component, "U2")
        self.assertIn("Pin not connected", results[0].message)

    @patch("kicad_erc.subprocess.run")
    def test_fails_when_kicad_erc_cannot_run(self, run):
        run.return_value = SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="invalid schematic",
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "invalid schematic",
        ):
            run_schematic_erc("broken.kicad_sch")


if __name__ == "__main__":
    unittest.main()
