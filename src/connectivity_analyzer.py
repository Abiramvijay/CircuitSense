from component_recognition import recognize_component


def find_net_for_pin(circuit, reference, pin):
    """Find the net connected to a particular component pin."""
    for net in circuit["nets"]:
        for node in net["nodes"]:
            if (
                node["reference"] == reference
                and str(node["pin"]) == str(pin)
            ):
                return net["name"]

    return None


def get_component_pin_nets(circuit, reference):
    """Return a mapping of connected pin numbers to net names."""
    pin_nets = {}

    for net in circuit["nets"]:
        for node in net["nodes"]:
            if node["reference"] == reference:
                pin_nets[str(node["pin"])] = net["name"]

    return pin_nets


def get_component_nets(circuit, reference):
    """Return all nets connected to a component."""
    return set(
        get_component_pin_nets(circuit, reference).values()
    )


def get_recognized_components(circuit):
    """Recognize all components in the circuit."""
    recognized = []

    for component in circuit["components"]:
        info = recognize_component(component)

        recognized.append({
            **component,
            "recognition": info
        })

    return recognized


def check_simple_series_pair(circuit, led, resistor):
    """
    Check whether an LED and resistor form a simple
    two-terminal series connection.

    This checks net topology, not electrical polarity
    or the suitability of component values.
    """
    led_ref = led["reference"]
    resistor_ref = resistor["reference"]

    led_pins = get_component_pin_nets(
        circuit,
        led_ref,
    )

    resistor_pins = get_component_pin_nets(
        circuit,
        resistor_ref,
    )

    if len(led_pins) != 2:
        return False, (
            f"{led_ref}: expected two connected LED pins, "
            f"but found {len(led_pins)}."
        )

    if len(resistor_pins) != 2:
        return False, (
            f"{resistor_ref}: expected two connected resistor "
            f"pins, but found {len(resistor_pins)}."
        )

    led_nets = set(led_pins.values())
    resistor_nets = set(resistor_pins.values())

    if len(led_nets) != 2 or len(resistor_nets) != 2:
        return False, (
            f"{led_ref} and {resistor_ref} do not each have "
            "two distinct connected nets."
        )

    shared_nets = led_nets & resistor_nets

    if len(shared_nets) != 1:
        return False, (
            f"{led_ref} and {resistor_ref} must share exactly "
            "one net for this simple series check."
        )

    shared_net = next(iter(shared_nets))

    nodes_on_shared_net = []

    for net in circuit["nets"]:
        if net["name"] == shared_net:
            nodes_on_shared_net = net["nodes"]
            break

    if len(nodes_on_shared_net) != 2:
        return False, (
            f"The shared net {shared_net} has "
            f"{len(nodes_on_shared_net)} connected pins. "
            "A simple series connection requires exactly two."
        )

    references = [
        node["reference"]
        for node in nodes_on_shared_net
    ]

    if (
        references.count(led_ref) != 1
        or references.count(resistor_ref) != 1
    ):
        return False, (
            f"The shared net {shared_net} does not connect "
            "exactly one LED pin and one resistor pin."
        )

    return True, "Simple series topology detected."


def find_led_resistor_pairs(circuit, recognized=None):
    """Return only LED-resistor pairs passing the topology check."""

    if recognized is None:
        recognized = get_recognized_components(circuit)

    leds = [
        component
        for component in recognized
        if component["recognition"].get("type") == "led"
    ]

    resistors = [
        component
        for component in recognized
        if component["recognition"].get("type") == "resistor"
    ]

    valid_pairs = []

    for led in leds:
        for resistor in resistors:
            shared = (
                get_component_nets(circuit, led["reference"])
                & get_component_nets(
                    circuit,
                    resistor["reference"],
                )
            )

            if not shared:
                continue

            valid, _ = check_simple_series_pair(
                circuit,
                led,
                resistor,
            )

            if valid:
                valid_pairs.append(
                    (led, resistor)
                )

    return valid_pairs


def find_led_resistor_pairs_from_model(model):
    """
    Find LED-resistor pairs using the general CircuitModel
    topology representation.

    The pair is accepted only when:
    - the LED has exactly two connected pins,
    - the resistor has exactly two connected pins,
    - both components have two distinct nets,
    - they share exactly one net,
    - the shared net contains exactly the LED and resistor pins.

    Returns:
        List of (LED component, resistor component) tuples.
    """

    from component_classifier import (
        classify_component_with_support
    )

    leds = []
    resistors = []

    for component in model.components:
        recognition = classify_component_with_support(
            component
        )

        component_type = recognition.get("type")

        if component_type == "led":
            leds.append(component)

        elif component_type == "resistor":
            resistors.append(component)

    valid_pairs = []

    for led in leds:
        led_ref = led.get("reference")

        led_pin_nets = model.get_component_pin_nets(
            led_ref
        )

        if len(led_pin_nets) != 2:
            continue

        led_nets = set(led_pin_nets.values())

        if len(led_nets) != 2:
            continue

        for resistor in resistors:
            resistor_ref = resistor.get("reference")

            resistor_pin_nets = (
                model.get_component_pin_nets(
                    resistor_ref
                )
            )

            if len(resistor_pin_nets) != 2:
                continue

            resistor_nets = set(
                resistor_pin_nets.values()
            )

            if len(resistor_nets) != 2:
                continue

            shared_nets = (
                led_nets & resistor_nets
            )

            if len(shared_nets) != 1:
                continue

            shared_net = next(
                iter(shared_nets)
            )

            shared_connections = (
                model.get_net_connections(
                    shared_net
                )
            )

            if len(shared_connections) != 2:
                continue

            references = [
                connection["reference"]
                for connection in shared_connections
            ]

            if (
                references.count(led_ref) == 1
                and references.count(resistor_ref) == 1
            ):
                valid_pairs.append(
                    (led, resistor)
                )

    return valid_pairs


def check_led_resistor_connection(circuit):
    """Report LED-resistor connection and topology issues."""
    issues = []
    recognized = get_recognized_components(circuit)

    leds = [
        component
        for component in recognized
        if component["recognition"].get("type") == "led"
    ]

    resistors = [
        component
        for component in recognized
        if component["recognition"].get("type") == "resistor"
    ]

    for led in leds:
        led_ref = led["reference"]

        led_nets = get_component_nets(
            circuit,
            led_ref,
        )

        if not led_nets:
            issues.append(
                f"{led_ref} (LED) has no connected pins."
            )
            continue

        if len(get_component_pin_nets(
            circuit,
            led_ref,
        )) != 2:
            issues.append(
                f"{led_ref} (LED) does not have exactly "
                "two connected pins in the netlist."
            )
            continue

        connected_resistors = [
            resistor
            for resistor in resistors
            if led_nets
            & get_component_nets(
                circuit,
                resistor["reference"],
            )
        ]

        if not connected_resistors:
            issues.append(
                f"No recognized resistor shares a net "
                f"with {led_ref} (LED)."
            )
            continue

        valid_pair_found = False

        for resistor in connected_resistors:
            valid, reason = check_simple_series_pair(
                circuit,
                led,
                resistor,
            )

            if valid:
                valid_pair_found = True
            else:
                issues.append(
                    f"{led_ref} and {resistor['reference']}: "
                    f"{reason}"
                )

        if (
            not valid_pair_found
            and not any(
                led_ref in issue
                for issue in issues
            )
        ):
            issues.append(
                f"No simple series connection was verified "
                f"for {led_ref} (LED)."
            )

    return issues


def analyze_connectivity(circuit):
    """Perform basic net connectivity checks."""
    issues = []

    for net in circuit["nets"]:
        nodes = net["nodes"]

        references = [
            node["reference"]
            for node in nodes
        ]

        print(
            f"Net: {net['name']}, "
            f"Components: {references}"
        )

        if len(nodes) < 2:
            issues.append(
                f"Possible connectivity issue: "
                f"{net['name']} has fewer than two "
                "connected pins."
            )

    return issues


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

    circuit = load_circuit(str(xml_file))

    print("\n--- Connectivity Analysis ---")

    issues = analyze_connectivity(circuit)

    issues.extend(
        check_led_resistor_connection(circuit)
    )

    print("\n--- Connectivity Results ---")

    if issues:
        for issue in issues:
            print("Warning:", issue)
    else:
        print("No basic connectivity issues detected.")