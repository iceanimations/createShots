'''
Created on Jun 26, 2015

@author: qurban.ali
'''
from uiContainer import uic
from PyQt4.QtGui import QMessageBox, QFileDialog, QPushButton, QCheckBox, qApp
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
import appUsageApp
reload(appUsageApp)
import mayaStartup
reload(mayaStartup)
import pymel.core as pc
from collections import OrderedDict
import sys
import imaya
reload(imaya)
from pprint import pprint

rcUtils = backend.rcUtils

renderShotsBackend = osp.join(qutil.dirname(__file__, 3), 'renderShots', 'src', 'backend')
sys.path.insert(0, renderShotsBackend)

compositingDir = osp.join(osp.expanduser('~'), 'compositing')
if not osp.exists(compositingDir):
    os.mkdir(compositingDir)
    
nukePath = r"C:\Program Files\Nuke8.0v5\python.exe"
if not osp.exists(nukePath):
    nukePath = r"C:\Program Files\Nuke8.0v3\python.exe"
    if not osp.exists(nukePath):
        nukePath = r"C:\Program Files\Nuke9.0v4\python.exe"

rootPath = qutil.dirname(__file__, depth=2)
uiPath = osp.join(rootPath, 'ui')

# option var keys
shotsPath_key = 'createShots_shotsPath_key'
resolution_key = 'createShts_resolution_key'

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
        self.lastPath = ''

        self.stopButton.hide()
        self.saveToLocalButton.hide()
        self.label_3.hide()
        self.outputPathBox.hide()
        self.browseButton1.hide()
        self.useRendersButton.hide()
        self.resolutionBox.hide()
        
        self.shotsBox = cui.MultiSelectComboBox(self, msg='--Select Shots--')
        self.shotsLayout.addWidget(self.shotsBox)
        
        self.resolutions = OrderedDict()
        self.resolutions['320x240'] = [320, 240, 1.333]
        self.resolutions['640x480'] = [640, 480, 1.333]
        self.resolutions['960x540'] = [960, 540, 1.777]
        self.resolutions['1280x720'] = [1280, 720, 1.777]
        self.resolutions['1920x1080'] = [1920, 1080, 1.777]
        
        self.startButton.clicked.connect(self.start)
        self.browseButton2.clicked.connect(self.setShotsFilePath)
        self.browseButton.clicked.connect(self.setCSVFilePath)
        self.stopButton.clicked.connect(self.stop)
        self.shotsFilePathBox.textChanged.connect(self.populateShots)
        self.browseButton1.clicked.connect(self.setOutputPath)
        self.createFilesButton.toggled.connect(lambda val: self.saveToLocalButton.setChecked(False))
        self.resolutionBox.activated.connect(self.resolutionBoxActivated)
        self.createCollageButton.toggled.connect(lambda: self.useRendersButton.setChecked(False))
        
        
        self.setupWindow()

        appUsageApp.updateDatabase('createShots')
        
    def resolutionBoxActivated(self):
        qutil.addOptionVar(resolution_key, self.resolutionBox.currentText())
        
    def getResolution(self):
        return self.resolutions[self.resolutionBox.currentText()]
        
    def setupWindow(self):
        # setup the resolution box
        self.resolutionBox.addItems(self.resolutions.keys())
        val = qutil.getOptionVar(resolution_key)
        if val:
            for i in range(self.resolutionBox.count()):
                text = self.resolutionBox.itemText(i)
                if text == val:
                    self.resolutionBox.setCurrentIndex(i)
                    break
        # setup the shots path
        path = qutil.getOptionVar(shotsPath_key)
        if path:
            self.shotsFilePathBox.setText(path)
            self.lastPath = path
        
    def createFiles(self):
        return self.createFilesButton.isChecked()
        
    def setOutputPath(self):
        filename = QFileDialog.getExistingDirectory(self, 'Select File', '', QFileDialog.ShowDirsOnly)
        if filename:
            self.outputPathBox.setText(filename)
        
    def getOutputPath(self, msg=True):
        path = self.outputPathBox.text()
        if path:
            if osp.exists(path):
                return path
            else:
                self.showMessage(msg='Could not find the output path',
                                 icon=QMessageBox.Information)
        else:
            if msg:
                self.showMessage(msg='Output path not specified',
                                 icon=QMessageBox.Information)
    
    def isRender(self):
        return self.useRendersButton.isChecked()
        
    def isShotNameValid(self, name):
        parts = name.split('_')
        if len(parts) == 2:
            if re.match('SQ\\d{3}', parts[0]) and re.match('SH\\d{3}', parts[1]):
                return True
            
    def createCollage(self):
        return self.createCollageButton.isChecked()
        
    def populateShots(self, path):
        if path:
            if osp.exists(path):
                qutil.addOptionVar(shotsPath_key, path)
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
            
    def isLocal(self):
        return self.saveToLocalButton.isChecked()

    def start(self):
        try:
            if self.isRender():
                if not osp.exists(nukePath):
                    self.showMessage(msg='It seems like Nuke is not installed on this system, comps will not be created',
                                     icon=QMessageBox.Warning)
                    return
            geoSets = imaya.getGeoSets()
            if geoSets:
                geoLen = len(geoSets)
                if geoLen > 1:
                    s = 's'
                    ss = 'them'
                else:
                    s = ''
                    ss = 'it'
                
                btn = self.showMessage(msg='%s Geometry Set%s found in the scene'%(geoLen, s),
                                       ques='Do you want to combine and add %s to characters group?'%ss,
                                       icon=QMessageBox.Question,
                                       btns=QMessageBox.Yes|QMessageBox.No)
                if btn == QMessageBox.Yes:
                    sb = cui.SelectionBox(self, [QCheckBox(s.name(), self) for s in geoSets], msg='Select sets')
                    sb.setCancelToolTip('Skip adding Geometry sets to characters group')
                    if not sb.exec_():
                        geoSets = [pc.PyNode(s) for s in sb.getSelectedItems()]
                        meshes = []
                        for s in geoSets:
                            mesh = imaya.getCombinedMeshFromSet(s)
                            if not mesh:
                                self.appendStatus('Warning: Could not combine %s'%s)
                                continue
                            meshes.append(mesh)
                        if meshes:
                            imaya.addMeshesToGroup(meshes, 'characters')
            mayaStartup.FPSDialog(self).exec_()
            self.statusBox.clear()
            shotsFilePath = self.getShotsFilePath()
            if self.isLocal():
                if not self.getOutputPath():
                    return
            if len([x for x in pc.ls(type='camera') if not x.orthographic.get()]) > 1:
                btn = self.showMessage(msg='Extra cameras found in the scene',
                                                 ques='Do you want to continue?',
                                                 btns=QMessageBox.Yes|QMessageBox.No,
                                                 icon = QMessageBox.Question)
                if btn == QMessageBox.No:
                    return
            if self.isRender():
                layers = [layer for layer in imaya.getRenderLayers() if not layer.name().lower().startswith('default')]
                if not layers:
                    self.showMessage(msg='No renderable layer found. If you want to render "masterLayer", copy it and name it as "Env" or "Char"',
                                     icon=QMessageBox.Information)
                    return
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
                if self.isRender():
                    scene.collage = self.createCollageFromRenders()
                self.appendStatus('DONE...')
                if self.createCollage():
                    if scene.collage:
                        ep = re.search('EP\d+', self.getShotsFilePath(), re.IGNORECASE).group()
                        sq = re.search('SQ\d+', self.getShotsFilePath(), re.IGNORECASE).group()
                        name = '_'.join([ep, sq, 'collage']) + osp.splitext(scene.collage)[-1]
                        name = osp.join(osp.dirname(scene.collage), name).replace('\\', '/')
                        os.rename(scene.collage, name)
                        fileButton = QPushButton('Copy File Path')
                        folderButton = QPushButton('Copy Folder Path')
                        btn = self.showMessage(msg='<a href=%s style="color: lightGreen">'%name + name +'</a>',
                                               btns=QMessageBox.Ok,
                                               customButtons=[fileButton, folderButton],
                                               icon=QMessageBox.Information)
                        if btn == fileButton:
                            qApp.clipboard().setText(scene.collage)
                        elif btn == folderButton:
                            qApp.clipboard().setText(osp.dirname(scene.collage))
                        else:
                            pass
        except Exception as ex:
            self.showMessage(msg=str(ex), icon=QMessageBox.Critical)
                
    def createCollageFromRenders(self):
        compositingFile = osp.join(renderShotsBackend, 'compositing.py')
        import collageMaker
        reload(collageMaker)
        import subprocess
        renderDirPath = osp.join(rcUtils.homeDir, 'renders')
        renderDirs = os.listdir(renderDirPath)
        flag = False
        if renderDirs:
            renderDirs = [renderDir for renderDir in renderDirs if osp.isdir(osp.join(renderDirPath, renderDir))]
            for renderDir in renderDirs:
                path = osp.join(renderDirPath, renderDir)
                layerDirs = os.listdir(path)
                if layerDirs:
                    if len(layerDirs) > 1 or not layerDirs[0].lower().startswith('master'):
                        flag = True
            if flag:
                with open(osp.join(compositingDir, 'info.txt'), 'w') as f:
                    f.write(str([False, renderDirPath] + renderDirs))
                self.appendStatus('<b>Creating and rendering comps</b>')
                os.chdir(osp.dirname(nukePath))
                subprocess.call('python %s'%compositingFile, shell=True)
                collageMaker.collageDir = osp.join(rcUtils.homeDir, 'collage')
                if not osp.exists(collageMaker.collageDir):
                    os.mkdir(collageMaker.collageDir)
                collageMaker.compRenderDir = osp.join(renderDirPath, 'comps', 'renders')
                shotLen = len(renderDirs)
                cm = collageMaker.CollageMaker()
                for i, renderDir in enumerate(renderDirs):
                    if osp.isdir(osp.join(renderDirPath, renderDir)) and re.search('SQ\d+_SH\d+', renderDir):
                        self.appendStatus('Creating collage for %s (%s of %s)'%(renderDir, i+1, shotLen))
                        cm.makeShot(renderDir)
                collagePath = cm.make()
                if collagePath and osp.exists(collagePath):
                    return collagePath
        
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
        filename = QFileDialog.getExistingDirectory(self, 'Select File', self.lastPath, QFileDialog.ShowDirsOnly)
        if filename:
            self.shotsFilePathBox.setText(filename)
            self.lastPath = filename

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
    
    def clearStatusBox(self):
        self.statusBox.clear()
    
    def showMessage(self, **kwargs):
        return msgBox.showMessage(self, title='Create Shots', **kwargs)