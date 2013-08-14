try:
    import json
except ImportError:
    import simplejson as json

from scal2.lib import OrderedDict

dataToPrettyJson = lambda data: json.dumps(data, sort_keys=False, indent=2)
dataToCompactJson = lambda data: json.dumps(data, sort_keys=False, separators=(',', ':'))
jsonToData = json.loads
jsonToOrderedData = lambda text: json.JSONDecoder(object_pairs_hook=OrderedDict).decode(text)

