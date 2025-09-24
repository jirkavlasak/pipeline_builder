import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout,
    QHBoxLayout, QWidget, QListWidget, QTextEdit, QLabel, QMenuBar, QMenu
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pipeline Builder")
        self.resize(1000, 700)

        # ---- Modulová "knihovna" s popisy ----
        self.module_info = {
            "FastQC": "Nástroj pro kontrolu kvality sekvenačních dat (FASTQ).",
            "Trimmomatic": "Ořezává adaptery a nízkou kvalitu z FASTQ souborů.",
            "BWA": "Mapování DNA čtení na referenční genom.",
            "GATK": "Toolkit pro variant calling a analýzu genomických dat."
        }

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

        # ---- Pravý spodní panel: modul info ----
        self.info_area = QTextEdit()
        self.info_area.setReadOnly(True)

        info_layout = QVBoxLayout()
        info_layout.addWidget(QLabel("Module Info"))
        info_layout.addWidget(self.info_area)

        info_panel = QWidget()
        info_panel.setLayout(info_layout)

        # ---- Log panel (dole) ----
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)

        # ---- Hlavní rozložení ----
        main_split = QHBoxLayout()
        main_split.addWidget(left_panel, 2)
        main_split.addWidget(right_panel, 3)
        main_split.addWidget(info_panel, 3)

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
        """Zobrazí popis vybraného modulu"""
        name = item.text()
        description = self.module_info.get(name, "Popis není dostupný.")
        self.info_area.setPlainText(f"{name}\n\n{description}")

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
