from orm_classes import sess, Users, TwitterUsers
from flask import session, render_template, request, url_for, flash, redirect
from app import cfapp
from flask_oauth import OAuth
import utils

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
    if 'twitter_token' in session:
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
    username = resp['screen_name']
    session['twitter_user'] = username
    # check if twitter user has already logged in to cartoforum
    twitteruser = sess.query(TwitterUsers).filter_by(username=username).count()

    flash('You were signed in as %s' % username)
    if twitteruser == 0:
        tu = TwitterUsers(oauth_provider='twitter', username=username, oauth_uid=resp['user_id'],
                          oauth_token=resp['oauth_token'], oauth_secret=resp['oauth_token_secret'])
        sess.add(tu)
        sess.commit()

    else:
        tu = sess.query(TwitterUsers).filter_by(username=username).first()
        tu.oauth_token = resp['oauth_token']
        tu.oauth_secret = resp['oauth_token_secret']
        sess.commit()

    # check if the twitter users screen name has already been taken.
    userquery = sess.query(Users).filter_by(username='{}'.format(username)).count()

    if userquery == 0:
        # move on with their twitter screen name
        newuser = Users(username='{}'.format(username), password='twitter_user', twitterid=resp['user_id'])
        sess.add(newuser)
        sess.commit()
    else:
        # this username exists, is the twitterid different from what we have logged?
        twitterid = sess.query(TwitterUsers).filter_by(username='{}'.format(username)).count()
        if twitterid == 0:
            # offer them a different name
            alt_name = utils.get_alternate_username(session['twitter_user'])
            return render_template('select_username.html', alt_name=alt_name)
        else:
            username = sess.query(Users).filter_by(twitterid=resp['user_id']).one().username

    tulogged = sess.query(Users).filter_by(username='{}'.format(username)).one()
    session['userid'] = tulogged.userid
    session['logged_in'] = True
    return render_template('groupselect.html', username=username)


@twitter.tokengetter
def get_twitter_token():
    return session.get('twitter_token')


@cfapp.route("/_select_username_for_twitter", methods=['POST'])
def select_username_for_twitter():
    alt_name = request.form['username']
    userquery = sess.query(Users).filter_by(username='{}'.format(alt_name)).count()
    if userquery == 0:
        # move on with their alt
        twitterid = sess.query(TwitterUsers).filter_by(username=session['twitter_user']).one().oauth_uid
        newuser = Users(username='{}'.format(alt_name), password='twitter_user', twitterid=twitterid)
        sess.add(newuser)
        sess.commit()
        tulogged = sess.query(Users).filter_by(username='{}'.format(alt_name)).one()
        session['userid'] = tulogged.userid
        session['logged_in'] = True
        return render_template('groupselect.html', username=alt_name)
    else:
        # offer them a different name
        alt_name = utils.get_alternate_username(session['twitter_user'])
        return render_template('select_username.html', alt_name=alt_name)
