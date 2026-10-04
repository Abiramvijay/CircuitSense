import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from gui import CircuitSenseWindow


def find_schematic(xml_path, project_path=None):
    """Find the schematic corresponding to the XML netlist."""

    xml_path = Path(xml_path).resolve()

    # First try the same directory as the XML file.
    same_directory = xml_path.parent / f"{xml_path.stem}.kicad_sch"

    if same_directory.is_file():
        return same_directory

    # Then search the KiCad project directory.
    if project_path:
        project_path = Path(project_path).resolve()

        direct_match = project_path / f"{xml_path.stem}.kicad_sch"

        if direct_match.is_file():
            return direct_match

        matches = list(project_path.rglob(f"{xml_path.stem}.kicad_sch"))

        if matches:
            return matches[0]

    return None


def main():
    if len(sys.argv) < 2:
        print("Error: No KiCad netlist was provided.")
        return 1

    input_path = Path(sys.argv[1]).resolve()

    if not input_path.is_file():
        print(f"Error: Input file not found: {input_path}")
        return 1

    # ---------------------------------------------------------
    # KiCad custom exporter workflow
    # ---------------------------------------------------------
    # KiCad passes:
    #
    #   argument 1 = intermediate XML netlist (%I)
    #   argument 2 = project directory (%P)
    #
    # ---------------------------------------------------------

    if input_path.suffix.lower() == ".xml":

        project_path = None

        if len(sys.argv) >= 3:
            project_path = Path(sys.argv[2]).resolve()

        schematic_path = find_schematic(
            input_path,
            project_path,
        )

        if schematic_path is None:
            print(
                "Error: Could not find the corresponding "
                ".kicad_sch file for the XML netlist."
            )
            print(f"XML file: {input_path}")

            if project_path:
                print(f"Project directory: {project_path}")

            return 1

        netlist_path = input_path

    # ---------------------------------------------------------
    # Direct launcher workflow
    # ---------------------------------------------------------
    # Allows:
    #
    #   python src/kicad_launcher.py file.kicad_sch
    #
    # for testing outside KiCad.
    #
    # ---------------------------------------------------------

    elif input_path.suffix.lower() == ".kicad_sch":

        print(
            "Direct .kicad_sch launching is no longer handled "
            "by this integration launcher."
        )
        print(
            "Use the KiCad CircuitSense exporter or provide "
            "an XML netlist."
        )
        return 1

    else:
        print(
            "Error: CircuitSense launcher expects either "
            "a .xml netlist or a .kicad_sch file."
        )
        return 1

    try:
        app = QApplication(sys.argv[:1])

        window = CircuitSenseWindow(
            netlist_path=netlist_path,
            schematic_path=schematic_path,
        )

        window.show()

        return app.exec()

    except Exception as error:
        print(f"Error launching CircuitSense: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
