# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_login import current_user
from apps import db
from sqlalchemy.orm import raiseload, aliased


class ChannelChannel(db.Model):
    __tablename__ = 'ChannelChannel'

    id = db.Column(db.Integer, primary_key=True)
    channel_in = db.Column(db.Integer, db.ForeignKey(
        "Channels.channel_id", ondelete="cascade"), nullable=False)
    channel_out = db.Column(db.Integer, db.ForeignKey(
        "Channels.channel_id", ondelete="cascade"), nullable=False)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            setattr(self, property, value)

    def __repr__(self):
        return str(self.channel_name)


class Channels(db.Model):
    __tablename__ = 'Channels'

    id = db.Column(db.Integer, primary_key=True)
    channel_id = db.Column(db.String(64), unique=True)
    channel_name = db.Column(db.String(64), unique=False)
    channel_image = db.Column(db.String(64), nullable=True)
    channel_monetize = db.Column(db.Boolean, nullable=False, default=True)
    channel_credentials = db.Column(db.String(1000), nullable=True)
    channel_subscribers = db.Column(db.Integer, nullable=True)
    channel_subscriptions = db.Column(db.Integer, nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey(
        "Users.id", ondelete="cascade"), nullable=False)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            setattr(self, property, value)

    def __repr__(self):
        return str(self.channel_name)


def load_channels(subscribe: bool = False):
    if current_user.is_authenticated:
        if subscribe:  
            CC_out = aliased(ChannelChannel)
            CC_in = aliased(ChannelChannel)
            data = db.session.query(
                Channels,
                db.func.count(CC_out.channel_out).label(
                    'channel_internal_subscribers_count'),
                db.func.count(CC_in.channel_in).label(
                    'channel_internal_subscribed_count')
            ).filter(
                Channels.user_id == current_user.id
            ).outerjoin(
                CC_out, Channels.channel_id == CC_out.channel_out
            ).outerjoin(
                CC_in, Channels.channel_id == CC_in.channel_in
            ).group_by(Channels.id).all()

            channels = []
            for row in data:
                channel = row[0]
                channel.channel_internal_subscribers_count = row[1]
                channel.channel_internal_subscribed_count = row[2]
                channels.append(channel)

            return channels
        else:
            return Channels.query.options(raiseload('*')).filter_by(user_id=current_user.id).all()
    return []


def get_channel(id: int):
    return Channels.query.filter_by(id=id, user_id=current_user.id).first()


def count_channels_in(channel_ids: list):
    return Channels.query.filter(Channels.channel_id.in_(channel_ids)).count()


def get_channels_in(channel_ids: list):
    return Channels.query.with_entities(Channels.channel_id).filter(Channels.channel_id.in_(channel_ids)).all()


def update_relations(channel_ids: list, channel_id: str):
    relation_ids = get_channels_in(channel_ids)
    ChannelChannel.query.filter_by(channel_in=channel_id).delete()
    for relation_id in relation_ids:
        if relation_id[0] == channel_id:
            continue
        cc = ChannelChannel(channel_in=channel_id,
                            channel_out=relation_id[0])
        db.session.add(cc)

    db.session.commit()


def get_internal_subscriber(channel_id: str):
    return ChannelChannel.query.filter_by(channel_out=channel_id).count()


def get_not_subscribed(channel_id: str):
    # Retorna os canais que não estão inscritos no canal passado
    return Channels.query.with_entities(Channels.channel_id).filter(
        Channels.channel_id.notin_(
            ChannelChannel.query.with_entities(
                ChannelChannel.channel_out)
            .filter_by(channel_in=channel_id
                       ))).all()

def delete_channel(channel_id: str):
    ChannelChannel.query.filter_by(channel_in=channel_id).delete()
    ChannelChannel.query.filter_by(channel_out=channel_id).delete()
    Channels.query.filter_by(channel_id=channel_id).delete()
    db.session.commit()