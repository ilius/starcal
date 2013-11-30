import os
from os.path import isfile
from copy import deepcopy

from scal2.json_utils import *
from scal2.core import myRaise, dataToJson

class SObjBase:
    params = ()## used in getData and setData and copyFrom
    def copyFrom(self, other):
        for attr in self.params:
            try:
                value = getattr(other, attr)
            except AttributeError:
                continue
            setattr(
                self,
                attr,
                deepcopy(value),
            )
    def copy(self):
        newObj = self.__class__()
        newObj.copyFrom(self)
        return newObj
    getData = lambda self:\
        dict([(param, getattr(self, param)) for param in self.params])
    def setData(self, data):
        #if isinstance(data, dict):## FIXME
        for key, value in data.items():
            if key in self.params:
                setattr(self, key, value)



def makeOrderedData(data, params):
    if isinstance(data, dict):
        if params:
            data = data.items()
            def paramIndex(key):
                try:
                    return params.index(key)
                except ValueError:
                    return len(params)
            data.sort(cmp=lambda x, y: cmp(paramIndex(x[0]), paramIndex(y[0])))
            data = OrderedDict(data)
    return data


class JsonSObjBase(SObjBase):
    file = ''
    jsonParams = ()
    getDataOrdered = lambda self: makeOrderedData(self.getData(), self.jsonParams)
    getJson = lambda self: dataToJson(self.getDataOrdered())
    setJson = lambda self, jsonStr: self.setData(jsonToData(jsonStr))
    def save(self):
        jstr = self.getJson()
        open(self.file, 'w').write(jstr)
    def load(self):
        if not isfile(self.file):
            raise IOError('error while loading json file %r: no such file'%self.file)
            if hasattr(self, 'modified'):
                self.setModifiedFromFile()
        else:
            'no modified param'
        jstr = open(self.file).read()
        if jstr:
            self.setJson(jstr)## FIXME
    def setModifiedFromFile(self):
        try:
            self.modified = int(os.stat(self.file).st_mtime)
        except OSError:
            pass

