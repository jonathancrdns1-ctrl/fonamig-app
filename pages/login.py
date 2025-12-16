import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
from flask_login import login_user
from database.models import Usuario

# Usamos un fondo suave para la página de login
layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.Div([
                    # Logo o Título Grande con estilo
                    html.H1("FONAMIG", className="text-center mb-0 text-gradient display-3"),
                    html.P("Fondo de Amigos y Familia", className="text-center text-muted mb-4 lead"),

                    dbc.Card([
                        dbc.CardBody([
                            html.H4("¡Hola de nuevo! 👋", className="text-center mb-4 fw-bold text-primary"),
                            
                            dbc.Label("Usuario", className="fw-bold text-muted"),
                            dbc.Input(id="login-user", type="text", placeholder="Ingresa tu usuario", className="mb-3 form-control-lg"),
                            
                            dbc.Label("Contraseña", className="fw-bold text-muted"),
                            dbc.Input(id="login-password", type="password", placeholder="••••••••", className="mb-4 form-control-lg"),
                            
                            dbc.Button("INGRESAR", id="login-button", color="primary", className="w-100 btn-lg mb-3 shadow-sm"),
                            
                            html.Div(className="text-center", children=[
                                html.Span("¿No tienes cuenta? "),
                                dcc.Link("Regístrate aquí", href="/registro", className="fw-bold text-primary text-decoration-none")
                            ]),

                            html.Div(id="login-alert", className="mt-3")
                        ], className="p-4") # Más espacio interno (Padding 4)
                    ], className="shadow-lg border-0") # Sombra grande, sin borde
                ], className="py-5")
            ], width=12, sm=10, md=8, lg=5) # Ajuste de ancho responsivo
        ], justify="center", align="center", className="vh-100") # Centrado vertical total
    ])
], style={"backgroundColor": "#f4f6f9"}) # Fondo gris claro para toda la pantalla

@callback(
    [Output("url", "pathname"), Output("login-alert", "children")],
    [Input("login-button", "n_clicks")],
    [State("login-user", "value"), State("login-password", "value")],
    prevent_initial_call=True
)
def login_success(n_clicks, username, password):
    if not username or not password:
        return dash.no_update, dbc.Alert("Faltan datos.", color="warning", dismissable=True)

    user = Usuario.query.filter_by(username=username).first()

    if user and user.check_password(password):
        if not user.activo:
            return dash.no_update, dbc.Alert("Tu cuenta aún no ha sido activada por el Admin.", color="warning")
            
        login_user(user)
        return "/home", ""
    else:
        return dash.no_update, dbc.Alert("Credenciales inválidas.", color="danger", dismissable=True)