# 10. Decisiones, hallazgos y reflexión

## Decisiones propias

- La fuente es una **API real de Juliaca**, no un sensor propio: el contrato lleva `observadoEn` (cuándo midió la API) y `timestamp` (cuándo se publicó), y se mide la *edad del dato* además de la latencia.
- Los **umbrales de alerta salen de mediciones propias** (latencia sana ~2 500 ms, lag sano 0 a 2), no de los ejemplos de la guía.
- Los eventos **inválidos se filtran antes del modelo** (campos nulos, temperatura fuera de −50 a 50 °C).
- Se compara siempre contra la **persistencia** y, a horizontes largos, contra la **climatología**, porque a 12 h la persistencia es una referencia demasiado débil.
- El **MAE en vivo** del tablero se calcula con lecturas reales y no se escribe a mano.
- La hora del evento se convierte a la **hora local de Juliaca** (UTC−5) con `from_utc_timestamp`, igual que la columna con la que se entrenó el modelo.

## Errores y hallazgos diagnosticados

| # | Hallazgo | Diagnóstico y solución |
|---|---|---|
| 1 | `AnalysisException` al deduplicar (S10) | `dropDuplicates(["observadoEn"])` se aplicaba después de un `select` que ya no traía esa columna. Se reordenó: deduplicar antes de seleccionar |
| 2 | `VectorAssembler` falló con valores nulos (S10) | Eventos de prueba (`prueba-dedup`, `prueba-watermark`, `prueba-alerta`) llegaron al modelo. Se agregó `solo_validos` antes de predecir |
| 3 | "Multiple streaming queries are concurrently using…" (S10) | Una consulta anterior seguía viva sobre el mismo checkpoint. Se detuvieron todas las consultas activas y se reanudó con el mismo checkpoint |
| 4 | Paneles de comparación con «SIN DATOS» | Las series de dos modelos tienen distinta etiqueta `modelo` y la resta no coincidía. Se corrigió con `ignoring(modelo)` en PromQL |
| 5 | Ejes del gráfico de barras con «1 %» o «0 °C 1 °C…» | El eje X numérico heredaba la unidad. Se forzó unidad `none` y conversión del campo a texto |
| 6 | `PUT` al Pushgateway borra el grupo completo | Para actualizar solo el MAE en vivo se usó `POST`, que reemplaza únicamente esas métricas y deja intactas las demás |
| 7 | MAE en vivo escrito a mano (0.442 y 0.644) no coincidía con la auditoría | Se reemplazó por los valores calculados con una lectura por hora (1.217 y 0.886) |
| 8 | Auditoría con pares repetidos | La API repite cada valor 4 veces por hora (lecturas de 15 min). Se conservó una lectura por hora (7 horas distintas) |
| 9 | Consulta en vivo detenida por error al auditar | El `stop()` se había incluido en la celda. Se reanudó con el mismo checkpoint y se quitó el `stop()` |

## Limitaciones

- El histórico es **horario** (la API no ofrece 15 minutos con esta clave); en streaming llegan lecturas cada 15 minutos que repiten valores.
- Una sola ciudad: todo el tráfico va a una partición y agregar particiones no ayuda.
- **Recall de la alerta a 1 h: 0.684** (se escapa el 31.6 % de las heladas); a partir de las 10 h el modelo no emite alertas.
- La validación en vivo cubre solo **7 horas de una noche cálida**; no es concluyente.
- El margen de aviso de U1 (0.75 °C) se eligió sobre el conjunto de prueba, por lo que el recall real podría ser algo menor.
- Más allá de ~4 horas la predicción equivale a la climatología por hora y mes; mejorarla requeriría variables que el evento no trae (presión, viento, pronóstico numérico).
- Los datos vienen de una API meteorológica, no de una estación física en Juliaca.

## Reflexión técnica

Un pipeline de streaming no se valida solo porque funcione hoy: hay que poder ver, con métricas, si está sano y qué tan bien predice **en producción**. Aquí el modelo ganó con claridad en la prueba histórica, pero en las primeras horas en vivo la persistencia le ganó; si el tablero solo mostrara las métricas de prueba, esa diferencia habría pasado inadvertida. Medir el error con lecturas reales y publicarlo junto a los KPIs es lo que permite confiar (o desconfiar) del modelo con datos.

La comparación contra la persistencia es necesaria pero no suficiente: a 12 horas la persistencia es un rival muy débil porque ignora el ciclo diario, y ganarle ahí no demuestra capacidad de predicción. Con la climatología como referencia se vio que la ventaja real del modelo dura 3 a 4 horas. Reportar ese límite, y no el número más favorable, es parte de la honestidad del resultado.

Por último, el Pushgateway resolvió el problema de mostrar en Grafana un job de Spark que no termina, pero es un atajo: si el productor se detiene, el último valor queda congelado como si fuera actual. Por eso el tablero muestra la edad del último dato.
