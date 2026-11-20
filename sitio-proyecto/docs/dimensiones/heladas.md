# ❄️ Heladas — NILVER

<div class="dim-card amber" markdown>
<div class="dim-card-header"><span>U1 · Batch — Predictiva sin tiempo real</span><span class="integrante">NILVER</span></div>

<p class="dim-question">¿En qué meses (2010 – 01-oct-2026) la mínima diaria es ≤ 0 °C en más del 30 % de los días, y qué tan bien se puede predecir la temperatura mínima de la noche con lo que se mide a las 18:00?</p>

<div class="dim-body" markdown>

| Campo | Detalle |
|---|---|
| **Indicador(es)** | Porcentaje de días con helada por mes (mínima diaria ≤ 0 °C, umbral meteorológico SENAMHI) y temperatura mínima de la noche predicha por el modelo a partir de las 18:00. |
| **Decisión que habilita** | El agricultor decide si cubrir sus cultivos sensibles a heladas según el mes de mayor riesgo y la mínima esperada esa noche. |
| **Fuente batch** | WeatherAPI, histórico horario de Juliaca 2010-01-01 → 2026-10-01 (146 832 lecturas): temperatura, punto de rocío, humedad y nubosidad. Capa Gold en Parquet, particionada y verificada con lectura de vuelta. |
| **Fuente streaming** | El mismo instrumento acumulado por Kafka; en U1 no se procesa en vivo. |
| **Modelo predictivo** | Regresión de la temperatura mínima nocturna con Spark MLlib. Se comparan: (A) solo estacionalidad, (B) estacionalidad + variables de las 18:00, tres regularizaciones (Ridge, Lasso, ElasticNet) y Random Forest. |
| **Salida** | Notebook PySpark con tablas y gráficos (porcentaje de helada por mes, real contra predicho, importancia de variables, compromiso entre detectar heladas y evitar falsas alarmas) y modelo ganador guardado. |
| **Se combina con** | La dimensión de streaming (U2) en el mismo tablero final. |

**Resultado obtenido (Random Forest):** RMSE 1.077 °C, R² 0.801, MAE 0.839 °C. Con la regla estándar (avisar si la mínima predicha es ≤ 0 °C) detecta solo el 56 % de las heladas; con un margen de aviso de **0.75 °C** el recall sube a **0.875** (161 de 184 heladas) con 118 falsas alarmas en 1 175 noches (10 %).

**Requisitos mínimos**

1. El sistema debe calcular el porcentaje mensual de días con helada a partir del histórico horario de Juliaca, con el umbral de helada definido por criterio meteorológico (no supuesto).
2. El sistema debe entrenar y evaluar un modelo que compare al menos dos configuraciones de predictores y un segundo algoritmo, reportando RMSE, R² y MAE sobre un conjunto de prueba.
3. El sistema debe guardar el modelo ganador de la comparación y verificar que, recargado, da las mismas predicciones.

</div>
</div>

<div class="dim-card blue" markdown>
<div class="dim-card-header"><span>U2 · Streaming — Predictiva con tiempo real</span><span class="integrante">NILVER</span></div>

<p class="dim-question">¿Se puede predecir la temperatura de Juliaca con 1 hora de anticipación y avisar si habrá helada (≤ 0 °C), mejor que simplemente asumir que "la próxima hora será igual que ahora"?</p>

<div class="dim-body" markdown>

| Campo | Detalle |
|---|---|
| **Indicador(es)** | Temperatura prevista a 1 hora (°C) y alerta de helada (predicción ≤ 0 °C); métricas de error (RMSE, MAE, R²) y de alerta (precisión, recall, F1). |
| **Decisión que habilita** | Cubrir los cultivos esa noche cuando el modelo anticipa temperatura ≤ 0 °C dentro de la próxima hora. |
| **Fuente batch** | El histórico Gold de U1, usado para entrenar el modelo antes de ponerlo a trabajar sobre el flujo. |
| **Fuente streaming** | Tópico Kafka `heladas-eventos`, alimentado por un productor que consulta `current.json` de WeatherAPI cada 15 minutos (campos `temperatura`, `puntoRocio`, `humedad`, `nubosidad`, `observadoEn`). |
| **Modelo predictivo** | `PipelineModel` (VectorAssembler + RandomForestRegressor) entrenado con partición cronológica y comparado contra la persistencia (y, a horizontes largos, contra la climatología por hora y mes). Corre en vivo sobre Spark Structured Streaming, sin estado: una sola lectura basta. |
| **Salida** | Tablero de Grafana en vivo con alerta, temperatura real, predicción a 1 h, comparación de modelos, salud del pipeline e histórico, alimentado vía Pushgateway y Prometheus. |
| **Se combina con** | Los KPIs batch del flujo y el histórico (U1) en el mismo tablero. |

**Resultado obtenido (Random Forest, 29 377 horas de prueba):** RMSE 0.971 °C frente a 1.499 °C de la persistencia (−35 %); alerta con precisión 0.912, recall 0.684 y F1 0.782 (persistencia: 0.677 de F1).

**Requisitos mínimos**

1. El sistema debe ingerir lecturas de clima en near-real-time desde el tópico Kafka y filtrar los eventos inválidos antes de predecir.
2. El job de Spark Structured Streaming debe aplicar el modelo a cada micro-lote entrante y publicar la última predicción para el tablero.
3. El sistema debe medir su error de predicción en vivo con lecturas reales y mostrarlo junto a los KPIs en el tablero.

</div>
</div>
