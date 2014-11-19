__author__ = 'Tonakai'

# from databases.database import DATABASES
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'tracker',                      # Or path to database file if using sqlite3.
        'USER': 'root',                      # Not used with sqlite3.
        'PASSWORD': 'godlike999',                  # Not used with sqlite3.
        'HOST': 'localhost',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '3306',                      # Set to empty string for default. Not used with sqlite3.
    }
}

SESSION_COOKIE_DOMAIN = 'heliard.topnotchstudios.ru'
SOCKET_SERVER_ADDRESS = 'localhost'
project_root = '/home/heliard/heliard/'

# GIT MODULE SETTINGS
USE_GIT_MODULE = True
GITOLITE_ACCESS_URL = 'heliard@heliard.topnotchstudios.ru'
GITOLITE_ADMIN_REPOSITORY = '/home/heliard/gitolite-admin'