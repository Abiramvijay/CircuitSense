import unittest

from circuit_analyzer import analyze_circuit
from component_classifier import classify_component
from specification_extractor import (
    extract_specifications,
    parse_engineering_value,
)


class ResistanceParsingTests(unittest.TestCase):
    def test_kicad_resistor_notation(self):
        examples = {
            "1k5": 1500,
            "2k2": 2200,
            "4k7": 4700,
            "10k": 10000,
            "100R": 100,
            "220": 220,
        }

        for raw_value, expected in examples.items():
            with self.subTest(raw_value=raw_value):
                self.assertEqual(
                    parse_engineering_value(raw_value, "ohm"),
                    expected,
                )

    def test_resistor_rule_uses_extracted_1k5_value(self):
        circuit = {
            "components": [
                {
                    "reference": "R1",
                    "value": "1k5",
                    "lib_id": "Device:R",
                    "pins": [],
                }
            ],
            "nets": [],
        }

        results = analyze_circuit(circuit)

        self.assertFalse(
            any(
                result.rule_id == "RES_002"
                and result.component == "R1"
                for result in results
            )
        )

    def test_resistor_rule_still_reports_missing_value(self):
        circuit = {
            "components": [
                {
                    "reference": "R1",
                    "value": "",
                    "lib_id": "Device:R",
                    "pins": [],
                }
            ],
            "nets": [],
        }

        results = analyze_circuit(circuit)

        self.assertTrue(
            any(
                result.rule_id == "RES_002"
                and result.component == "R1"
                and "missing or invalid resistance value" in result.message
                for result in results
            )
        )


class CrystalRecognitionTests(unittest.TestCase):
    def test_crystal_gnd24_library_symbol_is_classified_as_crystal(self):
        component = {
            "reference": "Y1",
            "value": "16MHz",
            "lib_id": "Device:Crystal_GND24",
        }

        self.assertEqual(classify_component(component), "crystal")

    def test_crystal_is_not_inferred_only_from_reference_prefix(self):
        component = {
            "reference": "Y1",
            "value": "16MHz",
            "lib_id": "",
        }

        self.assertEqual(classify_component(component), "unknown")

    def test_crystal_frequency_is_extracted_from_value(self):
        component = {
            "reference": "Y1",
            "value": "16MHz",
            "lib_id": "Device:Crystal_GND24",
        }

        frequency = extract_specifications(component)["specifications"][
            "frequency"
        ]

        self.assertEqual(frequency["value"], 16_000_000)
        self.assertEqual(frequency["unit"], "Hz")
        self.assertEqual(frequency["raw_value"], "16MHz")
        self.assertEqual(frequency["source"], "kicad_value")


if __name__ == "__main__":
    unittest.main()
