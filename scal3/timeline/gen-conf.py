import io
import os
import sys
from os.path import dirname, join

rootDir = dirname(dirname(dirname(__file__)))

os.environ["STARCAL_NO_LOAD_CONFIG"] = "1"

sys.path.insert(0, rootDir)

from scal3.timeline import options


def genParamDict(names: list[str]) -> str:
	return "{" + "\n".join([f"\t{name!r}: {name}," for name in names]) + "\n}\n"


confOptions = sorted([opt.v3Name for opt in options.confOptionsData])
all_names = sorted(confOptions + ["confOptions"])

output = io.StringIO()

output.write(
	"from __future__ import annotations\n\n"
	"import typing\n"
	"from scal3.color_utils import RGB, RGBA\n"
	"from scal3.option import StrDictOption, ListOption, Option\n\n"
	"if typing.TYPE_CHECKING:\n"
	"\tfrom typing import Any, Final\n\n"
	"\tfrom scal3.color_utils import ColorType\n"
	"\tfrom scal3.font import Font\n",
)
output.write(f"__all__ = {all_names!r}\n\n")

for p in options.confOptionsData:
	assert p.default is not options.NOT_SET
	value = p.default
	if p.type.startswith("list["):
		itemType = p.type[5:-1]
		output.write(
			f"{p.v3Name}: Final[ListOption[{itemType}]] = ListOption({value!r})\n"
		)
		continue
	if p.type.startswith("dict[str, "):
		itemType = p.type[10:-1]
		output.write(
			f"{p.v3Name}: Final[StrDictOption[{itemType}]] = StrDictOption({value!r})\n"
		)
		continue
	output.write(f"{p.v3Name}: Final[Option[{p.type}]] = Option({value!r})" + "\n")


output.write("\n\n")

output.write("confOptions: dict[str, Option[Any]] = " + genParamDict(confOptions))

output.write("\n")

with open(join(rootDir, "scal3/timeline/conf.py"), "w", encoding="utf-8") as file:
	file.write(output.getvalue())
