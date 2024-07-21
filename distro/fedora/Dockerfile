FROM fedora:40
MAINTAINER Saeed Rasooli saeed.gnu@gmail.com
LABEL Description="Dockefile to build StarCalendar package for Fedora"

COPY . /root/starcal

RUN sh /root/starcal/distro/fedora/setup-pkg-manager.sh

CMD /bin/bash
