# blueprints/events.py
from flask import Blueprint, render_template
from models import EventData

events_bp = Blueprint('events', __name__, url_prefix='/events')

@events_bp.route('/')
def events_home():
    data = EventData.query.all()
    return render_template('events.html', events_data=data)
