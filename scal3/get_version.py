#!/usr/bin/env python3
import os
import sys
import subprocess

srcDir = os.path.dirname(__file__)
rootDir = os.path.dirname(srcDir)

gitDir = os.path.join(rootDir, ".git")
if os.path.isdir(gitDir):
	try:
		outputB, error = subprocess.Popen(
			[
				"git",
				"--git-dir", gitDir,
				"describe",
				"--tags",
				"--always",
			],
			stdout=subprocess.PIPE,
		).communicate()
		# if error == None:
		print(outputB.decode("utf-8").strip())
		sys.exit(0)
	except Exception as e:
		sys.stderr.write(str(e) + "\n")


VERSION = ""
fp = open("%s/core.py" % srcDir)
while True:
	line = fp.readline()
	if line.startswith("VERSION"):
		exec(line)
		break
print(VERSION)

