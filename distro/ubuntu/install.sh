#!/bin/bash
apt-get install 'gir1.2-appindicator3*'

myPath=$(realpath "$0")
myDir1=$(dirname "$myPath")
myDir2=$(dirname "$myDir1")

"$myDir2/debian/install.sh"


