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

myDir=$(dirname "$myPath")
pkgDir=$(dirname "$myDir")
sourceDir=$(dirname "$pkgDir")
#"$sourceDir/scripts/assert_python3"

version=$("$sourceDir/scripts/version" | sed 's/\-/_/g')

#echo "myPath=$myPath"
#echo "sourceDir=$sourceDir"
#echo version=$version

depends=('python>=3.9')
depends+=('python-gobject>=3.24') ## The new gobject introspection
depends+=('gtksourceview4')
depends+=('python-cairo')
depends+=('python-httplib2')
depends+=('python-psutil')
depends+=('python-cachetools')
depends+=('python-requests')
depends+=('python-setuptools')
depends+=('python-six')
#depends+=('python-gflags') # for google api client


optdepends=()
optdepends+=('libappindicator-gtk3')
optdepends+=('python-igraph' 'igraph' 'icu')
#optdepends+=('python-gnomevfs')
optdepends+=('lxqt-openssh-askpass')
optdepends+=('python-pygit2')

optdepends+=('ntp')
# package extra/ntp contains /usr/bin/ntpdate

## Note: optdepends are not installed by default

depends_str=$(printf " '%s'" "${depends[@]}") ; depends_str=${depends_str:1}
optdepends_str=$(printf " '%s'" "${optdepends[@]}") ; optdepends_str=${optdepends_str:1}

cd "$outDir/"

echo "# Contributor: Saeed Rasooli <saeed.gnu@gmail.com>
# This is a local PKGBUILD
sourceDir='$sourceDir'
pkgname=$pkgName
pkgver=$version
pkgrel=1
pkgdesc='A full-featured international calendar written in Python'
arch=('any')
url=http://ilius.github.io/starcal
license=('GPLv3')
depends=($depends_str)
optdepends=($optdepends_str)
makedepends=()
conflicts=('starcal-git')
source=()
md5sums=()
package() {
	\"\$sourceDir/distro/base/install.sh\" \"\$pkgdir\" --for-pkg --python=\"$pyCmd\"
}" > PKGBUILD

makepkg --nodeps --force

rm -rf "$outDir/pkg" "$outDir/PKGBUILD" "$outDir/src"

# will create in outDir, so no need to copy
ls -l $pkgName*.pkg.tar*

cd - > /dev/null
