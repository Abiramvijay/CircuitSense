
import sys
import tempfile
import subprocess
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox
from gui import CircuitSenseWindow


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

    if source_path is None:
        netlist_path = DEFAULT_NETLIST

    elif source_path.suffix == ".xml":
        netlist_path = source_path

    elif source_path.suffix == ".kicad_sch":
        if not source_path.is_file():
            QMessageBox.critical(
                None, "File not found",
                f"Schematic not found:\n{source_path}"
            )
            return 1

        temp_dir = tempfile.TemporaryDirectory(
            prefix="circuitsense_"
        )
        netlist_path = Path(temp_dir.name) / "circuit.xml"

        try:
            subprocess.run(
                [
                    "kicad-cli",
                    "sch", "export", "netlist",
                    "--format", "kicadxml",
                    "--output", str(netlist_path),
                    str(source_path)
                ],
                check=True,
                capture_output=True,
                text=True
            )
        except FileNotFoundError:
            temp_dir.cleanup()
            QMessageBox.critical(
                None, "KiCad CLI not found",
                "Could not find kicad-cli. "
                "Check your KiCad installation and PATH."
            )
            return 1
        except subprocess.CalledProcessError as error:
            temp_dir.cleanup()
            details = error.stderr or error.stdout or str(error)
            QMessageBox.critical(
                None, "Netlist export failed",
                f"Could not export the schematic:\n\n{details}"
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

    window = CircuitSenseWindow(netlist_path)
    window.show()

    try:
        return app.exec()
    finally:
        if temp_dir is not None:
            temp_dir.cleanup()


if __name__ == "__main__":
    sys.exit(main())