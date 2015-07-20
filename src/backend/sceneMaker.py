'''
Created on Jun 26, 2015

@author: qurban.ali
'''
import qutil
reload(qutil)
import pymel.core as pc
import setupSaveScene
reload(setupSaveScene)
import os.path as osp
import imaya as mi
import rcUtils
reload(rcUtils)
import os
import collageMaker
reload(collageMaker)


homeDir = rcUtils.homeDir

class SceneMaker(object):
    '''
    Creates a scene from given object of DataCollector
    '''
    def __init__(self, dataCollector, parentWin=None):
        '''
        @param dataCollector: instance of DataCollector class
        @param parentWin: RenderCheckUI objec to update the ui  
        '''
        self.cacheLDMappings = dataCollector.cacheLDMappings
        self.meshes = dataCollector.meshes
        self.parentWin = parentWin
        self.shotsPath = parentWin.getShotsFilePath()
        self.collageMaker = collageMaker.CollageMaker(self.parentWin)
        self.collage = None
        
    def updateUI(self, msg):
        if self.parentWin:
            self.parentWin.appendStatus(msg)
            
    def clearCaches(self):
        for mesh in self.meshes:
            if mesh.history(type='cacheFile'):
                pc.select(mesh)
                pc.mel.eval('deleteCacheFile 3 { "keep", "", "geometry" } ;')

    def make(self):
        if self.cacheLDMappings:
            for phile in os.listdir(homeDir):
                path = osp.join(homeDir, phile)
                if osp.isfile(path):
                    os.remove(osp.join(homeDir, phile))
                else:
                    if phile == 'incrementalSave':
                        continue
                    for phile2 in os.listdir(path):
                        path2 = osp.join(path, phile2)
                        os.remove(path2)
            self.updateUI('<b>Starting scene making</b>')
            for shot in self.cacheLDMappings.keys():
                self.clearCaches()
                self.updateUI('Creating <b>%s</b>'%shot)
                data = self.cacheLDMappings[shot]
                self.updateUI('applying cache to objects')
                for cache, ld in data[0].items():
                    if ld:
                        self.updateUI('Applying %s to <b>%s</b>'%(cache, ld.name()))
                        mi.applyCache(ld, cache)
                cameraRef = None
                if len(data) == 2:
                    self.updateUI('adding camera %s'%osp.basename(data[-1]))
                    cameraRef = qutil.addRef(data[-1])
                    camera = None
                    try:
                        camera = [node for node in cameraRef.nodes() if type(node) == pc.nt.Camera][0]
                    except IndexError:
                        self.updateUI('Could not find camera in %s'%data[-1])
                    if camera:
                        pc.lookThru(camera)
                        errors = setupSaveScene.setupScene(msg=False, cam=camera)
                        if errors:
                            for error in errors:
                                self.updateUI(error)
                path = osp.join(self.shotsPath, shot, 'lighting', 'files', shot + qutil.getExtension())
                try:
                    self.updateUI('Saving shot as %s'%path)
                    raise RuntimeError, 'No error, just bypassed the file saving in P drive'
                    mi.saveSceneAs(path)
                except Exception as ex:
                    self.updateUI('Warning: '+ str(ex))
                    self.updateUI('Saving shot to %s'%homeDir)
                    rcUtils.saveScene(osp.basename(path))
                self.collageMaker.makeShot(shot)
                if cameraRef:
                    self.updateUI('Removing camera %s'%str(cameraRef.path))
                    cameraRef.remove()
            self.collage = self.collageMaker.make()
        return self