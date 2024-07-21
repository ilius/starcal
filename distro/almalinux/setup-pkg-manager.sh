#!/bin/sh
set -e
set -x

echo 'keepcache=1' >> /etc/dnf/dnf.conf

# release=$(cat /etc/almalinux-release | grep -o '[0-9]*')

# rm /etc/yum.repos.d/*.repo

# /etc/yum.repos.d/almalinux-appstream.repo
# /etc/yum.repos.d/almalinux-baseos.repo
# /etc/yum.repos.d/almalinux-crb.repo
# /etc/yum.repos.d/almalinux-extras.repo
# /etc/yum.repos.d/almalinux-highavailability.repo
# /etc/yum.repos.d/almalinux-nfv.repo
# /etc/yum.repos.d/almalinux-plus.repo
# /etc/yum.repos.d/almalinux-resilientstorage.repo
# /etc/yum.repos.d/almalinux-rt.repo
# /etc/yum.repos.d/almalinux-sap.repo
# /etc/yum.repos.d/almalinux-saphana.repo

# use $releasever (and $basearch) in baseurl
# and don't forget "/os/" at the end

# mirrors
# https://mirrors.almalinux.org/

