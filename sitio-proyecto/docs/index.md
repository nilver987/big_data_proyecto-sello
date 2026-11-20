# Brief Técnico Analítico

<p class="pill">PROYECTO SELLO · BIG DATA</p>

# Anticipación de heladas en Juliaca

*Documento de diseño técnico y resultados del equipo **BIG IMPACT** para el curso de Big Data.*

---

<table class="cover-table">
<tr><td>Equipo</td><td>10 · BIG IMPACT</td></tr>
<tr><td>Integrante</td><td>Salcca Aquino, Nilver</td></tr>
<tr><td>Repositorio</td><td><a href="https://github.com/nilver987/big_data_proyecto-sello">github.com/nilver987/big_data_proyecto-sello</a></td></tr>
<tr><td>Fuente de datos</td><td>WeatherAPI · lecturas reales de Juliaca (histórico 2010 – 01-oct-2026 y lectura actual cada 15 min)</td></tr>
<tr><td>Versión</td><td>v3 — Unidades I, II y III (Producto Final)</td></tr>
</table>

## Resumen del proyecto

Juliaca, en el altiplano andino (>3 800 msnm), está expuesta a heladas nocturnas que afectan directamente la producción agrícola local (papa, quinua, cebada). Este proyecto construye un pipeline de Big Data con arquitectura Lambda que combina el histórico climático (capa batch) con lecturas en tiempo real (Kafka, Spark Structured Streaming, Prometheus y Grafana), para que agricultores y gestores de riesgo local puedan anticipar la helada y actuar a tiempo.

!!! question "Pregunta central de negocio"
    ¿Cómo anticipar las heladas (temperatura ≤ 0 °C) en Juliaca para apoyar decisiones agrícolas y de gestión de riesgo local?

*Helada meteorológica = temperatura mínima ≤ 0 °C (criterio SENAMHI).*

## Resultados principales

| Tema | Resultado |
|---|---|
| Datos batch (Gold) | 146 832 lecturas horarias, 2010-01-01 → 2026-10-01 |
| Unidad I · mejor modelo (Random Forest) | RMSE 1.077 °C, R² 0.801; con margen de aviso de 0.75 °C detecta **87.5 %** de las heladas |
| Unidad II · modelo a 1 h (Random Forest) | RMSE **0.971 °C** frente a 1.499 °C de la persistencia (**−35 %**); F1 de la alerta 0.782 frente a 0.677 |
| Unidad II · en vivo | Predicciones llegando por Kafka y publicadas en Grafana en cada micro-lote; una lectura nueva tiene predicción en ≈ 6 s |
| Horizonte útil | Ventaja real sobre la persistencia y la climatología hasta **3-4 h**; alerta con F1 ≥ 0.6 hasta **3 h** |
| Costo estimado de operación | US$ 91.16 al mes |

!!! warning "Hallazgo honesto"
    En las primeras **7 horas medidas en vivo** (una sola noche cálida) la persistencia tuvo menos error que el modelo (MAE 0.886 °C frente a 1.217 °C). La muestra es muy corta, pero muestra que el error real debe medirse en producción y no solo en la prueba histórica. Ver [BI/ML en Grafana](unidad2/bi-ml.md#auditoria-del-error-en-produccion).

## Navegación

- **[Datos del equipo](equipo.md)** — integrante y rol
- **[Dominio del proyecto](dominio.md)** — problema, fuentes de datos, arquitectura
- **[Dimensión de análisis](dimensiones/asignacion.md)** — heladas, batch y streaming
- **[Alcance](alcance.md)** — qué sí y qué no cubre el proyecto
- **[Resultados técnicos](resultados/heladas/01_heladas_nilver.md)** — Unidad I (ETL batch y modelo)
- **[Unidad 2](unidad2/index.md)** — pipeline en tiempo real, de Kafka a Grafana
- **[Unidad 3](unidad3/index.md)** — Producto Final: integración, DataOps, hardening y demo
