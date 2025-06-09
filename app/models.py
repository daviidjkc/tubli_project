from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json

favorites = db.Table(
    'favorites',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('book_id', db.Integer, db.ForeignKey('books.id'))
)

class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(150), nullable=False)
    year = db.Column(db.Integer)
    language = db.Column(db.String(50))
    languages = db.Column(db.String(200))  # NUEVO: lista de idiomas separados por coma
    author_birth_year = db.Column(db.Integer)  # NUEVO
    author_death_year = db.Column(db.Integer)  # NUEVO
    subject = db.Column(db.String(100))
    file_url = db.Column(db.String(255))
    cover_url = db.Column(db.String(255))
    summary = db.Column(db.Text)
    download_count = db.Column(db.Integer)
    formats = db.Column(db.Text)  # NUEVO: guarda el dict de formatos como JSON
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # NUEVO: referencia al usuario

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='user')
    books = db.relationship('Book', backref='user', lazy=True)
    favorites = db.relationship('Book', secondary=favorites, backref='favorited_by')
    profile_pic = db.Column(db.String(255), default='img/user_icon.png')  # NUEVO

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))





