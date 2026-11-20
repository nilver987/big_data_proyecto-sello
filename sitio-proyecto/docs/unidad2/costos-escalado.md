# 5. Costos y escalado

## Estimación de costos con valores medidos

| Variable | Valor medido | Supuesto |
|---|---|---|
| Eventos por segundo (pico) | 0.29 (17.3 por minuto, Prometheus) | Un evento cada 3 s del productor |
| Latencia promedio por minuto | 2 642 ms en régimen normal (p95 4 889 ms) | Trigger de 5 s |
| Crecimiento del Parquet por hora | 1 080 filas, 3.25 MB y 720 archivos | 2.3 GB al mes |
| Costo de cómputo | US$ 91.10 al mes | 3 instancias t3.medium a US$ 0.0416/h, 730 h (AWS us-east-1, precio de referencia de la guía) |
| Costo de almacenamiento | US$ 0.05 al mes | S3 Standard a US$ 0.023 por GB al mes |
| **Total estimado** | **US$ 91.16 al mes** | Sin tráfico de red ni mantenimiento |

## Plan de escalado

| Umbral de decisión | Dato que lo justifica | Acción |
|---|---|---|
| Lag > 100 por más de 2 min, o latencia promedio > 6 000 ms | Lag sano 0 a 2. En el atraso de las 00:09 la latencia llegó a 369 s y tardó ~7 min en recuperarse | Revisar primero el consumidor (Spark); si se repite, subir recursos de la instancia de Spark |
| `inputRowsPerSecond` > 1 fila/s (mitad de la capacidad medida) | Spark procesó 2.3 filas/s con entrada de 0.2 filas/s: ~11 veces de holgura | Añadir más ciudades (más claves) y subir particiones y paralelismo antes de agregar máquinas |

**Qué escalaría primero:** el consumidor de Spark, no el broker ni la escritura a Parquet. Hoy todo el tráfico va a una sola partición porque la `key` es siempre "Juliaca"; agregar particiones no ayuda mientras haya una sola clave.

**Por qué no es lo mismo que el costo del batch de U1:** el batch corre y termina (se paga por tiempo de ejecución); el streaming corre 24 h al día, así que el cómputo es un costo fijo mensual y además hay crecimiento continuo del almacenamiento y de archivos pequeños.

**Riesgo operativo:** el volumen (2.3 GB al mes) cuesta centavos, pero 720 archivos pequeños por hora (~17 mil al día) degradan las lecturas. Haría falta compactación periódica y una política de retención.
