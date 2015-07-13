'''
Created on Jun 26, 2015

@author: qurban.ali
'''
from PyQt4.QtGui import QRadioButton
import maya.cmds as cmds
import pymel.core as pc
import qutil
reload(qutil)
import os.path as osp
import os
import cui
reload(cui)


class DataCollector(object):
    '''
    Collects data from a maya scene
    Data includes:
    cache, camera
    and creates a mapping between LD path and cache
    optionally can write all the data to a database file
    '''

    def __init__(self, shotsPath, shots, parentWin=None, database=None):
        '''
        @param shotsPath: path to directory where shot directories live
        @param shots: shots to be created (selected from the ui)
        @param parentWin: RenderCheckUI object to update it
        @param database: sqlite database file path (optional)
        '''
        self.shotsPath = shotsPath
        self.shots = shots
        self.parentWin = parentWin
        self.database = database
        self.meshes = []
        
        self.cacheLDMappings = {}
        self.camera = None
        self.environments = []
        
        self.collectMeshes()

    def updateUI(self, msg):
        if self.parentWin:
            self.parentWin.appendStatus(msg)
            
    def collectMeshes(self):
        props = pc.ls('props')
        self.updateUI('Collecting props')
        if props:
            if len(props) > 1:
                propNode = None
                for prop in props:
                    if prop.name().lower() == 'props' or prop.name().lower() == '|props':
                        propNode = prop
                        break
            else:
                propNode = props[0]
            if not propNode:
                self.updateUI('Warning: Could not find Prop node in the scene')
            else:
                for prop in propNode.getChildren():
                    self.updateUI('Found: %s'%prop)
                    self.meshes.append(prop)
        else:
            self.updateUI('Warning: Props node not found in the scene')
        self.updateUI('Collecting characters')
        characters = pc.ls('character')
        if characters:
            if len(characters) > 1:
                charNode = None
                for char in characters:
                    if char.name().lower() == 'character' or char.name().lower() == '|character' or char.name().lower() == 'characters' or char.name().lower() == '|characters':
                        charNode = char
                        break
            else:
                charNode = characters[0]
            if not charNode:
                self.updateUI('Warning: Could not find character node in the scene')
            else:
                for char in charNode.getChildren():
                    self.updateUI('Found: %s'%char)
                    self.meshes.append(char)
        else:
            self.updateUI('Warning: Characters node not found in the scene')
    
    def matchStrings(self, s1, s2):
        s1 = s1.lower(); s2 = s2.lower()
        count = 0
        length = len(s1) if len(s1) < len(s2) else len(s2)
        for i in range(length):
            if s1[i] == s2[i]:
                count += 1
            else:
                break
        return count
            
            
    def getMeshFromCacheName(self, cacheName, mappedMeshes):
        newCacheName = cacheName.replace('_geo', '_shaded').replace('_set', '_combined')
        meshNames = {mesh: qutil.getNiceName(mesh.name()) for mesh in self.meshes}
        count = 0
        match = None
        for mesh, meshName in meshNames.items():
            newCount = self.matchStrings(newCacheName, meshName)
            if newCount > count and mesh not in mappedMeshes:
                match = mesh
                count = newCount
        return match
    
    def getCacheXMLFiles(self, path):
        return [phile for phile in os.listdir(path) if osp.splitext(phile)[-1] == '.xml']
    
    def getCameraFile(self, path):
        files = os.listdir(path)
        files = [phile for phile in files if osp.splitext(phile)[-1] in ['.ma', '.mb']]
        if not files:
            self.updateUI('Warning: Camera file not found in %s'%path)
        else:
            if len(files) > 1:
                sBox = cui.SelectionBox(self, [QRadioButton(phile) for phile in files], 'More than one camera fils found in %s, please select one'%path)
                sBox.exec_()
                try:
                    phile = sBox.getSelectedItems()[0]
                    return osp.join(path, phile)
                except IndexError:
                    pass
            else:
                return osp.join(path, files[0])
            
    def collect(self):
        if self.shots:
            self.updateUI('Collecting data for shot creation')
            for shot in self.shots:
                self.updateUI(osp.join(shot))
                shotPath = osp.join(self.shotsPath, shot, 'animation')
                cachePath = osp.join(shotPath, 'cache')
                cameraPath = osp.join(shotPath, 'camera')
                if not osp.exists(cachePath):
                    self.updateUI('Warning: Cache directory does not exist in %s'%shotPath)
                    continue
                if not osp.exists(cameraPath):
                    self.updateUI('Warning: Camera directory not found in %s'%shotPath)
                    continue
                self.updateUI('Collecting cache files for %s'%shot)
                cacheFiles = self.getCacheXMLFiles(cachePath)
                if not cacheFiles:
                    self.updateUI('Warning: No cache file found in %s'%cachePath)
                    continue
                self.updateUI('Finding meshes for cache files in %s'%shot)
                cacheMeshMappings = {}
                for cacheFile in cacheFiles:
                    mesh = self.getMeshFromCacheName(cacheFile, cacheMeshMappings.keys())
                    #print cacheFile +' >> '+ mesh
                    if not mesh:
                        self.updateUI('Warning: Could not find a mesh for %s in %s'%(cacheFile, shot))
                        continue
                    self.updateUI('Found: %s for %s'%(mesh.name(), cacheFile))
                    cacheMeshMappings[mesh] = osp.join(cachePath, cacheFile)
                camera = self.getCameraFile(cameraPath)
                if not camera:
                    self.updateUI('Warning: Could find camera file for %s'%shot)
                self.cacheLDMappings[shot] = (cacheMeshMappings, camera)
        else:
            self.updateUI('Warning: Could not find shots in %s'%self.shotsPath)
        return self