try:
    import json
except ImportError:
    import simplejson as json

dataToPrettyJson = lambda data: json.dumps(data, sort_keys=False, indent=2)
dataToCompactJson = lambda data: json.dumps(data, sort_keys=False, separators=(',', ':'))
jsonToData = json.loads

