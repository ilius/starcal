#!/bin/bash
set -e

myDir="`dirname \"$0\"`"
myDir=`realpath "$myDir"`
cd "$myDir/../.."

distro=fedora
distroDir="$HOME/.cache/starcal3-pkgs/$distro"
pkgCacheDir="$distroDir/cache"

mkdir -p "$pkgCacheDir"

function shouldBuild() {
	imageName=$1
	if [ $REBUILD = 1 ] ; then
		return 0
	fi
	imageCreated=$(docker inspect -f '{{ .Created }}' "$imageName" 2>/dev/null)
	if [ -z "$imageCreated" ] ; then
		return 0
	fi
	imageAge=$[$(/usr/bin/date +%s) - $(/usr/bin/date +%s -d "$imageCreated")]
	if [ -z "$imageAge" ] ; then
		return 0
	fi
	echo "Existing $imageName image is $imageAge seconds old"
	if [[ "$imageAge" > 604800 ]] ; then
		# more than a week old
		return 0
	fi
	return 1
}

if shouldBuild starcal3-$distro ; then
	docker build . \
		-f pkg/$distro/Dockerfile \
		-t starcal3-$distro:latest
else
	echo "Using existing starcal3-$distro image"
fi

DATE=`/bin/date +%F-%H%M%S`
dockerOutDir=/root/pkgs/$DATE/

docker run -it \
	--volume $distroDir:/root/pkgs \
	--volume $pkgCacheDir:/var/cache/dnf \
	starcal3-$distro:latest \
	/root/starcal/pkg/$distro/docker-build-internal.sh $dockerOutDir

#	--mount type=bind,source="$pkgCacheDir",target=/var/cache/zypp

cd -

outDir="$distroDir/$DATE"
ls -l "$outDir"/*.rpm
