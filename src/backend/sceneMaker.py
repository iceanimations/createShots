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
import imaya
reload(imaya)
import rcUtils
reload(rcUtils)
import os
import collageMaker
reload(collageMaker)
import sys
import shutil
from loader.command.python import RedshiftAOVTools
from pprint import pprint

renderShotsBackend = osp.join(qutil.dirname(__file__, 4), 'renderShots', 'src', 'backend')
sys.path.insert(0, renderShotsBackend)

import rendering
reload(rendering)


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
        self.renderLayers = dataCollector.renderLayers
        self.envLayerSettings = dataCollector.envLayerSettings
        self.meshes = dataCollector.meshes
        if self.meshes is None:
            self.meshes = []
        self.parentWin = parentWin
        self.shotsPath = parentWin.getShotsFilePath()
        self.collageMaker = collageMaker.CollageMaker(self.parentWin)
        self.collage = None
        self.usedObjects = []
        self.resolution = [] # to collect resolution and aspect ratio in render settings
        self.frameRange = {} # to collect frame range and step in render settings
        
        self.setAllObjects()
    
    def setAllObjects(self):
        for value in self.cacheLDMappings.values():
            for ld in value[0].values():
                if ld and ld not in self.meshes:
                    self.meshes.append(ld)
        
    def updateUI(self, msg):
        if self.parentWin:
            self.parentWin.appendStatus(msg)
            
    def clearCaches(self):
        for mesh in self.meshes:
            if mesh.history(type='cacheFile'):
                pc.select(mesh)
                pc.mel.eval('deleteCacheFile 3 { "keep", "", "geometry" } ;')

    def hideShowObjects(self):
        good = []
        bad = []
        for layer in imaya.getRenderLayers(renderableOnly=False):
            if layer.name().lower().startswith('env'): continue
            pc.editRenderLayerGlobals(currentRenderLayer=layer)
            del good[:]
            del bad[:]
            for obj in self.meshes:
                if self.isCacheApplied(obj):
                    good.append(obj)
                else:
                    bad.append(obj)
            pc.select(bad)
            pc.mel.HideSelectedObjects()
            pc.select(good)
            pc.mel.ShowSelectedObjects()
            pc.select(cl=True)

    def isCacheApplied(self, obj):
        if obj.history(type='cacheFile'):
            return True
        return False
            
    def setupEnvLayer(self, shot):
        self.updateUI('Checking Env layer settings for %s'%shot)
        if self.envLayerSettings:
            settings = self.envLayerSettings[shot]
            if settings:
                cl = pc.PyNode(pc.editRenderLayerGlobals(q=True, currentRenderLayer=True))
                node = pc.PyNode('defaultRenderGlobals')
                for layer in imaya.getRenderLayers(renderableOnly=False):
                    if layer.name().lower().startswith('env'):
                        pc.editRenderLayerGlobals(currentRenderLayer=layer)
                        if settings[0]:
                            pc.editRenderLayerAdjustment(node.endFrame)
                            node.endFrame.set(node.startFrame.get())
                        else:
                            if settings[1]:
                                if settings[2] != node.startFrame.get():
                                    pc.editRenderLayerAdjustment(node.startFrame)
                                    node.startFrame.set(settings[2])
                                if settings[3] != node.endFrame.get():
                                    pc.editRenderLayerAdjustment(node.endFrame)
                                    node.endFrame.set(settings[3])
                pc.editRenderLayerGlobals(currentRenderLayer=cl)
                    
    def collectRenderSettings(self):
        self.frameRange.clear()
        # frame range
        for layer in imaya.getRenderLayers():
            pc.editRenderLayerGlobals(currentRenderLayer=layer)
            self.frameRange[layer.name()] = [pc.getAttr('defaultRenderGlobals.startFrame'),
                                      pc.getAttr('defaultRenderGlobals.endFrame')]
            
    def collectResolution(self):
        # resolution
        del self.resolution[:]
        self.resolution.append(pc.getAttr('defaultResolution.width'))
        self.resolution.append(pc.getAttr('defaultResolution.height'))
        self.resolution.append(pc.getAttr('defaultResolution.deviceAspectRatio'))
    
    def restoreRenderSettings(self):
        node = pc.PyNode('redshiftOptions')
        node.imageFilePrefix.set("<Camera>\<RenderLayer>\<RenderLayer>_<AOV>\<RenderLayer>_<AOV>_")
        pc.setAttr("defaultRenderGlobals.imageFilePrefix", "<Camera>/<RenderLayer>/<RenderLayer>_<AOV>/<RenderLayer>_<AOV>_", type="string")
        RedshiftAOVTools.fixAOVPrefixes()
        pc.setAttr('defaultRenderGlobals.byFrameStep', 1)
        
        # resolution
        pc.setAttr('defaultResolution.width', self.resolution[0])
        pc.setAttr('defaultResolution.height', self.resolution[1])
        pc.setAttr('defaultResolution.deviceAspectRatio', self.resolution[2])
        
        # frame range
#         for layer in imaya.getRenderLayers():
#             pc.editRenderLayerGlobals(currentRenderLayer=layer)
#             name = layer.name()
#             pc.setAttr('defaultRenderGlobals.startFrame', self.frameRange[name][0])
#             pc.setAttr('defaultRenderGlobals.endFrame', self.frameRange[name][1])
#             pc.setAttr('defaultRenderGlobals.byFrameStep', 1)


    def importNanoScreen(self, path):
        if osp.exists(path):
            self.updateUI('Importing Nano Textures')
            nodes = pc.ls(type='file')
            flag = False
            for node in nodes:
                if node.hasAttr('nanoScreen'):
                    node.ftn.set(path)
                    node.useFrameExtension.set(1)
                    flag=True
            if not flag:
                self.updateUI('Warning: Nano Textures found but no marked File node found in the scene')

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
                        try:
                            os.remove(path2)
                        except:
                            shutil.rmtree(path2)
            self.updateUI('<b>Starting scene making</b>')
            # switch to masterLayer
            for layer in imaya.getRenderLayers(renderableOnly=False):
                if layer.name().lower().startswith('default'):
                    pc.editRenderLayerGlobals(currentRenderLayer=layer)
                    break
            count = 1
            shotLen = len(self.cacheLDMappings.keys())
            cameraRef = None
            self.collectResolution()
            for shot in sorted(self.cacheLDMappings.keys()):
                self.parentWin.setStatus('Creating <b>%s</b> (%s of %s)'%(shot, count, shotLen))
                self.clearCaches()
                self.updateUI('Creating <b>%s</b>'%shot)
                data = self.cacheLDMappings[shot]
                self.updateUI('applying cache to objects')
                for cache, ld in data[0].items():
                    if ld:
                        self.updateUI('Applying %s to <b>%s</b>'%(osp.basename(cache), ld.name()))
                        try:
                            self.usedObjects.append(ld)
                            imaya.applyCache(ld, cache)
                        except Exception as ex:
                            self.updateUI('Warning: Could not apply cache to %s, %s'%(ld.name(), str(ex)))
                if cameraRef:
                    self.updateUI('Removing camera %s'%str(osp.basename(cameraRef.path)))
                    cameraRef.remove()
                if len(data) == 3:
                    self.importNanoScreen(data[1])
                    self.updateUI('adding camera %s'%osp.basename(data[-1]))
                    cameraRef = pc.createReference(data[-1], mergeNamespacesOnClash=True, ignoreVersion=True, gl=True, options="v=0;", namespace=":")
                    camera = None
                    try:
                        camera = [node for node in cameraRef.nodes() if type(node) == pc.nt.Camera][0]
                    except IndexError:
                        self.updateUI('Warning: Could not find camera in %s'%data[-1])
                    if camera:
                        camera = camera.firstParent()
                        pc.lookThru(camera)
                        errors = setupSaveScene.setupScene(msg=False, cam=camera, ro=True)
                        if errors:
                            for error in errors:
                                self.updateUI(error)
                cl = pc.PyNode(pc.editRenderLayerGlobals(q=True, currentRenderLayer=True))
                if self.renderLayers:
                    for layer, val in self.renderLayers[shot].items():
                        try:
                            pc.PyNode(layer).renderable.set(val)
                        except Exception as ex:
                            self.updateUI('Warning: Could not adjust render layer, '+ str(ex))
                pc.editRenderLayerGlobals(currentRenderLayer=cl)
                path = osp.join(self.shotsPath, shot, 'lighting', 'files', shot + qutil.getExtension())
                self.hideShowObjects()
                self.setupEnvLayer(shot)
                try:
                    if self.parentWin.createFiles():
                        if os.environ['USERNAME'] == 'qurban.ali' or self.parentWin.isLocal():
                            outputPath = self.parentWin.getOutputPath(msg=False)
                            if outputPath:
                                self.updateUI('Saving %s to %s'%(shot, outputPath))
                                rcUtils.saveScene(osp.basename(path), path=outputPath)
                            else:
                                raise RuntimeError, "Could not find a location to save files"
                        else:
                            self.updateUI('Saving shot as %s'%path)
                            imaya.saveSceneAs(path)
                except Exception as ex:
                    self.updateUI('Warning: '+ str(ex))
                    self.updateUI('Saving %s to %s'%(shot, homeDir))
                    rcUtils.saveScene(osp.basename(path))
                if self.parentWin.createCollage():
                    if not self.parentWin.isRender():
                        imaya.toggleTextureMode(True)
                    if self.parentWin.isRender():
                        self.parentWin.appendStatus('<b>Rendering %s</b>'%shot)
                        rendering.homeDir = osp.join(homeDir, 'renders')
                        if not osp.exists(rendering.homeDir):
                            os.mkdir(rendering.homeDir)
                        rendering.configureScene(self.parentWin, resolution=self.parentWin.getResolution(), shot=shot)
                        layers = imaya.getRenderLayers()
                        length = len(layers)
                        for i, layer in enumerate(imaya.batchRender()):
                            self.updateUI('Rendering: %s (%s of %s)'%(layer, i+1, length))
                        for layer in layers:
                            layer.renderable.set(1)
                        self.restoreRenderSettings()
                    else:
                        self.collageMaker.makeShot(shot, self.renderLayers[shot])
                    if not self.parentWin.isRender():
                        imaya.toggleTextureMode(False)
                count += 1
            self.parentWin.setStatus('')
            if self.parentWin.createCollage() or not self.parentWin.isRender():
                self.collage = self.collageMaker.make()
        return self