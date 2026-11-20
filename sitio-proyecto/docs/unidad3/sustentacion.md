# Sustentación y trazabilidad

## Matriz de trazabilidad

**Variable central:** heladas en Juliaca (helada meteorológica = temperatura mínima ≤ 0 °C, criterio SENAMHI).

!!! question "Pregunta central"
    ¿Con qué anticipación y precisión se puede predecir la helada en Juliaca a partir de temperatura, punto de rocío, humedad y nubosidad?

| Dimensión (integrante) | Indicador | Unidad | Fuente y técnica | Evidencia |
|---|---|---|---|---|
| Heladas en Juliaca · Salcca Aquino, Nilver | Porcentaje de horas con helada por mes | U1 (batch) | WeatherAPI histórico por hora → PySpark Bronze/Silver/Gold, agregación por mes | [Resultados U1](../resultados/heladas/01_heladas_nilver.md); pico en junio (8.4 % de las horas) |
| Heladas en Juliaca · Salcca Aquino, Nilver | Temperatura mínima nocturna predicha a las 18:00 (RMSE, recall con margen) | U1 (batch) | Spark MLlib: regresión lineal, Ridge, Lasso, ElasticNet, Random Forest | [Resultados U1](../resultados/heladas/01_heladas_nilver.md); RMSE 1.077 °C, R² 0.801, recall 0.875 |
| Heladas en Juliaca · Salcca Aquino, Nilver | Temperatura a 1 h y alerta ≤ 0 °C (RMSE y F1 frente a persistencia) | U2 (streaming) | WeatherAPI actual → Kafka → Structured Streaming + PipelineModel | [Series de tiempo](../unidad2/series-tiempo.md); RMSE 0.971 frente a 1.499 °C, F1 0.782 |
| Heladas en Juliaca · Salcca Aquino, Nilver | Salud del pipeline: lag, latencia (p50/p95) y MAE en vivo | U2 y U3 | Prometheus, Pushgateway, kafka-exporter, Grafana | [Observabilidad](../unidad2/observabilidad.md), [Integración](integracion-dataops.md) |

## Aporte individual

El proyecto lo desarrolló **Nilver Salcca Aquino** de forma individual, de punta a punta.

| Tarea | Sesión | Dónde está |
|---|---|---|
| Descarga del histórico, arquitectura y esquema explícito | S1-S2 | [Resultados U1](../resultados/heladas/01_heladas_nilver.md) |
| Calidad de datos y Gold particionado | S3 | [Resultados U1](../resultados/heladas/01_heladas_nilver.md) |
| Modelo de mínima nocturna y evaluación | S4-S5 | [Resultados U1](../resultados/heladas/01_heladas_nilver.md) |
| Ingesta con Kafka y streaming | S8 | [Ingesta](../unidad2/ingesta-kafka.md), [Streaming](../unidad2/streaming-spark.md) |
| Observabilidad y costos | S9 | [Observabilidad](../unidad2/observabilidad.md), [Costos](../unidad2/costos-escalado.md) |
| Series de tiempo e inferencia en vivo | S10 | [Series de tiempo](../unidad2/series-tiempo.md) |
| BI/ML en Grafana y multihorizonte | S11, S11b | [BI/ML](../unidad2/bi-ml.md), [Multihorizonte](../unidad2/multihorizonte.md) |
| Integración, DataOps, hardening y demo | S13-S14 | [Integración](integracion-dataops.md), [Hardening](hardening.md) |

**Decisión propia, con lo que gana y lo que cuesta:** comparar el modelo contra persistencia y climatología y auditarlo en vivo. Gana credibilidad, porque se reporta que en 7 h de auditoría la persistencia ganó y que la ventaja real llega hasta 3-4 h. Cuesta que el producto declara un límite en lugar de prometer un horizonte largo.

## Repositorio y estándares

| Elemento | Detalle |
|---|---|
| Repositorio | [github.com/nilver987/big_data_proyecto-sello](https://github.com/nilver987/big_data_proyecto-sello) |
| Documentación | Este sitio, publicado con MkDocs Material en GitHub Pages |
| Estructura | `pyspark/sesiones/u1` (S1-S5), `u2` (S8-S11b), `u3` (S13-S14); `kafka/`, `obs/`, `uso-heladas/`, `sitio-proyecto/` |
| Secretos | `.env` fuera de git; `artifacts/` ignorado y regenerable ejecutando las sesiones |
| Reproducibilidad | [Instalación y ejecución](ejecucion.md) |

## Limitaciones y mejoras

| Limitación | Mejora priorizada |
|---|---|
| Ventaja del modelo solo hasta 3-4 h; desde las 10 h no hay alertas | Más variables y un modelo por horizonte |
| Una sola ciudad y una sola partición activa (key = ciudad) | Varias ciudades o estaciones, más claves y particiones |
| Histórico solo por hora; el modelo ignora las lecturas de 15 min | Fuente sub-horaria y entrenamiento a 15 min |
| 720 archivos pequeños por hora en el Parquet de streaming | Compactación periódica y política de retención |
| Pushgateway congela el último valor si el productor se detiene | Endpoint `/metrics` propio y panel de antigüedad |
| Sin reentrenamiento ni vigilancia de deriva | Reentrenamiento programado y alerta si el MAE supera a persistencia |
| Riesgos de seguridad aceptados en el laboratorio | TLS/SASL, secretos gestionados y publicar solo el punto de entrada |

## Preguntas esperadas

??? question "¿Por qué Lambda?"
    Hay dos necesidades distintas: entrenar con 16 años de historia (batch, sin prisa) y avisar a tiempo con lecturas nuevas (speed, baja latencia). Lambda las separa y el modelo aprendido en batch se aplica sobre el flujo en vivo; se midieron ≈ 6 s de la lectura a la predicción.

??? question "¿Qué demuestra la integración end-to-end?"
    Que batch, streaming y observabilidad corren juntos en una sola ejecución, con compuertas que la detienen si algo falta y un manifiesto que registra qué pasó.

??? question "¿Cómo sabes que el hardening no rompió nada?"
    Se repite la ejecución integrada y se compara el manifiesto anterior con el nuevo: compuertas, horas del Gold, filas del stream y valores en Prometheus. Que el MAE cambie no es regresión.

??? question "¿Qué riesgo no corregiste y por qué?"
    Kafka sin volumen ni autenticación, Grafana `admin`/`admin` y puertos publicados: es un laboratorio local, y cada fila de la [tabla de riesgos](hardening.md#4-riesgos-aceptados) dice qué cambiaría en producción.

??? question "¿Hasta cuántas horas funciona el modelo?"
    Ventaja real hasta 3-4 h y F1 ≥ 0.6 hasta 3 h. En la auditoría en vivo de 7 h la persistencia ganó (MAE 0.886 frente a 1.217 °C), y por eso se declara el límite. Ver [Multihorizonte](../unidad2/multihorizonte.md).

??? question "¿Es reproducible valor por valor?"
    No: la fuente está en vivo. Es reproducible el procedimiento y auditable cada corrida con su manifiesto.

??? question "¿Qué aporta el p95 que no da el promedio?"
    Muestra la cola: un promedio puede no describir a ningún grupo. La compuerta usa la mediana y el p95 queda como advertencia.
