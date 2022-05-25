import os
import sys
sys.path.append(os.getenv('cf'))

from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer, Date, Boolean, ForeignKey, asc
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from cartoforum_api import config

db_string = "postgresql://{}:{}@pg.cf.net:5432/{}".format(config.dbusername,config.dbpassword,config.dbname)
db = create_engine(db_string)
base = declarative_base()

Session = sessionmaker(db)
sess = Session()

base.metadata.create_all(db)


class Users(base):
    __tablename__ = 'users'
    userid = Column(Integer,primary_key=True)
    username = Column(String)
    password = Column(String)
    email = Column(String)
    verified = Column(Boolean)
    twitterid = Column(Integer)
    basemap = Column(Integer)
    color = Column(Integer)


class PasswordReset(base):
    __tablename__ = 'passwordreset'
    requestid = Column(Integer, primary_key=True)
    userid = Column(Integer, ForeignKey("users.userid"))
    date = Column(Date)
    token = Column(String)
    used = Column(Boolean)
    passwordreset_users = relationship("Users", foreign_keys=[userid])


class TwitterUsers(base):
    __tablename__ = 'twitterusers'
    id = Column(Integer,primary_key=True)
    oauth_provider = Column(String)
    oauth_uid = Column(String, ForeignKey("users.twitterid"))
    oauth_token = Column(String)
    oauth_secret = Column(String)
    username = Column(String)
    twitterusers_users = relationship("Users", foreign_keys=[oauth_uid])


class Post(base):
    __tablename__ = 'posts'
    postid = Column(Integer,primary_key=True)
    userid = Column(Integer, ForeignKey("users.userid"))
    groupid = Column(Integer)
    objectid = Column(Integer)
    date = Column(Date)
    postcontent = Column(String)
    responseto = Column(Integer)
    threadid = Column(Integer, ForeignKey("thread.threadid"))
    post_thread = relationship("Thread", foreign_keys=[threadid])
    post_users = relationship("Users", foreign_keys=[userid])

class Thread(base):
    __tablename__ = 'thread'
    threadid = Column(Integer,primary_key=True)
    nickname = Column(String)
    name = Column(String)
    groupid = Column(Integer, ForeignKey("groups.groupid"))
    resolved = Column(Integer)
    retired = Column(Boolean)
    thread_group = relationship("Group", foreign_keys=[groupid])


class UsersGroups(base):
    __tablename__ = 'usersgroups'
    userid = Column(Integer, ForeignKey("users.userid"), primary_key=True)
    groupid = Column(Integer, ForeignKey("groups.groupid"), primary_key=True)
    usersgroups_users = relationship("Users", foreign_keys=[userid])
    usersgroups_groups = relationship("Group", foreign_keys=[groupid])


class Group(base):
    __tablename__ = 'groups'
    groupid = Column(Integer,primary_key=True)
    groupname = Column(String)
    userid = Column(Integer)
    bounds = Column(String)
    opengroup = Column(Boolean)


class Votes(base):
    __tablename__ = 'votes'
    userid = Column(Integer, ForeignKey("users.userid"), primary_key=True)
    postid = Column(Integer, ForeignKey("posts.postid"), primary_key=True)
    vote = Column(Integer)
    votes_posts = relationship("Post", foreign_keys=[postid])
    votes_users = relationship("Users", foreign_keys=[userid])


class InviteMe(base):
    __tablename__ = 'inviteme'
    requestid = Column(Integer, primary_key=True)
    userid = Column(Integer, ForeignKey("users.userid"))
    groupid = Column(Integer, ForeignKey("groups.groupid"))
    date = Column(Date)
    accepted = Column(Boolean)
    inviteme_users = relationship("Users",foreign_keys=[userid])
    inviteme_group = relationship("Group",foreign_keys=[groupid])

class GroupRequests(base):
    __tablename__= 'grouprequests'
    requestid = Column(Integer,primary_key=True)
    requester = Column(Integer, ForeignKey("users.userid"))
    invitee = Column(Integer)
    groupid = Column(Integer, ForeignKey("groups.groupid"))
    dateissued = Column(Date)
    complete = Column(Boolean)
    grouprequests_users = relationship("Users",foreign_keys=[requester])
    grouprequests_group = relationship("Group",foreign_keys=[groupid])