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
        self.resize(600, 600)
        self.layout = QVBoxLayout(self)
        self.param_widgets = {}

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        form_layout = QFormLayout(content)  # OPRAVA zde (původně QVBoxLayout)

        # --- General output dir (společný pro všechny moduly) ---
        self.output_dir_edit = QLineEdit()
        output_dir_btn = QPushButton("Browse")
        output_dir_btn.clicked.connect(self.select_output_dir)
        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(self.output_dir_edit)
        output_dir_layout.addWidget(output_dir_btn)
        form_layout.addRow("General output directory:", output_dir_layout)

        for module_name in modules:
            params = module_info[module_name].get("parameters", {})
            inputs = module_info[module_name].get("input", [])
            group = QGroupBox(module_name)
            group_layout = QFormLayout(group)
            widgets = {}

            # Dynamicky pro všechny vstupy
            for input_name in inputs:
                input_edit = QLineEdit()
                input_btn = QPushButton("Browse")
                input_btn.clicked.connect(lambda _, e=input_edit: self.select_file(e))
                input_layout = QHBoxLayout()
                input_layout.addWidget(input_edit)
                input_layout.addWidget(input_btn)
                group_layout.addRow(f"{input_name}:", input_layout)
                widgets[input_name] = input_edit

            # Parametry modulu
            for pname, pinfo in params.items():
                edit = QLineEdit(str(pinfo.get("default", "")))
                group_layout.addRow(f"{pname}:", edit)
                widgets[pname] = edit

            # Předvyplnit předchozí hodnoty
            if module_name in workflow_params:
                for pname, edit in widgets.items():
                    if pname in workflow_params[module_name]:
                        edit.setText(workflow_params[module_name][pname])

            group.setLayout(group_layout)
            form_layout.addWidget(group)
            self.param_widgets[module_name] = widgets

        content.setLayout(form_layout)
        scroll.setWidget(content)
        self.layout.addWidget(scroll)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

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
        for module_name, widgets in self.param_widgets.items():
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

        # --- Kontrola, že všechny moduly mají input_files tam, kde je třeba ---
        for module_name in modules:
            module_params = self.workflow_params.get(module_name, {})
            #if self.module_info[module_name].get("input") and not module_params.get("input_files"):
            #    from PySide6.QtWidgets import QMessageBox
            #    QMessageBox.warning(
            #        self,
            #        "Missing input files",
            #        f"No input files selected for module '{module_name}'. Please select them in Pipeline Settings."
            #    )
            #    self.log(f"Pipeline generation aborted: input files missing for {module_name}")
             #   return

        script_lines = [
            "#!/usr/bin/env nextflow",
            "",
            "nextflow.enable.dsl=2",
            ""
        ]

        # --- Procesy ---
        for module_name in modules:
            data = self.module_info[module_name]
            params = self.workflow_params.get(module_name, {})
            container = data.get("container", "")
            command_template = data.get("command", "")

            # Nahrazení parametrů
            command = command_template
            for pname, pval in params.items():
                pname_clean = pname[2:] if pname.startswith("--") else pname
                command = command.replace(f"{{{pname_clean}}}", pval)

            # Nahrazení vstupů placeholder
            if data.get("input"):
                command = command.replace("{input}", "${reads}")
            else:
                # moduly bez vstupu, pokud je placeholder {input}, nech ho prázdný
                command = command.replace("{input}", "")

            # Přidání --outdir pokud není v command
            if "--outdir" not in command and container:
                command += " --outdir ${task.process}"

            # Název procesu
            process_name = module_name.upper().replace(" ", "_")
            script_lines.append(f"process {process_name} {{")
            if container:
                script_lines.append(f"    container '{container}'")

            # --- Input ---
            script_lines.append("    input:")
            if data.get("input"):
                script_lines.append("        path reads")
            else:
                script_lines.append("        path dummy_input")  # kanál se nastaví workflow blokem

            # --- Output ---
            outputs = data.get("output", [])
            script_lines.append("    output:")
            if len(outputs) > 1:
                script_lines.append("        path '*'")
            elif outputs:
                for outp in outputs:
                    script_lines.append(f"        path '{outp}'")
            else:
                script_lines.append("        path 'output_*'")

            # --- Script ---
            script_lines.append("    script:")
            script_lines.append("    \"\"\"")
            script_lines.append(f"    {command}")
            script_lines.append("    \"\"\"")
            script_lines.append("}\n")

        # --- Workflow blok ---
        script_lines.append("workflow {")
        prev_channel = None

        for i, module_name in enumerate(modules):
            process_name = module_name.upper().replace(" ", "_")
            module_params = self.workflow_params.get(module_name, {})

            if module_params.get("input_files"):
                # první modul s input_files → vytvoří channel
                prev_channel = f"{process_name}_in"
                script_lines.append(f"    {prev_channel} = Channel.fromPath('{module_params['input_files']}')")

            # zavolat proces s předaným kanálem
            if prev_channel:
                script_lines.append(f"    {process_name}({prev_channel})")
                prev_channel = f"{process_name}.out"
            else:
                # moduly bez input_files → zavoláme je bez argumentu
                script_lines.append(f"    {process_name}()")

        script_lines.append("}")

        # --- Uložit soubor ---
        output_dir = "workflows"
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
