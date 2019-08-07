import fileinput
import sys

from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QMainWindow, QPushButton, \
    QGridLayout, QGroupBox
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot, Qt
from pathlib import Path


def process_file(file):
    for line in fileinput.FileInput(str(file), inplace=True):
        if "BORDER_" in line or "VBORE_" in line or "ROUTE_" in line:
            if 'BORDER' in line:
                print('BORDER')
                continue
            i = line.rfind('T')

            if i > -1:
                if line[i - 1] == "L" or line[i - 1] == "R":
                    offset = line[i - 1] + 'T'
                    p = line.rpartition(offset)
                else:
                    offset = 'T'
                    p = line.rpartition('T')
                tool = '_' + offset + p[2].rstrip()
                layer = p[0]
            else:
                layer = line
                tool = ''

            p = layer.partition('_')
            operation = p[0]
            depth = p[2].replace('P', '.').rstrip()
            print("{}{}_{}".format(operation, tool, depth))
        else:
            print(line, end='')


class scanFiles(QThread):
    updated = pyqtSignal(str)

    def __init__(self, force=False):
        QThread.__init__(self)
        self.force = force

    def run(self):
        self.scanDirectory(self.force)

    def scanDirectory(self, force=False):
        self.updated.emit("Scanning for DXF files on server...{}".format(
            "\n\nProcessing all files even if already fixed!" if force else ""))
        path = Path("M:\\", "Homestead_Library", "Work Orders")
        dirs = list(path.glob("**/dxf/"))
        self.updated.emit("Folder scan finished!\nScanning files...")

        for d in list(dirs):
            self.updated.emit(str(d))
            if not Path(d, '.fixed').is_file() or force is True:
                files = list(d.glob("**/*.dxf"))
                for file in files:
                    self.updated.emit(str(file))
                    process_file(file)

                Path(d, '.fixed').touch()


class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.title = "Brad's DXF Fixer"
        self.width = 440
        self.height = 240
        self.centralWidget = QWidget(self)
        self.setCentralWidget(self.centralWidget)
        self.update_thread = scanFiles()
        self.update_thread.updated.connect(self.update)
        self.update_thread.finished.connect(self.scanDone)
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.resize(self.width, self.height)
        self.setFixedWidth(self.width)

        self.pleaseWait = QLabel()
        self.pleaseWait.setWordWrap(True)
        self.pleaseWait.setObjectName("Beans")
        self.pleaseWait.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        self.closeBtn = QPushButton("Close")
        self.closeBtn.clicked.connect(self.close)
        self.forceBtn = QPushButton("Reprocess ALL files")
        self.forceBtn.setToolTip("Files that have already been processed will normally be" \
            + " skipped.\nThis button will force everything to be processed again!")
        self.forceBtn.clicked.connect(self.forceScan)

        self.windowLayout = QVBoxLayout()
        self.windowLayout.addWidget(self.pleaseWait)
        self.centralWidget.setLayout(self.windowLayout)
        self.show()
        self.update_thread.start()

    @pyqtSlot(str, name="text")
    def update(self, text):
        self.pleaseWait.setText(text)

    @pyqtSlot()
    def scanDone(self):
        self.pleaseWait.setText("Files have been fixed!\nYou can close this now.")
        # self.windowLayout.removeWidget(self.pleaseWait)
        self.forceBtn.setEnabled(True)
        self.windowLayout.addWidget(self.forceBtn)
        self.windowLayout.addWidget(self.closeBtn)

    @pyqtSlot()
    def forceScan(self):
        self.forceBtn.setEnabled(False)
        self.force_update_thread = scanFiles(force=True)
        self.force_update_thread.updated.connect(self.update)
        self.force_update_thread.finished.connect(self.scanDone)
        self.force_update_thread.start()




if __name__ == '__main__':
    appctxt = ApplicationContext()
    stylesheet = appctxt.get_resource('styles.qss')
    appctxt.app.setStyleSheet(open(stylesheet).read())
    ex = App()
    exit_code = appctxt.app.exec_()
    sys.exit(exit_code)
