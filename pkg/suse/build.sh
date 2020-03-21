#!/bin/bash
set -e

outDir="$1"
if [ -z "$outDir" ] ; then
	echo "OUT_DIR argument is missing"
	echo "Usage: $0 OUT_DIR PYTHON_COMMAND"
	exit 1
fi
if [ ! -d "$outDir" ] ; then
	echo "Directory not found: $outDir"
	echo "Usage: $0 OUT_DIR PYTHON_COMMAND"
	exit 1
fi

pyCmd="$2"
if [ -z "$pyCmd" ] ; then
	echo "PYTHON_COMMAND argument is missing"
	echo "Usage: $0 OUT_DIR PYTHON_COMMAND"
	exit 1
fi


myPath=$(realpath "$0")

pkgName=starcal3
iconName=starcal32.png

myDir="`dirname \"$myPath\"`"
pkgDir="`dirname \"$myDir\"`"
sourceDir="`dirname \"$pkgDir\"`"
#"$sourceDir/scripts/assert_python3"

"$sourceDir/fetch" || echo "WARNING: failed to fetch tags"
version=`"$sourceDir/scripts/version" | sed 's/\-/_/g'`

#echo "myPath=$myPath"
#echo "sourceDir=$sourceDir"
#echo version=$version


requires=("$pyCmd")

# Confirmed: all following 5 packages are required!
requires+=('typelib(Gtk) = 3.0' 'typelib(Gdk) = 3.0')
requires+=('typelib(GdkPixbuf) = 2.0')
requires+=('python3-gobject >= 3.24') ## The new gobject introspection
requires+=('python3-gobject-Gdk')
requires+=('python3-gobject-cairo')
requires+=('python3-cairo')

requires+=('python3-httplib2')
requires+=('python3-dateutil')
requires+=('python3-psutil')
requires+=('python3-requests')
#requires+=('python3-gflags') # for google api client


## Recommended Packages are treated as strict dependency in openSUSE by default
## unless you uncheck this in Software Management:
## [ ] Dependencies -> Install Recommended Packages

recommends=()
recommends+=('typelib(AppIndicator3)')
#recommends+=('python3-igraph')
recommends+=('openssh-askpass-gnome')
recommends+=('python3-pygit2')

## The package for AppIndicator is: typelib-1_0-AppIndicator3-0_1
## Which provides: typelib(AppIndicator3) = 0.1

requires_str="Requires: ${requires[@]}"
recommends_str="Recommends: ${recommends[@]}"

#echo "$requires_str"; exit



echo "Name: $pkgName
Version: $version
Release: 1
Summary: A full-featured international calendar written in Python

Group: User Interface/Desktops
License: GPLv3+
URL: http://ilius.github.io/starcal

$requires_str
$recommends_str

BuildArch: noarch

%description
StarCalendar is a full-featured international calendar written in Python,
using Gtk3-based interface, that supports Jalai(Iranian), Hijri(Islamic),
and Indian National calendars, as well as common English(Gregorian) calendar

%install
\"$sourceDir/install\" \"%{buildroot}\" --for-pkg --prefix=%{_prefix} --python='$pyCmd'

%files
%defattr(-,root,root,-)
%{_prefix}/share/$pkgName/*
%{_prefix}/bin/$pkgName*
%{_prefix}/share/applications/$pkgName.desktop
%{_prefix}/share/doc/$pkgName/*
%{_prefix}/share/pixmaps/$pkgName.png
%{_prefix}/share/icons/hicolor/*/apps/$iconName
%{_prefix}/share/locale/*/LC_MESSAGES/$pkgName.mo
" > $pkgName.spec

#less $pkgName.spec ; exit 0

if [ ! -f /usr/bin/rpmbuild ] ; then
	zypper install rpm-build
fi

rpmbuild -bb $pkgName.spec

pkgPath="`ls /usr/src/packages/RPMS/noarch/$pkgName*$version*.rpm`"
cp "$pkgPath" "$outDir/"


