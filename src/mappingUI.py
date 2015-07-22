'''
Created on Jul 17, 2015

@author: qurban.ali
'''
from uiContainer import uic
from PyQt4.QtGui import QMessageBox, QFileDialog, QPushButton, qApp, QPixmap
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
        
    def populate(self):
        if self.mappings:
            lds = self.data.meshes
            for key, value in self.mappings.items():
                item = Item(self, value[0], lds).update()
                item.setTitle(key +' ('+ str(len(item.getItems())) +')')
                
                self.items.append(item)
                self.itemLayout.addWidget(item)
        return self
    
    def getMappings(self):
        mappings = {}
        for item in self.items:
            mappings[item.getTitle()] = item.getMappings()
        return mappings
    
    def clear(self):
        pass
        
        
Form2, Base2 = uic.loadUiType(osp.join(uiPath, 'item.ui'))
class Item(Form2, Base2):
    def __init__(self, parent=None, mapping=None, lds=None):
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

        self.iconLabel.setStyleSheet(self.styleText%osp.join(iconPath,
                                                         'ic_collapse.png').replace('\\', '/'))
        self.collapse()
        self.titleFrame.mouseReleaseEvent = self.collapse
        
    def update(self):
        self.clearItems()
        if self.mappings:
            for cache, ld in self.mappings.items():
                item = Mapping(self.parentWin, cache, self.lds, ld).update()
                self.itemLayout.addWidget(item)
                self.items.append(item)
        return self

    def getItems(self):
        return self.items
                
    def clearItems(self):
        for item in self.items:
            item.deleteLater()
        del self.items[:]
        
    def getMappings(self):
        mappings = {}
        for item in self.items:
            mappings[item.getCache()] = item.getLD()
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
        
    def showFileName(self):
        if self.parentWin.isToggleAll():
            self.parentWin.showFileName(self.filePath, self.getCache())
        else:
            self.filePath = self.filePath
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
        if self.lds:
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
        current = pc.PyNode(current)
        for i in range(self.ldBox.count()):
            if current.name() == self.ldBox.itemText(i):
                self.ldBox.setCurrentIndex(i)
                break

    def getCache(self):
        return osp.join(self.basePath, self.cacheLabel.text())
    
    def updateUI(self, msg):
        if self.parentWin:
            self.parentWin.updateUI(msg)
            
    def addRef(self, path):
        for ref in  qutil.getReferences():
            if osp.normcase(osp.normpath(str(ref.path))) == osp.normcase(osp.normpath(path)):
                return ref
        return qutil.addRef(path)
    
    def getLD(self):
        if self.filePath:
            self.updateUI('Adding reference: %s'%self.filePath)
            ref = self.addRef(self.filePath)
            if ref:
                meshes = qutil.getCombinedMesh(ref)
                if not meshes:
                    self.updateUI('Warning: No meshes found in %s'%self.filePath)
                    return ''
                if len(meshes) > 1:
                    self.updateUI('Warning: More than one meshes found in %s'%self.filePath)
                    return ''
                return meshes[0]
            else:
                self.updateUI('Could not add reference: %s'%self.filePath)
                return
        else:
            node = self.ldBox.currentText()
            if node:
                return pc.PyNode(node)
            return ''