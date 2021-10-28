#!/usr/bin/env python3
import os
from os.path import join
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
		VERSION_GIT_RAW = outputB.decode("utf-8").strip()
	except Exception as e:
		sys.stderr.write(str(e) + "\n")
	else:
		# Python believes:
		# 3.1.12-15-gd50399ea	< 3.1.12
		# 3.1.12dev15+d50399ea	< 3.1.12
		# 3.1.12post15+d50399ea	> 3.1.12
		# so the only way to make it work is to use "post"
		if VERSION_GIT_RAW:
			VERSION_GIT = re.sub(
				'-([0-9]+)-g([0-9a-f]{8})',
				r'post\1+\2',
				VERSION_GIT_RAW,
			)
			if parse_version(VERSION_GIT) > parse_version(VERSION):
				VERSION = VERSION_GIT

print(VERSION)
