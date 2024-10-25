# app.py
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  # Importa Flask-Migrate
from config import SafeConfig, SafeMiddleConfig
from models import db
from blueprints.weather import weather_bp
from blueprints.events import events_bp

def create_app():
    app = Flask(__name__)
    
    # Configura le connessioni al database
    app.config.from_object(SafeConfig)
    app.config.from_object(SafeMiddleConfig)
    
    db.init_app(app)
    migrate = Migrate(app, db)  # Inizializza Flask-Migrate

    # Registra i blueprint
    app.register_blueprint(weather_bp)
    app.register_blueprint(events_bp)
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=False)
