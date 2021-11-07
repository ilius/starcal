#!/bin/bash
## makes PKGUILD and builds it (without root access), then installs it (prompts for password if necessary)
set -e

initPwd=$PWD

sudo pacman -Sy

if ! git --version ; then
	if ! sudo pacman -S git ; then
		echo -e "\n\nPlease install git and try again" >&2
		exit 1
	fi
fi

pkgName=starcal3

myPath=$(realpath "$0")
myDir1=$(dirname "$myPath")
myDir2=$(dirname "$myDir1")
sourceDir=$(dirname "$myDir2")

outDir="$HOME/.${pkgName}/pkgs/archlinux/`/bin/date +%F-%H%M%S`"
mkdir -p "$outDir"

pyCmd=$(ls -1 /usr/bin/python3.? | tail -n1)
if [ -z "$pyCmd" ] ; then
	echo "Could not find python3.x binary" >&2
	exit 1
fi
echo "Using python: \"$pyCmd\""

"$sourceDir/distro/archlinux/build.sh" "$outDir" "$pyCmd"
pkgPath=`ls -1 "$outDir"/*.pkg.tar* | tail -n1`

sudo pacman -U "$pkgPath"

cd "$initPwd"
