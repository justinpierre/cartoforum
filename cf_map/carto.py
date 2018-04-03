from flask import session, render_template, request, jsonify
from app import cfapp, cur, pgconnect
import datetime
import urlparse


@cfapp.route('/_save_object', methods=['GET'])
def save_object():
    geom = request.args.get('jsonshp', 0, type=str)
    geom = urlparse.unquote(geom)
    query = cur.execute("SELECT count(*) FROM mapobjects where geom = ST_GeomFromText('{}',3857) AND userid = {} and "
                        "date > (now() - INTERVAL '2 MINUTE');".format(geom, session["userid"]))
    response = cur.fetchall()
    for row in response:
        if row[0] > 0:
            return None

    cur.execute("INSERT INTO mapobjects (geom, groupid, userid, date) VALUES (ST_GeomFromText('{}',3857), {}, {}, "
                "'{}');".format(geom, session['groupid'], session['userid'], datetime.datetime.utcnow()))
    pgconnect.commit()
    query = cur.execute("SELECT objectid FROM mapobjects WHERE userid = {0} AND date = (SELECT max(date) "
                        "FROM mapobjects WHERE userid = {0});".format(session["userid"]))
    response = cur.fetchall()
    for row in response:
        return jsonify(objid=row[0])


@cfapp.route('/_zoom_to', methods=['GET'])
def zoom_to():
    bbox = ''
    objid = request.args.get('objid', 0, type=int)
    cur.execute("Select ST_xmin(ST_Envelope(geom)), ST_ymin(ST_Envelope(geom)), ST_xmax(ST_Envelope(geom)), "
                "ST_ymax(ST_Envelope(geom)) from mapobjects where objectid={}".format(objid))
    response = cur.fetchall()
    for row in response:
        bbox = "{}, {}, {}, {}".format(row[0], row[1], row[2], row[3])
    return jsonify(bounds=bbox)


@cfapp.route('/map', methods=['POST'])
def go_to_group():
    groupid = request.form['groupid']
    session['groupid'] = request.form['groupid']
    cur.execute("SELECT groupname,bounds from groups where groupid = {}".format(groupid))
    response = cur.fetchall()
    for row in response:
        groupname = row[0]
        bounds = row[1]
    # Check for group membership, return group name and bounds and username
    pgconnect.commit()
    return render_template('map.html',
                           groupid=groupid,
                           userid=session['userid'],
                           groupname=groupname,
                           bounds=bounds
                           )


@cfapp.route('/discovery', methods=['POST'])
def go_to_disc():
    return render_template('discovery.html')


@cfapp.route('/viewmap', methods=['GET'])
def readonly_view():
    session['groupid'] = groupid = request.args.get('group', 0, type=str)
    cur.execute("SELECT groupname,bounds from groups where groupid = {}".format(groupid))
    response = cur.fetchall()
    for row in response:
        groupname = row[0]
        bounds = row[1]
    return render_template('map.html', groupid=groupid, groupname=groupname, bounds=bounds, userid=0)


@cfapp.route('/_discovery_popup')
def discovery_popup():
    import config
    from requests.auth import HTTPBasicAuth
    import requests
    onlineresource = request.args.get('url')
    parsed = urlparse.urlparse(onlineresource)
    host = parsed.netloc
    if host != "cartoforum.com:8443":
        return "Host not allowed"
    r = requests.get(onlineresource, auth=HTTPBasicAuth(config.argoomapusername, config.argoomappassword))
    return r.text
