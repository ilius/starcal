#!/bin/bash
set -e

myDir="`dirname \"$0\"`"
myDir=`realpath "$myDir"`
cd "$myDir/../.."

fedoraDir="$HOME/.starcal3/pkgs/fedora"
pkgCacheDir="$fedoraDir/cache"

mkdir -p "$pkgCacheDir"

docker build . \
	-f pkg/fedora/Dockerfile \
	-t starcal3-fedora:latest

DATE=`/bin/date +%F-%H%M%S`
dockerOutDir=/root/pkgs/$DATE/

docker run -it \
	--volume $fedoraDir:/root/pkgs \
	--volume $pkgCacheDir:/var/cache/dnf \
	starcal3-fedora:latest \
	/root/starcal/pkg/fedora/docker-build-internal.sh $dockerOutDir

#	--mount type=bind,source="$pkgCacheDir",target=/var/cache/zypp

cd -

outDir="$fedoraDir/$DATE"
ls -l "$outDir"/*.rpm
