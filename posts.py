# -*- coding: utf8 -*-

__author__ = u'justinpierre'

from flask import Flask
from flask import render_template, jsonify, flash, redirect, request, session, abort
from flask import Session

import psycopg2
import hashlib
import config
import posts

@app.route('/_recent_posts')
def recent_posts():
    groupid = request.form['groupid']
    posts = []
    try:
        pgconnect = psycopg2.connect(database=config.dbname, user=config.dbusername,
                                     password=config.dbpassword, host='localhost', port=config.dbport)
    except:
        print("no connection")

    cur = pgconnect.cursor()

    query = "SELECT posts.postid, posts.userid, posts.date, posts.objectid, posts.postcontent, thread.nickname " \
            "FROM posts INNER JOIN thread on thread.threadid = posts.threadid " \
            "WHERE posts.groupid = {} Order by date DESC limit 20;".format(groupid)

    response = cur.fetchall()
    for row in response:
        posts.append(row)
    return jsonify(posts=posts)