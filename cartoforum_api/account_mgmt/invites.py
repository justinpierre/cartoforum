import os
import sys
sys.path.append(os.getenv('cf'))

import datetime
from cartoforum_api.orm_classes import sess
from flask import session, render_template, request, jsonify
from cartoforum_api.orm_classes import GroupRequests, Group, Users, UsersGroups, InviteMe
from cartoforum_api.core import cur, pgconnect


# @cfapp.route('/invite_user', methods=['GET'])
def invite_user():
    invitee = request.args.get('invitee', type=str)
    try:
        inviteeuserid = sess.query(Users).filter_by(username=invitee).one().userid
    except:
        return jsonify(response="user doesn't exist")
    inviteexists = sess.query(GroupRequests).filter_by(invitee=inviteeuserid).\
        filter_by(groupid=session['groupid']).count()
    if inviteexists > 0:
        return jsonify(response='invite already exists')
    useringroup = sess.query(UsersGroups).filter_by(groupid=session['groupid']).filter_by(userid=inviteeuserid).count()
    if useringroup > 0:
        return jsonify(response='user already in group')
    newinvite = GroupRequests(requester=session['userid'], invitee=inviteeuserid, groupid=session['groupid'],
                              dateissued=datetime.datetime.utcnow(), complete='f')
    sess.add(newinvite)
    sess.commit()
    return jsonify(response='invite sent')


def get_user_invites(userid):
    invreq = {'invites': [], 'requests': []}
    for gr, g, u in sess.query(GroupRequests, Group, Users).filter_by(invitee=userid).\
            filter_by(complete='f').join(Group).join(Users):
        invreq['requests'].append({"requestid": gr.requestid, "requester": u.username, "group": g.groupname,
                                   "date": gr.dateissued})

    cur.execute("SELECT inviteme.requestid, users.username, groups.groupname, inviteme.date "
                "FROM inviteme INNER JOIN users ON users.userid = inviteme.userid "
                "JOIN groups ON groups.groupid = inviteme.groupid  "
                "WHERE accepted is null AND groups.userid = '{}'".format(userid))
    response = cur.fetchall()
    for row in response:
        invreq['invites'].append({"requestid": row[0], "requester": row[1], "group": [2], "date": row[3]})
    pgconnect.commit()
    return invreq
    


# @cfapp.route('/manageRequest', methods=['POST'])
def manage_request():
    requestid = request.form['requestid']
    action = request.form['submit']
    cur.execute("SELECT groupid,invitee FROM grouprequests WHERE requestid = {};".format(requestid))
    response = cur.fetchall()
    for row in response:
        if action == 'accept':
            # make sure it doesn't add twice
            cur.execute("INSERT INTO usersgroups VALUES ({},{})".format(row[1], row[0]))
        cur.execute("UPDATE grouprequests set complete = 't' WHERE requestid = {}".format(requestid))
        pgconnect.commit()
    return render_template('groupselect.html')


# @cfapp.route('/manageInvite', methods=['POST'])
def accept_invite():
    requestid = request.form['requestid']
    action = request.form['submit']

    cur.execute("SELECT groupid,userid FROM inviteme WHERE requestid = {};".format(requestid))
    response = cur.fetchall()
    for row in response:
        if action == 'accept':
            # make sure it doesn't add twice
            cur.execute("INSERT INTO usersgroups VALUES ({},{})".format(row[1], row[0]))
        cur.execute("UPDATE inviteme set accepted = 't' WHERE requestid = {}".format(requestid))
        pgconnect.commit()
    return render_template('groupselect.html')


# @cfapp.route('/request_invite', methods=['POST'])
def request_invite():
    gid = request.form['gid']
    newinvite = InviteMe(userid=session['userid'], groupid=gid, date=datetime.datetime.utcnow())
    sess.add(newinvite)
    sess.commit()
    return render_template("discovery.html", invite="sent")
