from database.db import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# --- MODELO DE USUARIO ---
class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default='usuario') # 'admin' o 'usuario'
    
    # Datos personales
    nombre_completo = db.Column(db.String(100))
    email = db.Column(db.String(100))
    telefono = db.Column(db.String(20))
    
    # Estado del usuario (Para que el admin apruebe el ingreso)
    activo = db.Column(db.Boolean, default=False) 
    
    # Relaciones
    aportes = db.relationship('Aporte', backref='usuario', lazy=True)
    prestamos = db.relationship('Prestamo', backref='usuario', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# --- MODELO DE APORTES (Ahorros/Entradas) ---
class Aporte(db.Model):
    __tablename__ = 'aportes'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_confirmacion = db.Column(db.DateTime, nullable=True) # Cuando el admin aprueba
    
    monto = db.Column(db.Float, nullable=False)
    tipo = db.Column(db.String(50), default='Aporte Mensual') # Aporte, Multa, Extra, etc.
    estado = db.Column(db.String(20), default='Pendiente') # Pendiente, Aprobado, Rechazado
    notas = db.Column(db.String(200))

# --- MODELO DE PRESTAMOS ---
class Prestamo(db.Model):
    __tablename__ = 'prestamos'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    monto_solicitado = db.Column(db.Float, nullable=False)
    tasa_interes = db.Column(db.Float, nullable=False) # Ej: 0.05 para 5%
    cuotas_totales = db.Column(db.Integer, nullable=False)
    
    fecha_solicitud = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_aprobacion = db.Column(db.DateTime, nullable=True)
    
    estado = db.Column(db.String(20), default='Pendiente') # Pendiente, Activo, Pagado, Rechazado, Vencido
    
    # Relación con las cuotas generadas
    plan_pagos = db.relationship('Cuota', backref='prestamo', lazy=True, cascade="all, delete-orphan")

# --- MODELO DE CUOTAS (Tabla de amortización) ---
class Cuota(db.Model):
    __tablename__ = 'cuotas'
    
    id = db.Column(db.Integer, primary_key=True)
    prestamo_id = db.Column(db.Integer, db.ForeignKey('prestamos.id'), nullable=False)
    
    numero_cuota = db.Column(db.Integer, nullable=False)
    fecha_vencimiento = db.Column(db.Date, nullable=False)
    
    monto_capital = db.Column(db.Float) # Parte que va al préstamo
    monto_interes = db.Column(db.Float) # Ganancia del fondo
    monto_total = db.Column(db.Float, nullable=False) # Lo que paga el usuario
    
    estado = db.Column(db.String(20), default='Pendiente') # Pendiente, Pagado, Mora
    fecha_pago = db.Column(db.DateTime, nullable=True)