'''
Created on Jun 26, 2015

@author: qurban.ali
'''
from uiContainer import uic
from PyQt4.QtGui import QMessageBox, QFileDialog, qApp
import os.path as osp
import qtify_maya_window as qtfy
import msgBox
import backend
reload(backend)

rcUtils = backend.rcUtils

rootPath = osp.dirname(osp.dirname(__file__))
uiPath = osp.join(rootPath, 'ui')

Form, Base = uic.loadUiType(osp.join(uiPath, 'main.ui'))
class RenderCheckUI(Form, Base):
    '''
    Takes input from the user for scene creation
    '''
    def __init__(self, parent=qtfy.getMayaWindow()):
        super(RenderCheckUI, self).__init__(parent)
        self.setupUi(self)
        
        self.dataCollector = None
        self.sceneMaker = None
        self.deadlineSubmitter = None
        
        self.progressBar.hide()
        self.stopButton.hide()
        
        self.startButton.clicked.connect(self.start)
        self.browseButton1.clicked.connect(self.setAnimationFilePath)
        self.browseButton2.clicked.connect(self.setCSVFilePath)
        self.stopButton.clicked.connect(self.stop)
        
    def closeEvent(self, event):
        self.deleteLater()
        
    def processEvents(self):
        qApp.processEvents()
        
    def stop(self):
        if self.dataCollector:
            del self.dataCollector
            self.dataCollector = None
        if self.sceneMaker:
            del self.sceneMaker
            self.sceneMaker = None
        if self.deadlineSubmitter:
            del self.deadlineSubmitter
            self.deadlineSubmitter = None
        
    def start(self):
        pass
    
    def setAnimationFilePath(self):
        filename = QFileDialog.getOpenFileName(self, 'Select File', '', '*.ma *.mb')
        if filename:
            self.animFilePathBox.setText(filename)
    
    def setCSVFilePath(self):
        filename = QFileDialog.getOpenFileName(self, 'Select File', '', '*.csv')
        if filename:
            self.csvFilePathBox.setText(filename)
    
    def getAnimationFilePath(self):
        path = self.animFilePathBox.text()
        if not osp.exists(path):
            self.showMessage(msg='Animation file path does not exist',
                             icon=QMessageBox.Information)
            path = ''
        return path
    
    def getCSVFilePath(self):
        path = self.csvFilePathBox.text()
        if not osp.exists(path):
            self.showMessage(msg='CSV file path does not exist',
                             icon=QMessageBox.Information)
            path = ''
        return path
    
    def appendStatus(self, msg):
        self.statusBox.append(msg)
        self.processEvents()
        
    def showProgressBar(self):
        self.progressBar.show()
        self.progressBar.setValue(0)
        self.processEvents()
        
    def pbSetMax(self, val):
        self.progressBar.setMaximum(val)
    
    def pbSetMin(self, val):
        self.progressBar.setMinimum(val)
        
    def updateProgressBar(self, val):
        self.progressBar.setValue(val)
        self.processEvents()
    
    def hideProgressBar(self):
        self.progressBar.hide()
        self.progressBar.setValue(0)
        self.processEvents()
    
    def clearStatusBox(self):
        self.statusBox.clear()
    
    def showMessage(self, **kwargs):
        return msgBox.showMessage(self, title='Render Check', **kwargs)