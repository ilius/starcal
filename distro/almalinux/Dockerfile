FROM almalinux:latest
MAINTAINER Saeed Rasooli saeed.gnu@gmail.com
LABEL Description="Dockefile to build StarCalendar package for AlmaLinux"

COPY . /root/starcal

RUN sh /root/starcal/distro/almalinux/setup-pkg-manager.sh

CMD /bin/bash
