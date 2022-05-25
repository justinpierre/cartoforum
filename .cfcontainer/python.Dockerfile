FROM ubuntu:20.04 AS step1

ARG PYTHON="3.7"
ENV TZ=Canada/Eastern
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
ARG DEBIAN_FRONTEND=noninteractive 
ENV PATH /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV cf /cartoforum

RUN mkdir -p ${cf} && \
    mkdir /${cf}/tests

FROM step1 as step2

RUN apt-get -y update && \
    apt-get install -y python-dev && \
    apt-get install -y pkg-config && \
    apt-get install -y locales && locale-gen en_US.UTF-8 && \
    apt-get install -y wget && \ 
    apt-get clean

FROM step2 as step3

RUN wget -P ${HOME} https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    chmod 777 ${HOME}/Miniconda3-latest-Linux-x86_64.sh && \
    ${HOME}/Miniconda3-latest-Linux-x86_64.sh -b -p ${INSTALLS}/miniconda3 && \
    rm -rf ${HOME}/Miniconda3-latest-Linux-x86_64.sh && \
    ${INSTALLS}/miniconda3/bin/conda install -y python=3.7 && \
    ${INSTALLS}/miniconda3/bin/conda install -y psycopg2 && \    
    ${INSTALLS}/miniconda3/bin/conda install -y paramiko && \
    ${INSTALLS}/miniconda3/bin/conda install -y sqlalchemy && \
    ${INSTALLS}/miniconda3/bin/conda install -y flask && \
    ${INSTALLS}/miniconda3/bin/conda install -y -c conda-forge flask-mail && \
    ${INSTALLS}/miniconda3/bin/conda install -y pandas && \
    ${INSTALLS}/miniconda3/bin/conda clean -a

RUN ${INSTALLS}/miniconda3/bin/conda init bash

ENTRYPOINT ["tail", "-f", "/dev/null"]