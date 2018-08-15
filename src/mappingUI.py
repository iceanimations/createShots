'''
Created on Jul 17, 2015

@author: qurban.ali
'''
from uiContainer import uic
from PyQt4.QtGui import QMessageBox, QFileDialog, QPushButton, qApp, QPixmap, QRadioButton
from PyQt4.QtCore import Qt
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
import pymel.core as pc
import backend.rcUtils as rcUtils
reload(rcUtils)
from collections import OrderedDict
import pprint
import imaya
reload(imaya)

rootPath = qutil.dirname(__file__, depth=2)
uiPath = osp.join(rootPath, 'ui')
iconPath = osp.join(rootPath, 'icons')

Form, Base = uic.loadUiType(osp.join(uiPath, 'mappings.ui'))
class MappingUI(Form, Base):
    '''
    Takes input from the user to map cache -> LD for scene creation
    '''
    def __init__(self, parent=None, data=None):
        super(MappingUI, self).__init__(parent)
        self.setupUi(self)
        self.setWindowModality(Qt.NonModal);
        self.setModal(False)
        self.parentWin = parent
        self.data = data
        self.mappings = OrderedDict()
        for key in sorted(data.cacheLDMappings):
            self.mappings[key] = data.cacheLDMappings[key]
        self.items = []
        self.lastPath = ''
        
        self.okButton.clicked.connect(lambda: self.accept())
        self.cancelButton.clicked.connect(lambda: self.reject())
        
    def updateUI(self, msg):
        if self.parentWin:
            self.parentWin.appendStatus(msg)
        
    def isToggleAll(self):
        return self.toggleAllButton.isChecked()
        
    def activated(self, cache, ld):
        if self.isToggleAll():
            for item in self.items:
                for itm in item.getItems():
                    if osp.basename(itm.getCache()).lower() == osp.basename(cache).lower():
                        itm.setLDs(ld, add=False)
                        
    def showFileName(self, filePath, cache):
        if self.isToggleAll():
            for item in self.items:
                for itm in item.getItems():
                    if osp.basename(itm.getCache()).lower() == osp.basename(cache).lower():
                        itm.filePath = filePath
                        itm.fileLabel.show()
                        itm.removeLabel.show()
                        itm.ldBox.hide()
                        itm.fileLabel.setText(osp.basename(filePath))
                        itm.setToolTip(osp.normpath(filePath))
    
    def hideFileName(self, cache):
        if self.isToggleAll():
            for item in self.items:
                for itm in item.getItems():
                    if osp.basename(itm.getCache()).lower() == osp.basename(cache).lower():
                        itm.filePath = None
                        itm.removeLabel.hide()
                        itm.fileLabel.hide()
                        itm.fileLabel.setText('')
                        itm.ldBox.show()
                        
    def getEnvStartEnd(self):
        _, start, end = rcUtils.getEnvLayerStartEnd()
        return start, end
        
    def populate(self):
        start, end = self.getEnvStartEnd()
        if self.mappings:
            lds = self.data.meshes
            for key, value in self.mappings.items():
                item = Item(self, value[0], lds, start, end).update()
                item.setTitle(key +' ('+ str(len(item.getItems())) +')')
                self.items.append(item)
                self.itemLayout.addWidget(item)
        return self
    
    def addRefs(self):
        self.updateUI('Adding references')
        mapping = {} # how many times a file is added to each item in the mappings ui
        for item in self.items:
            mapping[item] = {}
            for itm in item.getItems():
                if itm.filePath:
                    path = rcUtils.getNicePath(itm.filePath)
                    if mapping[item].has_key(path):
                        mapping[item][path] += 1
                    else:
                        mapping[item][path] = 1
        paths = {} # how many times a path should be referenced according to the mappings ui
        for key, value in mapping.items():
            for path in value.keys():
                if paths.has_key(path):
                    if mapping[key][path] > paths[path]:
                        paths[path] = mapping[key][path]
                else:
                    paths[path] = mapping[key][path]
        refs = {} # how many times a path is referenced in maya
        for ref in qutil.getReferences():
            path = rcUtils.getNicePath(str(ref.path))
            if refs.has_key(path):
                refs[path] += 1
            else:
                refs[path] = 1
        # add the references which are not added as many times as required
        for path in paths:
            if refs.has_key(path):
                num = paths[path] - refs[path]
            else:
                num = paths[path]
            if num > 0:
                for _ in range(num):
                    qutil.addRef(path)
                    
    def getRenderLayers(self):
        renderLayers = {}
        for item in self.items:
            renderLayers[item.getTitle()] = item.getRenderLayers()
        return renderLayers
    
    def getEnvLayerSettings(self):
        settings = {}
        for item in self.items:
            settings[item.getTitle()] = [item.isSingleFrame(), item.isOverride(), item.getStartFrame(), item.getEndFrame()]
        return settings
    
    def getMappings(self):
        mappings = {}
        self.addRefs()
        for item in self.items:
            mappings[item.getTitle()] = item.getMappings()
        return mappings
    
    def clear(self):
        pass
        
        
Form2, Base2 = uic.loadUiType(osp.join(uiPath, 'item.ui'))
class Item(Form2, Base2):
    def __init__(self, parent=None, mapping=None, lds=None, envStart=None, envEnd=None):
        super(Item, self).__init__(parent)
        self.setupUi(self)
        self.parentWin = parent
        self.mappings = OrderedDict()
        for key in sorted(mapping):
            self.mappings[key] = mapping[key]
        self.lds = lds
        self.items = []
        self.collapsed = False
        self.styleText = ('background-image: url(%s);\n'+
                      'background-repeat: no-repeat;\n'+
                      'background-position: center right')
        
        self.label_3.hide()
        self.label_4.hide()
        self.startFrameBox.hide()
        self.endFrameBox.hide()
        
        self.startFrameBox.setValue(envStart)
        self.endFrameBox.setValue(envEnd)

        self.iconLabel.setStyleSheet(self.styleText%osp.join(iconPath,
                                                         'ic_collapse.png').replace('\\', '/'))
        self.layersBox = cui.MultiSelectComboBox(self, '--Select Layers--')
        self.renderLayerLayout.addWidget(self.layersBox)
        self.singleFrameButton.toggled.connect(lambda: self.overrideButton.setChecked(False))
        self.singleFrameButton.setChecked(True)
        
        self.collapse()
        self.titleFrame.mouseReleaseEvent = self.collapse
        
    def update(self):
        layers = imaya.getRenderLayers(renderableOnly=False)
        self.layersBox.addItems([layer.name() for layer in layers], selected=[layer.name() for layer in layers if layer.renderable.get()])
        self.clearItems()
        if self.mappings:
            for cache, ld in self.mappings.items():
                item = Mapping(self.parentWin, cache, self.lds, ld).update()
                self.itemLayout.addWidget(item)
                self.items.append(item)
        return self

    def getItems(self):
        return self.items
    
    def updateUI(self, msg):
        if self.parentWin:
            self.parentWin.updateUI(msg)
                
    def clearItems(self):
        for item in self.items:
            item.deleteLater()
        del self.items[:]
        
    def getStartFrame(self):
        return self.startFrameBox.value()

    def getEndFrame(self):
        return self.endFrameBox.value()
    
    def isOverride(self):
        return self.overrideButton.isChecked()

    def isSingleFrame(self):
        return self.singleFrameButton.isChecked()

    def getRenderLayers(self):
        layers = {}
        selectedItems = self.layersBox.getSelectedItems()
        for item in self.layersBox.getItems():
            layers[item] = item in selectedItems
        return layers

    def getMappings(self):
        mappings = {}
        tempItems = []
        usedRefs = []
        for item in self.items:
            if item.filePath:
                if osp.exists(item.filePath):
                    tempItems.append(item)
                else:
                    self.updateUI('Warning: File %s does not exist')
            else:
                mappings[item.getCache()] = item.getLD()
        if tempItems:
            for itm in tempItems:
                for ref in qutil.getReferences():
                    if rcUtils.getNicePath(itm.filePath) == rcUtils.getNicePath(str(ref.path)) and ref not in usedRefs:
                        meshes = qutil.getCombinedMesh(ref)
                        if meshes:
                            if len(meshes) > 1:
                                sBox = cui.SelectionBox(self.parentWin, [QRadioButton(mesh.name()) for mesh in meshes], 'More than one meshes found for %s, please select one'%itm.getCache())
                                sBox.setCancelToolTip('skip this cache file')
                                sBox.exec_()
                                try:
                                    meshes = sBox.getSelectedItems()
                                    if not meshes: continue
                                    else: meshes = [pc.PyNode(meshes[0])]
                                except IndexError:
                                    continue
                            mappings[itm.getCache()] = meshes[0]
                            usedRefs.append(ref)
                            break
                        else:
                            self.updateUI('Warning: Could not find a mesh for %s'%itm.getCache())
        return mappings

    def collapse(self, event=None):
        if self.collapsed:
            self.frame.show()
            self.collapsed = False
            path = osp.join(iconPath, 'ic_collapse.png')
        else:
            self.frame.hide()
            self.collapsed = True
            path = osp.join(iconPath, 'ic_expand.png')
        path = path.replace('\\', '/')
        self.iconLabel.setStyleSheet(self.styleText%path)

    def toggleCollapse(self, state):
        self.collapsed = not state
        self.collapse()

    def setTitle(self, title):
        self.nameLabel.setText(title)

    def getTitle(self):
        return str(self.nameLabel.text().split()[0])

    def mouseReleaseEvent(self, event):
        pass
        
Form3, Base3 = uic.loadUiType(osp.join(uiPath, 'mapping.ui'))
class Mapping(Form3, Base3):
    def __init__(self, parent=None, cache=None, lds=None, currentLD=None):
        super(Mapping, self).__init__(parent)
        self.setupUi(self)
        
        self.cache = cache
        self.basePath = osp.dirname(cache)
        self.lds = lds
        self.currentLD = currentLD
        self.filePath = None
        self.parentWin = parent

        self.removeLabel.setPixmap(QPixmap(osp.join(iconPath, 'ic_remove.png')))
        self.removeLabel.hide()
        self.fileLabel.hide()
        
        self.ldBox.activated[str].connect(self.activated)
        self.removeLabel.mouseReleaseEvent = self.hideFileName
        self.browseButton.clicked.connect(self.browseFileDialog)
        
    def showFileName(self, toggle=True):
        if self.parentWin.isToggleAll() and toggle:
            self.parentWin.showFileName(self.filePath, self.getCache())
        else:
            self.fileLabel.show()
            self.removeLabel.show()
            self.ldBox.hide()
            self.fileLabel.setText(osp.basename(self.filePath))
            self.fileLabel.setToolTip(osp.normpath(self.filePath))
    
    def hideFileName(self, event=None):
        if self.parentWin.isToggleAll():
            self.parentWin.hideFileName(self.getCache())
        else:
            self.filePath = None
            self.fileLabel.hide()
            self.removeLabel.hide()
            self.ldBox.show()
            self.fileLabel.setText('')
        if event: event.accept()
        
    def browseFileDialog(self):
        filename = QFileDialog.getOpenFileName(self, 'Select LD', osp.normpath(osp.dirname(self.parentWin.lastPath)), '*.mb *.ma')
        if filename:
            self.parentWin.lastPath = filename
            self.filePath = filename
            self.showFileName()
        
    def activated(self, text):
        self.parentWin.activated(self.getCache(), text)

    def update(self):
        if self.cache:
            self.setCache(self.cache)
        #if self.lds:
        self.setLDs(self.currentLD)
        return self
            
    def setCache(self, cache):
        self.cacheLabel.setText(osp.basename(cache))
    
    def setLDs(self, current, add=True):
        if add:
            for ld in self.lds:
                if not ld:
                    continue
                self.ldBox.addItem(ld.name())
        if not current:
            self.ldBox.setCurrentIndex(0)
            return
        try:
            current = pc.PyNode(current)
            for i in range(self.ldBox.count()):
                if current.name() == self.ldBox.itemText(i):
                    self.ldBox.setCurrentIndex(i)
                    break
        except pc.MayaAttributeError:
            if osp.exists(str(current)):
                if osp.isfile(current):
                    if osp.splitext(current)[-1] in ['.ma', '.mb']:
                        self.filePath = current
                        self.showFileName(False)
            else:
                self.updateUI('Warning: File not found: %s'%current)

    def getCache(self):
        return osp.join(self.basePath, self.cacheLabel.text())

    def updateUI(self, msg):
        if self.parentWin:
            self.parentWin.updateUI(msg)

    def getLD(self):
        node = self.ldBox.currentText()
        if node:
            return pc.PyNode(node)
        return ''