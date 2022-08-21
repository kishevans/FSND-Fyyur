import os
SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database


#Remove <> and add your db password and database name
SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:5807@localhost:5432/fyyurdb'

SQLALCHEMY_TRACK_MODIFICATIONS = False