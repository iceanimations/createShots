'''
Created on Jun 26, 2015

@author: qurban.ali
'''

class DeadlineSubmitter(object):
    '''
    submits the current scene to deadline for rendering
    '''
    def __init__(self, sceneMaker, parentWin=None):
        '''
        @param sceneMaker: SceneMaker class object
        @param parentwin: RenderCheckUI object to update it  
        '''
        self.parentWin = parentWin
        self.sceneMaker = sceneMaker
    
    def submit(self):
        pass