"""
CircuitSense Component Support Registry

Defines supported component families and their
current analysis capabilities.
"""

COMPONENT_REGISTRY = {
    "resistor": {
        "name": "Resistor",
        "category": "passive",
        "recognition": True,
        "specifications": [
            "resistance",
            "power_rating",
            "tolerance",
        ],
        "checks": [
            "resistance_value",
            "power_dissipation",
        ],
        "analysis_level": "electrical",
    },

    "capacitor": {
        "name": "Capacitor",
        "category": "passive",
        "recognition": True,
        "specifications": [
            "capacitance",
            "voltage_rating",
            "tolerance",
        ],
        "checks": [
            "capacitance_value",
            "voltage_rating",
        ],
        "analysis_level": "recognition",
    },

    "inductor": {
        "name": "Inductor",
        "category": "passive",
        "recognition": True,
        "specifications": [
            "inductance",
            "current_rating",
            "resistance",
        ],
        "checks": [
            "inductance_value",
            "current_rating",
        ],
        "analysis_level": "recognition",
    },

    "led": {
        "name": "LED",
        "category": "diode",
        "recognition": True,
        "specifications": [
            "forward_voltage",
            "forward_current",
            "power_rating",
        ],
        "checks": [
            "led_current",
            "resistor_power",
        ],
        "analysis_level": "electrical",
    },

    "diode": {
        "name": "Diode",
        "category": "diode",
        "recognition": True,
        "specifications": [
            "forward_voltage",
            "forward_current",
            "reverse_voltage",
        ],
        "checks": [
            "polarity",
            "current_rating",
            "reverse_voltage",
        ],
        "analysis_level": "recognition",
    },

    "transistor": {
        "name": "Transistor",
        "category": "semiconductor",
        "recognition": True,
        "specifications": [
            "maximum_voltage",
            "maximum_current",
            "power_rating",
        ],
        "checks": [
            "voltage_rating",
            "current_rating",
            "power_dissipation",
        ],
        "analysis_level": "recognition",
    },

    "integrated_circuit": {
        "name": "Integrated Circuit",
        "category": "semiconductor",
        "recognition": True,
        "specifications": [
            "supply_voltage",
            "input_voltage",
            "output_current",
        ],
        "checks": [
            "supply_voltage",
            "pin_connectivity",
        ],
        "analysis_level": "recognition",
    },

    "connector": {
        "name": "Connector",
        "category": "electromechanical",
        "recognition": True,
        "specifications": [
            "pin_count",
            "current_rating",
            "voltage_rating",
        ],
        "checks": [
            "pin_connectivity",
        ],
        "analysis_level": "recognition",
    },

    "fuse": {
        "name": "Fuse",
        "category": "protection",
        "recognition": True,
        "specifications": [
            "current_rating",
            "voltage_rating",
        ],
        "checks": [
            "current_rating",
        ],
        "analysis_level": "recognition",
    },

    "switch": {
        "name": "Switch",
        "category": "electromechanical",
        "recognition": True,
        "specifications": [
            "current_rating",
            "voltage_rating",
        ],
        "checks": [
            "pin_connectivity",
        ],
        "analysis_level": "recognition",
    },

    "relay": {
        "name": "Relay",
        "category": "electromechanical",
        "recognition": True,
        "specifications": [
            "coil_voltage",
            "contact_current",
            "contact_voltage",
        ],
        "checks": [
            "coil_voltage",
            "contact_rating",
        ],
        "analysis_level": "recognition",
    },

    "transformer": {
        "name": "Transformer",
        "category": "power",
        "recognition": True,
        "specifications": [
            "primary_voltage",
            "secondary_voltage",
            "power_rating",
        ],
        "checks": [
            "voltage_ratio",
        ],
        "analysis_level": "recognition",
    },

    "crystal": {
        "name": "Crystal",
        "category": "timing",
        "recognition": True,
        "specifications": [
            "frequency",
            "load_capacitance",
        ],
        "checks": [
            "frequency_value",
        ],
        "analysis_level": "recognition",
    },

    "motor": {
        "name": "Motor",
        "category": "electromechanical",
        "recognition": True,
        "specifications": [
            "rated_voltage",
            "rated_current",
        ],
        "checks": [
            "voltage_rating",
            "current_rating",
        ],
        "analysis_level": "recognition",
    },
}


def get_component_info(component_type):
    """Return registry information for a component family."""
    return COMPONENT_REGISTRY.get(component_type)


def get_supported_components():
    """Return all registered component families."""
    return list(COMPONENT_REGISTRY.keys())


def get_components_by_category(category):
    """Return components belonging to a category."""
    return {
        name: info
        for name, info in COMPONENT_REGISTRY.items()
        if info["category"] == category
    }


if __name__ == "__main__":
    print("CircuitSense Component Registry")
    print("-" * 40)

    for component_type, info in COMPONENT_REGISTRY.items():
        print(
            f"{info['name']}: "
            f"{info['analysis_level']}"
        )

    print("-" * 40)
    print(f"Registered families: {len(COMPONENT_REGISTRY)}")
