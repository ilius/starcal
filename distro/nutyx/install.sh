#!/usr/bin/env bash

if [ "$UID" != "0" ] ; then
	echo "Run this script as root" >&2
	exit 1
fi

if ! which python3 ; then
	cards install python
fi


PIP=pip3
if [ -n "$1" ] ; then
	PIP="python$1 -m pip"
	shift
fi

cards sync

cards install python-gobject
cards install gtksourceview4
cards install python-cairo
cards install dejavu-ttf
cards install python-requests
cards install python-psutil


$PIP install httplib2
$PIP install cachetools

$PIP install python-igraph
$PIP install pygit2


myPath=$(realpath "$0")
myDir1=$(dirname "$myPath")
myDir2=$(dirname "$myDir1")
sourceDir=$(dirname "$myDir2")

"$sourceDir/distro/base/install.sh" --system

