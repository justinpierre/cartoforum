from orm_classes import sess
from flask import session, render_template, request, jsonify
from orm_classes import Group, Users, UsersGroups, Post, Thread
from app import cfapp, cur, pgconnect


@cfapp.route('/_get_user_groups', methods=['GET'])
def get_user_groups():
    groups = []
    for g, u in sess.query(Group, UsersGroups).join(UsersGroups).filter_by(userid=session['userid']):
        if g.userid == session['userid']:
            groups.append({"name": g.groupname, "groupid": g.groupid, "admin": "true"})
        else:
            groups.append({"name": g.groupname, "groupid": g.groupid, "admin": "false"})
    return jsonify(groups=groups)


@cfapp.route('/_get_group_users', methods=['GET'])
def get_group_users():
    users = []
    for u, ug in sess.query(Users, UsersGroups).join(UsersGroups).filter_by(groupid=session['groupid']):
        users.append({"name": u.username, "userid": u.userid})
    return jsonify(users=users)


@cfapp.route('/createGroup', methods=['GET'])
def create_group():
    groupname = request.args.get('groupname')
    bounds = request.args.get('bounds')
    bounds_arr = request.args.get('bounds').split(" ")
    opengroup = 'false'
    if request.args.get('opengroup') == 'on':
        opengroup = 'true'
    cur.execute("INSERT INTO groups (geom, groupname, userid, bounds,opengroup) "
                "VALUES (ST_Centroid(ST_GeomFromText('MULTIPOINT ({} {},{} {})')), '{}', {}, '{}', {})".
                format(bounds_arr[0], bounds_arr[1], bounds_arr[2], bounds_arr[3], groupname, session['userid'],
                       bounds, opengroup))
    cur.execute("SELECT groupid FROM groups WHERE groupname = '{}'".format(groupname))
    response = cur.fetchall()
    for row in response:
        groupid = row[0]
    cur.execute("INSERT INTO usersgroups VALUES ({},{})".format(session['userid'], groupid))
    pgconnect.commit()
    return jsonify(groupid=groupid)


@cfapp.route('/delete_group', methods=['POST'])
def delete_group():
    cur.execute("Delete from mapobjects where groupid = {}".format(session['groupid']))
    pgconnect.commit()
    sess.query(Post).filter_by(groupid=session['groupid']).delete()
    sess.query(Thread).filter_by(groupid=session['groupid']).delete()
    sess.query(Group).filter_by(groupid=session['groupid']).delete()
    return render_template('groupselect.html')
