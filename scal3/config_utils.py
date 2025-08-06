from __future__ import annotations

from typing import TYPE_CHECKING, Any

from scal3 import logger
from scal3.option import Option

log = logger.get()

import json

from scal3.json_utils import dataToPrettyJson

if TYPE_CHECKING:
	from collections.abc import Callable

__all__ = [
	"loadModuleConfig",
	"loadSingleConfig",
	"saveSingleConfig",
]


def loadSingleConfig(
	confPath: str,
	options: dict[str, Option[Any]],
	decoders: dict[str, Callable[[Any], Any]] | None = None,
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
	assert isinstance(options, dict), f"{options=}"
	for optName, value_ in data.items():
		if optName not in options:
			log.warning(f"Ignoring config option {optName}")
			continue
		value = value_
		if decoders and optName in decoders:
			value = decoders[optName](value)
		option = options[optName]
		assert isinstance(option, Option), f"{option=}, {optName=}"
		option.v = value


def saveSingleConfig(
	confPath: str,
	options: dict[str, Option[Any]],
	encoders: dict[str, Callable[[Any], Any]] | None = None,
) -> None:
	data = {}
	for optName, option in options.items():
		assert isinstance(option, Option), f"{option=}, {optName=}"
		value = option.v
		if encoders and optName in encoders:
			value = encoders[optName](value)
		data[optName] = value
	# ---
	text = dataToPrettyJson(data, sort_keys=True)
	try:
		with open(confPath, "w", encoding="utf-8") as fp:
			fp.write(text)
	except Exception as e:
		log.error(f"failed to save file {confPath!r}: {e}")
		return


def loadModuleConfig(
	confPath: str,
	sysConfPath: str | None,
	options: dict[str, Option[Any]],
	decoders: dict[str, Callable[[Any], Any]] | None = None,
) -> None:
	if sysConfPath:
		loadSingleConfig(
			sysConfPath,
			options,
			decoders,
		)
	# ----
	loadSingleConfig(
		confPath,
		options,
		decoders,
	)
