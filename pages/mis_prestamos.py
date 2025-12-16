import dash
from dash import dcc, html, Input, Output, callback, dash_table
import dash_bootstrap_components as dbc
from flask_login import current_user
from database.models import Prestamo, Cuota
from database.db import db
from components.navbar import crear_navbar
import pandas as pd

# --- FUNCION LAYOUT (Dinámica) ---
def layout():
    if not current_user.is_authenticated:
        return html.Div("Por favor inicia sesión.")

    # Buscar préstamos del usuario logueado
    mis_prestamos = Prestamo.query.filter_by(usuario_id=current_user.id).all()
    
    # Opciones para el Dropdown
    opciones_prestamos = [
        {'label': f"Préstamo #{p.id} - ${p.monto_solicitado:,.0f} ({p.estado})", 'value': p.id}
        for p in mis_prestamos
    ]
    
    # Si no tiene préstamos, mostrar mensaje amigable
    if not mis_prestamos:
        contenido_inicial = html.Div([
            html.H4("No tienes préstamos registrados.", className="text-muted"),
            dbc.Button("Solicitar uno ahora", href="/prestamo", color="primary", className="mt-3")
        ], className="text-center py-5")
        valor_defecto = None
    else:
        # Por defecto seleccionar el último
        contenido_inicial = html.Div("Selecciona un préstamo para ver detalles.")
        valor_defecto = mis_prestamos[-1].id

    return html.Div([
        crear_navbar(),
        dbc.Container([
            html.H2("📂 Mis Préstamos", className="mb-4 text-primary"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Label("Seleccionar Préstamo:"),
                    dcc.Dropdown(
                        id="dropdown-mis-prestamos",
                        options=opciones_prestamos,
                        value=valor_defecto,
                        clearable=False,
                        className="mb-4"
                    )
                ], width=12, md=6)
            ]),
            
            html.Div(id="contenedor-detalle-prestamo", children=contenido_inicial)
        ])
    ])

# --- CALLBACK PARA MOSTRAR DETALLES ---
@callback(
    Output("contenedor-detalle-prestamo", "children"),
    Input("dropdown-mis-prestamos", "value")
)
def mostrar_detalle(prestamo_id):
    if not prestamo_id:
        return dash.no_update
    
    # 1. Obtener datos del préstamo y sus cuotas
    prestamo = Prestamo.query.get(prestamo_id)
    cuotas = Cuota.query.filter_by(prestamo_id=prestamo_id).order_by(Cuota.numero_cuota).all()
    
    if not cuotas:
        return dbc.Alert("Este préstamo está en revisión o rechazado (No tiene plan de pagos generado).", color="warning")

    # 2. Calcular totales para la barra de progreso
    total_pagar = sum(c.monto_total for c in cuotas)
    pagado = sum(c.monto_total for c in cuotas if c.estado == 'Pagado')
    porcentaje = (pagado / total_pagar) * 100 if total_pagar > 0 else 0
    
    # 3. Preparar datos para la tabla
    df_cuotas = pd.DataFrame([{
        '#': c.numero_cuota,
        'Vencimiento': c.fecha_vencimiento.strftime('%d/%m/%Y'), # <--- CAMBIO 1: FECHA CORTA
        'Valor': f"${c.monto_total:,.2f}",
        'Capital': f"${c.monto_capital:,.2f}",
        'Interés': f"${c.monto_interes:,.2f}",
        'Estado': c.estado
    } for c in cuotas])

    # 4. Construir la interfaz de detalle
    return dbc.Card([
        dbc.CardHeader(html.H5(f"Detalle del Préstamo #{prestamo.id} - Estado: {prestamo.estado}")),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H6("Progreso de Pago"),
                    dbc.Progress(label=f"{porcentaje:.1f}%", value=porcentaje, color="success", striped=True, className="mb-3"),
                    html.P(f"Pagado: ${pagado:,.2f} / Total: ${total_pagar:,.2f}")
                ])
            ]),
            html.Hr(),
            html.H6("Plan de Amortización"),
            
            # Tabla interactiva
            dash_table.DataTable(
                data=df_cuotas.to_dict('records'),
                columns=[{"name": i, "id": i} for i in df_cuotas.columns],
                style_cell={'textAlign': 'center', 'padding': '5px'},
                style_header={'backgroundColor': 'black', 'color': 'white', 'fontWeight': 'bold'},
                
                # <--- CAMBIO 2: PROPIEDAD PARA SCROLL HORIZONTAL
                style_table={'overflowX': 'auto'}, 
                
                style_data_conditional=[
                    {
                        'if': {'filter_query': '{Estado} = "Pagado"'},
                        'backgroundColor': '#d4edda',
                        'color': '#155724'
                    },
                    {
                        'if': {'filter_query': '{Estado} = "Mora"'},
                        'backgroundColor': '#f8d7da',
                        'color': '#721c24'
                    }
                ]
            )
        ])
    ], className="shadow")