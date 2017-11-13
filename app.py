# -*- coding: utf8 -*-

__author__ = u'justinpierre'

from flask import Flask
from flask import render_template, jsonify, flash, redirect, request, session, abort
from flask import Session

import psycopg2
import hashlib
import config

app = Flask(__name__)
sess = Session()
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
    content = u'Cartoforum'
    if not session.get('logged_in'):
        return render_template('index.html')
    else:
        return render_template('groupselect.html', content=content)


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
            groups.append({"name": row[0], "groupid": row[2], "admin": True})
        else:
            groups.append({"name": row[0], "groupid": row[2], "admin": False})
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
            cur.execute("INSERT INTO usersgroups VALUES ({},{})".format(session['userid'],row[0]))
        cur.execute("UPDATE grouprequests set complete = true WHERE requestid = {}".format(requestid))
        pgconnect.commit()
    return render_template('groupselect.html')


@app.route('/createGroup', methods=['POST'])
def create_group():
    groupname = request.form['groupName']
    bounds = request.form['bounds']
    bounds_arr = request.form['bounds'].split(" ")
    opengroup = 'false'
    if request.form['opengroup'] == 'on':
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
    return render_template('groupselect.html')


@app.route('/_go_to_disc')
def go_to_disc():
    return render_template('index2.html')



@app.route('/map', methods=['POST'])
def go_to_group():
    groupid = request.form['groupid']
    cur.execute("SELECT groupname,bounds from groups where groupid = {}".format(groupid))
    response  = cur.fetchall()
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
    cur = pgconnect.cursor()
    query = "SELECT posts.postid, posts.userid, posts.date, posts.objectid, posts.postcontent, thread.nickname " \
            "FROM posts INNER JOIN thread on thread.threadid = posts.threadid " \
            "WHERE posts.groupid = {} Order by date DESC limit 20;".format(groupid)
    cur.execute(query)

    response = cur.fetchall()
    for row in response:
        posts.append(row)
    return jsonify(posts=posts)
    pgconnect.commit()

if __name__ == '__main__':
    app.run()
