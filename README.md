# CircuitSense

**A Python-based circuit analysis tool with KiCad integration.**

CircuitSense reads KiCad XML netlists, builds a structured representation of a circuit, and presents component information and analysis findings through a desktop GUI built with PySide6.

It integrates with KiCad's command-line interface for schematic netlist export and Electrical Rules Checker (ERC) reports.

## Features

- **Netlist parsing:** Read and process KiCad XML netlists.
- **Component classification:** Classify recognized electronic components.
- **Specification extraction:** Extract component values and specifications.
- **Connectivity analysis:** Perform rule-based checks on circuit connectivity.
- **KiCad ERC integration:** Process Electrical Rules Checker results.
- **Schematic export:** Export netlists from KiCad schematics using KiCad CLI.
- **Desktop GUI:** Explore components, view schematics, and review analysis findings.

## Requirements

- Python 3.10 or newer
- PySide6 6.11.2
- KiCad with `kicad-cli` available in your system's PATH for automatic schematic export and ERC integration

KiCad CLI is not required to open an existing XML netlist, provided a suitable netlist file is available.

## Installation

### 1. Clone the repository

Replace the placeholder URL with the actual GitHub repository URL.

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd CircuitSense
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Usage

### Launch with the bundled example

```bash
python src/main.py
```

### Open an existing KiCad XML netlist

```bash
python src/main.py /path/to/design.xml
```

### Open a KiCad schematic directly

```bash
python src/main.py /path/to/design.kicad_sch
```

Opening a schematic directly requires KiCad CLI to be installed and available in PATH.

## KiCad Integration

CircuitSense includes a launcher intended for use with a KiCad custom netlist exporter.

Example command template:

```text
/path/to/CircuitSense/.venv/bin/python /path/to/CircuitSense/src/kicad_launcher.py "%I" "%P"
```

Replace `/path/to/CircuitSense` with the actual project directory. Confirm the exporter substitutions supported by your KiCad configuration before using this command.

## Running Tests

Install pytest if it is not already installed:

```bash
python -m pip install pytest
```

Run the test suite from the project root:

```bash
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
```

## Project Structure

```text
CircuitSense/
├── data/
│   ├── rules/
│   └── schematics/
├── src/
│   ├── main.py
│   ├── gui.py
│   ├── netlist_reader.py
│   ├── circuit_model.py
│   ├── circuit_analyzer.py
│   ├── connectivity_analyzer.py
│   ├── electrical_rules.py
│   ├── kicad_exporter.py
│   ├── kicad_erc.py
│   └── kicad_launcher.py
├── tests/
├── requirements.txt
├── CHANGELOG.md
├── README.md
└── LICENSE
```

## Current Scope and Limitations

CircuitSense currently focuses on KiCad XML netlists, component information, rule-based circuit analysis, and KiCad CLI integration.

Analysis results depend on the implemented rules and available design data. Review reported findings against the original schematic and relevant electrical requirements.

Broader EDA platform support, advanced PCB analysis, and AI-assisted recommendations are potential future enhancements and are not claimed as completed features in this release.

## License

CircuitSense is released under the MIT License. See [LICENSE](LICENSE) for details.
