import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'park-energy-secret-key'
    DATABASE = os.path.join(os.path.dirname(__file__), 'park_energy.db')

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}