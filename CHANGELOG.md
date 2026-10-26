# Changelog

## [1.0.0] - Initial public release

### Features
- Parse KiCad XML netlists.
- Build a structured representation of circuit components and connectivity.
- Classify components and extract engineering specifications.
- Perform rule-based circuit and connectivity analysis.
- Integrate KiCad schematic Electrical Rules Checker (ERC).
- Export schematic netlists using the KiCad command-line interface.
- Display circuit information and analysis findings in a PySide6 GUI.

### Notes
- KiCad CLI is required for automatic schematic netlist export and ERC.
- Analysis coverage depends on implemented rules and available circuit information.
- Multi-platform EDA support, AI-assisted recommendations, and advanced PCB analysis
  are planned future enhancements, not completed features in this release.
