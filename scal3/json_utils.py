from __future__ import annotations

from scal3 import logger

log = logger.get()

import json
import sys
from collections import OrderedDict
from json import JSONEncoder
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Sequence

__all__ = [
	"dataToCompactJson",
	"dataToPrettyJson",
	"jsonToData",
	"jsonToOrderedData",
	"loadJsonConf",
	"loadModuleJsonConf",
	"saveJsonConf",
	"saveModuleJsonConf",
]


def _default(_self, obj):
	return getattr(obj.__class__, "to_json", _default.default)(obj)


_default.default = JSONEncoder().default
JSONEncoder.default = _default


def dataToPrettyJson(data, ensure_ascii=False, sort_keys=False):
	try:
		return json.dumps(
			data,
			indent="\t",
			ensure_ascii=ensure_ascii,
			sort_keys=sort_keys,
		)
	except Exception:
		log.exception(f"{data =}")


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


# -------------------------------


def loadJsonConf(module, confPath, decoders: dict | None = None):
	from os.path import isfile

	# ---
	if not isfile(confPath):
		return
	# ---
	try:
		with open(confPath, encoding="utf-8") as fp:
			text = fp.read()
	except Exception as e:
		log.error(f"failed to read file {confPath!r}: {e}")
		return
	# ---
	try:
		data = json.loads(text)
	except Exception as e:
		log.error(f"invalid json file {confPath!r}: {e}")
		return
	# ---
	if isinstance(module, str):
		module = sys.modules[module]
	for param, value in data.items():
		if decoders and param in decoders:
			value = decoders[param](value)  # noqa: PLW2901
		setattr(module, param, value)


def saveJsonConf(
	module,
	confPath: str,
	params: Sequence[str] | dict[str, str],
	encoders: dict | None = None,
):
	if isinstance(module, str):
		module = sys.modules[module]
	# ---
	data = {}
	for param in params:
		value = getattr(module, param)
		if encoders and param in encoders:
			value = encoders[param](value)
		data[param] = value
	# ---
	text = dataToPrettyJson(data, sort_keys=True)
	try:
		with open(confPath, "w", encoding="utf-8") as fp:
			fp.write(text)
	except Exception as e:
		log.error(f"failed to save file {confPath!r}: {e}")
		return


def loadModuleJsonConf(module):
	if isinstance(module, str):
		module = sys.modules[module]
	# ---
	decoders = getattr(module, "confDecoders", {})
	# ---
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
	# ----
	loadJsonConf(
		module,
		module.confPath,
		decoders,
	)
	# FIXME: should use module.confParams to restrict json keys?


def saveModuleJsonConf(module):
	if isinstance(module, str):
		module = sys.modules[module]
	# ---
	saveJsonConf(
		module,
		module.confPath,
		module.confParams,
		getattr(module, "confEncoders", {}),
	)
