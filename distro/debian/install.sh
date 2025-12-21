#!/bin/bash
## This script builds DEB package on a debian-based distribution
## (like debian, ubuntu, mint, ...) and installs the package
set -e

function installPackage(){
	# must run `set +e` before running this function
	pkgPath="$1"
	pkgPathAbs=$(realpath "$pkgPath")
	if apt-get install --reinstall "$pkgPathAbs" ; then
		return 0
	fi
	if [ -f /usr/bin/apt ] ; then
		/usr/bin/apt reinstall "$pkgPath" 2>/tmp/starcal-apt-error
		aptExitCode="$?"
		if [[ $aptExitCode == "0" ]] ; then
			return 0
		fi
		cat /tmp/starcal-apt-error
		rm /tmp/starcal-apt-error
		if [[ $aptExitCode == "1" ]] ; then
			# user answered No, abort installation
			return $aptExitCode
		fi
	fi
	dpkg -i "$pkgPath" || apt-get -f install
}

if [ "$UID" != "0" ] ; then
	echo "Run this script as root" >&2
	exit 1
fi

if ! git --version ; then
	if ! apt-get install git ; then
		echo -e "\n\nPlease install git and try again" >&2
		exit 1
	fi
fi
if ! command -v msgfmt ; then
	apt-get install gettext
fi

pkgName=starcal3

myPath=$(realpath "$0")
myDir1=$(dirname "$myPath")
myDir2=$(dirname "$myDir1")
sourceDir=$(dirname "$myDir2")

DTIME=$(/bin/date +%F-%H%M%S)
outDir="$HOME/.${pkgName}/pkgs/debian/$DTIME"
mkdir -p "$outDir"

if "$sourceDir/distro/debian/build.sh" "$outDir" ; then
	pkgPath=$(find "$outDir" -maxdepth 1 -name '*.deb' | sort | tail -n1)
	echo "Package file $pkgPath created, installing..."
	set +e
	installPackage "$pkgPath"
fi
