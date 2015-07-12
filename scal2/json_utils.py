import sys
try:
    import json
except ImportError:
    import simplejson as json

from scal2.lib import OrderedDict

dataToPrettyJson = lambda data, ensure_ascii=False: json.dumps(
    data,
    sort_keys=False,
    indent=2,
    ensure_ascii=ensure_ascii,
)

dataToCompactJson = lambda data, ensure_ascii=False: json.dumps(
    data,
    sort_keys=False,
    separators=(',', ':'),
    ensure_ascii=ensure_ascii,
)

jsonToData = json.loads

jsonToOrderedData = lambda text: json.JSONDecoder(
    object_pairs_hook=OrderedDict,
).decode(text)

###############################

def loadJsonConf(module, confPath):
    from os.path import isfile
    ###
    if not isfile(confPath):
        return
    ###
    try:
        text = open(confPath).read()
    except Exception as e:
        print('failed to read file "%s": %s'%(confPath, e))
        return
    ###
    try:
        data = json.loads(text)
    except Exception as e:
        print('invalid json file "%s": %s'%(confPath, e))
        return
    ###
    if isinstance(module, str):
        module = sys.modules[module]
    for key, value in data.items():
        setattr(module, key, value)


def saveJsonConf(module, confPath, params):
    if isinstance(module, str):
        module = sys.modules[module]
    ###
    data = {}
    for param in params:
        data[param] = getattr(module, param)
    ###
    text = dataToPrettyJson(data)
    try:
        open(confPath, 'w').write(text)
    except Exception as e:
        print('failed to save file "%s": %s'%(confPath, e))
        return


