FROM fedora:latest
MAINTAINER Saeed Rasooli saeed.gnu@gmail.com
LABEL Description="Dockerfile to build StarCalendar package for Fedora"

COPY . /root/starcal

RUN sh /root/starcal/distro/fedora/setup-pkg-manager.sh

CMD /bin/bash
