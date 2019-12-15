FROM fedora:latest
MAINTAINER Saeed Rasooli saeed.gnu@gmail.com
LABEL Description="Dockefile to build StarCalendar package for Fedora"

RUN dnf install -y dnf-plugins-core
RUN dnf config-manager --set-disabled fedora-modular
RUN dnf config-manager --set-disabled updates
RUN dnf config-manager --set-disabled updates-modular

RUN echo 'keepcache=1' >> /etc/dnf/dnf.conf


COPY . /root/starcal

CMD /bin/bash
