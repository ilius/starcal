#!/bin/bash
## makes rpm package and installs it using yum
set -e

## yum install @development-tools
## yum install rpm-build rpmdevtools rpmlint mock


if [ "$UID" != "0" ] ; then
	echo "Run this script as root" >&2
	exit 1
fi

if ! git --version ; then
	if ! dnf install git-core ; then
		echo -e "\n\nPlease install git and try again" >&2
		exit 1
	fi
fi


if [ ! -f /usr/bin/python3 ] ; then
	echo "/usr/bin/python3 was not found" >&2
	exit 1
fi
pyCmd=/usr/bin/python3
echo "Using python: \"$pyCmd\""

pkgName=starcal3

myPath=$(realpath "$0")
myDir1=$(dirname "$myPath")
myDir2=$(dirname "$myDir1")
sourceDir=$(dirname "$myDir2")

DTIME=$(/bin/date +%F-%H%M%S)
outDir="$HOME/.${pkgName}/pkgs/fedora/$DTIME"
mkdir -p "$outDir"

if ! which rpmbuild ; then
	if which dnf ; then
		dnf install rpm-build
	elif which yum ; then
		yum install rpm-build
	else
		echo "No 'dnf' nor 'yum' commands were found" >&2
		exit 1
	fi
fi

"$sourceDir/distro/fedora/build.sh" "$outDir" "$pyCmd"
pkgPath=$(find "$outDir" -maxdepth 1 -name '*.rpm' | sort | tail -n1)

if [ ! -f "$pkgPath" ] ; then
	echo "rpmbuild exited with success status, but no package file was found" >&2
	exit 1
fi

echo "Package created in \"$pkgPath\", installing"
dnf remove -y $pkgName >/dev/null 2>&1 || true
dnf install --nogpgcheck "$pkgPath"
#rpm -U --force "$pkgPath" ## its OK when required packages are installed!

