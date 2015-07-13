'''
Created on Jun 26, 2015

@author: qurban.ali
'''
import os
import os.path as osp
import maya.cmds as cmds
import pymel.core as pc

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