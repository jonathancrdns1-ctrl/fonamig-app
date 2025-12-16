import dash
from dash import dcc, html
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
        # Si está en mora, sí avisamos con rojo, si no, azul tranquilo
        if proxima_cuota.estado == 'Mora':
            color_deuda = "danger" 
            texto_deuda = "¡Atención! Pago Atrasado"
            icono_deuda = "🚨"
        else:
            color_deuda = "info" # Azul suave
            texto_deuda = "Próximo vencimiento"
            icono_deuda = "📅"
    else:
        fecha_texto = ""
        valor_deuda = "Nada pendiente"
        color_deuda = "light"
        texto_deuda = "¡Estás al día!"
        icono_deuda = "✅"

    # --- INTERFAZ POSITIVA ---
    return html.Div([
        crear_navbar(),
        dbc.Container([
            
            # 1. SALUDO AMIGABLE
            html.Div([
                html.H2(f"Bienvenido, {current_user.nombre_completo.split()[0]}", className="text-muted"),
            ], className="text-center mb-4"),

            # 2. TARJETA HÉROE: MIS AHORROS (LO PRIMERO QUE VEN)
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
                    # bg-success pone el fondo verde automáticamente
                ], width=12, lg=8, className="mx-auto")
            ]),

            # 3. INFORMACIÓN DE PAGOS (MÁS PEQUEÑO Y ABAJO)
            dbc.Row([
                dbc.Col([
                    dbc.Alert([
                        html.H4(f"{icono_deuda} {texto_deuda}", className="alert-heading"),
                        html.Hr(),
                        html.P(f"Monto a pagar: {valor_deuda}", className="mb-0 fs-4 fw-bold"),
                        html.Small(f"Fecha límite: {fecha_texto}", className="mb-0") if fecha_texto else None
                    ], color=color_deuda, className="shadow-sm", style={"borderRadius": "15px"})
                ], width=12, lg=6, className="mx-auto")
            ], className="mb-4"),

            html.Hr(className="my-4"),

            # 4. BOTONES GRANDES DE ACCIÓN
            html.H3("¿Qué deseas hacer?", className="text-center mb-4 text-muted"),
            dbc.Row([
                # AHORRAR (Acción positiva primero)
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

                # PAGAR / VER CUOTAS
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

                # PEDIR PRESTADO
                dbc.Col([
                    dcc.Link([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div("✋", style={"fontSize": "3.5rem"}), # Mano pidiendo
                                html.H4("Pedir Prestado", className="mt-2 fw-bold text-info"),
                            ], className="text-center py-4")
                        ], className="shadow hover-zoom h-100", style={"borderRadius": "20px"})
                    ], href="/prestamo", style={"textDecoration": "none"})
                ], width=6, md=3, className="mb-3"),

                # MI PERFIL
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
            ])

        ], className="py-4")
    ])