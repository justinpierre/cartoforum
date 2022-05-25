'''
Test Data validations on contributor sync

-*- coding: utf8 -*-
'''

__author__ = "Justin Pierre"

import unittest
import os
import sys
sys.path.append(os.getenv('cf'))

from src.orm_classes import sess
from flask import session, render_template, request, jsonify
from src.orm_classes import Group, Users, UsersGroups, Post, Thread, GroupRequests, InviteMe, Votes
from src.core import pgconnect, cur
from src.group_mgmt import cf_groups
from src.account_mgmt import logins
from src.cf_map import carto
import src


class test_create_user(unittest.TestCase):
    def setUp(self):
        self.tearDown()
        

    def tearDown(self):
        u_count = sess.query(Users).filter_by(username='test').count()
        if u_count > 0:
            userid = sess.query(Users).filter_by(username='test').one().userid
            sess.query(UsersGroups).filter_by(userid=userid).delete()
            sess.query(Group).filter_by(userid=userid).delete()
            sess.query(Users).filter_by(userid=userid).delete()
            sess.commit()
        return None

    def test_geom(self):
        uid = logins.create_account(username='test', password='secret', email='test@test.ca')
        gid = cf_groups.create_group(groupname='test', userid = uid, bounds = "0 0 1 1", opengroup='true')
        geom = "GEOMETRYCOLLECTION(POINT(40 60))"
        src.cf_map.carto.save_object(geom, uid, gid)

if __name__ == '__main__':
    unittest.main()
