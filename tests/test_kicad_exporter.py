import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from kicad_exporter import export_schematic_netlist


class SchematicNetlistExportTests(unittest.TestCase):
    @patch("kicad_exporter.subprocess.run")
    def test_exports_schematic_to_temporary_netlist(self, run):
        def create_netlist(command, **kwargs):
            output_path = Path(command[command.index("--output") + 1])
            output_path.write_text(
                "<export><components/><nets/></export>",
                encoding="utf-8",
            )
            return SimpleNamespace(
                returncode=0,
                stdout="",
                stderr="",
            )

        run.side_effect = create_netlist

        temp_dir, netlist_path = export_schematic_netlist(
            "board.kicad_sch"
        )
        self.addCleanup(temp_dir.cleanup)

        self.assertTrue(netlist_path.is_file())
        self.assertEqual(netlist_path.name, "circuit.xml")
        run.assert_called_once()
        self.assertIn("board.kicad_sch", run.call_args.args[0][-1])

    @patch("kicad_exporter.subprocess.run")
    def test_reports_kicad_export_errors(self, run):
        run.return_value = SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="invalid schematic",
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "invalid schematic",
        ):
            export_schematic_netlist("broken.kicad_sch")

    @patch("kicad_exporter.subprocess.run")
    def test_propagates_missing_kicad_cli(self, run):
        run.side_effect = FileNotFoundError("kicad-cli")

        with self.assertRaises(FileNotFoundError):
            export_schematic_netlist("board.kicad_sch")


if __name__ == "__main__":
    unittest.main()
