import dash
import dash_bootstrap_components as dbc
from flask import Flask
from flask_login import LoginManager
from database.db import db
from database.models import Usuario
import os

# 1. Configurar Servidor Flask
server = Flask(__name__)

# Configuración Secreta (Necesaria para sesiones)
server.config.update(
    SECRET_KEY=os.urandom(24),
    SQLALCHEMY_DATABASE_URI='sqlite:///fondo.db',
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)

# 2. Inicializar Base de Datos con la App
db.init_app(server)

# 3. Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = '/login' # Si no está logueado, redirigir aquí

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# 4. Inicializar Dash con Bootstrap
# USAMOS EL TEMA "FLATLY" (Moderno y limpio para dashboards)
app = dash.Dash(
    __name__,
    server=server,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.FLATLY, dbc.icons.BOOTSTRAP] 
)

app.title = "FONAMIG"