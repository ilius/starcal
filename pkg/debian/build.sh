#!/bin/bash
set -e

outDir="$1"
if [ -z "$outDir" ] ; then
	echo "OUT_DIR argument is missing"
	echo "Usage: $0 OUT_DIR"
	exit 1
fi
if [ ! -d "$outDir" ] ; then
	echo "Directory not found: $outDir"
	echo "Usage: $0 OUT_DIR"
	exit 1
fi

pyCmd="/usr/bin/python3"


function getDirTotalSize(){
	du -ks "$1" | python3 -c "import sys;print(input().split('\t')[0])"
}

myPath=$(realpath "$0")

pkgName=starcal3
iconName=starcal32.png

myDir="`dirname \"$myPath\"`"
pkgDir="`dirname \"$myDir\"`"
sourceDir="`dirname \"$pkgDir\"`"

git fetch --tags https://github.com/ilius/starcal || echo "WARNING: failed to fetch tags"
version=`"$sourceDir/scripts/version"`

tmpDir="$outDir/tmp"

mkdir -p $tmpDir
mkdir -p "$tmpDir/DEBIAN"

if [ ! -f /usr/bin/python3 ] ; then
	echo "/usr/bin/python3 was not found" >&2
	exit 1
fi

"$sourceDir/install" "$tmpDir" "--for-pkg" "--python=$pyCmd"
chown -R root "$tmpDir"
installedSize=`getDirTotalSize "$tmpDir"` ## only /usr ? FIXME

#getDirTotalSize "$tmpDir"
#getDirTotalSize "$tmpDir/usr"


depends=('python3.7 | python3.6')
depends+=('gir1.2-gtk-3.0')
depends+=('python3-gi(>=3.24)') ## The new gobject introspection
depends+=('python3-gi-cairo')
## it's "python-gobject-cairo" in ubuntu FIXME
depends+=('python3-httplib2')
depends+=('python3-dateutil')
depends+=('python3-psutil')
depends+=('python3-requests')
#depends+=('python3-gflags') # for google api client

recommends=()
recommends+=('python3-igraph')
recommends+=('python3-gnomevfs')
recommends+=('ssh-askpass-gnome')
recommends+=('python3-pygit2')


depends_str=$(printf ", %s" "${depends[@]}") ; depends_str=${depends_str:2}
recommends_str=$(printf ", %s" "${recommends[@]}") ; recommends_str=${recommends_str:2}

mkdir -p $tmpDir/DEBIAN
echo "Package: $pkgName
Version: $version
Architecture: all
Maintainer: Saeed Rasooli <saeed.gnu@gmail.com>
Installed-Size: $installedSize
Depends: $depends_str
Recommends: $recommends_str
Section: Utilities
Priority: optional
Homepage: http://ilius.github.io/starcal
Description: A full-featured international calendar written in Python
 StarCalendar is a full-featured international calendar written in Python,
 using Gtk3-based interface, that supports Jalai(Iranian), Hijri(Islamic),
 and Indian National calendars, as well as common English(Gregorian) calendar
 Homepage: http://ilius.github.io/starcal
" > "$tmpDir/DEBIAN/control"


echo "#!/bin/bash
if [ -f /usr/share/starcal3/scal3/core.py ] ; then
	exit 0
fi
if [ -d '/usr/share/starcal3' ] ; then
	echo 'Cleaning up /usr/share/starcal3'
	find '/usr/share/starcal3' -regex '^.*\(__pycache__\|\.py[co]\)$' -print -delete || true
	find '/usr/share/starcal3' -type d -print -delete || true
fi
" > "$tmpDir/DEBIAN/postrm"
chmod a+x "$tmpDir/DEBIAN/postrm"


pkgPath="$outDir/${pkgName}_${version}-1_all.deb"

exitCode=1
if dpkg-deb -b "$tmpDir" "$pkgPath" ; then
	exitCode=0
fi

rm -Rf "$tmpDir"

ls -l "$pkgPath"
exit $exitCode
