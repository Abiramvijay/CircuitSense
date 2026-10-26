
import sys
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QFileDialog, QFrame, QTableWidget,
    QTableWidgetItem, QMessageBox, QHeaderView,
    QStackedWidget, QScrollArea
)
from PySide6.QtSvgWidgets import QSvgWidget

from kicad_erc import run_schematic_erc
from kicad_exporter import export_schematic_netlist
from netlist_reader import load_circuit
from circuit_analyzer import analyze_circuit
from component_classifier import classify_component_with_support
from specification_extractor import extract_specifications


class CircuitSenseWindow(QMainWindow):
    def __init__(self, netlist_path=None, schematic_path=None):
        super().__init__()

        self.setWindowTitle("CircuitSense")

        icon_path = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "ckt.png"
        )
        self.setWindowIcon(QIcon(str(icon_path)))

        self.resize(1200, 850)
        self.setMinimumSize(950, 700)

        default_schematic = (
            Path(__file__).resolve().parent.parent
            / "data" / "schematics" / "CircuitSense_Test.kicad_sch"
        )

        if schematic_path is None:
            if netlist_path is None:
                self.schematic_path = default_schematic
            else:
                matching_schematic = Path(
                    netlist_path
                ).resolve().with_suffix(".kicad_sch")
                self.schematic_path = (
                    matching_schematic
                    if matching_schematic.is_file()
                    else None
                )
        else:
            self.schematic_path = Path(schematic_path).resolve()

        self._svg_tempdir = None
        self._analysis_tempdir = None

        # Accept a netlist supplied by the launcher or main.py.
        # Otherwise, load the default test netlist.
        if netlist_path is None:
            self.netlist_path = (
                Path(__file__).resolve().parent.parent
                / "data" / "schematics"
                / "CircuitSense_Test.xml"
            )
        else:
            self.netlist_path = Path(netlist_path).resolve()

        self.setStyleSheet("""
            QMainWindow {
                background: #e6f0fa;
            }
            QWidget {
                font-family: "Inter", "Segoe UI", sans-serif;
                color: #22232b;
                font-size: 13px;
            }
            QFrame#shell {
                background: #24252c;
                border-radius: 24px;
            }
            QFrame#sidebar {
                background: #24252c;
                border: none;
            }
            QFrame#content {
                background: #ffffff;
                border-radius: 19px;
            }
            QLabel#app_title {
                color: #ffffff;
                font-size: 23px;
                font-weight: 700;
            }
            QLabel#app_subtitle {
                color: #a7a8b5;
                font-size: 11px;
            }
            QLabel#section_title {
                color: #24252c;
                font-size: 21px;
                font-weight: 700;
            }
            QLabel#section_subtitle {
                color: #7b7d8c;
                font-size: 12px;
            }
            QLabel#metric_title {
                color: #777988;
                font-size: 11px;
                font-weight: 600;
            }
            QLabel#metric_value {
                font-size: 26px;
                font-weight: 700;
            }
            QLabel#status {
                color: #398a65;
                font-weight: 700;
                padding: 6px 10px;
                background: #e6f5ec;
                border-radius: 8px;
            }
            QLabel#field_label {
                color: #555765;
                font-weight: 600;
            }
            QLabel#file_label {
                color: #525564;
                background: #f4f5f8;
                border: 1px solid #e4e6ed;
                border-radius: 8px;
                padding: 9px;
            }
            QPushButton {
                background: #7057d9;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 9px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #5d45c6;
            }
            QPushButton:pressed {
                background: #4d36b5;
            }
            QPushButton#secondary {
                background: #eeeafb;
                color: #634acb;
                border: 1px solid #ded7fa;
            }
            QPushButton#secondary:hover {
                background: #e2dcfa;
            }
            QTableWidget {
                background: #ffffff;
                alternate-background-color: #f8f9fc;
                border: 1px solid #e7e8ee;
                border-radius: 9px;
                gridline-color: #ececf1;
                selection-background-color: #eeeafb;
                selection-color: #22232b;
            }
            QHeaderView::section {
                background: #f3f4f8;
                color: #555765;
                border: none;
                border-bottom: 1px solid #e1e3ea;
                padding: 10px;
                font-weight: 700;
            }
            QScrollBar:vertical {
                background: #f2f3f7;
                width: 9px;
                margin: 2px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #c4c6d0;
                min-height: 25px;
                border-radius: 4px;
            }
            QMessageBox {
                background: #24252c;
            }
            QMessageBox QLabel {
                color: #ffffff;
                min-width: 300px;
            }
            QMessageBox QPushButton {
                min-width: 85px;
            }
        """)

        self.build_ui()
        self.refresh_overview()

    def card(self, object_name="card"):
        frame = QFrame()
        frame.setObjectName(object_name)
        frame.setStyleSheet("""
            QFrame#card {
                background: #ffffff;
                border: 1px solid #e8e9ef;
                border-radius: 12px;
            }
        """)
        return frame

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(0)

        shell = QFrame()
        shell.setObjectName("shell")
        shell_layout = QHBoxLayout(shell)
        shell_layout.setContentsMargins(12, 12, 12, 12)
        shell_layout.setSpacing(12)
        main_layout.addWidget(shell)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(205)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 14, 10, 10)
        sidebar_layout.setSpacing(12)

        title = QLabel("CircuitSense")
        title.setObjectName("app_title")
        sidebar_layout.addWidget(title)

        subtitle = QLabel("CIRCUIT DESIGN ASSISTANT")
        subtitle.setObjectName("app_subtitle")
        sidebar_layout.addWidget(subtitle)

        sidebar_layout.addSpacing(25)

        nav_label = QLabel("WORKSPACE")
        nav_label.setStyleSheet(
            "color: #858795; font-size: 10px; font-weight: 700;"
        )
        sidebar_layout.addWidget(nav_label)

        self.nav_buttons = []
        for text in ("Overview", "Schematic", "Analysis"):
            button = QPushButton(text)
            button.setCheckable(True)
            button.setObjectName("secondary")
            button.clicked.connect(
                lambda checked=False, name=text: self.select_nav(name)
            )
            sidebar_layout.addWidget(button)
            self.nav_buttons.append(button)

        self.nav_buttons[0].setChecked(True)

        sidebar_layout.addStretch()

        version = QLabel("CircuitSense  •  Development")
        version.setStyleSheet(
            "color: #858795; font-size: 10px;"
        )
        sidebar_layout.addWidget(version)

        shell_layout.addWidget(sidebar)

        # Page container: Overview, Schematic, and Analysis.
        self.pages = QStackedWidget()
        self.overview_page = self.build_overview_page()
        self.pages.addWidget(self.overview_page)
        self.schematic_page = self.build_schematic_page()
        self.pages.addWidget(self.schematic_page)
        shell_layout.addWidget(self.pages, 1)

        # Main content (Analysis page)
        content = QFrame()
        content.setObjectName("content")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(25, 23, 25, 22)
        content_layout.setSpacing(15)
        self.pages.addWidget(content)

        # Header
        header = QHBoxLayout()

        heading_layout = QVBoxLayout()
        heading_layout.setSpacing(3)

        heading = QLabel("Circuit Analysis")
        heading.setObjectName("section_title")
        heading_layout.addWidget(heading)

        description = QLabel(
            "Inspect schematic connectivity and electrical rules."
        )
        description.setObjectName("section_subtitle")
        heading_layout.addWidget(description)

        header.addLayout(heading_layout)
        header.addStretch()

        self.status = QLabel("●  READY")
        self.status.setObjectName("status")
        header.addWidget(self.status)

        content_layout.addLayout(header)

        # Schematic file selection
        file_card = self.card()
        file_layout = QVBoxLayout(file_card)
        file_layout.setContentsMargins(15, 13, 15, 13)
        file_layout.setSpacing(8)

        file_heading = QLabel("SCHEMATIC NETLIST")
        file_heading.setObjectName("metric_title")
        file_layout.addWidget(file_heading)

        file_row = QHBoxLayout()
        file_row.setSpacing(8)

        self.file_label = QLabel(str(self.netlist_path))
        self.file_label.setObjectName("file_label")
        self.file_label.setWordWrap(True)
        self.file_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        file_row.addWidget(self.file_label, 1)

        browse = QPushButton("Browse")
        browse.setObjectName("secondary")
        browse.clicked.connect(self.browse_file)
        file_row.addWidget(browse)

        file_layout.addLayout(file_row)
        content_layout.addWidget(file_card)

        # Summary cards
        metrics = QGridLayout()
        metrics.setHorizontalSpacing(10)
        metrics.setVerticalSpacing(10)

        self.findings_value = self.metric_card(
            "Total findings", "—", "findings", "#7057d9"
        )
        self.warnings_value = self.metric_card(
            "Warnings", "—", "warnings", "#d97706"
        )
        self.errors_value = self.metric_card(
            "Errors", "—", "errors", "#dc4444"
        )

        metrics.addWidget(self.findings_value, 0, 0)
        metrics.addWidget(self.warnings_value, 0, 1)
        metrics.addWidget(self.errors_value, 0, 2)

        content_layout.addLayout(metrics)

        # Analyze button
        action_row = QHBoxLayout()
        action_row.addStretch()

        self.analyze_button = QPushButton("Analyze")
        self.analyze_button.setMinimumWidth(130)
        self.analyze_button.clicked.connect(self.analyze)
        action_row.addWidget(self.analyze_button)

        content_layout.addLayout(action_row)

        # Results table
        results_heading = QLabel("Analysis results")
        results_heading.setStyleSheet(
            "font-size: 16px; font-weight: 700; color: #24252c;"
        )
        content_layout.addWidget(results_heading)

        self.results_table = QTableWidget(0, 6)
        self.results_table.setHorizontalHeaderLabels([
            "Rule", "Severity", "Component",
            "Finding", "Measured", "Limit"
        ])
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.results_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.results_table.setWordWrap(True)
        self.results_table.verticalHeader().setVisible(False)

        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )
        header.setSectionResizeMode(
            4, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            5, QHeaderView.ResizeMode.ResizeToContents
        )

        content_layout.addWidget(self.results_table, 1)

    def build_overview_page(self):
        page = QFrame()
        page.setObjectName("content")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(25, 23, 25, 22)
        layout.setSpacing(15)

        heading = QLabel("Circuit Overview")
        heading.setObjectName("section_title")
        layout.addWidget(heading)

        description = QLabel(
            "Summary of the components and connections in the loaded netlist."
        )
        description.setObjectName("section_subtitle")
        layout.addWidget(description)

        summary = QGridLayout()
        summary.setHorizontalSpacing(10)
        summary.setVerticalSpacing(10)
        self.overview_components_value = self.metric_card(
            "Components", "—", "components", "#7057d9"
        )
        self.overview_nets_value = self.metric_card(
            "Nets", "—", "nets", "#0891b2"
        )
        self.overview_findings_value = self.metric_card(
            "Last analysis findings", "—", "findings", "#d97706"
        )
        summary.addWidget(self.overview_components_value, 0, 0)
        summary.addWidget(self.overview_nets_value, 0, 1)
        summary.addWidget(self.overview_findings_value, 0, 2)
        layout.addLayout(summary)

        components_heading = QLabel("Components")
        components_heading.setStyleSheet(
            "font-size: 16px; font-weight: 700; color: #24252c;"
        )
        layout.addWidget(components_heading)

        self.components_table = QTableWidget(0, 5)
        self.components_table.setHorizontalHeaderLabels(
            [
                "Reference", "Type", "Value",
                "Library symbol", "Specifications",
            ]
        )
        self.components_table.setAlternatingRowColors(True)
        self.components_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.components_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.components_table.verticalHeader().setVisible(False)
        component_header = self.components_table.horizontalHeader()
        component_header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        component_header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        component_header.setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        component_header.setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )
        component_header.setSectionResizeMode(
            4, QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.components_table, 1)

        refresh_row = QHBoxLayout()
        refresh_row.addStretch()
        refresh_button = QPushButton("Refresh Overview")
        refresh_button.setObjectName("secondary")
        refresh_button.clicked.connect(self.refresh_overview)
        refresh_row.addWidget(refresh_button)
        layout.addLayout(refresh_row)

        return page

    def refresh_overview(self):
        if not hasattr(self, "components_table"):
            return

        self.components_table.setRowCount(0)
        try:
            if not self.netlist_path.is_file():
                self.overview_components_value.findChild(
                    QLabel, "metric_value"
                ).setText("—")
                self.overview_nets_value.findChild(
                    QLabel, "metric_value"
                ).setText("—")
                findings_count = getattr(
                    self, "last_findings_count", None
                )
                self.overview_findings_value.findChild(
                    QLabel, "metric_value"
                ).setText(str(
                    findings_count
                    if findings_count is not None
                    else "—"
                ))
                return

            circuit = load_circuit(str(self.netlist_path))
            components = circuit.get("components", [])
            nets = circuit.get("nets", [])

            self.overview_components_value.findChild(
                QLabel, "metric_value"
            ).setText(str(len(components)))
            self.overview_nets_value.findChild(
                QLabel, "metric_value"
            ).setText(str(len(nets)))
            findings_count = getattr(
                self, "last_findings_count", None
            )
            self.overview_findings_value.findChild(
                QLabel, "metric_value"
            ).setText(str(
                findings_count
                if findings_count is not None
                else "—"
            ))

            for component in components:
                row = self.components_table.rowCount()
                self.components_table.insertRow(row)
                recognition = classify_component_with_support(component)
                support_info = recognition.get("support_info") or {}
                component_type = support_info.get(
                    "name",
                    recognition.get("type", "unknown")
                    .replace("_", " ")
                    .title(),
                )
                specification_data = extract_specifications(component)
                values = [
                    component.get("reference", "—"),
                    component_type,
                    component.get("value", "—"),
                    component.get("lib_id", "—"),
                    self.format_specifications(
                        specification_data.get("specifications", {})
                    ),
                ]
                for column, value in enumerate(values):
                    item = QTableWidgetItem(str(value or "—"))
                    item.setFlags(
                        item.flags() & ~Qt.ItemFlag.ItemIsEditable
                    )
                    self.components_table.setItem(row, column, item)
            self.components_table.resizeRowsToContents()

        except (OSError, ValueError, KeyError) as error:
            self.overview_components_value.findChild(
                QLabel, "metric_value"
            ).setText("—")
            self.overview_nets_value.findChild(
                QLabel, "metric_value"
            ).setText("—")
            self.overview_findings_value.findChild(
                QLabel, "metric_value"
            ).setText("—")
            self.status.setText("●  OVERVIEW ERROR")
            QMessageBox.warning(
                self, "Overview could not be loaded", str(error)
            )

    @staticmethod
    def format_specifications(specifications):
        """Format extracted specifications for their component row."""
        values = []
        for name, details in specifications.items():
            value = details.get("value")
            unit = details.get("unit", "")
            if isinstance(value, (int, float)):
                if unit == "ohm":
                    formatted_value = f"{value:g} Ω"
                else:
                    formatted_value = f"{value:g} {unit}".strip()
            else:
                formatted_value = str(value)
            label = name.replace("_", " ").capitalize()
            values.append(f"{label}: {formatted_value}")
        return "; ".join(values) if values else "—"

    def build_schematic_page(self):
        page = QFrame()
        page.setObjectName("content")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(25, 23, 25, 22)
        layout.setSpacing(12)

        heading = QLabel("Schematic Viewer")
        heading.setObjectName("section_title")
        layout.addWidget(heading)

        description = QLabel(
            "Select a KiCad schematic to update analysis and view its SVG."
        )
        description.setObjectName("section_subtitle")
        layout.addWidget(description)

        file_row = QHBoxLayout()
        self.schematic_file_label = QLabel(
            str(self.schematic_path or "No schematic selected")
        )
        self.schematic_file_label.setObjectName("file_label")
        self.schematic_file_label.setWordWrap(True)
        self.schematic_file_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        file_row.addWidget(self.schematic_file_label, 1)

        browse_button = QPushButton("Browse Schematic")
        browse_button.setObjectName("secondary")
        browse_button.clicked.connect(self.browse_schematic)
        file_row.addWidget(browse_button)

        reload_button = QPushButton("Reload")
        reload_button.clicked.connect(self.load_schematic_svg)
        file_row.addWidget(reload_button)
        layout.addLayout(file_row)

        self.schematic_view = QSvgWidget()
        self.schematic_view.setMinimumSize(700, 450)
        self.schematic_view.setStyleSheet(
            "background: #f8f9fc; border: 1px solid #e7e8ee;"
        )
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.schematic_view)
        layout.addWidget(scroll, 1)

        self.schematic_message = QLabel(
            "Choose a KiCad schematic and click Reload to display it."
        )
        self.schematic_message.setObjectName("section_subtitle")
        self.schematic_message.setWordWrap(True)
        layout.addWidget(self.schematic_message)

        return page

    def browse_schematic(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select KiCad schematic",
            str(
                self.schematic_path.parent
                if self.schematic_path is not None
                else Path.home()
            ),
            "KiCad schematics (*.kicad_sch)"
        )
        if filename:
            schematic_path = Path(filename).resolve()
            analysis_tempdir = None

            try:
                analysis_tempdir, netlist_path = (
                    export_schematic_netlist(schematic_path)
                )
                load_circuit(str(netlist_path))
            except (
                OSError,
                RuntimeError,
                ValueError,
                KeyError,
                ET.ParseError,
            ) as error:
                if analysis_tempdir is not None:
                    analysis_tempdir.cleanup()
                QMessageBox.critical(
                    self,
                    "Schematic could not be loaded",
                    str(error),
                )
                return

            previous_tempdir = self._analysis_tempdir
            self._analysis_tempdir = analysis_tempdir
            self.netlist_path = netlist_path
            self.file_label.setText(str(self.netlist_path))
            self.schematic_path = schematic_path
            self.schematic_file_label.setText(str(self.schematic_path))
            if previous_tempdir is not None:
                previous_tempdir.cleanup()
            self.clear_results()
            self.status.setText("●  READY")
            self.refresh_overview()
            self.load_schematic_svg()

    def load_schematic_svg(self):
        if not hasattr(self, "schematic_view"):
            return

        if (
            self.schematic_path is None
            or not self.schematic_path.is_file()
        ):
            self.schematic_message.setText(
                "No matching schematic found. Use Browse Schematic to select a .kicad_sch file."
            )
            return

        try:
            if self._svg_tempdir is not None:
                self._svg_tempdir.cleanup()
            self._svg_tempdir = tempfile.TemporaryDirectory(
                prefix="circuitsense_svg_"
            )
            output_dir = Path(self._svg_tempdir.name)

            completed = subprocess.run(
                [
                    "kicad-cli", "sch", "export", "svg",
                    "-o", str(output_dir), str(self.schematic_path)
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            svg_files = sorted(output_dir.glob("*.svg"))
            if completed.returncode != 0 or not svg_files:
                detail = (completed.stderr or completed.stdout).strip()
                self.schematic_message.setText(
                    "Could not export the schematic to SVG. "
                    + (detail if detail else "Check that kicad-cli is installed.")
                )
                return

            self.schematic_view.load(str(svg_files[0]))
            self.schematic_message.setText(
                f"Displaying {svg_files[0].name}. "
                "For multi-sheet schematics, the first exported sheet is shown."
            )
        except OSError as error:
            self.schematic_message.setText(
                f"Could not run the KiCad exporter: {error}"
            )

    def closeEvent(self, event):
        for temp_dir in (
            self._svg_tempdir,
            self._analysis_tempdir,
        ):
            if temp_dir is not None:
                temp_dir.cleanup()
        super().closeEvent(event)

    def metric_card(self, title, value, name, color):
        frame = self.card()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 11, 14, 11)
        layout.setSpacing(5)

        title_label = QLabel(title.upper())
        title_label.setObjectName("metric_title")
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setObjectName("metric_value")
        value_label.setStyleSheet(
            f"color: {color}; font-size: 25px; font-weight: 700;"
        )
        layout.addWidget(value_label)

        return frame

    def select_nav(self, selected):
        page_indices = {
            "Overview": 0,
            "Schematic": 1,
            "Analysis": 2,
        }
        for button in self.nav_buttons:
            button.setChecked(button.text() == selected)

        self.pages.setCurrentIndex(page_indices[selected])
        if selected == "Overview":
            self.refresh_overview()
        elif selected == "Schematic":
            self.load_schematic_svg()

    def browse_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select KiCad XML netlist",
            str(self.netlist_path.parent),
            "XML netlists (*.xml)"
        )

        if filename:
            previous_tempdir = self._analysis_tempdir
            self._analysis_tempdir = None
            self.netlist_path = Path(filename).resolve()
            self.file_label.setText(str(self.netlist_path))
            self.schematic_path = self.netlist_path.with_suffix(
                ".kicad_sch"
            )
            if not self.schematic_path.is_file():
                self.schematic_path = None
            self.schematic_file_label.setText(
                str(self.schematic_path or "No schematic selected")
            )
            if previous_tempdir is not None:
                previous_tempdir.cleanup()
            self.clear_results()
            self.load_schematic_svg()
            self.status.setText("●  READY")

    def analyze(self):
        if not self.netlist_path.is_file():
            QMessageBox.warning(
                self,
                "File not found",
                "Please select a valid XML netlist."
            )
            return

        try:
            self.status.setText("●  ANALYZING")
            self.analyze_button.setEnabled(False)
            QApplication.processEvents()

            circuit = load_circuit(str(self.netlist_path))

            results = analyze_circuit(circuit)
            if self.schematic_path is not None:
                results.extend(
                    run_schematic_erc(self.schematic_path)
                )
            self.show_results(results)

            self.status.setText("●  COMPLETE")

        except (OSError, ValueError, KeyError) as error:
            self.status.setText("●  FAILED")
            QMessageBox.critical(
                self,
                "Analysis failed",
                f"Could not analyze the netlist:\n\n{error}"
            )
        except Exception as error:
            self.status.setText("●  FAILED")
            QMessageBox.critical(
                self,
                "Unexpected analysis error",
                f"An unexpected error occurred:\n\n{error}"
            )
        finally:
            self.analyze_button.setEnabled(True)

    def clear_results(self):
        self.last_findings_count = None
        self.results_table.setRowCount(0)
        for metric in (
            self.findings_value,
            self.warnings_value,
            self.errors_value,
        ):
            metric.findChild(
                QLabel, "metric_value"
            ).setText("—")

    def show_results(self, results):
        results = [
            result for result in results
            if result.rule_id != "ERC_LIB_SYMBOL_MISMATCH"
        ]
        self.last_findings_count = len(results)
        self.results_table.setRowCount(0)

        warning_count = sum(
            1 for result in results
            if result.severity.lower() == "warning"
        )
        error_count = sum(
            1 for result in results
            if result.severity.lower() == "error"
        )

        self.findings_value.findChild(
            QLabel, "metric_value"
        ).setText(str(len(results)))

        self.warnings_value.findChild(
            QLabel, "metric_value"
        ).setText(str(warning_count))

        self.errors_value.findChild(
            QLabel, "metric_value"
        ).setText(str(error_count))

        for result in results:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)

            measured = self.format_value(result.measured, result.rule_id)
            limit = self.format_value(result.limit, result.rule_id)

            values = [
                result.rule_id,
                result.severity.upper(),
                result.component or "—",
                result.message,
                measured,
                limit
            ]

            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(
                    item.flags()
                    & ~Qt.ItemFlag.ItemIsEditable
                )

                if column == 1:
                    severity = result.severity.lower()
                    if severity == "error":
                        item.setForeground(QColor("#dc4444"))
                    elif severity == "warning":
                        item.setForeground(QColor("#d97706"))
                    else:
                        item.setForeground(QColor("#398a65"))

                self.results_table.setItem(row, column, item)

        self.results_table.resizeRowsToContents()
    def format_value(self, value, rule_id):
        if value is None:
            return "—"
        if rule_id.startswith("LED_"):
            return f"{value:g} mA"
        if rule_id.startswith("RES_"):
            return f"{value:g} W"
        return str(value)
