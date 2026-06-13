import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'park-energy-secret-key'
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or 'Lrs08642'
    MYSQL_DB = os.environ.get('MYSQL_DB') or 'campus_ops'
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT') or 3306)

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