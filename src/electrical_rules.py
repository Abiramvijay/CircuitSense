from analysis_result import AnalysisResult
from component_classifier import classify_component_with_support


def parse_resistance(value):
    """Parse a resistor value into ohms."""

    if value is None:
        return None

    text = str(value).strip().lower()

    if not text:
        return None

    multipliers = {
        "k": 1_000,
        "m": 1_000_000,
        "meg": 1_000_000,
    }

    try:
        for suffix, multiplier in multipliers.items():
            if text.endswith(suffix):
                number = float(
                    text[:-len(suffix)].strip()
                )

                return number * multiplier

        return float(text)

    except (TypeError, ValueError):
        return None


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

        value = component.get("value")

        resistance = parse_resistance(value)

        if resistance is None:
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