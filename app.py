from flask import Flask
from flask import render_template, jsonify, flash, redirect, request, session, abort
import psycopg2

app = Flask(__name__)


@app.route('/')
def index():
    content = u'Cartoforum'
    if not session.get('logged_in'):
        return render_template('groupselect.html')
    else:
        return render_template('index.html', content=content)


@app.route('/_jquerytest')
def jquerytest():
    return jsonify('blerg')


@app.route('/login', methods=['POST'])
def do_login():
    if request.form['password'] == 'password' and request.form['username'] == 'admin':
        session['logged_in'] = True
    else:
        flash('wrong password')
    return index()


if __name__ == '__main__':
    app.run()
