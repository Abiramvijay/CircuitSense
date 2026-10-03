
"""Extract electrical specifications from KiCad component data."""

import re

from component_classifier import classify_component


# Supported engineering suffixes, expressed in base SI units.
UNIT_MULTIPLIERS = {
    "": 1.0,
    "p": 1e-12,
    "n": 1e-9,
    "u": 1e-6,
    "µ": 1e-6,
    "m": 1e-3,
    "k": 1e3,
    "K": 1e3,
    "meg": 1e6,
    "M": 1e6,
    "g": 1e9,
    "G": 1e9,
}

VALUE_SPECS = {
    "resistor": ("resistance", "ohm"),
    "capacitor": ("capacitance", "F"),
    "inductor": ("inductance", "H"),
}

# Names commonly used for electrical properties.
PROPERTY_ALIASES = {
    "resistance": ("resistance", "resistance_ohms"),
    "capacitance": ("capacitance",),
    "inductance": ("inductance",),
    "voltage_rating": (
        "voltage_rating", "rated_voltage", "voltage",
    ),
    "power_rating": (
        "power_rating", "rated_power", "power",
    ),
    "current_rating": (
        "current_rating", "rated_current", "current",
    ),
    "forward_voltage": (
        "forward_voltage", "vf",
    ),
    "forward_current": (
        "forward_current", "if",
    ),
    "reverse_voltage": (
        "reverse_voltage", "vr",
    ),
    "supply_voltage": (
        "supply_voltage", "vcc",
    ),
    "coil_voltage": ("coil_voltage",),
    "contact_current": ("contact_current",),
    "contact_voltage": ("contact_voltage",),
    "frequency": ("frequency", "rated_frequency"),
    "load_capacitance": ("load_capacitance",),
    "maximum_voltage": ("maximum_voltage", "max_voltage"),
    "maximum_current": ("maximum_current", "max_current"),
    "output_current": ("output_current",),
    "input_voltage": ("input_voltage",),
    "primary_voltage": ("primary_voltage",),
    "secondary_voltage": ("secondary_voltage",),
    "rated_voltage": ("rated_voltage",),
    "rated_current": ("rated_current",),
}

SPEC_UNITS = {
    "resistance": "ohm",
    "capacitance": "F",
    "inductance": "H",
    "voltage_rating": "V",
    "power_rating": "W",
    "current_rating": "A",
    "forward_voltage": "V",
    "forward_current": "A",
    "reverse_voltage": "V",
    "supply_voltage": "V",
    "coil_voltage": "V",
    "contact_current": "A",
    "contact_voltage": "V",
    "frequency": "Hz",
    "load_capacitance": "F",
    "maximum_voltage": "V",
    "maximum_current": "A",
    "output_current": "A",
    "input_voltage": "V",
    "primary_voltage": "V",
    "secondary_voltage": "V",
    "rated_voltage": "V",
    "rated_current": "A",
}


def parse_engineering_value(value, expected_unit):
    """Convert values such as 4.7uF or 10k into SI units."""

    if value is None:
        return None

    text = str(value).strip().replace(",", "")
    text = re.sub(r"\s+", "", text)

    # Match a number, optional engineering suffix and optional unit.
    match = re.fullmatch(
        r"([+-]?(?:\d+(?:\.\d*)?|\.\d+))"
        r"(meg|[pnumµkKMgG]?)"
        r"(ohm|Ω|[FHVWA]|[fvhvwa])?",
        text,
    )

    if not match:
        return None

    number_text, suffix, unit = match.groups()

    if unit:
        normalized_unit = unit.lower()
        expected = expected_unit.lower()

        unit_aliases = {
            "ohm": {"ohm", "ω"},
            "f": {"f"},
            "h": {"h"},
            "v": {"v"},
            "w": {"w"},
            "a": {"a"},
            "hz": {"hz"},
        }

        allowed = unit_aliases.get(expected, {expected})
        if normalized_unit not in allowed:
            return None

    number = float(number_text)
    multiplier = UNIT_MULTIPLIERS.get(suffix)

    if multiplier is None:
        return None

    result = number * multiplier

    if result <= 0:
        return None

    return result


def _get_properties(component):
    """Combine KiCad fields and properties for lookup."""
    combined = {}

    for source in ("fields", "properties"):
        values = component.get(source, {})
        if isinstance(values, dict):
            for name, value in values.items():
                combined[name.strip().lower()] = value

    return combined


def extract_specifications(component):
    """Extract known specifications without inventing ratings."""

    component_type = classify_component(component)
    specifications = {}

    # Extract the component's nominal value where supported.
    if component_type in VALUE_SPECS:
        spec_name, unit = VALUE_SPECS[component_type]
        raw_value = component.get("value", "")
        parsed = parse_engineering_value(raw_value, unit)

        if parsed is not None:
            specifications[spec_name] = {
                "value": parsed,
                "unit": unit,
                "raw_value": raw_value,
                "source": "kicad_value",
                "status": "extracted",
            }

    # Extract explicit electrical properties, if available.
    properties = _get_properties(component)

    for spec_name, aliases in PROPERTY_ALIASES.items():
        if spec_name in specifications:
            continue

        for alias in aliases:
            raw_value = properties.get(alias.lower())

            if raw_value is None or not str(raw_value).strip():
                continue

            unit = SPEC_UNITS.get(spec_name)
            if unit is None:
                break

            parsed = parse_engineering_value(raw_value, unit)

            if parsed is not None:
                specifications[spec_name] = {
                    "value": parsed,
                    "unit": unit,
                    "raw_value": raw_value,
                    "source": "kicad_property",
                    "status": "extracted",
                }
                break

    return {
        "reference": component.get("reference", ""),
        "type": component_type,
        "specifications": specifications,
    }


if __name__ == "__main__":
    examples = [
        {"reference": "R1", "value": "220",
         "lib_id": "Device:R"},
        {"reference": "C1", "value": "4.7uF",
         "lib_id": "Device:C"},
        {"reference": "L1", "value": "10mH",
         "lib_id": "Device:L"},
        {"reference": "D1", "value": "LED",
         "lib_id": "Device:LED"},
    ]

    for component in examples:
        print(extract_specifications(component))
