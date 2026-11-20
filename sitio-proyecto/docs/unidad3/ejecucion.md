# Instalación y ejecución

Pasos para reproducir el sistema desde una copia del repositorio, **sin ayuda del equipo**.

## Requisitos

| Requisito | Detalle |
|---|---|
| Docker Desktop | Con Docker Compose v2 |
| Memoria | 8 GB de RAM libres recomendados (Spark local + Kafka + Grafana) |
| Clave de WeatherAPI | Archivo `pyspark/sesiones/u1/.env` con `WEATHERAPI_KEY=...` (no se versiona) |
| PowerShell | Los comandos de esta página son de PowerShell, desde la raíz del repositorio |

!!! warning "Los artefactos no viajan con `git clone`"
    `pyspark/sesiones/*/*/artifacts/` está en el `.gitignore`. El Gold de U1, el Parquet de S9 y el modelo de S10 se **generan** ejecutando las sesiones S3, S9 y S10. La primera compuerta previa de S13 lo dice con el nombre exacto de lo que falta.

## Levantar el sistema

```powershell
docker compose -f kafka/compose.yml up -d --wait
docker compose -f pyspark/compose.yml -f pyspark/compose.kafka.yml up -d
docker compose -f obs/compose.yml up -d --wait
docker compose -f uso-heladas/compose.yml up -d
docker exec -d lambda26-uso-heladas python producer_clima.py
```

Kafka va primero porque `obs/` y `pyspark` se unen a su red (`lambda26-kafka-net`). El contenedor `uso-heladas` arranca en `sleep infinity`: el productor se lanza con `docker exec`.

| Servicio | URL | Para qué |
|---|---|---|
| Jupyter | <http://localhost:4488/lab?token=sintoken> | Notebooks de las sesiones |
| Kafka UI | <http://localhost:48085> | Ver el tópico y sus mensajes |
| Prometheus | <http://localhost:49090> | Consultas PromQL |
| Pushgateway | <http://localhost:49091> | Grupos de métricas publicadas |
| Grafana | <http://localhost:43000> | Tableros (`admin` / `admin` por defecto) |

Confirma que el productor publica leyendo el *offset* dos veces con unos minutos de diferencia (llega una lectura cada 15 min):

```powershell
docker exec lambda26-kafka /opt/kafka/bin/kafka-get-offsets.sh --bootstrap-server localhost:9092 --topic heladas-eventos
```

## Orden de las sesiones

| Unidad | Sesiones | Carpeta |
|---|---|---|
| I (batch) | S1 a S5 | `pyspark/sesiones/u1` |
| II (streaming) | S8 a S11 y S11b | `pyspark/sesiones/u2` |
| III (integración) | S13 y S14 | `pyspark/sesiones/u3` |

## Demo end-to-end

La demo dura unos 10 minutos y se apoya en `13_integracion_dataops.ipynb`.

| Min. | Qué se muestra | Qué debe verse | Plan alternativo |
|---:|---|---|---|
| 0-1 | Entorno sano: `docker ps --filter name=lambda26` | Servicios en `(healthy)` | Captura con fecha y hora |
| 1-3 | Compuertas previas (S13, 3.3) | Ocho `OK`, incluido el productor activo | Captura de una corrida anterior |
| 3-5 | Batch del Gold y latencia (3.4) | 146 832 horas, % de helada, p50 frente a p95 | Salida guardada del notebook |
| 5-7 | Streaming con el modelo (3.5-3.6) | Predicciones y MAE frente a persistencia | Manifiesto de una corrida anterior |
| 7-9 | Observabilidad (3.7 y 3.9) | Métricas `lambda26_int_*` y antigüedad de la última ejecución en Grafana | Captura del tablero |
| 9-10 | Manifiesto (3.8) | Compuertas, KPI, bitácora y duración | El archivo abierto |

!!! tip "Antes de empezar"
    Verifica que el productor esté publicando y ensaya la demo completa con cronómetro. Todo plan alternativo debe existir antes de la demostración, con fecha y hora visibles.

## Si algo falla

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| `Compuertas que fallan: ['Productor activo ...']` | El último evento tiene más de 30 min | `docker top lambda26-uso-heladas` debe mostrar `producer_clima.py`; si no, relánzalo |
| `Compuertas que fallan: ['Gold de U1 existe']` | No se corrió S3 | Ejecuta S1 a S3 |
| `Compuertas que fallan: ['Modelo de S10 existe']` | No se corrió S10 | Ejecuta S10 |
| `El stream no entrego ninguna fila` | Topic vacío o modelo no guardado | Revisa el productor y `modelo_rf_temp_h1` |
| `Prometheus no devolvio los valores recien publicados` | El *scrape* tardó más de 90 s | Vuelve a ejecutar la celda 3.7 |
