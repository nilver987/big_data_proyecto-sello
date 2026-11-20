# 4. Observabilidad y alertas

Notebook: `pyspark/sesiones/u2/s09-observabilidad-pipeline/09_observabilidad_pipeline_grafana_costos.ipynb`.

## Qué se mide

- **Infraestructura (Kafka):** brokers visibles, `kafka_consumergroup_lag`, estado del exporter, vía `kafka-exporter` → Prometheus → Grafana.
- **Aplicación (Spark):** throughput y latencia por evento (`latencyMs = processedAt − timestamp`), con `lastProgress`, y latencia agregada por ventana de un minuto.
- **Negocio:** ratio de eventos válidos (solo se puede calcular con las reglas del dominio) y, en S11, el error del modelo medido en vivo.

## Alertas propuestas y umbrales

| Situación | Regla | Justificación con datos medidos |
|---|---|---|
| Kafka no visible | `kafka_brokers < 1` | Valor sano medido: 1 |
| Exporter caído | `up{job="kafka-exporter"} == 0` | Valor sano: 1 (target `UP`) |
| Lag alto sostenido | `kafka_consumergroup_lag > 100` durante 2 min | Lag sano: 0 a 2. A 17-20 eventos por minuto, 100 equivale a ~5 min de atraso |
| Latencia sensible | `avgLatencyMs > 4000` (por minuto) | Promedio sano: 2 573 ms; el mayor promedio por minuto fue 2 720 ms |
| Latencia crítica | `avgLatencyMs > 6000` (por minuto) | Supera el trigger de 5 s y el máximo individual medido (4 892 ms; p99 4 863 ms) |

!!! note "Por qué no se usaron los umbrales de la guía"
    Los umbrales de 100 ms y 1 000 ms de la guía del docente no se usaron: con 3 s de intervalo del productor y un trigger de 5 s, la latencia sana ya es de ~2 500 ms y esas alertas dispararían siempre.

## Régimen normal y backlog

Al arrancar el consumidor aparece latencia muy alta que no es un fallo: es **backlog acumulado**. Por eso se separó el régimen normal (mediana 4 362 ms en el Parquet de S9) del atraso (promedio de 92 327 ms inflado por pocos eventos con retraso enorme), y los umbrales se calcularon sobre la ventana estable.

## En el tablero

La fila C del tablero muestra el estado del pipeline: eventos procesados, ratio de válidos, latencia promedio frente a mediana, **edad del último dato procesado** y ritmo de predicciones por minuto. La fila E reutiliza los paneles de infraestructura Kafka de S9. Ver [7. Tableros](tableros.md).
