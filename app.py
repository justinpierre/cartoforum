# -*- coding: utf8 -*-

__author__ = u'justinpierre'

from flask import Flask
from flask import render_template, jsonify, flash, redirect, request, session, abort, url_for


import psycopg2
import hashlib
import config
import datetime
import urlparse
import re
from flask_oauth import OAuth


import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer, Date, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship

oauth = OAuth()
twitter = oauth.remote_app('twitter',
                           base_url='https://api.twitter.com/1/',
                           request_token_url='https://api.twitter.com/oauth/request_token',
                           access_token_url='https://api.twitter.com/oauth/access_token',
                           authorize_url='https://api.twitter.com/oauth/authorize',
                           consumer_key=config.ckey,
                           consumer_secret=config.csecret
                           )

db_string = "postgres://{}:{}@localhost:5432/{}".format(config.dbusername,config.dbpassword,config.dbname)
db = create_engine(db_string)
base = declarative_base()

class Users(base):
    __tablename__ = 'users'
    userid = Column(Integer,primary_key=True)
    username = Column(String)
    password = Column(String)
    email = Column(String)
    verified = Column(Boolean)
    twitterid = Column(Integer)


class TwitterUsers(base):
    __tablename__ = 'twitterusers'
    id = Column(Integer,primary_key=True)
    oauth_provider = Column(String)
    oauth_uid = Column(String)
    oauth_token = Column(String)
    oauth_secret = Column(String)
    username = Column(String)


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


@app.route('/groupselect', methods=['POST'])
def group_select():
    username = sess.query(Users).filter_by(userid=session['userid']).one().username
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

@app.route('/logout', methods=['POST'])
def do_logout():
    session['logged_in'] = False
    session['userid'] = None
    return index()


@app.route('/twitter-oauth', methods=['POST'])
def twitter_oauth():
    if session.has_key('twitter_token'):
        del session['twitter_token']
    return twitter.authorize(callback=url_for('oauth_authorized',
                             next=request.args.get('next') or request.referrer or None))


@app.route('/oauth-authorized')
@twitter.authorized_handler
def oauth_authorized(resp):
    next_url = request.args.get('next') or url_for('index')
    if resp is None:
        flash(u'You denied the request to sign in.')
        return redirect(next_url)

    session['twitter_token'] = (
        resp['oauth_token'],
        resp['oauth_token_secret']
    )
    session['twitter_user'] = resp['screen_name']
    twitteruser = sess.query(TwitterUsers).filter_by(username=resp['screen_name']).count()
    print(twitteruser)

    flash('You were signed in as %s' % resp['screen_name'])
    if twitteruser == 0:
        tu = TwitterUsers(oauth_provider='twitter', username=resp['screen_name'], oauth_uid=resp['user_id'],
                          oauth_token=resp['oauth_token'], oauth_secret=resp['oauth_token_secret'])
        sess.add(tu)
        sess.commit()

    else:
        tu = sess.query(TwitterUsers).filter_by(username=resp['screen_name']).first()
        tu.oauth_token = resp['oauth_token']
        tu.oauth_secret = resp['oauth_token_secret']
        sess.commit()
    userquery = sess.query(Users).filter_by(username='@{}'.format(resp['screen_name'])).count()
    if userquery == 0:
        newuser = Users(username='@{}'.format(resp['screen_name']), password='twitter_user', twitterid=resp['user_id'])
        sess.add(newuser)
        sess.commit()
    tulogged = sess.query(Users).filter_by(username='@{}'.format(resp['screen_name'])).one()
    session['userid'] = tulogged.userid
    session['logged_in'] = True
    return render_template('groupselect.html', username=resp['screen_name'])


@twitter.tokengetter
def get_twitter_token(token=None):
    return session.get('twitter_token')


@app.route('/_get_user_groups', methods=['GET'])
def get_user_groups():
    groups = []
    for g, u in sess.query(Group, UsersGroups).join(UsersGroups).filter_by(userid=session['userid']):
        if g.userid == session['userid']:
            groups.append({"name":g.groupname, "groupid": g.groupid, "admin": "true"})
        else:
            groups.append({"name": g.groupname, "groupid": g.groupid, "admin": "false"})
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
    import config
    from requests.auth import HTTPBasicAuth
    import requests
    onlineresource = request.args.get('url')
    parsed = urlparse.urlparse(onlineresource)
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
    groupid = session['groupid']
    threads = []
    for t in sess.query(Thread).filter_by(groupid=groupid):
        threads.append({"threadid": t.threadid, "name": t.nickname, "retired": t.retired})
    return jsonify(threads=threads)


@app.route('/_get_thread_posts', methods=['GET'])
def get_thread_posts():
    threads=[]
    threadid = request.args.get('threadid', 0, type=str)
    for t in sess.query(Thread).filter_by(threadid=threadid):
        threads.append({"threadid": t.threadid, "name": t.nickname, "retired": t.retired, "posts" : []})
        for p,t,u in sess.query(Post,Thread,Users).filter_by(threadid=threadid).join(Thread).join(Users):
            threads[len(threads)-1]["posts"].append([p.postid, p.userid, p.date, p.objectid, p.postcontent, t.nickname, u.username])
    return jsonify(threads=threads)


@app.route('/_get_group_users', methods=['GET'])
def get_group_users():
    group_users = {}
    for ug, u in sess.query(UsersGroups,Users).filter_by(groupid=session['groupid']).join(Users):
        group_users[ug.userid] = u.username
    return jsonify(group_users=group_users)


@app.route('/map', methods=['POST'])
def go_to_group():
    groupid = request.form['groupid']
    session['groupid'] = request.form['groupid']
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
    posts = []
    voted = vtotal = None
    for p, t, u in sess.query(Post, Thread, Users).order_by(Post.date).join(Thread).filter_by(groupid=session['groupid']).join(Users):
        qry = sess.query(sqlalchemy.sql.func.sum(Votes.vote)).filter_by(postid=p.postid)
        for res in qry.all():
            vtotal = res
        for v in sess.query(Votes).filter_by(postid=p.postid).filter_by(userid=session['userid']):
            voted = v.vote
        posts.append([p.postid, p.userid, p.date, p.objectid, p.postcontent, t.nickname, u.username, vtotal[0] or 0, voted or 0])
    return jsonify(posts=posts)


@app.route('/_user_posts', methods=['GET'])
def user_posts():
    userid = request.args.get('userid',0,type=str)
    posts = []
    for p, t in sess.query(Post, Thread).filter_by(userid=userid).join(Thread):
        qry = sess.query(sqlalchemy.sql.func.sum(Votes.vote)).filter_by(postid=p.postid)
        for res in qry.all():
            vtotal = res
        for v in sess.query(Votes).filter_by(postid=p.postid).filter_by(userid=session['userid']):
            voted = v.vote
        posts.append([p.postid, p.userid, p.date, p.objectid, p.postcontent, t.nickname, vtotal[0], voted])
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
    for t in sess.query(Thread).filter_by(retired='t'):
        retired_threads.append(t.threadid)
    # create a list of threads related to the clicked object
    if data_type == "objid":
        for t in sess.query(Post).filter_by(objectid=id):
            clicked_thread[t.threadid] = []
        for t, v in clicked_thread.iteritems():
            for p in sess.query(Post).filter_by(objectid=id).filter_by(threadid=t):
                clicked_thread[t].append(p.postid)
                clicked_post.append(p.postid)
    else:
        clicked_post.append(id)
        t = sess.query(Post).filter_by(postid=id).one().threadid
        clicked_thread[t] = [id]
    # figure out every thread, recursive conversation list, clicked or not, votes
    for i, clickedid in clicked_thread.iteritems():
        thread_name = sess.query(Thread).filter_by(threadid=i).one().nickname
        thread_data[i] = {"name": thread_name}
        thread_data[i]['posts'] = []
        if i in retired_threads:
            thread_data[i]['retired'] = True
        # set next_post equal to the clicked id and assume it is a response to something
        next_post = clickedid[0]
        responseto = True
        while responseto:
            for p in sess.query(Post).filter_by(postid=next_post):
                if p.responseto > 0:
                    next_post = p.responseto
                else:
                    responseto = False
        vtotal = voted = None
        # now next_post is the original post id
        for p, t, u in sess.query(Post, Thread,Users).filter_by(postid=next_post).join(Thread).join(Users):
            qry = sess.query(sqlalchemy.sql.func.sum(Votes.vote)).filter_by(postid=p.postid)
            for res in qry.all():
                vtotal = res
            for v in sess.query(Votes).filter_by(postid=p.postid).filter_by(userid=session['userid']):
                voted = v.vote
            thread_data[i]['posts'].append([p.postid, p.userid, p.date, p.objectid, p.postcontent, t.nickname, u.username, vtotal[0], voted,p.postid in clicked_post])
            responseto = True
            while responseto:
                for p2 in sess.query(Post).filter_by(responseto=next_post):
                    next_post = p2.postid
                    checkresponse = sess.query(Post).filter_by(responseto=next_post).count()
                    if checkresponse == 0:
                        responseto = False
                    for p3, t3, u3 in sess.query(Post, Thread, Users).filter_by(postid=next_post).join(Thread).join(Users):
                        deleteable = False
                        qry = sess.query(sqlalchemy.sql.func.sum(Votes.vote)).filter_by(postid=p3.postid)
                        for res in qry.all():
                            vtotal = res
                        for v in sess.query(Votes).filter_by(postid=p3.postid).filter_by(userid=session['userid']):
                            voted = v.vote
                        if p3.userid == session['userid'] and not responseto:
                            deleteable = True
                        thread_data[i]['posts'].append(
                            [p3.postid, p3.userid, p3.date, p3.objectid, p3.postcontent, t3.nickname, u3.username, vtotal[0],
                             voted, p3.postid in clicked_post, deleteable])

    return jsonify(data=thread_data)


@app.route('/_search_posts', methods = ['GET'])
def search_posts():
    posts = []
    qstr = request.args.get('q', 0, type=str)
    voted = vtotal = None
    for p, t, u in sess.query(Post, Thread, Users).order_by(Post.date).filter(Post.postcontent.like("%{}%".format(qstr))).join(Thread).filter_by(groupid=session['groupid']).join(Users):
        qry = sess.query(sqlalchemy.sql.func.sum(Votes.vote)).filter_by(postid=p.postid)
        for res in qry.all():
            vtotal = res
        for v in sess.query(Votes).filter_by(postid=p.postid).filter_by(userid=session['userid']):
            voted = v.vote
        posts.append([p.postid, p.userid, p.date, p.objectid, p.postcontent, t.nickname, u.username, vtotal[0], voted])
    return jsonify(posts=posts)


@app.route('/_posts_by_extent', methods=['GET'])
def posts_by_extent():
    posts = []
    extent = request.args.get('ext', 0, type=str)
    extent = re.sub(' ',',',extent)
    for geometrytype in ['POINT','LINE','POLYGON']:
        cur.execute("SELECT posts.postid, posts.userid, posts.date, posts.objectid, posts.postcontent, thread.nickname, users.username "
                    "FROM posts INNER JOIN thread on thread.threadid = posts.threadid INNER JOIN mapobjects on posts.objectid = mapobjects.objectid "
                    "INNER JOIN users on users.userid = posts.userid WHERE posts.groupid = {} and ST_Within(mapobjects.geom,ST_MakeEnvelope({}, 3857)) "
                    "AND ST_AsText(geom) like '{}%' Order by date DESC;".format(session['groupid'],extent,geometrytype))
        response = cur.fetchall()
        for row in response:
            voted = vtotal = None
            qry = sess.query(sqlalchemy.sql.func.sum(Votes.vote)).filter_by(postid=row[0])
            for res in qry.all():
                vtotal = res
            for v in sess.query(Votes).filter_by(postid=row[0]).filter_by(userid=session['userid']):
                voted = v.vote
            posts.append([row[0], row[1], row[2], row[3], row[4], row[5], row[6], vtotal[0], voted])
    return jsonify(posts=posts)


@app.route('/_zoom_to',methods=['GET'])
def zoom_to():
    bbox = ''
    objid = request.args.get('objid',0,type=int)
    cur.execute("Select ST_xmin(ST_Envelope(geom)), ST_ymin(ST_Envelope(geom)), ST_xmax(ST_Envelope(geom)), "
                "ST_ymax(ST_Envelope(geom)) from mapobjects where objectid={}".format(objid))
    response = cur.fetchall()
    for row in response:
        bbox = "{}, {}, {}, {}".format(row[0],row[1], row[2], row[3])
    return jsonify(bounds=bbox)

@app.route('/_save_object', methods=['GET'])
def save_object():
    geom = request.args.get('jsonshp',0,type=str)
    geom = urlparse.unquote(geom)
    query = cur.execute("SELECT count(*) FROM mapobjects where geom = ST_GeomFromText('{}',3857) AND userid = {} and date > (now() - INTERVAL '2 MINUTE');".format(geom,session["userid"]))
    response = cur.fetchall()
    for row in response:
        if row[0]>0:
            return None
    cur.execute("INSERT INTO mapobjects (geom, groupid, userid, date) VALUES (ST_GeomFromText('{}',3857), {}, {}, '{}');".format(geom,session['groupid'],session['userid'],datetime.datetime.utcnow()))
    pgconnect.commit()
    query = cur.execute("SELECT objectid FROM mapobjects WHERE userid = {0} AND date = (SELECT max(date) FROM mapobjects WHERE userid = {0});".format(session["userid"]))
    response = cur.fetchall()
    for row in response:
        return jsonify(objid=row[0])


@app.route('/_save_post', methods = ['POST'])
def save_post():
    threadid = request.form['threadid']
    replyID = request.form['replyID']
    objid = request.form['objid']
    text = request.form['text']
    ug = sess.query(UsersGroups).filter_by(userid=session['userid']).filter_by(groupid=session['groupid']).one().userid
    if not ug:
        return jsonify("user not permitted to do this")

    if replyID:
        thread_id = sess.query(Post).filter_by(postid=replyID).one().threadid
        insert_post = Post(userid=session['userid'], groupid=session['groupid'], date=datetime.datetime.utcnow(),
                           responseto=replyID,objectid=objid,postcontent=text,threadid=thread_id)

    else:
        insert_post = Post(userid=session['userid'], groupid=session['groupid'], date=datetime.datetime.utcnow(),
                           objectid=objid, postcontent=text, threadid=threadid)
    sess.add(insert_post)
    sess.commit()
    return jsonify("success")


@app.route('/_save_thread', methods=['GET'])
def save_thread():
    nick = request.args.get('nick', 0, type=str)
    name = request.args.get('name', 0, type=str)
    ug = sess.query(UsersGroups).filter_by(userid=session['userid']).filter_by(groupid=session['groupid']).one().userid
    if not ug:
        return jsonify("user not permitted to do this")

    t_exists = sess.query(Thread).filter_by(nickname=nick).filter_by(groupid=session['groupid'])
    if not t_exists:
        return jsonify("group already exists")
    try:
        insert_thread = Thread(nickname=nick, name=name, groupid=session['groupid'])
        sess.add(insert_thread)
        sess.commit()
        return jsonify("success")
    except:
        return jsonify("something went wrong")


@app.route('/_cast_vote', methods=['GET'])
def cast_vote():
    post = request.args.get('post', 0, type=int)
    vote = request.args.get('vote',0, type=int)
    v = sess.query(Votes).filter_by(userid=session['userid']).filter_by(postid=post).count()
    if v > 0:
        v = sess.query(Votes).filter_by(userid=session['userid']).filter_by(postid=post).first()
        v.vote = vote
        sess.commit()
        return jsonify('vote updated')
    else:
        v = Votes(postid=post, userid=session['userid'], vote=vote)
        sess.add(v)
        sess.commit()
        return jsonify('new vote cast')



if __name__ == '__main__':
    app.run()
