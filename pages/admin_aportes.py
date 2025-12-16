import dash
from dash import dcc, html, Input, Output, State, callback, dash_table
import dash_bootstrap_components as dbc
from database.models import Usuario, Aporte
from database.db import db
from components.navbar import crear_navbar
from datetime import datetime

# --- FUNCION PARA CARGAR DATOS ---
def cargar_aportes_pendientes():
    # Hacemos un JOIN implícito para obtener el nombre del usuario
    # Buscamos solo los que dicen 'Pendiente'
    pendientes = db.session.query(Aporte, Usuario).join(Usuario, Aporte.usuario_id == Usuario.id).filter(Aporte.estado == 'Pendiente').all()
    
    data = []
    for aporte, usuario in pendientes:
        data.append({
            'ID': aporte.id,
            'Usuario': usuario.nombre_completo,
            'Fecha': aporte.fecha_registro.strftime('%Y-%m-%d'),
            'Tipo': aporte.tipo,
            'Monto': aporte.monto, # Mantenemos numero para ordenar
            'Monto ($)': f"${aporte.monto:,.0f}", # Texto bonito
            'Nota': aporte.notas
        })
    return data

# --- LAYOUT DINÁMICO ---
def layout():
    # Cargamos los datos al abrir la página
    data_inicial = cargar_aportes_pendientes()

    return html.Div([
        crear_navbar(),
        dbc.Container([
            html.H2("📥 Gestión de Aportes y Ahorros", className="mb-4 text-primary"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Solicitudes de Aporte Pendientes"),
                        dbc.CardBody([
                            html.P("Selecciona una fila para aprobar o rechazar el ingreso del dinero.", className="text-muted"),
                            
                            dash_table.DataTable(
                                id='tabla-aportes-pendientes',
                                columns=[
                                    {'name': 'ID', 'id': 'ID'},
                                    {'name': 'Usuario', 'id': 'Usuario'},
                                    {'name': 'Fecha', 'id': 'Fecha'},
                                    {'name': 'Tipo', 'id': 'Tipo'},
                                    {'name': 'Monto', 'id': 'Monto ($)'},
                                    {'name': 'Nota', 'id': 'Nota'},
                                ],
                                data=data_inicial,
                                row_selectable='single', # Solo uno a la vez para evitar errores
                                style_table={'overflowX': 'auto'},
                                style_cell={'textAlign': 'center', 'padding': '10px'},
                                style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
                                page_size=10
                            ),
                            
                            html.Div([
                                dbc.Button("✅ Aprobar Ingreso", id="btn-aprobar-aporte", color="success", className="me-3"),
                                dbc.Button("❌ Rechazar", id="btn-rechazar-aporte", color="danger")
                            ], className="mt-3 d-flex justify-content-end"),
                            
                            html.Div(id="msg-admin-aporte", className="mt-3")
                        ])
                    ], className="shadow")
                ], width=12)
            ])
        ])
    ])

# --- CALLBACKS ---
@callback(
    [Output("msg-admin-aporte", "children"), 
     Output("tabla-aportes-pendientes", "data")], # Actualizamos la tabla después de la acción
    [Input("btn-aprobar-aporte", "n_clicks"),
     Input("btn-rechazar-aporte", "n_clicks")],
    [State("tabla-aportes-pendientes", "selected_rows"),
     State("tabla-aportes-pendientes", "data")]
)
def gestionar_aporte(btn_aprob, btn_rech, selected_rows, data):
    ctx = dash.callback_context
    if not ctx.triggered or not selected_rows:
        return dash.no_update, dash.no_update
    
    # Identificar qué botón se oprimió
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Obtener ID del aporte seleccionado
    row_idx = selected_rows[0]
    aporte_id = data[row_idx]['ID']
    
    try:
        aporte = Aporte.query.get(aporte_id)
        
        if button_id == "btn-aprobar-aporte":
            aporte.estado = 'Aprobado'
            aporte.fecha_confirmacion = datetime.utcnow()
            mensaje = dbc.Alert(f"Aporte de {aporte.monto:,.0f} aprobado exitosamente.", color="success")
            
        elif button_id == "btn-rechazar-aporte":
            aporte.estado = 'Rechazado'
            mensaje = dbc.Alert("Aporte rechazado.", color="warning")
            
        db.session.commit()
        
        # Recargar la tabla para que desaparezca el procesado
        nueva_data = cargar_aportes_pendientes()
        return mensaje, nueva_data

    except Exception as e:
        db.session.rollback()
        return dbc.Alert(f"Error: {str(e)}", color="danger"), dash.no_update