import dash
# AQUI FALTABA 'callback' EN LA LISTA DE IMPORTACIONES
from dash import dcc, html, Input, Output, State, callback, dash_table 
import dash_bootstrap_components as dbc
from database.models import Usuario, Prestamo, Cuota
from database.db import db
from utils.financiero import calcular_plan_pagos
from components.navbar import crear_navbar
from datetime import datetime

# --- FUNCIONES DE CARGA DE DATOS ---
def cargar_usuarios_pendientes():
    # Esta consulta se ejecutará solo cuando se llame a la función
    users = Usuario.query.filter_by(activo=False).all()
    data = [{'ID': u.id, 'Usuario': u.username, 'Nombre': u.nombre_completo, 'Email': u.email} for u in users]
    return data

def cargar_prestamos_pendientes():
    prestamos = Prestamo.query.filter_by(estado='Pendiente').all()
    data = []
    for p in prestamos:
        user = Usuario.query.get(p.usuario_id)
        data.append({
            'ID Préstamo': p.id,
            'Solicitante': user.nombre_completo if user else 'Desconocido',
            'Monto': f"${p.monto_solicitado:,.2f}",
            'Cuotas': p.cuotas_totales,
            'Fecha': p.fecha_solicitud.strftime('%Y-%m-%d')
        })
    return data

# --- LAYOUT COMO FUNCIÓN (Para evitar el error de contexto) ---
def layout():
    return html.Div([
        crear_navbar(),
        dbc.Container([
            html.H2("Panel de Administración 👑", className="text-primary mb-4"),
            
            dbc.Tabs([
                # --- PESTAÑA 1: USUARIOS ---
                dbc.Tab(label="Usuarios Pendientes", children=[
                    dbc.CardBody([
                        html.H5("Usuarios esperando activación"),
                        dash_table.DataTable(
                            id='tabla-usuarios-pendientes',
                            columns=[{'name': i, 'id': i} for i in ['ID', 'Usuario', 'Nombre', 'Email']],
                            data=cargar_usuarios_pendientes(), # Se llama aquí, dentro del contexto activo
                            row_selectable='single',
                            style_table={'overflowX': 'auto'},
                            page_size=5
                        ),
                        dbc.Button("Activar Usuario Seleccionado", id="btn-activar-usuario", color="success", className="mt-3"),
                        html.Div(id="msg-usuario", className="mt-2")
                    ])
                ]),
                
                # --- PESTAÑA 2: PRÉSTAMOS ---
                dbc.Tab(label="Préstamos Pendientes", children=[
                    dbc.CardBody([
                        html.H5("Solicitudes de Dinero"),
                        dash_table.DataTable(
                            id='tabla-prestamos-pendientes',
                            columns=[{'name': i, 'id': i} for i in ['ID Préstamo', 'Solicitante', 'Monto', 'Cuotas', 'Fecha']],
                            data=cargar_prestamos_pendientes(), # Se llama aquí
                            row_selectable='single',
                            style_table={'overflowX': 'auto'},
                            page_size=5
                        ),
                        html.Div([
                            dbc.Button("✅ Aprobar Préstamo", id="btn-aprobar-prestamo", color="success", className="me-2"),
                            dbc.Button("❌ Rechazar Préstamo", id="btn-rechazar-prestamo", color="danger")
                        ], className="mt-3"),
                        html.Div(id="msg-prestamo", className="mt-2")
                    ])
                ])
            ])
        ])
    ])

# --- CALLBACKS ---

# 1. ACTIVAR USUARIO
@callback(
    [Output("msg-usuario", "children"), Output("tabla-usuarios-pendientes", "data")],
    Input("btn-activar-usuario", "n_clicks"),
    State("tabla-usuarios-pendientes", "selected_rows"),
    State("tabla-usuarios-pendientes", "data")
)
def activar_usuario(n_clicks, selected_rows, data):
    if not n_clicks or not selected_rows:
        return dash.no_update, dash.no_update
    
    row_index = selected_rows[0]
    user_id = data[row_index]['ID']
    
    try:
        usuario = Usuario.query.get(user_id)
        usuario.activo = True
        db.session.commit()
        # Recargamos la data para actualizar la tabla
        return dbc.Alert(f"Usuario {usuario.username} activado.", color="success"), cargar_usuarios_pendientes()
    except Exception as e:
        return dbc.Alert(f"Error: {str(e)}", color="danger"), dash.no_update

# 2. APROBAR O RECHAZAR PRÉSTAMO
@callback(
    [Output("msg-prestamo", "children"), Output("tabla-prestamos-pendientes", "data")],
    [Input("btn-aprobar-prestamo", "n_clicks"), Input("btn-rechazar-prestamo", "n_clicks")],
    State("tabla-prestamos-pendientes", "selected_rows"),
    State("tabla-prestamos-pendientes", "data")
)
def gestionar_prestamo(btn_aprob, btn_rech, selected_rows, data):
    ctx = dash.callback_context
    if not ctx.triggered or not selected_rows:
        return dash.no_update, dash.no_update
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    row_index = selected_rows[0]
    prestamo_id = data[row_index]['ID Préstamo']
    prestamo = Prestamo.query.get(prestamo_id)
    
    if not prestamo:
        return dbc.Alert("Error: Préstamo no encontrado.", color="danger"), dash.no_update

    try:
        if button_id == "btn-rechazar-prestamo":
            prestamo.estado = 'Rechazado'
            db.session.commit()
            return dbc.Alert("Préstamo rechazado.", color="warning"), cargar_prestamos_pendientes()
            
        elif button_id == "btn-aprobar-prestamo":
            # 1. Cambiar estado
            prestamo.estado = 'Activo'
            prestamo.fecha_aprobacion = datetime.utcnow()
            
            # 2. Generar Plan de Pagos REAL en la BD
            df_plan = calcular_plan_pagos(
                monto=prestamo.monto_solicitado,
                tasa_mensual=prestamo.tasa_interes,
                num_cuotas=prestamo.cuotas_totales,
                fecha_inicio=datetime.utcnow().date()
            )
            
            # 3. Insertar cada cuota en la tabla 'cuotas'
            for index, row in df_plan.iterrows():
                nueva_cuota = Cuota(
                    prestamo_id=prestamo.id,
                    numero_cuota=row['Cuota #'],
                    fecha_vencimiento=row['Fecha Pago'],
                    monto_capital=row['Abono Capital'],
                    monto_interes=row['Interés'],
                    monto_total=row['Valor Cuota'],
                    estado='Pendiente'
                )
                db.session.add(nueva_cuota)
            
            db.session.commit()
            return dbc.Alert("¡Préstamo Aprobado y Cuotas Generadas!", color="success"), cargar_prestamos_pendientes()

    except Exception as e:
        db.session.rollback()
        return dbc.Alert(f"Error crítico: {str(e)}", color="danger"), dash.no_update