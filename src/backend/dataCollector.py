'''
Created on Jun 26, 2015

@author: qurban.ali
'''
import maya.cmds as cmds
import pymel.core as pc
import qutil
reload(qutil)
import os.path as osp
import os


class DataCollector(object):
    '''
    Collects data from a maya scene
    Data includes:
    cache, camera
    and creates a mapping between LD path and cache
    optionally can write all the data to a database file
    '''

    def __init__(self, mappingsFilePath, csvFilePath, parentWin=None, database=None):
        '''
        @param animationFilePath: to collect the data from
        @param csvFilePath: to get the LD paths
        @param parentWin: RenderCheckUI object to update it
        @param database: sqlite database file path (optional)   
        '''
        self.mappingsFilePath = mappingsFilePath
        self.csvFilePath = csvFilePath
        self.parentWin = parentWin
        self.database = database
        
        self.cacheLDMappings = {}
        self.camera = None
        self.environment = None
        
    def updateUI(self, msg):
        if self.parentWin:
            self.parentWin.appendStatus(msg)
        
    def collect(self):
        '''
        collects the data
        '''
        self.updateUI('Reading mappings file')
        rigLDMappings = qutil.getCSVFileData(self.csvFilePath)
        rigCacheMappings = None
        with open(self.mappingsFilePath) as f:
            rigCacheMappings = eval(f.read())
        if rigCacheMappings and rigLDMappings:
            self.updateUI('collecting camera')
            camera = osp.join(qutil.dirname(rigCacheMappings.items()[0][0], depth=2), 'camera')
            if osp.exists(camera):
                files = os.listdir(camera)
                if files:
                    self.camera = osp.join(camera, files[0])
            self.updateUI('Collecting cache files')
            for rig, cache in rigCacheMappings.items():
                for item in rigLDMappings:
                    if osp.normpath(osp.normcase(rig)) == osp.normpath(osp.normcase(item[0])):
                        self.parentWin.appendStatus(cache +' >> '+ item[1])
                        self.cacheLDMappings[cache] = item[1]
            self.updateUI('Getting environment file')
            with open(osp.join(osp.dirname(self.mappingsFilePath), 'environment.txt')) as f:
                path = f.read()
                if osp.exists(path):
                    self.environment = path
        return self