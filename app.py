# -*- coding: utf8 -*-

__author__ = u'justinpierre'

from flask import Flask
from flask import render_template, jsonify, flash, redirect, request, session, abort
from flask import Session

import psycopg2
import hashlib
import config

from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer, Date, Boolean,ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship

db_string = "postgres://{}:{}@localhost:5432/{}".format(config.dbusername,config.dbpassword,config.dbname)
db = create_engine(db_string)
base = declarative_base()

class Post(base):
    __tablename__ = 'posts'
    postid = Column(Integer,primary_key=True)
    userid = Column(Integer)
    groupid = Column(Integer)
    objectid = Column(Integer)
    date = Column(Date)
    postcontent = Column(String)
    responseto = Column(Integer)
    threadid = Column(Integer, ForeignKey("thread.threadid"))
    post_thread = relationship("Thread", foreign_keys=[threadid])

class Thread(base):
    __tablename__ = 'thread'
    threadid = Column(Integer,primary_key=True)
    nickname = Column(String)
    name = Column(String)
    groupid = Column(Integer)
    resolved = Column(Integer)
    retired = Column(Boolean)


app = Flask(__name__)

Session = sessionmaker(db)
sess = Session()
base.metadata.create_all(db)

app.secret_key = config.secret_key
app.config['SESSION_TYPE'] = 'filesystem'
try:
    pgconnect = psycopg2.connect(database=config.dbname, user=config.dbusername,
                                 password=config.dbpassword, host='localhost', port=config.dbport)
except:
    print("no connection")

cur = pgconnect.cursor()


@app.route('/')
def index():
    if not session.get('logged_in'):
        return render_template('index.html')
    else:
        cur.execute("SELECT username from users where userid = {}".format(session['userid']))
        response = cur.fetchall()
        for row in response:
            username = row[0]
        return render_template('groupselect.html', username=username)


@app.route('/login', methods=['POST'])
def do_login():
    query = "SELECT userid, password FROM users WHERE username = '{}'".format(request.form['username'])
    cur.execute(query)
    response = cur.fetchall()
    for row in response:
        m = hashlib.sha256()
        m.update(request.form['password'].encode("utf-8"))
        hashpwd = m.hexdigest()
        if row[1] == '\\x{}'.format(hashpwd):
            session['logged_in'] = True
            session['userid'] = row[0]
        else:
            flash('wrong password')
    pgconnect.commit()
    return index()


@app.route('/_get_user_groups', methods=['GET'])
def get_user_groups():
    groups = []
    cur.execute("SELECT groupname, groups.userid, groups.groupid FROM groups INNER JOIN usersgroups on "
                "groups.GroupID = usersgroups.GroupID "
                "WHERE usersgroups.UserID = {}".format(session['userid']))
    response = cur.fetchall()
    for row in response:
        if row[1] == session['userid']:
            groups.append({"name": row[0], "groupid": row[2], "admin": "true"})
        else:
            groups.append({"name": row[0], "groupid": row[2], "admin": "false"})
    pgconnect.commit()
    return jsonify(groups=groups)


@app.route('/_get_user_invites', methods=['GET'])
def get_user_invites():
    invreq = {'invites': [], 'requests': []}
    cur.execute("SELECT grouprequests.requestid, users.username, groups.groupname, grouprequests.dateissued "
                "FROM grouprequests INNER JOIN users ON users.userid = grouprequests.requester "
                "JOIN groups ON groups.groupid = grouprequests.groupid  "
                "WHERE complete = false AND invitee = '{}'".format(session['userid']))
    response = cur.fetchall()
    for row in response:
        invreq['invites'].append({"requestid": row[0], "requester": row[1], "group": row[2], "date": row[3]})

    cur.execute("SELECT inviteme.requestid, users.username, groups.groupname, inviteme.date "
                "FROM inviteme INNER JOIN users ON users.userid = inviteme.userid "
                "JOIN groups ON groups.groupid = inviteme.groupid  "
                "WHERE accepted is null AND groups.userid = '{}'".format(session['userid']))
    response = cur.fetchall()
    for row in response:
        invreq['requests'].append({"requestid": row[0], "requester": row[1], "group": [2], "date": row[3]})
    pgconnect.commit()
    return jsonify(invites=invreq)


@app.route('/manageRequest', methods=['POST'])
def manage_request():
    requestid = request.form['requestid']
    action = request.form['submit']

    cur.execute("SELECT groupid,userid FROM inviteme WHERE requestid = {};".format(requestid))
    response = cur.fetchall()

    for row in response:
        if action == 'accept':
            # make sure it doesn't add twice
            cur.execute("INSERT INTO usersgroups VALUES ({},{})".format(row[1],row[0]))
        cur.execute("UPDATE inviteme set accepted = 't' WHERE requestid = {}".format(requestid))
        pgconnect.commit()
    return render_template('groupselect.html')


@app.route('/manageInvite', methods=['POST'])
def accept_invite():
    requestid = request.form['requestid']
    action = request.form['submit']

    cur.execute("SELECT groupid FROM grouprequests WHERE requestid = {};".format(requestid))
    response = cur.fetchall()
    for row in response:
        if action == 'accept':
            # make sure it doesn't add twice
            cur.execute("INSERT INTO usersgroups VALUES ({},{})".format(session['userid'],row[0]))
        cur.execute("UPDATE grouprequests set complete = true WHERE requestid = {}".format(requestid))
        pgconnect.commit()
    return render_template('groupselect.html')


@app.route('/createGroup', methods=['POST'])
def create_group():
    groupname = request.json['groupname']
    bounds = request.json['bounds']
    bounds_arr = request.json['bounds'].split(" ")
    opengroup = 'false'
    if request.json['opengroup'] == 'on':
        opengroup = 'true'
    cur.execute("INSERT INTO groups (geom, groupname, userid, bounds,opengroup) "
                "VALUES (ST_Centroid(ST_GeomFromText('MULTIPOINT ({} {},{} {})')), '{}', {}, '{}', {})".
                format(bounds_arr[0],bounds_arr[1],bounds_arr[2],bounds_arr[3],groupname,session['userid'],bounds,opengroup))
    cur.execute("SELECT groupid FROM groups WHERE groupname = '{}'".format(groupname))
    response = cur.fetchall()
    for row in response:
        groupid = row[0]
    cur.execute("INSERT INTO usersgroups VALUES ({},{})".format(session['userid'],groupid))
    pgconnect.commit()
    return groupid

@app.route('/discovery', methods=['POST'])
def go_to_disc():
    return render_template('discovery.html')


@app.route('/_discovery_popup')
def discovery_popup():
    from urlparse import urlparse
    import config
    from requests.auth import HTTPBasicAuth
    import requests
    onlineresource = request.args.get('url')
    parsed = urlparse(onlineresource)
    host = parsed.netloc

    if host != "127.0.0.1:8080":
        return "Host not allowed"
    r = requests.get(onlineresource,auth=HTTPBasicAuth(config.argoomapusername,config.argoomappassword))
    return r.text


@app.route('/admin', methods=['POST'])
def go_to_admin():
    groupid = request.form['gropuid']
    cur.execute("SELECT userid, username from groups where groupid = {}".format(groupid))
    response = cur.fetchall()
    for row in response:
        if row[0] != session['userid']:
            return index()
        else:
            return render_template("admin.html",groupid=groupid,username=row[1])


@app.route('/_get_group_threads', methods=['GET'])
def get_group_threads():
    groupid = request.args.get('groupid')
    query = cur.execute("Select * FROM thread WHERE groupid = {}".format(groupid))
    response = cur.fetchall(query)
    threads = []
    for row in response:
        threads.append({"threadid": row[0], "name": row[1], "retired": row[5], "posts" : []})

        query = cur.execute("SELECT postcontent, SUM(vote) AS votetotal FROM posts left JOIN votes ON posts.postid = votes.postid " \
                "WHERE posts.threadid = {} GROUP BY postcontent ORDER BY votetotal DESC;".format(row[0]))

        response2 =  cur.fetchall(query)
        for row2 in response2:
            threads[len(threads)-1]["posts"].append({"postcontent": row2[0], "votes": row2[1]})
    pgconnect.commit()
    return jsonify(threads=threads)


@app.route('/map', methods=['POST'])
def go_to_group():
    groupid = request.form['groupid']
    cur.execute("SELECT groupname,bounds from groups where groupid = {}".format(groupid))
    response = cur.fetchall()
    for row in response:
        groupname = row[0]
        bounds = row[1]
    # Check for group membership, return group name and bounds and username
    return render_template('map.html',
                           groupid=groupid,
                           userid=session['userid'],
                           groupname=groupname,
                           bounds=bounds
                           )
    pgconnect.commit()


@app.route('/_recent_posts', methods=['GET'])
def recent_posts():
    groupid = request.args.get('groupid', 0, type=str)
    posts = []

    for p, t in sess.query(Post, Thread).join(Thread).where(Post.groupid == groupid):
        print(p.postcontent, t.nickname)
        posts.append([p.postid, p.userid, p.date, p.objectid, p.postcontent, t.nickname])
    return jsonify(posts=posts)


@app.route('/_get_post', methods=['GET'])
def get_post():
    id = request.args.get('id', 0, type=int)
    data_type = request.args.get('type', 0, type=str)
    thread_data = {}
    clicked_post = []
    clicked_thread = {}
    retired_threads = []
    # get a list of retired threads
    for t in sess.query(Thread).where(Thread.retired == 't'):
        retired_threads.append(t.threadid)
    # create a list of threads related to the clicked object
    if data_type == "objid":
        for t in sess.query(Post).where(Post.objectid == id):
            clicked_thread[t.threadid] = []
        for t, v in clicked_thread.iteritems:
            for p in sess.query(Post).where(Post.objectid == id).where(Post.threadid == t):
                clicked_thread[t].append(p.postid)
                clicked_post.append(p.postid)

    else:
        clicked_post.append(id)
        t = sess.query(Thread).where(Thread.threadid == id).one().threadid
        clicked_thread[t] = [id]

    # figure out every thread, recursive conversation list, clicked or not, votes

    for i, clickedid in clicked_thread.iteritems():
        thread_name = sess.query(Thread).where(Thread.threadid == i)
        thread_data[i] = {"name": thread_name}
        thread_data[i]['posts'] = []
        if i in retired_threads:
            thread_data[i]['retired'] = True

        original_post = clickedid[0]
        responseto = True
        while responseto:
            for p, r in sess.query(Post, Thread).join(Thread).where(Post.threadid == i
                                                                    and Post.postid == original_post):
                if p.responseto > 0:
                    original_post = p.responseto
                else:
                    responseto = False

        # also join username and vote count
        for p, t in sess.query(Post, Thread).join(Thread).where(Post.threadid == i).where(Post.postid == original_post):
            thread_data[i]['posts'].append({"postid": p.postid, "userposted": p.userid, "date": p.date,
                                           "post": p.postcontent, "objectid": p.objectid})


if __name__ == '__main__':
    app.run()
