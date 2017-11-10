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

@app.route('/')
def index():
    content = u'Cartoforum'
    if not session.get('logged_in'):
        return render_template('index.html')
    else:
        return render_template('groupselect.html', content=content)


@app.route('/_jquerytest')
def jquerytest():
    return jsonify('blerg')


@app.route('/login', methods=['POST'])
def do_login():
    try:
        pgconnect = psycopg2.connect(database = config.dbname, user=config.dbusername,
                                 password=config.dbpassword, host='localhost',port=config.dbport)
    except:
        print ("no connection")
    cur = pgconnect.cursor()

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
    cur.close
    return index()

@app.route('/_get_user_groups', methods=['GET'])
def get_user_groups():
    try:
        pgconnect = psycopg2.connect(database = config.dbname, user=config.dbusername,
                                 password=config.dbpassword, host='localhost',port=config.dbport)
    except:
        print ("no connection")
    groups = []
    cur = pgconnect.cursor()
    cur.execute("SELECT groupname, groups.userid, groups.groupid FROM groups INNER JOIN usersgroups on "
                "groups.GroupID = usersgroups.GroupID "
                "WHERE usersgroups.UserID = {}".format(session['userid']))
    response = cur.fetchall()
    for row in response:
        if row[1] == session['userid']:
            groups.append({"name": row[0], "groupid": row[2], "admin": True})
        else:
            groups.append({"name": row[0], "groupid": row[2], "admin": False})
    return jsonify(groups = groups)


@app.route('/_go_to_group', methods=['POST'])
def go_to_group():
    data = request.json
    groupid = data['group']
    # Check for group membership
    return render_template('map.html',
                           groupid=groupid,
                           userid=session['userid']
                        )

if __name__ == '__main__':
    app.run()
