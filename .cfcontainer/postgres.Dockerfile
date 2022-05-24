FROM ubuntu:20.04 AS step1
   
#have to specify timezone   
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
EXPOSE 5432:5432
# COPY ./restore_db.sh /home
# COPY ./db_dumps.zip /home
RUN useradd -ms /bin/bash postgres && \
    printf '#!/bin/sh\nexit 0' > /usr/sbin/policy-rc.d && \
    apt-get -y update && \
    apt-get install -y postgresql-client-12 && \
    apt-get install -y postgresql-12 && \
    apt-get install -y unzip && \
    echo "local all all trust" > /etc/postgresql/12/main/pg_hba.conf && \
    echo "host  all  all  0.0.0.0/0   md5" >> /etc/postgresql/12/main/pg_hba.conf && \
    echo "listen_addresses = '*'" >> /etc/postgresql/12/main/postgresql.conf && \
    # unzip /home/db_dumps.zip -d /tmp && \
    update-rc.d postgresql enable
    # sed -i -e 's/\r$//' /home/restore_db.sh && \
    # chmod 777 /home/restore_db.sh
USER postgres    

CMD /usr/lib/postgresql/12/bin/pg_ctl -D /var/lib/postgresql/12/main restart; sleep infinity