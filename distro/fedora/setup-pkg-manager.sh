#!/bin/sh
set -e
set -x

echo 'keepcache=1' >> /etc/dnf/dnf.conf

# release=$(cat /etc/fedora-release | grep -o '[0-9]*')

# rm /etc/yum.repos.d/*.repo

# echo '[fedora]
# name=Fedora $releasever - $basearch
# baseurl=http://mirror.speedpartner.de/fedora/linux//development/$releasever/Everything/$basearch/os/
# enabled=1
# countme=1
# metadata_expire=7d
# repo_gpgcheck=0
# type=rpm
# gpgcheck=0' > /etc/yum.repos.d/fedora.repo

# use $releasever (and $basearch) in baseurl
# and don't forget "/os/" at the end

# get mirrors in a country by downloading this xml file:
# https://mirrors.fedoraproject.org/metalink?repo=fedora-35&arch=x86_64&country=de

