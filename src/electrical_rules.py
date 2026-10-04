import math

from analysis_result import AnalysisResult
from component_classifier import classify_component_with_support
from specification_extractor import parse_engineering_value


def parse_resistance(value):
    """Parse a resistor value into ohms."""
    return parse_engineering_value(value, "ohm")


def check_resistor_values(model):
    """
    Check every recognized resistor for a valid
    positive resistance value.
    """

    results = []

    for component in model.components:
        recognition = classify_component_with_support(
            component
        )

        component_type = recognition.get("type")

        if component_type != "resistor":
            continue

        reference = component.get(
            "reference",
            "Unknown resistor"
        )

        resistance = model.get_component_specification(
            reference,
            "resistance",
        )
        if resistance is None:
            resistance = parse_resistance(component.get("value"))

        if (
            not isinstance(resistance, (int, float))
            or not math.isfinite(float(resistance))
        ):
            results.append(
                AnalysisResult(
                    "RES_002",
                    "warning",
                    reference,
                    (
                        f"Resistor {reference} has a "
                        "missing or invalid resistance value."
                    ),
                    (
                        "Enter a valid positive resistance "
                        "value such as 220, 1k, or 10k."
                    ),
                )
            )

        elif resistance <= 0:
            value = component.get("value")
            results.append(
                AnalysisResult(
                    "RES_002",
                    "warning",
                    reference,
                    (
                        f"Resistor {reference} has a "
                        f"non-positive resistance value "
                        f"({value})."
                    ),
                    (
                        "Use a resistance value greater "
                        "than zero."
                    ),
                )
            )

    return results