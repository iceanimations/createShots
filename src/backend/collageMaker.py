'''
Created on Jul 14, 2015

@author: qurban.ali
'''
import imaya
reload(imaya)
try:
    import iutilities as iutil
except:
    import iutil
reload(iutil)
import subprocess
import os
import os.path as osp
import rcUtils
reload(rcUtils)
import pymel.core as pc

homeDir = osp.join(rcUtils.homeDir, 'snapshots')
if not osp.exists(homeDir):
    os.mkdir(homeDir)

class CollageMaker(object):
    def __init__(self, parentWin=None):
        super(CollageMaker, self).__init__()
        self.parentWin = parentWin
        
    def updateUI(self, msg):
        if self.parentWin:
            self.parentWin.appendStatus(msg)
    
    def make(self):
        snapshots = []
        for snap in os.listdir(homeDir):
            snapshots.append(osp.join(homeDir, snap))
        if snapshots:
            command = r"R:\Pipe_Repo\Users\Qurban\applications\ImageMagick\montage.exe -geometry +1+1 -label %f -frame 5 -background '#336699'"
            for snap in snapshots:
                command += " "+ snap
            path = osp.join(homeDir, 'collage.png')
            command += " "+ path
            subprocess.call(command, shell=True)
            return path
            
            
    def makeShot(self, shot):
        self.updateUI('Taking snapshot %s'%shot)
        s1 = self.snapshot()
        pc.currentTime(pc.playbackOptions(q=True, maxTime=True))
        s2 = self.snapshot()
        command = r"R:\Pipe_Repo\Users\Qurban\applications\ImageMagick\montage.exe -geometry +1+1"
        command += ' %s %s %s'%(s1, s2, osp.join(homeDir, shot +'.png'))
        subprocess.call(command, shell=True)
            
    def snapshot(self):
        return imaya.snapshot()
        
    def render(self, directory, filename):
        mels = ('\"setAttr defaultRenderGlobals.animation 0;setAttr defaultRenderLayer.renderable 1;\"',
                '\"setAttr defaultRenderGlobals.animation 0;currentTime `playbackOptions -q -maxTime`;setAttr "defaultRenderLayer.renderable" 1;\"')
        for i, mel in enumerate(mels):
            newDir = osp.join(directory, str(i))
            if not osp.exists(newDir):
                os.mkdir(newDir)
            command = r'C:\Program Files\Autodesk\Maya2015\bin\render.exe  -preRender %s -rd %s %s'%(mel, newDir, filename)
            subprocess.call(command)
        return directory
        