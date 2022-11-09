#!/bin/bash
set -e

myDir=$(dirname "$0")
myDir=$(realpath "$myDir")
cd "$myDir/../.."

distro=appimage
pkgs="$HOME/.cache/starcal3-pkgs/"
tmpDir="$pkgs/$distro"

rm -rf "$tmpDir" 2>/dev/null
mkdir -p "$tmpDir"

pyCmd="/usr/bin/python3"

pkgName=starcal3
APP=StarCalendar
export ARCH=x86_64

pkgDir=$(dirname "$myDir")
sourceDir=$(dirname "$pkgDir")

version=$("$sourceDir/scripts/version")





"$sourceDir/distro/base/install.sh" "$tmpDir" "--for-pkg" "--python=$pyCmd"

echo "---------- tmpDir: $tmpDir"

mv "$tmpDir/usr/share/starcal3/" "$tmpDir"
mv "$tmpDir/usr/share/applications/starcal3.desktop" "$tmpDir/starcal3"
cp $tmpDir/usr/share/pixmaps/starcal3*.png "$tmpDir/starcal3"
sed -i 's/\.png//g' "$tmpDir/starcal3/starcal3.desktop"
cp "$tmpDir/usr/bin/starcal3" "$tmpDir/starcal3/"

cd "$tmpDir/starcal3/"
if  [ ! -f $pkgs/AppRun ]; then
    wget -c https://github.com/AppImage/AppImageKit/releases/download/continuous/AppRun-${ARCH} -O $pkgs/AppRun
else
    cp $pkgs/AppRun .
fi
chmod a+x AppRun
export AppRun="AppRun"

cd "$tmpDir/"
# generate_type2_appimage
VERSION=$version appimagetool -v -n ./starcal3


# rm -rf "$tmpDir"
