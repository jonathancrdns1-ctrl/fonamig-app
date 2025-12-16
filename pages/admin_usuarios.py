import dash
from dash import dcc, html, Input, Output, State, callback, dash_table
import dash_bootstrap_components as dbc
from database.models import Usuario, Prestamo, Aporte
from database.db import db
from components.navbar import crear_navbar

def layout():
    # Cargar usuarios
    usuarios = Usuario.query.all()
    data_users = [{
        'ID': u.id,
        'Usuario': u.username,
        'Nombre': u.nombre_completo,
        'Rol': u.rol,
        'Activo': 'SI' if u.activo else 'NO'
    } for u in usuarios]

    return html.Div([
        crear_navbar(),
        dbc.Container([
            html.H2("🛠️ Panel de Control Total (Modo Admin)", className="mb-4 text-danger"),
            
            # 1. TABLA MAESTRA DE USUARIOS
            dbc.Card([
                dbc.CardHeader("1. Selecciona un Usuario para Administrarlo"),
                dbc.CardBody([
                    dash_table.DataTable(
                        id='master-table-users',
                        columns=[
                            {'name': 'ID', 'id': 'ID'},
                            {'name': 'Usuario', 'id': 'Usuario'},
                            {'name': 'Nombre', 'id': 'Nombre'},
                            {'name': 'Rol', 'id': 'Rol'},
                            {'name': 'Activo', 'id': 'Activo'},
                        ],
                        data=data_users,
                        row_selectable='single',
                        filter_action="native",
                        style_table={'overflowX': 'auto'},
                        style_cell={'textAlign': 'left'},
                        page_size=5
                    ),
                    html.Div([
                        dbc.Button("Activar", id="btn-quick-active", size="sm", color="success", className="me-2"),
                        dbc.Button("Bloquear", id="btn-quick-block", size="sm", color="dark", className="me-2"),
                        dbc.Button("Hacer Admin", id="btn-quick-admin", size="sm", color="warning"),
                    ], className="mt-2")
                ])
            ], className="shadow mb-4"),

            # 2. SECCIÓN DE EDICIÓN
            html.Div(id="editor-finanzas-container", children=[
                html.H4("Edición Directa (Modifica y luego presiona Guardar)", className="text-center mb-3"),
                
                dbc.Row([
                    # --- EDITAR PRÉSTAMOS ---
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("✏️ Editar Préstamos"),
                            dbc.CardBody([
                                dash_table.DataTable(
                                    id='editor-prestamos',
                                    columns=[
                                        {'name': 'ID', 'id': 'id', 'editable': False},
                                        {'name': 'Monto ($)', 'id': 'monto_solicitado', 'editable': True, 'type': 'numeric'},
                                        {'name': 'Cuotas', 'id': 'cuotas_totales', 'editable': True, 'type': 'numeric'},
                                        {'name': 'Estado', 'id': 'estado', 'editable': True, 'presentation': 'dropdown'},
                                    ],
                                    dropdown={
                                        'estado': {
                                            'options': [
                                                {'label': 'Pendiente', 'value': 'Pendiente'},
                                                {'label': 'Activo', 'value': 'Activo'},
                                                {'label': 'Pagado', 'value': 'Pagado'},
                                                {'label': 'Rechazado', 'value': 'Rechazado'},
                                                {'label': 'Vencido', 'value': 'Vencido'}
                                            ]
                                        }
                                    },
                                    data=[],
                                    row_deletable=True, # El usuario puede borrar filas aquí
                                    style_header={'backgroundColor': '#ffcccc', 'fontWeight': 'bold'},
                                    style_data_conditional=[{'if': {'column_editable': True}, 'backgroundColor': 'rgb(255, 255, 235)'}]
                                ),
                                dbc.Button("💾 Sincronizar Préstamos (Guardar/Borrar)", id="btn-save-prestamos", color="danger", className="w-100 mt-2")
                            ])
                        ])
                    ], width=12, lg=6),

                    # --- EDITAR APORTES ---
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("✏️ Editar Aportes"),
                            dbc.CardBody([
                                dash_table.DataTable(
                                    id='editor-aportes',
                                    columns=[
                                        {'name': 'ID', 'id': 'id', 'editable': False},
                                        {'name': 'Monto', 'id': 'monto', 'editable': True, 'type': 'numeric'},
                                        {'name': 'Tipo', 'id': 'tipo', 'editable': True},
                                        {'name': 'Estado', 'id': 'estado', 'editable': True, 'presentation': 'dropdown'},
                                    ],
                                    dropdown={
                                        'estado': {
                                            'options': [
                                                {'label': 'Pendiente', 'value': 'Pendiente'},
                                                {'label': 'Aprobado', 'value': 'Aprobado'},
                                                {'label': 'Rechazado', 'value': 'Rechazado'}
                                            ]
                                        }
                                    },
                                    data=[],
                                    row_deletable=True,
                                    style_header={'backgroundColor': '#ccffcc', 'fontWeight': 'bold'},
                                    style_data_conditional=[{'if': {'column_editable': True}, 'backgroundColor': 'rgb(255, 255, 235)'}]
                                ),
                                dbc.Button("💾 Sincronizar Aportes (Guardar/Borrar)", id="btn-save-aportes", color="success", className="w-100 mt-2")
                            ])
                        ])
                    ], width=12, lg=6),
                ]),
                html.Div(id="msg-god-mode", className="mt-3 text-center fw-bold")
            ])
        ])
    ])

# --- CALLBACK 1: CARGAR DATOS ---
@callback(
    [Output("editor-prestamos", "data"), Output("editor-aportes", "data"), Output("msg-god-mode", "children")],
    Input("master-table-users", "selected_rows"),
    State("master-table-users", "data")
)
def cargar_datos_usuario(selected_rows, data_users):
    if not selected_rows:
        return [], [], "Selecciona un usuario arriba."
    
    row_idx = selected_rows[0]
    user_id = data_users[row_idx]['ID']
    
    prestamos = Prestamo.query.filter_by(usuario_id=user_id).all()
    data_p = [{'id': p.id, 'monto_solicitado': p.monto_solicitado, 'cuotas_totales': p.cuotas_totales, 'estado': p.estado} for p in prestamos]

    aportes = Aporte.query.filter_by(usuario_id=user_id).all()
    data_a = [{'id': a.id, 'monto': a.monto, 'tipo': a.tipo, 'estado': a.estado} for a in aportes]
    
    return data_p, data_a, f"Editando a: {data_users[row_idx]['Nombre']}"

# --- CALLBACK 2: GUARDAR PRÉSTAMOS (INCLUYE BORRADO) ---
@callback(
    Output("btn-save-prestamos", "children"),
    Input("btn-save-prestamos", "n_clicks"),
    State("editor-prestamos", "data"),
    State("master-table-users", "selected_rows"), # Necesitamos saber el usuario dueño
    State("master-table-users", "data"),
    prevent_initial_call=True
)
def guardar_prestamos_editados(n_clicks, rows_tabla, selected_rows, data_users):
    if not selected_rows:
        return "⚠️ Error: Selecciona usuario"
        
    try:
        user_id = data_users[selected_rows[0]]['ID']
        
        # 1. Obtener los Préstamos REALES en la Base de Datos
        prestamos_db = Prestamo.query.filter_by(usuario_id=user_id).all()
        
        # 2. Obtener los IDs que quedaron en la Tabla (Los que NO borraste)
        ids_en_tabla = [r['id'] for r in rows_tabla]
        
        # 3. Lógica de Sincronización
        for p_db in prestamos_db:
            if p_db.id not in ids_en_tabla:
                # A. Si está en DB pero NO en la tabla -> ELIMINAR
                db.session.delete(p_db)
            else:
                # B. Si está en ambos -> ACTUALIZAR
                # Buscamos la fila correspondiente en la data de la tabla
                row = next(r for r in rows_tabla if r['id'] == p_db.id)
                p_db.monto_solicitado = float(row['monto_solicitado'])
                p_db.cuotas_totales = int(row['cuotas_totales'])
                p_db.estado = row['estado']
        
        db.session.commit()
        return "✅ Cambios Guardados (Actualizado/Borrado)"
    except Exception as e:
        db.session.rollback()
        return f"Error: {str(e)}"

# --- CALLBACK 3: GUARDAR APORTES (INCLUYE BORRADO) ---
@callback(
    Output("btn-save-aportes", "children"),
    Input("btn-save-aportes", "n_clicks"),
    State("editor-aportes", "data"),
    State("master-table-users", "selected_rows"),
    State("master-table-users", "data"),
    prevent_initial_call=True
)
def guardar_aportes_editados(n_clicks, rows_tabla, selected_rows, data_users):
    if not selected_rows:
        return "⚠️ Error: Selecciona usuario"

    try:
        user_id = data_users[selected_rows[0]]['ID']
        
        aportes_db = Aporte.query.filter_by(usuario_id=user_id).all()
        ids_en_tabla = [r['id'] for r in rows_tabla]
        
        for a_db in aportes_db:
            if a_db.id not in ids_en_tabla:
                # BORRAR
                db.session.delete(a_db)
            else:
                # ACTUALIZAR
                row = next(r for r in rows_tabla if r['id'] == a_db.id)
                a_db.monto = float(row['monto'])
                a_db.tipo = row['tipo']
                a_db.estado = row['estado']
        
        db.session.commit()
        return "✅ Cambios Guardados"
    except Exception as e:
        db.session.rollback()
        return f"Error: {str(e)}"
    
# --- CALLBACK 4: ACCIONES RÁPIDAS (Se mantiene igual) ---
@callback(
    Output("master-table-users", "data"),
    [Input("btn-quick-active", "n_clicks"), Input("btn-quick-block", "n_clicks"), Input("btn-quick-admin", "n_clicks")],
    [State("master-table-users", "selected_rows"), State("master-table-users", "data")]
)
def acciones_rapidas(btn_act, btn_block, btn_adm, selected, data):
    ctx = dash.callback_context
    if not ctx.triggered or not selected: return dash.no_update
    
    user_id = data[selected[0]]['ID']
    usuario = Usuario.query.get(user_id)
    trigger = ctx.triggered[0]['prop_id'].split('.')[0]
    
    try:
        if trigger == "btn-quick-active": usuario.activo = True
        elif trigger == "btn-quick-block": usuario.activo = False
        elif trigger == "btn-quick-admin": usuario.rol = 'admin'
        
        db.session.commit()
        nuevos_users = Usuario.query.all()
        return [{'ID': u.id, 'Usuario': u.username, 'Nombre': u.nombre_completo, 'Rol': u.rol, 'Activo': 'SI' if u.activo else 'NO'} for u in nuevos_users]
    except:
        return dash.no_update