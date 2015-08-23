import os
from os.path import isfile, join
from time import time as now
from collections import OrderedDict

from hashlib import sha1
from bson import BSON

from scal3.path import objectDir
from scal3.os_utils import makeDir
from scal3.json_utils import *
from scal3.utils import myRaise

dataToJson = dataToPrettyJson
#from scal3.core import dataToJson## FIXME


class SObjBase:
    params = ()## used in getData and setData and copyFrom
    __nonzero__ = lambda self: self.__bool__()
    def __bool__(self):
        raise NotImplementedError
    def copyFrom(self, other):
        from copy import deepcopy
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
    def getIdPath(self):
        try:
            parent = self.parent
        except AttributeError:
            raise NotImplementedError('%s.getIdPath: no parent attribute'%self.__class__.__name__)
        try:
            _id = self.id
        except AttributeError:
            raise NotImplementedError('%s.getIdPath: no id attribute'%self.__class__.__name__)
        ######
        path = []
        if _id is not None:
            path.append(_id)
        if parent is None:
            return path
        else:
            return parent.getIdPath() + path
    def getPath(self):
        parent = self.parent
        if parent is None:
            return []
        index = parent.index(self.id)
        return parent.getPath() + [index]


def makeOrderedData(data, params):
    if isinstance(data, dict):
        if params:
            data = list(data.items())
            def paramIndex(key):
                try:
                    return params.index(key)
                except ValueError:
                    return len(params)
            data.sort(key=lambda x: paramIndex(x[0]))
            data = OrderedDict(data)
    return data

def getSortedDict(data):
    return OrderedDict(sorted(data.items()))

class JsonSObjBase(SObjBase):
    file = ''
    paramsOrder = ()
    getDataOrdered = lambda self: makeOrderedData(self.getData(), self.paramsOrder)
    getJson = lambda self: dataToJson(self.getDataOrdered())
    setJson = lambda self, jsonStr: self.setData(jsonToData(jsonStr))
    def save(self):
        if self.file:
            jstr = self.getJson()
            open(self.file, 'w').write(jstr)
        else:
            print('save method called for object %r while file is not set'%self)
    def load(self):
        if not isfile(self.file):
            raise IOError('error while loading json file %r: no such file'%self.file)
        jstr = open(self.file).read()
        if jstr:
            self.setJson(jstr)## FIXME
        self.setModifiedFromFile()
    def setModifiedFromFile(self):
        if hasattr(self, 'modified'):
            try:
                self.modified = int(os.stat(self.file).st_mtime)
            except OSError:
                pass
        else:
            print('no modified param for object %r'%self)


def saveBsonObject(data):
    data = getSortedDict(data)
    bsonBytes = bytes(BSON.encode(data))
    _hash = sha1(bsonBytes).hexdigest()
    dpath = join(objectDir, _hash[:2])
    fpath = join(dpath, _hash[2:])
    if not isfile(fpath):
        makeDir(dpath)
        open(fpath, 'wb').write(bsonBytes)
    return _hash

def loadBsonObject(_hash):
    fpath = join(objectDir, _hash[:2], _hash[2:])
    bsonBytes = open(fpath, 'rb').read()
    if _hash != sha1(bsonBytes).hexdigest():
        raise IOError('sha1 diggest does not match for object file "%s"'%fpath)
    return BSON.decode(bsonBytes)
    

class BsonHistObjBase(SObjBase):
    file = ''
    ## basicParams or noHistParams ? FIXME
    basicParams = (
    )
    def loadBasicData(self):
        if not isfile(self.file):
            return {}
        return jsonToData(open(self.file).read())
    def loadHistory(self):
        lastBasicData = self.loadBasicData()
        try:
            return lastBasicData['history']
        except KeyError:
            if lastBasicData:
                print('no "history" in json file "%s"'%self.file)
            return []
    def saveBasicData(self, basicData):
        jsonStr = dataToJson(basicData)
        open(self.file, 'w').write(jsonStr)
    def save(self, *histArgs):
        '''
            returns last history record: (lastEpoch, lastHash, **args)
        '''
        if not self.file:
            raise RuntimeError('save method called for object %r while file is not set'%self)
        data = self.getData()
        basicData = {}
        for param in self.basicParams:
            try:
                basicData[param] = data.pop(param)
            except KeyError:
                pass
        try:
            data.pop('modified')
        except KeyError:
            pass
        _hash = saveBsonObject(data)
        ###
        history = self.loadHistory()
        ###
        try:
            lastHash = history[0][1]
        except IndexError:
            lastHash = None
        if _hash != lastHash:## or lastHistArgs != histArgs:## FIXME
            tm = now()
            history.insert(0, [tm, _hash] + list(histArgs))
            self.modified = tm
        basicData['history'] = history
        self.saveBasicData(basicData)
        return history[0]
    def load(self):
        '''
            loads the json (and last bson) file, and sets the params to object
            returns last history record: (lastEpoch, lastHash, **args)
        '''
        if not self.file:
            raise RuntimeError('load method called for object %r while file is not set'%self)
        if not isfile(self.file):
            raise IOError('error while loading json file %r: no such file'%self.file)
        data = self.loadBasicData()
        ####
        history = data.pop('history')## we don't keep the history in memory
        lastHistRecord = history[0]
        lastEpoch = lastHistRecord[0]
        lastHash = lastHistRecord[1]
        ####
        data.update(loadBsonObject(lastHash))
        self.setData(data)
        self.modified = int(lastEpoch)
        return lastHistRecord


def updateBasicDataFromBson(data, filePath, fileType):
    '''
        fileType: 'event' | 'group' | 'account'..., display only, does not matter much
    '''
    try:
        lastHash = data['history'][0][1]
    except (KeyError, IndexError):
        raise ValueError('invalid %s file "%s", no "history"'%(fileType, filePath))
    data.update(loadBsonObject(lastHash))



