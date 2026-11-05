# Simulador de ahorro para el retiro.
# Todo va en terminos reales (pesos de hoy) para no tener que adivinar la inflacion futura.
# Los rendimientos de CONSAR ya vienen netos de comision, asi que no se vuelve a restar.

import numpy as np
import pandas as pd


def proyectar(saldo_inicial, aporte_mensual, anios, rend_real_anual, crecimiento_aporte_real=0.0):
    """Saldo mes a mes (arreglo de meses + 1 valores), en pesos de hoy.

    El aporte se hace al final de cada mes. El aporte esta en pesos de hoy y puede crecer
    una vez al año por encima de la inflacion (crecimiento_aporte_real, en %).
    Los rendimientos van en % anual (2.5 = 2.5%).
    """
    meses = int(round(anios * 12))
    r_mensual = (1 + rend_real_anual / 100) ** (1 / 12) - 1
    g = crecimiento_aporte_real / 100
    saldo = float(saldo_inicial)
    serie = [saldo]
    for m in range(1, meses + 1):
        aporte = aporte_mensual * (1 + g) ** ((m - 1) // 12)
        saldo = saldo * (1 + r_mensual) + aporte
        serie.append(saldo)
    return np.array(serie)


def saldo_final(saldo_inicial, aporte_mensual, anios, rend_real_anual, crecimiento_aporte_real=0.0):
    return proyectar(saldo_inicial, aporte_mensual, anios, rend_real_anual, crecimiento_aporte_real)[-1]


def total_aportado(saldo_inicial, aporte_mensual, anios, crecimiento_aporte_real=0.0):
    """Lo que pondria la persona en total, sin rendimientos."""
    return proyectar(saldo_inicial, aporte_mensual, anios, 0.0, crecimiento_aporte_real)[-1]


def rendimientos_por_afore(gen_real, fondo, plazo="5 años", fecha=None):
    """Rendimiento real de cada AFORE en un fondo, de mayor a menor.

    gen_real es la tabla gen despues de pasarla por agregar_real. Si no se da fecha
    se usa el ultimo mes disponible.
    """
    d = gen_real[(gen_real["fondo"] == fondo) & (gen_real["plazo"] == plazo)].dropna(subset=["real"])
    if fecha is None:
        fecha = d["fecha"].max()
    return d[d["fecha"] == fecha].set_index("afore")["real"].sort_values(ascending=False)


def ajustar_persistencia(rend, persistencia):
    """Reduce la distancia de cada AFORE al promedio.

    persistencia = 1 deja los rendimientos como estan (la ventaja pasada se repite igual).
    persistencia = 0 hace que todas rindan el promedio.
    """
    promedio = rend.mean()
    return promedio + persistencia * (rend - promedio)


def comparar_afores(rend_real, saldo_inicial, aporte_mensual, anios, crecimiento_aporte_real=0.0):
    """Tabla con el saldo final de cada AFORE y cuanto le saca a la peor."""
    out = pd.DataFrame({"rend_real_%": rend_real})
    out["saldo_final"] = [saldo_final(saldo_inicial, aporte_mensual, anios, r, crecimiento_aporte_real)
                          for r in rend_real]
    out["vs_peor_$"] = out["saldo_final"] - out["saldo_final"].min()
    out["vs_peor_%"] = out["saldo_final"] / out["saldo_final"].min() * 100 - 100
    return out
