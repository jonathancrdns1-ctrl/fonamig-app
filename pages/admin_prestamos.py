import dash
from dash import dcc, html, Input, Output, State, callback, dash_table
import dash_bootstrap_components as dbc
from database.models import Usuario, Prestamo, Cuota
from database.db import db
from components.navbar import crear_navbar
from utils.financiero import calcular_plan_pagos # Importamos tu fórmula financiera
from datetime import datetime

# --- CARGAR SOLICITUDES PENDIENTES ---
def cargar_solicitudes():
    # Buscamos préstamos con estado 'Pendiente' y sus usuarios
    pendientes = db.session.query(Prestamo, Usuario).join(Usuario, Prestamo.usuario_id == Usuario.id).filter(Prestamo.estado == 'Pendiente').all()
    
    data = []
    for p, u in pendientes:
        data.append({
            'ID': p.id,
            'Usuario': u.nombre_completo,
            'Fecha': p.fecha_solicitud.strftime('%Y-%m-%d'),
            'Monto': f"${p.monto_solicitado:,.0f}",
            'Monto_Raw': p.monto_solicitado, # Para cálculos
            'Cuotas': p.cuotas_totales,
            'Tasa': p.tasa_interes
        })
    return data

def layout():
    data = cargar_solicitudes()

    return html.Div([
        crear_navbar(),
        dbc.Container([
            html.H2("✍️ Aprobación de Créditos", className="mb-4 text-primary"),
            
            dbc.Card([
                dbc.CardHeader("Solicitudes Pendientes de Aprobación"),
                dbc.CardBody([
                    dash_table.DataTable(
                        id='tabla-solicitudes',
                        columns=[
                            {'name': 'ID', 'id': 'ID'},
                            {'name': 'Solicitante', 'id': 'Usuario'},
                            {'name': 'Fecha', 'id': 'Fecha'},
                            {'name': 'Monto', 'id': 'Monto'},
                            {'name': 'Plazo (Meses)', 'id': 'Cuotas'},
                        ],
                        data=data,
                        row_selectable='single',
                        style_table={'overflowX': 'auto'},
                        style_cell={'textAlign': 'center', 'padding': '10px'},
                        style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
                        page_size=10
                    ),
                    
                    html.Div([
                        dbc.Button("✅ Aprobar Crédito y Generar Pagos", id="btn-aprobar-prestamo", color="success", className="me-3"),
                        dbc.Button("❌ Rechazar Solicitud", id="btn-rechazar-prestamo", color="danger")
                    ], className="mt-4 d-flex justify-content-end"),
                    
                    html.Div(id="msg-gestion-prestamo", className="mt-3")
                ])
            ], className="shadow")
        ])
    ])

# --- CALLBACK DE APROBACIÓN ---
@callback(
    [Output("msg-gestion-prestamo", "children"),
     Output("tabla-solicitudes", "data")],
    [Input("btn-aprobar-prestamo", "n_clicks"),
     Input("btn-rechazar-prestamo", "n_clicks")],
    [State("tabla-solicitudes", "selected_rows"),
     State("tabla-solicitudes", "data")]
)
def procesar_solicitud(btn_ok, btn_cancel, selected, data):
    ctx = dash.callback_context
    if not ctx.triggered or not selected:
        return dash.no_update, dash.no_update
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    row_idx = selected[0]
    
    prestamo_id = data[row_idx]['ID']
    monto = data[row_idx]['Monto_Raw']
    cuotas = data[row_idx]['Cuotas']
    tasa = data[row_idx]['Tasa']
    
    try:
        prestamo = Prestamo.query.get(prestamo_id)
        
        if button_id == "btn-aprobar-prestamo":
            # 1. Actualizar estado del préstamo
            prestamo.estado = 'Activo'
            prestamo.fecha_aprobacion = datetime.utcnow()
            
            # 2. GENERAR TABLA DE AMORTIZACIÓN (Cuotas)
            # Usamos tu función financiera
            df_plan = calcular_plan_pagos(monto, tasa, cuotas)
            
            for index, row in df_plan.iterrows():
                nueva_cuota = Cuota(
                    prestamo_id=prestamo.id,
                    numero_cuota=int(row['Cuota #']),
                    fecha_vencimiento=row['Fecha Pago'],
                    monto_capital=row['Abono Capital'],
                    monto_interes=row['Interés'],
                    monto_total=row['Valor Cuota'],
                    estado='Pendiente'
                )
                db.session.add(nueva_cuota)
            
            msg = dbc.Alert(f"Préstamo #{prestamo.id} APROBADO. Se generaron {cuotas} cuotas de cobro.", color="success")

        elif button_id == "btn-rechazar-prestamo":
            prestamo.estado = 'Rechazado'
            msg = dbc.Alert("Solicitud rechazada.", color="warning")
            
        db.session.commit()
        return msg, cargar_solicitudes()

    except Exception as e:
        db.session.rollback()
        return dbc.Alert(f"Error técnico: {str(e)}", color="danger"), dash.no_update