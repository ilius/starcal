#!/bin/bash
dnf config-manager --set-enabled ha

myPath=$(realpath "$0")
myDir1=$(dirname "$myPath")
myDir2=$(dirname "$myDir1")

"$myDir2/fedora/install.sh"


