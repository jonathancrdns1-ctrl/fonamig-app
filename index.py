from dash import dcc, html, Input, Output
from flask_login import current_user, logout_user
import dash_bootstrap_components as dbc

# Importaciones del sistema
from app import app, server

# Importamos TODAS las páginas (incluyendo la nueva admin_usuarios y perfil_usuario)
from pages import (
    login, registro, home, prestamo, mis_prestamos, 
    mis_aportes, perfil_usuario,
    admin_reportes, admin_pagos, admin_aportes, admin_usuarios,admin_prestamos
)

# Layout base (Contenedor principal)
app.layout = html.Div([
    dcc.Location(id="url", refresh=True),
    html.Div(id="page-content")
])

@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname")
)
def display_page(pathname):
    # 1. MANEJO DE CIERRE DE SESIÓN (Prioridad Alta)
    if pathname == "/logout":
        if current_user.is_authenticated:
            logout_user()
        return login.layout

    # 2. RUTAS PÚBLICAS (No requieren login)
    if pathname == "/login":
        if current_user.is_authenticated:
            # Si ya está logueado, lo mandamos adentro
            if current_user.rol == 'admin':
                return admin_reportes.layout()
            return home.layout()
        return login.layout
    
    if pathname == "/registro":
        if current_user.is_authenticated:
            return home.layout()
        return registro.layout

    # 3. RUTAS PRIVADAS (Requieren usuario autenticado)
    if current_user.is_authenticated:
        
        # --- LÓGICA DE ADMINISTRADOR ---
        if current_user.rol == 'admin':
            # Si el admin va al "Home", lo redirigimos al Dashboard Gerencial
            if pathname == "/home" or pathname == "/" or pathname == "/admin_panel":
                return admin_reportes.layout()
            
            # Rutas exclusivas de Admin
            if pathname == "/admin_reportes": return admin_reportes.layout()
            if pathname == "/admin_usuarios": return admin_usuarios.layout()
            if pathname == "/admin_prestamos": return admin_prestamos.layout() # <--- Tu nueva página
            if pathname == "/admin_pagos": return admin_pagos.layout()
            if pathname == "/admin_aportes": return admin_aportes.layout()

        # --- LÓGICA DE USUARIO ESTÁNDAR ---
        else:
            # Si un usuario normal intenta entrar a páginas de admin, lo devolvemos al home
            if "/admin" in pathname:
                return home.layout()
            
            if pathname == "/home" or pathname == "/":
                return home.layout()

        # --- RUTAS COMUNES (Para ambos roles) ---
        if pathname == "/prestamo": return prestamo.layout()
        if pathname == "/mis_prestamos": return mis_prestamos.layout()
        if pathname == "/mis_aportes": return mis_aportes.layout()
        if pathname == "/perfil": return perfil_usuario.layout()

        # Si la ruta no existe, por defecto al Home (o Dashboard si es admin)
        if current_user.rol == 'admin':
            return admin_reportes.layout()
        return home.layout()

    # 4. SI NO ESTÁ AUTENTICADO Y QUIERE ENTRAR A OTRA COSA -> LOGIN
    return login.layout

if __name__ == "__main__":
    # IMPORTANTE: host='0.0.0.0' abre las puertas a la red
    app.run(host='0.0.0.0', port=8050, debug=False)