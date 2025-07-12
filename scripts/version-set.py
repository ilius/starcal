#!/usr/bin/env python3

import sys
from datetime import datetime
from os.path import abspath, dirname, join

from packaging.version import parse


def main() -> None:
	version = sys.argv[1]
	parse(version)
	versionQuoted = f'"{version}"'
	rootDir = dirname(dirname(abspath(__file__)))
	replaceVar(join(rootDir, "scal3/app_info.py"), "VERSION_TAG", versionQuoted)
	# replaceVar(join(rootDir, "pyproject.toml"), "version", versionQuoted)

	# update copyright year number
	for fname in ("about", "license-dialog"):
		with open(fname, encoding="utf-8") as file:
			text = file.read()
		pos = text.find("© ")
		text = text[: pos + 7] + str(datetime.now().year) + text[pos + 11 :]
		with open(fname, "w", encoding="utf-8") as file:
			file.write(text)


def replaceVar(fname: str, name: str, value: str) -> None:
	prefix = name + ": "
	lines = []
	with open(fname, encoding="utf-8") as _file:
		for _line in _file:
			line = _line
			if line.startswith(prefix):
				line = f"{name}: Final[str] = {value}\n"
			lines.append(line)
	with open(fname, mode="w", encoding="utf-8") as _file:
		_file.writelines(lines)


if __name__ == "__main__":
	main()
