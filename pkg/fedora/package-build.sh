#!/bin/bash
set -e

myDir="`dirname \"$0\"`"
myDir=`realpath "$myDir"`
cd "$myDir/../.."

fedoraDir="$HOME/.cache/starcal3-pkgs/fedora"
pkgCacheDir="$fedoraDir/cache"

mkdir -p "$pkgCacheDir"

function shouldBuild() {
	imageName=$1
	imageCreated=$(docker inspect -f '{{ .Created }}' "$imageName" 2>/dev/null)
	if [ -z "$imageCreated" ] ; then
		return 0
	fi
	imageAge=$[$(/usr/bin/date +%s) - $(/usr/bin/date +%s -d "$imageCreated")]
	if [ -z "$imageAge" ] ; then
		return 0
	fi
	echo "Existing image is $imageAge seconds old"
	if [[ "$imageAge" > 604800 ]] ; then
		# more than a week old
		return 0
	fi
	return 1
}

if shouldBuild starcal3-fedora ; then
	docker build . \
		-f pkg/fedora/Dockerfile \
		-t starcal3-fedora:latest
else
	echo "Using existing starcal3-fedora image"
fi

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
