# Integración y DataOps (S13)

Una sola ejecución integrada que comprueba sus dependencias, procesa el batch con compuertas de calidad, procesa el streaming con el modelo de S10 sobre Kafka, publica en Prometheus y deja un manifiesto. Notebook: `pyspark/sesiones/u3/s13-integracion-dataops/13_integracion_dataops.ipynb`.

## DataOps en tres rasgos

| Rasgo | Cómo se aplica |
|---|---|
| Dependencias declaradas | Las compuertas previas listan lo que la ejecución necesita antes de empezar |
| Comprobaciones automáticas | La calidad de los datos se verifica dentro del pipeline, no al final y a mano |
| Registro de cada ejecución | El manifiesto JSON deja qué corrió, con qué y con qué resultado |

## 1. Compuertas previas

Ocho dependencias comprobadas en la primera celda. Si alguna falla, la ejecución **se detiene en el acto** con su nombre, en vez de fallar minutos después dentro de Spark.

| # | Compuerta |
|---|---|
| 1 | Gold de U1 existe |
| 2 | Parquet de S9 existe |
| 3 | Modelo de S10 existe |
| 4 | Pushgateway listo |
| 5 | Prometheus listo |
| 6 | Grafana saludable |
| 7 | Kafka: tópico `heladas-eventos` con datos |
| 8 | Productor activo (último evento publicado hace menos de 30 min) |

## 2. Batch con compuertas de calidad y de plausibilidad

**Gold de U1** (146 832 horas reales): hay filas, sin nulos en las cuatro variables, temperatura en rango plausible (−30 a 40 °C) y porcentaje de horas con helada coherente.

**Parquet de S9** (latencia de la ingesta): hay filas, `isValid` y `latencyMs` sin nulos, `ratioValidos` entre 0 y 1 y **latencia típica (p50) menor a 60 s**.

!!! info "Por qué percentiles y no el promedio"
    El promedio resume una distribución en un solo número y puede no describir a nadie si hay una cola larga. Se publican **p50** (qué vive un evento típico), **p95** (qué tan mal le va a los peores) y la fracción que supera 1 minuto. La compuerta usa la mediana; el p95 queda como **advertencia**, porque detener todo el pipeline por una cola larga sería una decisión de negocio, no técnica.

## 3. Streaming con el modelo de S10

El `PipelineModel` de S10 se aplica sobre el tópico completo con `trigger(availableNow=True)`: el stream lee todo lo publicado, lo procesa y **termina**, que es lo que exige una ejecución comprobable.

!!! note "Decisión propia respecto del ejemplo del docente"
    El ejemplo de la guía recibe un evento cada 3 s y usa una ventana fija de 45 s. Aquí el productor publica **cada 15 minutos**: una ventana de 45 s no vería ningún evento. La vivacidad del productor se comprueba con la edad del último evento (compuerta 8).

## 4. Error de predicción en producción

Para cada lectura se compara la predicción con la temperatura **real una hora después** y con la **persistencia** (repetir la última lectura):

| Métrica | Qué responde |
|---|---|
| MAE del modelo (°C) | ¿Cuánto se equivoca el modelo frente a la realidad? |
| MAE de persistencia (°C) | ¿Y la referencia más simple? |
| Alertas de helada (pred ≤ 0 °C) y matriz de aciertos | ¿Cuántas alertas emite y cuántas aciertan? |

El MAE **cambia en cada corrida** porque el tópico crece con lecturas nuevas: con una fuente en vivo no hay reproducibilidad valor por valor. Lo reproducible es el **procedimiento** y lo auditable es **qué dio cada corrida**, para eso existe el manifiesto.

## 5. Observabilidad: Pushgateway, Prometheus y Grafana

Once métricas `lambda26_int_*` publicadas en el grupo `lambda26_integracion_heladas`. La celda las confirma en Prometheus comparando **cada valor devuelto con el que acaba de publicarse** (no con "algún valor"; así no valida datos de una corrida anterior).

| Panel de Grafana | Consulta PromQL |
|---|---|
| Latencia p50 y p95 | `lambda26_int_batch_latencia_p50_ms`, `lambda26_int_batch_latencia_p95_ms` |
| Ratio de eventos válidos | `lambda26_int_batch_validos_ratio` |
| Error del modelo en producción | `lambda26_int_stream_mae`, `lambda26_int_stream_mae_persistencia` |
| Antigüedad de la última ejecución | `time() - lambda26_int_ultima_ejecucion_timestamp` |
| Contexto | `lambda26_int_gold_horas_total`, `lambda26_int_gold_helada_pct`, `lambda26_int_stream_filas_total`, `lambda26_int_stream_alertas_total` |

El panel de antigüedad es el que convierte al tablero en parte de DataOps: sin él, una ejecución que dejó de correr hace días deja un tablero con apariencia de estar vivo. El tablero se llama *S13 - Integración Heladas Juliaca* y la celda 3.9 lo crea por la API de Grafana.

## 6. Manifiesto de ejecución

`artifacts/manifiesto_<runId>.json` registra el identificador de la ejecución, las versiones de Spark y Python, el resultado de cada compuerta, los KPI del Gold y de la latencia, el MAE, las métricas confirmadas en Prometheus, la duración total y la bitácora de hallazgos.

!!! warning "`artifacts/` no se versiona"
    El manifiesto es evidencia de **cada corrida**; se guarda para la sustentación y no viaja con `git clone`.

## Bitácora de integración

| # | Hallazgo | Corrección | Prueba |
|---|---|---|---|
| 1 | El promedio de latencia puede esconder una cola larga | Percentiles p50/p95, fracción > 1 min, compuerta sobre p50 y advertencia sobre p95 | La celda imprime promedio, p50 y p95 juntos |
| 2 | Una copia clonada no puede ejecutar la integración: faltan los artefactos | Compuertas previas que nombran el artefacto que falta | Con el artefacto ausente la ejecución se detiene con su nombre |
| 3 | El productor publica cada 15 min: una ventana fija de 45 s no recibe eventos | `availableNow` sobre el tópico y compuerta de edad del último evento | El stream procesa las predicciones del tópico y termina |
