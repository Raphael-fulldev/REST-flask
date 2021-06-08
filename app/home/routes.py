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

SECRET_KEY = "*G-KaPdSgVkYp2t6"
ACCESS_TOKEN_LIFETIME = 1800

@blueprint.route('/index')
@login_required
def index():
    encoded_jwt2 = jwt.encode({"user": current_user.id, "exp": time.time() + ACCESS_TOKEN_LIFETIME, "permission_field": 'layer2'}, SECRET_KEY, algorithm="HS256")
    print("token for second api--->", encoded_jwt2)
    encoded_jwt1 = jwt.encode({"user": current_user.id, "exp": time.time() + ACCESS_TOKEN_LIFETIME, "permission_field": 'layer1'}, SECRET_KEY, algorithm="HS256")
    print("token for first api--->", encoded_jwt1)
    encoded_refresh_jwt = replace_refresh_token(current_user.id)
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

def replace_refresh_token(user_id):
    encoded_refresh_jwt = jwt.encode({"user": user_id, "exp": time.time() + 3600*24*200, "permission_field": 'refresh'}, SECRET_KEY, algorithm="HS256")
    print("refresh token--->", encoded_refresh_jwt)
    me = User.query.filter_by(id=user_id).first()
    me.refresh_token = encoded_refresh_jwt
    db.session.commit()
    return encoded_refresh_jwt

# revoke current refresh token.
@blueprint.route('/revoke')
@login_required
def revoke_current_refresh_token():
    me = User.query.filter_by(id=current_user.id).first()
    me.refresh_token = ""
    db.session.commit()
    return "refresh token removed"

@blueprint.route('/api/layer1')
def api():
    try:
        encoded_jwt = request.headers.get('Authorization')
        decoded_jwt = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"])
        if decoded_jwt["permission_field"] != "layer1":
            return 'invalid token'
        if decoded_jwt['exp'] < time.time():
            return 'token expired'
        check_limit(decoded_jwt['user'])
    except:
        return 'Invalid'
    return jsonify(decoded_jwt)

@blueprint.route('/api/layer2')
def api2():
    try:
        encoded_jwt = request.headers.get('Authorization')
        decoded_jwt = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"])
        if decoded_jwt["permission_field"] != "layer2":
            return 'invalid token'
        if decoded_jwt['exp'] < time.time():
            return 'token expired'
        check_limit(decoded_jwt['user'])
    except:
        return 'Invalid'
    return jsonify(decoded_jwt)

@blueprint.route('/api/refresh_token', methods=['POST', 'GET'])
def refresh_token():
    if request.method == "POST":
        try:
            access_exp = request.json['exp']
        except:
            access_exp = 10
    else:
        access_exp = 10

    try:
        encoded_jwt = request.headers.get('Authorization')
        decoded_jwt = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"])
        if decoded_jwt["permission_field"] != "refresh":
            return 'not refresh token'
        if decoded_jwt['exp'] < time.time():
            return 'refresh token expired'
        user_id = decoded_jwt["user"]

        # check if the refresh token is stored in DB, if exists, the current refresh token is valid one.
        me = User.query.filter_by(id=user_id).first()
        if encoded_jwt != me.refresh_token:
            return 'this refresh token is not valid anymore'

        encoded_jwt2 = jwt.encode({"user": user_id, "exp": time.time() + 3600*access_exp, "permission_field": 'layer2'}, SECRET_KEY, algorithm="HS256")
        encoded_jwt1 = jwt.encode({"user": user_id, "exp": time.time() + 3600*access_exp, "permission_field": 'layer1'}, SECRET_KEY, algorithm="HS256")
    except:
        return 'Invalid'

    return {
        "first API token": encoded_jwt1,
        "second API token": encoded_jwt2,
    }

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
