class Config:
    SECRET_KEY = 'B!1w8NAt1T^%kvhUI*S^'


class DevelopmentConfig(Config):
    DEBUG = True
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'newsletter'
    MYSQL_PASSWORD = 'Soun001920'
    MYSQL_DB = 'newsletter_ia'

config = {
    'development': DevelopmentConfig
}