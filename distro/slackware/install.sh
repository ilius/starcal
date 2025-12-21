#!/bin/bash
set -e

if [ "$UID" != "0" ] ; then
	echo "Run this script as root" >&2
	exit 1
fi

SLACKPKG=slackpkg-2.83.0-noarch-4.txz

if command -v slackpkg ; then
	slackpkg install pygobject3 pycairo python-dateutil
	# TODO: gtksource-4 / gtksourceview4
else
	curl -o $SLACKPKG "https://slackpkg.org/stable/$SLACKPKG"
	installpkg $SLACKPKG
	# need to edit /etc/slackpkg/mirrors and then run:
	# slackpkg update
fi

if ! command -v pip3 ; then
	slackpkg install python-pip
fi

myPath=$(realpath "$0")
myDir1=$(dirname "$myPath")
myDir2=$(dirname "$myDir1")
sourceDir=$(dirname "$myDir2")

"$sourceDir/distro/base/install.sh" --system

