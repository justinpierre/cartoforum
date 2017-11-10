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
        groups.append(row[0])
    return jsonify(groups = groups)


if __name__ == '__main__':
    app.run()
