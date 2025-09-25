import sys
import os
import json
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QListWidget, QTextEdit, QLabel, QMenuBar, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton,QScrollArea, QFrame
)


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
        left_layout.addWidget(QLabel("Dostupné moduly"))
        left_layout.addWidget(self.module_list)
        left_panel = QWidget()
        left_panel.setLayout(left_layout)

        # ---- Pravý horní panel: workflow ----
        self.workflow_area = QListWidget()
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Workflow"))
        right_layout.addWidget(self.workflow_area)

        self.btn_generate = QPushButton("Vygenerovat pipeline")
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

    def show_module_info(self, item):
        """Zobrazí detail vybraného modulu"""
        name = item.text()
        data = self.module_info.get(name)

        if not data:
            self.info_description.setPlainText("Žádné informace o modulu.")
            self.info_table.clearContents()
            self.info_table.setRowCount(0)
            return

        # Popis + URL
        desc = f"{data['name']}\n\n{data['description']}\n\n🔗 {data['url']}"
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
            self.param_layout.addWidget(QLabel("Žádné parametry."))

    def add_module_to_workflow(self, item):
        """Přidá modul do workflow panelu"""
        self.workflow_area.addItem(item.text())
        self.log(f"Modul {item.text()} přidán do workflow")

    def generate_pipeline(self):
        """Zatím jen logovací funkce"""
        modules = [self.workflow_area.item(i).text() for i in range(self.workflow_area.count())]
        self.log(f"Pipeline by obsahovala: {', '.join(modules)}")

    def log(self, message: str):
        """Vypíše zprávu do log panelu"""
        self.log_area.append(message)

    # ---- Menu funkce ----
    def new_project(self):
        self.workflow_area.clear()
        self.log("Nový projekt vytvořen")

    def open_project(self):
        self.log("TODO: Implementovat načtení projektu")

    def save_project(self):
        self.log("TODO: Implementovat uložení projektu")

    def show_about(self):
        self.log("Pipeline Builder v0.1\nVyvíjeno v Python + PySide6")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
