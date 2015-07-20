'''
Created on Jul 17, 2015

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
        self.data = data
        self.mappings = data.cacheLDMappings
        self.items = []
        
        self.okButton.clicked.connect(lambda: self.accept())
        self.cancelButton.clicked.connect(lambda: self.reject())
        
    def activated(self, cache, ld):
        if self.toggleAllButton.isChecked():
            for item in self.items:
                for itm in item.getItems():
                    if osp.basename(itm.getCache()).lower() == osp.basename(cache).lower():
                        itm.setLDs(ld, add=False)
        
    def populate(self):
        if self.mappings:
            lds = self.data.meshes #list(set([val for mapping in self.mappings.values() for val in mapping[0].values()]))
            for key, value in self.mappings.items():
                item = Item(self, value[0], lds).update()
                item.setTitle(key)
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
            mappings[rcUtils.getNicePath(item.getCache())] = item.getLD()
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
        return str(self.nameLabel.text())

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
        self.parentWin = parent
        
        self.ldBox.activated[str].connect(self.activated)
        
    def activated(self, text):
        self.parentWin.activated(self.getCache(), text)

    def update(self):
        if self.cache and self.lds:
            self.setCache(self.cache)
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
    
    def getLD(self):
        node = self.ldBox.currentText()
        if node:
            return pc.PyNode(node)
        return ''