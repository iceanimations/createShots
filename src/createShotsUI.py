'''
Created on Jun 26, 2015

@author: qurban.ali
'''
from uiContainer import uic
from PyQt4.QtGui import QMessageBox, QFileDialog, QPushButton, qApp
import os.path as osp
import qtify_maya_window as qtfy
import msgBox
import backend
reload(backend)
import qutil
reload(qutil)
import os
import re
import cui
reload(cui)
import mappingUI as mUI
reload(mUI)
import pprint
import appUsageApp
reload(appUsageApp)
import mayaStartup
reload(mayaStartup)

rcUtils = backend.rcUtils

rootPath = qutil.dirname(__file__, depth=2)
uiPath = osp.join(rootPath, 'ui')

Form, Base = uic.loadUiType(osp.join(uiPath, 'main.ui'))
class CreateShotsUI(Form, Base):
    '''
    Takes input from the user for scene creation
    '''
    def __init__(self, parent=qtfy.getMayaWindow()):
        super(CreateShotsUI, self).__init__(parent)
        self.setupUi(self)
        
        self.dataCollector = None
        self.sceneMaker = None
        self.deadlineSubmitter = None
        
        self.progressBar.hide()
        self.stopButton.hide()
        self.hideDetailsButton.hide()
        self.showDetailsButton.hide()
        
        self.shotsBox = cui.MultiSelectComboBox(self, msg='--Select Shots--')
        self.shotsLayout.addWidget(self.shotsBox)
        
        self.startButton.clicked.connect(self.start)
        self.browseButton2.clicked.connect(self.setShotsFilePath)
        self.browseButton.clicked.connect(self.setCSVFilePath)
        self.stopButton.clicked.connect(self.stop)
        self.shotsFilePathBox.textChanged.connect(self.populateShots)

        appUsageApp.updateDatabase('createShots')
        
    def isShotNameValid(self, name):
        parts = name.split('_')
        if len(parts) == 2:
            if re.match('SQ\\d{3}', parts[0]) and re.match('SH\\d{3}', parts[1]):
                return True
            
    def isCollageOnly(self):
        return self.collageOnlyButton.isChecked()
        
    def populateShots(self, path):
        if path:
            if osp.exists(path):
                files = os.listdir(path)
                if files:
                    goodFiles = []
                    for phile in files:
                        if not self.isShotNameValid(phile):
                            continue
                        goodFiles.append(phile)
                    self.shotsBox.addItems(goodFiles)
                    return
        self.shotsBox.clearItems()

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
        mayaStartup.FPSDialog(self).exec_()
        self.statusBox.clear()
        shotsFilePath = self.getShotsFilePath()
        if shotsFilePath:
            selectedShots = self.shotsBox.getSelectedItems()
            if not selectedShots:
                selectedShots = self.shotsBox.getItems()
            data = backend.DataCollector(shotsFilePath, self.getCSVFilePath(), selectedShots, parentWin=self).collect()
            mappingUI = mUI.MappingUI(self, data).populate()
            if mappingUI.exec_():
                mappings = mappingUI.getMappings()
                renderLayers = mappingUI.getRenderLayers()
                envLayerSettings = mappingUI.getEnvLayerSettings()
            else:
                return
            for key, value in mappings.items():
                data.cacheLDMappings[key][0] = value
            data.renderLayers = renderLayers
            data.envLayerSettings = envLayerSettings
            scene = backend.SceneMaker(data, parentWin=self).make()
            fileButton = QPushButton('Copy File Path')
            folderButton = QPushButton('Copy Folder Path')
            btn = self.showMessage(msg='<a href=%s style="color: lightGreen">'%scene.collage.replace('\\', '/') + scene.collage +'</a>',
                                   btns=QMessageBox.Ok,
                                   customButtons=[fileButton, folderButton],
                                   icon=QMessageBox.Information)
            if btn == fileButton:
                qApp.clipboard().setText(scene.collage)
            elif btn == folderButton:
                qApp.clipboard().setText(osp.dirname(scene.collage))
            else:
                pass
        self.appendStatus('DONE...')
        
    def setCSVFilePath(self):
        filename = QFileDialog.getOpenFileName(self, 'Select File', '', '*.csv')
        if filename:
            self.csvFilePathBox.setText(filename)
    
    def getCSVFilePath(self):
        path = self.csvFilePathBox.text()
        if not osp.exists(path):
            self.appendStatus('Warning: Could not find csv file')
            path = ''
        return path

    def setShotsFilePath(self):
        filename = QFileDialog.getExistingDirectory(self, 'Select File', '', QFileDialog.ShowDirsOnly)
        if filename:
            self.shotsFilePathBox.setText(filename)

    def getShotsFilePath(self):
        path = self.shotsFilePathBox.text()
        if not osp.exists(path):
            self.showMessage(msg='Shots path does not exist',
                             icon=QMessageBox.Information)
            path = ''
        return path

    def appendStatus(self, msg):
        if 'Warning:' in msg:
            msg = '<span style="color: orange;">'+ msg.replace('Warning:', '<b>Warning:</b>') + '<span>'
        self.statusBox.append(msg)
        self.processEvents()
        
    def setStatus(self, msg):
        self.statusLabel.setText(msg)
        self.processEvents()
        
    def showProgressBar(self):
        self.progressBar.show()
        self.progressBar.setValue(0)
        self.pbSetMin(0)
        self.statusBox.setFocus()
        self.processEvents()
        
    def pbSetMax(self, val):
        self.progressBar.setMaximum(val)
    
    def pbSetMin(self, val):
        self.progressBar.setMinimum(val)
        
    def pbSetVal(self, val):
        self.progressBar.setValue(val)
        self.processEvents()
    
    def hideProgressBar(self):
        self.progressBar.hide()
        self.progressBar.setValue(0)
        self.processEvents()
    
    def clearStatusBox(self):
        self.statusBox.clear()
    
    def showMessage(self, **kwargs):
        return msgBox.showMessage(self, title='Create Shots', **kwargs)