import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
from flask_login import current_user
from database.models import Usuario
from database.db import db
from components.navbar import crear_navbar

def layout():
    # Validación de seguridad: Si no está logueado, mostrar mensaje
    if not current_user.is_authenticated:
        return html.Div([crear_navbar(), dbc.Alert("Debes iniciar sesión para ver tus datos.", color="danger")])

    # Recargamos el usuario de la DB para asegurar datos frescos
    usuario_actual = Usuario.query.get(current_user.id)

    return html.Div([
        crear_navbar(),
        dbc.Container([
            html.H2("⚙️ Mi Perfil y Configuración", className="mb-4 text-primary"),
            
            dbc.Row([
                # --- DATOS PERSONALES ---
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("👤 Información Personal")),
                        dbc.CardBody([
                            dbc.Label("Nombre Completo"),
                            dbc.Input(id="perfil-nombre", value=usuario_actual.nombre_completo, type="text", className="mb-3"),
                            
                            dbc.Label("Correo Electrónico"),
                            dbc.Input(id="perfil-email", value=usuario_actual.email, type="email", className="mb-3"),
                            
                            dbc.Label("Teléfono"),
                            dbc.Input(id="perfil-telefono", value=usuario_actual.telefono, type="text", className="mb-3"),
                            
                            dbc.Label("Usuario (No editable)"),
                            dbc.Input(value=usuario_actual.username, disabled=True, className="bg-light mb-3"),
                            
                            dbc.Button("💾 Guardar Datos", id="btn-save-datos", color="primary", className="w-100"),
                            html.Div(id="msg-save-datos", className="mt-2")
                        ])
                    ], className="shadow h-100")
                ], width=12, md=6),

                # --- CAMBIO DE CONTRASEÑA ---
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("🔒 Seguridad")),
                        dbc.CardBody([
                            dbc.Label("Contraseña Actual"),
                            dbc.Input(id="pass-actual", type="password", className="mb-3"),
                            
                            html.Hr(),
                            
                            dbc.Label("Nueva Contraseña"),
                            dbc.Input(id="pass-nueva", type="password", className="mb-3"),
                            
                            dbc.Label("Confirmar Nueva"),
                            dbc.Input(id="pass-confirm", type="password", className="mb-3"),
                            
                            dbc.Button("🔐 Actualizar Contraseña", id="btn-save-pass", color="warning", className="w-100"),
                            html.Div(id="msg-save-pass", className="mt-2")
                        ])
                    ], className="shadow h-100")
                ], width=12, md=6)
            ])
        ])
    ])

# --- CALLBACK: GUARDAR DATOS PERSONALES ---
@callback(
    Output("msg-save-datos", "children"),
    Input("btn-save-datos", "n_clicks"),
    [State("perfil-nombre", "value"),
     State("perfil-email", "value"),
     State("perfil-telefono", "value")],
    prevent_initial_call=True
)
def actualizar_datos(n_clicks, nombre, email, telefono):
    try:
        user = Usuario.query.get(current_user.id)
        user.nombre_completo = nombre
        user.email = email
        user.telefono = telefono
        db.session.commit()
        return dbc.Alert("✅ Datos actualizados.", color="success")
    except Exception as e:
        db.session.rollback()
        return dbc.Alert(f"Error: {str(e)}", color="danger")

# --- CALLBACK: CAMBIAR CONTRASEÑA ---
@callback(
    Output("msg-save-pass", "children"),
    Input("btn-save-pass", "n_clicks"),
    [State("pass-actual", "value"),
     State("pass-nueva", "value"),
     State("pass-confirm", "value")],
    prevent_initial_call=True
)
def cambiar_password(n_clicks, actual, nueva, confirm):
    if not actual or not nueva:
        return dbc.Alert("Llena todos los campos.", color="warning")
    
    if nueva != confirm:
        return dbc.Alert("Las contraseñas nuevas no coinciden.", color="danger")
    
    user = Usuario.query.get(current_user.id)
    
    # Verificar contraseña vieja
    if not user.check_password(actual):
        return dbc.Alert("Tu contraseña actual es incorrecta.", color="danger")
    
    try:
        user.set_password(nueva)
        db.session.commit()
        return dbc.Alert("✅ Contraseña cambiada exitosamente.", color="success")
    except Exception as e:
        return dbc.Alert(f"Error técnico: {str(e)}", color="danger")