#!/usr/bin/env python3
# mypy: ignore-errors

from __future__ import annotations

from os.path import abspath, dirname, join

from lxml import etree as ET

myDir = dirname(abspath(__file__))
rootDir = dirname(myDir)

with open(join(rootDir, "resources.xml"), encoding="utf-8") as _file:
	root = ET.fromstring(_file.read())


for res in root.getchildren():
	path = res.attrib.get("path", None)
	if not path:
		continue
	if not path.endswith(".png"):
		continue
	author = res.find("author")
	if author is not None:
		if author.text == "Saeed Rasooli":
			continue
		# print(author.text)
	comment = res.find("comment")
	if comment is not None and comment.text:
		if comment.text.startswith("See file "):
			# converted from a svg file that is in repo
			continue
	sourceEl = res.find("source")
	if sourceEl is None:
		print(f"--- no source for: {path}")
		continue
	source = sourceEl.text
	if not source:
		print(f"--- no source for: {path}")
		continue
	if not source.startswith(("http://", "https://")):
		print(f"--- {path=}, {source=}  (bad url)")
	if not source.endswith((".svg", ".svgz")):
		print(f"--- {path=}, {source=}  (bad ext)")
	print(f"{path}\t	{source}")


# --- no source for: pixmaps/screenruler-redline.png
