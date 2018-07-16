import os

APP_HOST = '127.0.0.1'
APP_PORT = '8080'

DB_HOST = os.environ.get('DB_HOST') or '0.0.0.0'
DB_PORT = os.environ.get('DB_PORT') or '5432'
DB_NAME = os.environ.get('DB_NAME') or 'postgres'
DB_USER = os.environ.get('DB_USER') or 'postgres'
DB_PASS = os.environ.get('DB_PASSWORD') or 'password'

JWT_SECRET = 'some_secret'

PASSWORD_SALT = 'some_salt'