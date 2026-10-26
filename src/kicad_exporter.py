import subprocess
import tempfile
from pathlib import Path


def export_schematic_netlist(schematic_path):
    """Export a KiCad schematic to a temporary XML netlist."""
    schematic_path = Path(schematic_path).resolve()
    temp_dir = tempfile.TemporaryDirectory(
        prefix="circuitsense_"
    )
    netlist_path = Path(temp_dir.name) / "circuit.xml"

    try:
        completed = subprocess.run(
            [
                "kicad-cli",
                "sch", "export", "netlist",
                "--format", "kicadxml",
                "--output", str(netlist_path),
                str(schematic_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        temp_dir.cleanup()
        raise

    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        temp_dir.cleanup()
        message = "Could not export the schematic."
        if detail:
            message = f"{message}\n\n{detail}"
        raise RuntimeError(message)

    if not netlist_path.is_file():
        temp_dir.cleanup()
        raise RuntimeError(
            "KiCad did not create the expected XML netlist."
        )

    return temp_dir, netlist_path
