import xml.etree.ElementTree as ET


def load_circuit(xml_file):
    """Load components, pins, properties and nets from a KiCad XML netlist."""

    tree = ET.parse(xml_file)
    root = tree.getroot()

    if root.tag != "export":
        raise ValueError(
            "The selected XML file is not a KiCad netlist."
        )

    if (
        root.find("./components") is None
        or root.find("./nets") is None
    ):
        raise ValueError(
            "The KiCad netlist is missing its components or nets section."
        )

    circuit = {
        "components": [],
        "nets": [],
    }

    for component in root.findall("./components/comp"):
        libsource = component.find("libsource")

        lib_id = ""
        library_description = ""

        if libsource is not None:
            library = libsource.get("lib", "")
            symbol = libsource.get("part", "")

            lib_id = (
                f"{library}:{symbol}"
                if library
                else symbol
            )

            library_description = libsource.get(
                "description",
                ""
            )

        fields = {}

        fields_element = component.find("fields")

        if fields_element is not None:
            for field in fields_element.findall("field"):
                name = field.get("name", "")

                if name:
                    fields[name] = field.text or ""

        properties = {}

        for prop in component.findall("property"):
            name = prop.get("name", "")

            if name:
                properties[name] = prop.get(
                    "value",
                    ""
                )

        pins = []

        for pin in component.findall(
            "./units/unit/pins/pin"
        ):
            pin_number = pin.get("num")

            if pin_number is not None:
                pins.append(pin_number)

        circuit["components"].append(
            {
                "reference": component.get("ref"),
                "value": component.findtext(
                    "value",
                    default=""
                ),
                "lib_id": lib_id,
                "footprint": component.findtext(
                    "footprint",
                    default=""
                ),
                "description": component.findtext(
                    "description",
                    default=""
                ),
                "fields": fields,
                "properties": properties,
                "library_description": library_description,
                "pins": pins,
            }
        )

    for net in root.findall("./nets/net"):
        nodes = []

        for node in net.findall("node"):
            nodes.append(
                {
                    "reference": node.get("ref"),
                    "pin": node.get("pin"),
                }
            )

        circuit["nets"].append(
            {
                "name": net.get("name"),
                "nodes": nodes,
            }
        )

    return circuit
