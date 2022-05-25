# -*- coding: utf8 -*-

__author__ = 'justinpierre'
import os
import sys
sys.path.append(os.getenv('cf'))

from flask import render_template, request, session, Flask, jsonify
from flask_mail import Mail
import hashlib
import config
from orm_classes import Users, Group, sess, UsersGroups
from group_mgmt.cf_groups import cf_groups
from account_mgmt import logins, invites
from cf_map.carto import carto
from cf_map.forum import forum



cfapp = Flask(__name__)
cfapp.register_blueprint(cf_groups)
cfapp.register_blueprint(carto)
cfapp.register_blueprint(forum)

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


@cfapp.route('/_check_username', methods=['GET'])
def check_username():
    requestedname = request.args.get('name')
    taken = sess.query(Users).filter_by(username=requestedname).count()
    if taken > 0:
        return jsonify({requestedname: 'taken'})
    else:
        return jsonify({requestedname: 'ok'})

@cfapp.route('/login', methods=['POST'])
def do_login():
    for u in sess.query(Users).filter_by(username=request.form['username']):
        m = hashlib.sha256()
        m.update(request.form['password'].encode("utf-8"))
        hashpwd = m.hexdigest()
        if u.password.strip() == hashpwd or u.password.strip() == hashpwd[0:59]:
            session['logged_in'] = True
            session['userid'] = u.userid
        else:
            return render_template('index.html', login='failed')
    return index()

@cfapp.route('/_get_user_invites', methods=['GET'])
def get_user_invites():
    invreq = invites.get_user_invites(session['userid'])
    return jsonify(invites=invreq)


if __name__ == '__main__':
    cfapp.run(debug=True)
