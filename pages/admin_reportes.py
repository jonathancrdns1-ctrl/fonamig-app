import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from database.models import Usuario, Prestamo, Aporte, Cuota
from database.db import db
from components.navbar import crear_navbar

# --- LAYOUT ---
def layout():
    # =========================================================
    # 1. CÁLCULO DE DATOS GLOBALES (KPIs)
    # =========================================================
    
    # A. Total Ahorrado
    total_ahorrado = db.session.query(db.func.sum(Aporte.monto)).filter(Aporte.estado == 'Aprobado').scalar() or 0
    
    # B. Cartera Activa REAL
    total_prestado_bruto = db.session.query(db.func.sum(Prestamo.monto_solicitado)).filter(Prestamo.estado == 'Activo').scalar() or 0
    
    capital_recuperado = db.session.query(db.func.sum(Cuota.monto_capital)).join(Prestamo).filter(
        Prestamo.estado == 'Activo',
        Cuota.estado == 'Pagado'
    ).scalar() or 0

    cartera_activa_real = total_prestado_bruto - capital_recuperado

    # C. Intereses Recaudados
    total_intereses = db.session.query(db.func.sum(Cuota.monto_interes)).filter(Cuota.estado == 'Pagado').scalar() or 0
    
    # =========================================================
    # 2. PREPARACIÓN DE GRÁFICAS
    # =========================================================
    
    df_balance = pd.DataFrame({
        "Concepto": ["Capital en Caja", "Cartera Activa"],
        "Monto": [total_ahorrado, cartera_activa_real]
    })
    
    fig_balance = px.pie(
        df_balance, 
        values='Monto', 
        names='Concepto', 
        title='Distribución de Activos', 
        hole=0.4, 
        color_discrete_sequence=['#28a745', '#dc3545']
    )
    # Ajuste importante: Márgenes pequeños para que no ocupe tanto espacio
    fig_balance.update_layout(margin=dict(t=30, b=0, l=0, r=0))

    usuarios = Usuario.query.all()
    opts_users = [{'label': u.nombre_completo, 'value': u.id} for u in usuarios]

    # =========================================================
    # 3. ESTRUCTURA VISUAL
    # =========================================================
    return html.Div([
        crear_navbar(),
        dbc.Container([
            html.H2("📊 Dashboard Gerencial FONAMIG", className="text-primary mb-4"),
            
            # --- FILA DE TARJETAS (KPIs) ---
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H6("Total en Caja (Ahorros)"), 
                        html.H3(f"${total_ahorrado:,.0f}", className="text-success")
                    ])
                ], className="shadow-sm border-success h-100"), width=12, lg=4, className="mb-3"),
                
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H6("Cartera Activa (Saldo Real)"), 
                        html.H3(f"${cartera_activa_real:,.0f}", className="text-danger"),
                        html.Small(f"Desembolsado orig: ${total_prestado_bruto:,.0f}", className="text-muted")
                    ])
                ], className="shadow-sm border-danger h-100"), width=12, lg=4, className="mb-3"),

                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H6("Intereses Recaudados"), 
                        html.H3(f"${total_intereses:,.0f}", className="text-primary"),
                        html.Small("Ganancia neta", className="text-muted")
                    ])
                ], className="shadow-sm border-primary h-100"), width=12, lg=4, className="mb-3"),
            ]),

            html.Hr(),

            # --- FILA DE GRÁFICA Y DETALLE ---
            dbc.Row([
                # CORRECCIÓN AQUÍ: Quitamos 'h-100' y definimos altura en el Graph
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Visión General de Activos"),
                        dbc.CardBody(
                            dcc.Graph(
                                figure=fig_balance, 
                                config={'displayModeBar': False},
                                style={'height': '350px'} # <--- ESTO EVITA QUE CAIGA INFINITAMENTE
                            )
                        )
                    ], className="shadow-sm mb-4") 
                ], width=12, lg=6),

                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("🔍 Inspección Detallada por Usuario"),
                        dbc.CardBody([
                            html.Label("Selecciona un usuario para analizar su riesgo:"),
                            dcc.Dropdown(id="filtro-user-360", options=opts_users, placeholder="Buscar socio...", className="mb-3"),
                            
                            html.Div(id="resultado-user-360", className="p-3 border rounded bg-light", children="Selecciona a alguien de la lista...")
                        ])
                    ], className="shadow-sm h-100")
                ], width=12, lg=6)
            ])
        ], fluid=True, className="py-3")
    ])

# --- CALLBACK (Sin cambios, solo se incluye para que el archivo funcione completo) ---
@callback(
    Output("resultado-user-360", "children"),
    Input("filtro-user-360", "value")
)
def mostrar_perfil_360(user_id):
    if not user_id:
        return html.Div("Selecciona un usuario para ver sus estadísticas.", className="text-center text-muted mt-5")

    user = Usuario.query.get(user_id)
    ahorros = db.session.query(db.func.sum(Aporte.monto)).filter_by(usuario_id=user_id, estado='Aprobado').scalar() or 0
    
    deuda = 0
    cuotas_mora = 0
    prestamos = Prestamo.query.filter_by(usuario_id=user_id, estado='Activo').all()
    
    for p in prestamos:
        pendientes = Cuota.query.filter(Cuota.prestamo_id == p.id, Cuota.estado.in_(['Pendiente', 'Mora'])).all()
        deuda += sum(c.monto_total for c in pendientes)
        cuotas_mora += sum(1 for c in pendientes if c.estado == 'Mora')

    color_estado = "success" if cuotas_mora == 0 else "danger"
    estado_texto = "Excelente Cliente (Al día)" if cuotas_mora == 0 else f"⚠️ ATENCIÓN: Tiene {cuotas_mora} cuotas en Mora"

    return html.Div([
        html.Div([
            html.H4(user.nombre_completo, className="text-primary mb-0"),
            html.Span(f"@{user.username}", className="text-muted small")
        ], className="mb-3"),
        
        dbc.Row([
            dbc.Col([
                html.Div("Ahorro Total", className="small text-uppercase text-muted"),
                html.H4(f"${ahorros:,.0f}", className="text-success")
            ], width=6, className="border-end"),
            dbc.Col([
                html.Div("Deuda Total", className="small text-uppercase text-muted"),
                html.H4(f"${deuda:,.0f}", className="text-danger")
            ], width=6, className="text-end"),
        ], className="mb-4 bg-white p-2 rounded border"),
        
        dbc.Alert([
            html.I(className="bi bi-info-circle-fill me-2"),
            estado_texto
        ], color=color_estado, className="d-flex align-items-center"),
        
        html.Hr(),
        html.Div([
            html.Small("Email de contacto:", className="fw-bold"),
            html.Span(f" {user.email}", className="d-block")
        ], className="text-muted small")
    ])