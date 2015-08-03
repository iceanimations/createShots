'''
Created on Jun 26, 2015

@author: qurban.ali
'''
import os
import os.path as osp
import maya.cmds as cmds
import pymel.core as pc
import imaya
reload(imaya)

homeDir = osp.join(osp.expanduser('~'), 'create_shots')
if not osp.exists(homeDir):
    os.mkdir(homeDir)

def saveScene(name):
    path = osp.join(homeDir, name)
    cmds.file(rename=path)
    cmds.file(save=True)
    
def removeCameraRef():
    for ref in pc.ls(type=pc.nt.Reference):
        rf = ref.referenceFile()
        if rf:
            if pc.nt.Camera in [type(node) for node in rf.nodes()]:
                rf.remove()
                
def getNicePath(path):
    return osp.normcase(osp.normpath(path))

def getEnvLayerStartEnd():
    cl = currentLayer = pc.PyNode(pc.editRenderLayerGlobals(currentRenderLayer=True, q=True))
    if not currentLayer.name().lower().startswith('env'):
        try:
            currentLayer = [layer for layer in imaya.getRenderLayers(renderableOnly=False)][0]
            pc.editRenderLayerGlobals(currentRenderLayer=currentLayer)
        except IndexError:
            return
    start, end = pc.PyNode('defaultRenderGlobals').startFrame.get(), pc.PyNode('defaultRenderGlobals').endFrame.get()
    pc.editRenderLayerGlobals(currentRenderLayer=cl)
    return currentLayer, start, end