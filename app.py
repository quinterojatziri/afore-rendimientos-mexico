# App de Streamlit: simulador de ahorro para el retiro.
# Para correrla:  streamlit run app.py

import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

# para que encuentre la carpeta src sin importar desde donde se corra
RAIZ = Path(__file__).parent
sys.path.insert(0, str(RAIZ / "src"))

from limpieza import cargar_y_limpiar, cargar_inpc, agregar_real  # noqa: E402
from simulacion import (proyectar, saldo_final, total_aportado,  # noqa: E402
                        rendimientos_por_afore, ajustar_persistencia)

st.set_page_config(page_title="Simulador AFORE", layout="wide")


@st.cache_data(show_spinner="Cargando datos...")
def cargar_datos():
    # se carga una sola vez y queda en cache, si no tardaria en cada click
    _, gen, _ = cargar_y_limpiar(str(RAIZ / "data" / "10_rendimientos_precio_bolsa.csv"))
    inpc = cargar_inpc(str(RAIZ / "data" / "inpc_mensual.csv"))
    return agregar_real(gen, inpc)


def fondo_de(anio_nacimiento):
    # 1992 -> "90-94". Solo sirve de 1960 a 1999, que son los fondos con datos
    inicio = anio_nacimiento // 5 * 5
    return f"{inicio % 100:02d}-{(inicio + 4) % 100:02d}"


def pesos(x):
    return f"${x:,.0f}"


gen_r = cargar_datos()
fecha_datos = gen_r["fecha"].max()

# ---------- barra lateral ----------
st.sidebar.header("Tus datos")
anio_nac = st.sidebar.number_input("Año de nacimiento", min_value=1960, max_value=1999, value=1992, step=1)
edad = date.today().year - int(anio_nac)
edad_retiro = st.sidebar.slider("Edad a la que piensas retirarte", 60, 70, 65)
saldo_inicial = st.sidebar.number_input("Saldo actual en tu AFORE ($)", min_value=0, max_value=20_000_000,
                                        value=150_000, step=10_000)
aporte = st.sidebar.number_input("Ahorro mensual a tu AFORE ($ de hoy)", min_value=0, max_value=200_000,
                                 value=1_800, step=100,
                                 help="Lo que aportas tú, tu patrón y el gobierno, más lo voluntario. "
                                      "Ponlo en pesos de hoy.")
crecimiento = st.sidebar.slider("Crecimiento real anual de tu aportación (%)", 0.0, 5.0, 0.0, 0.5,
                                help="0 significa que tu aportación solo sigue a la inflación. "
                                     "Súbelo si esperas que tu sueldo crezca más que los precios.")

st.sidebar.header("Supuestos del rendimiento")
# uso solo el plazo de 5 años. Con 36 meses la ventana arranca en el piso de 2022
# y los rendimientos salen exagerados
PLAZO = "5 años"
persistencia = st.sidebar.slider("Qué parte de la ventaja histórica se mantiene (%)", 0, 100, 50, 5,
                                 help="Con 0% todas las AFOREs rinden igual al promedio. Con 100% la diferencia "
                                      "que hubo entre ellas en los últimos 5 años se repite igual todo el tiempo. "
                                      "En el análisis vi que el ranking pasado predice poco.") / 100
fijar = st.sidebar.checkbox("Fijar yo el rendimiento real promedio", value=False,
                            help="Por defecto se usa el rendimiento de los últimos 5 años (2021 a 2025), "
                                 "que incluye un rebote fuerte después de 2022. Aquí puedes poner uno más "
                                 "prudente. Se conservan las diferencias entre AFOREs.")
rend_promedio_usuario = st.sidebar.slider("Rendimiento real promedio (% anual)", 0.0, 6.0, 1.5, 0.25,
                                          disabled=not fijar)

# ---------- encabezado ----------
st.title("Simulador de ahorro para el retiro")
st.caption("Calcula cuánto podrías juntar según la AFORE que elijas. Los resultados están en pesos de hoy "
           "(ya sin inflación). Es un ejercicio con escenarios, no una predicción ni asesoría financiera.")

anios = edad_retiro - edad
fondo = fondo_de(int(anio_nac))

if anios <= 0:
    st.warning(f"Con año de nacimiento {int(anio_nac)} tendrías {edad} años. Elige una edad de retiro mayor.")
    st.stop()

rend = rendimientos_por_afore(gen_r, fondo, plazo=PLAZO)
if rend.empty:
    st.error("No hay datos de rendimiento para esa generación.")
    st.stop()

afore_sel = st.sidebar.selectbox("Tu AFORE", list(rend.index), index=0)

st.markdown(f"Generación SB {fondo}, {anios} años de ahorro (de {edad} a {edad_retiro}). "
            f"Rendimientos al {fecha_datos:%b %Y}.")

# ---------- calculo ----------
rend_aj = ajustar_persistencia(rend, persistencia)
if fijar:
    # muevo todos los rendimientos para que el promedio sea el que puso el usuario
    rend_aj = rend_aj - rend_aj.mean() + rend_promedio_usuario

saldos = pd.Series({a: saldo_final(saldo_inicial, aporte, anios, r, crecimiento) for a, r in rend_aj.items()})
aportado = total_aportado(saldo_inicial, aporte, anios, crecimiento)
promedio = saldo_final(saldo_inicial, aporte, anios, rend_aj.mean(), crecimiento)

# ---------- resultados ----------
c1, c2, c3, c4 = st.columns(4)
c1.metric(f"Con {afore_sel}", pesos(saldos[afore_sel]), f"{(saldos[afore_sel] / promedio - 1) * 100:+.1f}% vs promedio")
c2.metric("Promedio de las 10 AFOREs", pesos(promedio))
c3.metric(f"Mejor ({saldos.idxmax()})", pesos(saldos.max()))
c4.metric(f"Peor ({saldos.idxmin()})", pesos(saldos.min()))
st.caption(f"En total pondrías {pesos(aportado)} sin contar rendimientos. "
           f"Con estos supuestos, la diferencia entre la mejor y la peor AFORE es de "
           f"{pesos(saldos.max() - saldos.min())}.")

anios_eje = np.arange(0, anios * 12 + 1) / 12
trayectorias = pd.DataFrame({
    f"Tu AFORE ({afore_sel})": proyectar(saldo_inicial, aporte, anios, rend_aj[afore_sel], crecimiento),
    "Promedio": proyectar(saldo_inicial, aporte, anios, rend_aj.mean(), crecimiento),
    f"Mejor ({saldos.idxmax()})": proyectar(saldo_inicial, aporte, anios, rend_aj.max(), crecimiento),
    f"Peor ({saldos.idxmin()})": proyectar(saldo_inicial, aporte, anios, rend_aj.min(), crecimiento),
    "Solo lo aportado": proyectar(saldo_inicial, aporte, anios, 0.0, crecimiento),
}, index=anios_eje)
trayectorias.index.name = "Años desde hoy"
st.subheader("Saldo proyectado")
st.line_chart(trayectorias)

st.subheader("Comparación por AFORE")
tabla = pd.DataFrame({
    "Rendimiento real histórico (%)": rend,
    "Rendimiento real usado (%)": rend_aj,
    "Saldo al retiro": saldos,
    "Diferencia vs promedio": saldos - promedio,
}).sort_values("Saldo al retiro", ascending=False)
st.dataframe(tabla.style.format({"Rendimiento real histórico (%)": "{:.2f}",
                                 "Rendimiento real usado (%)": "{:.2f}",
                                 "Saldo al retiro": "${:,.0f}",
                                 "Diferencia vs promedio": "${:+,.0f}"}))

with st.expander("Cómo se calcula y qué supuestos tiene"):
    st.markdown(f"""
- Rendimiento: el rendimiento real anualizado de cada AFORE en tu generación (SB {fondo}) a {PLAZO}, publicado por
  CONSAR y descontando la inflación con el INPC de INEGI. Ya viene neto de comisión.
- Persistencia ({persistencia:.0%}): solo esa parte de la diferencia entre cada AFORE y el promedio se mantiene hacia
  adelante. En el análisis el ranking de corto plazo explicó poco del largo plazo.
- Aportación: la escribes tú, en pesos de hoy, y se hace al final de cada mes. No se calcula a partir de tu sueldo.
- No incluye retiros por desempleo, cambios de AFORE, semanas cotizadas, pensión garantizada ni impuestos.
- Los últimos años incluyen la caída de 2022 y un rebote fuerte. No tiene por qué repetirse.
""")

st.caption("Proyecto educativo con datos abiertos de CONSAR e INEGI. No es asesoría financiera.")
