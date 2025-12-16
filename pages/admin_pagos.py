import dash
from dash import dcc, html, Input, Output, State, callback, dash_table
import dash_bootstrap_components as dbc
from database.models import Usuario, Prestamo, Cuota
from database.db import db
from components.navbar import crear_navbar
from datetime import datetime

# --- LAYOUT DINÁMICO ---
def layout():
    # Buscar usuarios que tengan al menos un préstamo ACTIVO
    usuarios = Usuario.query.all()
    opciones_usuarios = []
    
    for u in usuarios:
        tiene_activos = any(p.estado == 'Activo' for p in u.prestamos)
        if tiene_activos:
            opciones_usuarios.append({'label': u.nombre_completo, 'value': u.id})

    # Definimos las columnas fijas de una vez
    columnas_tabla = [{"name": i, "id": i} for i in ['ID Cuota', 'Préstamo #', 'Cuota #', 'Vence', 'Valor Total', 'Estado']]

    return html.Div([
        crear_navbar(),
        dbc.Container([
            html.H2("💰 Registrar Recuados (Pagos)", className="mb-4 text-success"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("1. Seleccionar Deudor"),
                        dbc.CardBody([
                            dbc.Label("Buscar Usuario:"),
                            dcc.Dropdown(
                                id="filtro-usuario-pago",
                                options=opciones_usuarios,
                                placeholder="Selecciona un usuario...",
                                className="mb-3"
                            ),
                        ])
                    ], className="shadow-sm h-100")
                ], width=12, md=4),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("2. Cuotas Pendientes"),
                        dbc.CardBody([
                            # CORRECCIÓN: La tabla existe SIEMPRE, pero empieza vacía
                            dash_table.DataTable(
                                id='datatable-pagos',
                                columns=columnas_tabla,
                                data=[], # Inicialmente vacía
                                row_selectable='single',
                                style_table={'overflowX': 'auto'},
                                style_cell={'textAlign': 'center'},
                                page_size=5,
                                # Mensaje cuando está vacía
                                style_data_conditional=[{
                                    'if': {'row_index': 'odd'},
                                    'backgroundColor': 'rgb(248, 248, 248)'
                                }]
                            ),
                            
                            html.Div(id="mensaje-tabla-vacia", className="text-muted text-center mt-2", children="Selecciona un usuario para cargar datos."),
                            
                            html.Hr(),
                            dbc.Button("✅ Confirmar Pago Recibido", id="btn-confirmar-pago", color="success", disabled=True, className="w-100"),
                            html.Div(id="msg-pago", className="mt-2")
                        ])
                    ], className="shadow-sm h-100")
                ], width=12, md=8)
            ])
        ])
    ])

# --- CALLBACKS ---

# 1. Cargar datos EN la tabla existente (Ya no creamos la tabla, solo inyectamos DATA)
@callback(
    [Output("datatable-pagos", "data"), 
     Output("mensaje-tabla-vacia", "children"),
     Output("btn-confirmar-pago", "disabled")],
    Input("filtro-usuario-pago", "value")
)
def cargar_deuda_usuario(usuario_id):
    if not usuario_id:
        return [], "Selecciona un usuario arriba.", True
    
    # Buscar préstamos activos del usuario
    prestamos = Prestamo.query.filter_by(usuario_id=usuario_id, estado='Activo').all()
    ids_prestamos = [p.id for p in prestamos]
    
    if not ids_prestamos:
        return [], "Este usuario no tiene préstamos activos.", True
    
    # Buscar cuotas pendientes
    cuotas = Cuota.query.filter(
        Cuota.prestamo_id.in_(ids_prestamos),
        Cuota.estado.in_(['Pendiente', 'Mora'])
    ).order_by(Cuota.fecha_vencimiento).all()
    
    if not cuotas:
        return [], "¡El usuario está al día! No hay cuotas pendientes.", True

    # Crear data para la tabla
    data = []
    for c in cuotas:
        data.append({
            'ID Cuota': c.id,
            'Préstamo #': c.prestamo_id,
            'Cuota #': c.numero_cuota,
            'Vence': c.fecha_vencimiento,
            'Valor Total': c.monto_total,
            'Estado': c.estado
        })
    
    # Retornamos data llena, borramos mensaje de error, habilitamos botón
    return data, "", False

# 2. Procesar el pago (Igual que antes, pero ahora el ID siempre existe)
@callback(
    [Output("msg-pago", "children"), Output("filtro-usuario-pago", "value")],
    Input("btn-confirmar-pago", "n_clicks"),
    [State("datatable-pagos", "selected_rows"),
     State("datatable-pagos", "data")] # No necesitamos filtro-usuario-pago aquí
)
def registrar_pago(n_clicks, selected_rows, data):
    if not n_clicks or not selected_rows:
        return dash.no_update, dash.no_update
    
    # Obtener la fila seleccionada
    row_idx = selected_rows[0]
    cuota_id = data[row_idx]['ID Cuota']
    
    try:
        # 1. Marcar cuota como pagada
        cuota = Cuota.query.get(cuota_id)
        if not cuota:
             return dbc.Alert("Error: Cuota no encontrada.", color="danger"), dash.no_update
             
        cuota.estado = 'Pagado'
        cuota.fecha_pago = datetime.utcnow()
        
        db.session.commit()
        
        # 2. Verificar si el préstamo se terminó de pagar
        prestamo = Prestamo.query.get(cuota.prestamo_id)
        cuotas_pendientes = Cuota.query.filter_by(prestamo_id=prestamo.id, estado='Pendiente').count()
        
        msg_extra = ""
        if cuotas_pendientes == 0:
            prestamo.estado = 'Pagado'
            db.session.commit()
            msg_extra = " ¡PRÉSTAMO FINALIZADO! 🥳"

        # Retornamos alerta y NULL en el dropdown para resetear la vista
        return dbc.Alert(f"Pago de ${cuota.monto_total:,.2f} registrado.{msg_extra}", color="success"), None

    except Exception as e:
        db.session.rollback()
        return dbc.Alert(f"Error al registrar pago: {str(e)}", color="danger"), dash.no_update