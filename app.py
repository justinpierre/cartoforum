# -*- coding: utf8 -*-

__author__ = u'justinpierre'

from flask import Flask
from flask import render_template, request, session
from flask_mail import Mail

import psycopg2
import config
from orm_classes import Users, Group, sess


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

from account_mgmt import logins, invites, twitter, google
from group_mgmt import cf_groups
from cf_map import forum, carto


@cfapp.route('/')
def index():
    if not session.get('logged_in'):
        return render_template('index.html')
    else:
        username = sess.query(Users).filter_by(userid=session['userid']).one().username
        return render_template('groupselect.html', username=username)


@cfapp.route('/admin', methods=['POST'])
def go_to_admin():
    session['groupid'] = groupid = request.form['groupid']
    uid = sess.query(Group).filter_by(groupid=groupid).filter_by(userid=session['userid']).count()
    if uid == 1:
        return render_template("admin.html", groupid=groupid)
    else:
        return index()


if __name__ == '__main__':
    cfapp.run()
