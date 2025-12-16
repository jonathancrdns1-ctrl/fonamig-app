from app import server, db
from database.models import Usuario

with server.app_context():
    db.create_all()
    
    # Crear un usuario ADMIN por defecto si no existe
    if not Usuario.query.filter_by(username='admin').first():
        admin = Usuario(username='admin', rol='admin', nombre_completo='Admin Principal', activo=True)
        admin.set_password('admin123') # Contraseña temporal
        db.session.add(admin)
        db.session.commit()
        print("✅ Base de datos creada y usuario 'admin' registrado.")
    else:
        print("ℹ️ La base de datos ya existe.")