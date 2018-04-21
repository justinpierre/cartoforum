from orm_classes import sess
from flask import session, request, jsonify
from orm_classes import Users
from app import cfapp


@cfapp.route('/_update_basemap_pref', methods=['GET'])
def update_basemap_pref():
    basemap = request.args.get('basemap', 0, type=int)
    v = sess.query(Users).filter_by(userid=session['userid']).first()
    v.basemap = basemap
    sess.commit()
    return jsonify('basemap pref updated')


@cfapp.route('/_update_color_pref', methods=['GET'])
def update_color_pref():
    colormap = {'green': 0, 'red': 1, 'purple': 2, 'blue': 3, 'orange': 4}
    color = request.args.get('color', type=str)
    v = sess.query(Users).filter_by(userid=session['userid']).first()
    v.color = colormap[color]
    sess.commit()
    return jsonify('color pref updated')
