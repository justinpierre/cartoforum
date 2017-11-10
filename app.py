# -*- coding: utf8 -*-

__author__ = u'justinpierre'

from flask import Flask
from flask import render_template, jsonify, flash, redirect, request, session, abort
import psycopg2
import hashlib
import config

app = Flask(__name__)


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
        m.update(request.form['password'])
        m.digest()
        if row[1] == '\\x{}'.format(m):
            session['logged_in'] = True
            session['userid'] = row[0]
        else:
            flash('wrong password')

    return index()


if __name__ == '__main__':
    app.secret_key = config.secret_key
    app.run()
