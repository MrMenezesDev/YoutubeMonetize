# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps import db
from apps.config import Config
from apps.youtube import blueprint
from apps.youtube.models import ChannelChannel, Channels, delete_channel, update_relations, get_channel, load_channels
from apps.youtube.service import get_statistics, get_subscriptions, subscribe_all
from apps.youtube.utils import credentials_to_dict

import google_auth_oauthlib
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery

from flask import redirect, render_template, request, url_for, session
from flask_login import login_required, current_user


@blueprint.route('/canal/<int:id>/atualizar')
@login_required
def atualizar_inscritos(id: int):

    canal = get_channel(id)
    
    atualizar_canal(canal)

    return redirect('/canais')


@blueprint.route('/canais/atualizar')
@login_required
def atualizar_todos_inscritos():
    canais = load_channels(False)

    for canal in canais:
        atualizar_canal(canal)

    return redirect('/canais')

@blueprint.route('/canal/<int:id>/delete')
@login_required
def delete(id: int):
    canal = get_channel(id)

    delete_channel(canal.channel_id)

    return redirect('/canais')


@blueprint.route('/canal/<int:id>/inscrever')
@login_required
def inscrever(id: int):
    canal = get_channel(id)

    subscribe_all(canal)

    return redirect('/canal/{}/atualizar'.format(id))

@blueprint.route('/canais/inscrever')
@login_required
def inscrever_todos_canais():
    canais = load_channels(False)

    for canal in canais:
        subscribe_all(canal)

    return redirect('/canais/atualizar')

@blueprint.route('/canais')
@login_required
def canais():
    canais = load_channels(True)
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
    try:
        channels = youtube.channels().list(
            part="id,snippet,statistics",
            mine=True
        ).execute()
    except Exception as e:
        print(e)
        try:
            import time
            time.sleep(2)
            channels = youtube.channels().list(
                part="id,snippet,statistics",
                mine=True
            ).execute()
        except Exception as e:
            print(e)
            return redirect('add_canal')
    for item in channels['items']:
        # Verifica se o canal já existe
        channel = Channels.query.filter_by(channel_id=item['id']).first()
        if channel:
            channel.channel_credentials=str(session['credentials'])
            db.session.add(channel)
            db.session.commit()
        else:
            channel = Channels(
                channel_id=item['id'],
                channel_name=item['snippet']['title'],
                channel_image=item['snippet']['thumbnails']['default']['url'] if 'thumbnails' in item['snippet'] else None,
                channel_credentials=str(session['credentials']),
                user_id=current_user.id
            )
            db.session.add(channel)
            db.session.commit()

    return redirect('/canal/{}/atualizar'.format(channel.id))


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


def atualizar_canal(canal: Channels):
    statistics = get_statistics(canal)
    subscriptions = get_subscriptions(canal)
    canal.channel_subscribers = statistics["subscriberCount"]
    canal.channel_subscriptions = len(subscriptions)
    db.session.add(canal)
    db.session.commit()
    update_relations(subscriptions, canal.channel_id)
