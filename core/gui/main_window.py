import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout,
    QHBoxLayout, QWidget, QListWidget, QTextEdit, QLabel
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pipeline Builder")
        self.resize(900, 600)

        # ---- Levý panel: seznam modulů ----
        self.module_list = QListWidget()
        self.module_list.addItems(["FastQC", "Trimmomatic", "BWA", "GATK"])
        self.module_list.itemDoubleClicked.connect(self.add_module_to_workflow)

        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Dostupné moduly"))
        left_layout.addWidget(self.module_list)

        left_panel = QWidget()
        left_panel.setLayout(left_layout)

        # ---- Pravý panel: workflow canvas ----
        self.workflow_area = QListWidget()  # zatím jen seznam
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Workflow"))
        right_layout.addWidget(self.workflow_area)

        # tlačítko generovat
        self.btn_generate = QPushButton("Vygenerovat pipeline")
        self.btn_generate.clicked.connect(self.generate_pipeline)
        right_layout.addWidget(self.btn_generate)

        right_panel = QWidget()
        right_panel.setLayout(right_layout)

        # ---- Spodní panel: log ----
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)

        # ---- Hlavní rozložení ----
        main_split = QHBoxLayout()
        main_split.addWidget(left_panel, 2)   # poměr velikosti
        main_split.addWidget(right_panel, 3)

        top_panel = QWidget()
        top_panel.setLayout(main_split)

        main_layout = QVBoxLayout()
        main_layout.addWidget(top_panel, 5)
        main_layout.addWidget(QLabel("Log"))
        main_layout.addWidget(self.log_area, 2)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def add_module_to_workflow(self, item):
        """Přidá vybraný modul do workflow panelu"""
        self.workflow_area.addItem(item.text())
        self.log(f"Modul {item.text()} přidán do workflow")

    def generate_pipeline(self):
        """Zatím jen logovací funkce"""
        modules = [self.workflow_area.item(i).text() for i in range(self.workflow_area.count())]
        self.log(f"Pipeline by obsahovala: {', '.join(modules)}")

    def log(self, message: str):
        """Vypíše zprávu do log panelu"""
        self.log_area.append(message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
