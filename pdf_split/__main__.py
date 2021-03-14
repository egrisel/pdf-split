import sys
import os
import math
import ctypes

from pathlib import Path
from PyPDF2 import PdfFileReader, PdfFileWriter

from PySide2.QtWidgets import (
    QApplication, QWidget, QGridLayout, QLabel, QPushButton, QFileDialog,
    QMessageBox, QSpinBox, QVBoxLayout
)
from PySide2.QtCore import (
    QRunnable, QThreadPool, Slot, Signal, QObject, Qt, QSize
)

from PySide2.QtGui import QPixmap, QIcon


myappid = 'gwap.pdf-split.1.0.0'
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


class MyEmitter(QObject):
    done = Signal(str)


class SplitFileTask(QRunnable):
    def __init__(self, file, quantity, folder):
        super(SplitFileTask, self).__init__()
        self.file = file
        self.quantity = quantity
        self.folder = folder
        self.emitter = MyEmitter()

    def run(self):
        with open(self.file, 'rb') as f:
            pdf = PdfFileReader(f, strict=False)
            total_pages = pdf.getNumPages()
            pages_per_pdf = math.ceil(total_pages / self.quantity())
            current_pdf = 1
            current_page_in_loop = 0
            file = Path(self.file)
            for page in range(total_pages):
                finished = False
                if current_page_in_loop == 0:
                    pdf_writer = PdfFileWriter()
                pdf_writer.addPage(pdf.getPage(page))
                current_page_in_loop += 1
                if current_page_in_loop == pages_per_pdf:
                    output_filename = f"{file.stem}_{current_pdf}.pdf"
                    full_output_filename = Path(
                        self.folder, output_filename
                    )
                    current_pdf += 1
                    current_page_in_loop = 0
                    with open(full_output_filename, 'wb') as out:
                        pdf_writer.write(out)
                    print(f"Créé : {full_output_filename}")
                    finished = True
            if not finished:
                output_filename = f"{file.stem}_{current_pdf}.pdf"
                full_output_filename = Path(
                    self.folder, output_filename
                )
                with open(full_output_filename, 'wb') as out:
                    pdf_writer.write(out)
                print(f"Créé : {full_output_filename}")
        self.emitter.done.emit(str(file.stem))


class SplitWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PDF Split")
        self.setMinimumWidth(400)
        self.setStyleSheet("background: white;")

        # Icône du programme
        app_icon = QIcon()
        app_icon.addFile('logo_icon_white.png', QSize(64, 64))
        self.setWindowIcon(app_icon)

        # Définit le logo du programme
        image = QPixmap('logo-app.png')
        self.logo_lbl = QLabel()
        self.logo_lbl.setAlignment(Qt.AlignCenter)
        self.logo_lbl.setPixmap(image)
        self.logo_lbl.setStyleSheet("margin: 20px 0;")

        # Variables du programme
        self.folder = str(Path.home())
        self.file_to_split = None
        self.destination_folder = None

        self.main_layout = QVBoxLayout()

        # Label d'introduction
        self.select_lbl = QLabel("Sélectionner un PDF à diviser")
        self.select_lbl.setStyleSheet(
            "font-weight: bold;"
        )

        # Bouton de sélection de fichier
        self.select_btn = QPushButton("Sélectionner")
        self.select_btn.clicked.connect(self.getfile)

        # Label affichant le fichier sélectionné
        self.selected_lbl = QLabel("")
        self.selected_lbl.setStyleSheet(
            "font-style: italic;" +
            "color: gray;"
        )

        # Layout pour la sélection du fichier
        self.select_layout = QGridLayout()
        self.select_layout.addWidget(self.select_btn, 0, 0)
        self.select_layout.addWidget(self.selected_lbl, 0, 1, 1, 2)

        # Nombre de pages
        self.quantity_lbl = QLabel("")
        self.quantity_lbl.setStyleSheet(("margin-top: 20px;"))

        self.quantity_text_lbl = QLabel("Fractionner le PDF en")

        self.quantity = QSpinBox()
        # self.quantity.setStyleSheet(
        #     "margin: 0 10px;"
        # )
        self.quantity.setMaximumWidth(50)
        self.quantity.setMinimum(2)
        self.quantity.setMaximum(2)

        self.split_lbl = QLabel("fichiers")

        # Layout pour le fractionnement du PDF
        self.split_layout = QGridLayout()
        self.split_layout.addWidget(self.quantity_text_lbl, 0, 0)
        self.split_layout.addWidget(self.quantity, 0, 1)
        self.split_layout.addWidget(self.split_lbl, 0, 2)

        # Destination
        self.destination_text_lbl = QLabel("Répertoire de destination")
        self.destination_text_lbl.setStyleSheet(
            "margin-top: 20px;" +
            "font-weight: bold;"
        )

        # Bouton de sélection de la destination
        self.destination_btn = QPushButton("Sélectionner")
        self.destination_btn.clicked.connect(self.getdestination)

        # Label affichant le répertoire de destination
        self.destination_lbl = QLabel("")
        self.destination_lbl.setStyleSheet(
            "font-style: italic;" +
            "color: gray;"
        )

        # Layout  pour la destination
        self.destination_layout = QGridLayout()
        self.destination_layout.addWidget(self.destination_btn, 0, 0)
        self.destination_layout.addWidget(self.destination_lbl, 0, 1, 1, 2)

        # Fractionnement
        self.split_lbl = QLabel("")
        self.btn_split = QPushButton("Fractionner le PDF")
        self.btn_split.setEnabled(False)
        self.btn_split.clicked.connect(self.split_file)

        # Applique le layout final
        self.main_layout.addWidget(self.logo_lbl)
        self.main_layout.addWidget(self.select_lbl)
        self.main_layout.addLayout(self.select_layout)
        self.main_layout.addWidget(self.quantity_lbl)
        self.main_layout.addLayout(self.split_layout)
        self.main_layout.addWidget(self.destination_text_lbl)
        self.main_layout.addLayout(self.destination_layout)
        self.main_layout.addWidget(self.split_lbl)
        self.main_layout.addWidget(self.btn_split)
        self.setLayout((self.main_layout))

        self.pool = QThreadPool()

    def getfile(self):
        fileName = QFileDialog.getOpenFileName(
            self, "Sélectionner un PDF", self.folder, "Fichiers PDF (*.pdf)"
        )
        file = Path(fileName[0])
        with open(fileName[0], 'rb') as f:
            pdf = PdfFileReader(f, strict=False)
            if pdf.getNumPages() < 2:
                dlg = QMessageBox(self)
                dlg.setWindowTitle("Error")
                dlg.setText("Votre PDF n'a qu'une page.")
                dlg.exec_()
                return
            # Affiche le nombre de page du PDF choisi
            self.quantity_lbl.setText(
                "Le fichier sélectionné fait " +
                f"<b>{pdf.getNumPages()}</b> pages."
            )

            self.quantity.setMaximum(pdf.getNumPages())
        # Affiche le nom du fichier sélectionné
        self.selected_lbl.setText(file.name)
        # file name without extension : file.stem
        # Récupère le chemin du fichier sélectionné
        self.folder = os.path.dirname(fileName[0])
        self.file_to_split = fileName[0]
        self.check_btn_split()

    def getdestination(self):
        if self.destination_folder:
            folder = self.destination_folder
        else:
            folder = self.folder
        directory = str(
            QFileDialog.getExistingDirectory(
                self, "Répertoire de destination", folder
            )
        )
        self.destination_folder = directory
        self.destination_lbl.setText(directory)
        self.check_btn_split()
        return

    def check_btn_split(self):
        if self.file_to_split is not None and\
                self.destination_folder is not None:
            self.btn_split.setEnabled(True)
        else:
            self.btn_split.setEnabled(False)

    def split_file(self):
        # On désactive les boutons
        self.select_btn.setEnabled(False)
        self.destination_btn.setEnabled(False)
        self.btn_split.setEnabled(False)
        self.btn_split.setText("Fractionnement en cours...")

        worker = SplitFileTask(
            self.file_to_split,
            self.quantity.value,
            self.destination_folder
        )
        worker.emitter.done.connect(self.on_worker_done)
        self.pool.start(worker)

    @Slot(str)
    def on_worker_done(self, worker):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Fractionnement terminé !")
        dlg.setText("Votre fichier a été fractionné.")
        dlg.exec_()

        self.select_btn.setEnabled(True)
        self.destination_btn.setEnabled(True)
        self.btn_split.setEnabled(True)
        self.btn_split.setText("Fractionner le PDF")


def main():
    app = QApplication()
    window = SplitWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
