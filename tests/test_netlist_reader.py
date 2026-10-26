import tempfile
import unittest
from pathlib import Path

from netlist_reader import load_circuit


class NetlistReaderValidationTests(unittest.TestCase):
    def test_rejects_non_kicad_xml(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            xml_path = Path(temp_dir) / "not-a-netlist.xml"
            xml_path.write_text("<root/>", encoding="utf-8")

            with self.assertRaisesRegex(
                ValueError,
                "not a KiCad netlist",
            ):
                load_circuit(xml_path)

    def test_rejects_netlist_missing_sections(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            xml_path = Path(temp_dir) / "incomplete.xml"
            xml_path.write_text(
                "<export><components/></export>",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError,
                "missing its components or nets",
            ):
                load_circuit(xml_path)

    def test_loads_kicad_netlist_sections(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            xml_path = Path(temp_dir) / "valid.xml"
            xml_path.write_text(
                "<export><components/><nets/></export>",
                encoding="utf-8",
            )

            self.assertEqual(
                load_circuit(xml_path),
                {"components": [], "nets": []},
            )


if __name__ == "__main__":
    unittest.main()
