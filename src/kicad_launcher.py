import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from gui import CircuitSenseWindow


def main():
    if len(sys.argv) < 2:
        print("Error: No netlist file was provided.")
        return 1

    netlist_path = Path(sys.argv[1]).resolve()

    if not netlist_path.is_file():
        print(f"Error: Netlist not found: {netlist_path}")
        return 1

    app = QApplication(sys.argv[:1])

    window = CircuitSenseWindow()
    window.netlist_path = netlist_path
    window.file_label.setText(str(netlist_path))
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
