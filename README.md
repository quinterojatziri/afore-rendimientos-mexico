# AFORE en México: cuánto importa elegir bien

Análisis de los rendimientos de las AFORE en México de diciembre de 2019 a diciembre de 2025, con datos abiertos de CONSAR. Descuento la comisión y la inflación y al final hay un simulador de ahorro para el retiro.

## Qué quería saber

Cada trabajador puede elegir su AFORE, pero no tenía claro cuánto cambia el resultado. Me preguntaba si sirve elegir la que ganó el último año, cuánto se llevan las comisiones y cuánto se gana de verdad una vez que se descuenta la inflación.

## Lo que encontré

Todas las cifras son de la generación 1990-94 (SB 90-94) a diciembre de 2025, salvo que diga otra cosa.

La diferencia entre AFOREs existe. A 5 años Inbursa rinde 8.40% anual y Coppel 6.00%, casi 2.4 puntos de diferencia cada año.

Pero el ranking de corto plazo predice poco. La correlación entre el orden a 12 meses y el orden a 5 años promedia 0.37. Sura fue la mejor a 12 meses (18.17%) y quedó a media tabla a 5 años (7.68%), así que elegir la AFORE que ganó el último año no es una guía muy buena.

La comisión ya no las distingue. Hoy cobran 0.54% (0.52% PensionISSSTE), una diferencia de 0.02 puntos contra 2.1 a 2.4 puntos de diferencia en rendimiento. Aun así, una comisión de 0.54% se lleva cerca de 9% del saldo a 30 años en un ejemplo ilustrativo, y 19% si fuera la de 2014.

Al descontar la inflación los números bajan mucho. A 5 años el rendimiento real va de 0.44% (Coppel) a 2.71% (Inbursa), y el rendimiento real a 12 meses fue negativo en 18 de los 22 meses entre enero de 2022 y octubre de 2023.

2022 separó a las AFOREs. En su peor momento a 12 meses Inbursa cayó 1.57% y Banamex 11.45%. Los fondos jóvenes cayeron más que los cercanos al retiro: en promedio 8.80% la SB 90-94 contra 3.65% la SB 60-64.

Elegir bien ayuda pero no es lo único. En un perfil de ejemplo (33 años, 32 de ahorro, $150,000 de saldo y $1,800 al mes) el saldo al retiro en pesos de hoy va de $915,168 con Coppel a $1,445,328 con Inbursa, si la ventaja de los últimos 5 años se mantuviera completa. Si solo se mantuviera la mitad, la diferencia baja a unos $265,000, parecido a lo que cambia el saldo por suponer un punto más o menos de rendimiento real.

## Cómo está organizado

```
afore-analysis/
├── data/
│   ├── 10_rendimientos_precio_bolsa.csv
│   └── inpc_mensual.csv
├── notebooks/
│   ├── 00_limpieza_y_eda.ipynb
│   ├── 01_analisis.ipynb
│   ├── 02_comisiones.ipynb
│   ├── 03_inflacion.ipynb
│   └── 04_simulador.ipynb
├── src/
│   ├── limpieza.py
│   └── simulacion.py
├── images/
├── app.py
├── requirements.txt
└── README.md
```

Los notebooks se leen en orden. `src/limpieza.py` tiene la carga y limpieza que usan todos los notebooks y la app, y `src/simulacion.py` tiene el cálculo del simulador. Las gráficas de cada notebook se guardan en `images/` en una carpeta con su número.

## Cómo correrlo

```
python -m venv .venv
.venv\Scripts\activate        (en Mac o Linux: source .venv/bin/activate)
pip install -r requirements.txt
streamlit run app.py
```

Para los notebooks, ábrelos en VS Code y elige el kernel de `.venv`.

## Datos

Los rendimientos vienen de CONSAR (Rendimientos de las AFORE 2019-2025, datos abiertos): 38,179 filas, 10 AFOREs y 73 meses. Son rendimientos a precio de bolsa, que según una fuente secundaria ya incluyen la comisión. Los plazos de 24, 36 meses y 5 años vienen anualizados, y eso lo comprobé con los propios datos en el notebook 03.

La inflación sale del INPC mensual de INEGI. Lo capturé en `data/inpc_mensual.csv` desde una tabla histórica publicada por El Contribuyente y lo comparé con la inflación anual oficial de 2017 a 2024, que coincide, pero conviene contrastarlo con INEGI antes de citarlo.

Las comisiones (0.54% en nueve AFOREs y 0.52% en PensionISSSTE para 2026) las tomé de notas de prensa que citan a CONSAR y hay que revisarlas en gob.mx/consar.

Comparo siempre dentro de cada generación, porque cada una invierte con un nivel de riesgo distinto. El rendimiento real es (1 + nominal) / (1 + inflación) - 1, con la inflación anualizada en el mismo plazo.

## Limitaciones

Los rendimientos son ventanas móviles, así que los meses consecutivos no son datos independientes. Por eso comparo rankings y mínimos y no hago pruebas estadísticas.

Los últimos 5 años incluyen la caída de 2022 y un rebote fuerte. Suponer que se repiten por décadas es un supuesto fuerte, y por eso el simulador deja reducir la ventaja histórica y fijar un rendimiento propio.

El simulador no calcula el ahorro a partir del sueldo y tampoco considera retiros por desempleo, cambios de AFORE, semanas cotizadas ni la pensión que resultaría de ese saldo.

Es un proyecto educativo y no es asesoría financiera. El rendimiento pasado no garantiza el futuro.
