# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import google_auth_oauthlib
from apps import db
from apps.config import Config
from apps.youtube import blueprint
from apps.youtube.models import Channels, load_channels

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery

from flask import redirect, render_template, request, url_for, session
from flask_login import login_required, current_user


@blueprint.route('/canais')
@login_required
def canais():
    canais = load_channels()
    return render_template('youtube/canais.html', canais=canais, segment="canais")


@blueprint.route('/add_canal', methods=['GET', 'POST'])
@login_required
def add_canal():
    if 'credentials' not in session:
        return redirect('autorize_canal')

    credentials = google.oauth2.credentials.Credentials(
        **session['credentials'])

    youtube = googleapiclient.discovery.build(
        Config.YOUTUBE_API_SERVICE_NAME, Config.YOUTUBE_API_VERSION, credentials=credentials)

    channels = youtube.channels().list(
        part="id,snippet,statistics",
        mine=True
    ).execute()

    for item in channels['items']:
        # Verifica se o canal já existe
        channel = Channels.query.filter_by(channel_id=item['id']).first()
        if channel:
            channel.channel_credentials = session['state']
            db.session.add(channel)
            db.session.commit()
        else:
            channel = Channels(
                channel_id=item['id'],
                channel_name=item['snippet']['title'],
                channel_image=item['snippet']['thumbnails']['default']['url'],
                channel_credentials=str(session['credentials']),
                user_id=current_user.id
            )
            db.session.add(channel)
            db.session.commit()

    list_channels = load_channels()
    return render_template('youtube/canais.html', canais=list_channels, segment="canais")


@blueprint.route('/autorize_canal', methods=['GET', 'POST'])
@login_required
def autorize_canal():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        Config.YOUTUBE_CLIENT_SECRET, scopes=['https://www.googleapis.com/auth/youtube'])

    flow.redirect_uri = url_for(
        'youtube_blueprint.oauth2callback', _external=True)

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')

    session['state'] = state

    return redirect(authorization_url)


@blueprint.route('/oauth2callback')
def oauth2callback():
    state = session['state']
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        Config.YOUTUBE_CLIENT_SECRET, scopes=['https://www.googleapis.com/auth/youtube'], state=state)
    flow.redirect_uri = url_for(
        'youtube_blueprint.oauth2callback', _external=True)
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)
    return redirect(url_for('youtube_blueprint.add_canal'))


def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}
