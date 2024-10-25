# models.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class WeatherData(db.Model):
    __tablename__ = 'weather_data'
    id = db.Column(db.Integer, primary_key=True)
    luogo = db.Column(db.String(100), nullable=False)
    temperatura = db.Column(db.Float, nullable=False)
    umidita = db.Column(db.Float, nullable=False)

class EventData(db.Model):
    __bind_key__ = 'safe_middle'
    __tablename__ = 'event_data'
    id = db.Column(db.Integer, primary_key=True)
    luogo = db.Column(db.String(100), nullable=False)
    evento = db.Column(db.String(50), nullable=False)
    data_inizio = db.Column(db.Date, nullable=False)
    data_fine = db.Column(db.Date, nullable=False)
