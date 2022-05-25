import os
import sys
sys.path.append(os.getenv('cf'))

from cartoforum_api.orm_classes import sess
from flask import session, request, jsonify, Blueprint
from cartoforum_api.orm_classes import Users, UsersGroups, Post, Thread, Votes

import sqlalchemy
import datetime
import re
from sqlalchemy import asc
from . import carto

forum = Blueprint('forum', __name__)

@forum.route('/_get_group_threads', methods=['GET'])
def get_group_threads():
    groupid = session['groupid']
    threads = []
    for t in sess.query(Thread).filter_by(groupid=groupid):
        threads.append({"threadid": t.threadid, "name": t.nickname, "retired": t.retired})
    return jsonify(threads=threads)


@forum.route('/_get_thread_posts', methods=['GET'])
def get_thread_posts():
    userid = session['userid'] if 'userid' in session else 0
    threads = []
    threadid = request.args.get('threadid', 0, type=str)
    for t in sess.query(Thread).filter_by(threadid=threadid):
        threads.append({"threadid": t.threadid, "name": t.nickname, "retired": t.retired, "posts": []})
        for p, th, u in sess.query(Post, Thread, Users).filter_by(threadid=threadid).join(Thread).join(Users):
            voted = vtotal = None
            qry = sess.query(sqlalchemy.sql.func.sum(Votes.vote)).filter_by(postid=p.postid)
            for res in qry.all():
                vtotal = res
            for v in sess.query(Votes).filter_by(postid=p.postid).filter_by(userid=userid):
                voted = v.vote
            threads[len(threads)-1]["posts"].append([p.postid, p.userid, p.date, p.objectid, p.postcontent, t.nickname, u.username, vtotal[0] or 0,
                                                     voted or 0])
    return jsonify(threads=threads)


@forum.route('/_recent_posts', methods=['GET'])
def recent_posts():
    userid = session['userid'] if 'userid' in session else 0
    posts = []

    for p, t, u in sess.query(Post, Thread, Users).order_by(Post.date.desc()).join(Thread).\
            filter_by(groupid=session['groupid']).join(Users):
        voted = vtotal = None
        qry = sess.query(sqlalchemy.sql.func.sum(Votes.vote)).filter_by(postid=p.postid)
        for res in qry.all():
            vtotal = res
        for v in sess.query(Votes).filter_by(postid=p.postid).filter_by(userid=userid):
            voted = v.vote
        posts.append([p.postid, p.userid, p.date, p.objectid, p.postcontent, t.nickname, u.username, vtotal[0] or 0,
                      voted or 0])
    return jsonify(posts=posts)


@forum.route('/_user_posts', methods=['GET'])
def user_posts():
    vtotal = voted = None
    userid = request.args.get('userid', 0, type=str)
    posts = []
    for p, t, u in sess.query(Post, Thread, Users).filter_by(userid=userid).filter_by(groupid=session['groupid']).\
            join(Thread).join(Users):
        qry = sess.query(sqlalchemy.sql.func.sum(Votes.vote)).filter_by(postid=p.postid)
        for res in qry.all():
            vtotal = res
        for v in sess.query(Votes).filter_by(postid=p.postid).filter_by(userid=session['userid']):
            voted = v.vote
        posts.append([p.postid, p.userid, p.date, p.objectid, p.postcontent, t.nickname, u.username, vtotal[0] or 0,
                      voted or 0])
    return jsonify(posts=posts)


@forum.route('/_posts_by_extent', methods=['GET'])
def posts_by_extent():
    posts = []
    extent = request.args.get('ext', 0, type=str)
    extent = re.sub(' ', ',', extent)
    for geometrytype in ['POINT', 'LINE', 'POLYGON']:
        cur.execute("SELECT posts.postid, posts.userid, posts.date, posts.objectid, posts.postcontent, thread.nickname,"
                    "users.username FROM posts INNER JOIN thread on thread.threadid = posts.threadid INNER JOIN "
                    "mapobjects on posts.objectid = mapobjects.objectid INNER JOIN users on users.userid = posts.userid"
                    " WHERE posts.groupid = {} and ST_Within(mapobjects.geom,ST_MakeEnvelope({}, 3857)) "
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


@forum.route('/_delete_post', methods=['GET'])
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


@forum.route('/_save_post', methods=['POST'])
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


@forum.route('/_cast_vote', methods=['GET'])
def cast_vote():
    post = request.args.get('post', 0, type=int)
    vote = request.args.get('vote', 0, type=int)
    v = sess.query(Votes).filter_by(userid=session['userid']).filter_by(postid=post)
    if v.count() > 0:
        v = sess.query(Votes).filter_by(userid=session['userid']).filter_by(postid=post).first()
        v.vote = vote
    else:
        v = Votes(postid=post, userid=session['userid'], vote=vote)
        sess.add(v)
    sess.commit()
    pid = sess.query(Votes).filter_by(userid=session['userid']).filter_by(postid=post).one().postid
    oid = sess.query(Post).filter_by(postid=pid).one().objectid
    score_ind = carto.update_object_stats(oid)
    return jsonify(score_ind)

@forum.route('/_save_thread', methods=['GET'])
def save_thread():
    nick = request.args.get('nick', 0, type=str)
    name = request.args.get('name', 0, type=str)
    ug = sess.query(UsersGroups).filter_by(userid=session['userid']).filter_by(groupid=session['groupid']).one().userid
    if not ug:
        return jsonify("user not permitted to do this")

    t_exists = sess.query(Thread).filter_by(nickname=nick).filter_by(groupid=session['groupid']).count()
    if t_exists == 1:
        return jsonify("group already exists")
    try:
        insert_thread = Thread(nickname=nick, groupid=session['groupid'])
        sess.add(insert_thread)
        sess.commit()
        return jsonify("success")
    except:
        return jsonify("something went wrong")


@forum.route('/_get_post', methods=['GET'])
def get_post():
    handled_postids = []
    thread_data = {}
    clicked_post = []
    indent = 0
    userid = session['userid'] if 'userid' in session else 0
    def get_replies(postid,clickedid,indent):
        indent += 10
        vtotal = voted = None
        for p3, t3, u3 in sess.query(Post, Thread, Users).filter_by(responseto=postid).order_by(asc(Post.date))\
                .join(Thread).join(
                Users):
            responseto = sess.query(Post).filter_by(responseto=p3.postid).count()
            deleteable = False
            qry = sess.query(sqlalchemy.sql.func.sum(Votes.vote)).filter_by(postid=p3.postid)
            for res in qry.all():
                vtotal = res
            for v in sess.query(Votes).filter_by(postid=p3.postid).filter_by(userid=userid):
                voted = v.vote
            if p3.userid == userid and responseto == 0:
                deleteable = True
            if p3.postid:
                thread_data[i]['posts'].append(
                    [p3.postid, p3.userid, p3.date, p3.objectid, p3.postcontent, t3.nickname, u3.username,
                     vtotal[0], voted, p3.postid in clicked_post, deleteable, indent])
            if responseto>0:
                get_replies(p3.postid, clickedid, indent)

    id = request.args.get('id', 0, type=int)
    data_type = request.args.get('type', 0, type=str)

    clicked_thread = {}
    retired_threads = []
    # get a list of retired threads
    for t in sess.query(Thread).filter_by(retired='t'):
        retired_threads.append(t.threadid)
    # create a list of threads related to the clicked object
    if data_type == "objid":
        for t in sess.query(Post).filter_by(objectid=id):
            if t.threadid in clicked_thread:
                continue
            else:
                clicked_thread[t.threadid] = []
        for t, v in clicked_thread.iteritems():
            for p in sess.query(Post).filter_by(objectid=id).filter_by(threadid=t):
                clicked_thread[t].append(p.postid)
                clicked_post.append(p.postid)
    else:
        clicked_post.append(id)
        t = sess.query(Post).filter_by(postid=id).one().threadid
        clicked_thread[t] = [id]
    # figure out every thread, recursive conversation list, clicked or not, votes
    for i, clickedid in clicked_thread.iteritems():
        indent = 0
        thread_name = sess.query(Thread).filter_by(threadid=i).one().nickname
        thread_data[i] = {"name": thread_name}
        thread_data[i]['posts'] = []
        if i in retired_threads:
            thread_data[i]['retired'] = True
        # set next_post equal to the clicked id and assume it is a response to something
        for j in clickedid:
            next_post = j
            responseto = True
            while responseto:
                for p in sess.query(Post).filter_by(postid=next_post):
                    if p.responseto > 0:
                        next_post = p.responseto
                    else:
                        responseto = False
            vtotal = voted = None
            # now next_post is the original post id
            # make sure we don't report on the same chain twice
            if next_post in handled_postids:
                continue
            handled_postids.append(next_post)

            indent = 0
            for p, t, u in sess.query(Post, Thread, Users).filter_by(postid=next_post).order_by(asc(Post.date))\
                    .join(Thread).join(Users):
                qry = sess.query(sqlalchemy.sql.func.sum(Votes.vote)).filter_by(postid=p.postid)
                for res in qry.all():
                    vtotal = res
                for v in sess.query(Votes).filter_by(postid=p.postid).filter_by(userid=userid):
                    voted = v.vote
                checkdeletable = sess.query(Post).filter_by(responseto=p.postid).count()
                deleteable = False
                responseto = True
                if checkdeletable == 0:
                    deleteable = True
                    responseto = False
                if p.postid:
                    thread_data[i]['posts'].append([p.postid, p.userid, p.date, p.objectid, p.postcontent, t.nickname,
                                                    u.username, vtotal[0], voted, p.postid in clicked_post, deleteable,
                                                    indent])
                # for all responses get all responses until checkresponse == 0
                get_replies(next_post, clicked_post, indent)
    return jsonify(data=thread_data)


@forum.route('/_search_posts', methods=['GET'])
def search_posts():
    userid = session['userid'] if 'userid' in session else 0
    posts = []
    qstr = request.args.get('q', 0, type=str)
    voted = vtotal = None
    for p, t, u in sess.query(Post, Thread, Users).order_by(Post.date).filter(
            Post.postcontent.like("%{}%".format(qstr))).join(Thread).filter_by(groupid=session['groupid']).join(Users):
        qry = sess.query(sqlalchemy.sql.func.sum(Votes.vote)).filter_by(postid=p.postid)
        for res in qry.all():
            vtotal = res
        for v in sess.query(Votes).filter_by(postid=p.postid).filter_by(userid=userid):
            voted = v.vote
        posts.append([p.postid, p.userid, p.date, p.objectid, p.postcontent, t.nickname, u.username, vtotal[0], voted])
    return jsonify(posts=posts)
