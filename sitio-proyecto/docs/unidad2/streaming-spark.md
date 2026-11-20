# 3. Streaming con Spark Structured Streaming

Notebook: `pyspark/sesiones/u2/s08-streaming-estructurado/`. Lee `heladas-eventos` en modo streaming con el conector `spark-sql-kafka-0-10`, parsea el JSON con esquema explícito y aplica ventanas, watermark, checkpoint, deduplicación y trigger.

## Hallazgos medidos

| Concepto | Qué se observó |
|---|---|
| Ventana sin límite (`complete`) | Cada tanda reimprimía todas las ventanas desde el inicio (5 ventanas en el Batch 9). El estado crece sin límite |
| Watermark (`update`) | Con 10 s de margen, cada tanda mostró solo la ventana que cambió y Spark descartó el estado de las ventanas cerradas |
| Ventana deslizante | Con ventana de 10 s y salto de 5 s, cada evento contó en dos ventanas traslapadas |
| Checkpoint | `offsets` y `commits` guardan una entrada por tanda; el último offset leído de la partición 1 fue 397. Al reiniciar, la consulta continúa desde ahí |
| Dato tardío | `juliaca-tardio` (45 s en el pasado, watermark de 5 s) fue descartado: nunca apareció en una ventana |
| Deduplicación | `juliaca-duplicado` se publicó dos veces con la misma ciudad y `timestamp` y salió una sola vez |
| Trigger | 1 s: 6 tandas de 1 fila. 6 s: 3 tandas de 1 a 2 filas. Menor intervalo da menor latencia pero más tandas |

## Conclusión para el proyecto

El **watermark** y la **deduplicación** evitan que el estado crezca sin límite y que una lectura repetida de la API cuente dos veces. El **checkpoint** permite reiniciar sin perder eventos. Además, el Parquet de salida **acumula** entre corridas (no sobreescribe) y el intervalo de disparo se midió con `batchId`.

## Demostración en vivo

El notebook incluye dos pruebas pensadas para la sustentación: los datos llegan en tiempo real (sección 15) y Spark "jala" de Kafka en vivo (sección 16).
