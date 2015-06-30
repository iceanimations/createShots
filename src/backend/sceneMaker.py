'''
Created on Jun 26, 2015

@author: qurban.ali
'''
import qutil
reload(qutil)
import pymel.core as pc
import os.path as osp
import setupSaveScene

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
        self.camera = dataCollector.camera # path to camera file
        self.environment = dataCollector.environment # path to environment file
        self.parentWin = parentWin
        
    def updateUI(self, msg):
        if self.parentWin:
            self.parentWin.appendStatus(msg)

    def make(self):
        if self.cacheLDMappings and self.camera and self.environment:
            self.updateUI('Starting scene making')
            self.updateUI('referencing camera')
            cameraRef = qutil.addRef(self.camera)
            self.updateUI('referencing environment')
            qutil.addRef(self.environment)
            self.updateUI('referencing characters, props and vehicles and applying cache')
            errors = qutil.applyCache(self.cacheLDMappings)
            if errors:
                for error in errors:
                    self.updateUI(error)
            camera = None
            try:
                camera = [node for node in cameraRef.nodes() if type(node) == pc.nt.Camera][0]
            except IndexError:
                self.updateUI('Could not find camera')
            if camera:
                errors = setupSaveScene.setupScene(msg=False, cam=camera)
                if errors:
                    for error in errors:
                        self.updateUI(error)
            self.updateUI('Applying new material to all meshes')
            rscmd = 'createRenderNodeCB -asShader "surfaceShader" RedshiftArchitectural ""'
            sg = pc.PyNode(pc.Mel.eval(rscmd)).outColor.outputs()[0]
            pc.sets(sg, e=True, fe=pc.ls(type=pc.nt.Mesh))
        return self