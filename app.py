from flask import Flask
from flask import render_template,jsonify

app = Flask(__name__)


@app.route('/')
def index():
    content = u"Cartoforum"
    return render_template('index.html',content=content)

@app.route('/_jquerytest')
def jquerytest():
    return jsonify('blerg')

if __name__ == '__main__':
    app.run()
