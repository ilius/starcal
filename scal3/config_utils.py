from __future__ import annotations

from typing import TYPE_CHECKING, Any

from scal3 import logger
from scal3.property import Property

log = logger.get()

import json
import sys

from scal3.json_utils import dataToPrettyJson

if TYPE_CHECKING:
	from types import ModuleType

__all__ = [
	"loadModuleConfig",
	"loadSingleConfig",
	"saveModuleConfig",
	"saveSingleConfig",
]


def loadSingleConfig(
	module: Any,
	confPath: str,
	params: dict[str, Property],
	decoders: dict | None = None,
) -> None:
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
	if not isinstance(module, str):
		module = str(module)
	assert isinstance(params, dict), repr(params)
	for param, value in data.items():
		if param not in params:
			log.warning(f"Ignoring config option {param} in {module}")
			continue
		if decoders and param in decoders:
			value = decoders[param](value)  # noqa: PLW2901
		prop = params[param]
		assert isinstance(prop, Property), f"{module}.{param}"
		prop.v = value


def saveSingleConfig(
	module: Any,  # noqa: ARG001
	confPath: str,
	params: dict[str, Property],
	encoders: dict | None = None,
) -> None:
	data = {}
	for param, prop in params.items():
		assert isinstance(prop, Property)
		value = prop.v
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


def loadModuleConfig(module: ModuleType | str) -> None:
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
		loadSingleConfig(
			module,
			sysConfPath,
			module.confParams,
			decoders,
		)
	# ----
	loadSingleConfig(
		module,
		module.confPath,
		module.confParams,
		decoders,
	)


def saveModuleConfig(module: ModuleType) -> None:
	if isinstance(module, str):
		module = sys.modules[module]
	# ---
	saveSingleConfig(
		module,
		module.confPath,
		module.confParams,
		getattr(module, "confEncoders", {}),
	)
