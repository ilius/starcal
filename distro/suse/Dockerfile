FROM opensuse/tumbleweed
MAINTAINER Saeed Rasooli saeed.gnu@gmail.com
LABEL Description="Dockefile to build StarCalendar package for openSUSE"

RUN zypper modifyrepo --disable repo-non-oss
RUN zypper modifyrepo --disable repo-update
RUN zypper modifyrepo --keep-packages repo-oss

COPY . /root/starcal

CMD /bin/bash
