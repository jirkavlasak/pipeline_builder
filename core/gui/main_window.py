import sys
import os
import json
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QListWidget, QTextEdit, QLabel, QMenuBar, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton,QScrollArea, QFrame,
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QFileDialog,
    QGroupBox
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


class PipelineSettingsDialog(QDialog):
    def __init__(self, modules, module_info, workflow_params, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pipeline Settings")
        self.setMinimumSize(600, 400)

        self.widgets = {}
        self.module_info = module_info
        self.workflow_params = workflow_params

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # --- Vstupy a parametry pro každý modul ---
        for module_name in modules:
            module_data = self.module_info.get(module_name, {})
            
            # Vstupy
            inputs = module_data.get("input", [])
            if inputs:
                group_box = QGroupBox(f"Inputs for {module_name}")
                group_layout = QFormLayout()
                
                for input_def in inputs:
                    # Zpracování nového i starého formátu
                    if isinstance(input_def, dict):
                        input_id = input_def.get("id")
                    else:
                        input_id = input_def

                    input_edit = QLineEdit()
                    # Načtení uložené hodnoty, pokud existuje
                    if module_name in self.workflow_params and input_id in self.workflow_params[module_name]:
                        input_edit.setText(self.workflow_params[module_name][input_id])

                    select_button = QPushButton("Select File")
                    select_button.clicked.connect(lambda _, le=input_edit: self.select_file(le))
                    
                    row_layout = QHBoxLayout()
                    row_layout.addWidget(input_edit)
                    row_layout.addWidget(select_button)
                    
                    group_layout.addRow(f"{input_id}:", row_layout)
                    self.widgets.setdefault(module_name, {})[input_id] = input_edit

                group_box.setLayout(group_layout)
                form_layout.addWidget(group_box)

            # Parametry
            params = module_data.get("params", [])
            if params:
                group_box = QGroupBox(f"Parameters for {module_name}")
                group_layout = QFormLayout()

                for param in params:
                    param_id = param.get("id")
                    param_edit = QLineEdit()
                    # Načtení uložené hodnoty nebo defaultní
                    default_value = param.get("default", "")
                    current_value = self.workflow_params.get(module_name, {}).get(param_id, default_value)
                    param_edit.setText(str(current_value))
                    
                    group_layout.addRow(f"{param_id}:", param_edit)
                    self.widgets.setdefault(module_name, {})[param_id] = param_edit
                
                group_box.setLayout(group_layout)
                form_layout.addWidget(group_box)


        # --- Obecné nastavení ---
        general_group = QGroupBox("General Settings")
        general_layout = QFormLayout()
        
        self.output_dir_edit = QLineEdit()
        if "_general_output_dir" in self.workflow_params:
            self.output_dir_edit.setText(self.workflow_params["_general_output_dir"])
        
        select_out_button = QPushButton("Select Directory")
        select_out_button.clicked.connect(self.select_output_dir)
        
        out_layout = QHBoxLayout()
        out_layout.addWidget(self.output_dir_edit)
        out_layout.addWidget(select_out_button)
        general_layout.addRow("Global Output Directory:", out_layout)
        
        general_group.setLayout(general_layout)
        form_layout.addWidget(general_group)

        # --- Tlačítka OK/Cancel ---
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)

    def select_file(self, line_edit):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Input File")
        if file_path:
            line_edit.setText(file_path)

    def select_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if dir_path:
            self.output_dir_edit.setText(dir_path)

    def get_all_values(self):
        result = {}
        for module_name, widgets in self.widgets.items():
            result[module_name] = {pname: edit.text() for pname, edit in widgets.items()}
        # Přidejte společný výstupní adresář
        result["_general_output_dir"] = self.output_dir_edit.text()
        return result


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pipeline Builder")
        self.resize(1200, 700)

        # ---- Načíst moduly ----
        self.module_info = load_modules()
        self.workflow_params = {}  # inicializace zde

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
        self.workflow_area.setContextMenuPolicy(Qt.CustomContextMenu)
        self.workflow_area.customContextMenuRequested.connect(self.show_workflow_context_menu)
        self.workflow_area.keyPressEvent = self.workflow_key_press_event  # Přidá podporu pro Delete
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Workflow"))
        right_layout.addWidget(self.workflow_area)

        # --- Pipeline Settings a Create Pipeline tlačítka ---
        pipeline_btns_layout = QHBoxLayout()
        self.btn_settings = QPushButton("Pipeline Settings")
        self.btn_settings.clicked.connect(self.open_pipeline_settings)
        self.btn_generate = QPushButton("Create Pipeline")
        self.btn_generate.clicked.connect(self.generate_pipeline)
        pipeline_btns_layout.addWidget(self.btn_settings)
        pipeline_btns_layout.addWidget(self.btn_generate)
        right_layout.addLayout(pipeline_btns_layout)

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

        # --- Tlačítka pro pipeline ---
        pipeline_btn_layout = QHBoxLayout()
        self.btn_run = QPushButton("Run pipeline")
        self.btn_run.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.btn_run.clicked.connect(self.run_pipeline)

        self.btn_pause = QPushButton("Pause pipeline")
        self.btn_pause.setStyleSheet("background-color: #FFD700; color: black; font-weight: bold;")
        self.btn_pause.clicked.connect(self.pause_pipeline)

        self.btn_end = QPushButton("End pipeline")
        self.btn_end.setStyleSheet("background-color: #F44336; color: white; font-weight: bold;")
        self.btn_end.clicked.connect(self.end_pipeline)

        pipeline_btn_layout.addWidget(self.btn_run)
        pipeline_btn_layout.addWidget(self.btn_pause)
        pipeline_btn_layout.addWidget(self.btn_end)
        main_layout.addLayout(pipeline_btn_layout)

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
            # Vyčištění parametrů
            for i in reversed(range(self.param_layout.count())):
                widget = self.param_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()
            return

        # Zpracování vstupů a výstupů pro zobrazení
        input_list = data.get("input", [])
        inputs = ", ".join([d.get("id") if isinstance(d, dict) else str(d) for d in input_list])

        output_list = data.get("output", [])
        outputs = ", ".join([d.get("path") if isinstance(d, dict) else str(d) for d in output_list])

        # Popis + URL + Input/Output
        desc = (
            f"{data.get('name', 'N/A')}\n\n"
            f"{data.get('description', '')}\n\n"
            f"Input: {inputs}\n"
            f"Output: {outputs}"
        )
        self.info_description.setPlainText(desc)

        # Parametry
        # Vyčistit staré parametry
        for i in reversed(range(self.param_layout.count())):
            widget = self.param_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Přidat nové parametry
        params = data.get("params", []) # Očekáváme seznam slovníků
        if params:
            for param_info in params:
                param_id = param_info.get("id", "N/A")
                param_type = param_info.get("type", "str")
                param_default = param_info.get("default", "None")

                # Detail parametru (název, typ, default)
                detail_text = f"{param_id} (type: {param_type}, default: {param_default})"
                detail_label = QLabel(detail_text)
                detail_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
                self.param_layout.addWidget(detail_label)

                # Oddělovací čára
                line = QFrame()
                line.setFrameShape(QFrame.HLine)
                line.setFrameShadow(QFrame.Sunken)
                self.param_layout.addWidget(line)
        else:
            self.param_layout.addWidget(QLabel("No parameters."))

    def add_module_to_workflow(self, item):
        """Přidá modul do workflow panelu BEZ dialogu pro parametry"""
        module_name = item.text()
        if self.workflow_area.findItems(module_name, Qt.MatchExactly):
            self.log(f"Module {module_name} is already in workflow.")
            return
        self.workflow_area.addItem(module_name)
        self.log(f"Module {module_name} was added to workflow.")

    def open_pipeline_settings(self):
        """Otevře dialog pro nastavení parametrů všech modulů ve workflow"""
        modules = [self.workflow_area.item(i).text() for i in range(self.workflow_area.count())]
        if not modules:
            self.log("Workflow is empty.")
            return
        dialog = PipelineSettingsDialog(modules, self.module_info, self.workflow_params, self)
        if dialog.exec():
            all_param_values = dialog.get_all_values()
            for module_name, param_values in all_param_values.items():
                self.workflow_params[module_name] = param_values
                self.log(f"Parameters for {module_name} set: {param_values}")

            # --- Shrnutí Docker image ---
            docker_images = []
            missing = []
            for module_name in modules:
                # Hledat docker image pod oběma klíči
                docker_image = (
                    self.module_info[module_name].get("docker_image")
                    or self.module_info[module_name].get("container")
                )
                if docker_image:
                    docker_images.append(f"{module_name}: {docker_image}")
                else:
                    missing.append(module_name)
            summary = "Docker images required for this pipeline:\n"
            summary += "\n".join(docker_images) if docker_images else "None"
            if missing:
                summary += "\n\nWARNING: These modules have no Docker image specified:\n"
                summary += "\n".join(missing)

            # Zobrazit v samostatném okně
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Docker Environment Summary", summary)

    def generate_pipeline(self):
        """Generuje validní Nextflow DSL2 skript podle workflow a parametrů z GUI."""
        modules = [self.workflow_area.item(i).text() for i in range(self.workflow_area.count())]
        if not modules:
            self.log("Workflow is empty.")
            return

        script_lines = [
            "#!/usr/bin/env nextflow",
            "",
            "nextflow.enable.dsl=2",
            ""
        ]

        # --- Parametry a kanály pro workflow blok ---
        workflow_params_lines = []
        input_channels = {}
        general_output_dir = self.workflow_params.get("_general_output_dir", "")

        for module_name in modules:
            module_data = self.module_info[module_name]
            params = self.workflow_params.get(module_name, {})
            # Najdi první definovaný vstupní soubor a vytvoř pro něj kanál
            for input_def in module_data.get("input", []):
                input_key = input_def if isinstance(input_def, str) else input_def.get("id")
                if input_key in params and params[input_key]:
                    channel_name = f"{module_name.upper().replace(' ', '_')}_IN"
                    workflow_params_lines.append(f"    {channel_name} = Channel.fromPath('{params[input_key]}')")
                    input_channels[module_name] = channel_name
                    break

        if general_output_dir:
             workflow_params_lines.append(f"    params.outdir = '{general_output_dir}'")


        # --- Procesy ---
        for module_name in modules:
            data = self.module_info[module_name]
            params = self.workflow_params.get(module_name, {})
            container = data.get("container", "")
            command_template = data.get("command", "")
            process_name = module_name.upper().replace(" ", "_")

            script_lines.append(f"process {process_name} {{")
            if container:
                script_lines.append(f"    container '{container}'")

            # --- Input ---
            script_lines.append("    input:")
            input_vars = {} # Mapování id vstupu na proměnnou (např. 'reads')
            for input_def in data.get("input", []):
                if isinstance(input_def, str): # Jednoduchý formát "input_id"
                    input_id = input_def
                    var_name = "input_files"
                else: # Strukturovaný formát {"id": "...", "variable": "..."
                    input_id = input_def.get("id")
                    var_name = input_def.get("variable", "input_files")
                
                script_lines.append(f"    path {var_name}")
                input_vars[input_id] = var_name

            # --- Output ---
            script_lines.append("    output:")
            for output_def in data.get("output", []):
                if isinstance(output_def, dict):
                    # Nový formát: {"path": "...", "emit": "..."
                    path = output_def.get("path")
                    emit_name = output_def.get("emit")
                    script_lines.append(f"    path '{path}', emit: {emit_name}")
                else:
                    # Starý formát: "soubor.txt"
                    # Vygenerujeme výstup bez 'emit'
                    script_lines.append(f"    path '{output_def}'")

            # --- Script ---
            script_lines.append("    script:")
            command = command_template
            # Nahrazení zástupných symbolů pro vstupy
            for input_id, var_name in input_vars.items():
                command = command.replace(f"{{{input_id}}}", f"${{{var_name}}}")
            # Nahrazení parametrů
            for pname, pval in params.items():
                if f"{{{pname}}}" in command:
                    command = command.replace(f"{{{pname}}}", str(pval))
            
            # Nahrazení obecných zástupných symbolů (např. pro multiqc)
            command = command.replace("{*}", ".")
            command = command.replace("{results}", ".")

            script_lines.append('    """')
            script_lines.append(f"    {command.strip()}")
            script_lines.append('    """')
            script_lines.append("}\n")

        # --- Workflow blok ---
        script_lines.append("workflow {")
        script_lines.extend(workflow_params_lines)
        
        process_outputs = {} # Udržuje výstupy z procesů
        for module_name in modules:
            process_name = module_name.upper().replace(" ", "_")
            module_data = self.module_info[module_name]
            
            input_for_call = ""
            # Zjistíme, zda má modul vlastní definovaný vstupní kanál
            if module_name in input_channels:
                input_for_call = input_channels[module_name]
            else:
                # Pokud ne, pokusí se najít vstup z předchozích procesů
                input_source_def = module_data.get("workflow_input", {})
                source_process = input_source_def.get("process")
                source_emit = input_source_def.get("emit")
                collect = input_source_def.get("collect", False)

                if source_process and source_emit and source_process in process_outputs:
                    input_for_call = f"{process_outputs[source_process]}.{source_emit}"
                    if collect:
                        input_for_call += ".collect()"

            call = f"    {process_name}({input_for_call})"
            script_lines.append(call)
            process_outputs[module_name] = f"{process_name}.out"

        script_lines.append("}")

        # --- Uložit soubor ---
        output_dir = os.path.join("core", "gui", "workflows")
        os.makedirs(output_dir, exist_ok=True)
        nf_path = os.path.join(output_dir, "main.nf")
        with open(nf_path, "w", encoding="utf-8") as f:
            f.write("\n".join(script_lines))

        self.log(f"Pipeline script generated at {nf_path}")


    def log(self, message: str):
        """Vypíše zprávu do log panelu"""
        self.log_area.append(message)

    # --- Pipeline tlačítka ---
    def run_pipeline(self):
        self.log("Pipeline started.")

    def pause_pipeline(self):
        self.log("Pipeline paused.")

    def end_pipeline(self):
        self.log("Pipeline ended.")

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
