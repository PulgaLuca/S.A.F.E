# config.py
class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class SafeConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///safe.db'

class SafeMiddleConfig(Config):
    SQLALCHEMY_BINDS = {
        'safe_middle': 'sqlite:///safe_middle.db'
    }
