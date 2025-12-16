import dash
from dash import dcc, html, Input, Output, State, callback, dash_table
import dash_bootstrap_components as dbc
from flask_login import current_user
from database.models import Aporte
from database.db import db
from components.navbar import crear_navbar
from datetime import datetime

# --- LAYOUT DINÁMICO ---
def layout():
    if not current_user.is_authenticated:
        return html.Div("Inicia sesión primero.")

    # Cargar historial de aportes del usuario
    mis_aportes = Aporte.query.filter_by(usuario_id=current_user.id).order_by(Aporte.fecha_registro.desc()).all()
    
    # Calcular total APROBADO (Plata real)
    total_ahorrado = sum(a.monto for a in mis_aportes if a.estado == 'Aprobado')
    
    data_tabla = [{
        'Fecha': a.fecha_registro.strftime('%Y-%m-%d'),
        'Monto': f"${a.monto:,.0f}",
        'Tipo': a.tipo,
        'Estado': a.estado,
        'Notas': a.notas
    } for a in mis_aportes]

    return html.Div([
        crear_navbar(),
        dbc.Container([
            dbc.Row([
                # TARJETA DE RESUMEN
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Mi Ahorro Total", className="text-muted"),
                            html.H1(f"${total_ahorrado:,.0f}", className="text-success fw-bold"),
                            html.Small("Solo incluye aportes aprobados por el admin.")
                        ])
                    ], className="shadow-sm mb-4 border-success")
                ], width=12),
            ]),

            dbc.Row([
                # FORMULARIO DE NUEVO APORTE
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("💸 Reportar Nuevo Aporte"),
                        dbc.CardBody([
                            dbc.Label("Monto ($)"),
                            dbc.Input(id="input-monto-aporte", type="number", placeholder="Ej: 50000", min=0, className="mb-3"),
                            
                            dbc.Label("Tipo de Aporte"),
                            dcc.Dropdown(
                                id="input-tipo-aporte",
                                options=[
                                    {'label': 'Cuota Mensual Obligatoria', 'value': 'Mensual'},
                                    {'label': 'Ahorro Extra Voluntario', 'value': 'Extra'},
                                    {'label': 'Multa / Sanción', 'value': 'Multa'}
                                ],
                                value='Mensual',
                                clearable=False,
                                className="mb-3"
                            ),
                            
                            dbc.Label("Nota (Opcional)"),
                            dbc.Input(id="input-nota-aporte", type="text", placeholder="Ej: Transferencia Bancolombia...", className="mb-3"),
                            
                            dbc.Button("Reportar Aporte", id="btn-enviar-aporte", color="primary", className="w-100"),
                            html.Div(id="msg-aporte", className="mt-2")
                        ])
                    ], className="shadow h-100")
                ], width=12, md=5),
                
                # HISTORIAL
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("📜 Historial de Movimientos"),
                        dbc.CardBody([
                            dash_table.DataTable(
                                data=data_tabla,
                                columns=[{'name': i, 'id': i} for i in ['Fecha', 'Monto', 'Tipo', 'Estado']],
                                page_size=10,
                                style_cell={'textAlign': 'center'},
                                style_data_conditional=[
                                    {'if': {'filter_query': '{Estado} = "Pendiente"'}, 'color': 'orange', 'fontWeight': 'bold'},
                                    {'if': {'filter_query': '{Estado} = "Aprobado"'}, 'color': 'green', 'fontWeight': 'bold'},
                                    {'if': {'filter_query': '{Estado} = "Rechazado"'}, 'color': 'red'}
                                ]
                            )
                        ])
                    ], className="shadow h-100")
                ], width=12, md=7)
            ])
        ])
    ])

# --- CALLBACKS ---
@callback(
    Output("msg-aporte", "children"),
    Input("btn-enviar-aporte", "n_clicks"),
    [State("input-monto-aporte", "value"),
     State("input-tipo-aporte", "value"),
     State("input-nota-aporte", "value")]
)
def registrar_aporte(n_clicks, monto, tipo, nota):
    if not n_clicks:
        return dash.no_update
    
    if not monto or monto <= 0:
        return dbc.Alert("Ingresa un monto válido.", color="warning")
    
    try:
        nuevo_aporte = Aporte(
            usuario_id=current_user.id,
            monto=monto,
            tipo=tipo,
            notas=nota,
            fecha_registro=datetime.utcnow(),
            estado='Pendiente' # Requiere aprobación del Admin
        )
        
        db.session.add(nuevo_aporte)
        db.session.commit()
        
        return html.Div([
            dbc.Alert("Aporte registrado. Esperando aprobación.", color="success"),
            dcc.Location(id="recargar-aportes", href="/mis_aportes") # Truco para recargar la página y actualizar tabla
        ])
    except Exception as e:
        db.session.rollback()
        return dbc.Alert(f"Error: {str(e)}", color="danger")