# Hardening y revisión técnica (S14)

**Hardening** es reducir los puntos débiles de un sistema ya construido: no agrega funcionalidad, quita fragilidad. El ciclo de la sesión es **revisar** la configuración con una lista, **corregir** los fallos, **repetir la ejecución integrada de S13** para demostrar que no se rompió nada y **registrar** los riesgos que se aceptan. Notebook: `pyspark/sesiones/u3/s14-revision-hardening/14_revision_hardening.ipynb`.

## 1. Lista de comprobación de configuración

El script `revision_config.py` revisa, solo en lectura, los `compose.yml` de `kafka/`, `obs/`, `pyspark/` y `uso-heladas/`:

```powershell
python pyspark/sesiones/u3/s14-revision-hardening/revision_config.py
```

| Punto | Pregunta | Dónde se mira |
|---|---|---|
| Versión de imágenes | ¿Cada imagen tiene versión exacta, no `latest`? | `image:` |
| Reinicio | ¿Qué hace el contenedor si el proceso cae? | `restart:` |
| Salud | ¿Hay forma automática de saber si está **listo**? | `healthcheck:` |
| Orden de arranque | ¿Espera a que la dependencia esté lista, no solo arrancada? | `depends_on` + `service_healthy` |
| Secretos | ¿Hay credenciales escritas en el archivo versionado? | `environment:` |
| Superficie expuesta | ¿Qué puertos se publican y por qué? | `ports:` |

### Resultado de la primera revisión

| Servicio | Imagen | Reinicio | Salud | Orden | Secretos |
|---|---|---|---|---|---|
| kafka | Cumple | Cumple | Cumple | N/A | Cumple |
| kafka-exporter, kafka-ui | Cumple | Cumple | N/A (auxiliares) | Cumple | Cumple |
| prometheus, pushgateway | Cumple | Cumple | Cumple | N/A | Cumple |
| grafana | Cumple | Cumple | Cumple | Cumple | Cumple |
| pyspark | N/A (build) | Cumple | **Falla** | N/A | Cumple |
| uso-heladas | N/A (build) | **Falla** | **Falla** | N/A | Cumple |

Tres fallos: `pyspark` sin `healthcheck`, y `uso-heladas` sin `restart` ni `healthcheck`.

## 2. Correcciones

Cada `healthcheck` se **prueba primero a mano** dentro del contenedor (el código de salida debe ser `0`):

```powershell
docker exec lambda26-uso-heladas python -c "import socket; socket.create_connection(('kafka', 9092), 5).close()"
docker exec lambda26-pyspark python -c "import socket; socket.create_connection(('localhost', 8888), 5).close()"
```

```yaml
  uso-heladas:
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import socket; socket.create_connection(('kafka', 9092), 5).close()"]
      interval: 15s
      timeout: 10s
      retries: 5
      start_period: 10s

  pyspark:
    healthcheck:
      test: ["CMD", "python", "-c", "import socket; socket.create_connection(('localhost', 8888), 5).close()"]
      interval: 15s
      timeout: 10s
      retries: 10
      start_period: 30s
```

```powershell
docker compose -f uso-heladas/compose.yml config -q
docker compose -f pyspark/compose.yml -f pyspark/compose.kafka.yml config -q
docker compose -f pyspark/compose.yml -f pyspark/compose.kafka.yml up -d --wait
docker compose -f uso-heladas/compose.yml up -d --wait
docker ps --filter name=lambda26
```

!!! info "Secretos"
    Grafana lee `${GRAFANA_ADMIN_USER:-admin}` y `${GRAFANA_ADMIN_PASSWORD:-admin}`; la clave de WeatherAPI está en `pyspark/sesiones/u1/.env`, ignorado por git (`git check-ignore -v pyspark/sesiones/u1/.env`).

!!! warning "Aplicar `up -d` recrea contenedores"
    Recrear `pyspark` cierra los kernels abiertos; recrear Kafka vacía sus tópicos porque no tiene volumen. `depends_on` no existe entre proyectos de Compose distintos: el orden se garantiza levantando Kafka primero con `up -d --wait`.

## 3. Prueba de no regresión

Se repite la ejecución integrada de S13 sobre la configuración corregida y se compara el **primer manifiesto (antes)** con el **último (después)**. Hay regresión si falla alguno de estos criterios:

| Criterio | Se espera |
|---|---|
| Compuertas previas | Siguen todas en OK |
| Horas del Gold | Idénticas |
| Filas procesadas por el stream | Mayor que 0 |
| Prometheus | Devuelve los valores recién publicados |

Que el **MAE cambie no es regresión**: el tópico crece con lecturas nuevas. Un resultado sin errores no basta; la tabla compara resultados, que es lo que detecta un cambio silencioso.

## 4. Riesgos aceptados

Un riesgo sin justificación escrita no está aceptado: está olvidado.

| Riesgo | Por qué se acepta aquí | Qué cambiaría en producción |
|---|---|---|
| Kafka sin volumen: recrear el contenedor vacía el tópico | El histórico vive en el Gold y el productor vuelve a llenar el tópico | Volumen persistente y replicación entre más de un broker |
| Kafka en PLAINTEXT, sin autenticación | Red local; TLS y SASL complicarían cada ejemplo | Cifrado y autenticación en cada *listener* |
| Grafana `admin`/`admin` y Jupyter con token `sintoken` | Debe arrancar sin configuración previa | Clave propia desde el primer arranque y acceso autenticado |
| Todos los puertos publicados al host | Se necesita llegar a cada herramienta desde el navegador | Publicar solo el punto de entrada |
| Clave de WeatherAPI de prueba (vence ~27-nov-2026) | El Gold ya está descargado; solo el productor en vivo la usa | Plan vigente o proveedor alterno y gestor de secretos |
| Modelo entrenado una sola vez, sin vigilancia de deriva | Alcance del curso; ventaja real medida hasta 3-4 h | Reentrenamiento periódico y alerta si el MAE supera a persistencia |
| Histórico solo por hora | La clave no entrega resolución de 15 min | Fuente sub-horaria |

## 5. Decisiones del sistema y su costo

| Decisión | Por qué | Qué se pierde |
|---|---|---|
| Arquitectura Lambda | Entrenar con 16 años (batch) y reaccionar con baja latencia (speed) | Dos caminos de código; se mitiga reutilizando `preparar()` |
| Publicar en Pushgateway | Un job corto no puede ser raspado por Prometheus | Prometheus no sabe si el dato es reciente: de ahí el panel de antigüedad |
| Percentiles en vez de promedio | El promedio de una cola larga no representa a ningún grupo | Más métricas y paneles que explicar |
| Compuertas que detienen la ejecución | Un resultado vacío o absurdo se detecta donde nace | Una compuerta mal calibrada detiene un pipeline sano |
| Streaming acotado con `availableNow` | Una ejecución integrada tiene que terminar | Evalúa lo publicado hasta ahora, no el futuro |
| Comparar contra persistencia | Sin referencia simple no se sabe si el modelo aporta | Hay que declarar el límite: ventaja real hasta 3-4 h |
