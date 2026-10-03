import math

from analysis_result import AnalysisResult
from circuit_model import CircuitModel
from component_classifier import classify_component_with_support
from connectivity_analyzer import (
    find_led_resistor_pairs as find_simple_series_pairs
)
from specification_extractor import extract_specifications
from rule_engine import RuleEngine
from topology_rules import check_net_connectivity
from electrical_rules import check_resistor_values
from rule_definitions import LED_001_REQUIREMENTS


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


def calculate_led_current(
    supply_voltage,
    forward_voltage,
    resistance,
):
    """Calculate LED current using Ohm's law."""

    if resistance <= 0:
        raise ValueError(
            "Resistance must be greater than zero."
        )

    voltage_across_resistor = (
        supply_voltage - forward_voltage
    )

    if voltage_across_resistor <= 0:
        raise ValueError(
            "Supply voltage must be greater than LED "
            "forward voltage."
        )

    return voltage_across_resistor / resistance


def calculate_resistor_power(
    current,
    resistance,
):
    """Calculate resistor power using P = I^2 R."""

    return current ** 2 * resistance


def recognize_components(circuit):
    """Recognize components and extract specifications."""

    recognized = []

    for component in circuit["components"]:
        recognition = classify_component_with_support(
            component
        )

        specification_data = extract_specifications(
            component
        )

        support_info = (
            recognition.get("support_info") or {}
        )

        recognized_component = {
            **component,
            "recognition": {
                **recognition,
                "category": support_info.get(
                    "category"
                ),
                "subtype": support_info.get(
                    "subtype"
                ),
            },
            "specification_data": specification_data,
        }

        recognized.append(
            recognized_component
        )

    return recognized


def get_extracted_value(
    component,
    specification,
):
    """Return one extracted specification value."""

    specification_data = component.get(
        "specification_data",
        {},
    )

    specifications = specification_data.get(
        "specifications",
        {},
    )

    item = specifications.get(
        specification
    )

    if not isinstance(item, dict):
        return None

    if item.get("status") != "extracted":
        return None

    value = item.get("value")

    if isinstance(
        value,
        (int, float),
    ) and math.isfinite(
        float(value)
    ):
        return float(value)

    return None


def get_model_specification(
    model,
    reference,
    specification,
):
    """Return a specification value from CircuitModel."""

    if model is None:
        return None

    return model.get_component_specification(
        reference,
        specification,
    )


def find_specification_on_connected_components(
    model,
    reference,
    specification,
):
    """
    Search directly connected components for a requested
    specification.

    Returns:
        (value, reference) if found
        (None, None) if not found
    """

    if model is None:
        return None, None

    connected_components = (
        model.get_connected_components(
            reference
        )
    )

    for connected_reference in connected_components:
        value = get_model_specification(
            model,
            connected_reference,
            specification,
        )

        if value is not None:
            return (
                value,
                connected_reference,
            )

    return None, None


def find_led_resistor_pairs(
    model,
):
    """Find LED-resistor pairs using CircuitModel topology."""

    from connectivity_analyzer import (
        find_led_resistor_pairs_from_model
    )

    return find_led_resistor_pairs_from_model(
        model
    )


def resolve_led_rule_requirements(
    model,
    led_reference,
    resistor_reference,
):
    """
    Resolve LED_001 requirements using the actual
    components involved in the detected LED-resistor circuit.
    """

    resolved = {
        "available": {},
        "missing_required": [],
        "missing_optional": [],
    }

    # ----------------------------------------------
    # LED specifications
    # ----------------------------------------------

    led_specifications = (
        model.get_component_specifications(
            led_reference
        )
    )

    # ----------------------------------------------
    # Resistor specifications
    # ----------------------------------------------

    resistor_specifications = (
        model.get_component_specifications(
            resistor_reference
        )
    )

    # ----------------------------------------------
    # Check each LED_001 requirement
    # ----------------------------------------------

    for requirement in (
        LED_001_REQUIREMENTS.get_all()
    ):
        specification = (
            requirement.specification
        )

        value = None

        # LED forward voltage
        if specification == "forward_voltage":
            value = (
                led_specifications
                .get(specification, {})
                .get("value")
            )

        # LED forward current
        elif specification == "forward_current":
            value = (
                led_specifications
                .get(specification, {})
                .get("value")
            )

        # Resistor resistance
        elif specification == "resistance":
            value = (
                resistor_specifications
                .get(specification, {})
                .get("value")
            )

        # Supply voltage can belong to a connected
        # power source rather than the LED itself.
        elif specification == "supply_voltage":
            value, source_reference = (
                find_specification_on_connected_components(
                    model,
                    led_reference,
                    "supply_voltage",
                )
            )

            if value is not None:
                resolved["available"][
                    specification
                ] = {
                    "value": value,
                    "source": source_reference,
                }

                continue

        if value is not None:
            resolved["available"][
                specification
            ] = {
                "value": value,
                "source": (
                    led_reference
                    if specification
                    in {
                        "forward_voltage",
                        "forward_current",
                    }
                    else resistor_reference
                ),
            }

        elif requirement.required:
            resolved["missing_required"].append(
                specification
            )

        else:
            resolved["missing_optional"].append(
                specification
            )

    return resolved


def analyze_led_resistor_pair(
    led,
    resistor,
    inputs,
    model=None,
):
    """
    Analyze an LED-resistor pair.

    LED_001 requirements are resolved from the actual
    components participating in the detected circuit.
    """

    results = []

    led_ref = led.get(
        "reference",
        "Unknown LED",
    )

    resistor_ref = resistor.get(
        "reference",
        "Unknown resistor",
    )

    # --------------------------------------------------
    # Resolve rule requirements
    # --------------------------------------------------

    requirement_data = (
        resolve_led_rule_requirements(
            model,
            led_ref,
            resistor_ref,
        )
    )

    available = requirement_data[
        "available"
    ]

    missing_required = requirement_data[
        "missing_required"
    ]

    # --------------------------------------------------
    # Resistor resistance
    # --------------------------------------------------

    resistance = (
        available
        .get("resistance", {})
        .get("value")
    )

    if resistance is None:
        # RES_002 owns resistor-value validation.
        return results

    try:
        resistance = float(
            resistance
        )

    except (TypeError, ValueError):
        return results

    if resistance <= 0:
        return results

    # --------------------------------------------------
    # Supply voltage
    # --------------------------------------------------

    supply_voltage = inputs.get(
        "supply_voltage"
    )

    if supply_voltage is None:
        supply_voltage = (
            available
            .get("supply_voltage", {})
            .get("value")
        )

    # --------------------------------------------------
    # Forward voltage
    # --------------------------------------------------

    forward_voltage = inputs.get(
        "forward_voltage"
    )

    if forward_voltage is None:
        forward_voltage = (
            available
            .get("forward_voltage", {})
            .get("value")
        )

    # --------------------------------------------------
    # Required specification check
    # --------------------------------------------------

    # Start with the requirements identified by the
    # rule-definition system.
    missing_required = set(
        missing_required
    )

    # GUI-provided values override missing schematic
    # specifications.
    if supply_voltage is not None:
        missing_required.discard(
            "supply_voltage"
        )

    if forward_voltage is not None:
        missing_required.discard(
            "forward_voltage"
        )

    # Resistor resistance is handled by RES_002.
    missing_required.discard(
        "resistance"
    )

    if missing_required:
        missing_descriptions = []

        for specification in missing_required:

            if specification == "supply_voltage":
                missing_descriptions.append(
                    "supply voltage"
                )

            elif specification == "forward_voltage":
                missing_descriptions.append(
                    "LED forward voltage"
                )

            else:
                missing_descriptions.append(
                    specification
                )

        results.append(
            AnalysisResult(
                "LED_001",
                "warning",
                led_ref,
                (
                    "LED current cannot be verified. "
                    "Missing: "
                    + " and ".join(
                        missing_descriptions
                    )
                    + "."
                ),
                (
                    "Provide the actual required "
                    "circuit specifications."
                ),
            )
        )

        return results

    # --------------------------------------------------
    # Calculate LED current
    # --------------------------------------------------

    try:
        supply_voltage = float(
            supply_voltage
        )

        forward_voltage = float(
            forward_voltage
        )

        current = calculate_led_current(
            supply_voltage,
            forward_voltage,
            resistance,
        )

    except (
        TypeError,
        ValueError,
    ) as error:

        results.append(
            AnalysisResult(
                "CALC_001",
                "warning",
                led_ref,
                str(error),
                (
                    "Review the supplied voltage "
                    "and resistance values."
                ),
            )
        )

        return results

    current_ma = current * 1000

    # --------------------------------------------------
    # LED forward-current rating
    # --------------------------------------------------

    rated_current = (
        available
        .get("forward_current", {})
        .get("value")
    )

    if rated_current is None:
        results.append(
            AnalysisResult(
                "LED_001",
                "info",
                led_ref,
                (
                    f"Calculated LED current is "
                    f"{current_ma:.3f} mA, but the LED "
                    "forward-current rating is not "
                    "available."
                ),
                (
                    "Provide the LED's actual "
                    "forward-current rating to verify "
                    "the calculated current."
                ),
                measured=current_ma,
            )
        )

    else:
        try:
            rated_current = float(
                rated_current
            )

        except (TypeError, ValueError):
            rated_current = None

        if rated_current is None:
            results.append(
                AnalysisResult(
                    "LED_001",
                    "warning",
                    led_ref,
                    (
                        "The LED forward-current "
                        "specification is invalid."
                    ),
                    (
                        "Provide a valid LED "
                        "forward-current rating."
                    ),
                    measured=current_ma,
                )
            )

        else:
            rated_current_ma = (
                rated_current * 1000
            )

            if current > rated_current:
                results.append(
                    AnalysisResult(
                        "LED_001",
                        "warning",
                        led_ref,
                        (
                            f"Calculated LED current is "
                            f"{current_ma:.3f} mA, above the "
                            f"rated forward current of "
                            f"{rated_current_ma:.3f} mA."
                        ),
                        (
                            "Increase the series resistance "
                            "or verify the LED's actual "
                            "operating requirements."
                        ),
                        measured=current_ma,
                        limit=rated_current_ma,
                    )
                )

            else:
                results.append(
                    AnalysisResult(
                        "LED_001",
                        "info",
                        led_ref,
                        (
                            f"Calculated LED current is "
                            f"{current_ma:.3f} mA, within the "
                            f"rated forward current of "
                            f"{rated_current_ma:.3f} mA."
                        ),
                        (
                            "No LED forward-current overload "
                            "detected from the available "
                            "specification."
                        ),
                        measured=current_ma,
                        limit=rated_current_ma,
                    )
                )

    # --------------------------------------------------
    # Resistor power
    # --------------------------------------------------

    resistor_power = calculate_resistor_power(
        current,
        resistance,
    )

    resistor_rating = inputs.get(
        "power_rating"
    )

    if resistor_rating is None:
        resistor_rating = get_model_specification(
            model,
            resistor_ref,
            "power_rating",
        )

    if resistor_rating is None:
        results.append(
            AnalysisResult(
                "RES_001",
                "info",
                resistor_ref,
                (
                    f"Calculated resistor power is "
                    f"{resistor_power:.5f} W, but the "
                    "resistor power rating is not available."
                ),
                (
                    "Provide the resistor's actual "
                    "power rating to verify thermal safety."
                ),
                measured=resistor_power,
            )
        )

    elif resistor_power > resistor_rating:
        results.append(
            AnalysisResult(
                "RES_001",
                "warning",
                resistor_ref,
                (
                    f"Calculated resistor power is "
                    f"{resistor_power:.5f} W, above the "
                    f"rated power of "
                    f"{resistor_rating:.5f} W."
                ),
                (
                    "Use a resistor with a higher "
                    "power rating."
                ),
                measured=resistor_power,
                limit=resistor_rating,
            )
        )

    else:
        results.append(
            AnalysisResult(
                "RES_001",
                "info",
                resistor_ref,
                (
                    f"Calculated resistor power is "
                    f"{resistor_power:.5f} W, within the "
                    f"rated power of "
                    f"{resistor_rating:.5f} W."
                ),
                "No resistor power overload detected.",
                measured=resistor_power,
                limit=resistor_rating,
            )
        )

    return results


def led_resistor_electrical_rule(
    model,
    inputs,
):
    """Run LED-resistor electrical analysis."""

    pairs = find_led_resistor_pairs(
        model
    )

    results = []

    for led, resistor in pairs:
        results.extend(
            analyze_led_resistor_pair(
                led,
                resistor,
                inputs,
                model,
            )
        )

    return results


def analyze_circuit(circuit):
    """Analyze a circuit using CircuitModel and RuleEngine."""

    model = CircuitModel(circuit)

    circuit["model"] = model

    inputs = circuit.get(
        "analysis_inputs",
        {},
    )

    engine = RuleEngine()

    engine.register_rule(
        check_net_connectivity,
        "NET_001",
        "Net Connectivity Check",
    )

    engine.register_rule(
        check_resistor_values,
        "RES_002",
        "Resistor Value Check",
        applies_to="resistor",
    )

    engine.register_rule(
        lambda current_model:
            led_resistor_electrical_rule(
                current_model,
                inputs,
            ),
        "LED_RESISTOR_ANALYSIS",
        "LED and Resistor Electrical Analysis",
        applies_to="led",
    )

    return engine.run(model)


if __name__ == "__main__":
    from pathlib import Path
    from netlist_reader import load_circuit

    project_root = Path(__file__).resolve().parent.parent

    xml_file = (
        project_root
        / "data"
        / "schematics"
        / "CircuitSense_Test.xml"
    )

    circuit = load_circuit(
        str(xml_file)
    )

    print("\n--- Circuit Analysis ---")

    results = analyze_circuit(
        circuit
    )

    print("\n--- Analysis Results ---")

    if results:
        for result in results:
            print(
                f"Rule: {result.rule_id}"
            )
            print(
                f"Severity: {result.severity}"
            )
            print(
                f"Component: {result.component}"
            )
            print(
                f"Finding: {result.message}"
            )
            print(
                f"Suggestion: {result.suggestion}"
            )
            print()

    else:
        print("No analysis results.")