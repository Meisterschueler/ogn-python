from app.main import bp
from app.model import Airport, Country, Sender, Receiver

from flask import url_for
import datetime
import math


@bp.app_template_filter()
def to_html_flag(obj):
    if obj is None:
        return ""

    if isinstance(obj, str):
        return f"""<img src="{url_for('static', filename='img/Transparent.gif')}" class="flag flag-{obj.lower()}" alt="{obj}"/>"""

    elif isinstance(obj, Airport):
        return f"""<img src="{url_for('static', filename='img/Transparent.gif')}" class="flag flag-{obj.country_code.lower()}" alt="{obj.country_code}"/>"""

    elif isinstance(obj, Country):
        return f"""<img src="{url_for('static', filename='img/Transparent.gif')}" class="flag flag-{obj.iso2.lower()}" alt="{obj.iso2}"/>"""


@bp.app_template_filter()
def to_html_link(obj):
    if isinstance(obj, Airport):
        airport = obj
        return f"""<a href="{url_for('main.airport_detail', airport_id=airport.id)}">{airport.name}</a>"""

    elif isinstance(obj, Sender):
        sender = obj
        if len(sender.infos) > 0 and len(sender.infos[0].registration) > 0:
            return f"""<a href="{url_for('main.sender_detail', sender_id=sender.id)}">{sender.infos[0].registration}</a>"""
        elif sender.address:
            return f"""<a href="{url_for('main.sender_detail', sender_id=sender.id)}">[{sender.address}]</a>"""
        else:
            return f"""<a href="{url_for('main.sender_detail', sender_id=sender.id)}">[{sender.name}]</a>"""

    elif isinstance(obj, Receiver):
        receiver = obj
        return f"""<a href="{url_for('main.receiver_detail', receiver_id=receiver.id)}">{receiver.name}</a>"""

    elif obj is None:
        return "-"

    else:
        raise NotImplementedError("cant apply filter 'to_html_link' to object {type(obj)}")


@bp.app_template_filter()
def to_ordinal(rad):
    deg = math.degrees(rad)
    if deg >= 337.5 or deg < 22.5:
        return "N"
    elif deg >= 22.5 and deg < 67.5:
        return "NW"
    elif deg >= 67.5 and deg < 112.5:
        return "W"
    elif deg >= 112.5 and deg < 157.5:
        return "SW"
    elif deg >= 157.5 and deg < 202.5:
        return "S"
    elif deg >= 202.5 and deg < 247.5:
        return "SE"
    elif deg >= 247.5 and deg < 292.5:
        return "E"
    elif deg >= 292.5 and deg < 337.5:
        return "NE"
