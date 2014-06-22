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

