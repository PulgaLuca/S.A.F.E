# app.py
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import SafeConfig, SafeMiddleConfig
from models import db
from blueprints.weather import weather_bp
from blueprints.events import events_bp
import pandas as pd

def create_app():
    app = Flask(__name__)
    
    # Configura le connessioni al database
    app.config.from_object(SafeConfig)
    app.config.from_object(SafeMiddleConfig)
    
    db.init_app(app)
    migrate = Migrate(app, db)

    # Registra i blueprint
    app.register_blueprint(weather_bp)
    app.register_blueprint(events_bp)

    @app.route('/')
    def index():
        # Leggi i CSV
        weather_data = pd.read_csv(r'C:\Users\Luca\Desktop\weather_data.csv')
        event_data = pd.read_csv(r'C:\Users\Luca\Desktop\event_data_with_location.csv')
        
        # Converti i DataFrame in dizionari
        weather_data_dict = weather_data.to_dict(orient='records')
        event_data_dict = event_data.to_dict(orient='records')

        return render_template('index.html', weather_data=weather_data_dict, event_data=event_data_dict)
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=False)
