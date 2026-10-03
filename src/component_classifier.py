
def classify_component(component):
    """Identify a component using its reference and library ID."""

    reference = str(component.get("reference", "")).upper()
    library_id = str(component.get("lib_id", "")).lower()

    # Check specific library IDs before general ones.
    library_rules = [
        ("resistor", ("device:r_us", "device:r", "resistor")),
        ("capacitor", (
            "device:c_polarized",
            "device:c_small",
            "device:c",
        )),
        ("led", ("device:led", "led:")),
        ("diode", (
            "device:d_zener",
            "device:d_schottky",
            "device:d_tv",
            "device:d",
            "diode:",
        )),
        ("inductor", ("device:l", "inductor:")),
        ("transistor", (
            "transistor:",
            "device:q_",
            "device:q",
        )),
        ("integrated_circuit", (
            "regulator:",
            "timer:",
            "amplifier_",
            "interface:",
            "logic_",
            "memory:",
        )),
        ("connector", ("connector:",)),
        ("fuse", ("device:f", "device:polyfuse")),
        ("switch", ("switch:",)),
        ("relay", ("relay:",)),
        ("transformer", ("transformer:",)),
        ("crystal", ("device:crystal", "device:resonator")),
        ("motor", ("motor:",)),
    ]

    for category, prefixes in library_rules:
        if any(library_id.startswith(p) for p in prefixes):
            return category

    # Fallback to the reference designator.
    reference_rules = [
        ("led", ("LED",)),
        ("resistor", ("R",)),
        ("capacitor", ("C",)),
        ("inductor", ("L",)),
        ("diode", ("D",)),
        ("transistor", ("Q",)),
        ("integrated_circuit", ("U",)),
        ("connector", ("J", "P")),
        ("fuse", ("F",)),
        ("switch", ("SW",)),
        ("relay", ("K",)),
        ("transformer", ("T",)),
        ("crystal", ("Y", "X")),
        ("motor", ("M",)),
    ]

    for category, prefixes in reference_rules:
        if any(reference.startswith(p) for p in prefixes):
            return category

    return "unknown"


def classify_components(components):
    """Classify all components in a circuit."""

    classified = []

    for component in components:
        result = component.copy()
        result["type"] = classify_component(component)
        classified.append(result)

    return classified


def classify_component_with_support(component):
    """Classify a component and retrieve registry information."""

    from component_registry import get_component_info

    component_type = classify_component(component)
    support_info = get_component_info(component_type)

    result = component.copy()
    result["type"] = component_type
    result["supported"] = support_info is not None
    result["support_info"] = support_info

    return result


if __name__ == "__main__":
    test_components = [
        {"reference": "R1", "value": "220",
         "lib_id": "Device:R"},
        {"reference": "C1", "value": "100uF",
         "lib_id": "Device:C"},
        {"reference": "L1", "value": "10mH",
         "lib_id": "Device:L"},
        {"reference": "D1", "value": "LED",
         "lib_id": "Device:LED"},
        {"reference": "D2", "value": "1N4148",
         "lib_id": "Device:D"},
        {"reference": "Q1", "value": "2N2222",
         "lib_id": "Transistor_BJT:Q_NPN"},
        {"reference": "U1", "value": "LM358",
         "lib_id": "Amplifier_Operational:LM358"},
        {"reference": "J1", "value": "Conn_01x02",
         "lib_id": "Connector_Generic:Conn_01x02"},
        {"reference": "ABC1", "value": "Unknown",
         "lib_id": ""},
    ]

    for component in classify_components(test_components):
        print(
            f"{component['reference']}: "
            f"{component['type']}"
        )
