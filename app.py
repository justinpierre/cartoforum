# -*- coding: utf8 -*-

__author__ = 'justinpierre'

from flask import Flask, jsonify
from flask import render_template, request, session
from flask_mail import Mail


import config
import src
from src.orm_classes import Users, Group, sess, UsersGroups
from src.group_mgmt import cf_groups
from src.account_mgmt import logins


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


@cfapp.route('/createGroup', methods=['GET'])
def create_group():
    groupname = request.args.get('groupname')
    bounds = request.args.get('bounds')
    
    opengroup = 'false'
    if request.args.get('opengroup') == 'on':
        opengroup = 'true'
    resp = cf_groups.create_group(groupname=groupname, bounds=bounds,opengroup=opengroup,userid=session['userid'])
    return jsonify(resp)

@cfapp.route('/create_account', methods=['POST'])
def create_account():
    username = request.form['username']
    email = request.form['email']
    if email in ['email address', '']:
        email = None
    password = request.form['password']
    create = logins.create_account(username=username, email=email, password=password)
    if create:
        return render_template('index.html', account='created')
    else:
        return render_template(email)

@cfapp.route('/save_object', methods=['POST'])
def save_object():
    geom = request.args.get('jsonshp', 0, type=str)
    geom = urlparse.unquote(geom)
    oid = src.cf_map.carto.save_object(geom)
    return jsonify(objid=oid, userid=session['userid'], groupid=session['groupid'])

if __name__ == '__main__':
    cfapp.run(debug=True)
