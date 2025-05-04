import os
import sys
from os.path import join

rootDir = os.getcwd()

sys.path.insert(0, rootDir)

from scal3.ui import conf

attrNames = {name for name in dir(conf) if not name.startswith("_")} - {
	"join",
	"sourceDir",
}


def fixFile(fpath: str) -> bool:
	with open(fpath, encoding="utf-8") as file:
		text = file.read()
	if "ui." not in text:
		return False
	text2 = text
	for attr in attrNames:
		text2 = text2.replace("ui." + attr, "conf." + attr)
	if text2 == text:
		return False
	i = text2.rfind("\nimport")
	if i == -1:
		text2 = "from scal3.ui import conf\n" + text2
	else:
		text2 = text2[:i] + "\nfrom scal3.ui import conf" + text2[i:]
	with open(fpath, "w", encoding="utf-8") as file:
		file.write(text2)
	return True


def scanDirAndfix() -> None:
	for root, _, files in os.walk(rootDir + "/scal3"):
		for fname in files:
			if not fname.endswith(".py"):
				continue
			fpath = join(root, fname)
			if fixFile(fpath):
				print("Wrote:", fpath)
			# else:
			# print("Skipped:", fpath)


scanDirAndfix()
