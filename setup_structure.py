import os

# Estructura de directorios
folders = [
    "assets",
    "components",
    "database",
    "pages",
    "utils"
]

# Crear directorios
for folder in folders:
    os.makedirs(folder, exist_ok=True)
    # Crear un __init__.py en cada uno para que Python los reconozca como paquetes
    with open(os.path.join(folder, '__init__.py'), 'w') as f:
        pass

# Crear archivos vacíos clave si no existen
files = [
    "assets/styles.css",
    "app.py",
    "index.py",  # Este será el punto de entrada principal para manejar rutas
    "database/models.py",
    "database/db.py"
]

for file in files:
    if not os.path.exists(file):
        with open(file, 'w') as f:
            pass

print("✅ Estructura de carpetas creada exitosamente en FONAMIG.")