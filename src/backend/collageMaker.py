'''
Created on Jul 14, 2015

@author: qurban.ali
'''
import imaya
reload(imaya)
try:
    import iutil
except:
    import iutilities as iutil
reload(iutil)
import subprocess
import os
import os.path as osp
import rcUtils
reload(rcUtils)
import pymel.core as pc
import shutil

homeDir = osp.join(rcUtils.homeDir, 'snapshots')
if not osp.exists(homeDir):
    os.mkdir(homeDir)

class CollageMaker(object):
    def __init__(self, parentWin=None):
        super(CollageMaker, self).__init__()
        self.parentWin = parentWin
        self.seqPath = self.parentWin.getShotsFilePath()
        
    def updateUI(self, msg):
        if self.parentWin:
            self.parentWin.appendStatus(msg)
    
    def make(self):
        snapshots = []
        for snap in os.listdir(homeDir):
            snapshots.append(osp.join(homeDir, snap))
        if osp.exists(self.seqPath):
            for shot in snapshots:
                try:
                    if self.parentWin.createCollage() and self.parentWin.createFiles() and not self.parentWin.isLocal():
                            shutil.copy(shot, osp.join(self.seqPath, osp.splitext(osp.basename(shot))[0], 'lighting', 'files'))
                except Exception as ex:
                    self.updateUI('Warning: %s'%str(ex))
        if snapshots:
            command = r"R:\Pipe_Repo\Users\Qurban\applications\ImageMagick\montage.exe -geometry +1+1 -label %f -frame 5 -background '#336699'"
            for snap in snapshots:
                command += " "+ snap
            path = osp.join(homeDir, 'collage.png')
            command += " "+ path
            subprocess.call(command, shell=True)
            return path
            
            
    def makeShot(self, shot, renderLayers, render=False):
        self.parentWin.processEvents()
        self.updateUI('Taking snapshot %s'%shot)
        s1, res = self.snapshot()
        snap1 = osp.join(osp.dirname(s1), osp.basename(s1)+'_texted')
        minTime = str(pc.playbackOptions(q=True, minTime=True)).split('.')[0]
        subprocess.call("R:\\Pipe_Repo\\Users\\Qurban\\applications\\ImageMagick\\convert.exe %s -draw \"text %s\" %s"%(s1, str(res[0]/2)+','+str(res[1]/8) +" '%s'"%minTime, " "+snap1), shell=True)
        maxTime = str(pc.playbackOptions(q=True, maxTime=True)).split('.')[0]
        pc.currentTime(pc.playbackOptions(q=True, maxTime=True))
        s2, res = self.snapshot()
        snap2 = osp.join(osp.dirname(s2), osp.basename(s2)+'texted')
        subprocess.call("R:\\Pipe_Repo\\Users\\Qurban\\applications\\ImageMagick\\convert.exe %s -draw \"text %s\" %s"%(s2, str(res[0]/2)+','+str(res[1]/8) +" '%s'"%maxTime, " "+snap2), shell=True)
        command = r"R:\Pipe_Repo\Users\Qurban\applications\ImageMagick\montage.exe -geometry +1+1"
        path = osp.join(homeDir, shot +'.png')
        command += ' %s %s %s'%(snap1, snap2, path)
        subprocess.call(command, shell=True)
        if renderLayers:
            y = 20
            for layer, val in renderLayers.items():
                if val:
                    subprocess.call("R:\\Pipe_Repo\\Users\\Qurban\\applications\\ImageMagick\\convert.exe %s -draw \"text 20,%s %s\" %s"%(path, y, layer, path), shell=True)
                    y += 20
        
    def snapshot(self):
        try:
            node = pc.PyNode('defaultResolution')
        except:
            node = None
        if node:
            width = node.width.get(); height = node.height.get()
            return imaya.snapshot([width, height]), [width, height]
        return imaya.snapshot(), [256, 256]