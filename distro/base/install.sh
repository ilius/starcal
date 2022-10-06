#!/usr/bin/env bash
set -e

function printUsage {
	## echo "Usage: $0 [TERGET_DIR] [--for-pkg|--portable] [--prefix=/usr/local]"
	U='\033[4m' ## start Underline
	E='\033[0;0;0m' ## End formatting
	echo -e "Usage: $0 [${U}TERGET_DIR${E}] [--for-pkg|--portable] [--prefix=${U}/usr/local${E}] [--python=${U}python3.x${E}]"
}

myPath=$(realpath "$0")
myDir1=$(dirname "$myPath")
myDir2=$(dirname "$myDir1")
sourceDir=$(dirname "$myDir2")

function getVersion {
	if version=$("$sourceDir/scripts/version") ; then
		echo "$version"
		return
	fi
	"$sourceDir/scripts/version.py"
}

pkgName=starcal3
iconName=starcal32.png

#"$sourceDir/scripts/assert_python3"

"$sourceDir/update-perm" ## FIXME

if ! options=$(
	getopt -o 'h' --long \
	'help,for-pkg,portable,system,prefix:,python:' -n "$0" -- "$@"
) ; then
	printUsage
	exit 1
fi
eval set -- "$options" ## Note the quotes around $options are essential!
options=""


pyCmd=""
prefix=""
installType=""

while true ; do
	case "$1" in
		--help | -h) printUsage ; exit 0 ;;
		--for-pkg) installType="for-pkg" ; shift ;;
		--portable) installType="portable" ; shift ;;
		--system) installType="system" ; shift ;;
		--prefix) prefix="$2" ; shift 2 ;;
		--python) pyCmd="$2" ; shift 2 ;;
		--) shift ; break ;;
		*) echo "Internal error!" >&2 ; exit 1 ;;
	esac
done


if [ "$installType" != "for-pkg" ] ; then
	if [ -f /etc/debian_version ] ; then
		if [ "$(lsb_release -is)" = "Ubuntu" ] ; then
			echo "Your distribution is based on Ubuntu, use: sudo ./distro/ubuntu/install.sh"
		else
			echo "Your distribution is based on Debian, use: sudo ./distro/debian/install.sh"
		fi
		#exit 1
	elif [ -f /etc/SUSE-brand ] || [ -f /etc/products.d/openSUSE.prod ] ; then
		echo "Your distribution is based on SUSE, use: sudo ./distro/suse/install.sh"
		exit 1
	elif [ -f /etc/fedora-release ] ; then
		echo "Your distribution is based on Red Hat, use: sudo ./distro/fedora/install.sh"
		exit 1
	elif [ -f /etc/arch-release ] ; then
		echo "Your distribution is based on ArchLinux, use ./distro/archlinux/install.sh"
		exit 1
	fi
fi

if [ -z "$pyCmd" ] ; then
	if ! pyCmd=$(which "python3") ; then
		echo "Python executable file not found." >&2
		echo "Make sure 'python3' is in one of \$PATH directories." >&2
		exit 1
	fi
fi
if which "$pyCmd" && \
"$pyCmd" -c 'import sys;exit((3, 8) <= sys.version_info < (3, 11))' ; then
	pyVer=$("$pyCmd" --version)
	printf "\e[31mWarning: %s is not officially supported.\e[m\n" "$pyVer" >&2
	printf "\e[31mPress Enter to continue anyway.\e[m\n" >&2
	read
fi

echo "Using $pyCmd"
version=$(getVersion)


targetDir=
if [ -n "$1" ] ; then
	targetDir="$1" ; shift
fi
if [ -n "$1" ] ; then ## extra arguments
	printUsage
	exit 1
fi

if [ -n "$targetDir" ] ; then ## non-Root directory
	n=${#targetDir}
	if [ "${targetDir:n-1:1}" = / ] ; then
		targetDir=${targetDir::-1}
	fi
	mkdir -p "${targetDir}"
fi

## do not f*** the system if a variable was empty amiss!
if [ -z $pkgName ] ; then
	echo "Internal Error! pkgName=''" >&2
	exit 1
fi
if [ -z "$prefix" ] ; then ## prefix is empty (not been set)
	if [ "$installType" = "for-pkg" ] ; then
		prefix=/usr
	elif [ "$installType" = "portable" ] ; then
		prefix=/usr/local
	elif [ "$installType" = "system" ] ; then
		prefix=/usr/local
	else
		prefix=/usr/local
	fi
else
	n=${#prefix}
	if [ ${prefix:n-1:1} = / ] ; then
		prefix=${prefix::-1}
	fi
fi

#echo "prefix: $prefix"
#echo "installType: $installType"
#echo "targetDir: $targetDir"
#exit 0

targetPrefix="${targetDir}${prefix}"
shareDir="${targetPrefix}/share"
targetCodeDir="${shareDir}/$pkgName"






mkdir -p "${shareDir}/doc"
mkdir -p "${shareDir}/applications"
mkdir -p "${shareDir}/icons"
mkdir -p "${shareDir}/pixmaps"
mkdir -p "${shareDir}/doc/$pkgName"
mkdir -p "${targetPrefix}/bin"
mkdir -p "${targetDir}/var/log/$pkgName"
mkdir -p "${targetDir}/etc"



if [ -L "$targetCodeDir" ] ; then ## a symbiloc link
	rm -f "$targetCodeDir"
elif [ -d "$targetCodeDir" ] ; then
	rm -Rf "$targetCodeDir"
fi

cp -Rf "$sourceDir/" "$targetCodeDir" ### PUT SLASH after $sourceDir to copy whole folder, not just a link (if was a link)

"$targetCodeDir/update-perm"

for docFile in license.txt authors donate ; do
	mv -f "$targetCodeDir/$docFile" "${shareDir}/doc/$pkgName/"
done


## "$sourceDir/config" is not used yet, and will not created by git yet
#if [ -e "${targetDir}/etc/$pkgName" ] ; then
#	rm -Rf "${targetDir}/etc/$pkgName" ## descard old configuration? FIXME
#fi
#cp -Rf "$sourceDir/config" "${targetDir}/etc/$pkgName"


mkdir -p "${shareDir}/icons/hicolor"
for SZ in 16 22 24 32 48 ; do
	relDir="icons/hicolor/${SZ}x${SZ}/apps"
	mkdir -p "${shareDir}/$relDir"
	mv -f "$targetCodeDir/$relDir/starcal.png" "${shareDir}/$relDir/$iconName"
done
rm -R "$targetCodeDir/icons"


cp -f "$sourceDir/pixmaps/starcal.png" "${shareDir}/pixmaps/$iconName"


if [ "$installType" = "for-pkg" ] ; then
	runDirStr="$prefix/share/$pkgName"
elif [ "$installType" = "portable" ] ; then
	runDirStr="\"\`dirname \\\"\$0\\\"\`\"/../share/$pkgName"
else
	runDirStr="$targetCodeDir"
fi


echo "#!/usr/bin/env bash
$pyCmd $runDirStr/scal3/ui_gtk/starcal-main.py \"\$@\"" > "${targetPrefix}/bin/$pkgName"
chmod 755 "${targetPrefix}/bin/$pkgName"

echo "$version" > "$targetCodeDir/VERSION"

if [ "$installType" = "system" ] ; then
	mv "$targetCodeDir/distro/base/uninstall" "$targetCodeDir/uninstall"
else
	rm "$targetCodeDir/distro/base/uninstall"
fi


echo "[Desktop Entry]
Encoding=UTF-8
Name=StarCalendar $version
GenericName=StarCalendar
Comment=Full-featured Calendar Program
Comment[fa]=یک برنامهٔ کامل تقویم
Exec=$pkgName
Icon=$iconName
Type=Application
Terminal=false
Categories=GTK;Office;Calendar;Utility;
StartupNotify=true" > "${shareDir}/applications/$pkgName.desktop"


"$sourceDir/locale.d/install" "${targetPrefix}" ## FIXME

rm "$targetCodeDir/libs/bson/setup.py" || true


if [ "$installType" = "for-pkg" ] || [ "$installType" = "system" ] ; then
	set -x
	DIR="$targetCodeDir"
	rm -Rf "$DIR/.git" 2>/dev/null
	rm -Rf "$DIR/.github" 2>/dev/null
	rm -Rf "$DIR/.gitignore" 2>/dev/null
	rm -Rf "$DIR/.Trash"* 2>/dev/null
	rm -Rf "$DIR/google-api-python-client/.git" 2>/dev/null
	rm -Rf "$DIR/google-api-python-client/.hg"* 2>/dev/null
	rm -Rf "$DIR/screenshots/" 2>/dev/null
	for EXP in '.hidden' '*~' '*.pyc' '*.pyo' '*.tar.xz' '*.tar.gz' '*.deb' '*.rpm' '*.spec'; do
		find "$DIR" -name "$EXP" -exec rm '{}' \; || true
	done 2>/dev/null
	find "$DIR" -name '__pycache__' -exec rm -R '{}' \; 2>/dev/null || true
	find "$DIR" -type d -empty -delete || true
	set +x
else
	DIR="$targetCodeDir"
	if [ -e "$DIR/.git" ] ; then
		echo "You may want to remove '$DIR/.git'"
	fi
fi


## lib/        -->    starcal3-platform-spec
## locale/     -->    starcal3-region-*


