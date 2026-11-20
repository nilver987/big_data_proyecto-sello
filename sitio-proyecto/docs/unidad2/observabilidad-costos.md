# S9 · Observabilidad y costos

Notebook: `pyspark/sesiones/u2/s09-observabilidad-pipeline/09_observabilidad_pipeline_grafana_costos.ipynb`.

## Qué se mide

- **Infraestructura (Kafka):** brokers visibles, `kafka_consumergroup_lag`, estado del exporter, vía `kafka-exporter` → Prometheus → Grafana.
- **Aplicación (Spark):** throughput y latencia por evento (`latencyMs = processedAt − timestamp`), con `lastProgress`, y latencia agregada por ventana de un minuto.
- **Negocio:** ratio de eventos válidos (solo se puede calcular con las reglas del dominio).

## Alertas propuestas y umbrales

| Situación | Regla | Justificación con datos medidos |
|---|---|---|
| Kafka no visible | `kafka_brokers < 1` | Valor sano medido: 1 |
| Exporter caído | `up{job="kafka-exporter"} == 0` | Valor sano: 1 (target `UP`) |
| Lag alto sostenido | `kafka_consumergroup_lag > 100` durante 2 min | Lag sano: 0 a 2. A 17-20 eventos por minuto, 100 equivale a ~5 min de atraso |
| Latencia sensible | `avgLatencyMs > 4000` (por minuto) | Promedio sano: 2 573 ms; el mayor promedio por minuto fue 2 720 ms |
| Latencia crítica | `avgLatencyMs > 6000` (por minuto) | Supera el trigger de 5 s y el máximo individual medido (4 892 ms; p99 4 863 ms) |

!!! note "Por qué no se usaron los umbrales de la guía"
    Los umbrales de 100 ms y 1000 ms de la guía del docente no se usaron: con 3 s de intervalo del productor y un trigger de 5 s, la latencia sana ya es de ~2 500 ms y esas alertas dispararían siempre.

## Estimación de costos y plan de escalado

| Variable | Valor medido | Supuesto |
|---|---|---|
| Eventos por segundo (pico) | 0.29 (17.3 por minuto, Prometheus) | Un evento cada 3 s del productor |
| Latencia promedio por minuto | 2 642 ms en régimen normal (p95 4 889 ms) | Trigger de 5 s |
| Crecimiento del Parquet por hora | 1 080 filas, 3.25 MB y 720 archivos | 2.3 GB al mes |
| Costo de cómputo | US$ 91.10 al mes | 3 instancias t3.medium a US$ 0.0416/h, 730 h (AWS us-east-1, precio de referencia de la guía) |
| Costo de almacenamiento | US$ 0.05 al mes | S3 Standard a US$ 0.023 por GB al mes |
| **Total estimado** | **US$ 91.16 al mes** | Sin tráfico de red ni mantenimiento |

### Plan de escalado

| Umbral de decisión | Dato que lo justifica | Acción |
|---|---|---|
| Lag > 100 por más de 2 min, o latencia promedio > 6 000 ms | Lag sano 0 a 2. En el atraso de las 00:09 la latencia llegó a 369 s y tardó ~7 min en recuperarse | Revisar primero el consumidor (Spark); si se repite, subir recursos de la instancia de Spark |
| `inputRowsPerSecond` > 1 fila/s (mitad de la capacidad medida) | Spark procesó 2.3 filas/s con entrada de 0.2 filas/s: ~11 veces de holgura | Añadir más ciudades (más claves) y subir particiones y paralelismo antes de agregar máquinas |

**Qué escalaría primero:** el consumidor de Spark, no el broker ni la escritura a Parquet. Hoy todo el tráfico va a una sola partición porque la `key` es siempre "Juliaca"; agregar particiones no ayuda mientras haya una sola clave.

**Riesgo operativo:** el volumen (2.3 GB al mes) cuesta centavos, pero 720 archivos pequeños por hora (~17 mil al día) degradan las lecturas. Haría falta compactación periódica y una política de retención.
