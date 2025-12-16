import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
from flask_login import current_user
from database.models import Prestamo, Cuota, Aporte
from database.db import db
from components.navbar import crear_navbar

def layout():
    if not current_user.is_authenticated:
        return html.Div("Inicia sesión primero.")

    # --- 1. CÁLCULO DE AHORROS (EL DATO ESTRELLA) ---
    ahorros_totales = db.session.query(db.func.sum(Aporte.monto)).filter(
        Aporte.usuario_id == current_user.id,
        Aporte.estado == 'Aprobado'
    ).scalar() or 0

    # --- 2. CÁLCULO DE DEUDAS (SECUNDARIO) ---
    proxima_cuota = Cuota.query.join(Prestamo).filter(
        Prestamo.usuario_id == current_user.id,
        Cuota.estado.in_(['Pendiente', 'Mora'])
    ).order_by(Cuota.fecha_vencimiento.asc()).first()

    if proxima_cuota:
        fecha_texto = proxima_cuota.fecha_vencimiento.strftime('%d-%b-%Y')
        valor_deuda = f"${proxima_cuota.monto_total:,.0f}"
        if proxima_cuota.estado == 'Mora':
            color_deuda = "danger" 
            texto_deuda = "¡Atención! Pago Atrasado"
            icono_deuda = "🚨"
        else:
            color_deuda = "info"
            texto_deuda = "Próximo vencimiento"
            icono_deuda = "📅"
    else:
        fecha_texto = ""
        valor_deuda = "Nada pendiente"
        color_deuda = "light"
        texto_deuda = "¡Estás al día!"
        icono_deuda = "✅"

    # --- DEFINICIÓN DEL MODAL DE PAGO (VENTANA EMERGENTE) ---
    modal_pago = dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("💸 Datos para realizar tu aporte")),
            dbc.ModalBody([
                html.H5("Paso 1: Transfiere tu cuota", className="text-primary"),
                html.P("Realiza la transferencia a cualquiera de estas cuentas:"),
                
                # TARJETA CON DATOS DE CUENTA (EDITA LOS NÚMEROS AQUÍ)
                dbc.Card([
                    dbc.CardBody([
                        html.B("📱 Nequi / Daviplata:"),
                        html.Br(),
                        html.Span("300 123 4567", className="h4"), # <--- PON TU NÚMERO AQUÍ
                        html.Br(),
                        html.Small("A nombre de: Jonathan Smith")   # <--- PON TU NOMBRE AQUÍ
                    ])
                ], className="mb-3 bg-light"),

                html.Hr(),

                html.H5("Paso 2: Reporta tu pago", className="text-primary"),
                html.P("Una vez transfieras, envíanos el comprobante por WhatsApp para validarlo."),
            ]),
            dbc.ModalFooter(
                dbc.Button(
                    "📲 ENVIAR COMPROBANTE AHORA",
                    # Edita el número 57300... con tu WhatsApp real
                    href="https://wa.me/573001234567?text=Hola,%20adjunto%20mi%20comprobante%20de%20pago%20para%20FONAMIG",
                    external_link=True,
                    color="success",
                    className="w-100 fw-bold"
                )
            ),
        ],
        id="modal-pago",
        is_open=False,
        centered=True,
    )

    # --- INTERFAZ PRINCIPAL ---
    return html.Div([
        crear_navbar(),
        dbc.Container([
            
            # SALUDO
            html.Div([
                html.H2(f"Bienvenido, {current_user.nombre_completo.split()[0]}", className="text-muted"),
            ], className="text-center mb-4"),

            # TARJETA DE AHORROS
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("🌟 MI DINERO GUARDADO (AHORROS)", className="text-white text-uppercase mb-2 opacity-75"),
                            html.Div("🐷", style={"fontSize": "4rem", "marginBottom": "10px"}),
                            html.H1(f"${ahorros_totales:,.0f}", className="display-1 fw-bold text-white"),
                            html.P("¡Muy buen trabajo! Tu dinero está seguro.", className="text-white lead mt-2")
                        ], className="text-center py-5")
                    ], className="shadow-lg bg-success mb-4", style={"borderRadius": "25px", "border": "none"}) 
                ], width=12, lg=8, className="mx-auto")
            ]),

            # BOTÓN DE REPORTAR PAGO Y ALERTA DE DEUDA
            dbc.Row([
                dbc.Col([
                    # Aquí insertamos el botón nuevo
                    dbc.Button(
                        "📢 REPORTAR PAGO / VER CUENTAS",
                        id="btn-abrir-modal-pago",
                        color="warning",
                        className="mb-3 w-100 fw-bold shadow-sm",
                        size="lg"
                    ),
                    # Aquí va la alerta de deuda que ya tenías
                    dbc.Alert([
                        html.H4(f"{icono_deuda} {texto_deuda}", className="alert-heading"),
                        html.Hr(),
                        html.P(f"Monto a pagar: {valor_deuda}", className="mb-0 fs-4 fw-bold"),
                        html.Small(f"Fecha límite: {fecha_texto}", className="mb-0") if fecha_texto else None
                    ], color=color_deuda, className="shadow-sm", style={"borderRadius": "15px"})
                ], width=12, lg=6, className="mx-auto")
            ], className="mb-4"),

            html.Hr(className="my-4"),

            # BOTONES DE ACCIÓN
            html.H3("¿Qué deseas hacer?", className="text-center mb-4 text-muted"),
            dbc.Row([
                # Guardar Dinero
                dbc.Col([
                    dcc.Link([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div("📥", style={"fontSize": "3.5rem"}),
                                html.H4("Guardar Dinero", className="mt-2 fw-bold text-success"),
                            ], className="text-center py-4")
                        ], className="shadow hover-zoom h-100", style={"borderRadius": "20px"})
                    ], href="/mis_aportes", style={"textDecoration": "none"})
                ], width=6, md=3, className="mb-3"),

                # Ver Cuotas
                dbc.Col([
                    dcc.Link([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div("📅", style={"fontSize": "3.5rem"}),
                                html.H4("Ver Cuotas", className="mt-2 fw-bold text-primary"),
                            ], className="text-center py-4")
                        ], className="shadow hover-zoom h-100", style={"borderRadius": "20px"})
                    ], href="/mis_prestamos", style={"textDecoration": "none"})
                ], width=6, md=3, className="mb-3"),

                # Pedir Prestado
                dbc.Col([
                    dcc.Link([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div("✋", style={"fontSize": "3.5rem"}), 
                                html.H4("Pedir Prestado", className="mt-2 fw-bold text-info"),
                            ], className="text-center py-4")
                        ], className="shadow hover-zoom h-100", style={"borderRadius": "20px"})
                    ], href="/prestamo", style={"textDecoration": "none"})
                ], width=6, md=3, className="mb-3"),

                # Mi Perfil
                dbc.Col([
                    dcc.Link([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div("⚙️", style={"fontSize": "3.5rem"}),
                                html.H4("Mis Datos", className="mt-2 fw-bold text-dark"),
                            ], className="text-center py-4")
                        ], className="shadow hover-zoom h-100", style={"borderRadius": "20px"})
                    ], href="/perfil", style={"textDecoration": "none"})
                ], width=6, md=3, className="mb-3"),
            ]),

            # AGREGAMOS EL MODAL AL FINAL DEL LAYOUT PARA QUE EXISTA EN LA PÁGINA
            modal_pago 

        ], className="py-4")
    ])

# --- CALLBACK PARA ABRIR/CERRAR EL MODAL ---
@callback(
    Output("modal-pago", "is_open"),
    Input("btn-abrir-modal-pago", "n_clicks"),
    State("modal-pago", "is_open"),
    prevent_initial_call=True
)
def toggle_modal(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open