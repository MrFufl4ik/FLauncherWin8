import sys
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow
from window_main import Ui_MainWindow as Ui_MainWindow


class FLauncherWindow(QMainWindow):
    def __init__(self):
        super(FLauncherWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)


if __name__ == '__main__':
     app = QApplication(sys.argv)

     window = FLauncherWindow()
     window.show()

     sys.exit(app.exec_())
