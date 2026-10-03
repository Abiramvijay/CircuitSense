import re


def recognize_component(component):
    """Recognize a component using its KiCad library ID."""

    lib_id = component.get("lib_id", "")
    value = str(component.get("value", ""))
    reference = str(component.get("reference", ""))

    library, _, symbol = lib_id.partition(":")
    text = f"{library} {symbol} {value}".lower()
    symbol_lower = symbol.lower()

    result = {
        "reference": reference,
        "value": value,
        "lib_id": lib_id,
        "category": "unknown",
        "subtype": "unknown",
        "confidence": "low"
    }

    def identified(category, subtype, confidence="high"):
        result["category"] = category
        result["subtype"] = subtype
        result["confidence"] = confidence
        return result

    # Diodes
    if "led" in text:
        return identified("diode", "led")

    if "zener" in text:
        return identified("diode", "zener")

    if "schottky" in text:
        return identified("diode", "schottky")

    if "tvs" in text or "transil" in text:
        return identified("diode", "tvs")

    if "photodiode" in text:
        return identified("diode", "photodiode")

    if "bridge" in text and "diode" in text:
        return identified("diode", "rectifier_bridge")

    if library.lower().startswith("device") and symbol_lower == "d":
        return identified("diode", "generic", "medium")

    # Resistors
    if "r_variable" in symbol_lower or "potentiometer" in text:
        return identified("resistor", "variable")

    if library.lower() == "device" and symbol_lower in {"r", "r_us"}:
        return identified("resistor", "fixed")

    # Capacitors
    if "c_polarized" in symbol_lower or "cp1" in symbol_lower:
        return identified("capacitor", "polarized")

    if library.lower() == "device" and symbol_lower in {"c", "c_small"}:
        return identified("capacitor", "generic")

    # Inductors and transformers
    if "inductor" in text or symbol_lower.startswith("l_"):
        return identified("inductor", "generic")

    if "transformer" in text or symbol_lower.startswith("transformer"):
        return identified("transformer", "transformer")

    # Transistors
    if "phototransistor" in text:
        return identified("transistor", "phototransistor")

    if "mosfet" in text:
        return identified("transistor", "mosfet")

    if "igbt" in text:
        return identified("transistor", "igbt")

    if "jfet" in text:
        return identified("transistor", "jfet")

    if "bjt" in text or "transistor" in text:
        return identified("transistor", "bjt", "medium")

    # Power conversion and management
    if "regulator_linear" in library.lower():
        return identified("integrated_circuit", "linear_regulator")

    if "regulator_switching" in library.lower():
        return identified("integrated_circuit", "switching_regulator")

    if "converter_dcdc" in library.lower():
        return identified("integrated_circuit", "dc_dc_converter")

    if "converter_acdc" in library.lower():
        return identified("integrated_circuit", "ac_dc_converter")

    if "power_management" in library.lower():
        return identified("integrated_circuit", "power_management")

    if "reference_voltage" in library.lower():
        return identified("integrated_circuit", "voltage_reference")

    if "power_protection" in library.lower():
        return identified("integrated_circuit", "power_protection")

    # Analog ICs
    if "comparator" in library.lower() or "comparator" in text:
        return identified("integrated_circuit", "comparator")

    if "amplifier" in library.lower() or "opamp" in text:
        return identified("integrated_circuit", "amplifier")

    if "analog_adc" in library.lower():
        return identified("integrated_circuit", "adc")

    if "analog_dac" in library.lower():
        return identified("integrated_circuit", "dac")

    if "analog_switch" in library.lower():
        return identified("integrated_circuit", "analog_switch")

    # Digital and embedded ICs
    if "interface_uart" in library.lower():
        return identified("integrated_circuit", "uart")

    if "interface_usb" in library.lower():
        return identified("integrated_circuit", "usb_interface")

    if "interface_can_lin" in library.lower():
        return identified("integrated_circuit", "can_lin_interface")

    if "memory" in library.lower():
        return identified("integrated_circuit", "memory")

    if "microcontroller" in library.lower():
        return identified("integrated_circuit", "microcontroller")

    if "dsp" in library.lower():
        return identified("integrated_circuit", "dsp")

    if "logic" in library.lower() or re.match(r"4\d{3}", symbol):
        return identified("integrated_circuit", "logic")

    if "isolator" in library.lower():
        return identified("integrated_circuit", "isolator")

    if "driver_motor" in library.lower():
        return identified("integrated_circuit", "motor_driver")

    if "driver_led" in library.lower():
        return identified("integrated_circuit", "led_driver")

    # Electromechanical components
    if "relay" in text:
        return identified("relay", "relay")

    if "switch" in text:
        return identified("switch", "switch", "medium")

    if "connector" in library.lower():
        return identified("connector", "connector")

    if "sensor" in library.lower():
        return identified("sensor", "sensor", "medium")

    if "motor" in text:
        return identified("motor", "motor", "medium")

    if "battery" in text:
        return identified("power_source", "battery", "medium")

    if "power" in library.lower() and symbol.startswith("PWR"):
        return identified("power_symbol", "power_symbol")

    return result