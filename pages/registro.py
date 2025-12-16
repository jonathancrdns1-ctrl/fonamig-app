import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
from database.models import Usuario
from database.db import db

layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3("Crear Cuenta Nueva", className="text-center mb-4 text-success"),
                    
                    dbc.Label("Nombre Completo"),
                    dbc.Input(id="reg-nombre", type="text", placeholder="Ej: Juan Pérez", className="mb-2"),
                    
                    dbc.Label("Usuario (Para entrar)"),
                    dbc.Input(id="reg-user", type="text", placeholder="Ej: juanperez", className="mb-2"),
                    
                    dbc.Label("Email"),
                    dbc.Input(id="reg-email", type="email", placeholder="juan@ejemplo.com", className="mb-2"),

                    # --- NUEVO CAMPO: TELÉFONO ---
                    dbc.Label("Teléfono / Celular"),
                    dbc.Input(id="reg-telefono", type="text", placeholder="Ej: 3001234567", className="mb-2"),
                    # -----------------------------
                    
                    dbc.Label("Contraseña"),
                    dbc.Input(id="reg-pass", type="password", className="mb-3"),
                    
                    dbc.Button("Registrarse", id="btn-registrar", color="success", className="w-100"),
                    
                    html.Div(id="alerta-registro", className="mt-3"),
                    
                    html.Hr(),
                    dbc.Button("¿Ya tienes cuenta? Inicia Sesión", href="/login", color="link", className="w-100")
                ])
            ], className="shadow-lg border-0")
        ], width=12, md=6, lg=4)
    ], justify="center", align="center", className="vh-100")
], fluid=True)

@callback(
    Output("alerta-registro", "children"),
    Input("btn-registrar", "n_clicks"),
    [State("reg-nombre", "value"),
     State("reg-user", "value"),
     State("reg-email", "value"),
     State("reg-telefono", "value"), # <--- Agregamos el Estado aquí
     State("reg-pass", "value")]
)
def registrar_usuario(n_clicks, nombre, user, email, telefono, password):
    if not n_clicks:
        return dash.no_update
    
    # Validamos que todo esté lleno (incluyendo teléfono)
    if not all([nombre, user, email, telefono, password]):
        return dbc.Alert("Todos los campos (incluyendo teléfono) son obligatorios.", color="warning")
    
    # Verificar si ya existe el usuario
    if Usuario.query.filter_by(username=user).first():
        return dbc.Alert("El usuario ya existe. Prueba otro.", color="danger")
    
    try:
        nuevo_user = Usuario(
            username=user, 
            nombre_completo=nombre, 
            email=email,
            telefono=telefono, # <--- Guardamos el teléfono
            activo=False 
        )
        nuevo_user.set_password(password)
        
        db.session.add(nuevo_user)
        db.session.commit()
        return dbc.Alert("Cuenta creada. Espera a que el Admin te active para entrar.", color="success")
    except Exception as e:
        db.session.rollback()
        return dbc.Alert(f"Error técnico: {str(e)}", color="danger")