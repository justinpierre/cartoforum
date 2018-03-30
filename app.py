# -*- coding: utf8 -*-

__author__ = u'justinpierre'

from flask import Flask
from flask import render_template, jsonify, request, session
from flask_mail import Mail

import psycopg2
import config
import datetime
import urlparse
from orm_classes import Users, Group, Post, Thread, UsersGroups, Votes, sess
import sqlalchemy
from sqlalchemy import asc


class Auth:
    CLIENT_ID = config.gid
    CLIENT_SECRET = config.gsecret
    REDIRECT_URI = 'https://cartoforum.com/gCallback'
    AUTH_URI = 'https://cf_accounts.google.com/o/oauth2/cf_accounts'
    TOKEN_URI = 'https://cf_accounts.google.com/o/oauth2/token'
    USER_INFO = 'https://www.googleapis.com/userinfo/v2/me'


cfapp = Flask(__name__)
mail = Mail(cfapp)

cfapp.config.update(
    DEBUG=True,
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False,
    MAIL_USERNAME=config.mailusername,
    MAIL_PASSWORD=config.mailpassword
    )
mail = Mail(cfapp)

cfapp.secret_key = config.secret_key
cfapp.config['SESSION_TYPE'] = 'filesystem'

try:
    pgconnect = psycopg2.connect(database=config.dbname, user=config.dbusername,
                                 password=config.dbpassword, host='localhost', port=config.dbport)
except:
    print("no connection")

cur = pgconnect.cursor()

from account_mgmt import logins, invites, twitter
from group_mgmt import cf_groups
from cf_map import forum


@cfapp.route('/')
def index():
    if not session.get('logged_in'):
        return render_template('index.html')
    else:
        username = sess.query(Users).filter_by(userid=session['userid']).one().username
        return render_template('groupselect.html', username=username)


# def get_google_auth(state=None, token=None):
#     if token:
#         return OAuth2Session(Auth.CLIENT_ID, token=token)
#     if state:
#         return OAuth2Session(
#             Auth.CLIENT_ID,
#             state=state,
#             redirect_uri=Auth.REDIRECT_URI)
#     oauth = OAuth2Session(
#         Auth.CLIENT_ID,
#         redirect_uri=Auth.REDIRECT_URI,
#         scope=Auth.SCOPE)
#     return oauth

@cfapp.route('/discovery', methods=['POST'])
def go_to_disc():
    return render_template('discovery.html')


@cfapp.route('/viewmap', methods=['GET'])
def readonly_view():
    session['groupid'] = groupid = request.args.get('group', 0, type=str)
    cur.execute("SELECT groupname,bounds from groups where groupid = {}".format(groupid))
    response = cur.fetchall()
    for row in response:
        groupname = row[0]
        bounds = row[1]
    return render_template('map.html', groupid=groupid, groupname=groupname, bounds=bounds, userid=0)


@cfapp.route('/_discovery_popup')
def discovery_popup():
    import config
    from requests.auth import HTTPBasicAuth
    import requests
    onlineresource = request.args.get('url')
    parsed = urlparse.urlparse(onlineresource)
    host = parsed.netloc
    if host != "cartoforum.com:8443":
        return "Host not allowed"
    r = requests.get(onlineresource,auth=HTTPBasicAuth(config.argoomapusername,config.argoomappassword))
    return r.text


@cfapp.route('/admin', methods=['POST'])
def go_to_admin():
    session['groupid'] = groupid = request.form['groupid']
    uid = sess.query(Group).filter_by(groupid=groupid).filter_by(userid=session['userid']).count()
    if uid == 1:
        return render_template("admin.html", groupid=groupid)
    else:
        return index()


@cfapp.route('/map', methods=['POST'])
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


@cfapp.route('/_get_post', methods=['GET'])
def get_post():
    thread_data = {}
    clicked_post = []
    indent = 0
    userid = session['userid'] if 'userid' in session else 0
    def get_replies(postid,clickedid,indent):
        indent += 10
        vtotal = voted = None
        for p3, t3, u3 in sess.query(Post, Thread, Users).filter_by(responseto=postid).order_by(asc(Post.date)).join(Thread).join(
                Users):
            responseto = sess.query(Post).filter_by(responseto=p3.postid).count()
            deleteable = False
            qry = sess.query(sqlalchemy.sql.func.sum(Votes.vote)).filter_by(postid=p3.postid)
            for res in qry.all():
                vtotal = res
            for v in sess.query(Votes).filter_by(postid=p3.postid).filter_by(userid=userid):
                voted = v.vote
            if p3.userid == userid and responseto==0:
                deleteable = True
            if p3.postid:
                thread_data[i]['posts'].append(
                    [p3.postid, p3.userid, p3.date, p3.objectid, p3.postcontent, t3.nickname, u3.username,
                     vtotal[0], voted, p3.postid in clicked_post, deleteable, indent])
            if responseto>0:
                get_replies(p3.postid,clickedid,indent)

    id = request.args.get('id', 0, type=int)
    data_type = request.args.get('type', 0, type=str)

    clicked_thread = {}
    retired_threads = []
    # get a list of retired threads
    for t in sess.query(Thread).filter_by(retired='t'):
        retired_threads.append(t.threadid)
    # create a list of threads related to the clicked object
    if data_type == "objid":
        for t in sess.query(Post).filter_by(objectid=id):
            if t.threadid in clicked_thread:
                continue
            else:
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
        indent = 0
        thread_name = sess.query(Thread).filter_by(threadid=i).one().nickname
        thread_data[i] = {"name": thread_name}
        thread_data[i]['posts'] = []
        if i in retired_threads:
            thread_data[i]['retired'] = True
        # set next_post equal to the clicked id and assume it is a response to something
        j= clickedid[0]
        # for j in clickedid:
        next_post = j
        responseto = True
        while responseto:
            for p in sess.query(Post).filter_by(postid=next_post):
                if p.responseto > 0:
                    next_post = p.responseto
                else:
                    responseto = False
        vtotal = voted = None
        # now next_post is the original post id
        indent = 0
        for p, t, u in sess.query(Post, Thread,Users).filter_by(postid=next_post).order_by(asc(Post.date)).join(Thread).join(Users):
            qry = sess.query(sqlalchemy.sql.func.sum(Votes.vote)).filter_by(postid=p.postid)
            for res in qry.all():
                vtotal = res
            for v in sess.query(Votes).filter_by(postid=p.postid).filter_by(userid=userid):
                voted = v.vote
            checkdeletable = sess.query(Post).filter_by(responseto=p.postid).count()
            deleteable = False
            responseto = True
            if checkdeletable == 0:
                deleteable = True
                responseto = False
            if p.postid:
                thread_data[i]['posts'].append([p.postid, p.userid, p.date, p.objectid, p.postcontent, t.nickname, u.username, vtotal[0], voted,p.postid in clicked_post,deleteable,indent])
            # for all responses get all responses until checkresponse == 0
            get_replies(next_post,clicked_post,indent)


    return jsonify(data=thread_data)


@cfapp.route('/_search_posts', methods = ['GET'])
def search_posts():
    userid = session['userid'] if 'userid' in session else 0
    posts = []
    qstr = request.args.get('q', 0, type=str)
    voted = vtotal = None
    for p, t, u in sess.query(Post, Thread, Users).order_by(Post.date).filter(Post.postcontent.like("%{}%".format(qstr))).join(Thread).filter_by(groupid=session['groupid']).join(Users):
        qry = sess.query(sqlalchemy.sql.func.sum(Votes.vote)).filter_by(postid=p.postid)
        for res in qry.all():
            vtotal = res
        for v in sess.query(Votes).filter_by(postid=p.postid).filter_by(userid=userid):
            voted = v.vote
        posts.append([p.postid, p.userid, p.date, p.objectid, p.postcontent, t.nickname, u.username, vtotal[0], voted])
    return jsonify(posts=posts)


@cfapp.route('/_zoom_to', methods=['GET'])
def zoom_to():
    bbox = ''
    objid = request.args.get('objid',0,type=int)
    cur.execute("Select ST_xmin(ST_Envelope(geom)), ST_ymin(ST_Envelope(geom)), ST_xmax(ST_Envelope(geom)), "
                "ST_ymax(ST_Envelope(geom)) from mapobjects where objectid={}".format(objid))
    response = cur.fetchall()
    for row in response:
        bbox = "{}, {}, {}, {}".format(row[0],row[1], row[2], row[3])
    return jsonify(bounds=bbox)


@cfapp.route('/_save_object', methods=['GET'])
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


@cfapp.route('/_save_thread', methods=['GET'])
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


if __name__ == '__main__':
    cfapp.run()
