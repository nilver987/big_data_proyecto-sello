# 2. Ingesta con Kafka

## Flujo

```text
WeatherAPI --HTTP cada 15 min--> producer_clima.py --> Kafka: heladas-eventos --> consumer_clima.py
 current.json                  arma el evento         key = ciudad              valida esquema y rango
```

Código: `uso-heladas/app/` (productor y consumidor). El contrato del evento está en [1. Arquitectura y contrato](arquitectura.md#contrato-del-evento-climalectura).

## Decisiones y particularidades

- **Datos reales, no simulados:** cada evento es una lectura real de la API para Juliaca (equivale a un sensor remoto accesible por HTTP).
- **`key = ciudad`:** garantiza orden, pero con una sola ciudad todos los eventos caen en la misma partición; el particionado por `key` no reparte carga.
- **Lecturas repetidas:** la API actualiza su observación cada ~15 minutos, por lo que varios eventos seguidos pueden compartir `observadoEn`. Por eso el procesamiento deduplica por tiempo del evento.
- **Validación:** el consumidor valida el esquema y el rango físico de la temperatura. En las pruebas de S8 se publicaron eventos inválidos a propósito (`prueba-dedup`, `prueba-watermark`, `prueba-alerta`, con temperaturas de 4 500 °C o campos nulos); el modelo de S10/S11 los filtra antes de predecir.
- **Dos ritmos de productor:** uno cada 15 minutos (régimen real, el que queda en marcha) y uno cada 3 segundos usado en las demostraciones para ver llegar eventos con rapidez.

!!! info "Evento empresarial (S6)"
    <!-- COMPLETAR: describir aquí el evento empresarial de S6 (tópico, contrato, evidencia de publicación y consumo en vivo), tal como se trabajó en esa sesión. -->
    La rúbrica (criterio 1) pide un evento **empresarial** con contrato y tópico documentados, además del de sensores (criterio 2). Completa esta sección con la evidencia de S6.

## Evidencia

- Kafka UI: mensajes del tópico `heladas-eventos` (`http://localhost:48085`).
- Prueba en vivo: una lectura nueva atraviesa Kafka → Spark → modelo en unos 6 segundos (S10, paso 14).
