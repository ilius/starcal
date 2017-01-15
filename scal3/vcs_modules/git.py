# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux

from os.path import join
from subprocess import Popen, PIPE

from scal3.utils import toStr
from scal3.time_utils import getEpochFromJd, encodeJd


def prepareObj(obj):
	pass


def clearObj(obj):
	pass


def decodeStatLine(line):
	if not line:
		return 0, 0, 0
	files_changed, insertions, deletions = 0, 0, 0
	for section in line.split(","):
		parts = section.strip().split(" ")
		if len(parts) < 2:
			continue
		try:
			num = int(parts[0])
		except:
			print("bad section: %r, stat line=%r" % (section, line))
		else:
			action = parts[-1].strip()
			if "changed" in action:
				files_changed = num
			elif "insertions" in action:
				insertions = num
			elif "deletions" in action:
				deletions = num
	return files_changed, insertions, deletions


def getCommitList(obj, startJd=None, endJd=None):
	"""
	returns a list of (epoch, commit_id) tuples
	"""
	cmd = [
		"git",
		"--git-dir", join(obj.vcsDir, ".git"),
		"log",
		"--format=%ct %H",## or "--format=%ct %H"
	]
	if startJd is not None:
		cmd += [
			"--since",
			encodeJd(startJd),
		]
	if endJd is not None:
		cmd += [
			"--until",
			encodeJd(endJd),
		]
	data = []
	for line in Popen(cmd, stdout=PIPE).stdout:
		line = toStr(line)
		parts = line.strip().split(" ")
		data.append((
			int(parts[0]),
			parts[1],
		))
	return data


def getCommitInfo(obj, commid_id):
	cmd = [
		"git",
		"--git-dir", join(obj.vcsDir, ".git"),
		"log",
		"-1",
		"--format=%at\n%cn <%ce>\n%h\n%s",
		commid_id,
	]
	parts = Popen(cmd, stdout=PIPE).stdout.read().strip().split("\n")
	if not parts:
		return
	return {
		"epoch": int(parts[0]),
		"author": parts[1],
		"shortHash": parts[2],
		"summary": parts[3],
		"description": "\n".join(parts[4:]),
	}


def getShortStatLine(obj, prevId, thisId):
	"""
	returns str
	"""
	cmd = [
		"git",
		"--git-dir", join(obj.vcsDir, ".git"),
		"diff",
		"--shortstat",
		prevId,
		thisId,
	]
	return toStr(Popen(cmd, stdout=PIPE).stdout.read().strip())


def getShortStat(obj, prevId, thisId):
	return decodeStatLine(getShortStatLine(obj, prevId, thisId))


def getCommitShortStatLine(obj, commit_id):
	"""
	returns str
	"""
	lines = Popen([
		"git",
		"--git-dir", join(obj.vcsDir, ".git"),
		"log",
		"--shortstat",
		"-1",
		"--pretty=format:",
		commit_id,
	], stdout=PIPE).stdout.readlines()
	if lines:
		return lines[-1].strip()
	return ""


def getCommitShortStat(obj, commit_id):
	"""
	returns (files_changed, insertions, deletions)
	"""
	return decodeStatLine(getCommitShortStatLine(obj.vcsDir, commit_id))


def getTagList(obj, startJd, endJd):
	"""
	returns a list of (epoch, tag_name) tuples
	"""
	startEpoch = getEpochFromJd(startJd)
	endEpoch = getEpochFromJd(endJd)
	cmd = [
		"git",
		"--git-dir", join(obj.vcsDir, ".git"),
		"tag",
	]
	data = []
	for line in Popen(cmd, stdout=PIPE).stdout:
		tag = line.strip()
		if not tag:
			continue
		line = Popen([
			"git",
			"--git-dir", join(obj.vcsDir, ".git"),
			"log",
			"-1",
			tag,
			"--pretty=%ct",
		], stdout=PIPE).stdout.read().strip()
		epoch = int(line)
		if epoch < startEpoch:
			continue
		if epoch >= endEpoch:
			break
		data.append((
			epoch,
			tag,
		))
	return data


def getTagShortStatLine(obj, prevTag, tag):
	return getShortStatLine(obj, prevTag, tag)


def getFirstCommitEpoch(obj):
	return int(
		Popen([
			"git",
			"--git-dir", join(obj.vcsDir, ".git"),
			"rev-list",
			"--max-parents=0",
			"HEAD",
			"--format=%ct",
		], stdout=PIPE).stdout.readlines()[1].strip()
	)


def getLastCommitEpoch(obj):
	return int(Popen([
		"git",
		"--git-dir", join(obj.vcsDir, ".git"),
		"log",
		"-1",
		"--format=%ct",
	], stdout=PIPE).stdout.read().strip())


def getLastCommitIdUntilJd(obj, jd):
	return Popen([
		"git",
		"--git-dir", join(obj.vcsDir, ".git"),
		"log",
		"--until", encodeJd(jd),
		"-1",
		"--format=%H",
	], stdout=PIPE).stdout.read().strip()
