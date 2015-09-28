import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.button = QPushButton("cliquez")

        self.main_window_init()

    def main_window_init(self):
        # le signal connecte le clickage du bouton à la fonction button_clicked
        self.button.clicked.connect(self.button_clicked)
        self.setCentralWidget(self.button)

        self.show()

    def button_clicked(self):
        print("bouton cliqué !")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())
