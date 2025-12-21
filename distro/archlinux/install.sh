#!/bin/bash
## makes PKGUILD and builds it (without root access), then installs it (prompts for password if necessary)
set -e

initPwd=$PWD

sudo pacman -Sy
sudo pacman -S archlinux-keyring

if ! git --version ; then
	if ! sudo pacman -S git ; then
		echo -e "\n\nPlease install git and try again" >&2
		exit 1
	fi
fi
if ! command -v msgfmt ; then
	pacman -S gettext
fi


pkgName=starcal3

myPath=$(realpath "$0")
myDir1=$(dirname "$myPath")
myDir2=$(dirname "$myDir1")
sourceDir=$(dirname "$myDir2")

DTIME=$(/bin/date +%F-%H%M%S)
outDir="$HOME/.${pkgName}/pkgs/archlinux/$DTIME"
mkdir -p "$outDir"

pyCmd=$(realpath /usr/bin/python3)
if [ -z "$pyCmd" ] ; then
	echo "Could not find python3.x binary" >&2
	exit 1
fi
echo "Using python: \"$pyCmd\""

"$sourceDir/distro/archlinux/build.sh" "$outDir" "$pyCmd"
pkgPath=$(find "$outDir" -maxdepth 1 -name '*.pkg.tar*' | sort | tail -n1)

sudo pacman -U "$pkgPath"

cd "$initPwd"
