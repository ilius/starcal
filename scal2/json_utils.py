import json

dataToPrettyJson = lambda data: json.dumps(data, sort_keys=True, indent=2)
dataToCompactJson = lambda data: json.dumps(data, sort_keys=True, separators=(',', ':'))
jsonToData = json.loads

