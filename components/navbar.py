import dash_bootstrap_components as dbc
from flask_login import current_user

def crear_navbar():
    children_links = []

    if current_user.is_authenticated:
        # 1. Enlaces Comunes
        children_links.append(dbc.NavItem(dbc.NavLink("Inicio", href="/home")))
        children_links.append(dbc.NavItem(dbc.NavLink("Solicitar Préstamo", href="/prestamo")))

        # 2. Menú Admin (Si es administrador)
        if hasattr(current_user, 'rol') and current_user.rol == 'admin':
            children_links.append(
                dbc.DropdownMenu(
                    children=[
                        dbc.DropdownMenuItem("📊 Dashboard Gerencial", href="/admin_reportes"),
                        dbc.DropdownMenuItem(divider=True),
                        dbc.DropdownMenuItem("👥 Gestionar Usuarios", href="/admin_usuarios"),
                        dbc.DropdownMenuItem("✍️ Aprobar Créditos", href="/admin_prestamos"),
                        dbc.DropdownMenuItem("💰 Registrar Pagos", href="/admin_pagos"),
                        dbc.DropdownMenuItem("📥 Gestionar Aportes", href="/admin_aportes"),
                    ],
                    nav=True,
                    in_navbar=True,
                    label="👑 Admin",
                    className="fw-bold text-warning"
                )
            )

        # 3. Menú Usuario (Perfil y Logout)
        children_links.append(
            dbc.DropdownMenu(
                children=[
                    # --- CORRECCIÓN AQUÍ ---
                    # Quitamos 'header=True' para que sea un botón clicable normal
                    dbc.DropdownMenuItem("Mis Datos", href="/perfil"), 
                    
                    dbc.DropdownMenuItem("Mis Préstamos", href="/mis_prestamos"),
                    dbc.DropdownMenuItem("Mis Aportes", href="/mis_aportes"),
                    dbc.DropdownMenuItem(divider=True),
                    dbc.DropdownMenuItem("Cerrar Sesión", href="/logout", className="text-danger"),
                ],
                nav=True,
                in_navbar=True,
                label=current_user.nombre_completo if hasattr(current_user, 'nombre_completo') else "Mi Cuenta",
                align_end=True
            )
        )

# ... (Imports y lógica igual) ...

    return dbc.NavbarSimple(
        children=children_links,
        brand="FONAMIG 💰",
        brand_href="/home",
        color="primary", # Esto lo sobrescribirá nuestro CSS
        dark=True,
        className="mb-4 navbar-custom", # <--- AQUÍ ESTÁ EL CAMBIO IMPORTANTE
        fluid=True # Para que ocupe todo el ancho
    )

