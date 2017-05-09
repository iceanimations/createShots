'''
Created on Jun 26, 2015

@author: qurban.ali
'''
from PyQt4.QtGui import QRadioButton, QMessageBox
import maya.cmds as cmds
import pymel.core as pc
try:
    pc.loadPlugin('redshift4maya')
except: pass
import qutil
from pymel.core.general import MayaNodeError
reload(qutil)
import os.path as osp
import os
import cui
reload(cui)
import re
import rcUtils
reload(rcUtils)
import imaya
reload(imaya)
try:
    import iutil
except:
    import iutilities as iutil
reload(iutil)


class DataCollector(object):
    '''
    Collects data from a maya scene
    Data includes:
    cache, camera
    and creates a mapping between LD path and cache
    optionally can write all the data to a database file
    '''

    def __init__(self, shotsPath, csvPath, shots, parentWin=None, database=None):
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
        self.renderLayers = None
        self.envLayerSettings = None
        self.camera = None
        self.environments = []
        self.csvData = None
        if csvPath:
            self.collectCSVData(csvPath)
        self.collectMeshes()

    def updateUI(self, msg):
        if self.parentWin:
            self.parentWin.appendStatus(msg)
            
    def collectCSVData(self, csvPath):
        if osp.exists(csvPath):
            data = qutil.getCSVFileData(csvPath)
            if data:
                self.csvData = data
                if self.csvData:
                    if len(self.csvData[0]) != 2:
                        self.parentWin.showMessage(msg='CSV file does not contain 2 columns (Rig -> LD)',
                                                   icon=QMessageBox.Warning)
            else:
                self.updateUI('Warning: Could not read data from the CSV file')
        else:
            self.updateUI('Warning: Could not find the specified CSV file')
            
    def collectMeshes(self):
        props = pc.ls('props')
        self.updateUI('Collecting props')
        if props:
            propNode = None
            if len(props) > 1:
                for prop in props:
                    if prop.name().lower() == 'props' or prop.name().lower() == '|props':
                        try:
                            prop.firstParent()
                        except MayaNodeError:
                            propNode = prop
                            break
            else:
                try:
                    props[0].firstParent()
                except MayaNodeError:
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
        characters = pc.ls('characters')
        if characters:
            charNode = None
            if len(characters) > 1:
                for char in characters:
                    if char.name().lower() == 'character' or char.name().lower() == '|character' or char.name().lower() == 'characters' or char.name().lower() == '|characters':
                        try:
                            char.firstParent()
                        except MayaNodeError:
                            charNode = char
                            break
            else:
                try:
                    characters[0].firstParent()
                except MayaNodeError:
                    charNode = characters[0]
            if not charNode:
                self.updateUI('Warning: Could not find character node in the scene')
            else:
                self.meshes.extend(self.getMeshes(charNode))
        else:
            self.updateUI('Warning: Characters node not found in the scene')
            
    def getMeshes(self, grp):
        meshes = []
        for child in grp.getChildren():
            try:
                if child.getShape(ni=True):
                    meshes.append(child)
            except AttributeError:
                pass
            else:
                meshes.extend(self.getMeshes(child))
        return meshes
    
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
    
    def matchStrings2(self, l1, l2):
        return len(set(l1) & set(l2))
    

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
        #return match
        return None
    
    def getMeshFromCacheName2(self, cacheName, mappedMeshes):
        newCacheName = cacheName.replace('_geo', '').replace('_set', '')
        newCacheName = re.split('[_:|]', newCacheName)
        newCacheName = [x.lower() for x in newCacheName]
        meshNames = {mesh: mesh.name() for mesh in self.meshes}
        count = 0
        match = None
        for mesh, meshName in meshNames.items():
            newCount = self.matchStrings2(newCacheName, [x.lower() for x in re.split('[_:|]', meshName)])
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
                sBox = cui.SelectionBox(self.parentWin, [QRadioButton(phile) for phile in files], 'More than one camera fils found in %s, please select one'%path)
                sBox.setCancelToolTip('Skip adding the camera')
                sBox.exec_()
                try:
                    phile = sBox.getSelectedItems()[0]
                    return osp.join(path, phile)
                except IndexError:
                    pass
            else:
                return osp.join(path, files[0])
            
    def getLDFromRig(self, rigPath):
        ldPath = ''
        if rigPath and osp.exists(rigPath):
            try:
                for rig, ld in self.csvData:
                    if iutil.paths_equal(rig, rigPath):
                        return ld
            except ValueError:
                pass
        else:
            self.updateUI('Warning: Rig <b>%s</b> did not found'%rigPath)
        return ldPath

    def collect(self):
        if self.shots:
            self.updateUI('Collecting data for shot creation')
            for shot in self.shots:
                self.updateUI(osp.join(shot))
                shotPath = osp.join(self.shotsPath, shot, 'animation')
                cachePath = osp.join(shotPath, 'cache')
                cameraPath = osp.join(shotPath, 'camera')
                nanoTexFilePath = ''
                nanoTexPath = osp.join(shotPath, 'tex')
                if not osp.exists(nanoTexPath): nanoTexPath = osp.join(cachePath, 'tex')
                if osp.exists(nanoTexPath):
                    files = os.listdir(nanoTexPath)
                    if files:
                        for phile in files:
                            filePath = osp.join(nanoTexPath, phile)
                            if osp.isfile(filePath):
                                nanoTexFilePath = osp.join(nanoTexPath, filePath)
                                break
                if not osp.exists(cameraPath):
                    self.updateUI('Warning: Camera directory not found: Skipping %s'%shotPath)
                    continue
                if not osp.exists(cachePath):
                    self.updateUI('Warning: Cache directory does not exist in %s'%shotPath)
                self.updateUI('Collecting cache files for %s'%shot)
                cacheFiles = self.getCacheXMLFiles(cachePath)
                if not cacheFiles:
                    self.updateUI('Warning: No cache file found in %s'%cachePath)
                cacheMeshMappings = {}
                if cacheFiles:
                    self.updateUI('Finding meshes for cache files in %s'%shot)
                
                    cacheFiles = sorted(cacheFiles, key=len)
                    cacheFiles.reverse()
                    mappingsFile = osp.join(cachePath, 'mappings.txt')
                    mappings = None
                    if self.csvData:
                        if not osp.exists(mappingsFile):
                            self.updateUI('Warning: Mappings file does not exist in %s'%cachePath)
                        else:
                            with open(mappingsFile) as f:
                                mappings = eval(f.read())
                    for cacheFile in cacheFiles:
                        if self.csvData:
                            mesh = ''
                            if mappings:
                                for cache, rig in mappings.items():
                                    if iutil.paths_equal(cache, osp.splitext(osp.join(cachePath, cacheFile))[0]):
                                        mesh = self.getLDFromRig(rig)
                                        break
                        else:
                            mesh = self.getMeshFromCacheName2(cacheFile, cacheMeshMappings.values())
                            if not mesh:
                                self.updateUI('Warning: Could not find a mesh for %s in %s'%(cacheFile, shot))
                            else:
                                self.updateUI('Found: %s for %s'%(mesh.name(), cacheFile))
                        cacheMeshMappings[osp.join(cachePath, cacheFile)] = mesh
                camera = self.getCameraFile(cameraPath)
                if not camera:
                    self.updateUI('Warning: Could find camera file: Skipping %s'%shot)
                    continue
                self.cacheLDMappings[shot] = [cacheMeshMappings, nanoTexFilePath, camera]
        else:
            self.updateUI('Warning: Could not find shots in %s'%self.shotsPath)
        return self