# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_login import current_user
from apps import db
from sqlalchemy.orm import raiseload

class Channels(db.Model):
        __tablename__ = 'Channels'
    
        id            = db.Column(db.Integer, primary_key=True)
        channel_name  = db.Column(db.String(64), unique=False)
        channel_id    = db.Column(db.String(64), unique=True)
        channel_image = db.Column(db.String(64), nullable=True)
        channel_monetize = db.Column(db.Boolean, nullable=False, default=True)
        channel_credentials   = db.Column(db.String(1000), nullable=True)
        user_id = db.Column(db.Integer, db.ForeignKey("Users.id", ondelete="cascade"), nullable=False)
    
        def __init__(self, **kwargs):
            for property, value in kwargs.items():
                setattr(self, property, value)
    
        def __repr__(self):
            return str(self.channel_name)


def load_channels():
    if current_user.is_authenticated:
        return Channels.query.filter_by(user_id=current_user.id).all()
    return []
