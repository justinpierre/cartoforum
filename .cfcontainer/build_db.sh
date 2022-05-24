#!/bin/bash
psql -U postgres -c "DROP DATABASE IF EXISTS cartoforum;"

psql -U postgres -c "DROP ROLE IF EXISTS cfadmin"
psql -U postgres -c "CREATE ROLE cfadmin LOGIN ENCRYPTED PASSWORD 'cart0f0ru3' SUPERUSER INHERIT;"

psql -U postgres -c "CREATE DATABASE cartoforum WITH ENCODING=UTF8 OWNER=cfadmin;"
psql -U cfadmin -d cartoforum -c "CREATE SCHEMA cfadmin AUTHORIZATION cfadmin;GRANT USAGE ON SCHEMA cfadmin TO cfadmin;"

psql -U cfadmin -d cartoforum -c "CREATE TABLE users (userid INT GENERATED ALWAYS AS IDENTITY,  \
    username VARCHAR(255),  \
    password VARCHAR(255),  \
    email VARCHAR(255),  \
    verified BOOLEAN,  \
    twitterid VARCHAR(255), \
    basemap INT,  \
    color INT, \
    PRIMARY KEY(userid) \
);"

psql -U cfadmin -d cartoforum -c "CREATE TABLE groups ( \
    groupid INT GENERATED ALWAYS AS IDENTITY, \
    groupname VARCHAR(255), \
    userid INT, \
    bounds VARCHAR(255), \
    opengroup BOOLEAN, \
    PRIMARY KEY(groupid)
);"

psql -U cfadmin -d cartoforum -c "CREATE TABLE thread ( \
    threadid INT GENERATED ALWAYS AS IDENTITY, \
    nickname VARCHAR(255), \
    name VARCHAR(255), \
    groupid INT, \
    resolved INT, \
    retired BOOLEAN, \
    PRIMARY KEY(threadid), \
    CONSTRAINT fk_groups \
        FOREIGN KEY (groupid) \
            REFERENCES groups(groupid) \
);"

psql -U cfadmin -d cartoforum -c "CREATE TABLE posts ( \
    postid INT GENERATED ALWAYS AS IDENTITY,  \
    userid INT, \
    groupid INT, \
    objectid INT, \
    date TIMESTAMP, \
    postcontent VARCHAR(5000), \
    responseto INT, \
    threadid INT,
    PRIMARY KEY(postid), \
    CONSTRAINT fk_users \
        FOREIGN KEY(userid) \
            REFERENCES users(userid), \
    CONSTRAINT fk_thread \
        FOREIGN KEY (threadid) \
            REFERENCES thread(threadid) \
);"

psql -U cfadmin -d cartoforum -c "CREATE TABLE passwordreset ( \
    requestid INT, \
    userid INT, \
    date TIMESTAMP, \
    token VARCHAR(255), \
    used BOOLEAN, \
    PRIMARY KEY(requestid), \
    CONSTRAINT fk_users \
        FOREIGN KEY(userid) \
            REFERENCES users(userid) \
);"

psql -U cfadmin -d cartoforum -c "CREATE TABLE twitterusers ( \
    id INT, \
    oauth_provider VARCHAR(50), \
    oauth_uid VARCHAR(255), \
    oauth_token VARCHAR(255), \
    oauth_secret VARCHAR(255), \
    username varchar(255), \
    PRIMARY KEY(id), \
    CONSTRAINT twitterusers_users \
        FOREIGN KEY(oauth_uid) \
            REFERENCES users(twitterid) \
);"

psql -U cfadmin -d cartoforum -c "CREATE TABLE usersgroups ( \
    userid INT, 
    groupid INT,
    CONSTRAINT fk_users \
        FOREIGN KEY(userid) \
            REFERENCES users(userid), \
    CONSTRAINT fk_groups \
        FOREIGN KEY(groupid) \
            REFERENCES groups(groupid) \
);"

psql -U cfadmin -d cartoforum -c "CREATE TABLE votes ( \
    userid INT, \
    postid INT, \
    vote INT, \
    CONSTRAINT fk_users \
        FOREIGN KEY(userid) \
            REFERENCES users(userid), \
    CONSTRAINT fk_posts \
        FOREIGN KEY(postid) \
            REFERENCES posts(postid) \
);"

psql -U cfadmin -d cartoforum -c "CREATE TABLE inviteme (  \
    requestid INT, \ 
    userid INT,
    groupid INT,
    date TIMESTAMP, \
    accepted BOOLEAN, \
    PRIMARY KEY(requestid), \
    CONSTRAINT fk_users \
        FOREIGN KEY(userid) \
            REFERENCES users(userid), \
    CONSTRAINT fk_groups \
        FOREIGN KEY(groupid) \
            REFERENCES groups(groupid) \
);"

psql -U cfadmin -d cartoforum -c "CREATE TABLE grouprequests (  \
    requestid INT, \
    requester INT, \
    invitee INT, 
    groupid INT, \
    dateissued TIMESTAMP, \
    complete BOOLEAN, \
    PRIMARY KEY(requestid), \
    CONSTRAINT fk_requester \
        FOREIGN KEY(requester) \
            REFERENCES users(userid), \
    CONSTRAINT fk_groups \
        FOREIGN KEY(groupid) \
            REFERENCES groups(groupid) \
);"
