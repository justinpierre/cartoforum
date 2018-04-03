import datetime
from orm_classes import sess, Users, TwitterUsers
from flask import session, render_template, request, url_for, flash,redirect
from app import cfapp
from flask_oauth import OAuth

import config

oauth = OAuth()
twitter = oauth.remote_app('twitter',
                           base_url='https://api.twitter.com/1/',
                           request_token_url='https://api.twitter.com/oauth/request_token',
                           access_token_url='https://api.twitter.com/oauth/access_token',
                           authorize_url='https://api.twitter.com/oauth/authorize',
                           consumer_key=config.ckey,
                           consumer_secret=config.csecret
                           )

@cfapp.route('/twitter-oauth', methods=['POST'])
def twitter_oauth():
    if session.has_key('twitter_token'):
        del session['twitter_token']
    return twitter.authorize(callback=url_for('oauth_authorized',
                             next=request.args.get('next') or request.referrer or None))


@cfapp.route('/oauth-authorized')
@twitter.authorized_handler
def oauth_authorized(resp):
    next_url = request.args.get('next') or url_for('index')
    if resp is None:
        flash(u'You denied the request to sign in.')
        return redirect(next_url)

    session['twitter_token'] = (
        resp['oauth_token'],
        resp['oauth_token_secret']
    )
    session['twitter_user'] = resp['screen_name']
    twitteruser = sess.query(TwitterUsers).filter_by(username=resp['screen_name']).count()

    flash('You were signed in as %s' % resp['screen_name'])
    if twitteruser == 0:
        tu = TwitterUsers(oauth_provider='twitter', username=resp['screen_name'], oauth_uid=resp['user_id'],
                          oauth_token=resp['oauth_token'], oauth_secret=resp['oauth_token_secret'])
        sess.add(tu)
        sess.commit()

    else:
        tu = sess.query(TwitterUsers).filter_by(username=resp['screen_name']).first()
        tu.oauth_token = resp['oauth_token']
        tu.oauth_secret = resp['oauth_token_secret']
        sess.commit()
    userquery = sess.query(Users).filter_by(username='@{}'.format(resp['screen_name'])).count()
    if userquery == 0:
        newuser = Users(username='@{}'.format(resp['screen_name']), password='twitter_user', twitterid=resp['user_id'])
        sess.add(newuser)
        sess.commit()
    tulogged = sess.query(Users).filter_by(username='@{}'.format(resp['screen_name'])).one()
    session['userid'] = tulogged.userid
    session['logged_in'] = True
    return render_template('groupselect.html', username=resp['screen_name'])


@twitter.tokengetter
def get_twitter_token(token=None):
    return session.get('twitter_token')
