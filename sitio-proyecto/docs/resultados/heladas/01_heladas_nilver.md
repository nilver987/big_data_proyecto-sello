# ❄️ Heladas · Unidad I (batch)

<p class="pill">UNIDAD I · PYSPARK · PARQUET · MLLIB</p>

Producto: pipeline batch de ETL distribuido con salidas analíticas en Parquet listas para BI/ML, sobre el histórico horario de Juliaca.

| Sesión | Qué se hizo |
|---|---|
| S1 | Descarga del histórico 2010 → 2026-10-01 por años, verificación con Spark (146 832 filas) y arquitectura Lambda con su justificación |
| S2 | Lectura con esquema explícito, transformaciones y acciones, `explain()`, `withColumn()`, agrupaciones, `Window` y RDD |
| S3 | Controles de calidad (nulos, duplicados, rangos), deduplicación determinista con `Window` + `row_number()`, capa Silver y salida particionada en Parquet |
| S4 | Modelo de la temperatura mínima nocturna: comparación de configuraciones y algoritmos |
| S5 | Pipeline end-to-end Bronze → Silver → Gold y sustentación |

## Capas de datos

- **Bronze:** lectura con esquema explícito del histórico descargado.
- **Silver:** duplicados y nulos tratados, columnas derivadas (`hay_helada`, año, mes).
- **Gold:** una fila por hora (`clima_particionado`), particionada en Parquet y verificada con lectura de vuelta.

## Modelo U1: mínima de la noche a partir de las 18:00

Se compararon dos conjuntos de predictores (solo estacionalidad frente a estacionalidad más variables de las 18:00), tres regularizaciones y un segundo algoritmo.

| Resultado | Valor |
|---|---|
| Mejor modelo | Random Forest |
| RMSE · R² · MAE | 1.077 °C · 0.801 · 0.839 °C |
| Detección con la regla estándar (mínima predicha ≤ 0 °C) | 56 % de las heladas (por debajo del objetivo de 80 %) |
| Con margen de aviso de 0.75 °C | **Recall 0.875** (161 de 184 heladas), 118 falsas alarmas en 1 175 noches (10 %) |

!!! warning "Hallazgo"
    El mejor modelo por RMSE no cumplía el objetivo de negocio con la regla estándar: un buen RMSE no garantizaba una buena decisión. Se convirtió la predicción en decisión (helada / no helada) y se eligió el margen de 0.75 °C. **Limitación:** ese margen se eligió sobre el mismo conjunto de prueba, por lo que el recall real podría ser algo menor; lo correcto es fijarlo con un conjunto de validación aparte.

Otros resultados: la regularización (Ridge, Lasso, ElasticNet) no mejoró al modelo lineal, y la configuración con solo estacionalidad tuvo recall 0 (nunca avisaba). Las variables más útiles fueron el punto de rocío a las 18:00 y la estacionalidad.

## Reflexión técnica

Si solo se hubiera entrenado el modelo con la fecha (configuración A) se habría concluido que predecir heladas era imposible: su recall fue 0. Si solo se hubiera entrenado una regresión lineal, el recall habría quedado en 0.53 sin saber que un bosque llega a 0.56 y que cambiando el umbral de aviso se alcanza 0.875. Comparar configuraciones y algoritmos mostró qué variables importan, que la regularización no ayudaba y que el RMSE por sí solo no decide si el modelo sirve para la decisión del agricultor.
