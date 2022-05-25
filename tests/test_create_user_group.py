'''
Test Data validations on contributor sync

-*- coding: utf8 -*-
'''

__author__ = "Justin Pierre"

import unittest
import os
import sys
sys.path.append('/cartoforum/src')

from orm_classes import sess
from flask import session, render_template, request, jsonify
from orm_classes import Group, Users, UsersGroups, Post, Thread, GroupRequests, InviteMe, Votes
from core import pgconnect, cur
from group_mgmt import cf_groups
from account_mgmt import logins

class test_create_uesr(unittest.TestCase):
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

    def test_create_user(self):
        uid = logins.create_account(username='test', password='secret', email='test@test.ca')
        self.assertTrue(uid)
    def test_create_group(self):
        uid = logins.create_account(username='test', password='secret', email='test@test.ca')
        cf_groups.create_group(groupname='test', userid = uid, bounds = "0 0 1 1", opengroup='true')
        gid = sess.query(Group).filter_by(userid=uid).one().groupid
        self.assertTrue(gid)
        ug = sess.query(UsersGroups).filter_by(userid=uid).filter_by(groupid=gid).one().uid
        self.assertEqual(ug, uid)

if __name__ == '__main__':
    unittest.main()
