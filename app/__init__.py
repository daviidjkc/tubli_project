import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv
from flask_migrate import Migrate  # Importa Migrate

# Cargar variables de entorno
load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()  # Crea la instancia de Migrate

def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('app.config.Config')
    
    # Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)  # Inicializa Flask-Migrate
    
    login_manager.login_view = 'auth.login'
    
    # Registrar Blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Manejo de errores personalizados
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500

    return app
