import logging
import logging.config

from os import startfile, path

import PyQt5.QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QTextCursor

from helper_functions import load_novels_list, get_site_domain, get_novel_path

from classes import Novel

logging.config.fileConfig(fname='log.conf')
logger = logging.getLogger(__name__)


class NewNovelWorker(PyQt5.QtCore.QRunnable):
    log = PyQt5.QtCore.pyqtSignal(str)

    def __init__(self, name, link, app):
        super(NewNovelWorker, self).__init__()
        self.novelName = name
        self.novelLink = link
        self.app = app

    @PyQt5.QtCore.pyqtSlot()
    def run(self):
        if self.novelLink and self.novelName:
            novel = Novel(self.novelName, link=self.novelLink)
            novel.initialize()
            novel.save()
        else:
            print(None, None)

        self.app.novelsList.reload()
        self.app.enable()


class UpdateNovelWorker(PyQt5.QtCore.QRunnable):
    log = PyQt5.QtCore.pyqtSignal(str)

    def __init__(self, name, app):
        super(UpdateNovelWorker, self).__init__()
        self.novelName = name
        self.app = app

    @PyQt5.QtCore.pyqtSlot()
    def run(self):
        global app
        novel = Novel(self.novelName, load=True)
        novel.initialize()
        novel.update()
        novel.save()

        self.app.novelsList.reload()
        self.app.enable()


class ExportNovelWorker(PyQt5.QtCore.QRunnable):
    log = PyQt5.QtCore.pyqtSignal(str)

    def __init__(self, name, app):
        super(ExportNovelWorker, self).__init__()
        self.novelName = name
        self.app = app

    @PyQt5.QtCore.pyqtSlot()
    def run(self):
        global app
        novel = Novel(self.novelName, load=True)
        novel.initialize()
        novel.export_as_html()
        novel.export_as_pdf()
        novel.export_as_pdf(dark_mode=True)

        self.app.novelsList.reload()
        self.app.enable()


class LogText(QPlainTextEdit):
    def __init__(self):
        super(QPlainTextEdit, self).__init__()

    def addLine(self, line):
        self.appendPlainText(line)
        self.moveCursor(QTextCursor.End)


class Log(logging.Handler):
    def __init__(self):
        super().__init__()
        # For Debugging
        # format = "[%(levelname)s][%(threadName)s][%(asctime)s]: %(message)s"
        format = "[%(levelname)s][%(asctime)s]: %(message)s"

        self.formatter = logging.Formatter(format)

        self.widget = LogText()
        self.widget.setStyleSheet("background-color:white;")
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.widget.addLine(msg)

    def write(self, m):
        pass


class TextInput(QWidget):
    def __init__(self, header):
        super(QWidget, self).__init__()
        self.setFixedSize(325, 25)

        self.label = QLabel(header, self)
        self.label.setFixedSize(50, 25)

        self.textField = QLineEdit(self)
        self.textField.setFixedSize(
            self.width() - self.label.width(), 25)
        self.textField.move(self.label.width(), 0)

        self.text = self.textField.text


class NewNovelDialog(QDialog):
    def __init__(self, parent):
        super(NewNovelDialog, self).__init__(parent)
        self.setParent(parent)
        self.setWindowTitle("Add new novel")

        self.vLayout = QVBoxLayout(self)
        self.setLayout(self.vLayout)

        self.nameField = TextInput('Name')
        self.vLayout.addWidget(self.nameField)

        self.linkField = TextInput('Link')
        self.vLayout.addWidget(self.linkField)

        self.okButton = QPushButton("Add", self)
        self.okButton.clicked.connect(self.accept)
        self.vLayout.addWidget(self.okButton)

        self.cancelButton = QPushButton("Cancel", self)
        self.cancelButton.clicked.connect(self.close)
        self.vLayout.addWidget(self.cancelButton)

        self.setFixedSize(self.vLayout.sizeHint())

    def getResults(self):
        if self.exec_() == QDialog.Accepted:
            name = self.nameField.text()
            link = self.linkField.text()
            if name and link:
                return name, link
            else:
                return None, None
        else:
            return None, None


class NovelsList(QListWidget):
    def __init__(self):
        super(QListWidget, self).__init__()
        self.setStyleSheet("QListView::item{height: 20px}")
        self.setFixedSize(600, 300)

        self.reload()

    def reload(self):
        self.novels_names = list(load_novels_list().keys())
        if (len(self.children()) < len(self.novels_names) or
           not self.children() == []):
            self.clear()
            for name in self.novels_names:
                self.insertItem(-1, name)
        logger.info("Novels list reloaded")


class ButtonsBox(QWidget):
    def __init__(self):
        super(QWidget, self).__init__()

        self.newNovelButton = QPushButton("Create New Novel")
        self.newNovelButton.setFixedHeight(50)

        self.updateButton = QPushButton("Update Selected Novel")
        self.updateButton.setFixedHeight(50)
        self.updateButton.setDisabled(True)

        self.exportButton = QPushButton("Export Selected Novel")
        self.exportButton.setFixedHeight(50)
        self.exportButton.setDisabled(True)

        self.vLayout = QVBoxLayout()
        self.vLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.vLayout)

        self.vLayout.addWidget(self.newNovelButton)
        self.vLayout.addWidget(self.updateButton)
        self.vLayout.addWidget(self.exportButton)


class InfoBox(QScrollArea):
    def __init__(self):
        super(QScrollArea, self).__init__()
        self.setStyleSheet("QLabel{font-size: 16px;}")

        self.name = ""
        self.url = ""

        self.vLayout = QVBoxLayout()
        self.vLayout.setAlignment(PyQt5.QtCore.Qt.AlignTop)
        self.setLayout(self.vLayout)

        self.nameLabel = QLabel()
        self.nameLabel.setContentsMargins(0, 0, 0, 10)
        self.nameLabel.setMaximumWidth(self.maximumWidth())
        self.nameLabel.setProperty('wordWrap', True)
        self.vLayout.addWidget(self.nameLabel)

        self.linkLabel = QLabel()
        self.linkLabel.setContentsMargins(0, 0, 0, 10)
        self.linkLabel.setOpenExternalLinks(True)
        self.vLayout.addWidget(self.linkLabel)

        self.openNovelDir = QPushButton("Open Folder")
        self.vLayout.addWidget(self.openNovelDir)

        self.openExportsDir = QPushButton("Open Exports Folder")
        self.vLayout.addWidget(self.openExportsDir)

    def showInfo(self, name, url):
        self.name = name
        self.path = get_novel_path(name)
        self.nameLabel.setText(name)

        self.url = url
        link = f"Link: <a href=\"{url}\">{get_site_domain(url)}</a>"
        self.linkLabel.setText(link)

        novelFolder = get_novel_path(self.name)
        self.openNovelDir.clicked.connect(lambda x: startfile(novelFolder))

        exportsPath = path.join(novelFolder, 'Exports')
        self.openExportsDir.clicked.connect(lambda x: startfile(exportsPath))


class BottomArea(QWidget):
    def __init__(self):
        super(QWidget, self).__init__()

        self.grid = QGridLayout()
        self.setLayout(self.grid)

        self.buttonsBox = ButtonsBox()
        self.grid.addWidget(self.buttonsBox, 0, 0, 1, 1)

        self.infoBox = InfoBox()
        self.grid.addWidget(self.infoBox, 0, 1, 1, 3)
        self.infoBox.setHidden(True)

    #    self.log = Log()
    #    self.grid.addWidget(self.log.widget, 1, 0, 2, 4)


class App(QWidget):
    def __init__(self):
        super(QWidget, self).__init__()
        self.setWindowTitle("Web Novels Reader")
        self.setFixedSize(620, 600)

        self.threadPool = PyQt5.QtCore.QThreadPool()

        self.vLayout = QVBoxLayout()
        self.vLayout.setContentsMargins(10, 10, 0, 0)
        self.setLayout(self.vLayout)

        self.novelsList = NovelsList()
        self.novelsList.itemClicked.connect(lambda x: self.novelSelected(x))
        self.vLayout.addWidget(self.novelsList)

        self.bottomArea = BottomArea()
        self.vLayout.addWidget(self.bottomArea)

        self.buttonsBox = self.bottomArea.buttonsBox

        self.newNovelButton = self.buttonsBox.newNovelButton
        self.newNovelButton.clicked.connect(self.addNovel)

        self.updateButton = self.buttonsBox.updateButton
        self.updateButton.clicked.connect(self.updateNovel)

        self.exportButton = self.buttonsBox.exportButton
        self.exportButton.clicked.connect(self.exportNovel)

        self.infoBox = self.bottomArea.infoBox

    #    self.log = self.bottomArea.log

    def novelSelected(self, selectedItem):
        self.buttonsBox.updateButton.setDisabled(False)
        self.buttonsBox.exportButton.setDisabled(False)
        self.infoBox.setHidden(False)

        novels_list = load_novels_list()
        name = selectedItem.text()
        link = novels_list[name]
        self.infoBox.showInfo(name, link)

    def addNovel(self):
        newNovelDialog = NewNovelDialog(self)
        name, link = newNovelDialog.getResults()

        newNovelWorker = NewNovelWorker(name, link, self)
        self.threadPool.start(newNovelWorker)

        self.disable()

    def updateNovel(self):
        name = self.novelsList.selectedItems()[0].text()
        updateNovelWorker = UpdateNovelWorker(name, self)
        self.threadPool.start(updateNovelWorker)

        self.disable()

    def exportNovel(self):
        name = self.novelsList.selectedItems()[0].text()
        exportNovelWorker = ExportNovelWorker(name, self)
        self.threadPool.start(exportNovelWorker)

        self.disable()

    def disable(self):
        self.buttonsBox.setDisabled(True)
        self.novelsList.setDisabled(True)

    def enable(self):
        self.buttonsBox.setDisabled(False)
        self.novelsList.setDisabled(False)
