
import csv
import json
from collections import Counter
from pathlib import Path

INPUT_FILE = Path("data/kicad_component_catalogue.json")
OUTPUT_DIR = Path("data")
JSON_FILE = OUTPUT_DIR / "classified_components.json"
CSV_FILE = OUTPUT_DIR / "classified_components.csv"


def classify_component(item):
    library = item.get("library", "").lower()
    symbol = item.get("symbol", "").lower()
    name = f"{library}:{symbol}"

    def result(category, subtype=None):
        return {
            "category": category,
            "subtype": subtype or category,
            "classification_method": "library_and_symbol"
        }

    # Diodes: check specialized types before generic diodes.
    if "led" in symbol or library.startswith("led"):
        return result("diode", "led")

    if any(x in name for x in ("zener", "dzener")):
        return result("diode", "zener")

    if "schottky" in name:
        return result("diode", "schottky")

    if any(x in name for x in ("tvs", "suppressor")):
        return result("diode", "tvs")

    if "bridge" in name and "diode" in name:
        return result("diode", "rectifier_bridge")

    if "diode" in library or symbol.startswith("d_") or symbol == "d":
        if "photo" in symbol:
            return result("diode", "photodiode")
        if "varactor" in symbol or "varicap" in symbol:
            return result("diode", "varactor")
        if "current-regulator" in symbol:
            return result("diode", "current_regulator")
        if "dual" in symbol:
            return result("diode", "dual_diode")
        return result("diode", "generic")

    # Transistors and related semiconductor devices.
    if "igbt" in symbol:
        return result("transistor", "igbt")

    if "jfet" in symbol or "jfet" in library:
        return result("transistor", "jfet")

    if "ujt" in symbol:
        return result("transistor", "ujt")

    if "mosfet" in symbol or symbol.startswith(("q_nmos", "q_pmos")):
        return result("transistor", "mosfet")

    if any(x in symbol for x in ("q_npn", "q_pnp")):
        return result("transistor", "bjt")

    if "photo" in symbol and "q_" in symbol:
        return result("transistor", "phototransistor")

    if symbol.startswith("q_") or library.startswith("transistor"):
        return result("transistor", "other")

    # Passive components.
    if library == "device":
        if symbol.startswith(("r_pot", "r_variable")):
            return result("resistor", "variable")
        if symbol.startswith("r"):
            return result("resistor", "fixed")

        if symbol.startswith("c"):
            if "polarized" in symbol or "electrolytic" in symbol:
                return result("capacitor", "polarized")
            return result("capacitor", "generic")

        if symbol.startswith("l"):
            return result("inductor", "generic")

    if "resistor" in library:
        if "pot" in symbol:
            return result("resistor", "variable")
        return result("resistor", "fixed")

    if "capacitor" in library:
        if "polarized" in symbol or "electrolytic" in symbol:
            return result("capacitor", "polarized")
        return result("capacitor", "generic")

    if "inductor" in library:
        return result("inductor", "generic")

    # Logic ICs.
    if (
        library.startswith(("4xxx", "74xx"))
        or library.startswith("74")
        or "logic" in library
    ):
        return result("integrated_circuit", "logic")

    # Microcontrollers and programmable devices.
    if library.startswith("mcu"):
        return result("integrated_circuit", "microcontroller")

    if library.startswith(("fpga", "cpld")):
        return result("integrated_circuit", "programmable_logic")

    if "memory" in library:
        return result("integrated_circuit", "memory")

    if "dsp" in library:
        return result("integrated_circuit", "dsp")

    # Amplifiers and power-management devices.
    if "amplifier" in library:
        if "operational" in symbol or "opamp" in symbol:
            return result("integrated_circuit", "operational_amplifier")
        return result("integrated_circuit", "amplifier")

    if library.startswith("regulator_linear"):
        return result("integrated_circuit", "linear_regulator")

    if library.startswith("regulator_switching"):
        return result("integrated_circuit", "switching_regulator")

    if library.startswith("regulator_controller"):
        return result("integrated_circuit", "power_controller")

    if library.startswith("regulator"):
        return result("integrated_circuit", "power_management")

    # Other common component families.
    if library.startswith("connector"):
        return result("connector")

    if library.startswith("switch"):
        return result("switch")

    if library.startswith("relay"):
        return result("relay")

    if library.startswith("transformer"):
        return result("transformer")

    if library.startswith(("sensor", "transducer")):
        return result("sensor")

    if library.startswith("motor"):
        return result("motor")

    if library.startswith("fuse") or symbol.startswith("f_"):
        return result("protection", "fuse")

    if library.startswith("battery") or "battery" in symbol:
        return result("power_source", "battery")

    if library == "power":
        return result("power_symbol")

    if library.startswith("crystal") or "resonator" in symbol:
        return result("timing", "crystal")

    return result("unknown", "unknown")


def main():
    if not INPUT_FILE.is_file():
        print(f"Catalogue not found: {INPUT_FILE}")
        return

    with INPUT_FILE.open(encoding="utf-8") as file:
        catalogue = json.load(file)

    classified = []
    counts = Counter()

    for item in catalogue:
        classification = classify_component(item)

        result = item.copy()
        result.update(classification)
        classified.append(result)
        counts[result["category"]] += 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with JSON_FILE.open("w", encoding="utf-8") as file:
        json.dump(classified, file, indent=2, ensure_ascii=False)

    fields = [
        "library",
        "symbol",
        "library_id",
        "category",
        "subtype",
        "classification_method",
    ]

    with CSV_FILE.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(classified)

    print("Refined classification completed.")
    print(f"Total symbols: {len(classified)}")
    print("\nCategory counts:")

    for category, count in sorted(counts.items()):
        print(f"{category}: {count}")

    print(f"\nJSON: {JSON_FILE}")
    print(f"CSV: {CSV_FILE}")


if __name__ == "__main__":
    main()