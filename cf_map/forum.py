from orm_classes import sess
from flask import session, render_template, request, jsonify
from orm_classes import Group, Users, UsersGroups, Post, Thread, Votes
from app import cfapp, cur, pgconnect
import sqlalchemy
import datetime
import re


@cfapp.route('/_get_group_threads', methods=['GET'])
def get_group_threads():
    groupid = session['groupid']
    threads = []
    for t in sess.query(Thread).filter_by(groupid=groupid):
        threads.append({"threadid": t.threadid, "name": t.nickname, "retired": t.retired})
    return jsonify(threads=threads)


@cfapp.route('/_get_thread_posts', methods=['GET'])
def get_thread_posts():
    threads = []
    threadid = request.args.get('threadid', 0, type=str)
    for t in sess.query(Thread).filter_by(threadid=threadid):
        threads.append({"threadid": t.threadid, "name": t.nickname, "retired": t.retired, "posts": []})
        for p, t, u in sess.query(Post, Thread, Users).filter_by(threadid=threadid).join(Thread).join(Users):
            threads[len(threads)-1]["posts"].append([p.postid, p.userid, p.date, p.objectid, p.postcontent, t.nickname,
                                                     u.username])
    return jsonify(threads=threads)


@cfapp.route('/_recent_posts', methods=['GET'])
def recent_posts():
    userid = session['userid'] if 'userid' in session else 0
    posts = []
    voted = vtotal = None
    for p, t, u in sess.query(Post, Thread, Users).order_by(Post.date.desc()).join(Thread).\
            filter_by(groupid=session['groupid']).join(Users):
        qry = sess.query(sqlalchemy.sql.func.sum(Votes.vote)).filter_by(postid=p.postid)
        for res in qry.all():
            vtotal = res
        for v in sess.query(Votes).filter_by(postid=p.postid).filter_by(userid=userid):
            voted = v.vote
        posts.append([p.postid, p.userid, p.date, p.objectid, p.postcontent, t.nickname, u.username, vtotal[0] or 0,
                      voted or 0])
    return jsonify(posts=posts)


@cfapp.route('/_user_posts', methods=['GET'])
def user_posts():
    vtotal = voted = None
    userid = request.args.get('userid', 0, type=str)
    posts = []
    for p, t, u in sess.query(Post, Thread, Users).filter_by(userid=userid).join(Thread).join(Users):
        qry = sess.query(sqlalchemy.sql.func.sum(Votes.vote)).filter_by(postid=p.postid)
        for res in qry.all():
            vtotal = res
        for v in sess.query(Votes).filter_by(postid=p.postid).filter_by(userid=session['userid']):
            voted = v.vote
        posts.append([p.postid, p.userid, p.date, p.objectid, p.postcontent, t.nickname, u.username, vtotal[0] or 0,
                      voted or 0])
    return jsonify(posts=posts)


@cfapp.route('/_posts_by_extent', methods=['GET'])
def posts_by_extent():
    posts = []
    extent = request.args.get('ext', 0, type=str)
    extent = re.sub(' ', ',', extent)
    for geometrytype in ['POINT', 'LINE', 'POLYGON']:
        cur.execute("SELECT posts.postid, posts.userid, posts.date, posts.objectid, posts.postcontent, thread.nickname,"
                    "users.username FROM posts INNER JOIN thread on thread.threadid = posts.threadid INNER JOIN "
                    "mapobjects on posts.objectid = mapobjects.objectid INNER JOIN users on users.userid = posts.userid"
                    "WHERE posts.groupid = {} and ST_Within(mapobjects.geom,ST_MakeEnvelope({}, 3857)) "
                    "AND ST_AsText(geom) like '{}%' Order by date DESC;".
                    format(session['groupid'], extent, geometrytype))
        response = cur.fetchall()
        for row in response:
            voted = vtotal = None
            qry = sess.query(sqlalchemy.sql.func.sum(Votes.vote)).filter_by(postid=row[0])
            for res in qry.all():
                vtotal = res
            for v in sess.query(Votes).filter_by(postid=row[0]).filter_by(userid=session['userid']):
                voted = v.vote
            posts.append([row[0], row[1], row[2], row[3], row[4], row[5], row[6], vtotal[0], voted])
    return jsonify(posts=posts)


@cfapp.route('/_delete_post', methods=['GET'])
def delete_post():
    postid = request.args.get('postid', 0, type=int)
    is_this_my_post = sess.query(Post).filter_by(userid=session['userid']).filter_by(postid=postid).one()
    if is_this_my_post.userid != session['userid']:
        return jsonify('request not allowed')
    objectid = is_this_my_post.objectid
    canIdelete = sess.query(Post).filter_by(responseto=postid).count()
    if canIdelete > 0:
        return jsonify('request not allowed')
    sess.query(Post).filter_by(userid=session['userid']).filter_by(postid=postid).delete()
    sess.commit()
    # check if you can delete the geometry
    usingobject = cur.execute("SELECT count(*) from posts where objectid = {}".format(objectid))
    response = cur.fetchall()
    for row in response:
        if row[0] == 0:
            cur.execute("DELETE from mapobjects where objectid = {}".format(objectid))
            pgconnect.commit()
    return jsonify('success')


@cfapp.route('/_save_post', methods=['POST'])
def save_post():
    threadid = request.form['threadid']
    replyID = request.form['replyID']
    objid = request.form['objid']
    if not objid:
        objid = 0
    text = request.form['text']
    ug = sess.query(UsersGroups).filter_by(userid=session['userid']).filter_by(groupid=session['groupid']).one().userid
    if not ug:
        return jsonify("user not permitted to do this")

    if replyID:
        thread_id = sess.query(Post).filter_by(postid=replyID).one().threadid
        insert_post = Post(userid=session['userid'], groupid=session['groupid'], date=datetime.datetime.utcnow(),
                           responseto=replyID, objectid=objid, postcontent=text, threadid=thread_id)

    else:
        insert_post = Post(userid=session['userid'], groupid=session['groupid'], date=datetime.datetime.utcnow(),
                           objectid=objid, postcontent=text, threadid=threadid)
    sess.add(insert_post)
    sess.commit()
    return jsonify("success")


@cfapp.route('/_cast_vote', methods=['GET'])
def cast_vote():
    post = request.args.get('post', 0, type=int)
    vote = request.args.get('vote', 0, type=int)
    v = sess.query(Votes).filter_by(userid=session['userid']).filter_by(postid=post).count()
    if v > 0:
        v = sess.query(Votes).filter_by(userid=session['userid']).filter_by(postid=post).first()
        v.vote = vote
        sess.commit()
        return jsonify('vote updated')
    else:
        v = Votes(postid=post, userid=session['userid'], vote=vote)
        sess.add(v)
        sess.commit()
        return jsonify('new vote cast')
