'''
Created on Jun 26, 2015

@author: qurban.ali
'''

class DataCollector(object):
    '''
    Collects data from a maya scene
    Data includes:
    cache, camera
    and creates a mapping between LD path and cache
    optionally can write all the data to a database file
    '''

    def __init__(self, animationFilePath, csvFilePath, parentWin, database=None):
        '''
        @param animationFilePath: to collect the data from
        @param csvFilePath: to get the LD paths
        @param parentWin: to update the ui
        @param database: sqlite database file path (optional)   
        '''
        self.animationFilePath = animationFilePath
        self.csvFilePath = csvFilePath
        self.parentWin = parentWin
        self.database = database
        
        self.cacheLDMappings = {}
        
    def collect(self):
        '''
        collects the data
        '''
        self.parentWin.appendStatus('Opening animation file path')