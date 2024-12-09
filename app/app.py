import os
import sys
import pandas as pd
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import SafeConfig, SafeMiddleConfig
from models import db
from blueprints.weather import weather_bp
from blueprints.events import events_bp

def get_data_file(file_name):
    """Ritorna il percorso del file CSV, gestendo sia l'esecuzione da script che da eseguibile."""
    if hasattr(sys, '_MEIPASS'):
        # Se il programma è eseguito come eseguibile, cerca il file nell'area temporanea
        base_path = sys._MEIPASS
    else:
        # Se il programma è eseguito come script, usa il percorso corrente
        base_path = os.getcwd()

    # Restituisce il percorso completo del file CSV
    return os.path.join(base_path, 'data', 'csv', file_name)

def create_app():
    app = Flask(__name__, template_folder='app/templates', static_folder='app/static')

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
        # Leggi i CSV utilizzando il nuovo metodo per ottenere il percorso corretto
        weather_data = pd.read_csv(get_data_file('weather_data.csv'))
        event_data = pd.read_csv(get_data_file('event_data_with_location.csv'))
        
        # Converti i DataFrame in dizionari
        weather_data_dict = weather_data.to_dict(orient='records')
        event_data_dict = event_data.to_dict(orient='records')

        return render_template('index.html', weather_data=weather_data_dict, event_data=event_data_dict)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=False)
