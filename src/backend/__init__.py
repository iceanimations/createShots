import dataCollector
import collageMaker
import rcUtils
import sceneMaker
map(lambda m: reload(m), [dataCollector, collageMaker,
                          rcUtils, sceneMaker])
DataCollector = dataCollector.DataCollector
CollageMaker = collageMaker.CollageMaker
SceneMaker = sceneMaker.SceneMaker