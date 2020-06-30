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
requires+=('python3-gobject >= 3.24') ## The new gobject introspection
requires+=('python3-cairo')
requires+=('libappindicator-gtk3')
requires+=('python3-httplib2')
requires+=('python3-dateutil')
requires+=('python3-psutil')
requires+=('python3-cachetools')
requires+=('python3-requests')
#requires+=('python3-gflags') # for google api client


recommends=()
recommends+=('python3-igraph') # since Fedora 27
#recommends+=('python3-gnomevfs')

recommends+=('lxqt-openssh-askpass')
# I did not find openssh-askpass-gnome in Fedora repos

recommends+=('python3-pygit2')

requires_str="Requires: ${requires[@]}"
recommends_str="Recommends: ${recommends[@]}"

## about "Recommends":
## https://docs.fedoraproject.org/en-US/packaging-guidelines/WeakDependencies/


echo "Name:     $pkgName
Version:        $version
Release:        1
Summary:        A full-featured international calendar written in Python

Group:          User Interface/Desktops
License:        GPLv3+
URL:            http://ilius.github.io/starcal

$requires_str
$recommends_str

BuildArch:      noarch
BuildRequires:  python3 desktop-file-utils gettext git-core

%description
StarCalendar is a full-featured international calendar written in Python,
using Gtk3-based interface, that supports Jalai(Iranian), Hijri(Islamic),
and Indian National calendars, as well as common English(Gregorian) calendar

# Turn off the brp-python-bytecompile automagic
%global _python_bytecompile_extra 0

%install
\"$sourceDir/install\" \"%{buildroot}\" --for-pkg --prefix=%{_prefix} --python='$pyCmd'

%files
%defattr(-,root,root,-)
%{_prefix}/share/$pkgName/*
%{_prefix}/bin/$pkgName*
%{_prefix}/share/applications/$pkgName*
%{_prefix}/share/doc/$pkgName/*
%{_prefix}/share/pixmaps/$pkgName.png
%{_prefix}/share/icons/hicolor/*/apps/$iconName
%{_prefix}/share/locale/*/LC_MESSAGES/$pkgName.mo
" > $pkgName.spec

rpmbuild -bb $pkgName.spec
status=$?
if [ "$status" != "0" ] ; then
	echo "rpmbuild exited with failed status '$status'" >&2
	exit $status
fi

pkgPath="$HOME/rpmbuild/RPMS/noarch/$pkgName-$version-1.noarch.rpm"
cp "$pkgPath" "$outDir/"
