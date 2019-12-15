FROM archlinux:latest
MAINTAINER Saeed Rasooli saeed.gnu@gmail.com
LABEL Description="Dockefile to build StarCalendar package for ArchLinux"

RUN useradd --shell=/bin/bash build

COPY . /home/build/starcal
RUN chown -R build /home/build/starcal

CMD /bin/bash
