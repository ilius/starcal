import io
import os
import sys
from os.path import dirname, join

rootDir = dirname(dirname(dirname(__file__)))

os.environ["STARCAL_NO_LOAD_CONFIG"] = "1"

sys.path.insert(0, rootDir)

from scal3.timeline import params


def genParamDict(names: list[str]) -> str:
	return "{" + "\n".join([f"\t{name!r}: {name}," for name in names]) + "\n}\n"


confParams = sorted([p.v3Name for p in params.confParamsData])
all_names = sorted(confParams + ["confParams"])

output = io.StringIO()

output.write(
	"from __future__ import annotations\n\n"
	"import typing\n"
	"from scal3.color_utils import RGB, RGBA\n"
	"from scal3.property import Property\n\n"
	"if typing.TYPE_CHECKING:\n"
	"\tfrom typing import Any\n\n"
	"\tfrom scal3.color_utils import ColorType\n"
	"\tfrom scal3.font import Font\n",
)
output.write(f"__all__ = {all_names!r}\n\n")

for p in params.confParamsData:
	assert p.default is not params.NOT_SET
	value = p.default
	output.write(f"{p.v3Name}: Property[{p.type}] = Property({value!r})" + "\n")


output.write("\n\n")

output.write("confParams: dict[str, Property] = " + genParamDict(confParams))

output.write("\n")

with open(join(rootDir, "scal3/timeline/conf.py"), "w", encoding="utf-8") as file:
	file.write(output.getvalue())
