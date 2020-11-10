#!/bin/bash
set -e

myDir="`dirname \"$0\"`"
myDir=`realpath "$myDir"`
cd "$myDir/../.."

archlinuxDir="$HOME/.cache/starcal3-pkgs/archlinux"
pkgCacheDir="$archlinuxDir/cache"

mkdir -p "$pkgCacheDir"

docker build . \
	-f pkg/archlinux/Dockerfile \
	-t starcal3-archlinux:latest

DATE=`/bin/date +%F-%H%M%S`
dockerOutDir=/home/build/pkgs/$DATE/

docker run -it \
	--volume $archlinuxDir:/home/build/pkgs \
	--volume $pkgCacheDir:/var/cache/pacman \
	starcal3-archlinux:latest \
	/home/build/starcal/pkg/archlinux/docker-build-internal.sh $dockerOutDir

#	--mount type=bind,source="$pkgCacheDir",target=/var/cache/zypp

cd -

outDir="$archlinuxDir/$DATE"
ls -l "$outDir"/*.pkg.tar* || rmdir "$outDir"
