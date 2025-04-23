from __future__ import annotations

from scal3 import logger

log = logger.get()

import json
import sys
from typing import TYPE_CHECKING

from scal3.json_utils import dataToPrettyJson

if TYPE_CHECKING:
	from collections.abc import Iterable

__all__ = [
	"loadModuleConfig",
	"loadSingleConfig",
	"saveModuleConfig",
	"saveSingleConfig",
]


def loadSingleConfig(
	module,
	confPath: str,
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
	if isinstance(module, str):
		module = sys.modules[module]
	for param, value in data.items():
		if decoders and param in decoders:
			value = decoders[param](value)  # noqa: PLW2901
		setattr(module, param, value)


def saveSingleConfig(
	module,
	confPath: str,
	params: Iterable[str],
	encoders: dict | None = None,
) -> None:
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


def loadModuleConfig(module):
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
			decoders,
		)
	# ----
	loadSingleConfig(
		module,
		module.confPath,
		decoders,
	)
	# FIXME: should use module.confParams to restrict json keys?


def saveModuleConfig(module):
	if isinstance(module, str):
		module = sys.modules[module]
	# ---
	saveSingleConfig(
		module,
		module.confPath,
		module.confParams,
		getattr(module, "confEncoders", {}),
	)
