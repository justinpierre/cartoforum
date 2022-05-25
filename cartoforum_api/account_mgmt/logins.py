import os
import sys
sys.path.append(os.getenv('cf'))
from cartoforum_api.orm_classes import sess
from flask import session, render_template, request, jsonify
from flask_mail import Message
from cartoforum_api.orm_classes import Users, PasswordReset
import hashlib
import datetime



# @cfapp.route('/groupselect', methods=['POST'])
def group_select():
    user = sess.query(Users).filter_by(userid=session['userid']).one()
    username = user.username
    return render_template('groupselect.html', username=username)


def create_account(**kwargs):
    m = hashlib.sha256()
    m.update(kwargs['password'].encode("utf-8"))
    hashpass = m.hexdigest()
    emailexists = sess.query(Users).filter_by(email=kwargs['email']).count()
    if emailexists > 0 and kwargs['email'] is not None:
        return False
    
    newuser = Users(email=kwargs['email'], password=hashpass, username=kwargs['username'])
    sess.add(newuser)
    sess.flush()
    sess.commit()
    sess.refresh(newuser)
    
    return newuser.userid


# @cfapp.route('/select_username', methods=['POST'])
def select_username():
    username = request.form['username']
    u = sess.query(Users).filter_by(userid=session['userid']).first()
    u.username = username
    sess.commit()
    # return app.index()


# @cfapp.route('/logout', methods=['POST'])
def do_logout():
    session['logged_in'] = False
    session['userid'] = None
    # return app.index()


# @cfapp.route('/_recover_password', methods=['POST'])
def recover_password():
    email = request.form['email']
    exists = sess.query(Users).filter_by(email=email).count()
    if exists == 0:
        return jsonify("Can't find that email address")
    elif exists > 1:
        return jsonify("Something terrible has happened")
    else:
        userid = sess.query(Users).filter_by(email=email).one().userid
        now = datetime.datetime.utcnow()
        m = hashlib.sha256()
        for i in [str(userid), str(now), email]:
            m.update(i.encode("utf-8"))
        token = m.hexdigest()
        newrequest = PasswordReset(userid=userid, token=token, date=now, used='f')
        sess.add(newrequest)
        sess.commit()
        resetlink = "https://cartoforum.com/resetpassword?token={}".format(token)
        msg = Message(
            'Hello',
            sender='Cartoforum',
            recipients=[email])
        msg.body = resetlink
        # mail.send(msg)
        return render_template('index.html', status='resetlinksent')


# @cfapp.route('/resetpassword', methods=['GET'])
def reset_password():
    token = request.args.get('token')
    userid = sess.query(PasswordReset).filter_by(token=token).filter_by(used='f').one().userid
    if userid > 0:
        return render_template('passwordreset.html', userid=userid)

