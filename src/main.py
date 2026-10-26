
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox
from gui import CircuitSenseWindow
from kicad_exporter import export_schematic_netlist


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_NETLIST = (
    PROJECT_ROOT / "data" / "schematics" / "CircuitSense_Test.xml"
)


def main():
    app = QApplication([sys.argv[0]])

    if len(sys.argv) > 2:
        QMessageBox.warning(
            None,
            "Invalid arguments",
            "Usage: python src/main.py [schematic.kicad_sch]"
        )
        return 2

    source_path = (
        Path(sys.argv[1]).expanduser().resolve()
        if len(sys.argv) == 2
        else None
    )

    temp_dir = None
    schematic_path = None

    if source_path is None:
        netlist_path = DEFAULT_NETLIST

    elif source_path.suffix == ".xml":
        netlist_path = source_path
        matching_schematic = source_path.with_suffix(
            ".kicad_sch"
        )
        if matching_schematic.is_file():
            schematic_path = matching_schematic

    elif source_path.suffix == ".kicad_sch":
        if not source_path.is_file():
            QMessageBox.critical(
                None, "File not found",
                f"Schematic not found:\n{source_path}"
            )
            return 1

        try:
            temp_dir, netlist_path = export_schematic_netlist(
                source_path
            )
            schematic_path = source_path
        except FileNotFoundError:
            QMessageBox.critical(
                None, "KiCad CLI not found",
                "Could not find kicad-cli. "
                "Check your KiCad installation and PATH."
            )
            return 1
        except RuntimeError as error:
            QMessageBox.critical(
                None, "Netlist export failed",
                str(error)
            )
            return 1

    else:
        QMessageBox.warning(
            None,
            "Unsupported file",
            "Please provide a .kicad_sch or .xml file."
        )
        return 1

    if not netlist_path.is_file():
        if temp_dir is not None:
            temp_dir.cleanup()
        QMessageBox.critical(
            None, "Netlist not found",
            "The netlist file could not be created or found."
        )
        return 1

    window = CircuitSenseWindow(
        netlist_path,
        schematic_path=schematic_path,
    )
    window.show()

    try:
        return app.exec()
    finally:
        if temp_dir is not None:
            temp_dir.cleanup()


if __name__ == "__main__":
    sys.exit(main())