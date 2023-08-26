# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.youtube import blueprint
from flask import render_template
from flask_login import login_required

from apps.youtube.models import load_channels


@blueprint.route('/canais')
@login_required
def canais():
    canais = load_channels()
    return render_template('youtube/canais.html', canais=canais, segment="canais")
