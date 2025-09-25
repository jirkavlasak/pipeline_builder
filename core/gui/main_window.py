import sys
import os
import json
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QListWidget, QTextEdit, QLabel, QMenuBar, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton,QScrollArea, QFrame,
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QFileDialog
)
from PySide6.QtCore import Qt,QPoint
from PySide6.QtWidgets import QMenu


def load_modules():
    """Načte všechny JSON moduly ze složky modules/"""
    module_info = {}
    if not os.path.exists("modules"):
        os.makedirs("modules")
    for file in os.listdir("modules"):
        if file.endswith(".json"):
            with open(os.path.join("modules", file), "r", encoding="utf-8") as f:
                data = json.load(f)
                module_info[data["name"]] = data
    return module_info


class ParameterDialog(QDialog):
    def __init__(self, module_name, parameters, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Set parameters for {module_name}")
        self.resize(400, 300)
        self.layout = QFormLayout(self)
        self.inputs = {}

        # Input files s tlačítkem
        self.input_files_edit = QLineEdit()
        self.input_files_btn = QPushButton("Browse")
        self.input_files_btn.clicked.connect(self.select_input_file)
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_files_edit)
        input_layout.addWidget(self.input_files_btn)
        self.layout.addRow("Input files path:", input_layout)

        # Output files s tlačítkem
        self.output_files_edit = QLineEdit()
        self.output_files_btn = QPushButton("Browse")
        self.output_files_btn.clicked.connect(self.select_output_file)
        output_layout = QHBoxLayout()
        output_layout.addWidget(self.output_files_edit)
        output_layout.addWidget(self.output_files_btn)
        self.layout.addRow("Output files path:", output_layout)

        # Parametry modulu
        for pname, pinfo in parameters.items():
            edit = QLineEdit(str(pinfo.get("default", "")))
            self.layout.addRow(f"{pname}:", edit)
            self.inputs[pname] = edit

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def select_input_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Input File")
        if file_path:
            self.input_files_edit.setText(file_path)

    def select_output_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Select Output File")
        if file_path:
            self.output_files_edit.setText(file_path)

    def get_values(self):
        values = {pname: edit.text() for pname, edit in self.inputs.items()}
        values["input_files"] = self.input_files_edit.text()
        values["output_files"] = self.output_files_edit.text()
        return values


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pipeline Builder")
        self.resize(1200, 700)

        # ---- Načíst moduly ----
        self.module_info = load_modules()

        # ---- Horní menu ----
        menubar = QMenuBar(self)
        file_menu = menubar.addMenu("File")
        file_menu.addAction("New", self.new_project)
        file_menu.addAction("Open", self.open_project)
        file_menu.addAction("Save", self.save_project)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)

        help_menu = menubar.addMenu("Help")
        help_menu.addAction("About", self.show_about)

        self.setMenuBar(menubar)

        # ---- Levý panel: seznam modulů ----
        self.module_list = QListWidget()
        self.module_list.addItems(self.module_info.keys())
        self.module_list.itemClicked.connect(self.show_module_info)
        self.module_list.itemDoubleClicked.connect(self.add_module_to_workflow)

        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Available Modules"))
        left_layout.addWidget(self.module_list)
        left_panel = QWidget()
        left_panel.setLayout(left_layout)

        # ---- Pravý horní panel: workflow ----
        self.workflow_area = QListWidget()
        from PySide6.QtCore import Qt, QPoint
        from PySide6.QtWidgets import QMenu
        # ...existing code...        self.workflow_area.setContextMenuPolicy(Qt.CustomContextMenu)
        self.workflow_area.customContextMenuRequested.connect(self.show_workflow_context_menu)
        self.workflow_area.keyPressEvent = self.workflow_key_press_event  # Přidá podporu pro Delete
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Workflow"))
        right_layout.addWidget(self.workflow_area)

        self.btn_generate = QPushButton("Create Pipeline")
        self.btn_generate.clicked.connect(self.generate_pipeline)
        right_layout.addWidget(self.btn_generate)
        right_panel = QWidget()
        right_panel.setLayout(right_layout)

        # ---- Pravý spodní panel: module info ----
        self.info_description = QTextEdit()
        self.info_description.setReadOnly(True)

        # Kontejner pro parametry
        self.param_container = QWidget()
        self.param_layout = QVBoxLayout()
        self.param_container.setLayout(self.param_layout)

        # Scrollovací oblast (aby se daly parametry posouvat)
        self.param_scroll = QScrollArea()
        self.param_scroll.setWidgetResizable(True)
        self.param_scroll.setWidget(self.param_container)

        info_layout = QVBoxLayout()
        info_layout.addWidget(QLabel("Module Info"))
        info_layout.addWidget(self.info_description, 2)
        info_layout.addWidget(QLabel("Parameters"))
        info_layout.addWidget(self.param_scroll, 3)

        info_panel = QWidget()
        info_panel.setLayout(info_layout)

        # ---- Log panel (dole) ----
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)

        # ---- Hlavní rozložení ----
        main_split = QHBoxLayout()
        main_split.addWidget(left_panel, 2)
        main_split.addWidget(right_panel, 3)
        main_split.addWidget(info_panel, 4)

        top_panel = QWidget()
        top_panel.setLayout(main_split)

        main_layout = QVBoxLayout()
        main_layout.addWidget(top_panel, 5)
        main_layout.addWidget(QLabel("Log"))
        main_layout.addWidget(self.log_area, 2)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    # ---------- Funkce ----------

    def show_workflow_context_menu(self, pos: QPoint):
        item = self.workflow_area.itemAt(pos)
        if item:
            menu = QMenu()
            remove_action = menu.addAction("Delete Module")
            action = menu.exec(self.workflow_area.mapToGlobal(pos))
            if action == remove_action:
                row = self.workflow_area.row(item)
                self.workflow_area.takeItem(row)
                self.log(f"Module {item.text()} was removed from workflow")

    def workflow_key_press_event(self, event):
        if event.key() == Qt.Key_Delete:
            selected_items = self.workflow_area.selectedItems()
            for item in selected_items:
                row = self.workflow_area.row(item)
                self.workflow_area.takeItem(row)
                self.log(f"Module {item.text()} was removed from workflow")
        else:
            QListWidget.keyPressEvent(self.workflow_area, event)


    def show_module_info(self, item):
        """Zobrazí detail vybraného modulu"""
        name = item.text()
        data = self.module_info.get(name)

        if not data:
            self.info_description.setPlainText("There are no informations about this module.")
            self.info_table.clearContents()
            self.info_table.setRowCount(0)
            return

        # Popis + URL + Input/Output
        inputs = ", ".join(data.get("input", []))
        outputs = ", ".join(data.get("output", []))
        desc = (
            f"{data['name']}\n\n"
            f"{data['description']}\n\n"
            f"🔗 {data['url']}\n\n"
            f"Input: {inputs}\n"
            f"Output: {outputs}"
        )
        self.info_description.setPlainText(desc)

        # Parametry
        for i in reversed(range(self.param_layout.count())):
            widget = self.param_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

# Přidat nové parametry
        params = data.get("parameters", {})
        if params:
            for pname, pinfo in params.items():
                # Popis
                desc_label = QLabel(pinfo.get("description", ""))
                desc_label.setWordWrap(True)
                desc_label.setStyleSheet("font-style: italic; color: gray; margin-top:10px;")
                self.param_layout.addWidget(desc_label)

                # Detail parametru (název, typ, default)
                detail_text = f"{pname} ({pinfo.get('type', 'str')}, default={pinfo.get('default', 'None')})"
                detail_label = QLabel(detail_text)
                detail_label.setStyleSheet("font-weight: bold;")
                self.param_layout.addWidget(detail_label)

                # Oddělovací čára
                line = QFrame()
                line.setFrameShape(QFrame.HLine)
                line.setFrameShadow(QFrame.Sunken)
                self.param_layout.addWidget(line)
        else:
            self.param_layout.addWidget(QLabel("No parameters."))

    def add_module_to_workflow(self, item):
        """Přidá modul do workflow panelu a otevře dialog pro parametry"""
        module_name = item.text()
        params = self.module_info[module_name].get("parameters", {})
        dialog = ParameterDialog(module_name, params, self)
        if dialog.exec():
            param_values = dialog.get_values()
            # Uložte parametry k modulu (např. do slovníku)
            if not hasattr(self, "workflow_params"):
                self.workflow_params = {}
            self.workflow_params[module_name] = param_values
            self.workflow_area.addItem(module_name)
            self.log(f"Module {module_name} was added to workflow with parameters: {param_values}")
        else:
            self.log(f"Module {module_name} was not added to workflow")

    def generate_pipeline(self):
        """Zatím jen logovací funkce"""
        modules = [self.workflow_area.item(i).text() for i in range(self.workflow_area.count())]
        self.log(f"Pipeline will contain: {', '.join(modules)}")

    def log(self, message: str):
        """Vypíše zprávu do log panelu"""
        self.log_area.append(message)

    # ---- Menu funkce ----
    def new_project(self):
        self.workflow_area.clear()
        self.log("New project created")

    def open_project(self):
        self.log("TODO: Implementovat načtení projektu")

    def save_project(self):
        self.log("TODO: Implementovat uložení projektu")

    def show_about(self):
        self.log("Pipeline Builder v0.1 - Created by Altho")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
