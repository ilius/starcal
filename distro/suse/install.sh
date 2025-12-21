#!/bin/bash
## makes rpm package and installs it using zypper

## rpmbuild command is provided by package "rpm" that is a base and essential package is SUSE

set -e

function check_pkg(){
	OUT=$(zypper info "$1" | grep 'Installed:')
	if [ "$OUT" = 'Installed: Yes' ] ; then
		echo 'installed'
	elif [ "$OUT" = 'Installed: No' ] ; then
		echo 'not_installed'
	else
		echo "not_found"
	fi
}

if [ "$UID" != "0" ] ; then
	echo "Run this script as root" >&2
	exit 1
fi

if ! git --version ; then
	if ! zypper install git-core ; then
		echo -e "\n\nPlease install git and try again" >&2
		exit 1
	fi
fi
if ! command -v msgfmt ; then
	zypper install gettext
fi


if [ ! -f /usr/bin/python3 ] ; then
	echo "/usr/bin/python3 was not found" >&2
	exit 1
fi
pyCmd=/usr/bin/python3
echo "Using python: \"$pyCmd\""
## --provides and --file-list both work
#pyPkg="`zypper search --match-exact --provides --installed-only \"$pyCmd\" | /bin/grep '^i |' | sed 's/i *| *//' | sed 's/ *|.*//g'`"
# if [ -z "$pyPkg" ] ; then
#	echo "Could not find python package name for \"$pyCmd\"" >&2
#	exit 1
#fi

pkgName=starcal3

myPath=$(realpath "$0")
myDir1=$(dirname "$myPath")
myDir2=$(dirname "$myDir1")
sourceDir=$(dirname "$myDir2")

DTIME=$(/bin/date +%F-%H%M%S)
outDir="$HOME/.${pkgName}/pkgs/suse/$DTIME"
mkdir -p "$outDir"

"$sourceDir/distro/suse/build.sh" "$outDir" "$pyCmd"
pkgPath=$(find "$outDir" -maxdepth 1 -name '*.rpm' | sort | tail -n1)

if [ -z "$pkgPath" ] ; then
	echo "Package build failed" >&2
	exit 1
fi
if [ ! -f "$pkgPath" ] ; then
	echo "Package file $pkgPath does not exit" >&2
	exit 1
fi

echo "Package created in \"$pkgPath\", installing"

zypper install -f --allow-unsigned-rpm "$pkgPath"

#rpm -U --force "$pkgPath" ## its OK when required packages are installed!

if [ "$(check_pkg gnome-shell)" = installed ] ; then
	case "$(check_pkg gnome-shell-extension-topicons)" in
		not_installed)
			zypper install gnome-shell-extension-topicons
			;;
		not_found)
			zypper ar -f http://download.opensuse.org/repositories/home:/PerryWerneck/openSUSE_13.2/ PerryWerneck && \
			zypper refresh && \
			zypper install gnome-shell-extension-topicons
			;;
	esac
fi


