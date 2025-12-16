import dash
from dash import dcc, html, Input, Output, State, callback, dash_table
import dash_bootstrap_components as dbc
from flask_login import current_user
from database.models import Prestamo, Cuota
from database.db import db
from utils.financiero import calcular_plan_pagos
from utils.config import TASA_INTERES_ADMIN
from components.navbar import crear_navbar
from datetime import datetime

# ... (imports iguales) ...

def layout():
    if not current_user.is_authenticated:
        return html.Div("Inicia sesión.")

    return html.Div([
        crear_navbar(),
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H3("📝 Solicitar Dinero", className="text-center")),
                        dbc.CardBody([
                            # LENGUAJE SENCILLO
                            html.Label("¿Cuánto dinero necesitas?", className="fs-4 fw-bold text-primary"),
                            dbc.Input(id="input-monto", type="number", placeholder="Ej: 500000", min=0, step=1000, className="mb-4 form-control-lg"), # form-control-lg hace la caja grande
                            
                            html.Label("¿En cuántos meses quieres pagar?", className="fs-4 fw-bold text-primary"),
                            dbc.Input(id="input-cuotas", type="number", placeholder="Ej: 6", min=1, max=36, step=1, className="mb-4 form-control-lg"),
                            
                            html.Label("Interés mensual (Fijo)", className="text-muted"),
                            dbc.Input(
                                id="input-tasa", 
                                value=f"{TASA_INTERES_ADMIN * 100}%", 
                                disabled=True, 
                                className="mb-4 bg-light fw-bold"
                            ),
                            
                            # BOTONES GRANDES
                            dbc.Button("1. CALCULAR CUOTAS", id="btn-simular", color="info", className="w-100 mb-3 btn-lg fw-bold text-white"),
                            dbc.Button("2. ¡ENVIAR SOLICITUD!", id="btn-solicitar", color="success", className="w-100 btn-lg fw-bold", disabled=True),
                            
                            html.Div(id="alerta-solicitud", className="mt-3")
                        ])
                    ], className="shadow border-0") # border-0 para que se vea más limpio
                ], width=12, md=6, className="mx-auto"), # Centrado
                
                # ... (La columna de resultados se mantiene, o puedes ocultarla hasta que calculen)
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Así quedarían tus pagos:"),
                        dbc.CardBody([
                            html.Div(id="resumen-pago", className="fs-5", children="Presiona 'Calcular' para ver."),
                            html.Hr(),
                            html.Div(id="tabla-amortizacion")
                        ])
                    ], className="shadow border-0 mt-3 mt-md-0")
                ], width=12, md=6)
            ])
        ])
    ])
# ... (Callbacks iguales) ...

@callback(
    [Output("tabla-amortizacion", "children"),
     Output("resumen-pago", "children"),
     Output("btn-solicitar", "disabled")],
    [Input("btn-simular", "n_clicks")],
    [State("input-monto", "value"),
     State("input-cuotas", "value")]
)
def simular_prestamo(n_clicks, monto, cuotas):
    if not n_clicks or not monto or not cuotas:
        return dash.no_update, "Ingresa monto y cuotas.", True

    df_plan = calcular_plan_pagos(monto, TASA_INTERES_ADMIN, cuotas)
    
    tabla = dash_table.DataTable(
        data=df_plan.to_dict('records'),
        columns=[{"name": i, "id": i} for i in df_plan.columns],
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'center', 'padding': '10px'},
        style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
        page_size=10
    )
    
    valor_cuota = df_plan.iloc[0]['Valor Cuota']
    total_pagar = df_plan['Valor Cuota'].sum()
    
    resumen = html.Div([
        html.P(f"Valor Cuota Aprox: ${valor_cuota:,.2f}"),
        html.P(f"Total a Pagar al final: ${total_pagar:,.2f}", className="text-primary fw-bold")
    ])
    
    return tabla, resumen, False 

@callback(
    Output("alerta-solicitud", "children"),
    [Input("btn-solicitar", "n_clicks")],
    [State("input-monto", "value"),
     State("input-cuotas", "value")]
)
def enviar_solicitud(n_clicks, monto, cuotas):
    if not n_clicks:
        return dash.no_update
    
    try:
        nuevo_prestamo = Prestamo(
            usuario_id=int(current_user.id),
            monto_solicitado=monto,
            tasa_interes=TASA_INTERES_ADMIN,
            cuotas_totales=cuotas,
            fecha_solicitud=datetime.utcnow(),
            estado='Pendiente'
        )
        
        db.session.add(nuevo_prestamo)
        db.session.commit()
        
        return dbc.Alert("¡Solicitud enviada con éxito! Espera la aprobación del Admin.", color="success")
    except Exception as e:
        db.session.rollback()
        return dbc.Alert(f"Error al guardar: {str(e)}", color="danger")