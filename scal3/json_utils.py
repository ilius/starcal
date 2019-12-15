#!/usr/bin/env python3

from scal3 import logger
log = logger.get()

import sys
import json
from collections import OrderedDict


def dataToPrettyJson(data, ensure_ascii=False, sort_keys=False):
	return json.dumps(
		data,
		indent="\t",
		ensure_ascii=ensure_ascii,
		sort_keys=sort_keys,
	)


def dataToCompactJson(data, ensure_ascii=False, sort_keys=False):
	return json.dumps(
		data,
		separators=(",", ":"),
		ensure_ascii=ensure_ascii,
		sort_keys=sort_keys,
	)


jsonToData = json.loads


def jsonToOrderedData(text):
	return json.JSONDecoder(
		object_pairs_hook=OrderedDict,
	).decode(text)


###############################


def loadJsonConf(module, confPath, decoders={}):
	from os.path import isfile
	###
	if not isfile(confPath):
		return
	###
	try:
		with open(confPath) as fp:
			text = fp.read()
	except Exception as e:
		log.error(f"failed to read file {confPath!r}: {e}")
		return
	###
	try:
		data = json.loads(text)
	except Exception as e:
		log.error(f"invalid json file {confPath!r}: {e}")
		return
	###
	if isinstance(module, str):
		module = sys.modules[module]
	for param, value in data.items():
		if param in decoders:
			value = decoders[param](value)
		setattr(module, param, value)


def saveJsonConf(module, confPath, params, encoders={}):
	if isinstance(module, str):
		module = sys.modules[module]
	###
	data = {}
	for param in params:
		value = getattr(module, param)
		if param in encoders:
			value = encoders[param](value)
		data[param] = value
	###
	text = dataToPrettyJson(data, sort_keys=True)
	try:
		with open(confPath, "w") as fp:
			fp.write(text)
	except Exception as e:
		log.error(f"failed to save file {confPath!r}: {e}")
		return


def loadModuleJsonConf(module):
	if isinstance(module, str):
		module = sys.modules[module]
	###
	decoders = getattr(module, "confDecoders", {})
	###
	try:
		sysConfPath = module.sysConfPath
	except AttributeError:
		pass
	else:
		loadJsonConf(
			module,
			sysConfPath,
			decoders,
		)
	####
	loadJsonConf(
		module,
		module.confPath,
		decoders,
	)
	# FIXME: should use module.confParams to restrict json keys?


def saveModuleJsonConf(module):
	if isinstance(module, str):
		module = sys.modules[module]
	###
	saveJsonConf(
		module,
		module.confPath,
		module.confParams,
		getattr(module, "confEncoders", {}),
	)
