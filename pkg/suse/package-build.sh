#!/bin/bash

myDir="`dirname \"$0\"`"
myDir=`realpath "$myDir"`
cd "$myDir/../.."

suseDir="$HOME/.cache/starcal3-pkgs/suse"
pkgCacheDir="$suseDir/cache"

mkdir -p "$pkgCacheDir"

docker build . \
	-f pkg/suse/Dockerfile \
	-t starcal3-suse:latest

DATE=`/bin/date +%F-%H%M%S`
dockerOutDir=/root/pkgs/$DATE/

docker run -it \
	--volume $suseDir:/root/pkgs \
	--volume $pkgCacheDir:/var/cache/zypp \
	starcal3-suse:latest \
	/root/starcal/pkg/suse/docker-build-internal.sh $dockerOutDir

#	--mount type=bind,source="$pkgCacheDir",target=/var/cache/zypp

cd -

outDir="$suseDir/$DATE"
ls -l "$outDir"/*.rpm
