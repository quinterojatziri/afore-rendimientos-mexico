# Funciones para cargar y limpiar los datos de CONSAR y el INPC.
# Las uso desde los notebooks y desde la app para no repetir el mismo codigo.

import numpy as np
import pandas as pd

# las 10 AFOREs del archivo (sin los subfondos de ahorro voluntario)
AFORES = ["azteca", "banamex", "coppel", "inbursa", "invercap",
          "pensionissste", "principal", "profuturo", "sura", "xxi banorte"]

# plazos que uso. El plazo "historico" solo existe para un fondo, asi que lo dejo fuera
PLAZOS = ["12 meses", "24 meses", "36 meses", "5 años"]

# meses que cubre cada plazo, para calcular la inflacion de la misma ventana
MESES_PLAZO = {"12 meses": 12, "24 meses": 24, "36 meses": 36, "5 años": 60}


def cargar_y_limpiar(path):
    """Lee el csv de CONSAR y regresa tres tablas: df, gen y sistema.

    df      todo el archivo ya limpio
    gen     las 10 AFOREs en los fondos por generacion (sin promedios)
    sistema el promedio ponderado del sistema por generacion y fondo de pensiones
    """
    df = pd.read_csv(path)
    df["fecha"] = pd.to_datetime(df["fecha"])

    # un rendimiento de exactamente 0.00 casi seguro es "sin dato" (ver notebook 00)
    df["monto"] = df["monto"].replace(0, np.nan)

    # nombres como "xxi-banorte (sps1)" quedan como "xxi banorte"
    df["afore_base"] = (df["afore"]
                        .str.replace(r"\s*\(.*\)", "", regex=True)
                        .str.replace("-", " ", regex=False)
                        .str.strip())

    # las filas de promedio ponderado no son una AFORE, las marco para separarlas
    df["es_promedio"] = df["afore"].str.contains("promedio ponderado")

    # "sb 90-94 promedio ponderado" -> "90-94"
    df["fondo"] = (df["tipo_recurso"]
                   .str.replace("promedio ponderado", "", regex=False)
                   .str.replace("sb ", "", regex=False)
                   .str.strip())

    es_generacion = df["fondo"].str.match(r"^\d{2}-\d{2}$")
    gen = df[es_generacion & ~df["es_promedio"] & df["afore"].isin(AFORES) & df["plazo"].isin(PLAZOS)].copy()
    sistema = df[df["es_promedio"] & (es_generacion | (df["fondo"] == "pensiones")) & df["plazo"].isin(PLAZOS)].copy()
    return df, gen, sistema


def cargar_inpc(path):
    """INPC mensual (base 2a quincena de julio 2018 = 100) como serie con la fecha de indice."""
    return pd.read_csv(path, parse_dates=["fecha"]).set_index("fecha")["inpc"].sort_index()


def inflacion_anualizada(inpc, meses):
    """Inflacion anualizada (en %) de la ventana de `meses` meses que termina en cada fecha."""
    return ((inpc / inpc.shift(meses)) ** (12 / meses) - 1) * 100


def agregar_real(d, inpc):
    """Agrega las columnas 'inflacion' y 'real' (rendimiento real anualizado, en %).

    Los plazos de 24, 36 meses y 5 años vienen anualizados (se comprueba en el notebook 03),
    por eso la inflacion tambien se anualiza.
    """
    d = d.copy()
    d["inflacion"] = np.nan
    for plazo, n in MESES_PLAZO.items():
        m = d["plazo"] == plazo
        d.loc[m, "inflacion"] = d.loc[m, "fecha"].map(inflacion_anualizada(inpc, n))
    d["real"] = ((1 + d["monto"] / 100) / (1 + d["inflacion"] / 100) - 1) * 100
    return d
