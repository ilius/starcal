#!/usr/bin/python3

from __future__ import annotations

import os
import sys
from os.path import dirname, join

rootDir = dirname(dirname(__file__))
gtkDir = join(rootDir, "scal3", "ui_gtk")

os.environ["STARCAL_NO_LOAD_CONFIG"] = "1"

sys.path.insert(0, rootDir)

from typing import TYPE_CHECKING

from scal3.ui import options

if TYPE_CHECKING:
	from collections.abc import Iterable


def searchOption(opt: options.OptionData) -> None:
	name = opt.v3Name
	# print(name)
	for fpath in listFilesRecursive(gtkDir):
		with open(fpath, encoding="utf-8") as file:
			text = file.read()
		index = text.find("\t" + f"option=conf.{name}")
		if index < 0:
			continue
		start = text.rfind("OptionUI(", 0, index)
		assert start > 0
		boundsStart = text.find("bounds=", start)
		if boundsStart < 0:
			print(f"no bounds for option conf.{name}")
			continue
		boundsEnd = text.find("\n", boundsStart)
		assert boundsEnd > 0
		bounds = text[boundsStart:boundsEnd].rstrip(",")
		# print(name)
		# print("\t" + bounds)
		stepStart = text.find("step=", start)
		if stepStart < 0:
			print(f"no step for option conf.{name}")
			continue
		stepEnd = text.find("\n", stepStart)
		assert stepEnd > 0
		step = text[stepStart:stepEnd].rstrip(",")
		# print("\t" + step)
		_, _, boundsValue = bounds.partition("=")
		_, _, stepValue = step.partition("=")
		boundsValue = boundsValue.strip(",()")

		if opt.type == "float":
			digitsStart = text.find("digits=", start)
			assert digitsStart > 0, f"{name=}"
			digitsEnd = text.find("\n", digitsStart)
			assert digitsEnd > 0
			digitsStr = text[digitsStart:digitsEnd].rstrip(",")
			_, _, digitsValue = digitsStr.partition("=")
			valid = f"FloatSpin({boundsValue}, {stepValue}, {digitsValue})"
		else:
			valid = f"IntSpin({boundsValue}, {stepValue})"

		if opt.valid:
			if opt.valid == valid:
				print(f"OK: {name}")
			else:
				print(f"ERROR: {name=}, {valid=}")
			continue
		print(f"\t{name=}, {valid=}")


def listFilesRecursive(direc: str) -> Iterable[str]:
	"""
	Iterate over full paths of all files (directly/indirectly)
	inside given directory.
	"""
	for root, _subDirs, files in os.walk(direc):
		for fname in files:
			yield join(root, fname)


for opt in options.confOptionsData:
	if opt.type not in {"int", "float"}:
		continue
	searchOption(opt)
