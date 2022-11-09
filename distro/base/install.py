#!/usr/bin/env python3
import os
import sys
import subprocess
from os.path import (
	join,
	dirname,
	abspath,
	realpath,
	isfile,
	isdir,
	islink,
)
import getopt
import shutil
from shutil import rmtree

# realpath gives the target of sym link (unlike abspath)
myPath = realpath(__file__)
sourceDir = dirname(dirname(dirname(myPath)))
print(sourceDir)

pkgName = "starcal3"
iconName = "starcal32.png"


def printAsError(msg):
	sys.stderr.write(msg + "\n")
	sys.stderr.flush()


def printUsage():
	## echo "Usage: $0 [TERGET_DIR] [--for-pkg|--portable] [--prefix=/usr/local]"
	U = "\x1b[4m"  # Start Underline # len=4
	E = "\x1b[0;0;0m"  # End Format # len=8
	print(
		f"Usage: python3 {sys.argv[0]} [{U}TERGET_DIR{E}] "
		f"[--for-pkg|--portable] "
		f"[--prefix={U}/usr/local{E}] "
		f"[--python={U}python3.x{E}]"
	)

def getVersion():
	outputB, error = subprocess.Popen(
		[
			"python3",
			f"{sourceDir}/scripts/version.py"
		],
		stdout=subprocess.PIPE,
	).communicate()
	# if error == None:
	return outputB.decode("utf-8").strip()


version = getVersion()

installTypeValues = [
	"for-pkg",
	"portable",
	"system",
]


def makeDir(direc):
	if not isdir(direc):
		os.makedirs(direc)

def cleanup(cpath):
	try:
		if isfile(cpath):
			os.remove(cpath)
		elif isdir(cpath):
			rmtree(direc, ignore_errors=True)
	except OSError:
		pass


def lsb_release() -> str:
	outputB, error = subprocess.Popen(
		["lsb_release", "-is"],
		stdout=subprocess.PIPE,
	).communicate()
	if error:
		printAsError(error)
	return outputB.decode("utf-8").strip()

def checkOperatingSystem(installType):
	if installType == "for-pkg":
		return True

	if isfile("/etc/debian_version"):
		if lsb_release() == "Ubuntu":
			printAsError("Your distribution is based on Ubuntu, use: sudo ./distro/ubuntu/install.sh")
		else:
			printAsError("Your distribution is based on Debian, use: sudo ./distro/debian/install.sh")
		return False

	elif isfile("/etc/SUSE-brand") or isfile("/etc/products.d/openSUSE.prod"):
		printAsError("Your distribution is based on SUSE, use: sudo ./distro/suse/install.sh")
		return False

	elif isfile("/etc/fedora-release"):
		printAsError("Your distribution is based on Red Hat, use: sudo ./distro/fedora/install.sh")
		return False

	elif isfile("/etc/arch-release"):
		printAsError("Your distribution is based on ArchLinux, use ./distro/archlinux/install.sh")
		return False

	return True


def main():
	try:
		(rawOptions, args) = getopt.gnu_getopt(
			sys.argv[1:],
			"",
			installTypeValues + [
				"help",
				"prefix=",
				"python=",
			],
		)
	except getopt.GetoptError as e:
		printAsError(str(e))
		printUsage()
		return 1

	options = {
		opt.lstrip("-"): value
		for opt, value in rawOptions
	}
	# print(options)
	# print(args)

	targetDir = ""
	if args:
		targetDir = args[0]
		args = args[1:]

	if args:
		printAsError("Too many unbound arguments")
		printUsage()
		return 1

	installType = None
	for value in installTypeValues:
		if value in options:
			if installType is not None:
				printAsError(f"can not pass both {installType} and {value}")
				return 1
			installType = value
	# print(f"installType = {installType}")

	# if not checkOperatingSystem(installType):
	# 	return 1

	prefix = ""
	if "prefix" in options:
		prefix = options["prefix"].rstrip("/")
	elif installType == "for-pkg":
		prefix = "/usr"
	elif installType == "portable":
		prefix = "/usr/local"
	elif installType == "system":
		prefix = "/usr/local"
	else:
		prefix = "/usr/local"
	print(f"{prefix = }")

	pyCmd = options.get("python", "")
	if pyCmd:
		if not isfile(pyCmd):
			printAsError(
				f"The given Python executable {pyCmd!r} does not exist"
			)
	else:
		pyCmd = sys.executable
		userPyCmd = shutil.which("python3")
		if not userPyCmd:
			printAsError(
				f"WARNING: Python executable {pyCmd!r} is not in your $PATH"
			)
		elif pyCmd != userPyCmd:
			printAsError(
				f"WARNING: Python executable {pyCmd!r} is different from {userPyCmd!r}"
			)
	print(f"Using {pyCmd}")

	if targetDir:
		targetDir = abspath(targetDir)
		makeDir(targetDir)

	targetPrefix = join(targetDir, prefix)
	shareDir = join(targetPrefix, "share")
	targetCodeDir = join(shareDir, pkgName)

	makeDir(join(shareDir, "doc"))
	makeDir(join(shareDir, "applications"))
	makeDir(join(shareDir, "icons"))
	makeDir(join(shareDir, "pixmaps"))
	makeDir(join(shareDir, "doc", pkgName))
	makeDir(join(targetPrefix, "bin"))
	makeDir(join(targetDir, "/var/log", pkgName))
	makeDir(join(targetDir, "/etc"))

	if islink(targetCodeDir):
		os.remove(targetCodeDir)
	elif isdir(targetCodeDir):
		rmtree(targetCodeDir)

	shutil.copytree(sourceDir, targetCodeDir)

	if subprocess.call(join(targetCodeDir, "update-perm")) != 0:
		return 1

	for docFile in ("license.txt", "authors", "donate"):
		os.rename(
			join(targetCodeDir, docFile),
			join(shareDir, "doc", pkgName, docFile)
		)

	makeDir(join(shareDir, "icons", "hicolor"))
	for size in (16, 22, 24, 32, 48):
		relDir = f"icons/hicolor/{size}x{size}/apps"
		makeDir(join(shareDir, relDir))
		os.rename(
			join(targetCodeDir, relDir, "starcal.png"),
			join(shareDir, relDir, iconName),
		)
	rmtree(join(targetCodeDir, "icons"))

	shutil.copy(
		join(sourceDir, "pixmaps", "starcal.png"),
		join(shareDir, "pixmaps", iconName)
	)

	if installType == "for-pkg":
		runDirStr = join(prefix, "share", pkgName)
	elif installType == "portable":
		runDirStr = f'"`dirname \\"\$0\\"`"/../share/{pkgName}'
	else:
		runDirStr = targetCodeDir

	# print(f"runDirStr: {runDirStr}")

	executablePath = join(targetPrefix, "bin", pkgName)
	with open(executablePath, mode="wt") as _file:
		_file.write(
			"#!/usr/bin/env sh\n"
			f'{pyCmd} {runDirStr}/scal3/ui_gtk/starcal-main.py "$@"\n'
		)
	os.chmod(executablePath, 0o755)
	print(f"Executable: {executablePath}")

	with open(join(targetCodeDir, "VERSION"), mode="w") as _file:
		_file.write(f"{version}\n")

	if installType == "system":
		shutil.move(
			join(targetCodeDir, "distro/base/uninstall"),
			join(targetCodeDir, "uninstall"),
		)
	else:
		os.remove(join(targetCodeDir, "distro/base/uninstall"))

	with open(join(shareDir, "applications", f"{pkgName}.desktop"), mode="w") as _file:
		_file.write(
			"[Desktop Entry]\n"
			"Encoding=UTF-8\n"
			f"Name=StarCalendar {version}\n"
			"GenericName=StarCalendar\n"
			"Comment=Full-featured Calendar Program\n"
			"Comment[fa]=یک برنامهٔ کامل تقویم\n"
			f"Exec={pkgName}\n"
			f"Icon={iconName}\n"
			"Type=Application\n"
			"Terminal=false\n"
			"Categories=GTK;Office;Calendar;Utility;\n"
			"StartupNotify=true\n"
		)

	if not subprocess.call([
		join(sourceDir, "locale.d/install"),
		targetPrefix,
	]):
		return 1

	if "$installType" in ("for-pkg", "system"):
		cleanup(join(targetCodeDir, ".git"))
		cleanup(join(targetCodeDir, ".github"))
		cleanup(join(targetCodeDir, ".gitignore"))
		# TODO: targetCodeDir/.Trash*
		cleanup(join(targetCodeDir, "google-api-python-client/.git"))
		cleanup(join(targetCodeDir, "google-api-python-client/.hg"))
		cleanup(join(targetCodeDir, "screenshots"))
		# for EXP in '.hidden' '*~' '*.pyc' '*.pyo' '*.tar.xz' '*.tar.gz' '*.deb' '*.rpm' '*.spec':
		# 		find "$DIR" -name "$EXP" -exec rm '{}' \; || true
		# find "$targetCodeDir" -name '__pycache__' -exec rm -R '{}' \; 2>/dev/null || true
		# find "$targetCodeDir" -type d -empty -delete || true

	else:
		targetDotGit = join(targetCodeDir, ".git")
		if isdir(targetDotGit):
			print(f"You may want to remove '{targetDotGit}'")


if __name__ == "__main__":
	# print(f"{sourceDir=}")
	# print(f"{version=}")
	sys.exit(main())
