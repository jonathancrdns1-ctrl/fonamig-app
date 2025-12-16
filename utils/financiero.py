import pandas as pd
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

def calcular_plan_pagos(monto, tasa_mensual, num_cuotas, fecha_inicio=None):
    """
    Genera una tabla de amortización (Sistema Francés).
    monto: Cantidad prestada.
    tasa_mensual: Interés en decimal (ej: 0.02 para 2%).
    num_cuotas: Cantidad de meses.
    """
    if fecha_inicio is None:
        fecha_inicio = date.today()
        
    # Fórmula de cuota fija: R = P * (r * (1+r)^n) / ((1+r)^n - 1)
    if tasa_mensual > 0:
        cuota = monto * (tasa_mensual * (1 + tasa_mensual)**num_cuotas) / ((1 + tasa_mensual)**num_cuotas - 1)
    else:
        cuota = monto / num_cuotas # Si la tasa es 0% (préstamos familiares sin interés)

    saldo = monto
    plan = []

    for i in range(1, num_cuotas + 1):
        interes = saldo * tasa_mensual
        capital = cuota - interes
        saldo -= capital
        
        # Fecha de vencimiento (mes a mes)
        vencimiento = fecha_inicio + relativedelta(months=i)
        
        plan.append({
            'Cuota #': i,
            'Fecha Pago': vencimiento,
            'Valor Cuota': round(cuota, 2),
            'Interés': round(interes, 2),
            'Abono Capital': round(capital, 2),
            'Saldo Restante': round(saldo if saldo > 0 else 0, 2)
        })
        
    return pd.DataFrame(plan)