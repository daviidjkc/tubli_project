from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app import db
import requests
from app.utils import contiene_palabras_prohibidas

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Se debe validar formulario y autenticación del usuario
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.index'))
        else:
            flash('Credenciales incorrectas', 'danger')
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        recaptcha_response = request.form.get('g-recaptcha-response')
        secret = 'TU_SECRET_KEY_AQUI'
        payload = {
            'secret': secret,
            'response': recaptcha_response
        }
        r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=payload)
        result = r.json()
        if not result.get('success'):
            flash('Por favor, verifica que no eres un robot.', 'danger')
            return redirect(url_for('auth.register'))
        # Verificar si el usuario ya existe
        if User.query.filter((User.username==username)|(User.email==email)).first():
            flash('El usuario ya existe.', 'warning')
        else:
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registro exitoso. Puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth_bp.route('/logout', methods=['POST'])
def logout():
    logout_user()
    return redirect(url_for('main.index'))
