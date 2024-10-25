# blueprints/weather.py
from flask import Blueprint, render_template
from models import WeatherData

weather_bp = Blueprint('weather', __name__, url_prefix='/weather')

@weather_bp.route('/')
def weather_home():
    data = WeatherData.query.all()
    return render_template('weather.html', weather_data=data)
