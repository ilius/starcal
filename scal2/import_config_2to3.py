import re

def loadConf(confPath):
    text = open(confPath).read()
    data = {}
    exec(text, {}, data)
    return data

def loadCoreConf(confPath):
    def loadPlugin(fname, **data):
        data['file'] = fname
        return data
    text = open(confPath).read()
    text = text.replace('calTypes.activeNames', 'calTypes__activeNames')
    text = text.replace('calTypes.inactiveNames', 'calTypes__inactiveNames')
    ######
    data = {}
    exec(text, {
        'loadPlugin': loadPlugin
    }, data)
    return data

def loadUiCustomizeConf(confPath):
    text = open(confPath).read()
    text = re.sub('^ui\.', '', text, flags=re.M)
    text = re.sub('^ud\.', 'ud__', text, flags=re.M)
    ######
    data = {}
    exec(text, {}, data)
    return data






