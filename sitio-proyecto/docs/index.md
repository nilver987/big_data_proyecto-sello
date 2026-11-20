---
hide:
  - navigation
  - toc
---

<div class="hero" markdown>

# :material-snowflake: Heladas en Juliaca

Pipeline Big Data con arquitectura **Lambda** que anticipa las heladas del altiplano (más de 3 800 msnm) con datos reales de WeatherAPI: capa **batch** con el histórico 2010 – 01-oct-2026 y capa de **tiempo real** con Kafka, Spark y Grafana.

<p class="meta">Proyecto Sello · Equipo 10 BIG IMPACT · Big Data UPeU 2026-2 · Nilver Salcca Aquino</p>

</div>

## Las preguntas

=== "Pregunta general"

    ¿Cómo anticipar las heladas (temperatura ≤ 0 °C) en Juliaca para apoyar decisiones agrícolas y de gestión de riesgo local?

    *Helada = temperatura mínima ≤ 0 °C (criterio meteorológico SENAMHI).*

=== "Unidad I · batch"

    ¿En qué meses (2010 – 01-oct-2026) la mínima diaria es ≤ 0 °C en más del 30 % de los días, y qué tan bien se puede predecir la temperatura mínima de la noche con lo que se mide a las 18:00?

=== "Unidad II · tiempo real"

    ¿Se puede predecir la temperatura de Juliaca con 1 hora de anticipación y avisar si habrá helada (≤ 0 °C), mejor que simplemente asumir que "la próxima hora será igual que ahora"?

## Resultados en cifras

<div class="grid cards" markdown>

- :material-database: **146 832**

    lecturas horarias en el Gold (2010-01-01 → 2026-10-01)

- :material-chart-line: **−35 %**

    de error (RMSE 0.971 frente a 1.499 °C) del modelo a 1 h frente a la persistencia

- :material-bell-alert: **87.5 %**

    de las heladas detectadas en U1 con margen de aviso de 0.75 °C

- :material-clock-fast: **≈ 6 s**

    desde que una lectura se publica en Kafka hasta que tiene predicción

- :material-timer-sand: **3 – 4 h**

    de horizonte con ventaja real sobre la persistencia y la climatología

- :material-currency-usd: **US$ 91.16 / mes**

    costo estimado de operar el streaming (3 instancias + almacenamiento)

</div>

!!! warning "Hallazgo honesto"
    En las primeras **7 horas medidas en vivo** (una sola noche cálida) la persistencia tuvo menos error que el modelo (MAE 0.886 °C frente a 1.217 °C). La muestra es muy corta, pero muestra que el error real debe medirse en producción y no solo en la prueba histórica. Ver [S11](unidad2/bi-ml-tablero.md#auditoria-del-error-en-produccion).

## Dónde está cada cosa

<div class="grid cards" markdown>

- :material-sitemap: **[Dominio y arquitectura](proyecto/arquitectura.md)**

    Por qué Lambda, componentes y flujo de datos.

- :material-database-cog: **[Unidad I](proyecto/unidad1.md)**

    ETL batch, calidad, particionamiento y modelo de la mínima nocturna.

- :material-transit-connection-variant: **[Unidad II](unidad2/index.md)**

    Ingesta, streaming, observabilidad, series de tiempo, tablero BI y horizonte útil.

- :material-image-multiple: **[Evidencias](evidencias.md)**

    Capturas con reloj y perfil: tablero, Prometheus, Pushgateway y auditoría.

- :material-presentation: **[Sustentación](sustentacion.md)**

    Guion de la demo, prueba en vivo y respuestas a las preguntas del docente.

</div>
