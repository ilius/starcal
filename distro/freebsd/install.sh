#!/bin/sh

set -x

if [ "$(id -u)" != "0" ] ; then
	echo "Run this script as root" >&2
	exit 1
fi

if ! which git ; then
	pkg install --yes git
fi

# it works without bash now

if ! which python3 ; then
	pkg install --yes python3
fi

PYV=$(python3 -c 'import sys;v=sys.version_info;print(f"py{v.major}{v.minor}")')

# you can run "pkg install -f ..." to re-install a package
# if it's installed with pip3, pkg will still install it without "-f"

pkg install \
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

# /usr/sbin/ntpdate exists by default, but couldn't figure out which package
# does it belong to

# pygobject			https://www.freshports.org/devel/py-gobject/
# pycairo			https://www.freshports.org/graphics/py-cairo/
# httplib2			https://www.freshports.org/www/py-httplib2/
# python-dateutil	https://www.freshports.org/devel/py-dateutil/
# psutil			https://www.freshports.org/sysutils/py-psutil
# cachetools		https://freebsd.pkgs.org/12/freebsd-aarch64/py38-cachetools-4.2.2.txz.html
# requests			https://www.freshports.org/www/py-requests
# ujson				https://www.freshports.org/devel/py-ujson/
# python-igraph		https://www.freshports.org/math/py-python-igraph/
# pygit2			https://www.freshports.org/devel/py-pygit2


myPath=$(realpath "$0")
myDir1=$(dirname "$myPath")
myDir2=$(dirname "$myDir1")
sourceDir=$(dirname "$myDir2")

"$sourceDir/distro/base/install.py" --system

# "install" script does not work in FreeBSD 13.0
# the "case" bash command acts very strangely!
# that's why we use "install.py" script instead

# looks like we can install all dependencies with "pkg" command
# so we do not need to install pip3 then use "install-pip"
# but if you want to install or upgrade pip3:
# 	python3 -m ensurepip
# 	pip3 install -U pip
