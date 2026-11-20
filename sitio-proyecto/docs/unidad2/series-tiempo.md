# S10 · Series de tiempo e inferencia en streaming

Notebook: `pyspark/sesiones/u2/s10-series-tiempo-inferencia-streaming/10_series_tiempo_inferencia_streaming.ipynb`.

!!! question "Pregunta"
    ¿Se puede predecir la temperatura de Juliaca con 1 hora de anticipación y avisar si habrá helada (≤ 0 °C), mejor que simplemente asumir que "la próxima hora será igual que ahora"?

## Método

1. **Objetivo con `lead()`:** `temp_h1` = temperatura de la hora siguiente. Heladas a 1 h: 3 180 de 146 831 horas (2.2 %), una clase muy rara, por eso se reportan precisión, recall y F1.
2. **Variables:** solo las que también llegan en el evento de Kafka (`temperatura`, `puntoRocio`, `humedad`, `nubosidad`) más hora del día y mes, para que el mismo modelo sirva en streaming sin reconstruir variables.
3. **Partición cronológica** (nunca aleatoria): 80 % más antiguo para entrenar (hasta 2023-05-26) y 20 % más reciente para evaluar (29 377 horas, 607 heladas). Se verificó que no hay fuga de información (0 horas en ambos conjuntos).
4. **Línea base:** persistencia (`pred = temperatura actual`).
5. **Modelos:** `LinearRegression` y `RandomForestRegressor` (100 árboles, profundidad 8) dentro de un `Pipeline` con `VectorAssembler`.

## Resultados (conjunto de prueba, 2023-05-26 → 2026-10-01)

| Modelo | RMSE (°C) | MAE (°C) | R² | Precisión | Recall | F1 |
|---|---|---|---|---|---|---|
| Persistencia (baseline) | 1.499 | 1.142 | 0.9021 | 0.677 | 0.677 | 0.677 |
| LinearRegression | 1.409 | 1.135 | 0.9134 | 0.723 | 0.336 | 0.459 |
| **RandomForest** | **0.971** | **0.730** | **0.9589** | **0.912** | 0.684 | **0.782** |

**Decisión: se despliega el RandomForest.** Reduce el RMSE un 35.2 % frente a la persistencia y, con la misma capacidad de detectar heladas (415 de 607 frente a 411), baja las falsas alarmas de 196 a 40. La regresión lineal mejora el RMSE solo 6 % y empeora la alerta (recall 0.336). Las variables más influyentes son la temperatura actual (0.50) y la hora del día (0.35): gran parte de la ganancia viene del ciclo diario.

## Inferencia en streaming (sin estado)

El `PipelineModel` guardado se aplica sobre el flujo de Kafka: cada lectura se puntúa por sí sola, sin historial en memoria. Los eventos con campos nulos o fuera de rango se filtran antes del modelo. Las predicciones se guardan en Parquet (`predicciones_heladas`), con checkpoint.

!!! success "Prueba en vivo"
    Una lectura nueva publicada en Kafka produjo su predicción en unos **6 segundos**, sin intervención entre la publicación y el resultado.

## Hallazgo y limitaciones

- El modelo guardado, recargado desde disco, da exactamente las mismas predicciones que el de memoria (diferencia máxima 0.0).
- **Recall 0.684:** deja pasar 192 de las 607 heladas (31.6 %). Un umbral de aviso más alto subiría el recall a costa de más falsas alarmas: decisión de negocio, no del modelo.
- Predice **1 hora**; no sustituye a un pronóstico nocturno completo.
- **Caso M4 (guía 1.6):** aquí el modelo no lineal sí ganó, porque la serie tiene un ciclo diario fuerte que la persistencia ignora. La lección es comparar siempre contra el baseline.
