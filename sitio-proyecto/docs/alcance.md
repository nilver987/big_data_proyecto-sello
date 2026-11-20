# Alcance del proyecto

<div class="scope-grid" markdown>
<div class="scope-card yes" markdown>
### ✓ Sí cubre

Porcentaje histórico mensual de días con helada y modelo predictivo batch de la temperatura mínima nocturna (Unidad I), y predicción de la temperatura a 1 hora con alerta de helada (≤ 0 °C) corriendo en vivo sobre Spark Structured Streaming, con el error medido en producción, observabilidad del pipeline y un único tablero de Grafana (Unidad II). Se evaluó además hasta cuántas horas hacia adelante (1 a 12) el modelo mejora a la persistencia y a la climatología.
</div>
<div class="scope-card no" markdown>
### ✕ Fuera de alcance

No incluye sensores físicos propios (fuente única: WeatherAPI, con lecturas reales de Juliaca publicadas en Kafka por un productor). No cubre otras ciudades, ni lluvia, viento o presión. No calcula pérdidas económicas ni recomienda variedades de cultivo: solo estima el riesgo de helada y su momento probable. El pronóstico más allá de ~4 horas no mejora a la climatología con las variables disponibles.
</div>
</div>
