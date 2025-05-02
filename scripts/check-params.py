#!/usr/bin/env python3

import os
import sys

rootDir = os.getcwd()

os.environ["STARCAL_NO_LOAD_CONFIG"] = "1"

sys.path.insert(0, rootDir)

from scal3.ui import conf, params

ignoreMissingParams = {
	"localTzHist",
}

attrNames = {name for name in dir(conf) if not name.startswith("_")} - {
	"join",
	"sourceDir",
	"annotations",
	"typing",
}


# paramByName = {p.v3Name: p for p in params.confParamsData}
paramNames = {p.v3Name for p in params.confParamsData}

for name in attrNames - paramNames - ignoreMissingParams:
	print(f"Missing param: {name}")
for name in paramNames - attrNames:
	print(f"Missing conf value: {name}")


for param in params.confParamsData:
	assert isinstance(param.type, str), param.v3Name
	assert param.type, param.v3Name
	if param.v3Name in ignoreMissingParams:
		continue
	value = getattr(conf, param.v3Name)
	# if not isinstance(value, param.type):
	if param.default is not params.NOT_SET:
		assert param.default == value, f"{param.default}!={value} for {param.v3Name}"
		continue
	print(f"name={param.name!r}, v3Name={param.v3Name!r}\n\t\tdefault={value!r},\n")
