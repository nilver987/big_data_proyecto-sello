# S6-S7 · Ingesta de eventos con Kafka

## Flujo

```text
WeatherAPI --HTTP cada 15 min--> producer_clima.py --> Kafka: heladas-eventos --> consumer_clima.py
 current.json                  arma el evento         key = ciudad              valida esquema y rango
```

Código: `uso-heladas/app/` (productor y consumidor).

## Contrato del evento `clima.lectura`

Tópico `heladas-eventos`, 3 particiones, `key = ciudad`.

```json
{
  "tipoEvento": "clima.lectura",
  "ciudad": "Juliaca",
  "temperatura": 10.2,
  "puntoRocio": 5.9,
  "humedad": 75,
  "nubosidad": 74,
  "origen": "weatherapi",
  "observadoEn": 1795144500000,
  "timestamp": 1795145208962
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `tipoEvento` | string | Nombre del evento publicado |
| `ciudad` | string | Ciudad consultada; también es la `key` de Kafka |
| `temperatura` | number | °C (`temp_c` de la API) |
| `puntoRocio` | number | °C (`dewpoint_c`) |
| `humedad` | number | % (`humidity`) |
| `nubosidad` | number | % (`cloud`) |
| `origen` | string | `"weatherapi"` |
| `observadoEn` | number | Hora en que la API midió (epoch ms, UTC). Es el **tiempo del evento** |
| `timestamp` | number | Hora en que el productor publicó (epoch ms) |

## Decisiones y particularidades

- **Datos reales, no simulados:** cada evento es una lectura real de la API para Juliaca (sensor físico remoto vía API).
- **`key = ciudad`:** garantiza orden, pero con una sola ciudad todos los eventos caen en la misma partición; el particionado por `key` no reparte carga.
- **Lecturas repetidas:** la API actualiza su observación cada ~15 minutos, por lo que varios eventos seguidos pueden compartir `observadoEn`. Por eso el procesamiento deduplica por tiempo del evento.
- **Validación:** el consumidor valida el esquema y el rango físico de la temperatura. En las pruebas de S8 se publicaron eventos inválidos a propósito (`prueba-dedup`, `prueba-watermark`, `prueba-alerta`, con temperaturas de 4 500 °C o campos nulos); el modelo de S10/S11 los filtra antes de predecir.

!!! info "Evento empresarial (S6)"
    <!-- COMPLETAR: describir aquí el evento empresarial de S6 (tópico, contrato, evidencia de publicación y consumo en vivo), tal como lo trabajaste en esa sesión. -->
    La rúbrica (criterio 1) pide un evento **empresarial** con contrato y tópico documentados, además del de sensores (criterio 2). Completa esta sección con tu evidencia de S6.

## Evidencia

- Kafka UI: mensajes del tópico `heladas-eventos` (`http://localhost:48085`).
- Prueba en vivo: una lectura nueva atraviesa Kafka → Spark → modelo en unos 6 segundos (S10, paso 14).
