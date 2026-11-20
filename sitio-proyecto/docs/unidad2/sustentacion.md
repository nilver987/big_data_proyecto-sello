# 11. Sustentación

Esta página resume cómo se sustenta cada decisión del proyecto: qué se decidió, por qué, qué alternativa se descartó y cómo se verificó. Sirve como guía para la defensa oral y la demostración en vivo.

Tiempos (S12): demo y sustentación 3 min, preguntas 3 min.

## Qué se construyó, en una frase

Un pipeline en tiempo real que toma lecturas reales de clima de Juliaca, las pasa por Kafka y Spark, las vigila con métricas, y las convierte en una predicción a 1 hora de **heladas** visible en un tablero de Grafana, midiendo además su propio error en vivo.

## Guion de la demo (7 pasos)

1. **Evolución desde U1.** U1 respondía "¿qué tan frío será esta noche?" con datos históricos (batch). U2 responde "¿habrá helada dentro de 1 hora?" con lecturas que llegan ahora (streaming), sobre el mismo instrumento.
2. **Ingesta en vivo.** Kafka UI: mensajes de `heladas-eventos`; mostrar un evento `clima.lectura` y su contrato.
3. **Streaming con ventana, watermark y checkpoint.** Notebook S8: ventana, descarte del dato tardío, deduplicación y offsets del checkpoint.
4. **Observabilidad y costos.** Fila C del tablero y S9: lag, latencia promedio frente a mediana, umbrales medidos, costo estimado de US$ 91.16 al mes.
5. **Modelo y métricas.** S10: RandomForest frente a persistencia (RMSE 0.971 frente a 1.499 °C).
6. **Tablero BI con KPIs y predicción juntos.** Grafana: filas A a D, y la prueba de que el valor cambia (consulta PromQL dos veces).
7. **Una decisión propia distinta del ejemplo del docente.** Umbrales de alerta medidos, comparación contra climatología además de persistencia, o MAE en vivo calculado en lugar del de la prueba.

## Prueba en vivo de que los datos vienen de Kafka

1. Abrir Prometheus (`:49090`) y ejecutar `lambda26_ml_predicciones_total`.
2. Esperar 30-60 s y ejecutar de nuevo: el número debe subir (por ejemplo 686 → 698 en un minuto).
3. En el notebook de S11, ver los micro-lotes imprimiéndose ("Micro-lote N: 1 predicción(es) guardadas y publicadas").
4. Opcional: publicar un evento nuevo y ver su predicción en el Parquet en ~6 s (S10, paso 14).

## Decisiones y su justificación

| Decisión | Por qué | Alternativa descartada | Cómo se verificó |
|---|---|---|---|
| Fuente: WeatherAPI con lecturas reales de Juliaca | Es una fuente real equivalente a un sensor, de la zona del proyecto | Datos simulados | Valores físicamente coherentes; histórico de 146 832 horas sin nulos ni huecos |
| Dos marcas de tiempo (`observadoEn`, `timestamp`) | La API actualiza cada ~15 min y el productor publica más seguido | Una sola marca de tiempo | Lecturas repetidas detectadas y deduplicadas; latencia medida con `timestamp` |
| Key = ciudad, 3 particiones | Mantiene el orden de las lecturas de una ciudad | Sin key (reparto aleatorio) | Kafka UI: todo el tráfico en una partición |
| Filtrar eventos inválidos antes del modelo | Un nulo o 4 500 °C rompe el `VectorAssembler` o distorsiona la predicción | Dejar que el modelo falle | Eventos de prueba descartados; el streaming no se cae |
| Partición cronológica 80/20 | En series de tiempo mezclar futuro con pasado da métricas optimistas | `randomSplit` | 0 horas en ambos conjuntos (verificado con `intersect`) |
| Baseline de persistencia y de climatología | Un modelo solo vale si supera la respuesta trivial | Reportar solo el error del modelo | RandomForest −35 % de RMSE a 1 h; a 12 h solo iguala a la climatología |
| Umbrales de alerta medidos, no genéricos | Los de la guía dispararían siempre | Umbrales de ejemplo | Tabla de umbrales con el dato medido que cada uno usa |
| Pushgateway para KPIs y predicción | El job de Spark no termina ni expone `/metrics` | Que Spark exponga `/metrics` | Valor que cambia entre dos consultas; se documenta el riesgo de valor congelado |
| `POST` en lugar de `PUT` para el MAE en vivo | `PUT` borraría el grupo completo | Reenviar todas las métricas | F1 de la prueba intacto tras publicar |

## Preguntas esperadas y respuestas

??? question "¿Por qué el modelo se compara primero contra la persistencia, y qué significaría que no le gane?"
    Porque es la referencia más simple ("la próxima hora será igual que ahora") y un modelo solo vale si la mejora. Aquí el RandomForest reduce el RMSE un 35 % (1.499 → 0.971 °C). Si no le ganara, no justificaría su complejidad: bastaría repetir la última lectura. En las primeras 7 horas en vivo la persistencia sí ganó (0.886 frente a 1.217 °C), lo que obliga a seguir midiendo en producción antes de afirmar nada.

??? question "¿Qué diferencia hay entre un KPI de negocio y una métrica de infraestructura o de aplicación?"
    Infraestructura: cómo está el sistema (lag del consumidor, brokers). Aplicación: cómo se comporta el código (latencia por evento, throughput). Negocio: si el resultado sirve para decidir; por ejemplo el **ratio de eventos válidos**, que solo se calcula con las reglas del dominio (temperatura en rango, campos completos), o el recall de heladas.

??? question "¿Por qué Pushgateway es un atajo pragmático y no la forma recomendada?"
    Prometheus trabaja por *pull*: consulta endpoints que están vivos. Un job de Spark que termina (o que no expone `/metrics`) no puede ser consultado, así que empuja sus valores al Pushgateway. Está pensado para jobs que terminan; con un job continuo, si el productor se detiene el último valor queda **congelado** y Prometheus lo sigue mostrando como actual. Lo recomendado sería exponer un endpoint `/metrics` en la aplicación. Se mitiga publicando el instante del último evento y mostrando la edad del dato.

??? question "Si un evento llega tarde a tu ventana, ¿qué hace el watermark?"
    Define hasta cuándo Spark espera eventos tardíos. Pasado ese margen cierra la ventana, **descarta** el evento tardío y libera el estado. En S8, con watermark de 5 s, el evento `juliaca-tardio` (45 s en el pasado) no apareció en ninguna ventana. Sin watermark, Spark guardaría el estado de todas las ventanas para siempre y la memoria crecería sin límite.

??? question "¿Qué métrica de observabilidad te alertaría primero ante acumulación de retraso, y por qué?"
    El **lag del consumidor** (`kafka_consumergroup_lag`): sube en cuanto Spark procesa menos de lo que llega, antes de que la latencia se vea afectada. Lag sano medido: 0 a 2; alerta con más de 100 durante 2 minutos (≈ 5 minutos de atraso a 17-20 eventos por minuto).

??? question "¿Por qué estimar el costo de escalar streaming no es lo mismo que el costo del batch de U1?"
    El batch corre y termina: se paga por el tiempo de ejecución. El streaming corre **24 h al día**, así que el cómputo es un costo fijo mensual (3 instancias × 730 h ≈ US$ 91 al mes) y además hay crecimiento continuo del almacenamiento (2.3 GB al mes) y de archivos pequeños (~17 mil por día) que exigen compactación y retención.

??? question "¿Qué gana el tablero BI al mostrar la predicción junto a los KPIs en vez de por separado?"
    Permite leer el riesgo y la confianza al mismo tiempo: la predicción a 1 h junto al error del modelo, la edad del último dato y el estado del pipeline. Una alerta de helada sin saber si el pipeline está retrasado o si el modelo suele fallar de noche no se puede usar para decidir.

??? question "¿Hasta cuántas horas se puede predecir?"
    Con las variables que llegan por Kafka, hay ventaja real sobre la persistencia y la climatología hasta unas **3-4 horas** (RMSE 0.98 – 1.75 °C frente a 1.85 °C). Desde las 5 h el error iguala al de la climatología; la alerta tiene F1 ≥ 0.6 solo hasta 3 h y desde las 10 h no emite alertas. Ver [9. ¿Hasta cuántas horas?](multihorizonte.md).

## Limitaciones que debo declarar

Ver la lista completa en [10. Hallazgos y reflexión](hallazgos.md#limitaciones).
