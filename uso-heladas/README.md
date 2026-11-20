# uso-heladas

Ingesta de eventos de clima de Juliaca en tiempo real con Kafka (S7, Proyecto Sello, Equipo 10 BIG IMPACT).

Fuente: WeatherAPI (`current.json`). A diferencia de `uso-atmos` (sensores ESP32 simulados), aquí cada evento es una lectura real de la API para Juliaca.

## Flujo

```text
WeatherAPI --HTTP cada 15 min--> producer_clima.py --> Kafka: heladas-eventos --> consumer_clima.py
 current.json                  arma el evento         key = ciudad              valida esquema y rango
```

## Contrato del evento `clima.lectura`

Topic: `heladas-eventos`

Particiones: 3 (con una sola ciudad como `key`, todos los eventos caen en la misma partición; el particionado por `key` garantiza orden, no reparto parejo).

Productor:

- `producer_clima.py` (consulta WeatherAPI y publica).

Consumidor:

- `consumer_clima.py` (group `uso-heladas-group`, en esta sesión). S8 agrega el procesamiento con Spark Structured Streaming.

Payload:

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

Campos:

| Campo | Tipo | Descripción |
|---|---|---|
| `tipoEvento` | string | Nombre del evento publicado. |
| `ciudad` | string | Ciudad consultada; también es la `key` de Kafka. |
| `temperatura` | number | Temperatura en grados Celsius (`temp_c` de la API). |
| `puntoRocio` | number | Punto de rocío en grados Celsius (`dewpoint_c`). |
| `humedad` | number | Humedad relativa, en porcentaje (`humidity`). |
| `nubosidad` | number | Cobertura de nubes, en porcentaje (`cloud`). |
| `origen` | string | Quién generó el dato: `"weatherapi"`. |
| `observadoEn` | number | Hora en que la API midió (`last_updated_epoch`), en milisegundos epoch. Es el tiempo del evento. |
| `timestamp` | number | Hora en que el productor publicó el evento, en milisegundos epoch. |

Key recomendada: `ciudad`

Nota: la API actualiza su observación aproximadamente cada 15 minutos, por lo que varios eventos seguidos pueden compartir el mismo `observadoEn`.

## Estados del consumer

| Estado | Condición |
|---|---|
| `consumed` | JSON válido, con todos los campos y valores dentro del rango físico. |
| `invalid` | No es JSON o falta algún campo obligatorio (se conserva `rawPayload` y `decodeError`). |
| `alerta` | JSON válido pero con un valor fuera del rango físico. |

Rango físico aceptado: temperatura -30 a 40 °C, punto de rocío -60 a 30 °C, humedad 0 a 100 %, nubosidad 0 a 100 %. El histórico de Juliaca (2010 a 1-oct-2026) va de -5.4 a 22.0 °C.

## Variables de entorno

| Variable | Valor por defecto | Aplica a |
|---|---|---|
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:9092` | producer y consumer |
| `KAFKA_TOPIC_HELADAS` | `heladas-eventos` | producer y consumer |
| `API_INTERVAL_MS` | `900000` (15 minutos, el ritmo con que WeatherAPI renueva su observación) | producer: pausa entre consultas a la API |
| `CIUDAD` | `Juliaca` | producer |
| `KAFKA_GROUP_ID` | `uso-heladas-group` | consumer |
| `WEATHERAPI_KEY` | *(sin valor por defecto; viene de `pyspark/sesiones/u1/.env`, nunca va en el repositorio)* | producer |

## Cómo ejecutar

Desde la raíz de `lambda26`:

```text
docker compose -f kafka/compose.yml up -d
docker compose -f uso-heladas/compose.yml up -d --build
docker compose -f uso-heladas/compose.yml exec uso-heladas python /app/consumer_clima.py
docker compose -f uso-heladas/compose.yml exec uso-heladas python /app/producer_clima.py
```

El consumer va primero (queda escuchando) y el producer en otra terminal.
