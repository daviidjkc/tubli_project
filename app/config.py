import os
from datetime import timedelta
from flask_login import login_user

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'clave_secreta_por_defecto')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///biblioteca.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'app', 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'epub'}
    REMEMBER_COOKIE_DURATION = timedelta(days=7)  # Mantener sesión 7 días
    REMEMBER_ME = True

# ... en tu vista de login:
# login_user(user, remember=True)
