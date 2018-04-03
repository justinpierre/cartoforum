import config
from flask import redirect, url_for, session, request, flash, render_template
from app import cfapp
from orm_classes import sess, Users, TwitterUsers
import json
import urllib2
from rauth import OAuth2Service

GOOGLE_LOGIN_CLIENT_ID = config.gid
GOOGLE_LOGIN_CLIENT_SECRET = config.gsecret

OAUTH_CREDENTIALS={
        'google': {
            'id': GOOGLE_LOGIN_CLIENT_ID,
            'secret': GOOGLE_LOGIN_CLIENT_SECRET
        }
}


class OAuthSignIn(object):
    providers = None

    def __init__(self, provider_name):
        self.provider_name = provider_name
        credentials = OAUTH_CREDENTIALS[provider_name]
        self.consumer_id = credentials['id']
        self.consumer_secret = credentials['secret']

    def authorize(self):
        pass

    def callback(self):
        pass

    def get_callback_url(self):
        return url_for('oauth_callback', _external=True)

    @classmethod
    def get_provider(self, provider_name):
        if self.providers is None:
            self.providers={}
            for provider_class in self.__subclasses__():
                provider = provider_class()
                self.providers[provider.provider_name] = provider
        return self.providers[provider_name]


class GoogleSignIn(OAuthSignIn):
    def __init__(self):
        super(GoogleSignIn, self).__init__('google')
        googleinfo = urllib2.urlopen('https://accounts.google.com/.well-known/openid-configuration')
        google_params = json.load(googleinfo)
        self.service = OAuth2Service(
                name='google',
                client_id=self.consumer_id,
                client_secret=self.consumer_secret,
                authorize_url=google_params.get('authorization_endpoint'),
                base_url=google_params.get('userinfo_endpoint'),
                access_token_url=google_params.get('token_endpoint')
        )

    def authorize(self):
        return redirect(self.service.get_authorize_url(
            scope='email',
            response_type='code',
            redirect_uri=self.get_callback_url())
            )

    def callback(self):
        if 'code' not in request.args:
            return None, None, None
        oauth_session = self.service.get_auth_session(
                data={'code': request.args['code'],
                      'grant_type': 'authorization_code',
                      'redirect_uri': self.get_callback_url()
                     },
                decoder=json.loads
        )
        me = oauth_session.get('').json()
        return (me['name'],
                me['email'])


@cfapp.route('/authorize/<provider>')
def oauth_authorize(provider):
    # Flask-Login function
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()


@cfapp.route('/gCallback')
def oauth_callback():
    provider = 'google'
    oauth = OAuthSignIn.get_provider(provider)
    username, email = oauth.callback()
    if email is None:
        # I need a valid email address for my user identification
        flash('Authentication failed.')
        return redirect(url_for('index'))
    # Look if the user already exists
    nickname = username
    if username is None or username == "":
        nickname = email.split('@')[0]

    googleuser = sess.query(TwitterUsers).filter_by(username=nickname).filter_by(oauth_provider='google')\
        .count()
    # log in oauth database
    if googleuser == 0:
        gu = TwitterUsers(oauth_provider='google', username=nickname, oauth_uid=nickname)
        sess.add(gu)
        sess.commit()
    else:
        gu = sess.query(TwitterUsers).filter_by(username=nickname).filter_by(oauth_provider='google').first()
        sess.commit()
    # log in users table
    userquery = sess.query(Users).filter_by(username='{}'.format(nickname)).count()
    if userquery == 0:
        newuser = Users(username='{}'.format(nickname), password='google_user')
        sess.add(newuser)
        sess.commit()
    tulogged = sess.query(Users).filter_by(username='{}'.format(nickname)).one()
    session['userid'] = tulogged.userid
    session['logged_in'] = True

    return render_template('groupselect.html', username=nickname)
