# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os
from flask_login import current_user, login_user
from flask_dance.consumer import oauth_authorized
from flask_dance.contrib.github import github, make_github_blueprint
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from sqlalchemy.orm.exc import NoResultFound
from apps.config import Config
from .models import Users, db, OAuth

github_blueprint = make_github_blueprint(
    client_id=Config.GITHUB_ID,
    client_secret=Config.GITHUB_SECRET,
    scope='user',
    storage=SQLAlchemyStorage(
        OAuth,
        db.session,
        user=current_user,
        user_required=False,
    ),
)


@oauth_authorized.connect_via(github_blueprint)
def github_logged_in(blueprint, token):
    info = github.get("/user")

    if info.ok:

        account_info = info.json()
        username = account_info["login"]

        query = Users.query.filter_by(oauth_github=username)
        try:

            user = query.one()
            login_user(user)

        except NoResultFound:

            # Save to db
            user = Users()
            user.username = '(gh)' + username
            user.oauth_github = username

            # Save current user
            db.session.add(user)
            db.session.commit()

            login_user(user)


google_blueprint = make_google_blueprint(
    client_id=Config.GOOGLE_ID,
    client_secret=Config.GOOGLE_SECRET,
    scope=['profile', 'email'],
    redirect_to='home_blueprint.index',
    storage=SQLAlchemyStorage(
        OAuth,
        db.session,
        user=current_user,
        user_required=False,
    ),
)


@oauth_authorized.connect_via(google_blueprint)
def google_logged_in(blueprint, token):
    info = google.get("/oauth2/v1/userinfo")

    if info.ok:
        account_info = info.json()
        id = account_info["id"]
        username = account_info["name"]
        picture = account_info["picture"] if "picture" in account_info else None
        link = account_info["link"] if "link" in account_info else None
        hd = account_info["hd"] if "hd" in account_info else None
        query = Users.query.filter_by(oauth_google=id)
        try:
            user = query.one()
            if user.picture != picture or user.username != username or user.link != link or user.hd != hd or user.email != account_info["email"] :
                user.picture = picture
                user.username = username
                user.link = link
                user.hd = hd
                user.email = account_info["email"]
                db.session.add(user)
                db.session.commit()
            login_user(user)

        except NoResultFound:
            # Save to db
            user = Users()
            user.oauth_google = id
            user.email = account_info["email"]
            user.username = username
            user.picture = picture
            user.link = link
            user.hd = hd

            # Save current user
            db.session.add(user)
            db.session.commit()

            login_user(user)
