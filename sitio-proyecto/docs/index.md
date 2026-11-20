# Proyecto Sello · Heladas en Juliaca

**Equipo 10 · BIG IMPACT** · Big Data, UPeU 2026-2 · Autor: Nilver Salcca Aquino

Pipeline Big Data con arquitectura **Lambda** que anticipa las heladas en Juliaca (altiplano, más de 3 800 msnm) con datos reales de WeatherAPI: una capa **batch** (histórico 2010 – 01-oct-2026, Unidad I) y una capa de **tiempo real** (Kafka → Spark Structured Streaming → Prometheus/Grafana, Unidad II).

## Preguntas del proyecto

!!! question "Pregunta general"
    ¿Cómo anticipar las heladas (temperatura ≤ 0 °C) en Juliaca para apoyar decisiones agrícolas y de gestión de riesgo local?

!!! question "Pregunta de la Unidad I (batch)"
    ¿En qué meses (2010 – 01-oct-2026) la mínima diaria es ≤ 0 °C en más del 30 % de los días, y qué tan bien se puede predecir la temperatura mínima de la noche con lo que se mide a las 18:00?

!!! question "Pregunta de la Unidad II (streaming)"
    ¿Se puede predecir la temperatura de Juliaca con 1 hora de anticipación y avisar si habrá helada (≤ 0 °C), mejor que simplemente asumir que "la próxima hora será igual que ahora"?

*Definición de helada:* temperatura mínima ≤ 0 °C (criterio meteorológico SENAMHI).

## Resultados principales

| Tema | Resultado |
|---|---|
| Datos batch (Gold) | 146 832 lecturas horarias, 2010-01-01 → 2026-10-01 |
| U1 · mejor modelo (Random Forest) | RMSE 1.077 °C, R² 0.801; con margen de aviso de 0.75 °C detecta **87.5 %** de las heladas (118 falsas alarmas en 1 175 noches) |
| U2 · modelo a 1 h (Random Forest) | RMSE **0.971 °C** frente a 1.499 °C de la persistencia (**−35 %**); F1 de la alerta 0.782 frente a 0.677 |
| U2 · en vivo | Predicciones llegando por Kafka y publicadas en Grafana cada micro-lote; contador de predicciones que sube en Prometheus |
| U2 · horizonte útil | Mejora real sobre la persistencia y la climatología hasta **3-4 h**; alerta de helada con F1 ≥ 0.6 hasta **3 h** |

!!! warning "Hallazgo honesto"
    En las primeras **7 horas medidas en vivo** (una sola noche cálida) la persistencia tuvo menos error que el modelo (MAE 0.886 °C frente a 1.217 °C). Es una muestra muy corta, pero muestra que el error real hay que medirlo en producción y no solo en la prueba histórica. Ver [S11](unidad2/bi-ml-tablero.md).

## Cómo navegar

- **[Dominio y arquitectura](proyecto/arquitectura.md):** por qué Lambda, componentes y flujo de datos.
- **[Unidad I](proyecto/unidad1.md):** ETL batch, calidad, particionamiento y modelo.
- **[Unidad II](unidad2/index.md):** ingesta, streaming, observabilidad, series de tiempo, tablero BI y horizonte útil.
- **[Sustentación](sustentacion.md):** rúbrica contra evidencia, guion de demo y respuestas a las preguntas del docente.
