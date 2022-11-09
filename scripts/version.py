#!/usr/bin/env python3
import os
from os.path import join, isfile
import sys
import subprocess
import re

try:
	from packaging.version import parse as parse_version
except ImportError:
	from pkg_resources import parse_version

scriptsDir = os.path.dirname(__file__)
rootDir = os.path.dirname(scriptsDir)
scalDir = join(rootDir, "scal3")

if isfile(join(rootDir, "VERSION")):
	with open(join(rootDir, "VERSION")) as _file:
		print(_file.read().strip())
		sys.exit(0)

VERSION = ""
fp = open("%s/core.py" % scalDir)
while True:
	line = fp.readline()
	if line.startswith("VERSION"):
		exec(line)
		break

gitDir = os.path.join(rootDir, ".git")
if os.path.isdir(gitDir):
	try:
		outputB, error = subprocess.Popen(
			[
				"git",
				"--git-dir", gitDir,
				"describe",
				"--always",
			],
			stdout=subprocess.PIPE,
		).communicate()
		# if error == None:
		gitVersionRaw = outputB.decode("utf-8").strip()
	except Exception as e:
		sys.stderr.write(str(e) + "\n")
	else:
		# Python believes:
		# 3.1.12-15-gd50399ea	< 3.1.12
		# 3.1.12dev15+d50399ea	< 3.1.12
		# 3.1.12post15+d50399ea	> 3.1.12
		# so the only way to make it work is to use "post"
		if gitVersionRaw:
			gitVersion = re.sub(
				'-([0-9]+)-g([0-9a-f]{6,8})',
				r'post\1+\2',
				gitVersionRaw,
			)
			if parse_version(gitVersion) > parse_version(VERSION):
				VERSION = gitVersion

print(VERSION)
