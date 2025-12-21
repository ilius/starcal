#!/bin/sh

set -x

if [ "$(id -u)" != "0" ] ; then
	echo "Run this script as root" >&2
	exit 1
fi

if ! command -v git ; then
	mport install --yes git
fi

# it works without bash now

if ! command -v python3 ; then
	mport install --yes python3
fi

PYV=$(python3 -c 'import sys;v=sys.version_info;print(f"py{v.major}{v.minor}")')


mport install \
	gettext \
	gtksourceview4 \
	"$PYV-gobject3" \
	"$PYV-cairo" \
	"$PYV-httplib2" \
	"$PYV-dateutil" \
	"$PYV-psutil" \
	"$PYV-cachetools" \
	"$PYV-requests" \
	"$PYV-ujson" \
	"$PYV-python-igraph" \
	"$PYV-pygit2"


myPath=$(realpath "$0")
myDir1=$(dirname "$myPath")
myDir2=$(dirname "$myDir1")
sourceDir=$(dirname "$myDir2")

"$sourceDir/distro/base/install.py" --system

# "install" script does not work in FreeBSD 13.0
# the "case" bash command acts very strangely!
# that's why we use "install.py" script instead

# looks like we can install all dependencies with "mport" command
# so we do not need to install pip3 then use "install-pip"
# but if you want to install or upgrade pip3:
# 	python3 -m ensurepip
# 	pip3 install -U pip
