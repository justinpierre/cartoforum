FROM ubuntu:20.04 AS step1
EXPOSE 8080:8080
ENV GEOSERVER_HOME=/usr/share/geoserver
RUN apt-get update && \
    apt-get install -y openjdk-8-jdk && \
    apt-get install -y openjdk-8-jre && \
    apt-get install -y wget && \
    apt-get install unzip && \
    mkdir /usr/share/geoserver && \
    wget https://sourceforge.net/projects/geoserver/files/GeoServer/2.20.4/geoserver-2.20.4-bin.zip -P /usr/share/geoserver && \
    unzip /usr/share/geoserver && \ 
    /usr/share/geoserver/bin/startup.sh

ENTRYPOINT ["tail", "-f", "/dev/null"]