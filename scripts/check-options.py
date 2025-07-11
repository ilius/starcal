#!/usr/bin/env python3

import os
import sys

rootDir = os.getcwd()

os.environ["STARCAL_NO_LOAD_CONFIG"] = "1"

sys.path.insert(0, rootDir)

from scal3.ui import conf, options

ignoreMissingOptions = {
	"localTzHist",
}

attrNames = {name for name in dir(conf) if not name.startswith("_")} - {
	"join",
	"sourceDir",
	"annotations",
	"typing",
}


# optionByName = {p.v3Name: p for p in options.confOptionsData}
optionNames = {p.v3Name for p in options.confOptionsData}

for name in attrNames - optionNames - ignoreMissingOptions:
	print(f"Missing option: {name}")
for name in optionNames - attrNames:
	print(f"Missing conf value: {name}")


for option in options.confOptionsData:
	assert isinstance(option.type, str), option.v3Name
	assert option.type, option.v3Name
	if option.v3Name in ignoreMissingOptions:
		continue
	value = getattr(conf, option.v3Name)
	# if not isinstance(value, option.type):
	if option.default is not options.NOT_SET:
		assert option.default == value, f"{option.default}!={value} for {option.v3Name}"
		continue
	print(f"name={option.name!r}, v3Name={option.v3Name!r}\n\t\tdefault={value!r},\n")
