# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from app.home import blueprint
from flask import render_template, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from app import login_manager
from jinja2 import TemplateNotFound
import jwt, time
from app.base.models import User
from datetime import date
from app import db

@blueprint.route('/index')
@login_required
def index():
    encoded_jwt2 = jwt.encode({"user": current_user.id, "exp": time.time() + 36000, "permission_field": 'layer2'}, "secret1", algorithm="HS256")
    print("token for second api--->", encoded_jwt2)
    encoded_jwt1 = jwt.encode({"user": current_user.id, "exp": time.time() + 36000, "permission_field": 'layer1'}, "secret1", algorithm="HS256")
    print("token for first api--->", encoded_jwt1)
    return render_template('index.html', segment='index')

def check_limit(id):
    me = User.query.filter_by(id=id).first()
    if me.today:
        if me.today_limit:
            if me.today_limit >= 1000:
                raise Error('limit over')
        else:
            me.today_limit = 0
    else:
        me.today = date.today().day
    # api working
    me.today = date.today().day
    me.today_limit += 1
    print("current count-->", me.today_limit)
    db.session.commit()

@blueprint.route('/api/layer1')
def api():
    encoded_jwt = request.headers.get('Authorization')
    decoded_jwt = jwt.decode((encoded_jwt), "secret1", algorithms=["HS256"])
    if decoded_jwt["permission_field"] != "layer1":
        return 'invalid token'
    if decoded_jwt['exp'] < time.time():
        return 'token expired'
    check_limit(decoded_jwt['user'])
    return jsonify(decoded_jwt)

@blueprint.route('/api/layer2')
def api2():
    encoded_jwt = request.headers.get('Authorization')
    decoded_jwt = jwt.decode((encoded_jwt), "secret1", algorithms=["HS256"])
    if decoded_jwt["permission_field"] != "layer2":
        return 'invalid token'
    if decoded_jwt['exp'] < time.time():
        return 'token expired'
    check_limit(decoded_jwt['user'])
    return jsonify(decoded_jwt)

@blueprint.route('/<template>')
@login_required
def route_template(template):

    try:

        if not template.endswith( '.html' ):
            template += '.html'

        # Detect the current page
        segment = get_segment( request )

        # Serve the file (if exists) from app/templates/FILE.html
        return render_template( template, segment=segment )

    except TemplateNotFound:
        return render_template('page-404.html'), 404
    
    except:
        return render_template('page-500.html'), 500

# Helper - Extract current page name from request 
def get_segment( request ): 

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment    

    except:
        return None  
